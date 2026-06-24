from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import time

from .analytics import build_keyword_trends, build_monthly_reports, build_trending_topics
from .arxiv import Paper, group_entries
from .arxiv_discovery import WIDE_ARXIV_KEYWORDS, fetch_wide_arxiv_papers, merge_paper_candidates
from .codex import run_codex_summary
from .config import AppConfig
from .db import backup_db, fetch_freshrss_entries, normalize_entry_ids, update_summary_links
from .pdf import download_pdf, extract_pdf_text, render_pdf_first_page_preview, select_pdf_context
from .prompt import build_summary_prompt
from .publisher import (
    publish_category_feeds,
    publish_detail,
    publish_feed,
    publish_feed_directory,
    publish_index,
    publish_keyword_trends,
    publish_monthly_reports,
    publish_source_health_report,
    publish_site_discovery,
    publish_status,
    publish_subscription_opml,
    publish_trending_topics,
    write_manifest,
)
from .state import load_state, save_state
from .source_health import (
    build_source_health_report,
    latest_source_health_records,
    record_source_health_snapshot,
)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def epoch_days_ago(days: int) -> int:
    return int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())


def attach_pdf_context(config: AppConfig, paper: Paper) -> None:
    pdf_dir = config.runtime.state_dir / "pdf"
    text_dir = config.runtime.state_dir / "pdf-text"
    text_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = download_pdf(
        paper,
        pdf_dir=pdf_dir,
        curl_bin=config.runtime.curl_bin,
        timeout=config.runtime.pdf_timeout_seconds,
    )
    text = extract_pdf_text(
        pdf_path,
        pdftotext_bin=config.runtime.pdftotext_bin,
        timeout=config.runtime.pdf_timeout_seconds,
    )
    text_path = text_dir / f"{paper.slug}.txt"
    text_path.write_text(text, encoding="utf-8")
    context = select_pdf_context(text, config.runtime.pdf_max_chars)
    paper.pdf_context = context if len(context) >= 2000 else text[: config.runtime.pdf_max_chars]
    paper.pdf_text_chars = len(text)
    paper.pdf_context_chars = len(paper.pdf_context)
    paper.pdf_error = None
    try:
        paper.hero_image_url = render_pdf_first_page_preview(
            pdf_path,
            output_dir=config.site.output_dir,
            public_base_url=config.site.public_base_url,
            slug=paper.slug,
        )
        paper.hero_image_error = None
    except Exception as exc:  # noqa: BLE001 - image preview is optional
        paper.hero_image_url = ""
        paper.hero_image_error = str(exc)


def select_papers(papers: list[Paper], state: dict[str, object], limit: int, force_id: str | None) -> list[Paper]:
    records = state.setdefault("papers", {})
    selected: list[Paper] = []
    for paper in papers:
        if force_id and paper.arxiv_id != force_id and paper.base_id != force_id:
            continue
        record = records.get(paper.arxiv_id, {}) if isinstance(records, dict) else {}
        if force_id or record.get("status") != "done":
            selected.append(paper)
        if len(selected) >= limit:
            break
    return selected


def run_once(
    config: AppConfig,
    *,
    limit: int = 1,
    since_days: int = 7,
    lookback: int = 1000,
    force_id: str | None = None,
    write_freshrss_links: bool = True,
    use_pdf: bool = True,
    dry_run: bool = False,
) -> list[dict[str, object]]:
    config.runtime.state_dir.mkdir(parents=True, exist_ok=True)
    config.site.output_dir.mkdir(parents=True, exist_ok=True)
    state_path = config.runtime.state_dir / "state.json"
    state = load_state(state_path)
    generated_at = now_iso()
    source_health_records: list[dict[str, object]] = []
    rows = fetch_freshrss_entries(
        config.freshrss.db_path,
        config.freshrss.category,
        since_epoch=epoch_days_ago(since_days),
        limit=lookback,
    )
    papers = group_entries(rows)
    source_health_records.append(
        {
            "name": f"FreshRSS: {config.freshrss.category}",
            "kind": "freshrss",
            "candidate_count": len(papers),
            "status": "ok",
            "raw_count": len(rows),
        }
    )
    if config.arxiv_discovery.enabled:
        arxiv_keywords = config.arxiv_discovery.keywords or list(WIDE_ARXIV_KEYWORDS)
        try:
            wide_papers = fetch_wide_arxiv_papers(
                keywords=arxiv_keywords,
                max_results=config.arxiv_discovery.max_results,
            )
            source_health_records.append(
                {
                    "name": "arXiv",
                    "kind": "arxiv-api",
                    "candidate_count": len(wide_papers),
                    "status": "ok",
                    "max_results": config.arxiv_discovery.max_results,
                }
            )
        except Exception as exc:  # noqa: BLE001 - discovery failures should be visible, not fatal
            wide_papers = []
            source_health_records.append(
                {
                    "name": "arXiv",
                    "kind": "arxiv-api",
                    "candidate_count": 0,
                    "status": "error",
                    "error": str(exc),
                    "max_results": config.arxiv_discovery.max_results,
                }
            )
        papers = merge_paper_candidates(papers, wide_papers)
    source_health_report = build_source_health_report(
        source_health_records,
        previous_records=latest_source_health_records(state),
        generated_at=generated_at,
    )
    record_source_health_snapshot(state, source_health_report)
    selected = select_papers(papers, state, max(limit, 1), force_id)
    records = state.setdefault("papers", {})
    if not isinstance(records, dict):
        raise RuntimeError("state['papers'] must be a dictionary")

    changed: list[dict[str, object]] = []
    if dry_run:
        return [asdict(paper) for paper in selected]

    db_backup_done = False
    work_dir = config.runtime.state_dir / "work"
    for paper in selected:
        record = records.setdefault(paper.arxiv_id, {})
        record.update(
            {
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "entry_ids": normalize_entry_ids(paper.entry_ids),
                "feed_names": paper.feed_names,
                "hero_image_url": paper.hero_image_url,
                "hero_image_error": paper.hero_image_error,
                "status": "running",
                "updated_at": now_iso(),
            }
        )
        save_state(state_path, state)

        if use_pdf:
            try:
                attach_pdf_context(config, paper)
            except Exception as exc:  # noqa: BLE001 - record and fall back to RSS abstract
                paper.pdf_error = str(exc)

        prompt = build_summary_prompt(paper)
        markdown = run_codex_summary(
            command=config.codex.command,
            reasoning_effort=config.codex.reasoning_effort,
            prompt=prompt,
            output_path=work_dir / f"{paper.slug}.summary.md",
            timeout_seconds=config.codex.timeout_seconds,
        )
        generated_at = now_iso()
        publish_record = publish_detail(
            paper,
            markdown,
            output_dir=config.site.output_dir,
            public_base_url=config.site.public_base_url,
            generated_at=generated_at,
        )
        record.update(publish_record)
        record["status"] = "done"
        record["updated_at"] = now_iso()

        if write_freshrss_links:
            if not db_backup_done:
                backup_db(config.freshrss.db_path, config.runtime.state_dir / "db-backups")
                db_backup_done = True
            record["freshrss_entries_updated"] = update_summary_links(
                config.freshrss.db_path,
                paper.arxiv_id,
                normalize_entry_ids(paper.entry_ids),
                str(publish_record["url"]),
            )
        changed.append(record.copy())
        save_state(state_path, state)
        time.sleep(0.1)

    all_done = [item for item in records.values() if isinstance(item, dict) and item.get("status") == "done"]
    generated_at = now_iso()
    publish_index(
        all_done,
        config.site.output_dir,
        generated_at=generated_at,
        public_base_url=config.site.public_base_url,
    )
    publish_feed(
        all_done,
        config.site.output_dir,
        public_base_url=config.site.public_base_url,
        generated_at=generated_at,
    )
    category_records = publish_category_feeds(
        all_done,
        config.site.output_dir,
        public_base_url=config.site.public_base_url,
        generated_at=generated_at,
    )
    publish_subscription_opml(
        category_records,
        config.site.output_dir,
        public_base_url=config.site.public_base_url,
    )
    publish_feed_directory(
        category_records,
        config.site.output_dir,
        public_base_url=config.site.public_base_url,
        generated_at=generated_at,
    )
    monthly_reports = build_monthly_reports(all_done, generated_at=generated_at)
    trending_topics = build_trending_topics(all_done, generated_at=generated_at)
    keyword_trends = build_keyword_trends(all_done, generated_at=generated_at)
    publish_monthly_reports(
        monthly_reports,
        config.site.output_dir,
        public_base_url=config.site.public_base_url,
        generated_at=generated_at,
    )
    publish_trending_topics(
        trending_topics,
        config.site.output_dir,
        public_base_url=config.site.public_base_url,
        generated_at=generated_at,
    )
    publish_keyword_trends(
        keyword_trends,
        config.site.output_dir,
        public_base_url=config.site.public_base_url,
        generated_at=generated_at,
    )
    publish_source_health_report(
        source_health_report,
        config.site.output_dir,
        public_base_url=config.site.public_base_url,
        generated_at=generated_at,
    )
    publish_status(
        all_done,
        category_records=category_records,
        monthly_reports=monthly_reports,
        trending_topics=trending_topics,
        keyword_trends=keyword_trends,
        output_dir=config.site.output_dir,
        public_base_url=config.site.public_base_url,
        generated_at=generated_at,
    )
    publish_site_discovery(
        all_done,
        monthly_reports=monthly_reports,
        trending_topics=trending_topics,
        keyword_trends=keyword_trends,
        output_dir=config.site.output_dir,
        public_base_url=config.site.public_base_url,
        generated_at=generated_at,
    )
    write_manifest(all_done, config.site.output_dir)
    save_state(state_path, state)
    return changed
