from oh_my_rss.render import markdown_to_html, render_detail_html


def test_markdown_to_html_renders_code_spans_without_raw_backticks():
    html = markdown_to_html("## 技术原理\n\n- Use `L_pred` as the training loss.")

    assert "<h2>技术原理</h2>" in html
    assert "<code>L_pred</code>" in html
    assert "`L_pred`" not in html


def test_render_detail_html_includes_mathjax_loader():
    html = render_detail_html(
        title="Paper",
        arxiv_id="2606.11184v1",
        feeds=["Robotics"],
        abs_url="https://arxiv.org/abs/2606.11184v1",
        pdf_url="https://arxiv.org/pdf/2606.11184v1",
        markdown="# Paper\n\n## Motivation\nText",
        generated_at="2026-06-10T18:00:00+08:00",
    )

    assert "MathJax" in html
    assert "tex-chtml.js" in html
    assert "2606.11184v1" in html
