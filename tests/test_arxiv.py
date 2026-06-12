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


def test_group_entries_accepts_doi_paper_without_arxiv_url():
    rows = [
        {
            "id": 10,
            "guid": "https://doi.org/10.1177/02783649261234567",
            "link": "https://journals.sagepub.com/doi/10.1177/02783649261234567",
            "title": "IJRR Paper",
            "author": "Grace",
            "content": "A robotics journal abstract.",
            "date": 20,
            "feed_name": "IJRR OnlineFirst",
            "feed_url": "https://journals.sagepub.com/action/showFeed?type=etoc&feed=rss",
        }
    ]

    papers = group_entries(rows)

    assert len(papers) == 1
    paper = papers[0]
    assert paper.paper_id == "doi:10.1177/02783649261234567"
    assert paper.arxiv_id == "doi:10.1177/02783649261234567"
    assert paper.source_kind == "DOI"
    assert paper.abs_url == "https://journals.sagepub.com/doi/10.1177/02783649261234567"
    assert paper.pdf_url == ""


def test_group_entries_accepts_generic_paper_link_when_no_doi_is_available():
    rows = [
        {
            "id": 11,
            "guid": "https://roboticsconference.org/program/paper-42",
            "link": "https://roboticsconference.org/program/paper-42",
            "title": "Conference Paper",
            "author": "",
            "content": "An accepted conference paper abstract.",
            "date": 21,
            "feed_name": "RSS Conference",
            "feed_url": "https://roboticsconference.org/rss.xml",
        }
    ]

    paper = group_entries(rows)[0]

    assert paper.paper_id.startswith("url:")
    assert paper.source_kind == "RSS"
    assert paper.abs_url == "https://roboticsconference.org/program/paper-42"
