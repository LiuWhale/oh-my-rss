from freshrss_arxiv_summarizer.freshrss import make_summary_snippet, upsert_summary_snippet


def test_upsert_summary_snippet_replaces_existing_link():
    old = (
        '<p data-codex-arxiv-summary="2606.11184v1"><strong>Codex 中文总结：</strong> '
        '<a href="http://old">查看 Motivation / Contribution / 技术原理 / 实验设计及分析</a></p>\n'
        "Abstract text"
    )
    snippet = make_summary_snippet("2606.11184v1", "http://new")

    updated, changed = upsert_summary_snippet(old, "2606.11184v1", snippet)

    assert changed is True
    assert "http://new" in updated
    assert "http://old" not in updated
    assert updated.count('data-codex-arxiv-summary="2606.11184v1"') == 1
