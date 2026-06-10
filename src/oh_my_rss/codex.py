from __future__ import annotations

from pathlib import Path
import shlex
import subprocess


def run_codex_summary(
    *,
    command: list[str],
    reasoning_effort: str,
    prompt: str,
    output_path: Path,
    timeout_seconds: int,
) -> str:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path = output_path.with_suffix(".prompt.md")
    log_path = output_path.with_suffix(".codex.log")
    prompt_path.write_text(prompt, encoding="utf-8")
    if output_path.exists():
        output_path.unlink()

    cmd = command + [
        "--skip-git-repo-check",
        "--ephemeral",
        "-c",
        f'model_reasoning_effort="{reasoning_effort}"',
        "-o",
        str(output_path),
        "-",
    ]
    result = subprocess.run(
        cmd,
        input=prompt,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_seconds,
    )
    log_path.write_text(
        "COMMAND:\n{}\n\nSTDOUT:\n{}\n\nSTDERR:\n{}\n".format(
            " ".join(shlex.quote(part) for part in cmd),
            result.stdout,
            result.stderr,
        ),
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(f"Codex failed with code {result.returncode}; see {log_path}")
    if not output_path.exists() or not output_path.read_text(encoding="utf-8").strip():
        raise RuntimeError(f"Codex produced empty output; see {log_path}")
    return output_path.read_text(encoding="utf-8").strip()
