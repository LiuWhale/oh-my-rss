# Changelog

All notable changes to Oh My RSS are documented in this file.

This project follows a practical changelog format inspired by
Keep a Changelog. Version tags use semantic versioning.

## [Unreleased]

### Added

- Add a Simplified Chinese README and language links between the English and
  Chinese documentation entry points.

### Fixed

- Avoid classifying VLM/LLM-based 3D semantic scene-graph papers as VLA merely
  because they mention robotics applications; VLA now needs explicit action,
  policy, control, or manipulation evidence.

## [0.1.15] - 2026-06-24

### Fixed

- Avoid classifying navigation world-model papers as VLA from generic
  `multimodal` action or trajectory wording unless explicit VLA,
  vision-language, language-conditioned, or VLM evidence is present.
- Require explicit domain evidence for paper categories instead of deriving
  fields from source feed labels or generic words such as `policy`,
  `navigation`, `manipulation`, `control`, or `learning`.
- Write stale-running recovery timestamps with a deterministic timezone instead
  of depending on the host machine's local timezone.

## [0.1.14] - 2026-06-24

### Fixed

- Recompute paper categories from title, abstract, keywords, and generated
  summary excerpts instead of trusting stale `research_domains` from earlier
  discovery runs.
- Keep arXiv discovery feeds out of published category feeds so source labels
  such as `arXiv Robotics latest (cs.RO)` do not masquerade as final research
  fields.
- Persist abstracts on generated summary records so later feed rebuilds can
  classify papers without falling back to old feed labels.

## [0.1.13] - 2026-06-24

### Fixed

- Rebuild the public main RSS feed, category feeds, reports, and status files
  after each generated summary instead of waiting for the full batch to finish,
  so RSS clients can see new papers during long summary runs.

## [0.1.12] - 2026-06-24

### Fixed

- Recover stale `running` paper records automatically after six hours, so a
  crashed or interrupted summary job cannot leave one paper permanently stuck
  in an in-progress state.

## [0.1.11] - 2026-06-24

### Fixed

- Normalize FreshRSS entry IDs before updating generated Codex summary links,
  so mixed string and integer IDs from existing state files do not break link
  repair or RSS-only refresh runs.

## [0.1.10] - 2026-06-23

### Fixed

- Classify research domains from abstract and keyword evidence first, with
  paper titles used only as auxiliary evidence when the abstract or keywords
  provide matching domain context.
- Prevent title-only Vision-Language-Action wording from pushing visual action
  understanding papers into VLA or robotics categories without robot policy,
  manipulation, or control evidence.
- Preserve paper keywords in published records so later reports and
  reclassification passes can reuse the same evidence.

## [0.1.9] - 2026-06-23

### Fixed

- Normalize category keyword matching across abbreviations, full names, spaces,
  slashes, hyphens, and Unicode dashes so variants such as `VLA`,
  `Vision-Language-Action`, `Vision/Language/Action`, and
  `Vision–Language–Action` are treated consistently.
- Tighten VLA and robotics context matching so visual action understanding and
  biological locomotion papers are not pulled into robot VLA or robotics feeds
  without robot/policy/control context.

## [0.1.8] - 2026-06-22

### Fixed

- Tighten broad category matching for robot policy, safety/control,
  benchmark/dataset, and embodied/foundation-model labels so generic words such
  as `policy`, `safety`, `evaluation`, and `foundation model` do not create
  unrelated category assignments without domain context.
- Add regression coverage for common false positives while preserving explicit
  VLA, robot imitation learning, CBF/safe-control, benchmark, and vision
  segmentation matches.

## [0.1.7] - 2026-06-22

### Fixed

- Tighten VLA classification so stale generated category labels cannot
  reinforce themselves, while explicit Vision-Language-Action papers still
  classify as VLA.
- Classify generic segmentation papers into vision/perception instead of
  falling back to stale category labels.

## [0.1.6] - 2026-06-22

### Fixed

- Keep duplicate category aliases in sync when publishing category RSS feeds,
  so equivalent category URLs keep receiving the same updated item set instead
  of drifting apart.

## [0.1.5] - 2026-06-22

### Added

- Add optional broad arXiv API discovery for papers that do not appear in the
  subscribed FreshRSS arXiv subjects. Discovered papers are still grouped by
  content-derived research-domain labels, not by arXiv subject names.
- Add a source health radar with HTML, JSON, and RSS outputs so self-hosted
  runs can see per-source candidate counts, fetch failures, sudden zero-count
  drops, and stale venue years.
- Add the source health radar to `feeds.json`, `status.json`, sitemap output,
  and the generated OPML subscription bundle.

### Fixed

- Show broad arXiv discovery papers as `arXiv` in generated metadata instead
  of exposing the internal discovery label.
- Keep historical release backfills from replacing the current version as the
  GitHub latest release.
- Set the release workflow repository context explicitly so GitHub Releases are
  created against the intended repository.

## [0.1.4] - 2026-06-13

### Fixed

- Add a GitHub Actions release workflow so version tags publish GitHub Releases
  with source and wheel artifacts.
- Group category OPML exports under `Oh My RSS 论文分类` so RSS clients that
  preserve OPML folders import all category feeds into one folder.
- Make report RSS descriptions render their `查看网页` targets as clickable
  HTML links.
- Point hot-topic and hot-keyword RSS items to aggregate report pages with
  anchors, and remove stale per-topic/per-keyword detail pages during
  publishing.

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
