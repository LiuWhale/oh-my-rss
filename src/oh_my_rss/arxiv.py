from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import html
import re
from typing import Any


ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)", re.I)
OLD_ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/([a-z.-]+/[0-9]{7}(?:v\d+)?)", re.I)
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.I)
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
PDF_URL_RE = re.compile(r"https?://[^\s\"'<>]+?\.pdf(?:\?[^\s\"'<>]*)?", re.I)


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
    paper_id: str = ""
    source_kind: str = "arXiv"
    source_url: str = ""
    pdf_url_override: str = ""
    pdf_context: str = ""
    pdf_text_chars: int | None = None
    pdf_context_chars: int | None = None
    pdf_error: str | None = None
    hero_image_url: str = ""
    hero_image_error: str | None = None

    @property
    def base_id(self) -> str:
        if self.source_kind == "arXiv":
            return re.sub(r"v\d+$", "", self.arxiv_id)
        return self.paper_id or self.arxiv_id

    @property
    def slug(self) -> str:
        return slug_for(self.paper_id or self.arxiv_id)

    @property
    def abs_url(self) -> str:
        if self.source_url:
            return self.source_url
        if self.source_kind != "arXiv":
            return self.rss_link
        return f"https://arxiv.org/abs/{self.arxiv_id}"

    @property
    def pdf_url(self) -> str:
        if self.pdf_url_override:
            return self.pdf_url_override
        if self.source_kind != "arXiv":
            return ""
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


def extract_doi(*values: str | None) -> str | None:
    for value in values:
        if not value:
            continue
        match = DOI_RE.search(html.unescape(str(value)))
        if match:
            return match.group(1).rstrip(".,;").lower()
    return None


def extract_pdf_url(*values: str | None) -> str:
    for value in values:
        if not value:
            continue
        match = PDF_URL_RE.search(html.unescape(str(value)))
        if match:
            return match.group(0).rstrip(".,;")
    return ""


def first_url(*values: str | None) -> str:
    for value in values:
        if not value:
            continue
        match = URL_RE.search(html.unescape(str(value)))
        if match:
            return match.group(0).rstrip(".,;")
    return ""


def identify_paper(row: dict[str, Any]) -> tuple[str, str, str, str] | None:
    values = (
        row.get("guid"),
        row.get("link"),
        row.get("content"),
        row.get("feed_url"),
    )
    arxiv_id = extract_arxiv_id(*values)
    if arxiv_id:
        return (
            arxiv_id,
            "arXiv",
            f"https://arxiv.org/abs/{arxiv_id}",
            extract_pdf_url(*values),
        )

    doi = extract_doi(*values)
    source_url = first_url(row.get("link"), row.get("guid"), row.get("content"))
    pdf_url = extract_pdf_url(*values)
    if doi:
        return (f"doi:{doi}", "DOI", source_url or f"https://doi.org/{doi}", pdf_url)

    if source_url:
        digest = hashlib.sha1(source_url.encode("utf-8")).hexdigest()[:16]
        return (f"url:{digest}", "RSS", source_url, pdf_url)
    return None


def group_entries(rows: list[dict[str, Any]]) -> list[Paper]:
    grouped: dict[str, Paper] = {}
    for row in rows:
        identity = identify_paper(row)
        if not identity:
            continue
        paper_id, source_kind, source_url, pdf_url = identity

        paper = grouped.setdefault(
            paper_id,
            Paper(
                arxiv_id=paper_id,
                title=clean_text(row.get("title")),
                authors=clean_text(row.get("author")),
                abstract=clean_text(row.get("content")),
                date=int(row.get("date") or 0),
                rss_link=row.get("link") or "",
                guid=row.get("guid") or "",
                paper_id=paper_id,
                source_kind=source_kind,
                source_url=source_url,
                pdf_url_override=pdf_url,
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

        if not paper.source_url and source_url:
            paper.source_url = source_url

        if not paper.pdf_url_override and pdf_url:
            paper.pdf_url_override = pdf_url

    return sorted(grouped.values(), key=lambda item: item.date, reverse=True)
