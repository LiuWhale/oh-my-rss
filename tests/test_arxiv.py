from oh_my_rss.arxiv import group_entries


def test_group_entries_deduplicates_same_arxiv_id_across_feeds():
    rows = [
        {
            "id": 1,
            "guid": "http://arxiv.org/abs/2606.11184v1",
            "link": "https://arxiv.org/pdf/2606.11184v1",
            "title": "Paper A",
            "author": "Ada",
            "content": "short abstract",
            "date": 10,
            "feed_name": "Robotics",
            "feed_url": "https://export.arxiv.org/rss/cs.RO",
        },
        {
            "id": 2,
            "guid": "http://arxiv.org/abs/2606.11184v1",
            "link": "https://arxiv.org/pdf/2606.11184v1",
            "title": "Paper A",
            "author": "Ada",
            "content": "a much longer abstract from another feed",
            "date": 12,
            "feed_name": "Manipulation",
            "feed_url": "https://export.arxiv.org/rss/cs.RO",
        },
    ]

    papers = group_entries(rows)

    assert len(papers) == 1
    paper = papers[0]
    assert paper.arxiv_id == "2606.11184v1"
    assert paper.entry_ids == [1, 2]
    assert paper.feed_names == ["Robotics", "Manipulation"]
    assert paper.abstract == "a much longer abstract from another feed"
