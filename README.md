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
- Classifies papers into research-domain labels such as robot learning,
  manipulation, humanoids, VLA, navigation, SLAM, perception, safety/control,
  embodied AI, and benchmarks.
- Calls Codex CLI to generate Chinese summaries with:
  - `Motivation`
  - `Contribution`
  - `技术原理`
  - `实验设计及分析`
  - `原文链接`
- Produces static HTML with MathJax support.
- Produces a static public RSS feed at `feed.xml`.
- Exposes RSS and OPML auto-discovery links from the public index page.
- Produces a monthly research radar feed with trend tables and SVG charts.
- Produces a trending-topic feed with one item per hot research direction.
- Produces a trending-keyword feed for specific terms such as VLA, diffusion
  policy, humanoid, SLAM, safety filter, and sim-to-real.
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
oh-my-rss doctor --config config.yaml
```

If the environment checks pass, generate summaries:

```bash
oh-my-rss run --config config.yaml --limit 1
```

To preview which papers would be processed without calling Codex:

```bash
oh-my-rss run --config config.yaml --dry-run --limit 5
```

To validate generated public site files before publishing or after a run:

```bash
oh-my-rss validate-site --site-dir ./site
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
- `feeds.json`: machine-readable directory of all public RSS and OPML entry
  points
- `status.json`: machine-readable service status summary with summary counts,
  category counts, report counts, latest summary, and public feed URLs
- `robots.txt` and `sitemap.xml`: crawler discovery files for the public index,
  generated summary pages, monthly reports, hot directions, and hot keywords
- `opml.xml`: complete OPML import file for the main feed, category feeds,
  monthly report feed, hot direction feed, and hot keyword feed
- `categories/*.xml`: per-source/category RSS feeds
- `categories/index.json`: machine-readable category feed list
- `categories/opml.xml`: category-only OPML import file for RSS clients
- `reports/monthly.xml`: monthly research trend report RSS feed
- `reports/monthly/YYYY-MM.html`: monthly report pages with direction bars,
  source distribution, animated trend charts, and representative papers
- `reports/trending.xml`: hot research-direction RSS feed
- `reports/trending/*.html`: direction pages with trend counts, sources, and
  representative papers
- `reports/keywords.xml`: hot research-keyword RSS feed
- `reports/keywords/*.html`: keyword pages with trend counts, sources, and
  representative papers
- `manifest.json`: machine-readable summary metadata

Category feed names are normalized for mixed paper sources: a leading `arXiv `
prefix is removed before publishing, and stale `categories/arxiv-*.xml` files
from older runs are cleaned up.

Newly generated records include `research_domains`. Category feeds and monthly
reports use those research-domain labels first, then fall back to normalized
feed names only when no research topic can be inferred.

Users can subscribe to:

```text
<site.public_base_url>/feed.xml
```

They can also subscribe to category-specific feeds. RSS clients generally do
not subscribe to JSON directly; use the complete OPML bundle for one-click
import:

```text
<site.public_base_url>/opml.xml
```

Use the category-only OPML file when you only want the topic/source feeds:

```text
<site.public_base_url>/categories/opml.xml
```

Use the JSON file only for integrations that need a machine-readable list:

```text
<site.public_base_url>/categories/index.json
```

For integrations that need every public RSS and OPML entry point, use:

```text
<site.public_base_url>/feeds.json
```

For monitoring or lightweight health checks, use:

```text
<site.public_base_url>/status.json
```

For crawler discovery, each run also writes:

```text
<site.public_base_url>/robots.txt
<site.public_base_url>/sitemap.xml
```

Monthly trend reports are published as a separate RSS feed:

```text
<site.public_base_url>/reports/monthly.xml
```

Each monthly report page includes an animated SVG trend chart, direction bar
chart, source distribution chart, summary tables, and links back to the
underlying Codex paper summaries.

Hot research directions are also published as their own feed:

```text
<site.public_base_url>/reports/trending.xml
```

Each trending-topic item links to a direction page with source counts, recent
trend counts, representative papers, and links back to the generated paper
summaries.

Specific research keywords are published as another RSS feed:

```text
<site.public_base_url>/reports/keywords.xml
```

Each keyword item links to a page that tracks term-level trends such as VLA,
diffusion policy, humanoid, SLAM, safety filter, and sim-to-real across recent
paper summaries.

These feeds are static. They let other people read generated summaries without
logging into your FreshRSS account or sharing your read/unread state.

## Scheduling

Generate a locked cron entry for a 10-minute scheduler:

```bash
oh-my-rss print-cron \
  --cwd /opt/oh-my-rss \
  --config config.yaml \
  --limit 1 \
  --interval-minutes 10 \
  --log-path state/cron.log \
  --venv .venv
```

The command prints a cron line like:

```cron
*/10 * * * * cd /opt/oh-my-rss && . .venv/bin/activate && flock -n /tmp/oh-my-rss.lock oh-my-rss run --config config.yaml --limit 1 >> state/cron.log 2>&1
```

Paste that line into cron or the equivalent scheduler. Use `--no-venv` if
`oh-my-rss` is installed on the scheduler's default `PATH`.

## Deployment Notes

- For Synology NAS and FreshRSS Docker setups, see [`docs/synology-freshrss.md`](docs/synology-freshrss.md).
- For adding RSS subscriptions, grouping feeds, and OPML import, see [`docs/feed-management.md`](docs/feed-management.md).
- For Reeder/FreshRSS behavior, see [`docs/reeder-workflow.md`](docs/reeder-workflow.md).

## Development

```bash
PYTHONPATH=src pytest -q
ruff check .
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
