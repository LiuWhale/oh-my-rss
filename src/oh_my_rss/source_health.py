from __future__ import annotations

from datetime import datetime


def build_source_health_report(
    records: list[dict[str, object]],
    *,
    previous_records: list[dict[str, object]] | None = None,
    generated_at: str,
    current_year: int | None = None,
) -> dict[str, object]:
    previous_by_name = {str(item.get("name") or ""): item for item in previous_records or []}
    year = current_year or _year_from_iso(generated_at)
    sources = []
    total_warnings = 0

    for record in records:
        item = dict(record)
        name = str(item.get("name") or "")
        warnings: list[str] = []
        warning_codes: list[str] = []

        status = str(item.get("status") or "ok")
        error = str(item.get("error") or "").strip()
        if status == "error" or error:
            warning_codes.append("fetch_error")
            warnings.append(f"抓取失败：{error or 'unknown error'}")

        previous = previous_by_name.get(name)
        count = _int_or_none(item.get("candidate_count"))
        previous_count = _int_or_none(previous.get("candidate_count")) if previous else None
        if count == 0 and previous_count and previous_count > 0:
            warning_codes.append("zero_after_nonzero")
            warnings.append(f"上一轮 {previous_count} 篇，这一轮 0 篇")

        configured_year = _int_or_none(item.get("configured_year"))
        if configured_year and year and configured_year < year:
            warning_codes.append("stale_year")
            warnings.append(f"配置年份 {configured_year} 早于当前年份 {year}")

        item["status"] = status
        item["candidate_count"] = count if count is not None else 0
        item["warnings"] = warnings
        item["warning_codes"] = warning_codes
        total_warnings += len(warnings)
        sources.append(item)

    return {
        "ok": total_warnings == 0,
        "title": "Oh My RSS source health radar",
        "generated_at": generated_at,
        "warning_count": total_warnings,
        "source_count": len(sources),
        "sources": sources,
    }


def record_source_health_snapshot(
    state: dict[str, object],
    report: dict[str, object],
    *,
    max_days: int = 31,
) -> None:
    generated_at = str(report.get("generated_at") or "")
    day = generated_at[:10] if len(generated_at) >= 10 else datetime.now().date().isoformat()
    health = state.setdefault("source_health", {})
    if not isinstance(health, dict):
        health = {}
        state["source_health"] = health

    history = health.setdefault("history", {})
    if not isinstance(history, dict):
        history = {}
        health["history"] = history

    health["latest"] = report
    history[day] = report

    for stale_day in sorted(history)[: max(0, len(history) - max_days)]:
        history.pop(stale_day, None)


def latest_source_health_records(state: dict[str, object]) -> list[dict[str, object]]:
    health = state.get("source_health")
    if not isinstance(health, dict):
        return []
    latest = health.get("latest")
    if not isinstance(latest, dict):
        return []
    sources = latest.get("sources")
    if not isinstance(sources, list):
        return []
    return [item for item in sources if isinstance(item, dict)]


def _int_or_none(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _year_from_iso(value: str) -> int | None:
    if len(value) < 4:
        return None
    try:
        return int(value[:4])
    except ValueError:
        return None
