from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree


@dataclass(frozen=True)
class FeedSource:
    title: str
    xml_url: str
    html_url: str = ""


FeedFetcher = Callable[[str, int], dict[str, object]]


def parse_opml_feeds(opml_text: str) -> list[FeedSource]:
    root = ElementTree.fromstring(opml_text)
    feeds: list[FeedSource] = []
    for outline in root.findall(".//outline"):
        xml_url = (outline.attrib.get("xmlUrl") or outline.attrib.get("xmlurl") or "").strip()
        if not xml_url:
            continue
        title = (
            outline.attrib.get("text")
            or outline.attrib.get("title")
            or outline.attrib.get("description")
            or xml_url
        )
        feeds.append(
            FeedSource(
                title=title.strip(),
                xml_url=xml_url,
                html_url=(outline.attrib.get("htmlUrl") or outline.attrib.get("htmlurl") or "").strip(),
            )
        )
    return feeds


def validate_opml_file(
    path: Path,
    *,
    timeout_seconds: int = 20,
    check_network: bool = True,
    fetcher: FeedFetcher | None = None,
) -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 - report validation errors as data
        return {
            "ok": False,
            "opml": str(path),
            "checked_network": check_network,
            "feed_count": 0,
            "failure_count": 1,
            "feeds": [],
            "errors": [f"could not read OPML: {exc}"],
        }
    result = validate_opml_text(
        text,
        timeout_seconds=timeout_seconds,
        check_network=check_network,
        fetcher=fetcher,
    )
    result["opml"] = str(path)
    return result


def validate_opml_text(
    opml_text: str,
    *,
    timeout_seconds: int = 20,
    check_network: bool = True,
    fetcher: FeedFetcher | None = None,
) -> dict[str, object]:
    try:
        feeds = parse_opml_feeds(opml_text)
    except Exception as exc:  # noqa: BLE001 - report validation errors as data
        return {
            "ok": False,
            "checked_network": check_network,
            "feed_count": 0,
            "failure_count": 1,
            "feeds": [],
            "errors": [f"OPML is not valid XML: {exc}"],
        }

    if check_network:
        fetch = fetcher or fetch_feed_url
        feed_results = [
            {
                "title": feed.title,
                "xml_url": feed.xml_url,
                "html_url": feed.html_url,
                **fetch(feed.xml_url, timeout_seconds),
            }
            for feed in feeds
        ]
    else:
        feed_results = [
            {
                "title": feed.title,
                "xml_url": feed.xml_url,
                "html_url": feed.html_url,
                "ok": None,
                "status": None,
                "content_type": "",
                "message": "not checked",
            }
            for feed in feeds
        ]

    failures = [item for item in feed_results if item["ok"] is False]
    errors = [] if feeds else ["OPML contains no xmlUrl feed outlines"]
    return {
        "ok": not failures and not errors,
        "checked_network": check_network,
        "feed_count": len(feeds),
        "failure_count": len(failures) + len(errors),
        "feeds": feed_results,
        "errors": errors,
    }


def fetch_feed_url(url: str, timeout_seconds: int) -> dict[str, object]:
    request = Request(
        url,
        headers={
            "User-Agent": "oh-my-rss feed validator",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - user-provided feed URL checker
            status = getattr(response, "status", None) or response.getcode()
            content_type = response.headers.get("content-type", "")
            sample = response.read(8192)
    except HTTPError as exc:
        return {
            "ok": False,
            "status": exc.code,
            "content_type": exc.headers.get("content-type", "") if exc.headers else "",
            "message": f"HTTP {exc.code}",
        }
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "ok": False,
            "status": None,
            "content_type": "",
            "message": str(exc),
        }

    looks_like_feed = sample.lstrip().startswith(
        (b"<?xml", b"<rss", b"<feed", b"<rdf:RDF", b"<rdf")
    )
    return {
        "ok": bool(200 <= int(status) < 400 and looks_like_feed),
        "status": int(status),
        "content_type": content_type,
        "message": "feed-like XML" if looks_like_feed else "response did not look like RSS/Atom XML",
    }
