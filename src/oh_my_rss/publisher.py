from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import html
import json
import re
import shutil
import unicodedata

from .analytics import KeywordTrend, MonthlyReport, TrendingTopic
from .arxiv import Paper
from .domains import classify_record_domains, classify_research_domains
from .reports import (
    render_direction_bars_svg,
    render_keyword_trends_index_html,
    render_keyword_trend_json,
    render_monthly_report_html,
    render_monthly_report_json,
    render_source_donut_svg,
    render_trend_animated_svg,
    render_trending_topics_index_html,
    render_trending_topic_json,
)
from .render import record_sort_key, render_detail_html, render_index_html, render_rss_xml


CATEGORY_ALIAS_GROUPS: tuple[tuple[str, ...], ...] = (
    ("Robotics / Embodied AI", "Robotics latest (cs.RO)"),
    ("VLA / Multimodal Agents", "VLA / Vision-Language-Action", "Vision-Language-Action"),
    ("Robot Learning / Policy", "机器人学习 / Policy Learning"),
    ("Navigation / Planning", "导航规划 / Navigation"),
    ("Benchmark / Dataset / Evaluation", "Benchmark数据集 / Dataset"),
    ("Safety / Control", "安全控制 / Safety"),
)


def detail_filename(arxiv_id: str, summary_sha256: str) -> str:
    safe = arxiv_id.replace("/", "_")
    return f"{safe}-{summary_sha256[:12]}.html"


def paper_source_published_at(paper: Paper) -> str:
    if not paper.date:
        return ""
    return datetime.fromtimestamp(paper.date, timezone.utc).isoformat()


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
        source_label=paper.source_kind,
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
        "paper_id": paper.paper_id or paper.arxiv_id,
        "source_kind": paper.source_kind,
        "source_url": paper.abs_url,
        "pdf_url": paper.pdf_url,
        "title": paper.title,
        "abstract": paper.abstract,
        "url": f"{public_base_url.rstrip('/')}/{name}",
        "detail_name": name,
        "generated_at": generated_at,
        "source_published_at": paper_source_published_at(paper),
        "summary_sha256": sha,
        "feed_names": paper.feed_names,
        "feed_urls": paper.feed_urls,
        "keywords": paper.keywords,
        "research_domains": classify_research_domains(paper),
        "entry_ids": paper.entry_ids,
        "summary_excerpt": summary_excerpt(markdown),
        "summary_source": "pdf" if paper.pdf_context else "rss",
        "pdf_text_chars": paper.pdf_text_chars,
        "pdf_context_chars": paper.pdf_context_chars,
        "pdf_error": paper.pdf_error,
        "hero_image_url": paper.hero_image_url,
        "hero_image_error": paper.hero_image_error,
    }


def publish_index(
    records: list[dict[str, object]],
    output_dir: Path,
    generated_at: str,
    public_base_url: str = "",
) -> None:
    done = [record for record in records if record.get("url")]
    done.sort(key=record_sort_key, reverse=True)
    html = render_index_html(done, generated_at, public_base_url=public_base_url)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(html, encoding="utf-8")


def publish_feed(
    records: list[dict[str, object]],
    output_dir: Path,
    public_base_url: str,
    generated_at: str,
) -> None:
    done = [record for record in records if record.get("url")]
    done.sort(key=record_sort_key, reverse=True)
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
    sync_duplicate_category_aliases(grouped)

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
        items = sorted(grouped[category_name], key=record_sort_key, reverse=True)
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


def publish_subscription_opml(
    category_records: list[dict[str, object]],
    output_dir: Path,
    public_base_url: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "opml.xml").write_text(
        render_subscription_opml(category_records, public_base_url),
        encoding="utf-8",
    )


def publish_feed_directory(
    category_records: list[dict[str, object]],
    output_dir: Path,
    public_base_url: str,
    generated_at: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    feeds = feed_directory_records(category_records, public_base_url)
    (output_dir / "feeds.json").write_text(
        json.dumps(
            {
                "title": "Oh My RSS feed directory",
                "generated_at": generated_at,
                "public_base_url": public_base_url.rstrip("/"),
                "feed_count": len(feeds),
                "feeds": feeds,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def publish_status(
    records: list[dict[str, object]],
    *,
    category_records: list[dict[str, object]],
    monthly_reports: list[object],
    trending_topics: list[object],
    keyword_trends: list[object],
    output_dir: Path,
    public_base_url: str,
    generated_at: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    base_url = public_base_url.rstrip("/")
    done = [record for record in records if record.get("url")]
    done.sort(key=record_sort_key, reverse=True)
    latest_summary = None
    if done:
        latest = done[0]
        latest_summary = {
            "title": str(latest.get("title") or latest.get("arxiv_id") or "Untitled paper"),
            "url": str(latest["url"]),
            "generated_at": str(latest.get("generated_at") or ""),
        }
    payload = {
        "ok": True,
        "title": "Oh My RSS status",
        "generated_at": generated_at,
        "public_base_url": base_url,
        "summary_count": len(done),
        "category_count": len(category_records),
        "monthly_report_count": len(monthly_reports),
        "trending_topic_count": len(trending_topics),
        "keyword_trend_count": len(keyword_trends),
        "latest_summary": latest_summary,
        "feeds": {
            "all": f"{base_url}/feed.xml",
            "feed_directory": f"{base_url}/feeds.json",
            "subscription_opml": f"{base_url}/opml.xml",
            "category_opml": f"{base_url}/categories/opml.xml",
            "monthly": f"{base_url}/reports/monthly.xml",
            "trending": f"{base_url}/reports/trending.xml",
            "keywords": f"{base_url}/reports/keywords.xml",
            "source_health": f"{base_url}/reports/source-health.xml",
        },
    }
    (output_dir / "status.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def publish_site_discovery(
    records: list[dict[str, object]],
    *,
    monthly_reports: list[MonthlyReport],
    trending_topics: list[TrendingTopic],
    keyword_trends: list[KeywordTrend],
    output_dir: Path,
    public_base_url: str,
    generated_at: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    base_url = public_base_url.rstrip("/")
    sitemap_url = f"{base_url}/sitemap.xml"
    (output_dir / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {sitemap_url}\n",
        encoding="utf-8",
    )
    urls = sitemap_url_records(
        records,
        monthly_reports=monthly_reports,
        trending_topics=trending_topics,
        keyword_trends=keyword_trends,
        public_base_url=public_base_url,
        generated_at=generated_at,
    )
    (output_dir / "sitemap.xml").write_text(render_sitemap_xml(urls), encoding="utf-8")


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
                "summary_excerpt": summary_with_html_link(report.summary, url),
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


def publish_trending_topics(
    topics: list[TrendingTopic],
    output_dir: Path,
    public_base_url: str,
    generated_at: str,
) -> list[dict[str, object]]:
    reports_root = output_dir / "reports"
    trending_dir = reports_root / "trending"
    trending_dir.mkdir(parents=True, exist_ok=True)
    base_url = public_base_url.rstrip("/")
    used_slugs: dict[str, str] = {}
    topic_pages: list[tuple[TrendingTopic, str]] = []

    index_records: list[dict[str, object]] = []
    feed_records: list[dict[str, object]] = []
    for topic in topics[:20]:
        slug = category_slug(topic.name)
        if slug in used_slugs and used_slugs[slug] != topic.name:
            slug = f"{slug}-{hashlib.sha256(topic.name.encode('utf-8')).hexdigest()[:8]}"
        used_slugs[slug] = topic.name

        json_path = trending_dir / f"{slug}.json"
        json_path.write_text(render_trending_topic_json(topic), encoding="utf-8")

        topic_pages.append((topic, slug))
        url = report_item_url(
            base_url=base_url,
            report_path="trending",
            fragment=f"topic-{slug}",
            report=topic,
        )
        record = {
            "title": topic.title,
            "url": url,
            "generated_at": topic.generated_at,
            "feed_names": ["Trending Research Topics"],
            "summary_excerpt": summary_with_html_link(topic.summary, url),
            "name": topic.name,
            "month": topic.month,
            "paper_count": topic.paper_count,
            "growth": topic.growth,
            "score": topic.score,
            "slug": slug,
        }
        index_records.append(record)
        feed_records.append(record)

    (trending_dir / "index.html").write_text(
        render_trending_topics_index_html(topic_pages),
        encoding="utf-8",
    )
    remove_stale_report_detail_pages(trending_dir)
    (trending_dir / "index.json").write_text(
        json.dumps(index_records, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    feed_xml = render_rss_xml(
        feed_records,
        generated_at=generated_at,
        public_base_url=public_base_url,
        title="Oh My RSS Trending Research Topics",
        description="Current hot research directions generated from Oh My RSS paper summaries.",
        feed_path="reports/trending.xml",
        channel_link=f"{base_url}/reports/trending/index.html",
        include_item_categories=False,
    )
    reports_root.mkdir(parents=True, exist_ok=True)
    (reports_root / "trending.xml").write_text(feed_xml, encoding="utf-8")
    return feed_records


def publish_keyword_trends(
    trends: list[KeywordTrend],
    output_dir: Path,
    public_base_url: str,
    generated_at: str,
) -> list[dict[str, object]]:
    reports_root = output_dir / "reports"
    keywords_dir = reports_root / "keywords"
    keywords_dir.mkdir(parents=True, exist_ok=True)
    base_url = public_base_url.rstrip("/")
    used_slugs: dict[str, str] = {}
    keyword_pages: list[tuple[KeywordTrend, str]] = []

    index_records: list[dict[str, object]] = []
    feed_records: list[dict[str, object]] = []
    for trend in trends[:20]:
        slug = category_slug(trend.keyword)
        if slug in used_slugs and used_slugs[slug] != trend.keyword:
            slug = f"{slug}-{hashlib.sha256(trend.keyword.encode('utf-8')).hexdigest()[:8]}"
        used_slugs[slug] = trend.keyword

        json_path = keywords_dir / f"{slug}.json"
        json_path.write_text(render_keyword_trend_json(trend), encoding="utf-8")

        keyword_pages.append((trend, slug))
        url = report_item_url(
            base_url=base_url,
            report_path="keywords",
            fragment=f"keyword-{slug}",
            report=trend,
        )
        record = {
            "title": trend.title,
            "url": url,
            "generated_at": trend.generated_at,
            "feed_names": ["Trending Research Keywords"],
            "summary_excerpt": summary_with_html_link(trend.summary, url),
            "keyword": trend.keyword,
            "month": trend.month,
            "paper_count": trend.paper_count,
            "growth": trend.growth,
            "score": trend.score,
            "slug": slug,
        }
        index_records.append(record)
        feed_records.append(record)

    (keywords_dir / "index.html").write_text(
        render_keyword_trends_index_html(keyword_pages),
        encoding="utf-8",
    )
    remove_stale_report_detail_pages(keywords_dir)
    (keywords_dir / "index.json").write_text(
        json.dumps(index_records, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    feed_xml = render_rss_xml(
        feed_records,
        generated_at=generated_at,
        public_base_url=public_base_url,
        title="Oh My RSS Trending Research Keywords",
        description="Current hot research keywords generated from Oh My RSS paper summaries.",
        feed_path="reports/keywords.xml",
        channel_link=f"{base_url}/reports/keywords/index.html",
        include_item_categories=False,
    )
    reports_root.mkdir(parents=True, exist_ok=True)
    (reports_root / "keywords.xml").write_text(feed_xml, encoding="utf-8")
    return feed_records


def publish_source_health_report(
    report: dict[str, object],
    output_dir: Path,
    public_base_url: str,
    generated_at: str,
) -> dict[str, object]:
    reports_root = output_dir / "reports"
    source_dir = reports_root / "source-health"
    source_dir.mkdir(parents=True, exist_ok=True)
    base_url = public_base_url.rstrip("/")
    url = f"{base_url}/reports/source-health/index.html"

    (source_dir / "index.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (source_dir / "index.html").write_text(render_source_health_html(report), encoding="utf-8")

    warning_count = int(report.get("warning_count") or 0)
    source_count = int(report.get("source_count") or 0)
    summary = f"本次检查 {source_count} 个源，发现 {warning_count} 个提醒。"
    if warning_count:
        warning_sources = [
            str(item.get("name") or "")
            for item in report.get("sources", [])
            if isinstance(item, dict) and item.get("warnings")
        ][:6]
        if warning_sources:
            summary += " 需要关注：" + "、".join(warning_sources) + "。"

    feed_record = {
        "title": "源健康检查 / Source Health Radar",
        "url": url,
        "generated_at": generated_at,
        "feed_names": ["Source Health Radar"],
        "summary_excerpt": summary_with_html_link(summary, url),
        "warning_count": warning_count,
        "source_count": source_count,
    }
    feed_xml = render_rss_xml(
        [feed_record],
        generated_at=generated_at,
        public_base_url=public_base_url,
        title="Oh My RSS Source Health Radar",
        description="Source health checks for Oh My RSS paper discovery.",
        feed_path="reports/source-health.xml",
        channel_link=url,
        include_item_categories=False,
    )
    reports_root.mkdir(parents=True, exist_ok=True)
    (reports_root / "source-health.xml").write_text(feed_xml, encoding="utf-8")
    return feed_record


def render_source_health_html(report: dict[str, object]) -> str:
    generated_at = html.escape(str(report.get("generated_at") or ""), quote=False)
    warning_count = int(report.get("warning_count") or 0)
    source_count = int(report.get("source_count") or 0)
    rows = []
    for item in report.get("sources", []):
        if not isinstance(item, dict):
            continue
        warnings = item.get("warnings") if isinstance(item.get("warnings"), list) else []
        warning_text = "；".join(str(warning) for warning in warnings) if warnings else "正常"
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('name') or ''), quote=False)}</td>"
            f"<td>{html.escape(str(item.get('kind') or ''), quote=False)}</td>"
            f"<td>{int(item.get('candidate_count') or 0)}</td>"
            f"<td>{html.escape(str(item.get('status') or 'ok'), quote=False)}</td>"
            f"<td>{html.escape(warning_text, quote=False)}</td>"
            "</tr>"
        )
    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        "<title>源健康检查 / Source Health Radar</title>\n"
        "<style>"
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:32px;line-height:1.55;color:#1f2933}"
        "table{border-collapse:collapse;width:100%;margin-top:18px}"
        "th,td{border-bottom:1px solid #e5e7eb;padding:9px 8px;text-align:left;vertical-align:top}"
        "th{background:#f6f8fa}"
        ".bad{color:#b42318;font-weight:600}"
        ".ok{color:#067647;font-weight:600}"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        "<h1>源健康检查 / Source Health Radar</h1>\n"
        f"<p>生成时间：{generated_at}</p>\n"
        f"<p>共检查 {source_count} 个源，提醒数："
        f"<span class=\"{'bad' if warning_count else 'ok'}\">{warning_count}</span></p>\n"
        "<table>\n"
        "<thead><tr><th>源</th><th>类型</th><th>候选数</th><th>状态</th><th>提醒</th></tr></thead>\n"
        "<tbody>\n"
        + "\n".join(rows)
        + "\n</tbody>\n</table>\n"
        "</body>\n</html>\n"
    )


def record_category_names(record: dict[str, object]) -> list[str]:
    return _unique_strings(normalize_category_name(name) for name in classify_record_domains(record))


def sync_duplicate_category_aliases(grouped: dict[str, list[dict[str, object]]]) -> None:
    for alias_group in CATEGORY_ALIAS_GROUPS:
        active_names = [name for name in alias_group if name in grouped]
        if len(active_names) < 2:
            continue
        merged = unique_category_records(record for name in active_names for record in grouped[name])
        for name in active_names:
            grouped[name] = list(merged)


def unique_category_records(records: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[str] = set()
    result: list[dict[str, object]] = []
    for record in records:
        key = category_record_key(record)
        if key in seen:
            continue
        seen.add(key)
        result.append(record)
    return result


def category_record_key(record: dict[str, object]) -> str:
    for field in ("url", "paper_id", "arxiv_id", "title"):
        value = str(record.get(field) or "").strip()
        if value:
            return f"{field}:{value}"
    return f"object:{id(record)}"


def normalize_category_name(name: object) -> str:
    text = str(name).strip()
    if text.startswith("arXiv "):
        return text[len("arXiv ") :].strip()
    return text


def remove_stale_arxiv_category_files(categories_dir: Path, active_slugs: set[str]) -> None:
    for path in categories_dir.glob("arxiv-*.xml"):
        if path.stem not in active_slugs:
            path.unlink()


def remove_stale_report_detail_pages(report_dir: Path) -> None:
    for path in report_dir.glob("*.html"):
        if path.name != "index.html":
            path.unlink()


def summary_with_html_link(summary: str, url: str) -> str:
    return f'{summary}\n\n<a href="{url}">查看网页</a>'


def report_item_url(
    *,
    base_url: str,
    report_path: str,
    fragment: str,
    report: TrendingTopic | KeywordTrend,
) -> str:
    snapshot = asdict(report)
    snapshot.pop("generated_at", None)
    encoded = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    version = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:12]
    return f"{base_url}/reports/{report_path}/index.html?v={version}#{fragment}"


def render_category_opml(category_records: list[dict[str, object]]) -> str:
    outlines = []
    for item in category_records:
        name = str(item["name"])
        url = str(item["url"])
        outlines.append(
            "      "
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
        '    <outline text="Oh My RSS 论文分类" title="Oh My RSS 论文分类">\n'
        + "\n".join(outlines)
        + "\n    </outline>\n"
        "  </body>\n</opml>\n"
    )


def render_subscription_opml(category_records: list[dict[str, object]], public_base_url: str) -> str:
    feed_records = [
        item for item in feed_directory_records(category_records, public_base_url)
        if item["format"] == "rss"
    ]
    outlines = [
        "    "
        f'<outline text="{_xml_attr(item["name"])}" title="{_xml_attr(item["name"])}" '
        f'type="rss" xmlUrl="{_xml_attr(item["url"])}" htmlUrl="{_xml_attr(item["html_url"])}" />'
        for item in feed_records
    ]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<opml version="2.0">\n'
        "  <head>\n"
        "    <title>Oh My RSS subscription bundle</title>\n"
        "  </head>\n"
        "  <body>\n"
        + "\n".join(outlines)
        + "\n  </body>\n</opml>\n"
    )


def feed_directory_records(category_records: list[dict[str, object]], public_base_url: str) -> list[dict[str, object]]:
    base_url = public_base_url.rstrip("/")
    records: list[dict[str, object]] = [
        {
            "name": "Oh My RSS - All Summaries",
            "kind": "summary",
            "format": "rss",
            "url": f"{base_url}/feed.xml",
            "html_url": f"{base_url}/index.html",
        },
        {
            "name": "Oh My RSS - Subscription OPML",
            "kind": "subscription-bundle",
            "format": "opml",
            "url": f"{base_url}/opml.xml",
            "html_url": f"{base_url}/opml.xml",
        },
        {
            "name": "Oh My RSS - Category OPML",
            "kind": "category-bundle",
            "format": "opml",
            "url": f"{base_url}/categories/opml.xml",
            "html_url": f"{base_url}/categories/opml.xml",
        },
        {
            "name": "Oh My RSS - Monthly Research Radar",
            "kind": "monthly-report",
            "format": "rss",
            "url": f"{base_url}/reports/monthly.xml",
            "html_url": f"{base_url}/reports/monthly.xml",
        },
        {
            "name": "Oh My RSS - Trending Research Topics",
            "kind": "topic-report",
            "format": "rss",
            "url": f"{base_url}/reports/trending.xml",
            "html_url": f"{base_url}/reports/trending.xml",
        },
        {
            "name": "Oh My RSS - Trending Research Keywords",
            "kind": "keyword-report",
            "format": "rss",
            "url": f"{base_url}/reports/keywords.xml",
            "html_url": f"{base_url}/reports/keywords.xml",
        },
        {
            "name": "Oh My RSS - Source Health Radar",
            "kind": "source-health-report",
            "format": "rss",
            "url": f"{base_url}/reports/source-health.xml",
            "html_url": f"{base_url}/reports/source-health/index.html",
        },
    ]
    records.extend(
        {
            "name": str(item["name"]),
            "kind": "category",
            "format": "rss",
            "url": str(item["url"]),
            "html_url": str(item["url"]),
            "slug": str(item["slug"]),
            "count": int(item["count"]),
        }
        for item in sorted(category_records, key=lambda record: str(record["name"]))
    )
    return records


def sitemap_url_records(
    records: list[dict[str, object]],
    *,
    monthly_reports: list[MonthlyReport],
    trending_topics: list[TrendingTopic],
    keyword_trends: list[KeywordTrend],
    public_base_url: str,
    generated_at: str,
) -> list[dict[str, str]]:
    base_url = public_base_url.rstrip("/")
    urls: dict[str, str] = {f"{base_url}/index.html": generated_at}

    for record in records:
        if record.get("url"):
            urls[str(record["url"])] = str(record.get("generated_at") or generated_at)

    for report in monthly_reports:
        urls[f"{base_url}/reports/monthly/{report.month}.html"] = report.generated_at

    if trending_topics:
        urls[f"{base_url}/reports/trending/index.html"] = newest_generated_at(
            topic.generated_at for topic in trending_topics
        )

    if keyword_trends:
        urls[f"{base_url}/reports/keywords/index.html"] = newest_generated_at(
            trend.generated_at for trend in keyword_trends
        )

    return [
        {"loc": loc, "lastmod": sitemap_date(lastmod)}
        for loc, lastmod in sorted(urls.items())
    ]


def render_sitemap_xml(urls: list[dict[str, str]]) -> str:
    rows = [
        "  <url>\n"
        f"    <loc>{_xml_attr(item['loc'])}</loc>\n"
        f"    <lastmod>{_xml_attr(item['lastmod'])}</lastmod>\n"
        "  </url>"
        for item in urls
    ]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows)
        + "\n</urlset>\n"
    )


def unique_slug(name: str, used_slugs: dict[str, str]) -> str:
    slug = category_slug(name)
    if slug in used_slugs and used_slugs[slug] != name:
        slug = f"{slug}-{hashlib.sha256(name.encode('utf-8')).hexdigest()[:8]}"
    used_slugs[slug] = name
    return slug


def newest_generated_at(values: Iterable[object]) -> str:
    items = [str(value) for value in values if str(value or "").strip()]
    return max(items) if items else ""


def sitemap_date(value: str) -> str:
    text = str(value or "").strip()
    if len(text) >= 10 and re.match(r"^\d{4}-\d{2}-\d{2}", text):
        return text[:10]
    return ""


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
