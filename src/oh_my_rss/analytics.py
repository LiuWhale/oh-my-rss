from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import re


@dataclass(frozen=True)
class PaperReference:
    title: str
    url: str
    generated_at: str
    source: str
    directions: list[str] = field(default_factory=list)
    summary_excerpt: str = ""


@dataclass(frozen=True)
class MonthlyReport:
    month: str
    generated_at: str
    total_papers: int
    direction_counts: dict[str, int]
    source_counts: dict[str, int]
    direction_growth: dict[str, int]
    direction_scores: dict[str, float]
    top_papers: list[PaperReference]
    trend_months: list[str]
    trend_counts: dict[str, list[int]]

    @property
    def title(self) -> str:
        return f"{self.month} 研究趋势月报"

    @property
    def summary(self) -> str:
        directions = sorted(
            self.direction_counts.items(),
            key=lambda item: (-self.direction_scores.get(item[0], item[1]), item[0]),
        )
        if not directions:
            return f"{self.month} 暂无可统计的论文总结。"
        highlights = "、".join(f"{name} {count} 篇" for name, count in directions[:3])
        return f"{self.month} 共收录 {self.total_papers} 篇论文总结，热门方向包括 {highlights}。"


def build_monthly_reports(
    records: list[dict[str, object]],
    *,
    generated_at: str,
    months: int = 12,
) -> list[MonthlyReport]:
    papers_by_month: dict[str, list[PaperReference]] = defaultdict(list)
    all_months: set[str] = set()

    for record in records:
        if not record.get("url"):
            continue
        month = record_month(record)
        if not month:
            continue
        all_months.add(month)
        papers_by_month[month].append(
            PaperReference(
                title=str(record.get("title") or record.get("arxiv_id") or "Untitled paper"),
                url=str(record["url"]),
                generated_at=str(record.get("generated_at") or ""),
                source=record_source(record),
                directions=record_directions(record),
                summary_excerpt=str(record.get("summary_excerpt") or ""),
            )
        )

    if not all_months:
        return []

    sorted_months = sorted(all_months)
    trend_months = sorted_months[-months:]
    reports: list[MonthlyReport] = []

    for month in reversed(trend_months):
        papers = papers_by_month.get(month, [])
        previous_month = previous_month_key(month)
        direction_counts = count_directions(papers)
        previous_counts = count_directions(papers_by_month.get(previous_month, []))
        source_counts = count_sources(papers)
        direction_growth = {
            name: count - previous_counts.get(name, 0) for name, count in direction_counts.items()
        }
        direction_scores = score_directions(direction_counts, direction_growth, source_counts)
        trend_directions = top_trend_directions(
            papers_by_month=papers_by_month,
            trend_months=trend_months,
            current_counts=direction_counts,
        )
        trend_counts = {
            name: [count_directions(papers_by_month.get(item, [])).get(name, 0) for item in trend_months]
            for name in trend_directions
        }
        reports.append(
            MonthlyReport(
                month=month,
                generated_at=generated_at,
                total_papers=len(papers),
                direction_counts=dict(sorted(direction_counts.items())),
                source_counts=dict(sorted(source_counts.items())),
                direction_growth=dict(sorted(direction_growth.items())),
                direction_scores=dict(sorted(direction_scores.items())),
                top_papers=sorted(papers, key=lambda item: item.generated_at, reverse=True)[:20],
                trend_months=trend_months,
                trend_counts=trend_counts,
            )
        )

    return reports


def record_month(record: dict[str, object]) -> str:
    generated_at = str(record.get("generated_at") or "")
    if not generated_at:
        return ""
    try:
        return datetime.fromisoformat(generated_at).strftime("%Y-%m")
    except ValueError:
        match = re.match(r"^(\d{4}-\d{2})", generated_at)
        return match.group(1) if match else ""


def record_directions(record: dict[str, object]) -> list[str]:
    raw = record.get("research_domains") or record.get("feed_names") or []
    if isinstance(raw, str):
        values = [raw]
    else:
        values = list(raw) if isinstance(raw, list | tuple | set) else []
    directions = unique_strings(normalize_direction(item) for item in values)
    return directions or ["Uncategorized"]


def record_source(record: dict[str, object]) -> str:
    explicit = first_string(record.get("venue"), record.get("source"), record.get("publication"))
    if explicit:
        return normalize_source(explicit)
    feed_names = record.get("feed_names") or []
    if isinstance(feed_names, str):
        feed_values = [feed_names]
    else:
        feed_values = list(feed_names) if isinstance(feed_names, list | tuple | set) else []
    for feed_name in feed_values:
        source = infer_source(str(feed_name))
        if source:
            return source
    if record.get("arxiv_id"):
        return "arXiv"
    return "Unknown"


def normalize_direction(value: object) -> str:
    text = str(value).strip()
    if text.startswith("arXiv "):
        text = text[len("arXiv ") :].strip()
    return re.sub(r"\s+", " ", text)


def normalize_source(value: str) -> str:
    text = normalize_direction(value)
    known = infer_source(text)
    return known or text


def infer_source(value: str) -> str:
    text = value.strip()
    upper = text.upper()
    if "ARXIV" in upper:
        return "arXiv"
    known_pairs = [
        ("SOFT ROBOTICS", "Soft Robotics"),
        ("IJRR", "IJRR"),
        ("INTERNATIONAL JOURNAL OF ROBOTICS RESEARCH", "IJRR"),
        ("TRO", "TRO"),
        ("TRANSACTIONS ON ROBOTICS", "TRO"),
        ("RAL", "RAL"),
        ("ROBOTICS AND AUTOMATION LETTERS", "RAL"),
        ("ICRA", "ICRA"),
        ("IROS", "IROS"),
        ("RSS", "RSS"),
        ("NEURIPS", "NeurIPS"),
        ("NIPS", "NeurIPS"),
        ("ICML", "ICML"),
        ("ICLR", "ICLR"),
        ("IEEE XPLORE", "IEEE Xplore"),
    ]
    for needle, label in known_pairs:
        if needle in upper:
            return label
    return ""


def count_directions(papers: list[PaperReference]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for paper in papers:
        for direction in paper.directions:
            counts[direction] += 1
    return counts


def count_sources(papers: list[PaperReference]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for paper in papers:
        counts[paper.source] += 1
    return counts


def score_directions(
    direction_counts: Counter[str],
    direction_growth: dict[str, int],
    source_counts: Counter[str],
) -> dict[str, float]:
    source_diversity_bonus = 0.2 * max(len(source_counts), 1)
    return {
        name: count + max(direction_growth.get(name, 0), 0) * 0.8 + source_diversity_bonus
        for name, count in direction_counts.items()
    }


def top_trend_directions(
    *,
    papers_by_month: dict[str, list[PaperReference]],
    trend_months: list[str],
    current_counts: Counter[str],
    limit: int = 5,
) -> list[str]:
    total_counts: Counter[str] = Counter()
    for month in trend_months:
        total_counts.update(count_directions(papers_by_month.get(month, [])))
    names = set(total_counts) | set(current_counts)
    return sorted(names, key=lambda name: (-current_counts.get(name, 0), -total_counts[name], name))[:limit]


def previous_month_key(month: str) -> str:
    year, month_number = (int(part) for part in month.split("-", maxsplit=1))
    if month_number == 1:
        return f"{year - 1}-12"
    return f"{year}-{month_number - 1:02d}"


def unique_strings(values: object) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def first_string(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""
