from __future__ import annotations

from pathlib import Path
import shlex


def build_cron_line(
    *,
    cwd: str | Path,
    config: str | Path,
    limit: int,
    interval_minutes: int,
    log_path: str | Path,
    lock_path: str | Path,
    venv_path: str | Path | None,
) -> str:
    if not 1 <= interval_minutes <= 59:
        raise ValueError("interval_minutes must be between 1 and 59")
    if limit < 1:
        raise ValueError("limit must be at least 1")

    schedule = "* * * * *" if interval_minutes == 1 else f"*/{interval_minutes} * * * *"
    steps = [f"cd {_quote(cwd)}"]

    if venv_path is not None:
        steps.append(f". {_quote(Path(venv_path) / 'bin' / 'activate')}")

    run_command = [
        "flock",
        "-n",
        str(lock_path),
        "oh-my-rss",
        "run",
        "--config",
        str(config),
        "--limit",
        str(limit),
    ]
    steps.append(" ".join(_quote(part) for part in run_command))

    return f"{schedule} {' && '.join(steps)} >> {_quote(log_path)} 2>&1"


def _quote(value: str | Path) -> str:
    return shlex.quote(str(value))
