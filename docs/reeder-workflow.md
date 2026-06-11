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

Use these for public readers. They can subscribe to generated summaries without
connecting to your FreshRSS account. The all-in-one feed intentionally omits
item-level RSS `<category>` tags so clients do not present one article as coming
from several feeds. Use category-specific feeds when a client should show
separate subscriptions or folders.
