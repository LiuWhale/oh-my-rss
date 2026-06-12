import json

from oh_my_rss.cli import main
from oh_my_rss.feed_validation import parse_opml_feeds, validate_opml_text


OPML = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <body>
    <outline text="论文">
      <outline
        type="rss"
        text="Good Feed"
        title="Good Feed"
        xmlUrl="https://example.com/good.xml"
        htmlUrl="https://example.com/good" />
      <outline
        type="rss"
        text="Bad Feed"
        title="Bad Feed"
        xmlUrl="https://example.com/bad.xml" />
    </outline>
  </body>
</opml>
"""


def test_parse_opml_feeds_extracts_nested_xml_urls():
    feeds = parse_opml_feeds(OPML)

    assert [feed.title for feed in feeds] == ["Good Feed", "Bad Feed"]
    assert feeds[0].xml_url == "https://example.com/good.xml"
    assert feeds[0].html_url == "https://example.com/good"


def test_validate_opml_text_reports_fetch_failures():
    def fetcher(url, timeout_seconds):
        if url.endswith("good.xml"):
            return {"ok": True, "status": 200, "content_type": "application/rss+xml", "message": "RSS"}
        return {"ok": False, "status": 404, "content_type": "text/html", "message": "HTTP 404"}

    result = validate_opml_text(OPML, timeout_seconds=3, fetcher=fetcher)

    assert result["ok"] is False
    assert result["feed_count"] == 2
    assert result["failure_count"] == 1
    assert result["feeds"][0]["ok"] is True
    assert result["feeds"][1]["message"] == "HTTP 404"


def test_validate_opml_text_can_parse_without_network():
    result = validate_opml_text(OPML, check_network=False)

    assert result["ok"] is True
    assert result["checked_network"] is False
    assert result["feed_count"] == 2
    assert result["feeds"][0]["ok"] is None
    assert result["feeds"][0]["message"] == "not checked"


def test_validate_opml_cli_supports_no_network_mode(tmp_path, capsys):
    opml_path = tmp_path / "feeds.opml"
    opml_path.write_text(OPML, encoding="utf-8")

    exit_code = main(["validate-opml", "--opml", str(opml_path), "--no-network"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["ok"] is True
    assert output["feed_count"] == 2
    assert output["checked_network"] is False


def test_validate_opml_cli_returns_nonzero_for_invalid_xml(tmp_path, capsys):
    opml_path = tmp_path / "broken.opml"
    opml_path.write_text("<opml>", encoding="utf-8")

    exit_code = main(["validate-opml", "--opml", str(opml_path), "--no-network"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["ok"] is False
    assert output["errors"]
