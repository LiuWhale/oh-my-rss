from __future__ import annotations

from datetime import datetime, timezone
import re
from urllib.request import urlopen
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

from .arxiv import Paper, clean_text, extract_arxiv_id


ARXIV_API_URL = "https://export.arxiv.org/api/query"
WIDE_ARXIV_KEYWORDS: tuple[str, ...] = (
    "robot",
    "robotics",
    "robot learning",
    "embodied ai",
    "manipulation",
    "dexterous",
    "humanoid",
    "locomotion",
    "motion planning",
    "visual navigation",
    "slam",
    "diffusion policy",
    "vision-language-action",
    "control barrier",
    "model predictive control",
)
WIDE_ARXIV_RELEVANCE_TERMS: tuple[str, ...] = (
    "robot",
    "robotic",
    "embodied",
    "physical ai",
    "robot manipulation",
    "dexterous",
    "grasp",
    "humanoid",
    "locomotion",
    "quadruped",
    "mobile robot",
    "robot motion planning",
    "autonomous navigation",
    "visual navigation",
    "slam",
    "simultaneous localization",
    "diffusion policy",
    "vision-language-action",
    "vision language action",
    "control barrier",
    "model predictive control",
    "tactile",
    "contact-rich",
)


def build_wide_arxiv_api_url(
    *,
    keywords: list[str] | tuple[str, ...] = WIDE_ARXIV_KEYWORDS,
    start: int = 0,
    max_results: int = 100,
) -> str:
    query = " OR ".join(f'all:"{keyword}"' for keyword in keywords)
    return (
        f"{ARXIV_API_URL}?"
        + urlencode(
            {
                "search_query": query,
                "start": int(start),
                "max_results": int(max_results),
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
        )
    )


def parse_arxiv_atom(atom_text: str, *, feed_name: str, feed_url: str = "") -> list[Paper]:
    root = ET.fromstring(atom_text)
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    papers: list[Paper] = []
    for entry in root.findall("atom:entry", ns):
        entry_id = entry.findtext("atom:id", default="", namespaces=ns)
        arxiv_id = extract_arxiv_id(entry_id)
        if not arxiv_id:
            continue
        title = clean_text(entry.findtext("atom:title", default="", namespaces=ns))
        summary = clean_text(entry.findtext("atom:summary", default="", namespaces=ns))
        authors = ", ".join(
            clean_text(author.findtext("atom:name", default="", namespaces=ns))
            for author in entry.findall("atom:author", ns)
            if author.findtext("atom:name", default="", namespaces=ns)
        )
        abs_url = ""
        pdf_url = ""
        for link in entry.findall("atom:link", ns):
            href = link.attrib.get("href", "")
            if link.attrib.get("type") == "application/pdf" or "/pdf/" in href:
                pdf_url = href
            elif link.attrib.get("rel") == "alternate":
                abs_url = href
        papers.append(
            Paper(
                arxiv_id=arxiv_id,
                title=title,
                authors=authors,
                abstract=summary,
                date=_parse_arxiv_epoch(
                    entry.findtext("atom:published", default="", namespaces=ns)
                    or entry.findtext("atom:updated", default="", namespaces=ns)
                ),
                feed_names=[feed_name] if feed_name else [],
                feed_urls=[feed_url] if feed_url else [],
                rss_link=abs_url or f"https://arxiv.org/abs/{arxiv_id}",
                guid=entry_id,
                paper_id=arxiv_id,
                source_kind="arXiv",
                source_url=abs_url or f"https://arxiv.org/abs/{arxiv_id}",
                pdf_url_override=pdf_url,
            )
        )
    return sorted(papers, key=lambda paper: paper.date, reverse=True)


def fetch_wide_arxiv_papers(
    *,
    keywords: list[str] | tuple[str, ...] | None = None,
    max_results: int = 100,
    timeout: int = 30,
) -> list[Paper]:
    discovery_keywords = tuple(keywords or WIDE_ARXIV_KEYWORDS)
    url = build_wide_arxiv_api_url(keywords=discovery_keywords, max_results=max_results)
    with urlopen(url, timeout=timeout) as response:  # noqa: S310 - URL is arXiv API from fixed builder.
        atom_text = response.read().decode("utf-8", errors="replace")
    return filter_relevant_wide_arxiv_papers(parse_arxiv_atom(atom_text, feed_name="arXiv wide discovery", feed_url=url))


def filter_relevant_wide_arxiv_papers(papers: list[Paper]) -> list[Paper]:
    return [paper for paper in papers if is_relevant_wide_arxiv_paper(paper)]


def is_relevant_wide_arxiv_paper(paper: Paper) -> bool:
    text = re.sub(r"[-_/]+", " ", f"{paper.title} {paper.abstract}".lower())
    text = re.sub(r"\s+", " ", text)
    return any(term in text for term in WIDE_ARXIV_RELEVANCE_TERMS)


def merge_paper_candidates(*paper_lists: list[Paper]) -> list[Paper]:
    merged: dict[str, Paper] = {}
    for papers in paper_lists:
        for paper in papers:
            key = _merge_key(paper)
            existing = merged.get(key)
            if not existing:
                merged[key] = paper
                continue
            _merge_into(existing, paper)
    return sorted(merged.values(), key=lambda paper: paper.date, reverse=True)


def _parse_arxiv_epoch(value: str) -> int:
    if not value:
        return 0
    normalized = re.sub(r"Z$", "+00:00", value.strip())
    return int(datetime.fromisoformat(normalized).astimezone(timezone.utc).timestamp())


def _merge_key(paper: Paper) -> str:
    return paper.base_id if paper.source_kind == "ArXiv" else paper.paper_id or paper.arxiv_id


def _merge_into(existing: Paper, paper: Paper) -> None:
    if paper.date >= existing.date:
        existing.title = paper.title or existing.title
        existing.authors = paper.authors or existing.authors
        existing.rss_link = paper.rss_link or existing.rss_link
        existing.guid = paper.guid or existing.guid
        existing.source_url = paper.source_url or existing.source_url
        existing.pdf_url_override = paper.pdf_url_override or existing.pdf_url_override
        existing.date = paper.date
    if len(paper.abstract) > len(existing.abstract):
        existing.abstract = paper.abstract
    for entry_id in paper.entry_ids:
        if entry_id not in existing.entry_ids:
            existing.entry_ids.append(entry_id)
    for feed_name in paper.feed_names:
        if feed_name not in existing.feed_names:
            existing.feed_names.append(feed_name)
    for feed_url in paper.feed_urls:
        if feed_url not in existing.feed_urls:
            existing.feed_urls.append(feed_url)
