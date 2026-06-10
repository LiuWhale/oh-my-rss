# Feed Management

This project does not own your subscriptions. FreshRSS remains the source of
truth for feeds, categories, unread state, and Reeder sync. The summarizer only
reads one FreshRSS category per run and writes summary links back into matching
entries.

## Recommended Categories

Use separate FreshRSS categories for different reading workflows:

- `论文`: arXiv and other research-paper feeds processed by this summarizer.
- `中文新闻`: Chinese-language news feeds for normal reading.
- `English News`: English-language news feeds for normal reading.

Set the summarizer to the research-paper category:

```yaml
freshrss:
  category: 论文
```

If you want to process multiple research categories, create multiple config
files and schedule one run for each category.

## Add One Feed In FreshRSS

1. Open FreshRSS in the browser.
2. Go to subscription management.
3. Create or choose a category, for example `论文`.
4. Add the RSS or Atom URL.
5. Trigger a refresh in FreshRSS.
6. Confirm new entries appear in the expected category.
7. Run the summarizer with `--dry-run` first:

```bash
freshrss-arxiv-codex run --config config.yaml --dry-run --limit 5
```

Reeder will show the FreshRSS categories as folders after the next FreshRSS
account sync.

## Move Existing Feeds Between Groups

In FreshRSS, edit the feed and change its category. The summarizer follows the
category stored in FreshRSS, so no code change is needed. Update
`freshrss.category` only when the category name that should be scanned changes.

## Batch Import With OPML

For a new deployment, OPML is the easiest way to create feeds and groups.
Import an OPML file through FreshRSS subscription management.

Minimal example:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>FreshRSS subscriptions</title>
  </head>
  <body>
    <outline text="论文" title="论文">
      <outline
        type="rss"
        text="arXiv cs.RO"
        title="arXiv cs.RO"
        xmlUrl="https://export.arxiv.org/rss/cs.RO"
        htmlUrl="https://arxiv.org/list/cs.RO/recent" />
      <outline
        type="rss"
        text="arXiv cs.AI"
        title="arXiv cs.AI"
        xmlUrl="https://export.arxiv.org/rss/cs.AI"
        htmlUrl="https://arxiv.org/list/cs.AI/recent" />
    </outline>
    <outline text="中文新闻" title="中文新闻">
      <outline
        type="rss"
        text="BBC News 中文"
        title="BBC News 中文"
        xmlUrl="https://feeds.bbci.co.uk/zhongwen/simp/rss.xml"
        htmlUrl="https://www.bbc.com/zhongwen/simp" />
    </outline>
    <outline text="English News" title="English News">
      <outline
        type="rss"
        text="BBC World"
        title="BBC World"
        xmlUrl="https://feeds.bbci.co.uk/news/world/rss.xml"
        htmlUrl="https://www.bbc.com/news/world" />
    </outline>
  </body>
</opml>
```

Keep private or personal feed lists out of git unless the repository is private.

## Replace Invalid Feed URLs

When a feed stops updating, replace it in FreshRSS rather than editing this
project:

1. Open the feed's original website and look for its RSS or Atom link.
2. Prefer official feeds over third-party scraping services.
3. Test the URL from the machine running FreshRSS:

```bash
curl -L --max-time 20 "https://example.com/feed.xml" | head
```

4. If the feed requires your NAS proxy, test with the same proxy environment
   used by the scheduled job.
5. Edit the feed URL in FreshRSS and refresh it.

For arXiv categories, prefer `https://export.arxiv.org/rss/<category>`, for
example `https://export.arxiv.org/rss/cs.RO`.
