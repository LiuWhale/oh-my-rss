# Oh My RSS

RSS-native AI research radar. Oh My RSS turns research feeds from FreshRSS into
Chinese paper-story summaries, static public feeds, category feeds, and monthly
trend reports that RSS clients such as Reeder can subscribe to.

## Features

- Reads RSS entries from a FreshRSS SQLite database.
- Detects arXiv papers from RSS titles, links, and content.
- De-duplicates papers that appear in multiple feeds.
- Downloads arXiv PDFs and extracts text with `pdftotext`.
- Renders a first-page PNG preview and embeds it in the Codex summary page.
- Calls Codex CLI to generate Chinese summaries with:
  - `Motivation`
  - `Contribution`
  - `技术原理`
  - `实验设计及分析`
  - `原文链接`
- Produces static HTML with MathJax support.
- Produces a static public RSS feed at `feed.xml`.
- Produces a monthly research radar feed with trend tables and SVG charts.
- Uses hash-based detail URLs to avoid stale browser/RSS-client caches.
- Optionally backs up the FreshRSS DB and updates entries with a clickable summary link.

## Project Goal

Oh My RSS is designed to become a self-hosted AI research radar rather than a
replacement RSS reader. The long-term goal is to let users connect paper feeds,
conference feeds, journal feeds, lab blogs, and news feeds, then publish a clean
knowledge stream with AI summaries, research-domain classification, trend
reports, and RSS-native distribution.

## Requirements

- Python 3.11+
- FreshRSS using SQLite
- `curl`
- `pdftotext` from Poppler
- PyMuPDF, installed automatically as a Python dependency
- Codex CLI authenticated on the machine running the job

## Quick Start

```bash
git clone https://github.com/LiuWhale/oh-my-rss.git
cd oh-my-rss
python3.11 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
oh-my-rss init-config --output config.yaml
```

Edit `config.yaml`, then run:

```bash
oh-my-rss run --config config.yaml --limit 1
```

To preview which papers would be processed without calling Codex:

```bash
oh-my-rss run --config config.yaml --dry-run --limit 5
```

## Configuration

See [`configs/example.yaml`](configs/example.yaml).

The key fields are:

- `freshrss.db_path`: path to FreshRSS `db.sqlite`.
- `freshrss.category`: FreshRSS category to scan, for example `论文` or `Papers`.
- `site.output_dir`: local directory where HTML files are written.
- `site.public_base_url`: public URL prefix for generated pages.
- `codex.command`: command used to invoke Codex CLI.
- `runtime.state_dir`: state, PDF cache, prompts, logs, and DB backups.

## Public Feed

Each run writes:

- `index.html`: public summary index
- `feed.xml`: public RSS feed for generated summaries
- `categories/*.xml`: per-source/category RSS feeds
- `categories/index.json`: machine-readable category feed list
- `categories/opml.xml`: OPML import file for RSS clients
- `reports/monthly.xml`: monthly research trend report RSS feed
- `reports/monthly/YYYY-MM.html`: monthly report pages with direction bars,
  source distribution, animated trend charts, and representative papers
- `manifest.json`: machine-readable summary metadata

Category feed names are normalized for mixed paper sources: a leading `arXiv `
prefix is removed before publishing, and stale `categories/arxiv-*.xml` files
from older runs are cleaned up.

Users can subscribe to:

```text
<site.public_base_url>/feed.xml
```

They can also subscribe to category-specific feeds. RSS clients generally do
not subscribe to JSON directly; use the OPML file for bulk import:

```text
<site.public_base_url>/categories/opml.xml
```

Use the JSON file only for integrations that need a machine-readable list:

```text
<site.public_base_url>/categories/index.json
```

Monthly trend reports are published as a separate RSS feed:

```text
<site.public_base_url>/reports/monthly.xml
```

Each monthly report page includes an animated SVG trend chart, direction bar
chart, source distribution chart, summary tables, and links back to the
underlying Codex paper summaries.

These feeds are static. They let other people read generated summaries without
logging into your FreshRSS account or sharing your read/unread state.

## Scheduling

Run every 10 minutes with cron:

```cron
*/10 * * * * cd /opt/oh-my-rss && . .venv/bin/activate && oh-my-rss run --config config.yaml --limit 1 >> state/cron.log 2>&1
```

Use a lock wrapper such as `flock` if your scheduler can overlap runs.

## Deployment Notes

- For Synology NAS and FreshRSS Docker setups, see [`docs/synology-freshrss.md`](docs/synology-freshrss.md).
- For adding RSS subscriptions, grouping feeds, and OPML import, see [`docs/feed-management.md`](docs/feed-management.md).
- For Reeder/FreshRSS behavior, see [`docs/reeder-workflow.md`](docs/reeder-workflow.md).

## Development

```bash
PYTHONPATH=src pytest -q
```

## Security

Do not commit:

- FreshRSS DB files
- Codex auth files
- real domains, private IPs, proxy credentials, or user accounts
- generated PDF caches

Use `.env.example` and `configs/example.yaml` as templates.

## License

MIT
