# Synology + FreshRSS Deployment

This project works on Synology when the runner can access:

- FreshRSS SQLite DB
- `curl`
- `pdftotext`
- Codex CLI
- a writable static web directory

## FreshRSS SQLite Path

FreshRSS Docker images commonly store user databases under:

```text
/var/www/FreshRSS/data/users/<fresh-rss-user>/db.sqlite
```

For a separate summarizer container, bind-mount the FreshRSS `data` directory and point `freshrss.db_path` at the mounted DB file.

## Static Output

Set:

```yaml
site:
  public_base_url: https://your-domain.example/paper-feeds/summaries
  output_dir: /path/to/static/paper-feeds/summaries
```

The URL must serve files from `output_dir`.

The public summary RSS feed will be available at:

```text
https://your-domain.example/paper-feeds/summaries/feed.xml
```

Category-specific feeds will be written under:

```text
https://your-domain.example/paper-feeds/summaries/categories/
```

For bulk import into RSS clients, use the generated OPML file:

```text
https://your-domain.example/paper-feeds/summaries/categories/opml.xml
```

## FreshRSS Link Back-Writing

By default, `run` writes a summary link into each FreshRSS entry it processed. It first backs up the SQLite DB into `runtime.state_dir/db-backups`.

To disable DB writes:

```bash
oh-my-rss run --config config.yaml --no-freshrss-link
```

## Proxy

If your NAS needs a proxy for arXiv, journal sites, PDF downloads, or Codex, set
environment variables before running:

```bash
export http_proxy=http://proxy-host:port
export https_proxy=http://proxy-host:port
```

Do not commit proxy credentials.

## Schedule

Use cron or Synology Task Scheduler to run:

```bash
oh-my-rss print-cron \
  --cwd /path/to/oh-my-rss \
  --config config.yaml \
  --limit 1 \
  --interval-minutes 10 \
  --log-path state/cron.log \
  --venv .venv
```

Paste the printed cron line into cron or the Synology scheduler.
