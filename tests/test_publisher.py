from xml.etree import ElementTree

from oh_my_rss.publisher import category_slug, detail_filename, publish_category_feeds, publish_feed


def test_detail_filename_includes_summary_hash_to_avoid_stale_caches():
    name = detail_filename("2606.11184v1", "abc123456789ffffffff")

    assert name == "2606.11184v1-abc123456789.html"


def test_publish_feed_writes_feed_xml(tmp_path):
    publish_feed(
        [
            {
                "title": "Paper",
                "arxiv_id": "2606.11184v1",
                "url": "https://example.com/summaries/2606.11184v1.html",
                "generated_at": "2026-06-10T18:00:00+08:00",
                "feed_names": ["Robotics"],
            }
        ],
        output_dir=tmp_path,
        public_base_url="https://example.com/summaries",
        generated_at="2026-06-10T18:01:00+08:00",
    )

    feed_path = tmp_path / "feed.xml"
    assert feed_path.exists()
    root = ElementTree.fromstring(feed_path.read_text(encoding="utf-8"))
    assert root.findtext("channel/item/guid") == "https://example.com/summaries/2606.11184v1.html"
    assert root.findall("channel/item/category") == []


def test_category_slug_prefers_ascii_words_and_falls_back_to_hash():
    assert category_slug("导航规划 / Navigation") == "navigation"
    assert category_slug("机器人").startswith("category-")


def test_publish_category_feeds_writes_one_feed_per_category(tmp_path):
    stale_categories = tmp_path / "categories"
    stale_categories.mkdir()
    (stale_categories / "arxiv-robotics-latest-cs-ro.xml").write_text("old", encoding="utf-8")
    (stale_categories / "arxiv-navigation.xml").write_text("old", encoding="utf-8")
    (stale_categories / "arxiv-vision.xml").write_text("old", encoding="utf-8")
    records = [
        {
            "title": "Robot Paper",
            "arxiv_id": "2606.11184v1",
            "url": "https://example.com/summaries/robot.html",
            "generated_at": "2026-06-10T18:00:00+08:00",
            "feed_names": ["arXiv Robotics latest (cs.RO)", "arXiv 导航规划 / Navigation"],
        },
        {
            "title": "Vision Paper",
            "arxiv_id": "2606.11185v1",
            "url": "https://example.com/summaries/vision.html",
            "generated_at": "2026-06-10T18:00:00+08:00",
            "feed_names": ["arXiv Vision"],
        },
    ]

    categories = publish_category_feeds(
        records,
        output_dir=tmp_path,
        public_base_url="https://example.com/summaries",
        generated_at="2026-06-10T18:01:00+08:00",
    )

    assert {item["slug"] for item in categories} == {
        "robotics-latest-cs-ro",
        "navigation",
        "vision",
    }

    robotics = ElementTree.parse(tmp_path / "categories" / "robotics-latest-cs-ro.xml")
    vision = ElementTree.parse(tmp_path / "categories" / "vision.xml")
    category_index = tmp_path / "categories" / "index.json"
    category_opml = tmp_path / "categories" / "opml.xml"

    assert robotics.findtext("./channel/title") == "Oh My RSS - Robotics latest (cs.RO)"
    assert robotics.findtext("./channel/item/title") == "Robot Paper"
    assert [item.text for item in robotics.findall("./channel/item/category")] == ["Robotics latest (cs.RO)"]
    assert vision.findtext("./channel/item/title") == "Vision Paper"
    assert [item.text for item in vision.findall("./channel/item/category")] == ["Vision"]
    assert not (tmp_path / "categories" / "arxiv-robotics-latest-cs-ro.xml").exists()
    assert not (tmp_path / "categories" / "arxiv-navigation.xml").exists()
    assert not (tmp_path / "categories" / "arxiv-vision.xml").exists()
    assert category_index.exists()
    assert category_opml.exists()

    opml = ElementTree.parse(category_opml)
    assert opml.getroot().tag == "opml"
    assert opml.getroot().attrib["version"] == "2.0"
    outlines = {outline.attrib["text"]: outline.attrib for outline in opml.findall("./body/outline")}
    assert outlines["Robotics latest (cs.RO)"]["type"] == "rss"
    assert (
        outlines["Robotics latest (cs.RO)"]["xmlUrl"]
        == "https://example.com/summaries/categories/robotics-latest-cs-ro.xml"
    )
    assert (
        outlines["导航规划 / Navigation"]["xmlUrl"]
        == "https://example.com/summaries/categories/navigation.xml"
    )
