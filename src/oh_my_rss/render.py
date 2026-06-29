from __future__ import annotations

from datetime import datetime, timezone
from email.utils import format_datetime
import html
import re


def render_inline(text: str) -> str:
    code_spans: list[str] = []

    def keep_code(match: re.Match[str]) -> str:
        code_spans.append(f"<code>{html.escape(match.group(1), quote=True)}</code>")
        return f"@@CODE{len(code_spans) - 1}@@"

    text = re.sub(r"`([^`]+)`", keep_code, text)
    escaped = html.escape(text, quote=True)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        escaped,
    )
    for idx, code_html in enumerate(code_spans):
        escaped = escaped.replace(f"@@CODE{idx}@@", code_html)
    return escaped


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    in_list = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            out.append("<p>{}</p>".format(render_inline(" ".join(paragraph))))
            paragraph = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_paragraph()
            close_list()
            continue
        if line.startswith("# "):
            flush_paragraph()
            close_list()
            out.append(f"<h1>{render_inline(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            flush_paragraph()
            close_list()
            out.append(f"<h2>{render_inline(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            flush_paragraph()
            close_list()
            out.append(f"<h3>{render_inline(line[4:].strip())}</h3>")
        elif re.match(r"^[-*]\s+", line):
            flush_paragraph()
            if not in_list:
                out.append("<ul>")
                in_list = True
            item_text = re.sub(r"^[-*]\s+", "", line)
            out.append(f"<li>{render_inline(item_text)}</li>")
        else:
            paragraph.append(line)
    flush_paragraph()
    close_list()
    return "\n".join(out)


def page_css() -> str:
    return """
:root { color-scheme: light dark; }
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.62; color: #1f2933; background: #f7f8fa; }
main { max-width: 860px; margin: 0 auto; padding: 42px 20px 72px; }
article, .index { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 28px; }
h1 { font-size: 30px; line-height: 1.25; margin: 0 0 18px; }
h2 { font-size: 20px; margin-top: 28px; border-top: 1px solid #edf0f2; padding-top: 20px; }
a { color: #0f5fb8; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.92em; background: #f1f4f7; border: 1px solid #e2e8f0; border-radius: 4px; padding: 1px 4px; }
.meta { color: #5d6673; font-size: 14px; margin-bottom: 18px; }
.links { display: flex; flex-wrap: wrap; gap: 10px; margin: 18px 0 24px; }
.links a, .back { display: inline-block; border: 1px solid #d7dde4; border-radius: 6px; padding: 6px 10px; text-decoration: none; background: #fbfcfd; }
.hero-image { margin: 18px 0 26px; }
.hero-image img { display: block; width: 100%; max-height: 680px; object-fit: contain; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; }
.hero-image figcaption { color: #687281; font-size: 13px; margin-top: 6px; }
.paper-list { list-style: none; padding: 0; margin: 18px 0 0; }
.paper-list li { padding: 16px 0; border-top: 1px solid #edf0f2; }
.paper-title { font-weight: 650; }
.paper-meta { color: #687281; font-size: 13px; margin-top: 4px; }
@media (prefers-color-scheme: dark) {
  body { background: #11161d; color: #e7edf5; }
  article, .index { background: #171d25; border-color: #2b3541; }
  h2, .paper-list li { border-color: #28313c; }
  a { color: #8ab8ff; }
  code { background: #222b36; border-color: #344050; }
  .meta, .paper-meta { color: #aab4c0; }
  .links a, .back { background: #1d2530; border-color: #374151; }
  .hero-image img { background: #fff; border-color: #344050; }
}
"""


def mathjax_scripts() -> str:
    return """
  <script>
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true
      },
      options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
      }
    };
  </script>
  <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
"""


def render_detail_html(
    *,
    title: str,
    arxiv_id: str,
    feeds: list[str],
    abs_url: str,
    pdf_url: str,
    source_label: str = "arXiv",
    hero_image_url: str = "",
    markdown: str,
    generated_at: str,
) -> str:
    summary_html = markdown_to_html(markdown)
    feed_text = ", ".join(feeds) if feeds else "FreshRSS"
    hero_html = ""
    if hero_image_url:
        hero_html = (
            '<figure class="hero-image">'
            f'<img src="{html.escape(hero_image_url, quote=True)}" alt="论文首页主图">'
            "<figcaption>论文首页预览</figcaption>"
            "</figure>"
        )
    page_label = "arXiv 页面" if source_label == "arXiv" else "原文页面"
    pdf_link = ""
    if pdf_url:
        pdf_link = f'<a href="{html.escape(pdf_url)}" target="_blank" rel="noopener">PDF</a>'
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} - Codex 中文总结</title>
  <style>{page_css()}</style>
{mathjax_scripts()}</head>
<body>
<main>
  <p><a class="back" href="./index.html">返回总结索引</a></p>
  <article>
    <div class="meta">{html.escape(source_label)}: {html.escape(arxiv_id)} · 生成时间：{html.escape(generated_at)}<br>来源：{html.escape(feed_text)}</div>
    <div class="links">
      <a href="{html.escape(abs_url)}" target="_blank" rel="noopener">{page_label}</a>
      {pdf_link}
    </div>
    {hero_html}
    {summary_html}
  </article>
</main>
</body>
</html>
"""


def render_index_html(records: list[dict[str, object]], generated_at: str, public_base_url: str = "") -> str:
    subscription_links = index_subscription_links(public_base_url)
    alternate_links = "\n".join(
        [
            (
                f'  <link rel="alternate" type="application/rss+xml" title="{html.escape(item["title"], quote=True)}" '
                f'href="{html.escape(item["url"], quote=True)}">'
            )
            for item in subscription_links
            if item["type"] == "rss"
        ]
        + [
            (
                f'  <link rel="alternate" type="text/x-opml" title="{html.escape(item["title"], quote=True)}" '
                f'href="{html.escape(item["url"], quote=True)}">'
            )
            for item in subscription_links
            if item["type"] == "opml"
        ]
    )
    subscription_html = "".join(
        f'<a href="{html.escape(item["url"], quote=True)}">{html.escape(item["label"], quote=False)}</a>'
        for item in subscription_links
    )
    rows: list[str] = []
    for item in records[:200]:
        url = html.escape(str(item["url"]))
        title = html.escape(str(item["title"]))
        paper_id = html.escape(str(item.get("paper_id") or item.get("arxiv_id") or ""))
        source_label = html.escape(record_source_label(item))
        created = html.escape(str(item.get("generated_at", "")))
        feeds = ", ".join(item.get("feed_names", []) or [])
        suffix = f" · {html.escape(feeds)}" if feeds else ""
        rows.append(
            f'<li><div class="paper-title"><a href="{url}">{title}</a></div>'
            f'<div class="paper-meta">{source_label}: {paper_id} · {created}{suffix}</div></li>'
        )
    if not rows:
        rows.append("<li>还没有生成论文总结。</li>")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Oh My RSS 中文总结</title>
{alternate_links}
  <style>{page_css()}</style>
</head>
<body>
<main>
  <section class="index">
    <h1>Oh My RSS 中文总结</h1>
    <div class="meta">自动从 FreshRSS 读取论文 RSS 条目，由 Codex CLI 生成中文总结。更新时间：{html.escape(generated_at)}</div>
    <div class="links">{subscription_html}</div>
    <ul class="paper-list">{''.join(rows)}</ul>
  </section>
</main>
</body>
</html>
"""


def index_subscription_links(public_base_url: str) -> list[dict[str, str]]:
    def url(path: str) -> str:
        base = public_base_url.rstrip("/")
        return f"{base}/{path}" if base else path

    return [
        {"label": "全部总结 RSS", "title": "Oh My RSS", "type": "rss", "url": url("feed.xml")},
        {
            "label": "完整 OPML",
            "title": "Oh My RSS subscription bundle",
            "type": "opml",
            "url": url("opml.xml"),
        },
        {
            "label": "分类 OPML",
            "title": "Oh My RSS category feeds",
            "type": "opml",
            "url": url("categories/opml.xml"),
        },
        {
            "label": "月报 RSS",
            "title": "Oh My RSS Monthly Research Radar",
            "type": "rss",
            "url": url("reports/monthly.xml"),
        },
        {
            "label": "热点方向 RSS",
            "title": "Oh My RSS Trending Research Topics",
            "type": "rss",
            "url": url("reports/trending.xml"),
        },
        {
            "label": "关键词趋势 RSS",
            "title": "Oh My RSS Trending Research Keywords",
            "type": "rss",
            "url": url("reports/keywords.xml"),
        },
    ]


def render_rss_xml(
    records: list[dict[str, object]],
    *,
    generated_at: str,
    public_base_url: str,
    title: str = "Oh My RSS",
    description: str = "RSS-driven paper summaries generated by Oh My RSS.",
    feed_path: str = "feed.xml",
    channel_link: str | None = None,
    include_item_categories: bool = True,
    item_category: str | None = None,
) -> str:
    base_url = public_base_url.rstrip("/")
    channel_link = channel_link or f"{base_url}/index.html"
    feed_url = f"{base_url}/{feed_path.lstrip('/')}"
    done = [record for record in records if record.get("url")]
    done.sort(key=record_sort_key, reverse=True)

    items = []
    for record in done[:200]:
        item_title = str(record.get("title") or record.get("arxiv_id") or "Untitled paper")
        item_url = str(record["url"])
        paper_id = str(record.get("paper_id") or record.get("arxiv_id") or "")
        source_label = record_source_label(record)
        published = record_pubdate_value(record, generated_at)
        feeds = ", ".join(record.get("feed_names", []) or [])
        summary_excerpt = str(record.get("summary_excerpt") or "").strip()
        if summary_excerpt:
            item_description = summary_excerpt
        else:
            item_description = f"{source_label}: {paper_id}"
            if feeds:
                item_description += f" · 来源：{feeds}"
        if item_category:
            category_values = [item_category]
        elif include_item_categories:
            category_values = _unique_strings(record.get("feed_names", []) or [])
        else:
            category_values = []
        categories = "\n".join(f"      <category>{_xml(category)}</category>" for category in category_values)
        categories = f"\n{categories}" if categories else ""
        items.append(
            "    <item>\n"
            f"      <title>{_xml(item_title)}</title>\n"
            f"      <link>{_xml(item_url)}</link>\n"
            f"      <guid isPermaLink=\"true\">{_xml(item_url)}</guid>\n"
            f"      <description>{_xml(item_description)}</description>\n"
            f"      <pubDate>{_xml(_rss_date(published))}</pubDate>\n"
            f"{categories}\n"
            "    </item>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        f"    <title>{_xml(title)}</title>\n"
        f"    <link>{_xml(channel_link)}</link>\n"
        f"    <description>{_xml(description)}</description>\n"
        f"    <language>zh-CN</language>\n"
        f"    <lastBuildDate>{_xml(_rss_date(generated_at))}</lastBuildDate>\n"
        f"    <atom:link href=\"{_xml(feed_url)}\" rel=\"self\" type=\"application/rss+xml\" />\n"
        + "\n".join(items)
        + "\n  </channel>\n</rss>\n"
    )


SOURCE_TIME_KEYS = (
    "source_published_at",
    "source_updated_at",
    "published_at",
    "entry_published_at",
    "entry_updated_at",
)

FALLBACK_TIME_KEYS = (
    "generated_at",
    "updated_at",
)


def record_sort_key(record: dict[str, object]) -> tuple[int, float]:
    source_time = _parse_record_datetime(_first_record_value(record, SOURCE_TIME_KEYS))
    if source_time is not None:
        return (1, source_time.timestamp())

    fallback_time = _parse_record_datetime(_first_record_value(record, FALLBACK_TIME_KEYS))
    return (0, fallback_time.timestamp() if fallback_time else 0.0)


def record_pubdate_value(record: dict[str, object], fallback: object = "") -> object:
    release_time = _first_record_value(record, FALLBACK_TIME_KEYS)
    if release_time:
        return release_time
    source_time = _first_record_value(record, SOURCE_TIME_KEYS)
    return source_time or fallback


def _first_record_value(record: dict[str, object], keys: tuple[str, ...]) -> object:
    for key in keys:
        value = record.get(key)
        if value:
            return value
    return ""


def _rss_date(value: object) -> str:
    parsed = _parse_record_datetime(value)
    if parsed is None:
        parsed = datetime.now(timezone.utc)
    return format_datetime(parsed.astimezone(timezone.utc), usegmt=True)


def _parse_record_datetime(value: object) -> datetime | None:
    try:
        if isinstance(value, int | float):
            parsed = datetime.fromtimestamp(float(value), timezone.utc)
        else:
            parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _xml(value: str) -> str:
    return html.escape(value, quote=True)


def _unique_strings(values: list[object]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def record_source_label(record: dict[str, object]) -> str:
    source_kind = str(record.get("source_kind") or "").strip()
    if source_kind:
        return source_kind
    paper_id = str(record.get("paper_id") or record.get("arxiv_id") or "")
    if paper_id.startswith("doi:"):
        return "DOI"
    if paper_id.startswith("url:"):
        return "RSS"
    if paper_id:
        return "arXiv"
    return "Paper"
