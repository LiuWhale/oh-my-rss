# Reeder Workflow

Reeder reads FreshRSS through the FreshRSS account. This project does not push directly to Reeder. Instead, it updates FreshRSS article content with a link like:

```html
<p data-codex-arxiv-summary="2606.11184v1">
  <strong>Codex 中文总结：</strong>
  <a href="https://example.com/paper-feeds/summaries/2606.11184v1-hash.html">
    查看 Motivation / Contribution / 技术原理 / 实验设计及分析
  </a>
</p>
```

After Reeder syncs FreshRSS, the link appears near the top of the article.

Generated detail pages use hash-based filenames. This avoids stale browser or RSS-client caches when the same paper is summarized again with improved prompts.

## Public Summary Feed

Oh My RSS also writes a static RSS feed:

```text
<site.public_base_url>/feed.xml
```

It also writes category-specific feeds under:

```text
<site.public_base_url>/categories/
```

For one-click import of the main summary feed, category feeds, monthly reports,
hot directions, and hot keywords, use:

```text
<site.public_base_url>/opml.xml
```

For category-only bulk import into RSS clients, use:

```text
<site.public_base_url>/categories/opml.xml
```

For scripts, launch pages, or integrations that need a machine-readable list of
all public RSS and OPML entry points, use:

```text
<site.public_base_url>/feeds.json
```

Monthly research trend reports are published as a separate feed:

```text
<site.public_base_url>/reports/monthly.xml
```

Each monthly report item links to an HTML report with direction statistics,
source distribution, trend SVG charts, and representative paper links.

Hot research directions are published separately:

```text
<site.public_base_url>/reports/trending.xml
```

Each item represents one currently hot research direction and links to the
representative papers behind that trend.

Use these for public readers. They can subscribe to generated summaries without
connecting to your FreshRSS account. The all-in-one feed intentionally omits
item-level RSS `<category>` tags so clients do not present one article as coming
from several feeds. Use category-specific feeds when a client should show
separate subscriptions or folders.
