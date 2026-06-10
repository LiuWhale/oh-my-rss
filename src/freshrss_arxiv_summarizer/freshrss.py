from __future__ import annotations

import html
import re


SUMMARY_MARKER_PREFIX = "data-codex-arxiv-summary="


def make_summary_snippet(arxiv_id: str, summary_url: str) -> str:
    return (
        f'<p data-codex-arxiv-summary="{html.escape(arxiv_id, quote=True)}">'
        "<strong>Codex 中文总结：</strong> "
        f'<a href="{html.escape(summary_url, quote=True)}" target="_blank" rel="noopener">'
        "查看 Motivation / Contribution / 技术原理 / 实验设计及分析</a></p>"
    )


def upsert_summary_snippet(content: str, arxiv_id: str, snippet: str) -> tuple[str, bool]:
    marker = f'{SUMMARY_MARKER_PREFIX}"{arxiv_id}"'
    if marker not in content:
        return f"{snippet}\n{content}", True

    pattern = re.compile(
        r'<p\s+data-codex-arxiv-summary="' + re.escape(arxiv_id) + r'".*?</p>\s*',
        re.S,
    )
    updated, count = pattern.subn(snippet + "\n", content, count=1)
    return updated, bool(count and updated != content)
