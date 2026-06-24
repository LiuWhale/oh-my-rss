from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import os
import tempfile


def load_state(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"papers": {}}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("papers", {})
    return data


def save_state(path: Path, state: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix="state-", suffix=".json", dir=path.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp_name, path)


def expire_stale_running_records(
    state: dict[str, object],
    *,
    now: datetime | None = None,
    max_age: timedelta = timedelta(hours=6),
) -> int:
    records = state.setdefault("papers", {})
    if not isinstance(records, dict):
        return 0

    now_value = normalize_datetime(now or datetime.now(timezone.utc))
    expired = 0
    for record in records.values():
        if not isinstance(record, dict) or record.get("status") != "running":
            continue
        updated_at = parse_state_datetime(record.get("updated_at") or record.get("generated_at"))
        if updated_at is not None and now_value - updated_at <= max_age:
            continue
        record["status"] = "error"
        record["error"] = (
            f"stale running record older than {format_timedelta(max_age)}; "
            "will retry if the paper appears in a future candidate set"
        )
        record["stale_running_recovered_at"] = now_value.astimezone().isoformat(timespec="seconds")
        record["updated_at"] = now_value.astimezone().isoformat(timespec="seconds")
        expired += 1
    return expired


def parse_state_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return normalize_datetime(parsed)


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def format_timedelta(value: timedelta) -> str:
    total_seconds = int(value.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if seconds:
        return f"{hours}h{minutes}m{seconds}s"
    if minutes:
        return f"{hours}h{minutes}m"
    return f"{hours}h"
