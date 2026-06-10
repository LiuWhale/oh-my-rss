from __future__ import annotations

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
    markdown: str,
    generated_at: str,
) -> str:
    summary_html = markdown_to_html(markdown)
    feed_text = ", ".join(feeds) if feeds else "FreshRSS"
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
    <div class="meta">arXiv: {html.escape(arxiv_id)} · 生成时间：{html.escape(generated_at)}<br>来源：{html.escape(feed_text)}</div>
    <div class="links">
      <a href="{html.escape(abs_url)}" target="_blank" rel="noopener">arXiv 页面</a>
      <a href="{html.escape(pdf_url)}" target="_blank" rel="noopener">PDF</a>
    </div>
    {summary_html}
  </article>
</main>
</body>
</html>
"""


def render_index_html(records: list[dict[str, object]], generated_at: str) -> str:
    rows: list[str] = []
    for item in records[:200]:
        url = html.escape(str(item["url"]))
        title = html.escape(str(item["title"]))
        arxiv_id = html.escape(str(item["arxiv_id"]))
        created = html.escape(str(item.get("generated_at", "")))
        feeds = ", ".join(item.get("feed_names", []) or [])
        suffix = f" · {html.escape(feeds)}" if feeds else ""
        rows.append(
            f'<li><div class="paper-title"><a href="{url}">{title}</a></div>'
            f'<div class="paper-meta">arXiv: {arxiv_id} · {created}{suffix}</div></li>'
        )
    if not rows:
        rows.append("<li>还没有生成论文总结。</li>")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>arXiv Codex 中文总结</title>
  <style>{page_css()}</style>
</head>
<body>
<main>
  <section class="index">
    <h1>arXiv Codex 中文总结</h1>
    <div class="meta">自动从 FreshRSS 读取 arXiv 新条目，由 Codex CLI 生成中文总结。更新时间：{html.escape(generated_at)}</div>
    <ul class="paper-list">{''.join(rows)}</ul>
  </section>
</main>
</body>
</html>
"""
