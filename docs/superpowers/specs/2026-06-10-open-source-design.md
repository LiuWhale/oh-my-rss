# Open Source Design

The project packages the NAS FreshRSS arXiv summarization workflow as a configurable Python CLI. It reads FreshRSS SQLite data, de-duplicates arXiv papers, downloads and extracts PDFs, invokes Codex CLI, renders static HTML with MathJax, and optionally writes hash-based summary links back into FreshRSS entries.

Private deployment details stay out of the repository. Users configure paths, public URLs, categories, and commands through YAML and environment variables.

The first release intentionally avoids a web UI and background daemon. Scheduling is handled by cron, systemd, Docker, or Synology Task Scheduler.
