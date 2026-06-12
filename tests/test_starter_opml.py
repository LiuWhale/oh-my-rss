from xml.etree import ElementTree

from oh_my_rss.cli import main
from oh_my_rss.starter_opml import STARTER_FEEDS, render_starter_opml


def test_render_starter_opml_contains_validated_research_feeds():
    opml = render_starter_opml(category="论文")
    root = ElementTree.fromstring(opml)

    assert root.tag == "opml"
    assert root.attrib["version"] == "2.0"
    assert root.findtext("./head/title") == "Oh My RSS starter paper feeds"

    category = root.find("./body/outline")
    assert category is not None
    assert category.attrib["text"] == "论文"

    feeds = {outline.attrib["text"]: outline.attrib for outline in category.findall("./outline")}
    assert len(feeds) == len(STARTER_FEEDS)
    assert feeds["arXiv cs.RO"]["xmlUrl"] == "https://export.arxiv.org/rss/cs.RO"
    assert feeds["IJRR OnlineFirst"]["xmlUrl"] == (
        "https://journals.sagepub.com/action/showFeed?type=axatoc&feed=rss&jc=ijr"
    )
    assert feeds["Soft Robotics OnlineFirst"]["xmlUrl"] == (
        "https://journals.sagepub.com/action/showFeed?type=axatoc&feed=rss&jc=srba"
    )


def test_print_starter_opml_cli_writes_stdout(capsys):
    exit_code = main(["print-starter-opml", "--category", "Papers"])

    output = capsys.readouterr().out
    root = ElementTree.fromstring(output)

    assert exit_code == 0
    assert root.find("./body/outline").attrib["text"] == "Papers"
    assert "arXiv cs.LG" in output


def test_print_starter_opml_cli_writes_file(tmp_path, capsys):
    output_path = tmp_path / "starter.opml"

    exit_code = main(["print-starter-opml", "--output", str(output_path)])

    assert exit_code == 0
    assert capsys.readouterr().out == f"wrote {output_path}\n"
    root = ElementTree.parse(output_path).getroot()
    assert root.findtext("./head/title") == "Oh My RSS starter paper feeds"
