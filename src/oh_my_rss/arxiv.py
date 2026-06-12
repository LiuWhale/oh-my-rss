from __future__ import annotations

from dataclasses import dataclass, field
import html
import re
from typing import Any


ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)", re.I)
OLD_ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([a-z.-]+/[0-9]{7}(?:v\d+)?)", re.I)


@dataclass
class Paper:
    arxiv_id: str
    title: str
    authors: str = ""
    abstract: str = ""
    date: int = 0
    entry_ids: list[int] = field(default_factory=list)
    feed_names: list[str] = field(default_factory=list)
    feed_urls: list[str] = field(default_factory=list)
    rss_link: str = ""
    guid: str = ""
    pdf_context: str = ""
    pdf_text_chars: int | None = None
    pdf_context_chars: int | None = None
    pdf_error: str | None = None
    hero_image_url: str = ""
    hero_image_error: str | None = None

    @property
    def base_id(self) -> str:
        return re.sub(r"v\d+$", "", self.arxiv_id)

    @property
    def slug(self) -> str:
        return slug_for(self.arxiv_id)

    @property
    def abs_url(self) -> str:
        return f"https://arxiv.org/abs/{self.arxiv_id}"

    @property
    def pdf_url(self) -> str:
        if self.rss_link and "/pdf/" in self.rss_link:
            return self.rss_link
        return f"https://arxiv.org/pdf/{self.arxiv_id}"


def slug_for(arxiv_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", arxiv_id)


def clean_text(value: Any) -> str:
    if not value:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_arxiv_id(*values: str | None) -> str | None:
    for value in values:
        if not value:
            continue
        match = ARXIV_RE.search(value) or OLD_ARXIV_RE.search(value)
        if match:
            return match.group(1)
    return None


def group_entries(rows: list[dict[str, Any]]) -> list[Paper]:
    grouped: dict[str, Paper] = {}
    for row in rows:
        arxiv_id = extract_arxiv_id(
            row.get("guid"),
            row.get("link"),
            row.get("content"),
            row.get("feed_url"),
        )
        if not arxiv_id:
            continue

        paper = grouped.setdefault(
            arxiv_id,
            Paper(
                arxiv_id=arxiv_id,
                title=clean_text(row.get("title")),
                authors=clean_text(row.get("author")),
                abstract=clean_text(row.get("content")),
                date=int(row.get("date") or 0),
                rss_link=row.get("link") or "",
                guid=row.get("guid") or "",
            ),
        )

        entry_id = int(row["id"])
        if entry_id not in paper.entry_ids:
            paper.entry_ids.append(entry_id)

        feed_name = clean_text(row.get("feed_name"))
        if feed_name and feed_name not in paper.feed_names:
            paper.feed_names.append(feed_name)

        feed_url = row.get("feed_url") or ""
        if feed_url and feed_url not in paper.feed_urls:
            paper.feed_urls.append(feed_url)

        row_date = int(row.get("date") or 0)
        if row_date > paper.date:
            paper.date = row_date

        abstract = clean_text(row.get("content"))
        if len(abstract) > len(paper.abstract):
            paper.abstract = abstract

        if not paper.authors and row.get("author"):
            paper.authors = clean_text(row.get("author"))

        if not paper.rss_link and row.get("link"):
            paper.rss_link = row.get("link")

    return sorted(grouped.values(), key=lambda item: item.date, reverse=True)
