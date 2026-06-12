# Changelog

All notable changes to Oh My RSS are documented in this file.

This project follows a practical changelog format inspired by
Keep a Changelog. Version tags use semantic versioning.

## [Unreleased]

## [0.1.3] - 2026-06-12

### Added

- Add `oh-my-rss validate-opml` to parse OPML files and optionally check each
  feed URL over the network before importing into FreshRSS.
- Add `oh-my-rss print-starter-opml` to generate a FreshRSS import bundle with
  validated starter paper feeds.
- Support generic paper RSS entries by accepting DOI and article-page links in
  addition to arXiv IDs. Direct PDF links are used when present; otherwise the
  summary falls back to RSS metadata.
- Add `oh-my-rss print-cron` to generate a locked cron entry for self-hosted
  periodic runs.
- Add `oh-my-rss doctor` to check config loading, FreshRSS DB paths, output
  directories, and required runtime commands before running summaries.
- Add `oh-my-rss validate-site` to check generated RSS, OPML, JSON, sitemap,
  and index files before publishing.
- Publish `robots.txt` and `sitemap.xml` so crawlers can discover the public
  index, summary pages, monthly reports, hot directions, and hot keywords.
- Publish `status.json`, a lightweight service status summary for monitoring
  and support checks.
- Publish `feeds.json`, a machine-readable directory of all public RSS and
  OPML entry points.
- Expose RSS and OPML auto-discovery links plus visible subscription links from
  the public index page.
- Publish a complete OPML subscription bundle for the main summary feed,
  category feeds, monthly reports, hot directions, and hot keywords.
- Publish a trending research-keyword feed for terms such as VLA, diffusion
  policy, humanoid, SLAM, safety filter, and sim-to-real.
- Publish a trending research-topic feed with one item per hot direction and
  per-direction pages that link to representative paper summaries.
- Classify generated paper records into research-domain labels so category feeds
  and monthly reports group by topic before falling back to source feed names.
- Publish a monthly research radar feed with monthly HTML reports, JSON
  statistics, direction bar charts, source distribution charts, and animated SVG
  trend charts.
- Embed a first-page PNG preview in generated paper summary pages.
- Document validated IJRR and Soft Robotics OnlineFirst RSS feeds.
- Build source and wheel distributions in CI to catch packaging regressions.
- Add a GitHub cover image for the repository README and social preview setup.

### Changed

- Update the Synology installer to print cron entries through
  `oh-my-rss print-cron` instead of carrying a stale hand-written schedule.
- Make `docker-compose.yml` honor the documented `CONFIG_PATH` environment
  variable.
- Add `.dockerignore` so Docker builds exclude local virtualenvs, generated
  state/site output, SQLite databases, and local secrets.
- Normalize mixed-source category feed names by removing the leading `arXiv `
  prefix from public category feeds.

### Fixed

- Let Docker Compose run with built-in defaults when no local `.env` file is
  present.
- Let `oh-my-rss run --dry-run` work without local `curl` or `pdftotext`,
  because preview mode does not download PDFs.
- Keep the runtime `oh_my_rss.__version__` aligned with the package metadata
  version.
- Use an SPDX license string in `pyproject.toml` to avoid setuptools license
  metadata deprecation warnings.

## [0.1.2] - 2026-06-11

### Added

- Publish a category OPML export so RSS clients can import all category-specific
  summary feeds in one step.
- Publish a machine-readable category index for integrations.

## [0.1.1] - 2026-06-11

### Fixed

- Keep the all-in-one public feed ungrouped so RSS clients do not display
  duplicate or confusing source choices for the same feed URL.

## [0.1.0] - 2026-06-11

### Added

- Initial public release of the FreshRSS-driven arXiv paper summarizer.
- Read FreshRSS SQLite entries from a configured category.
- Detect and de-duplicate arXiv papers from RSS titles, links, and content.
- Download arXiv PDFs, extract text, and call Codex CLI for Chinese summaries.
- Render static HTML summary pages with MathJax support.
- Publish a static all-in-one RSS feed for generated summaries.
- Publish category-specific RSS feeds for paper-source grouping.
- Optionally write clickable summary links back into matching FreshRSS entries.
- Include setup documentation for FreshRSS, Reeder, feed grouping, and Synology
  deployment.
