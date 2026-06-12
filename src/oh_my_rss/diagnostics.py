from __future__ import annotations

from pathlib import Path
import shutil

from .config import AppConfig


def run_doctor(config_path: Path) -> dict[str, object]:
    checks: list[dict[str, object]] = []

    try:
        config = AppConfig.from_yaml(config_path)
    except Exception as exc:  # noqa: BLE001 - diagnostic output should capture config failures
        checks.append(check("config", False, f"failed to load {config_path}: {exc}"))
        return doctor_result(config_path, checks)

    checks.append(check("config", True, f"loaded {config_path}"))
    checks.append(path_exists_check("freshrss_db", config.freshrss.db_path, expected="file"))
    checks.append(parent_ready_check("site_output_parent", config.site.output_dir))
    checks.append(parent_ready_check("runtime_state_parent", config.runtime.state_dir))
    checks.append(command_check("curl", config.runtime.curl_bin))
    checks.append(command_check("pdftotext", config.runtime.pdftotext_bin))
    checks.append(command_check("codex_command", config.codex.command[0] if config.codex.command else ""))

    return doctor_result(config_path, checks)


def doctor_result(config_path: Path, checks: list[dict[str, object]]) -> dict[str, object]:
    return {
        "ok": all(bool(item["ok"]) for item in checks),
        "config_path": str(config_path),
        "checks": checks,
    }


def check(name: str, ok: bool, message: str, **extra: object) -> dict[str, object]:
    item: dict[str, object] = {"name": name, "ok": ok, "message": message}
    item.update(extra)
    return item


def path_exists_check(name: str, path: Path, *, expected: str) -> dict[str, object]:
    if not path.exists():
        return check(name, False, f"{path} does not exist", path=str(path))
    if expected == "file" and not path.is_file():
        return check(name, False, f"{path} is not a file", path=str(path))
    if expected == "directory" and not path.is_dir():
        return check(name, False, f"{path} is not a directory", path=str(path))
    return check(name, True, f"{path} exists", path=str(path))


def parent_ready_check(name: str, path: Path) -> dict[str, object]:
    if path.exists():
        return check(name, path.is_dir(), f"{path} exists", path=str(path))
    parent = path.parent
    if parent.exists() and parent.is_dir():
        return check(name, True, f"{path} can be created under {parent}", path=str(path))
    return check(name, False, f"parent directory for {path} does not exist", path=str(path))


def command_check(name: str, command: str) -> dict[str, object]:
    if not command:
        return check(name, False, "command is empty")
    path = Path(command).expanduser()
    if path.is_absolute():
        if path.exists() and path.is_file():
            return check(name, True, f"{command} exists", command=command)
        return check(name, False, f"{command} does not exist", command=command)
    resolved = shutil.which(command)
    if resolved:
        return check(name, True, f"{command} resolves to {resolved}", command=command, resolved=resolved)
    return check(name, False, f"{command} was not found on PATH", command=command)
