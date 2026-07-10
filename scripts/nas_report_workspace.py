"""Static report-workspace renderer used by the Synology single-file runner.

The public package uses ``oh_my_rss.reports``. The NAS still runs a historical
single-file publisher, so this companion keeps its report HTML behavior aligned
without changing the RSS PHP endpoints.
"""

from __future__ import annotations

import html


def build_monthly_html(
    report: dict[str, object],
    *,
    base_css: str,
    report_css: str,
    summary: str,
    direction_rows: list[tuple[str, int]],
    source_rows: list[tuple[str, int]],
) -> str:
    month = str(report["month"])
    direction_table = "".join(
        "<tr>"
        f'<td><button type="button" class="report-filter-button" data-report-domain="{_attr(name)}">{_text(name)}</button></td>'
        f"<td>{count}</td>"
        f"<td>{_text(_signed_number(_mapping(report, 'direction_growth').get(name, 0)))}</td>"
        f"<td>{_mapping(report, 'direction_scores').get(name, float(count)):.1f}</td>"
        "</tr>"
        for name, count in direction_rows
    ) or '<tr><td colspan="4">暂无方向统计。</td></tr>'
    source_table = "".join(
        "<tr>"
        f'<td><button type="button" class="report-filter-button" data-report-source="{_attr(name)}">{_text(name)}</button></td>'
        f"<td>{count}</td>"
        "</tr>"
        for name, count in source_rows
    ) or '<tr><td colspan="2">暂无来源统计。</td></tr>'
    workspace = render_workspace(
        mode="monthly",
        papers=_papers(report),
        domain_choices=direction_rows,
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_text(report.get('title') or month)} - Oh My RSS</title>
  <style>{base_css}{report_css}{workspace_css()}</style>
</head>
<body>
<main>
  <p><a class="back" href="../../index.html">返回总结索引</a></p>
  <article>
    <h1>{_text(report.get('title') or month)}</h1>
    <div class="meta">生成时间：{_text(report.get('generated_at'))} · 本月论文：{_text(report.get('total_papers'))}</div>
    <p>{_text(summary)}</p>
    <section class="report-grid">
      <figure><img src="assets/{_attr(month)}-trend-animated.svg" alt="研究方向趋势动图"><figcaption>过去月份热门方向趋势</figcaption></figure>
      <figure><img src="assets/{_attr(month)}-direction-bars.svg" alt="热门方向柱状图"><figcaption>本月热门方向</figcaption></figure>
      <figure><img src="assets/{_attr(month)}-source-donut.svg" alt="来源分布饼图"><figcaption>本月来源分布</figcaption></figure>
    </section>
    <h2>热门方向</h2>
    <table><thead><tr><th>方向</th><th>数量</th><th>环比</th><th>热度分</th></tr></thead><tbody>{direction_table}</tbody></table>
    <h2>来源分布</h2>
    <table><thead><tr><th>来源</th><th>数量</th></tr></thead><tbody>{source_table}</tbody></table>
    <h2>论文</h2>
    {workspace}
  </article>
</main>
</body>
</html>
"""


def build_trending_html(
    topic_pages: list[tuple[dict[str, object], str]],
    *,
    base_css: str,
    report_css: str,
) -> str:
    month = _text(topic_pages[0][0].get("month")) if topic_pages else ""
    generated_at = _text(topic_pages[0][0].get("generated_at")) if topic_pages else ""
    cards = "\n".join(
        f'''<section id="topic-{_attr(slug)}" class="report-group-card"
                    data-legacy-fragment="topic-{_attr(slug)}" data-report-domain="{_attr(topic.get('name'))}">
              <button type="button" data-report-domain="{_attr(topic.get('name'))}"
                      data-legacy-fragment="topic-{_attr(slug)}">{_text(topic.get('name'))}</button>
              <div class="report-group-meta">{_text(topic.get('paper_count'))} 篇 · 环比 {_text(_signed_number(topic.get('growth', 0)))} · 热度 {float(topic.get('score', 0)):.1f}</div>
              <div class="report-group-meta">趋势月份：{_text(' / '.join(topic.get('trend_months') or []))}</div>
            </section>'''
        for topic, slug in topic_pages
    )
    papers = _unique_papers([paper for topic, _ in topic_pages for paper in _papers(topic)])
    choices = [(str(topic.get("name") or ""), int(topic.get("paper_count") or 0)) for topic, _ in topic_pages]
    workspace = render_workspace("trending", papers, domain_choices=choices, overview=cards)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>热点方向 - Oh My RSS</title>
  <style>{base_css}{report_css}{workspace_css()}</style>
</head>
<body>
<main>
  <p><a class="back" href="../../index.html">返回总结索引</a></p>
  <article>
    <h1>热点方向</h1>
    <div class="meta">月份：{month} · 生成时间：{generated_at}</div>
    <p>按研究领域查看当前论文流中的热点与对应中文总结。</p>
    {workspace}
  </article>
</main>
</body>
</html>
"""


def build_keywords_html(
    keyword_pages: list[tuple[dict[str, object], str]],
    *,
    base_css: str,
    report_css: str,
) -> str:
    month = _text(keyword_pages[0][0].get("month")) if keyword_pages else ""
    generated_at = _text(keyword_pages[0][0].get("generated_at")) if keyword_pages else ""
    cards = "\n".join(
        f'''<section id="keyword-{_attr(slug)}" class="report-group-card"
                    data-legacy-fragment="keyword-{_attr(slug)}" data-report-keyword="{_attr(keyword.get('keyword'))}">
              <button type="button" data-report-keyword="{_attr(keyword.get('keyword'))}"
                      data-legacy-fragment="keyword-{_attr(slug)}">{_text(keyword.get('keyword'))}</button>
              <div class="report-group-meta">{_text(keyword.get('paper_count'))} 篇 · 环比 {_text(_signed_number(keyword.get('growth', 0)))} · 热度 {float(keyword.get('score', 0)):.1f}</div>
              <div class="report-group-meta">趋势月份：{_text(' / '.join(keyword.get('trend_months') or []))}</div>
            </section>'''
        for keyword, slug in keyword_pages
    )
    memberships: dict[str, list[str]] = {}
    for keyword, _ in keyword_pages:
        for paper in _papers(keyword):
            memberships.setdefault(str(paper.get("url") or ""), []).append(str(keyword.get("keyword") or ""))
    papers = _unique_papers([paper for keyword, _ in keyword_pages for paper in _papers(keyword)])
    choices = [(str(keyword.get("keyword") or ""), int(keyword.get("paper_count") or 0)) for keyword, _ in keyword_pages]
    workspace = render_workspace(
        "keywords",
        papers,
        keyword_choices=choices,
        keyword_memberships=memberships,
        overview=cards,
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>关键词趋势 - Oh My RSS</title>
  <style>{base_css}{report_css}{workspace_css()}</style>
</head>
<body>
<main>
  <p><a class="back" href="../../index.html">返回总结索引</a></p>
  <article>
    <h1>关键词趋势</h1>
    <div class="meta">月份：{month} · 生成时间：{generated_at}</div>
    <p>按关键词查看近期研究脉络与对应中文总结。</p>
    {workspace}
  </article>
</main>
</body>
</html>
"""


def render_workspace(
    mode: str,
    papers: list[dict[str, object]],
    *,
    domain_choices: list[tuple[str, int]] | None = None,
    keyword_choices: list[tuple[str, int]] | None = None,
    keyword_memberships: dict[str, list[str]] | None = None,
    overview: str = "",
) -> str:
    domain_choices = domain_choices or []
    keyword_choices = keyword_choices or []
    keyword_memberships = keyword_memberships or {}
    sources = sorted({str(paper.get("source") or "Unknown") for paper in papers})
    source_options = "".join(f'<option value="{_attr(value)}">{_text(value)}</option>' for value in sources)
    domain_filter = _select("domain", "领域", "全部领域", domain_choices)
    keyword_filter = _select("keyword", "关键词", "全部关键词", keyword_choices)
    groups = f'<div class="report-group-grid">{overview}</div>' if overview else ""
    return f"""
    <section class="report-workspace" data-report-workspace="{_attr(mode)}">
      {groups}
      <div class="report-toolbar" aria-label="论文筛选">
        <label class="report-search">检索<input type="search" data-report-query="q" placeholder="标题、总结、来源或领域"></label>
        <label>来源<select data-report-filter="source"><option value="">全部来源</option>{source_options}</select></label>
        {domain_filter}
        {keyword_filter}
        <button type="button" class="report-clear" data-report-clear>清除筛选</button>
      </div>
      <div class="report-result-meta" data-report-result-meta></div>
      <div class="report-paper-list" data-report-paper-list>{_paper_cards(papers, keyword_memberships)}</div>
      <div class="report-pager" data-report-pager>
        <button type="button" data-report-page="previous" aria-label="上一页">上一页</button>
        <span data-report-page-status></span>
        <button type="button" data-report-page="next" aria-label="下一页">下一页</button>
      </div>
    </section>
    {workspace_script()}
"""


def _select(key: str, label: str, all_label: str, choices: list[tuple[str, int]]) -> str:
    if not choices:
        return ""
    options = "".join(f'<option value="{_attr(name)}">{_text(name)} ({count})</option>' for name, count in choices)
    return f'<label>{label}<select data-report-filter="{key}"><option value="">{all_label}</option>{options}</select></label>'


def _paper_cards(papers: list[dict[str, object]], memberships: dict[str, list[str]]) -> str:
    if not papers:
        return '<p class="report-empty">暂无可展示的论文。</p>'
    cards = []
    for paper in papers:
        url = str(paper.get("url") or "")
        source = str(paper.get("source") or "Unknown")
        domains = [str(value) for value in paper.get("directions") or []]
        keywords = memberships.get(url, [])
        search = " ".join([str(paper.get("title") or ""), source, *domains, *keywords, str(paper.get("summary_excerpt") or "")]).casefold()
        date = str(paper.get("published_at") or paper.get("generated_at") or "")
        meta = [source]
        if date:
            meta.append(f"公开：{date}")
        if domains:
            meta.append("领域：" + " / ".join(domains))
        if keywords:
            meta.append("关键词：" + " / ".join(keywords))
        cards.append(
            f'<article class="report-paper" data-report-paper data-report-paper-url="{_attr(url)}" '
            f'data-report-paper-source="{_attr(source)}" data-report-paper-domains="{_attr("||".join(domains))}" '
            f'data-report-paper-keywords="{_attr("||".join(keywords))}" data-report-search="{_attr(search)}">'
            f'<a class="report-paper-title" href="{_attr(url)}">{_text(paper.get("title") or "Untitled paper")}</a>'
            f'<div class="report-paper-meta">{_text(" · ".join(meta))}</div>'
            f'<p>{_text(paper.get("summary_excerpt") or "")}</p></article>'
        )
    return "\n".join(cards)


def _papers(report: dict[str, object]) -> list[dict[str, object]]:
    values = report.get("papers") or report.get("top_papers") or []
    return list(values) if isinstance(values, list) else []


def _unique_papers(papers: list[dict[str, object]]) -> list[dict[str, object]]:
    by_url = {str(paper.get("url") or ""): paper for paper in papers}
    return sorted(by_url.values(), key=lambda paper: str(paper.get("generated_at") or ""), reverse=True)


def _mapping(report: dict[str, object], key: str) -> dict[str, object]:
    value = report.get(key) or {}
    return value if isinstance(value, dict) else {}


def _signed_number(value: object) -> str:
    number = int(value or 0)
    return f"+{number}" if number > 0 else str(number)


def _attr(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def _text(value: object) -> str:
    return html.escape(str(value or ""), quote=False)


def workspace_css() -> str:
    return """
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
@media (max-width: 720px) { .report-toolbar { grid-template-columns: 1fr 1fr; } .report-search { grid-column: 1 / -1; } .report-group-grid { grid-template-columns: 1fr; } }
@media (prefers-color-scheme: dark) { .report-workspace, .report-paper-list, .report-paper { border-color: #28313c; } .report-toolbar input, .report-toolbar select, .report-clear, .report-pager button, .report-group-card { color: #e7edf5; background: #1d2530; border-color: #374151; } .report-paper p { color: #c6d0db; } }
"""


def workspace_script() -> str:
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
  const state = { q: params.get("q") || "", source: params.get("source") || "", domain: params.get("domain") || "", keyword: params.get("keyword") || "", page: Math.max(1, Number.parseInt(params.get("page") || "1", 10) || 1), legacyHash: window.location.hash.replace(/^#/, "") };
  const setControl = (control, value) => { if (control && [...control.options].some(option => option.value === value)) control.value = value; };
  const values = (item, name) => (item.dataset[name] || "").split("||").filter(Boolean);
  const applyLegacyHash = () => { const target = [...document.querySelectorAll("[data-legacy-fragment]")].find(item => item.dataset.legacyFragment === state.legacyHash); if (!target) return; if (target.dataset.reportDomain) state.domain = target.dataset.reportDomain; if (target.dataset.reportKeyword) state.keyword = target.dataset.reportKeyword; };
  const matching = () => papers.filter(item => (!state.q || (item.dataset.reportSearch || "").includes(state.q.toLowerCase())) && (!state.source || item.dataset.reportPaperSource === state.source) && (!state.domain || values(item, "reportPaperDomains").includes(state.domain)) && (!state.keyword || values(item, "reportPaperKeywords").includes(state.keyword)));
  const writeUrl = () => { const url = new URL(window.location.href); ["q", "source", "domain", "keyword", "page"].forEach(key => url.searchParams.delete(key)); ["q", "source", "domain", "keyword"].forEach(key => { if (state[key]) url.searchParams.set(key, state[key]); }); if (state.page > 1) url.searchParams.set("page", String(state.page)); url.hash = state.legacyHash ? `#${state.legacyHash}` : ""; history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`); };
  const render = () => { setControl(source, state.source); setControl(domain, state.domain); setControl(keyword, state.keyword); if (query) query.value = state.q; const matches = matching(); const totalPages = Math.max(1, Math.ceil(matches.length / pageSize)); state.page = Math.min(state.page, totalPages); const start = (state.page - 1) * pageSize; const visible = new Set(matches.slice(start, start + pageSize)); papers.forEach(item => { item.hidden = !visible.has(item); }); resultMeta.textContent = `显示 ${matches.length ? start + 1 : 0}-${Math.min(start + pageSize, matches.length)} / ${matches.length} 篇论文`; pageStatus.textContent = `${state.page} / ${totalPages}`; root.querySelector('[data-report-page="previous"]').disabled = state.page <= 1; root.querySelector('[data-report-page="next"]').disabled = state.page >= totalPages; document.querySelectorAll("[data-report-domain], [data-report-keyword], [data-report-source]").forEach(button => { const active = (button.dataset.reportDomain && button.dataset.reportDomain === state.domain) || (button.dataset.reportKeyword && button.dataset.reportKeyword === state.keyword) || (button.dataset.reportSource && button.dataset.reportSource === state.source); button.setAttribute("aria-pressed", String(active)); }); writeUrl(); };
  const resetPage = () => { state.page = 1; };
  if (query) query.addEventListener("input", event => { state.q = event.target.value.trim(); state.legacyHash = ""; resetPage(); render(); });
  [[source, "source"], [domain, "domain"], [keyword, "keyword"]].forEach(([control, key]) => { if (control) control.addEventListener("change", event => { state[key] = event.target.value; state.legacyHash = ""; resetPage(); render(); }); });
  document.querySelectorAll("[data-report-domain], [data-report-keyword], [data-report-source]").forEach(button => button.addEventListener("click", () => { if (button.dataset.reportDomain) state.domain = button.dataset.reportDomain; if (button.dataset.reportKeyword) state.keyword = button.dataset.reportKeyword; if (button.dataset.reportSource) state.source = button.dataset.reportSource; state.legacyHash = button.dataset.legacyFragment || ""; resetPage(); render(); root.scrollIntoView({ behavior: "smooth", block: "start" }); }));
  root.querySelector("[data-report-clear]").addEventListener("click", () => { Object.assign(state, { q: "", source: "", domain: "", keyword: "", page: 1, legacyHash: "" }); render(); });
  root.querySelectorAll("[data-report-page]").forEach(button => button.addEventListener("click", () => { state.page += button.dataset.reportPage === "next" ? 1 : -1; render(); root.scrollIntoView({ behavior: "smooth", block: "start" }); }));
  applyLegacyHash(); render();
})();
</script>
"""
