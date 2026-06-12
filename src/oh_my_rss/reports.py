from __future__ import annotations

from dataclasses import asdict
import html
import json
import math

from .analytics import KeywordTrend, MonthlyReport, TrendingTopic
from .render import page_css


PALETTE = [
    "#2563eb",
    "#dc2626",
    "#059669",
    "#7c3aed",
    "#d97706",
    "#0891b2",
    "#be123c",
    "#4f46e5",
    "#16a34a",
    "#9333ea",
]


def render_monthly_report_json(report: MonthlyReport) -> str:
    return json.dumps(asdict(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_trending_topic_json(topic: TrendingTopic) -> str:
    return json.dumps(asdict(topic), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_keyword_trend_json(keyword: KeywordTrend) -> str:
    return json.dumps(asdict(keyword), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_monthly_report_html(report: MonthlyReport) -> str:
    direction_rows = table_rows(
        [
            [
                name,
                str(count),
                signed_number(report.direction_growth.get(name, 0)),
                f"{report.direction_scores.get(name, float(count)):.1f}",
            ]
            for name, count in sorted_directions(report)
        ],
        empty_text="暂无方向统计。",
    )
    source_rows = table_rows(
        [[name, str(count)] for name, count in sorted_counts(report.source_counts)],
        empty_text="暂无来源统计。",
    )
    paper_rows = table_rows(
        [
            [
                f'<a href="{_attr(paper.url)}" target="_blank" rel="noopener">{_text(paper.title)}</a>',
                _text(paper.source),
                _text(", ".join(paper.directions)),
                _text(paper.summary_excerpt[:180]),
            ]
            for paper in report.top_papers[:10]
        ],
        empty_text="暂无代表论文。",
        raw_html=True,
    )
    trend_chart = f"assets/{report.month}-trend-animated.svg"
    direction_chart = f"assets/{report.month}-direction-bars.svg"
    source_chart = f"assets/{report.month}-source-donut.svg"
    json_href = f"{report.month}.json"

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_text(report.title)} - Oh My RSS</title>
  <style>{page_css()}{report_css()}</style>
</head>
<body>
<main>
  <p><a class="back" href="../../index.html">返回总结索引</a></p>
  <article>
    <h1>{_text(report.title)}</h1>
    <div class="meta">生成时间：{_text(report.generated_at)} · 本月论文：{report.total_papers}</div>
    <p>{_text(report.summary)}</p>
    <div class="links">
      <a href="../monthly.xml">订阅月报 RSS</a>
      <a href="{_attr(json_href)}">查看统计 JSON</a>
    </div>

    <section class="report-grid">
      <figure>
        <img src="{_attr(trend_chart)}" alt="研究方向趋势动图">
        <figcaption>过去月份热门方向趋势</figcaption>
      </figure>
      <figure>
        <img src="{_attr(direction_chart)}" alt="热门方向柱状图">
        <figcaption>本月热门方向</figcaption>
      </figure>
      <figure>
        <img src="{_attr(source_chart)}" alt="来源分布饼图">
        <figcaption>本月来源分布</figcaption>
      </figure>
    </section>

    <h2>热门方向</h2>
    <table>
      <thead><tr><th>方向</th><th>数量</th><th>环比</th><th>热度分</th></tr></thead>
      <tbody>{direction_rows}</tbody>
    </table>

    <h2>来源分布</h2>
    <table>
      <thead><tr><th>来源</th><th>数量</th></tr></thead>
      <tbody>{source_rows}</tbody>
    </table>

    <h2>代表论文</h2>
    <table>
      <thead><tr><th>论文</th><th>来源</th><th>方向</th><th>摘要片段</th></tr></thead>
      <tbody>{paper_rows}</tbody>
    </table>
  </article>
</main>
</body>
</html>
"""


def render_trending_topic_html(topic: TrendingTopic, *, slug: str | None = None) -> str:
    source_rows = table_rows(
        [[name, str(count)] for name, count in sorted_counts(topic.source_counts)],
        empty_text="暂无来源统计。",
    )
    trend_rows = table_rows(
        [[month, str(count)] for month, count in zip(topic.trend_months, topic.trend_counts, strict=True)],
        empty_text="暂无趋势统计。",
    )
    paper_rows = table_rows(
        [
            [
                f'<a href="{_attr(paper.url)}" target="_blank" rel="noopener">{_text(paper.title)}</a>',
                _text(paper.source),
                _text(paper.generated_at),
                _text(paper.summary_excerpt[:220]),
            ]
            for paper in topic.papers[:20]
        ],
        empty_text="暂无代表论文。",
        raw_html=True,
    )
    json_href = f"{slug or topic_slug_hint(topic.name)}.json"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_text(topic.title)} - Oh My RSS</title>
  <style>{page_css()}{report_css()}</style>
</head>
<body>
<main>
  <p><a class="back" href="../monthly/{_attr(topic.month)}.html">返回月报</a></p>
  <article>
    <h1>{_text(topic.name)}</h1>
    <div class="meta">热点方向 · 月份：{_text(topic.month)} · 论文：{topic.paper_count} · 环比：{signed_number(topic.growth)} · 热度分：{topic.score:.1f}</div>
    <p>{_text(topic.summary)}</p>
    <div class="links">
      <a href="../trending.xml">订阅热点方向 RSS</a>
      <a href="{_attr(json_href)}">查看统计 JSON</a>
    </div>

    <h2>来源分布</h2>
    <table>
      <thead><tr><th>来源</th><th>数量</th></tr></thead>
      <tbody>{source_rows}</tbody>
    </table>

    <h2>趋势月份</h2>
    <table>
      <thead><tr><th>月份</th><th>论文数</th></tr></thead>
      <tbody>{trend_rows}</tbody>
    </table>

    <h2>代表论文</h2>
    <table>
      <thead><tr><th>论文</th><th>来源</th><th>生成时间</th><th>摘要片段</th></tr></thead>
      <tbody>{paper_rows}</tbody>
    </table>
  </article>
</main>
</body>
</html>
"""


def render_keyword_trend_html(keyword: KeywordTrend, *, slug: str | None = None) -> str:
    source_rows = table_rows(
        [[name, str(count)] for name, count in sorted_counts(keyword.source_counts)],
        empty_text="暂无来源统计。",
    )
    trend_rows = table_rows(
        [[month, str(count)] for month, count in zip(keyword.trend_months, keyword.trend_counts, strict=True)],
        empty_text="暂无趋势统计。",
    )
    paper_rows = table_rows(
        [
            [
                f'<a href="{_attr(paper.url)}" target="_blank" rel="noopener">{_text(paper.title)}</a>',
                _text(paper.source),
                _text(", ".join(paper.directions)),
                _text(paper.summary_excerpt[:220]),
            ]
            for paper in keyword.papers[:20]
        ],
        empty_text="暂无代表论文。",
        raw_html=True,
    )
    json_href = f"{slug or topic_slug_hint(keyword.keyword)}.json"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_text(keyword.title)} - Oh My RSS</title>
  <style>{page_css()}{report_css()}</style>
</head>
<body>
<main>
  <p><a class="back" href="../monthly/{_attr(keyword.month)}.html">返回月报</a></p>
  <article>
    <h1>{_text(keyword.keyword)}</h1>
    <div class="meta">关键词趋势 · 月份：{_text(keyword.month)} · 论文：{keyword.paper_count} · 环比：{signed_number(keyword.growth)} · 热度分：{keyword.score:.1f}</div>
    <p>{_text(keyword.summary)}</p>
    <div class="links">
      <a href="../keywords.xml">订阅关键词趋势 RSS</a>
      <a href="{_attr(json_href)}">查看统计 JSON</a>
    </div>

    <h2>来源分布</h2>
    <table>
      <thead><tr><th>来源</th><th>数量</th></tr></thead>
      <tbody>{source_rows}</tbody>
    </table>

    <h2>趋势月份</h2>
    <table>
      <thead><tr><th>月份</th><th>论文数</th></tr></thead>
      <tbody>{trend_rows}</tbody>
    </table>

    <h2>代表论文</h2>
    <table>
      <thead><tr><th>论文</th><th>来源</th><th>方向</th><th>摘要片段</th></tr></thead>
      <tbody>{paper_rows}</tbody>
    </table>
  </article>
</main>
</body>
</html>
"""


def render_direction_bars_svg(report: MonthlyReport) -> str:
    rows = sorted_directions(report)[:10]
    width = 960
    row_height = 44
    chart_left = 300
    chart_width = 560
    height = 110 + max(len(rows), 1) * row_height
    max_count = max((count for _, count in rows), default=1)
    body: list[str] = []
    for idx, (name, count) in enumerate(rows):
        y = 78 + idx * row_height
        bar_width = int(chart_width * count / max_count)
        color = PALETTE[idx % len(PALETTE)]
        body.append(
            f'<text x="24" y="{y + 22}" class="label">{_svg_text(name)}</text>'
            f'<rect x="{chart_left}" y="{y}" width="{bar_width}" height="26" rx="4" fill="{color}">'
            '<animate attributeName="width" from="0" '
            f'to="{bar_width}" dur="800ms" fill="freeze" /></rect>'
            f'<text x="{chart_left + bar_width + 10}" y="{y + 20}" class="value">{count}</text>'
        )
    if not body:
        body.append('<text x="24" y="92" class="label">No data</text>')
    return svg_frame(
        width,
        height,
        "本月热门研究方向",
        "\n".join(body),
    )


def render_source_donut_svg(report: MonthlyReport) -> str:
    rows = sorted_counts(report.source_counts)[:10]
    width = 720
    height = 420
    total = sum(count for _, count in rows) or 1
    radius = 94
    circumference = 2 * math.pi * radius
    offset = 0.0
    segments: list[str] = []
    legends: list[str] = []
    for idx, (name, count) in enumerate(rows):
        color = PALETTE[idx % len(PALETTE)]
        segment = circumference * count / total
        gap = 2 if count < total else 0
        dash = max(segment - gap, 0)
        segments.append(
            f'<circle cx="210" cy="220" r="{radius}" fill="none" stroke="{color}" '
            f'stroke-width="42" stroke-dasharray="{dash:.2f} {circumference - dash:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 210 220)" />'
        )
        offset += segment
        ly = 124 + idx * 28
        legends.append(
            f'<rect x="390" y="{ly - 14}" width="16" height="16" rx="3" fill="{color}" />'
            f'<text x="416" y="{ly}" class="label">{_svg_text(name)} ({count})</text>'
        )
    if not segments:
        segments.append('<circle cx="210" cy="220" r="94" fill="none" stroke="#d1d5db" stroke-width="42" />')
    center_text = (
        f'<text x="210" y="212" text-anchor="middle" class="big">{total}</text>'
        '<text x="210" y="240" text-anchor="middle" class="muted">papers</text>'
    )
    return svg_frame(
        width,
        height,
        "本月来源分布",
        "\n".join(segments + [center_text] + legends),
    )


def render_trend_animated_svg(report: MonthlyReport) -> str:
    width = 960
    height = 520
    left = 96
    top = 94
    chart_width = 780
    chart_height = 300
    months = report.trend_months or [report.month]
    max_value = max(
        [max(values) for values in report.trend_counts.values() if values] + [1],
    )
    body: list[str] = [
        f'<line x1="{left}" y1="{top + chart_height}" x2="{left + chart_width}" '
        f'y2="{top + chart_height}" class="axis" />',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_height}" class="axis" />',
    ]
    for idx, month in enumerate(months):
        x = left + idx * chart_width / max(len(months) - 1, 1)
        body.append(f'<text x="{x:.1f}" y="{top + chart_height + 32}" text-anchor="middle" class="muted">{month}</text>')
    for idx in range(1, 5):
        value = max_value * idx / 4
        y = top + chart_height - value * chart_height / max_value
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_width}" y2="{y:.1f}" class="grid" />')

    for idx, (name, values) in enumerate(report.trend_counts.items()):
        color = PALETTE[idx % len(PALETTE)]
        points: list[str] = []
        for month_idx, value in enumerate(values):
            x = left + month_idx * chart_width / max(len(months) - 1, 1)
            y = top + chart_height - value * chart_height / max_value
            points.append(f"{x:.1f},{y:.1f}")
        if len(points) == 1:
            points.append(points[0])
        body.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" '
            'stroke-width="4" stroke-linecap="round" stroke-linejoin="round" '
            'stroke-dasharray="1200" stroke-dashoffset="1200">'
            '<animate attributeName="stroke-dashoffset" from="1200" to="0" '
            f'begin="{idx * 160}ms" dur="1200ms" fill="freeze" /></polyline>'
        )
        for point in points:
            x, y = point.split(",", maxsplit=1)
            body.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}" />')
        legend_y = 430 + idx * 24
        body.append(
            f'<rect x="{left}" y="{legend_y - 13}" width="14" height="14" rx="3" fill="{color}" />'
            f'<text x="{left + 22}" y="{legend_y}" class="label">{_svg_text(name)}</text>'
        )
    if not report.trend_counts:
        body.append(f'<text x="{left}" y="{top + 120}" class="label">No trend data</text>')
    return svg_frame(width, height, "研究方向趋势动图", "\n".join(body))


def report_css() -> str:
    return """
.report-grid { display: grid; grid-template-columns: 1fr; gap: 18px; margin: 22px 0; }
.report-grid figure { margin: 0; }
.report-grid img { width: 100%; border: 1px solid #e5e7eb; border-radius: 6px; background: #fff; }
.report-grid figcaption { color: #687281; font-size: 13px; margin-top: 6px; }
table { width: 100%; border-collapse: collapse; margin: 14px 0 28px; font-size: 14px; }
th, td { border-top: 1px solid #edf0f2; padding: 9px 8px; text-align: left; vertical-align: top; }
th { color: #374151; font-weight: 650; background: #f8fafc; }
@media (min-width: 900px) { .report-grid { grid-template-columns: 1fr 1fr; } .report-grid figure:first-child { grid-column: 1 / -1; } }
@media (prefers-color-scheme: dark) {
  .report-grid img { border-color: #344050; }
  th, td { border-color: #28313c; }
  th { background: #1d2530; color: #d7dee8; }
}
"""


def svg_frame(width: int, height: int, title: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
  <title>{_svg_text(title)}</title>
  <style>
    .title {{ font: 700 26px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #111827; }}
    .label {{ font: 500 15px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #374151; }}
    .value {{ font: 700 15px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #111827; }}
    .muted {{ font: 500 13px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #6b7280; }}
    .big {{ font: 800 36px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #111827; }}
    .axis {{ stroke: #9ca3af; stroke-width: 1.5; }}
    .grid {{ stroke: #e5e7eb; stroke-width: 1; }}
  </style>
  <rect width="100%" height="100%" fill="#ffffff" rx="8" />
  <text x="24" y="42" class="title">{_svg_text(title)}</text>
  {body}
</svg>
"""


def sorted_directions(report: MonthlyReport) -> list[tuple[str, int]]:
    return sorted(
        report.direction_counts.items(),
        key=lambda item: (-report.direction_scores.get(item[0], item[1]), -item[1], item[0]),
    )


def sorted_counts(counts: dict[str, int]) -> list[tuple[str, int]]:
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def table_rows(rows: list[list[str]], *, empty_text: str, raw_html: bool = False) -> str:
    if not rows:
        return f'<tr><td colspan="4">{_text(empty_text)}</td></tr>'
    rendered = []
    for row in rows:
        cells = []
        for cell in row:
            value = cell if raw_html else _text(cell)
            cells.append(f"<td>{value}</td>")
        rendered.append(f"<tr>{''.join(cells)}</tr>")
    return "".join(rendered)


def signed_number(value: int) -> str:
    if value > 0:
        return f"+{value}"
    return str(value)


def topic_slug_hint(name: str) -> str:
    ascii_text = re_sub_non_ascii(name).lower()
    slug = "-".join(part for part in ascii_text.split("-") if part)
    return slug or "topic"


def re_sub_non_ascii(value: str) -> str:
    output = []
    previous_dash = False
    for char in value:
        if char.isascii() and char.isalnum():
            output.append(char)
            previous_dash = False
        elif not previous_dash:
            output.append("-")
            previous_dash = True
    return "".join(output).strip("-")


def _text(value: object) -> str:
    return html.escape(str(value), quote=False)


def _attr(value: object) -> str:
    return html.escape(str(value), quote=True)


def _svg_text(value: object) -> str:
    return html.escape(str(value), quote=False)
