import pymupdf

from oh_my_rss.pdf import normalize_pdf_text, render_pdf_first_page_preview, select_pdf_context


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


def test_render_pdf_first_page_preview_writes_png_asset(tmp_path):
    pdf_path = tmp_path / "paper.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=480, height=360)
    page.draw_rect((32, 48, 448, 260), color=(0.1, 0.2, 0.7), fill=(0.9, 0.94, 1.0))
    page.draw_circle((380, 110), 46, color=(0.9, 0.3, 0.2), fill=(1.0, 0.75, 0.65))
    for row in range(8):
        y = 88 + row * 20
        page.draw_line((72, y), (310, y + 10), color=(0.15, 0.35, 0.35), width=1.2)
    page.insert_text((60, 310), "Main Figure: preview fixture with enough content")
    doc.save(pdf_path)
    doc.close()

    url = render_pdf_first_page_preview(
        pdf_path,
        output_dir=tmp_path / "site",
        public_base_url="https://example.com/summaries",
        slug="2606.11184v1",
    )

    image_path = tmp_path / "site" / "assets" / "2606.11184v1-main.png"
    assert url == "https://example.com/summaries/assets/2606.11184v1-main.png"
    assert image_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
