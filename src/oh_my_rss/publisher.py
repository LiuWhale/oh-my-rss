from __future__ import annotations

from pathlib import Path
import hashlib
import html
import json
import re
import shutil
import unicodedata

from .analytics import MonthlyReport
from .arxiv import Paper
from .reports import (
    render_direction_bars_svg,
    render_monthly_report_html,
    render_monthly_report_json,
    render_source_donut_svg,
    render_trend_animated_svg,
)
from .render import render_detail_html, render_index_html, render_rss_xml


def detail_filename(arxiv_id: str, summary_sha256: str) -> str:
    safe = arxiv_id.replace("/", "_")
    return f"{safe}-{summary_sha256[:12]}.html"


def publish_detail(paper: Paper, markdown: str, output_dir: Path, public_base_url: str, generated_at: str) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    name = detail_filename(paper.arxiv_id, sha)
    html = render_detail_html(
        title=paper.title,
        arxiv_id=paper.arxiv_id,
        feeds=paper.feed_names,
        abs_url=paper.abs_url,
        pdf_url=paper.pdf_url,
        hero_image_url=paper.hero_image_url,
        markdown=markdown,
        generated_at=generated_at,
    )
    detail_path = output_dir / name
    detail_path.write_text(html, encoding="utf-8")
    stable_path = output_dir / f"{paper.slug}.html"
    shutil.copyfile(detail_path, stable_path)
    return {
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "url": f"{public_base_url.rstrip('/')}/{name}",
        "detail_name": name,
        "generated_at": generated_at,
        "summary_sha256": sha,
        "feed_names": paper.feed_names,
        "entry_ids": paper.entry_ids,
        "summary_excerpt": summary_excerpt(markdown),
        "summary_source": "pdf" if paper.pdf_context else "rss",
        "pdf_text_chars": paper.pdf_text_chars,
        "pdf_context_chars": paper.pdf_context_chars,
        "pdf_error": paper.pdf_error,
        "hero_image_url": paper.hero_image_url,
        "hero_image_error": paper.hero_image_error,
    }


def publish_index(records: list[dict[str, object]], output_dir: Path, generated_at: str) -> None:
    done = [record for record in records if record.get("url")]
    done.sort(key=lambda item: str(item.get("generated_at", "")), reverse=True)
    html = render_index_html(done, generated_at)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(html, encoding="utf-8")


def publish_feed(
    records: list[dict[str, object]],
    output_dir: Path,
    public_base_url: str,
    generated_at: str,
) -> None:
    done = [record for record in records if record.get("url")]
    done.sort(key=lambda item: str(item.get("generated_at", "")), reverse=True)
    xml = render_rss_xml(
        done,
        generated_at=generated_at,
        public_base_url=public_base_url,
        include_item_categories=False,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "feed.xml").write_text(xml, encoding="utf-8")


def publish_category_feeds(
    records: list[dict[str, object]],
    output_dir: Path,
    public_base_url: str,
    generated_at: str,
) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for record in records:
        if not record.get("url"):
            continue
        category_names = record_category_names(record)
        if not category_names:
            category_names = ["Uncategorized"]
        for category_name in category_names:
            grouped.setdefault(category_name, []).append(record)

    categories_dir = output_dir / "categories"
    categories_dir.mkdir(parents=True, exist_ok=True)
    used_slugs: dict[str, str] = {}
    category_records: list[dict[str, object]] = []
    base_url = public_base_url.rstrip("/")

    for category_name in sorted(grouped):
        slug = category_slug(category_name)
        if slug in used_slugs and used_slugs[slug] != category_name:
            slug = f"{slug}-{hashlib.sha256(category_name.encode('utf-8')).hexdigest()[:8]}"
        used_slugs[slug] = category_name
        items = sorted(grouped[category_name], key=lambda item: str(item.get("generated_at", "")), reverse=True)
        feed_path = f"categories/{slug}.xml"
        xml = render_rss_xml(
            items,
            generated_at=generated_at,
            public_base_url=public_base_url,
            title=f"Oh My RSS - {category_name}",
            description=f"Generated summaries for {category_name}.",
            feed_path=feed_path,
            item_category=category_name,
        )
        (categories_dir / f"{slug}.xml").write_text(xml, encoding="utf-8")
        category_records.append(
            {
                "name": category_name,
                "slug": slug,
                "url": f"{base_url}/{feed_path}",
                "count": len(items),
            }
        )

    remove_stale_arxiv_category_files(categories_dir, set(used_slugs))

    (categories_dir / "index.json").write_text(
        json.dumps(category_records, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (categories_dir / "opml.xml").write_text(
        render_category_opml(category_records),
        encoding="utf-8",
    )
    return category_records


def publish_monthly_reports(
    reports: list[MonthlyReport],
    output_dir: Path,
    public_base_url: str,
    generated_at: str,
) -> list[dict[str, object]]:
    reports_root = output_dir / "reports"
    monthly_dir = reports_root / "monthly"
    assets_dir = monthly_dir / "assets"
    monthly_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    base_url = public_base_url.rstrip("/")

    feed_records: list[dict[str, object]] = []
    for report in reports[:12]:
        html_path = monthly_dir / f"{report.month}.html"
        json_path = monthly_dir / f"{report.month}.json"
        direction_path = assets_dir / f"{report.month}-direction-bars.svg"
        source_path = assets_dir / f"{report.month}-source-donut.svg"
        trend_path = assets_dir / f"{report.month}-trend-animated.svg"

        html_path.write_text(render_monthly_report_html(report), encoding="utf-8")
        json_path.write_text(render_monthly_report_json(report), encoding="utf-8")
        direction_path.write_text(render_direction_bars_svg(report), encoding="utf-8")
        source_path.write_text(render_source_donut_svg(report), encoding="utf-8")
        trend_path.write_text(render_trend_animated_svg(report), encoding="utf-8")

        url = f"{base_url}/reports/monthly/{report.month}.html"
        feed_records.append(
            {
                "title": report.title,
                "url": url,
                "generated_at": report.generated_at,
                "feed_names": ["Monthly Research Radar"],
                "summary_excerpt": report.summary,
                "month": report.month,
                "total_papers": report.total_papers,
            }
        )

    feed_xml = render_rss_xml(
        feed_records,
        generated_at=generated_at,
        public_base_url=public_base_url,
        title="Oh My RSS Monthly Research Radar",
        description="Monthly research trend reports generated from Oh My RSS paper summaries.",
        feed_path="reports/monthly.xml",
        channel_link=feed_records[0]["url"] if feed_records else f"{base_url}/index.html",
        include_item_categories=False,
    )
    reports_root.mkdir(parents=True, exist_ok=True)
    (reports_root / "monthly.xml").write_text(feed_xml, encoding="utf-8")
    return feed_records


def record_category_names(record: dict[str, object]) -> list[str]:
    raw_names = record.get("research_domains") or record.get("feed_names", []) or []
    return _unique_strings(normalize_category_name(name) for name in raw_names)


def normalize_category_name(name: object) -> str:
    text = str(name).strip()
    if text.startswith("arXiv "):
        return text[len("arXiv ") :].strip()
    return text


def remove_stale_arxiv_category_files(categories_dir: Path, active_slugs: set[str]) -> None:
    for path in categories_dir.glob("arxiv-*.xml"):
        if path.stem not in active_slugs:
            path.unlink()


def render_category_opml(category_records: list[dict[str, object]]) -> str:
    outlines = []
    for item in category_records:
        name = str(item["name"])
        url = str(item["url"])
        outlines.append(
            "    "
            f'<outline text="{_xml_attr(name)}" title="{_xml_attr(name)}" '
            f'type="rss" xmlUrl="{_xml_attr(url)}" htmlUrl="{_xml_attr(url)}" />'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<opml version="2.0">\n'
        "  <head>\n"
        "    <title>Oh My RSS category feeds</title>\n"
        "  </head>\n"
        "  <body>\n"
        + "\n".join(outlines)
        + "\n  </body>\n</opml>\n"
    )


def write_manifest(records: list[dict[str, object]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def summary_excerpt(markdown: str, max_chars: int = 500) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", markdown)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = re.sub(r"^\s*[-*]\s*", "", text, flags=re.M)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "..."


def category_slug(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    slug = re.sub(r"-+", "-", slug)
    if slug:
        return slug[:80].strip("-")
    return f"category-{hashlib.sha256(name.encode('utf-8')).hexdigest()[:10]}"


def _unique_strings(values: list[object]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _xml_attr(value: str) -> str:
    return html.escape(value, quote=True)
