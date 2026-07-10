from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import re

from .domains import classify_record_domains


@dataclass(frozen=True)
class PaperReference:
    title: str
    url: str
    generated_at: str
    source: str
    published_at: str = ""
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
    papers: list[PaperReference]
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


@dataclass(frozen=True)
class TrendingTopic:
    name: str
    month: str
    generated_at: str
    paper_count: int
    growth: int
    score: float
    source_counts: dict[str, int]
    papers: list[PaperReference]
    trend_months: list[str]
    trend_counts: list[int]

    @property
    def title(self) -> str:
        return f"{self.name} - {self.month} 热点方向"

    @property
    def summary(self) -> str:
        growth_text = f"+{self.growth}" if self.growth > 0 else str(self.growth)
        return (
            f"{self.month} {self.name} 方向收录 {self.paper_count} 篇论文，"
            f"环比 {growth_text}，热度分 {self.score:.1f}。"
        )


@dataclass(frozen=True)
class KeywordTrend:
    keyword: str
    month: str
    generated_at: str
    paper_count: int
    growth: int
    score: float
    source_counts: dict[str, int]
    papers: list[PaperReference]
    trend_months: list[str]
    trend_counts: list[int]

    @property
    def title(self) -> str:
        return f"{self.keyword} - {self.month} 关键词趋势"

    @property
    def summary(self) -> str:
        growth_text = f"+{self.growth}" if self.growth > 0 else str(self.growth)
        return (
            f"{self.month} 关键词 {self.keyword} 出现在 {self.paper_count} 篇论文中，"
            f"环比 {growth_text}，热度分 {self.score:.1f}。"
        )


KEYWORD_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("VLA", ("vla", "vision-language-action", "vision language action")),
    ("Diffusion Policy", ("diffusion policy", "diffusion policies")),
    ("Humanoid", ("humanoid", "humanoids")),
    ("SLAM", ("slam", "simultaneous localization")),
    ("Safety Filter", ("safety filter", "safe filter", "control barrier", "cbf")),
    ("MPC", ("mpc", "model predictive control")),
    ("Foundation Model", ("foundation model", "foundation models")),
    ("LLM", ("llm", "large language model", "large language models")),
    ("World Model", ("world model", "world models")),
    ("Dexterous Manipulation", ("dexterous", "dexterous manipulation", "in-hand", "in hand")),
    ("Imitation Learning", ("imitation learning", "behavior cloning")),
    ("Reinforcement Learning", ("reinforcement learning", "offline rl", "safe rl")),
    ("Point Cloud", ("point cloud", "point-cloud")),
    ("Benchmark", ("benchmark", "dataset", "evaluation", "leaderboard")),
    ("Sim-to-Real", ("sim-to-real", "sim to real", "domain randomization")),
]
KEYWORD_PRIORITY = {keyword: index for index, (keyword, _) in enumerate(KEYWORD_RULES)}


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
                published_at=str(record.get("source_published_at") or ""),
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
        ordered_papers = sorted(papers, key=lambda item: item.generated_at, reverse=True)
        reports.append(
            MonthlyReport(
                month=month,
                generated_at=generated_at,
                total_papers=len(papers),
                direction_counts=dict(sorted(direction_counts.items())),
                source_counts=dict(sorted(source_counts.items())),
                direction_growth=dict(sorted(direction_growth.items())),
                direction_scores=dict(sorted(direction_scores.items())),
                top_papers=ordered_papers[:20],
                papers=ordered_papers,
                trend_months=trend_months,
                trend_counts=trend_counts,
            )
        )

    return reports


def build_trending_topics(
    records: list[dict[str, object]],
    *,
    generated_at: str,
    month: str | None = None,
    months: int = 12,
    limit: int = 10,
) -> list[TrendingTopic]:
    papers_by_month = group_paper_references_by_month(records)
    if not papers_by_month:
        return []

    target_month = month or sorted(papers_by_month)[-1]
    current_papers = papers_by_month.get(target_month, [])
    if not current_papers:
        return []

    trend_months = [item for item in sorted(papers_by_month) if item <= target_month][-months:]
    direction_counts = count_directions(current_papers)
    previous_counts = count_directions(papers_by_month.get(previous_month_key(target_month), []))
    source_counts = count_sources(current_papers)
    direction_growth = {
        name: count - previous_counts.get(name, 0) for name, count in direction_counts.items()
    }
    direction_scores = score_directions(direction_counts, direction_growth, source_counts)

    topic_names = sorted(
        direction_counts,
        key=lambda name: (-direction_scores.get(name, 0), -direction_counts[name], name),
    )[:limit]
    topics: list[TrendingTopic] = []
    for name in topic_names:
        papers = [
            paper
            for paper in sorted(current_papers, key=lambda item: item.generated_at, reverse=True)
            if name in paper.directions
        ]
        topics.append(
            TrendingTopic(
                name=name,
                month=target_month,
                generated_at=generated_at,
                paper_count=direction_counts[name],
                growth=direction_growth.get(name, 0),
                score=direction_scores.get(name, float(direction_counts[name])),
                source_counts=dict(sorted(count_sources(papers).items())),
                papers=papers,
                trend_months=trend_months,
                trend_counts=[
                    count_directions(papers_by_month.get(item, [])).get(name, 0)
                    for item in trend_months
                ],
            )
        )
    return topics


def build_keyword_trends(
    records: list[dict[str, object]],
    *,
    generated_at: str,
    month: str | None = None,
    months: int = 12,
    limit: int = 12,
) -> list[KeywordTrend]:
    papers_by_month = group_keyword_papers_by_month(records)
    if not papers_by_month:
        return []

    target_month = month or sorted(papers_by_month)[-1]
    current_items = papers_by_month.get(target_month, [])
    if not current_items:
        return []

    trend_months = [item for item in sorted(papers_by_month) if item <= target_month][-months:]
    keyword_counts = count_keywords(current_items)
    previous_counts = count_keywords(papers_by_month.get(previous_month_key(target_month), []))
    growth = {name: count - previous_counts.get(name, 0) for name, count in keyword_counts.items()}
    scores = {
        name: count + max(growth.get(name, 0), 0) * 0.8 + keyword_source_diversity(current_items, name) * 0.2
        for name, count in keyword_counts.items()
    }
    keyword_names = sorted(
        keyword_counts,
        key=lambda name: (
            -scores[name],
            -keyword_counts[name],
            KEYWORD_PRIORITY.get(name, len(KEYWORD_PRIORITY)),
            name,
        ),
    )[:limit]

    trends: list[KeywordTrend] = []
    for name in keyword_names:
        papers = [
            paper
            for paper, keywords in sorted(
                current_items,
                key=lambda item: item[0].generated_at,
                reverse=True,
            )
            if name in keywords
        ]
        trends.append(
            KeywordTrend(
                keyword=name,
                month=target_month,
                generated_at=generated_at,
                paper_count=keyword_counts[name],
                growth=growth.get(name, 0),
                score=scores[name],
                source_counts=dict(sorted(count_sources(papers).items())),
                papers=papers,
                trend_months=trend_months,
                trend_counts=[
                    count_keywords(papers_by_month.get(item, [])).get(name, 0)
                    for item in trend_months
                ],
            )
        )
    return trends


def group_keyword_papers_by_month(
    records: list[dict[str, object]],
) -> dict[str, list[tuple[PaperReference, list[str]]]]:
    papers_by_month: dict[str, list[tuple[PaperReference, list[str]]]] = defaultdict(list)
    for record in records:
        if not record.get("url"):
            continue
        month = record_month(record)
        if not month:
            continue
        paper = PaperReference(
            title=str(record.get("title") or record.get("arxiv_id") or "Untitled paper"),
            url=str(record["url"]),
            generated_at=str(record.get("generated_at") or ""),
            source=record_source(record),
            published_at=str(record.get("source_published_at") or ""),
            directions=record_directions(record),
            summary_excerpt=str(record.get("summary_excerpt") or ""),
        )
        keywords = extract_keywords_from_record(record)
        if keywords:
            papers_by_month[month].append((paper, keywords))
    return papers_by_month


def extract_keywords_from_record(record: dict[str, object]) -> list[str]:
    text = searchable_text(
        record.get("title"),
        record.get("summary_excerpt"),
        " ".join(str(item) for item in as_list(record.get("research_domains"))),
        " ".join(str(item) for item in as_list(record.get("feed_names"))),
    )
    found = [
        keyword
        for keyword, variants in KEYWORD_RULES
        if any(keyword_variant_matches(text, variant) for variant in variants)
    ]
    return unique_strings(found)


def count_keywords(items: list[tuple[PaperReference, list[str]]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for _, keywords in items:
        counts.update(keywords)
    return counts


def keyword_source_diversity(items: list[tuple[PaperReference, list[str]]], keyword: str) -> int:
    return len({paper.source for paper, keywords in items if keyword in keywords})


def group_paper_references_by_month(
    records: list[dict[str, object]],
) -> dict[str, list[PaperReference]]:
    papers_by_month: dict[str, list[PaperReference]] = defaultdict(list)
    for record in records:
        if not record.get("url"):
            continue
        month = record_month(record)
        if not month:
            continue
        papers_by_month[month].append(
            PaperReference(
                title=str(record.get("title") or record.get("arxiv_id") or "Untitled paper"),
                url=str(record["url"]),
                generated_at=str(record.get("generated_at") or ""),
                source=record_source(record),
                published_at=str(record.get("source_published_at") or ""),
                directions=record_directions(record),
                summary_excerpt=str(record.get("summary_excerpt") or ""),
            )
        )
    return papers_by_month


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
    return classify_record_domains(record)


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


def searchable_text(*values: object) -> str:
    text = " ".join(str(value or "") for value in values)
    text = re.sub(r"[-_/]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def keyword_variant_matches(text: str, variant: str) -> bool:
    normalized = searchable_text(variant)
    if not normalized:
        return False
    return re.search(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", text) is not None


def as_list(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple | set):
        return list(value)
    return [value]


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
