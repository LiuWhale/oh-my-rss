from __future__ import annotations

from dataclasses import asdict
import html
import json
import math

from .analytics import KeywordTrend, MonthlyReport, PaperReference, TrendingTopic
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


def render_report_workspace(
    *,
    mode: str,
    papers: list[PaperReference],
    domain_choices: list[tuple[str, int]] | None = None,
    keyword_choices: list[tuple[str, int]] | None = None,
    keyword_memberships: dict[str, list[str]] | None = None,
    overview: str = "",
) -> str:
    domain_choices = domain_choices or []
    keyword_choices = keyword_choices or []
    keyword_memberships = keyword_memberships or {}
    source_choices = sorted({paper.source for paper in papers})

    source_options = "".join(
        f'<option value="{_attr(source)}">{_text(source)}</option>' for source in source_choices
    )
    domain_filter = ""
    if domain_choices:
        domain_options = "".join(
            f'<option value="{_attr(name)}">{_text(name)} ({count})</option>'
            for name, count in domain_choices
        )
        domain_filter = f"""
      <label>领域
        <select data-report-filter="domain">
          <option value="">全部领域</option>
          {domain_options}
        </select>
      </label>"""
    keyword_filter = ""
    if keyword_choices:
        keyword_options = "".join(
            f'<option value="{_attr(name)}">{_text(name)} ({count})</option>'
            for name, count in keyword_choices
        )
        keyword_filter = f"""
      <label>关键词
        <select data-report-filter="keyword">
          <option value="">全部关键词</option>
          {keyword_options}
        </select>
      </label>"""

    paper_cards = render_report_paper_cards(papers, keyword_memberships)
    overview_html = f'<div class="report-group-grid">{overview}</div>' if overview else ""
    return f"""
    <section class="report-workspace" data-report-workspace="{_attr(mode)}">
      {overview_html}
      <div class="report-toolbar" aria-label="论文筛选">
        <label class="report-search">检索
          <input type="search" data-report-query="q" placeholder="标题、总结、来源或领域">
        </label>
        <label>来源
          <select data-report-filter="source">
            <option value="">全部来源</option>
            {source_options}
          </select>
        </label>
        {domain_filter}
        {keyword_filter}
        <button type="button" class="report-clear" data-report-clear>清除筛选</button>
      </div>
      <div class="report-result-meta" data-report-result-meta></div>
      <div class="report-paper-list" data-report-paper-list>
        {paper_cards}
      </div>
      <div class="report-pager" data-report-pager>
        <button type="button" data-report-page="previous" aria-label="上一页">上一页</button>
        <span data-report-page-status></span>
        <button type="button" data-report-page="next" aria-label="下一页">下一页</button>
      </div>
    </section>
    {report_workspace_script()}
"""


def render_report_paper_cards(
    papers: list[PaperReference],
    keyword_memberships: dict[str, list[str]],
) -> str:
    if not papers:
        return '<p class="report-empty">暂无可展示的论文。</p>'

    cards: list[str] = []
    for paper in papers:
        keywords = keyword_memberships.get(paper.url, [])
        search_text = " ".join(
            [paper.title, paper.source, *paper.directions, *keywords, paper.summary_excerpt]
        ).casefold()
        domains = "||".join(paper.directions)
        keyword_values = "||".join(keywords)
        date = paper.published_at or paper.generated_at
        metadata = [paper.source]
        if date:
            metadata.append(f"公开：{date}")
        if paper.directions:
            metadata.append("领域：" + " / ".join(paper.directions))
        if keywords:
            metadata.append("关键词：" + " / ".join(keywords))
        cards.append(
            f'<article class="report-paper" data-report-paper '
            f'data-report-paper-url="{_attr(paper.url)}" '
            f'data-report-paper-source="{_attr(paper.source)}" '
            f'data-report-paper-domains="{_attr(domains)}" '
            f'data-report-paper-keywords="{_attr(keyword_values)}" '
            f'data-report-search="{_attr(search_text)}">'
            f'<a class="report-paper-title" href="{_attr(paper.url)}">{_text(paper.title)}</a>'
            f'<div class="report-paper-meta">{_text(" · ".join(metadata))}</div>'
            f'<p>{_text(paper.summary_excerpt)}</p>'
            "</article>"
        )
    return "\n".join(cards)


def report_workspace_script() -> str:
    return """
<script>
(() => {
  const root = document.querySelector("[data-report-workspace]");
  if (!root) return;
  const query = root.querySelector("[data-report-query]");
  const source = root.querySelector('[data-report-filter="source"]');
  const domain = root.querySelector('[data-report-filter="domain"]');
  const keyword = root.querySelector('[data-report-filter="keyword"]');
  const papers = [...root.querySelectorAll("[data-report-paper]")];
  const resultMeta = root.querySelector("[data-report-result-meta]");
  const pageStatus = root.querySelector("[data-report-page-status]");
  const pageSize = 30;
  const params = new URLSearchParams(window.location.search);
  const state = {
    q: params.get("q") || "",
    source: params.get("source") || "",
    domain: params.get("domain") || "",
    keyword: params.get("keyword") || "",
    page: Math.max(1, Number.parseInt(params.get("page") || "1", 10) || 1),
    legacyHash: window.location.hash.replace(/^#/, ""),
  };

  const setControl = (control, value) => {
    if (control && [...control.options].some(option => option.value === value)) control.value = value;
  };
  const applyLegacyHash = () => {
    if (!state.legacyHash) return;
    const target = [...document.querySelectorAll("[data-legacy-fragment]")]
      .find(element => element.dataset.legacyFragment === state.legacyHash);
    if (!target) return;
    if (target.dataset.reportDomain) state.domain = target.dataset.reportDomain;
    if (target.dataset.reportKeyword) state.keyword = target.dataset.reportKeyword;
  };
  const values = (item, name) => (item.dataset[name] || "").split("||").filter(Boolean);
  const matching = () => papers.filter(item => {
    const text = item.dataset.reportSearch || "";
    return (!state.q || text.includes(state.q.casefold()))
      && (!state.source || item.dataset.reportPaperSource === state.source)
      && (!state.domain || values(item, "reportPaperDomains").includes(state.domain))
      && (!state.keyword || values(item, "reportPaperKeywords").includes(state.keyword));
  });
  const writeUrl = () => {
    const url = new URL(window.location.href);
    for (const key of ["q", "source", "domain", "keyword", "page"]) url.searchParams.delete(key);
    for (const key of ["q", "source", "domain", "keyword"]) {
      if (state[key]) url.searchParams.set(key, state[key]);
    }
    if (state.page > 1) url.searchParams.set("page", String(state.page));
    url.hash = state.legacyHash ? `#${state.legacyHash}` : "";
    window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
  };
  const render = () => {
    setControl(source, state.source);
    setControl(domain, state.domain);
    setControl(keyword, state.keyword);
    if (query) query.value = state.q;
    const matches = matching();
    const totalPages = Math.max(1, Math.ceil(matches.length / pageSize));
    state.page = Math.min(state.page, totalPages);
    const start = (state.page - 1) * pageSize;
    const visible = new Set(matches.slice(start, start + pageSize));
    papers.forEach(item => { item.hidden = !visible.has(item); });
    resultMeta.textContent = `显示 ${matches.length ? start + 1 : 0}-${Math.min(start + pageSize, matches.length)} / ${matches.length} 篇论文`;
    pageStatus.textContent = `${state.page} / ${totalPages}`;
    root.querySelector('[data-report-page="previous"]').disabled = state.page <= 1;
    root.querySelector('[data-report-page="next"]').disabled = state.page >= totalPages;
    document.querySelectorAll("[data-report-domain], [data-report-keyword], [data-report-source]")
      .forEach(button => {
        const active = (button.dataset.reportDomain && button.dataset.reportDomain === state.domain)
          || (button.dataset.reportKeyword && button.dataset.reportKeyword === state.keyword)
          || (button.dataset.reportSource && button.dataset.reportSource === state.source);
        button.setAttribute("aria-pressed", String(active));
      });
    writeUrl();
  };
  const resetPage = () => { state.page = 1; };
  if (query) query.addEventListener("input", event => { state.q = event.target.value.trim(); state.legacyHash = ""; resetPage(); render(); });
  [[source, "source"], [domain, "domain"], [keyword, "keyword"]].forEach(([control, key]) => {
    if (control) control.addEventListener("change", event => { state[key] = event.target.value; state.legacyHash = ""; resetPage(); render(); });
  });
  document.querySelectorAll("[data-report-domain], [data-report-keyword], [data-report-source]")
    .forEach(button => button.addEventListener("click", () => {
      if (button.dataset.reportDomain) state.domain = button.dataset.reportDomain;
      if (button.dataset.reportKeyword) state.keyword = button.dataset.reportKeyword;
      if (button.dataset.reportSource) state.source = button.dataset.reportSource;
      state.legacyHash = button.dataset.legacyFragment || "";
      resetPage();
      render();
      root.scrollIntoView({ behavior: "smooth", block: "start" });
    }));
  root.querySelector("[data-report-clear]").addEventListener("click", () => {
    Object.assign(state, { q: "", source: "", domain: "", keyword: "", page: 1, legacyHash: "" });
    render();
  });
  root.querySelectorAll("[data-report-page]").forEach(button => button.addEventListener("click", () => {
    state.page += button.dataset.reportPage === "next" ? 1 : -1;
    render();
    root.scrollIntoView({ behavior: "smooth", block: "start" });
  }));
  applyLegacyHash();
  render();
})();
</script>
"""


def unique_papers(papers: list[PaperReference]) -> list[PaperReference]:
    by_url = {paper.url: paper for paper in papers}
    return sorted(by_url.values(), key=lambda paper: paper.generated_at, reverse=True)


def render_monthly_report_html(report: MonthlyReport) -> str:
    direction_rows = table_rows(
        [
            [
                (
                    f'<button type="button" class="report-filter-button" '
                    f'data-report-domain="{_attr(name)}">{_text(name)}</button>'
                ),
                str(count),
                signed_number(report.direction_growth.get(name, 0)),
                f"{report.direction_scores.get(name, float(count)):.1f}",
            ]
            for name, count in sorted_directions(report)
        ],
        empty_text="暂无方向统计。",
        raw_html=True,
    )
    source_rows = table_rows(
        [
            [
                (
                    f'<button type="button" class="report-filter-button" '
                    f'data-report-source="{_attr(name)}">{_text(name)}</button>'
                ),
                str(count),
            ]
            for name, count in sorted_counts(report.source_counts)
        ],
        empty_text="暂无来源统计。",
        raw_html=True,
    )
    trend_chart = f"assets/{report.month}-trend-animated.svg"
    direction_chart = f"assets/{report.month}-direction-bars.svg"
    source_chart = f"assets/{report.month}-source-donut.svg"

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

    <h2>论文</h2>
    {render_report_workspace(
        mode="monthly",
        papers=report.papers,
        domain_choices=sorted_directions(report),
    )}
  </article>
</main>
</body>
</html>
"""


def render_trending_topic_html(topic: TrendingTopic, *, slug: str | None = None) -> str:
    section = render_trending_topic_section(topic, slug=slug)
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
    <div class="links">
      <a href="../trending.xml">订阅热点方向 RSS</a>
      <a href="{_attr(json_href)}">查看统计 JSON</a>
    </div>
    {section}
  </article>
</main>
</body>
</html>
"""


def render_trending_topics_index_html(topics: list[tuple[TrendingTopic, str]]) -> str:
    month = topics[0][0].month if topics else ""
    generated_at = topics[0][0].generated_at if topics else ""
    topic_cards = "\n".join(
        f'''<section id="topic-{_attr(slug)}" class="report-group-card"
                    data-legacy-fragment="topic-{_attr(slug)}"
                    data-report-domain="{_attr(topic.name)}">
              <button type="button" data-report-domain="{_attr(topic.name)}"
                      data-legacy-fragment="topic-{_attr(slug)}">{_text(topic.name)}</button>
              <div class="report-group-meta">{topic.paper_count} 篇 · 环比 {signed_number(topic.growth)} · 热度 {topic.score:.1f}</div>
              <div class="report-group-meta">趋势月份：{_text(' / '.join(topic.trend_months))}</div>
            </section>'''
        for topic, slug in topics
    )
    papers = unique_papers([paper for topic, _ in topics for paper in topic.papers])
    topic_choices = [(topic.name, topic.paper_count) for topic, _ in topics]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>热点研究方向 - Oh My RSS</title>
  <style>{page_css()}{report_css()}</style>
</head>
<body>
<main>
  <p><a class="back" href="../../index.html">返回总结索引</a></p>
  <article>
    <h1>热点方向</h1>
    <div class="meta">月份：{_text(month)} · 生成时间：{_text(generated_at)}</div>
    <p>按研究领域查看当前论文流中的热点与对应中文总结。</p>
    {render_report_workspace(
        mode="trending",
        papers=papers,
        domain_choices=topic_choices,
        overview=topic_cards,
    )}
  </article>
</main>
</body>
</html>
"""


def render_trending_topic_section(topic: TrendingTopic, *, slug: str | None = None) -> str:
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
    section_id = f"topic-{slug or topic_slug_hint(topic.name)}"
    return f"""
    <section id="{_attr(section_id)}" class="report-section">
    <h1>{_text(topic.name)}</h1>
    <div class="meta">热点方向 · 月份：{_text(topic.month)} · 论文：{topic.paper_count} · 环比：{signed_number(topic.growth)} · 热度分：{topic.score:.1f}</div>
    <p>{_text(topic.summary)}</p>

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
    </section>
"""


def render_keyword_trend_html(keyword: KeywordTrend, *, slug: str | None = None) -> str:
    section = render_keyword_trend_section(keyword, slug=slug)
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
    <div class="links">
      <a href="../keywords.xml">订阅关键词趋势 RSS</a>
      <a href="{_attr(json_href)}">查看统计 JSON</a>
    </div>
    {section}
  </article>
</main>
</body>
</html>
"""


def render_keyword_trends_index_html(keywords: list[tuple[KeywordTrend, str]]) -> str:
    month = keywords[0][0].month if keywords else ""
    generated_at = keywords[0][0].generated_at if keywords else ""
    keyword_cards = "\n".join(
        f'''<section id="keyword-{_attr(slug)}" class="report-group-card"
                    data-legacy-fragment="keyword-{_attr(slug)}"
                    data-report-keyword="{_attr(keyword.keyword)}">
              <button type="button" data-report-keyword="{_attr(keyword.keyword)}"
                      data-legacy-fragment="keyword-{_attr(slug)}">{_text(keyword.keyword)}</button>
              <div class="report-group-meta">{keyword.paper_count} 篇 · 环比 {signed_number(keyword.growth)} · 热度 {keyword.score:.1f}</div>
              <div class="report-group-meta">趋势月份：{_text(' / '.join(keyword.trend_months))}</div>
            </section>'''
        for keyword, slug in keywords
    )
    keyword_memberships: dict[str, list[str]] = {}
    for keyword, _ in keywords:
        for paper in keyword.papers:
            keyword_memberships.setdefault(paper.url, []).append(keyword.keyword)
    papers = unique_papers([paper for keyword, _ in keywords for paper in keyword.papers])
    keyword_choices = [(keyword.keyword, keyword.paper_count) for keyword, _ in keywords]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>热点关键词 - Oh My RSS</title>
  <style>{page_css()}{report_css()}</style>
</head>
<body>
<main>
  <p><a class="back" href="../../index.html">返回总结索引</a></p>
  <article>
    <h1>关键词趋势</h1>
    <div class="meta">月份：{_text(month)} · 生成时间：{_text(generated_at)}</div>
    <p>按关键词查看近期研究脉络与对应中文总结。</p>
    {render_report_workspace(
        mode="keywords",
        papers=papers,
        keyword_choices=keyword_choices,
        keyword_memberships=keyword_memberships,
        overview=keyword_cards,
    )}
  </article>
</main>
</body>
</html>
"""


def render_keyword_trend_section(keyword: KeywordTrend, *, slug: str | None = None) -> str:
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
    section_id = f"keyword-{slug or topic_slug_hint(keyword.keyword)}"
    return f"""
    <section id="{_attr(section_id)}" class="report-section">
    <h1>{_text(keyword.keyword)}</h1>
    <div class="meta">关键词趋势 · 月份：{_text(keyword.month)} · 论文：{keyword.paper_count} · 环比：{signed_number(keyword.growth)} · 热度分：{keyword.score:.1f}</div>
    <p>{_text(keyword.summary)}</p>

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
    </section>
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
.toc { margin: 18px 0 28px; padding-left: 22px; }
.toc li { margin: 7px 0; }
.report-section { border-top: 1px solid #e5e7eb; padding-top: 22px; margin-top: 28px; }
.report-workspace { border-top: 1px solid #e5e7eb; padding-top: 20px; margin-top: 18px; }
.report-toolbar { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; align-items: end; }
.report-toolbar label { display: grid; gap: 5px; color: #5d6673; font-size: 12px; font-weight: 650; }
.report-toolbar input, .report-toolbar select { width: 100%; min-height: 36px; border: 1px solid #cfd7e1; border-radius: 5px; padding: 7px 9px; color: inherit; background: #fff; }
.report-search { grid-column: span 2; }
.report-clear, .report-filter-button, .report-group-card button, .report-pager button { min-height: 36px; border: 1px solid #cfd7e1; border-radius: 5px; padding: 7px 10px; color: #0f5fb8; background: #fbfcfd; font: inherit; cursor: pointer; }
.report-filter-button, .report-group-card button { min-height: auto; padding: 0; border: 0; background: transparent; font-weight: 650; text-align: left; }
.report-filter-button[aria-pressed="true"], .report-group-card button[aria-pressed="true"] { color: #063f80; text-decoration: underline; }
.report-result-meta { margin: 16px 0 8px; color: #5d6673; font-size: 13px; }
.report-paper-list { display: grid; border-top: 1px solid #e5e7eb; }
.report-paper { padding: 14px 0; border-bottom: 1px solid #e5e7eb; }
.report-paper-title { display: inline-block; font-weight: 700; text-decoration: none; }
.report-paper-meta, .report-group-meta { margin-top: 4px; color: #687281; font-size: 13px; }
.report-paper p { margin: 7px 0 0; color: #46505d; font-size: 14px; }
.report-pager { display: flex; justify-content: flex-end; align-items: center; gap: 8px; margin-top: 14px; color: #5d6673; font-size: 13px; }
.report-pager button:disabled { cursor: default; opacity: 0.45; }
.report-group-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-bottom: 18px; }
.report-group-card { border: 1px solid #d7dde4; border-radius: 6px; padding: 11px; background: #fbfcfd; scroll-margin-top: 80px; }
.report-empty { color: #687281; }
@media (min-width: 900px) { .report-grid { grid-template-columns: 1fr 1fr; } .report-grid figure:first-child { grid-column: 1 / -1; } }
@media (max-width: 720px) { .report-toolbar { grid-template-columns: 1fr 1fr; } .report-search { grid-column: 1 / -1; } .report-group-grid { grid-template-columns: 1fr; } }
@media (prefers-color-scheme: dark) {
  .report-grid img { border-color: #344050; }
  th, td { border-color: #28313c; }
  th { background: #1d2530; color: #d7dee8; }
  .report-section { border-color: #28313c; }
  .report-workspace, .report-paper-list, .report-paper { border-color: #28313c; }
  .report-toolbar input, .report-toolbar select, .report-clear, .report-pager button, .report-group-card { color: #e7edf5; background: #1d2530; border-color: #374151; }
  .report-paper p { color: #c6d0db; }
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
