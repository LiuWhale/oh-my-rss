from freshrss_arxiv_summarizer.publisher import detail_filename


def test_detail_filename_includes_summary_hash_to_avoid_stale_caches():
    name = detail_filename("2606.11184v1", "abc123456789ffffffff")

    assert name == "2606.11184v1-abc123456789.html"
