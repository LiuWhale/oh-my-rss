# Oh My RSS

RSS-driven reading automation. The first workflow turns arXiv papers found in
FreshRSS into Chinese paper-story summaries, publishes static HTML pages, and
optionally writes summary links back into FreshRSS so RSS clients such as Reeder
can open them.

## Features

- Reads RSS entries from a FreshRSS SQLite database.
- Detects arXiv papers from RSS titles, links, and content.
- De-duplicates papers that appear in multiple feeds.
- Downloads arXiv PDFs and extracts text with `pdftotext`.
- Calls Codex CLI to generate Chinese summaries with:
  - `Motivation`
  - `Contribution`
  - `技术原理`
  - `实验设计及分析`
  - `原文链接`
- Produces static HTML with MathJax support.
- Produces a static public RSS feed at `feed.xml`.
- Uses hash-based detail URLs to avoid stale browser/RSS-client caches.
- Optionally backs up the FreshRSS DB and updates entries with a clickable summary link.

## Requirements

- Python 3.11+
- FreshRSS using SQLite
- `curl`
- `pdftotext` from Poppler
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
- `manifest.json`: machine-readable summary metadata

Users can subscribe to:

```text
<site.public_base_url>/feed.xml
```

This feed is static. It lets other people read generated summaries without
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
