import json

from oh_my_rss.cli import main
from oh_my_rss.validation import validate_site_output


RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Oh My RSS</title></channel></rss>
"""
OPML = """<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0"><head><title>Feeds</title></head><body /></opml>
"""
SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/summaries/index.html</loc></url>
</urlset>
"""


def write_valid_site(site_dir):
    files = {
        "index.html": "<!doctype html><title>Oh My RSS</title>",
        "feed.xml": RSS,
        "opml.xml": OPML,
        "feeds.json": json.dumps({"feed_count": 1, "feeds": [{"name": "All"}]}),
        "status.json": json.dumps({"ok": True, "summary_count": 1}),
        "robots.txt": "User-agent: *\nSitemap: https://example.com/summaries/sitemap.xml\n",
        "sitemap.xml": SITEMAP,
        "manifest.json": json.dumps([]),
        "categories/index.json": json.dumps([]),
        "categories/opml.xml": OPML,
        "reports/monthly.xml": RSS,
        "reports/trending.xml": RSS,
        "reports/keywords.xml": RSS,
    }
    for relative, text in files.items():
        path = site_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def test_validate_site_output_accepts_complete_parseable_site(tmp_path):
    write_valid_site(tmp_path)

    result = validate_site_output(tmp_path)

    assert result["ok"] is True
    assert result["checked_count"] == 13
    assert result["errors"] == []


def test_validate_site_output_reports_missing_and_invalid_files(tmp_path):
    write_valid_site(tmp_path)
    (tmp_path / "feeds.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "reports" / "keywords.xml").unlink()

    result = validate_site_output(tmp_path)

    assert result["ok"] is False
    assert "reports/keywords.xml is missing" in result["errors"]
    assert any(error.startswith("feeds.json is not valid JSON") for error in result["errors"])


def test_validate_site_cli_returns_nonzero_for_invalid_site(tmp_path, capsys):
    write_valid_site(tmp_path)
    (tmp_path / "status.json").unlink()

    exit_code = main(["validate-site", "--site-dir", str(tmp_path)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["ok"] is False
    assert "status.json is missing" in output["errors"]
