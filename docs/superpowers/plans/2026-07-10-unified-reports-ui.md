# Unified Reports UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Upgrade the existing monthly, trending-topic, and keyword report pages into a single-page, filterable reading experience while preserving every published RSS URL and existing RSS item deep link.

**Architecture:** The publishing pipeline remains static: completed paper records are analyzed once, then HTML, JSON, SVG, and RSS files are written beneath the existing `reports/` tree. A shared, dependency-free browser script reads embedded report data, renders a paginated paper list, and persists filters in the page URL. The XML feeds keep their existing locations and media type.

**Tech Stack:** Python 3.11, static HTML/CSS/JavaScript, pytest.

## Global Constraints

- Keep `reports/monthly.xml`, `reports/trending.xml`, and `reports/keywords.xml` byte-compatible in purpose and URL.
- Keep existing `#topic-<slug>` and `#keyword-<slug>` RSS item links working.
- Do not add a new public feed or a separate Explorer page.
- Keep report pages static and dependency-free for NAS hosting.
- Preserve the pre-existing `feed_urls` working-tree changes.

---

### Task 1: Publish complete report-paper data

**Files:**
- Modify: `src/oh_my_rss/analytics.py`
- Modify: `tests/test_analytics.py`

**Interfaces:**
- `MonthlyReport.papers` contains every completed paper in the report month in newest-first order.
- `TrendingTopic.papers` and `KeywordTrend.papers` retain every matching current-month paper, with presentation pagination left to the browser.

- [x] Add failing tests for report data containing more than twenty records.
- [x] Run the focused analytics tests and confirm they fail because report arrays are truncated.
- [x] Extend report data structures and builders to retain the complete ordered collections.
- [x] Re-run the focused analytics tests.

### Task 2: Add shared static report controls

**Files:**
- Modify: `src/oh_my_rss/reports.py`
- Modify: `tests/test_publisher.py`

**Interfaces:**
- `render_report_workspace(...)` emits accessible search/filter controls, embedded JSON, and stable card markup.
- Query keys are `q`, `source`, `domain`, `keyword`, and `page`.
- Legacy `#topic-*` and `#keyword-*` fragments select the matching group without changing the feed URL.

- [x] Add failing publishing tests for shared controls, data payloads, URL query keys, and old fragment IDs.
- [x] Run the focused publisher tests and confirm they fail because the controls and payloads are absent.
- [x] Implement the common CSS, dependency-free client filtering, and paginated paper cards.
- [x] Re-run the focused publisher tests.

### Task 3: Apply the workspace to the existing three report pages

**Files:**
- Modify: `src/oh_my_rss/reports.py`
- Modify: `src/oh_my_rss/publisher.py`
- Modify: `tests/test_publisher.py`

**Interfaces:**
- `reports/monthly/YYYY-MM.html` displays metrics, interactive source/domain charts, and all papers for that month.
- `reports/trending/index.html` displays selectable topic summaries and a same-page matching-paper list.
- `reports/keywords/index.html` displays selectable keyword summaries and a same-page matching-paper list.

- [x] Add failing tests that each page contains all relevant paper records, visible source/domain metadata, and links to the generated Chinese summary.
- [x] Run the focused publisher tests and confirm they fail because current pages only render tables and top records.
- [x] Render each existing page through the shared workspace; preserve current RSS filenames, channel links, and item deep links.
- [x] Re-run the focused publisher tests.

### Task 4: Verify compatibility and document the release

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `CHANGELOG.md`
- Modify: `pyproject.toml`
- Modify: `src/oh_my_rss/__init__.py`

- [x] Retain tests that parse all three XML feeds and assert their existing URL targets remain unchanged.
- [x] Run the full test suite.
- [x] Generate sample output, validate static markup and public report endpoints; browser screenshots are unavailable because this Mac has no Playwright browser runtime.
- [x] Document that reports are upgraded web views behind existing RSS items, bump to `0.1.18`, and add release notes.
- [x] Run the full test suite again.
