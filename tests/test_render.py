from xml.etree import ElementTree

from oh_my_rss.render import markdown_to_html, render_detail_html, render_rss_xml


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


def test_render_rss_xml_outputs_parseable_public_feed():
    xml = render_rss_xml(
        [
            {
                "title": "A & B <Robot>",
                "arxiv_id": "2606.11184v1",
                "url": "https://example.com/summaries/2606.11184v1.html",
                "generated_at": "2026-06-10T18:00:00+08:00",
                "feed_names": ["Robotics"],
                "summary_excerpt": "Motivation and contribution.",
            }
        ],
        generated_at="2026-06-10T18:01:00+08:00",
        public_base_url="https://example.com/summaries",
    )

    root = ElementTree.fromstring(xml)
    channel = root.find("channel")

    assert root.tag == "rss"
    assert channel is not None
    assert channel.findtext("title") == "Oh My RSS"
    assert channel.findtext("link") == "https://example.com/summaries/index.html"
    assert channel.findtext("item/title") == "A & B <Robot>"
    assert channel.findtext("item/link") == "https://example.com/summaries/2606.11184v1.html"
