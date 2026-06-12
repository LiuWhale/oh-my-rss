from __future__ import annotations

from pathlib import Path
import re
import subprocess

from .arxiv import Paper


def normalize_pdf_text(text: str) -> str:
    text = text.replace("\x0c", "\n\n[PAGE BREAK]\n\n")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    lines: list[str] = []
    previous_blank = False
    for raw in text.splitlines():
        line = re.sub(r"[ \t]+", " ", raw).strip()
        if not line:
            if not previous_blank:
                lines.append("")
            previous_blank = True
            continue
        lines.append(line)
        previous_blank = False
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    merged = [list(item) for item in sorted(ranges)[:1]]
    for start, end in sorted(ranges)[1:]:
        last = merged[-1]
        if start <= last[1] + 500:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def select_pdf_context(text: str, max_chars: int = 60_000) -> str:
    lower = text.lower()
    method_keywords = [
        "method",
        "methodology",
        "approach",
        "framework",
        "architecture",
        "model",
        "algorithm",
        "policy",
        "loss",
        "training",
    ]
    experiment_keywords = [
        "experiment",
        "evaluation",
        "result",
        "ablation",
        "baseline",
        "metric",
        "success rate",
        "real-robot",
        "appendix",
    ]

    def find_ranges(keywords: list[str]) -> list[tuple[int, int]]:
        found: list[tuple[int, int]] = []
        for keyword in keywords:
            start = 0
            hits = 0
            while hits < 3:
                idx = lower.find(keyword, start)
                if idx < 0:
                    break
                found.append((max(0, idx - 120), min(len(text), idx + 5000)))
                start = idx + len(keyword)
                hits += 1
        return sorted(found)

    chunks: list[str] = []
    used = 0
    intro_budget = min(len(text), max(250, max_chars // 4), 5000)
    if intro_budget:
        chunks.append(f"[PDF excerpt chars 0-{intro_budget}]\n{text[:intro_budget].strip()}")
        used += intro_budget

    per_range_budget = max(500, min(8000, max_chars // 3))
    seen_spans: list[tuple[int, int]] = []
    prioritized = find_ranges(method_keywords)[:2] + find_ranges(experiment_keywords)[:3]
    for start, end in prioritized:
        end = min(end, start + per_range_budget)
        if any(abs(start - old_start) < 1000 for old_start, _ in seen_spans):
            continue
        chunk = text[start:end].strip()
        if not chunk:
            continue
        remaining = max_chars - used
        if remaining <= 0:
            break
        if len(chunk) > remaining:
            chunk = chunk[:remaining]
        chunks.append(f"[PDF excerpt chars {start}-{start + len(chunk)}]\n{chunk}")
        used += len(chunk)
        seen_spans.append((start, end))
    return "\n\n---\n\n".join(chunks)


def download_pdf(paper: Paper, pdf_dir: Path, curl_bin: str, timeout: int) -> Path:
    pdf_dir.mkdir(parents=True, exist_ok=True)
    if not paper.pdf_url:
        raise RuntimeError(f"no direct PDF URL for {paper.paper_id or paper.arxiv_id}")
    pdf_path = pdf_dir / f"{paper.slug}.pdf"
    if pdf_path.exists() and pdf_path.stat().st_size >= 1024:
        return pdf_path

    tmp_pdf = pdf_path.with_suffix(".pdf.tmp")
    if tmp_pdf.exists():
        tmp_pdf.unlink()
    subprocess.run(
        [
            curl_bin,
            "-L",
            "--fail",
            "--silent",
            "--show-error",
            "--max-time",
            str(timeout),
            "-o",
            str(tmp_pdf),
            paper.pdf_url,
        ],
        check=True,
        timeout=timeout + 20,
    )
    if tmp_pdf.stat().st_size < 1024:
        raise RuntimeError(f"downloaded PDF is too small: {paper.pdf_url}")
    tmp_pdf.replace(pdf_path)
    return pdf_path


def extract_pdf_text(pdf_path: Path, pdftotext_bin: str, timeout: int) -> str:
    result = subprocess.run(
        [pdftotext_bin, "-layout", "-enc", "UTF-8", str(pdf_path), "-"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )
    text = normalize_pdf_text(result.stdout)
    if len(text) < 2000:
        raise RuntimeError(f"extracted PDF text is too short: {len(text)} chars")
    return text


def render_pdf_first_page_preview(
    pdf_path: Path,
    output_dir: Path,
    public_base_url: str,
    slug: str,
    *,
    zoom: float = 1.6,
) -> str:
    try:
        import pymupdf
    except ModuleNotFoundError:  # pragma: no cover - compatibility for older PyMuPDF imports
        import fitz as pymupdf

    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    image_name = f"{slug}-main.png"
    image_path = assets_dir / image_name

    doc = pymupdf.open(pdf_path)
    try:
        if doc.page_count < 1:
            raise RuntimeError(f"PDF has no pages: {pdf_path}")
        page = doc.load_page(0)
        matrix = pymupdf.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        pixmap.save(image_path)
    finally:
        doc.close()

    if image_path.stat().st_size < 1024:
        raise RuntimeError(f"rendered preview image is too small: {image_path}")
    return f"{public_base_url.rstrip('/')}/assets/{image_name}"
