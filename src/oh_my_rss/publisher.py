from __future__ import annotations

from pathlib import Path
import hashlib
import html
import json
import re
import shutil
import unicodedata

from .analytics import KeywordTrend, MonthlyReport, TrendingTopic
from .arxiv import Paper
from .domains import classify_research_domains
from .reports import (
    render_direction_bars_svg,
    render_keyword_trend_html,
    render_keyword_trend_json,
    render_monthly_report_html,
    render_monthly_report_json,
    render_source_donut_svg,
    render_trend_animated_svg,
    render_trending_topic_html,
    render_trending_topic_json,
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
    done.sort(key=lambda item: str(item.get("generated_at", "")), reverse=True)
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
    done.sort(key=lambda item: str(item.get("generated_at", "")), reverse=True)
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

    index_records: list[dict[str, object]] = []
    feed_records: list[dict[str, object]] = []
    for topic in topics[:20]:
        slug = category_slug(topic.name)
        if slug in used_slugs and used_slugs[slug] != topic.name:
            slug = f"{slug}-{hashlib.sha256(topic.name.encode('utf-8')).hexdigest()[:8]}"
        used_slugs[slug] = topic.name

        html_path = trending_dir / f"{slug}.html"
        json_path = trending_dir / f"{slug}.json"
        html_path.write_text(render_trending_topic_html(topic, slug=slug), encoding="utf-8")
        json_path.write_text(render_trending_topic_json(topic), encoding="utf-8")

        url = f"{base_url}/reports/trending/{slug}.html"
        record = {
            "title": topic.title,
            "url": url,
            "generated_at": topic.generated_at,
            "feed_names": ["Trending Research Topics"],
            "summary_excerpt": topic.summary,
            "name": topic.name,
            "month": topic.month,
            "paper_count": topic.paper_count,
            "growth": topic.growth,
            "score": topic.score,
            "slug": slug,
        }
        index_records.append(record)
        feed_records.append(record)

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
        channel_link=feed_records[0]["url"] if feed_records else f"{base_url}/index.html",
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

    index_records: list[dict[str, object]] = []
    feed_records: list[dict[str, object]] = []
    for trend in trends[:20]:
        slug = category_slug(trend.keyword)
        if slug in used_slugs and used_slugs[slug] != trend.keyword:
            slug = f"{slug}-{hashlib.sha256(trend.keyword.encode('utf-8')).hexdigest()[:8]}"
        used_slugs[slug] = trend.keyword

        html_path = keywords_dir / f"{slug}.html"
        json_path = keywords_dir / f"{slug}.json"
        html_path.write_text(render_keyword_trend_html(trend, slug=slug), encoding="utf-8")
        json_path.write_text(render_keyword_trend_json(trend), encoding="utf-8")

        url = f"{base_url}/reports/keywords/{slug}.html"
        record = {
            "title": trend.title,
            "url": url,
            "generated_at": trend.generated_at,
            "feed_names": ["Trending Research Keywords"],
            "summary_excerpt": trend.summary,
            "keyword": trend.keyword,
            "month": trend.month,
            "paper_count": trend.paper_count,
            "growth": trend.growth,
            "score": trend.score,
            "slug": slug,
        }
        index_records.append(record)
        feed_records.append(record)

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
        channel_link=feed_records[0]["url"] if feed_records else f"{base_url}/index.html",
        include_item_categories=False,
    )
    reports_root.mkdir(parents=True, exist_ok=True)
    (reports_root / "keywords.xml").write_text(feed_xml, encoding="utf-8")
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

    used_topic_slugs: dict[str, str] = {}
    for topic in trending_topics:
        slug = unique_slug(topic.name, used_topic_slugs)
        urls[f"{base_url}/reports/trending/{slug}.html"] = topic.generated_at

    used_keyword_slugs: dict[str, str] = {}
    for trend in keyword_trends:
        slug = unique_slug(trend.keyword, used_keyword_slugs)
        urls[f"{base_url}/reports/keywords/{slug}.html"] = trend.generated_at

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
