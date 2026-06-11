from xml.etree import ElementTree

from oh_my_rss.publisher import detail_filename, publish_feed


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
