from __future__ import annotations

import re
from typing import Iterable, Protocol


class PaperLike(Protocol):
    title: str
    abstract: str
    feed_names: list[str]


DOMAIN_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "Robot Learning / Policy",
        (
            "diffusion policy",
            "policy learning",
            "robot learning",
            "reinforcement learning",
            "imitation learning",
            "behavior cloning",
            "offline rl",
            "policy",
            "skill learning",
        ),
    ),
    (
        "Manipulation / Dexterous Hands",
        (
            "manipulation",
            "dexterous",
            "grasp",
            "grasping",
            "in-hand",
            "bimanual",
            "mobile manipulation",
            "hand-object",
        ),
    ),
    (
        "Humanoid / Legged Robots",
        (
            "humanoid",
            "legged",
            "quadruped",
            "biped",
            "locomotion",
            "whole-body",
            "whole body",
        ),
    ),
    (
        "Vision-Language-Action",
        (
            "vision-language-action",
            "vision language action",
            "vla",
            "multimodal policy",
            "language-conditioned",
            "language conditioned",
            "large vision-language",
        ),
    ),
    (
        "Navigation / Planning",
        (
            "navigation",
            "motion planning",
            "path planning",
            "trajectory planning",
            "trajectory optimization",
            "mobile robot",
            "autonomous driving",
        ),
    ),
    (
        "SLAM / Mapping / Localization",
        (
            "slam",
            "simultaneous localization",
            "mapping",
            "localization",
            "place recognition",
            "visual odometry",
            "state estimation",
        ),
    ),
    (
        "3D Vision / Perception",
        (
            "3d vision",
            "point cloud",
            "point-cloud",
            "depth estimation",
            "pose estimation",
            "object detection",
            "semantic segmentation",
            "segmentation",
            "perception",
        ),
    ),
    (
        "Safety / Control",
        (
            "safe reinforcement learning",
            "safe learning",
            "control barrier",
            "barrier function",
            "cbf",
            "safety filter",
            "model predictive control",
            "mpc",
            "robust control",
            "safety",
        ),
    ),
    (
        "Embodied AI / Foundation Models",
        (
            "embodied ai",
            "embodied agent",
            "foundation model",
            "large language model",
            "llm",
            "world model",
            "robot foundation model",
        ),
    ),
    (
        "Benchmark / Dataset / Evaluation",
        (
            "benchmark",
            "dataset",
            "evaluation",
            "simulator",
            "simulation benchmark",
            "leaderboard",
        ),
    ),
]

VLA_DOMAIN_NAME = "Vision-Language-Action"
VLA_EXPLICIT_TERMS = (
    "vla",
    "vision language action",
    "vision-language-action",
    "openvla",
)
VLA_VISION_LANGUAGE_TERMS = (
    "vision language",
    "vision-language",
    "visual language",
    "vlm",
    "multimodal",
)
VLA_ACTION_TERMS = (
    "action model",
    "action policy",
    "action representation",
    "action controller",
    "controller",
    "policy",
    "robot",
    "robotic",
    "control",
    "manipulation",
    "trajectory",
    "actuation",
)
GENERATED_CATEGORY_NAMES = {
    "Robotics / Embodied AI",
    "VLA / Multimodal Agents",
    "VLA / Vision-Language-Action",
    *(name for name, _keywords in DOMAIN_RULES),
}
ROBOTICS_CONTEXT_TERMS = (
    "robot",
    "robotic",
    "manipulation",
    "dexterous",
    "humanoid",
    "legged",
    "quadruped",
    "bimanual",
    "mobile manipulator",
    "locomotion",
    "navigation",
    "embodied",
)
ROBOT_POLICY_EXPLICIT_TERMS = (
    "diffusion policy",
    "robot learning",
    "robotic learning",
    "vision-language-action",
    "vision language action",
)
ROBOT_POLICY_LEARNING_TERMS = (
    "policy learning",
    "reinforcement learning",
    "imitation learning",
    "behavior cloning",
    "offline rl",
    "skill learning",
    "policy",
)
SAFETY_CONTROL_EXPLICIT_TERMS = (
    "safe reinforcement learning",
    "safe learning",
    "safe control",
    "control barrier",
    "barrier function",
    "barrier certificate",
    "cbf",
    "safety filter",
    "runtime assurance",
    "model predictive control",
    "mpc",
    "robust control",
    "reachability",
)
SAFETY_CONTROL_CONTEXT_TERMS = (
    "control",
    "robot",
    "robotic",
    "autonomous",
    "navigation",
    "verification",
    "risk",
    "constraint",
)
BENCHMARK_EXPLICIT_TERMS = (
    "benchmark",
    "dataset",
    "leaderboard",
    "evaluation suite",
    "simulation benchmark",
    "simulator",
)
EMBODIED_EXPLICIT_TERMS = (
    "embodied ai",
    "embodied agent",
    "robot foundation model",
    "robotic foundation model",
    "generalist robot",
    "generalist policy",
)
FOUNDATION_MODEL_TERMS = (
    "foundation model",
    "large language model",
    "llm",
    "world model",
)
LEGGED_ROBOT_EXPLICIT_TERMS = (
    "humanoid",
    "quadruped",
    "biped",
    "bipedal",
    "legged robot",
    "legged robotics",
    "robot locomotion",
    "robotic locomotion",
)
LOCOMOTION_ROBOT_CONTEXT_TERMS = (
    "robot",
    "robotic",
    "legged",
    "humanoid",
    "quadruped",
    "biped",
    "bipedal",
)


def classify_research_domains(paper: PaperLike) -> list[str]:
    text = searchable_text(
        paper.title,
        paper.abstract,
    )
    domains = [name for name, keywords in DOMAIN_RULES if domain_rule_matches(name, text, keywords)]
    if is_robotics_paper(text, getattr(paper, "feed_names", [])):
        domains.append("Robotics / Embodied AI")
    if not domains:
        domains.extend(normalized_feed_topics(getattr(paper, "feed_names", [])))
    return unique_strings(domains) or ["Uncategorized"]


def classify_record_domains(record: dict[str, object]) -> list[str]:
    existing = record.get("research_domains")
    if existing:
        return unique_strings(normalize_topic(item) for item in as_iterable(existing))
    text = searchable_text(
        record.get("title"),
        record.get("summary_excerpt"),
    )
    domains = [name for name, keywords in DOMAIN_RULES if domain_rule_matches(name, text, keywords)]
    if is_robotics_paper(text, as_iterable(record.get("feed_names"))):
        domains.append("Robotics / Embodied AI")
    if not domains:
        domains.extend(normalized_feed_topics(as_iterable(record.get("feed_names"))))
    return unique_strings(domains) or ["Uncategorized"]


def domain_rule_matches(name: str, text: str, keywords: Iterable[str]) -> bool:
    if name == VLA_DOMAIN_NAME:
        return matches_vla_topic(text)
    if name == "Robot Learning / Policy":
        return matches_robot_learning_policy(text)
    if name == "Humanoid / Legged Robots":
        return matches_humanoid_legged_robot(text)
    if name == "Safety / Control":
        return matches_safety_control(text)
    if name == "Benchmark / Dataset / Evaluation":
        return matches_benchmark_dataset(text)
    if name == "Embodied AI / Foundation Models":
        return matches_embodied_foundation(text)
    return any(keyword_matches(keyword, text) for keyword in keywords)


def matches_robot_learning_policy(text: str) -> bool:
    if any(keyword_matches(term, text) for term in ROBOT_POLICY_EXPLICIT_TERMS):
        return True
    has_robot_context = any(keyword_matches(term, text) for term in ROBOTICS_CONTEXT_TERMS)
    has_policy_learning = any(keyword_matches(term, text) for term in ROBOT_POLICY_LEARNING_TERMS)
    return has_robot_context and has_policy_learning


def matches_humanoid_legged_robot(text: str) -> bool:
    if any(keyword_matches(term, text) for term in LEGGED_ROBOT_EXPLICIT_TERMS):
        return True
    has_locomotion = keyword_matches("locomotion", text)
    has_robot_context = any(keyword_matches(term, text) for term in LOCOMOTION_ROBOT_CONTEXT_TERMS)
    return has_locomotion and has_robot_context


def matches_safety_control(text: str) -> bool:
    if any(keyword_matches(term, text) for term in SAFETY_CONTROL_EXPLICIT_TERMS):
        return True
    has_safety = keyword_matches("safety", text) or keyword_matches("safe", text)
    has_control_context = any(keyword_matches(term, text) for term in SAFETY_CONTROL_CONTEXT_TERMS)
    return has_safety and has_control_context


def matches_benchmark_dataset(text: str) -> bool:
    return any(keyword_matches(term, text) for term in BENCHMARK_EXPLICIT_TERMS)


def matches_embodied_foundation(text: str) -> bool:
    if any(keyword_matches(term, text) for term in EMBODIED_EXPLICIT_TERMS):
        return True
    has_foundation_model = any(keyword_matches(term, text) for term in FOUNDATION_MODEL_TERMS)
    has_robot_context = any(keyword_matches(term, text) for term in ROBOTICS_CONTEXT_TERMS)
    return has_foundation_model and has_robot_context


def matches_vla_topic(text: str) -> bool:
    if any(keyword_matches(term, text) for term in VLA_EXPLICIT_TERMS):
        return True
    has_vision_language = any(keyword_matches(term, text) for term in VLA_VISION_LANGUAGE_TERMS)
    has_action = any(keyword_matches(term, text) for term in VLA_ACTION_TERMS)
    return has_vision_language and has_action


def keyword_matches(keyword: str, text: str) -> bool:
    keyword_text = normalize_match_text(keyword)
    haystack = f" {normalize_match_text(text)} "
    needle = f" {keyword_text} "
    return bool(keyword_text) and needle in haystack


def searchable_text(*values: object) -> str:
    text = " ".join(str(value or "") for value in values)
    text = re.sub(r"[-_/‐‑‒–—―]+", " ", text.lower())
    return re.sub(r"\s+", " ", text)


def normalize_match_text(value: object) -> str:
    text = searchable_text(value)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_robotics_paper(text: str, feed_names: Iterable[object]) -> bool:
    if any("robot" in str(name).lower() or "cs.ro" in str(name).lower() for name in feed_names):
        return True
    if any(keyword_matches(term, text) for term in ("robot", "robotic", "embodied")):
        return True
    if keyword_matches("manipulation", text) and any(
        keyword_matches(term, text) for term in ("robot", "robotic", "bimanual", "dexterous")
    ):
        return True
    return matches_humanoid_legged_robot(text)


def normalized_feed_topics(feed_names: Iterable[object]) -> list[str]:
    topics = []
    for feed_name in feed_names:
        topic = normalize_topic(feed_name)
        if topic and topic.lower() not in {"arxiv", "fresh rss", "freshrss"} and not is_generated_category_name(topic):
            topics.append(topic)
    return unique_strings(topics)


def is_generated_category_name(topic: str) -> bool:
    return topic in GENERATED_CATEGORY_NAMES


def normalize_topic(value: object) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if text.startswith("arXiv "):
        text = text[len("arXiv ") :].strip()
    return text


def as_iterable(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple | set):
        return list(value)
    return [value]


def unique_strings(values: Iterable[object]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result
