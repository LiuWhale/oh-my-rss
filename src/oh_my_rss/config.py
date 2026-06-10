from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import os

import yaml


@dataclass
class FreshRSSConfig:
    db_path: Path
    category: str = "论文"
    container_name: str | None = None


@dataclass
class SiteConfig:
    public_base_url: str
    output_dir: Path


@dataclass
class CodexConfig:
    command: list[str] = field(default_factory=lambda: ["codex", "-a", "never", "-s", "read-only", "exec"])
    timeout_seconds: int = 900
    reasoning_effort: str = "low"


@dataclass
class RuntimeConfig:
    state_dir: Path = Path("state")
    curl_bin: str = "curl"
    pdftotext_bin: str = "pdftotext"
    pdf_timeout_seconds: int = 120
    pdf_max_chars: int = 60_000


@dataclass
class AppConfig:
    freshrss: FreshRSSConfig
    site: SiteConfig
    codex: CodexConfig = field(default_factory=CodexConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> "AppConfig":
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        base = path.parent
        return cls(
            freshrss=FreshRSSConfig(
                db_path=_expand_path(data["freshrss"]["db_path"], base),
                category=data["freshrss"].get("category", "论文"),
                container_name=data["freshrss"].get("container_name"),
            ),
            site=SiteConfig(
                public_base_url=str(data["site"]["public_base_url"]).rstrip("/"),
                output_dir=_expand_path(data["site"]["output_dir"], base),
            ),
            codex=CodexConfig(
                command=list(data.get("codex", {}).get("command", CodexConfig().command)),
                timeout_seconds=int(data.get("codex", {}).get("timeout_seconds", 900)),
                reasoning_effort=str(data.get("codex", {}).get("reasoning_effort", "low")),
            ),
            runtime=RuntimeConfig(
                state_dir=_expand_path(data.get("runtime", {}).get("state_dir", "state"), base),
                curl_bin=str(data.get("runtime", {}).get("curl_bin", "curl")),
                pdftotext_bin=str(data.get("runtime", {}).get("pdftotext_bin", "pdftotext")),
                pdf_timeout_seconds=int(data.get("runtime", {}).get("pdf_timeout_seconds", 120)),
                pdf_max_chars=int(data.get("runtime", {}).get("pdf_max_chars", 60_000)),
            ),
        )


def _expand_path(value: str | os.PathLike[str], base: Path) -> Path:
    path = Path(os.path.expandvars(os.path.expanduser(str(value))))
    if not path.is_absolute():
        path = base / path
    return path.resolve()
