from freshrss_arxiv_summarizer.pdf import normalize_pdf_text, select_pdf_context


def test_normalize_pdf_text_joins_hyphenated_line_breaks():
    text = "TacFore-\nSight uses force.\n\n\nExperiments"

    assert normalize_pdf_text(text) == "TacForeSight uses force.\n\nExperiments"


def test_select_pdf_context_prioritizes_method_and_experiment_sections():
    text = (
        "Abstract " + ("intro " * 100)
        + "Method The model predicts future tactile latents. " + ("method details " * 80)
        + "Experiments We compare against baselines on real robots. " + ("results " * 80)
    )

    context = select_pdf_context(text, max_chars=1200)

    assert "Method" in context
    assert "Experiments" in context
    assert len(context) <= 1400
