from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json
import shutil
import sys


EXAMPLE_CONFIG = """# Copy to config.yaml and edit for your installation.
freshrss:
  # Path to FreshRSS SQLite DB. For Docker, bind-mount the DB file or data dir.
  db_path: /path/to/FreshRSS/data/users/your-user/db.sqlite
  category: 论文

site:
  public_base_url: https://example.com/paper-feeds/summaries
  output_dir: ./site

codex:
  command: [codex, -a, never, -s, read-only, exec]
  timeout_seconds: 900
  reasoning_effort: low

runtime:
  state_dir: ./state
  curl_bin: curl
  pdftotext_bin: pdftotext
  pdf_timeout_seconds: 120
  pdf_max_chars: 60000
"""


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="oh-my-rss")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init-config", help="write an example config file")
    init.add_argument("--output", type=Path, default=Path("config.yaml"))

    run = sub.add_parser("run", help="summarize new research papers")
    run.add_argument("--config", type=Path, default=Path("config.yaml"))
    run.add_argument("--limit", type=int, default=1)
    run.add_argument("--since-days", type=int, default=7)
    run.add_argument("--lookback", type=int, default=1000)
    run.add_argument("--force-id")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--no-pdf", action="store_true")
    run.add_argument("--no-freshrss-link", action="store_true")

    doctor = sub.add_parser("doctor", help="check config paths and required commands")
    doctor.add_argument("--config", type=Path, default=Path("config.yaml"))

    validate = sub.add_parser("validate-site", help="validate generated public site files")
    validate.add_argument("--site-dir", type=Path, default=Path("site"))

    cron = sub.add_parser("print-cron", help="print a flock-protected cron entry")
    cron.add_argument("--cwd", type=Path, default=Path.cwd())
    cron.add_argument("--config", type=Path, default=Path("config.yaml"))
    cron.add_argument("--limit", type=int, default=1)
    cron.add_argument("--interval-minutes", type=int, default=10)
    cron.add_argument("--log-path", type=Path, default=Path("state/cron.log"))
    cron.add_argument("--lock-path", type=Path, default=Path("/tmp/oh-my-rss.lock"))
    cron.add_argument("--venv", type=Path, default=Path(".venv"))
    cron.add_argument("--no-venv", action="store_true")

    starter = sub.add_parser("print-starter-opml", help="print a FreshRSS starter OPML")
    starter.add_argument("--category", default="论文")
    starter.add_argument("--output", type=Path)

    validate_opml = sub.add_parser("validate-opml", help="validate OPML feed URLs")
    validate_opml.add_argument("--opml", type=Path, required=True)
    validate_opml.add_argument("--timeout", type=int, default=20)
    validate_opml.add_argument("--no-network", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-config":
        if args.output.exists():
            parser.error(f"{args.output} already exists")
        args.output.write_text(EXAMPLE_CONFIG, encoding="utf-8")
        print(f"wrote {args.output}")
        return 0

    if args.command == "run":
        missing = [tool for tool in ("curl", "pdftotext") if shutil.which(tool) is None]
        if missing and not args.no_pdf and not args.dry_run:
            parser.error(f"missing required tools for PDF mode: {', '.join(missing)}")
        from .app import run_once
        from .config import AppConfig

        config = AppConfig.from_yaml(args.config)
        changed = run_once(
            config,
            limit=args.limit,
            since_days=args.since_days,
            lookback=args.lookback,
            force_id=args.force_id,
            write_freshrss_links=not args.no_freshrss_link,
            use_pdf=not args.no_pdf,
            dry_run=args.dry_run,
        )
        print(json.dumps(changed, ensure_ascii=False, indent=2))
        return 0

    if args.command == "validate-site":
        from .validation import validate_site_output

        result = validate_site_output(args.site_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1

    if args.command == "doctor":
        from .diagnostics import run_doctor

        result = run_doctor(args.config)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1

    if args.command == "print-cron":
        from .scheduling import build_cron_line

        try:
            line = build_cron_line(
                cwd=args.cwd,
                config=args.config,
                limit=args.limit,
                interval_minutes=args.interval_minutes,
                log_path=args.log_path,
                lock_path=args.lock_path,
                venv_path=None if args.no_venv else args.venv,
            )
        except ValueError as exc:
            parser.error(str(exc))
        print(line)
        return 0

    if args.command == "print-starter-opml":
        from .starter_opml import render_starter_opml

        opml = render_starter_opml(category=args.category)
        if args.output:
            args.output.write_text(opml, encoding="utf-8")
            print(f"wrote {args.output}")
        else:
            print(opml, end="")
        return 0

    if args.command == "validate-opml":
        from .feed_validation import validate_opml_file

        result = validate_opml_file(
            args.opml,
            timeout_seconds=args.timeout,
            check_network=not args.no_network,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
