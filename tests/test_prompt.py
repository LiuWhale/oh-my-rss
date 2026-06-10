from oh_my_rss.arxiv import Paper
from oh_my_rss.prompt import build_summary_prompt


def test_prompt_requires_story_sized_summary_and_mathjax_safe_formula_style():
    paper = Paper(
        arxiv_id="2606.11184v1",
        title="Paper",
        authors="Ada",
        abstract="abstract",
        feed_names=["Robotics"],
        pdf_context="method and experiment text",
        pdf_text_chars=10000,
        pdf_context_chars=5000,
    )

    prompt = build_summary_prompt(paper)

    assert "900-1300" in prompt
    assert "论文故事" in prompt
    assert "公式最多保留 1 个" in prompt
    assert "$$ ... $$" in prompt
    assert "RSS 摘要未提供完整实验细节" not in prompt
