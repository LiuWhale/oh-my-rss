from __future__ import annotations

from pathlib import Path
import json
from xml.etree import ElementTree


REQUIRED_FILES = {
    "html": ["index.html"],
    "json": [
        "feeds.json",
        "status.json",
        "manifest.json",
        "categories/index.json",
    ],
    "opml": [
        "opml.xml",
        "categories/opml.xml",
    ],
    "rss": [
        "feed.xml",
        "reports/monthly.xml",
        "reports/trending.xml",
        "reports/keywords.xml",
    ],
    "xml": ["sitemap.xml"],
    "text": ["robots.txt"],
}


def validate_site_output(site_dir: Path) -> dict[str, object]:
    errors: list[str] = []
    checked: list[str] = []

    for kind, relatives in REQUIRED_FILES.items():
        for relative in relatives:
            path = site_dir / relative
            if not path.exists():
                errors.append(f"{relative} is missing")
                continue
            checked.append(relative)
            if kind == "json":
                validate_json(path, relative, errors)
            elif kind in {"rss", "opml", "xml"}:
                validate_xml(path, relative, errors)
            elif kind == "html":
                validate_nonempty(path, relative, errors)
            elif kind == "text":
                validate_nonempty(path, relative, errors)

    validate_feed_directory(site_dir / "feeds.json", errors)
    validate_status(site_dir / "status.json", errors)

    return {
        "ok": not errors,
        "site_dir": str(site_dir),
        "checked_count": len(checked),
        "checked": checked,
        "errors": errors,
    }


def validate_json(path: Path, relative: str, errors: list[str]) -> None:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - validation should report all parse failures
        errors.append(f"{relative} is not valid JSON: {exc}")


def validate_xml(path: Path, relative: str, errors: list[str]) -> None:
    try:
        ElementTree.parse(path)
    except Exception as exc:  # noqa: BLE001 - validation should report all parse failures
        errors.append(f"{relative} is not valid XML: {exc}")


def validate_nonempty(path: Path, relative: str, errors: list[str]) -> None:
    if not path.read_text(encoding="utf-8").strip():
        errors.append(f"{relative} is empty")


def validate_feed_directory(path: Path, errors: list[str]) -> None:
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    feeds = data.get("feeds")
    if not isinstance(feeds, list):
        errors.append("feeds.json does not contain a feeds list")
        return
    if data.get("feed_count") != len(feeds):
        errors.append("feeds.json feed_count does not match feeds length")


def validate_status(path: Path, errors: list[str]) -> None:
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    if data.get("ok") is not True:
        errors.append("status.json ok is not true")
