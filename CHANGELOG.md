# Changelog

All notable changes to Oh My RSS are documented in this file.

This project follows a practical changelog format inspired by
Keep a Changelog. Version tags use semantic versioning.

## [Unreleased]

### Added

- Publish a monthly research radar feed with monthly HTML reports, JSON
  statistics, direction bar charts, source distribution charts, and animated SVG
  trend charts.
- Embed a first-page PNG preview in generated paper summary pages.
- Document validated IJRR and Soft Robotics OnlineFirst RSS feeds for
  deployments that support generic paper RSS sources.

### Changed

- Normalize mixed-source category feed names by removing the leading `arXiv `
  prefix from public category feeds.

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
