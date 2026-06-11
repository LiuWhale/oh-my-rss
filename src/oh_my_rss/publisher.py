from __future__ import annotations

from pathlib import Path
import hashlib
import json
import re
import shutil

from .arxiv import Paper
from .render import render_detail_html, render_index_html, render_rss_xml


def detail_filename(arxiv_id: str, summary_sha256: str) -> str:
    safe = arxiv_id.replace("/", "_")
    return f"{safe}-{summary_sha256[:12]}.html"


def publish_detail(paper: Paper, markdown: str, output_dir: Path, public_base_url: str, generated_at: str) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    name = detail_filename(paper.arxiv_id, sha)
    html = render_detail_html(
        title=paper.title,
        arxiv_id=paper.arxiv_id,
        feeds=paper.feed_names,
        abs_url=paper.abs_url,
        pdf_url=paper.pdf_url,
        markdown=markdown,
        generated_at=generated_at,
    )
    detail_path = output_dir / name
    detail_path.write_text(html, encoding="utf-8")
    stable_path = output_dir / f"{paper.slug}.html"
    shutil.copyfile(detail_path, stable_path)
    return {
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "url": f"{public_base_url.rstrip('/')}/{name}",
        "detail_name": name,
        "generated_at": generated_at,
        "summary_sha256": sha,
        "feed_names": paper.feed_names,
        "entry_ids": paper.entry_ids,
        "summary_excerpt": summary_excerpt(markdown),
        "summary_source": "pdf" if paper.pdf_context else "rss",
        "pdf_text_chars": paper.pdf_text_chars,
        "pdf_context_chars": paper.pdf_context_chars,
        "pdf_error": paper.pdf_error,
    }


def publish_index(records: list[dict[str, object]], output_dir: Path, generated_at: str) -> None:
    done = [record for record in records if record.get("url")]
    done.sort(key=lambda item: str(item.get("generated_at", "")), reverse=True)
    html = render_index_html(done, generated_at)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(html, encoding="utf-8")


def publish_feed(
    records: list[dict[str, object]],
    output_dir: Path,
    public_base_url: str,
    generated_at: str,
) -> None:
    done = [record for record in records if record.get("url")]
    done.sort(key=lambda item: str(item.get("generated_at", "")), reverse=True)
    xml = render_rss_xml(done, generated_at=generated_at, public_base_url=public_base_url)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "feed.xml").write_text(xml, encoding="utf-8")


def write_manifest(records: list[dict[str, object]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def summary_excerpt(markdown: str, max_chars: int = 500) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", markdown)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = re.sub(r"^\s*[-*]\s*", "", text, flags=re.M)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "..."
