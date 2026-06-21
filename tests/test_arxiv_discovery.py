from oh_my_rss.arxiv import Paper
from oh_my_rss.arxiv_discovery import (
    build_wide_arxiv_api_url,
    filter_relevant_wide_arxiv_papers,
    merge_paper_candidates,
    parse_arxiv_atom,
)
from oh_my_rss.domains import classify_research_domains


def test_build_wide_arxiv_api_url_uses_keyword_discovery_without_subject_filter():
    url = build_wide_arxiv_api_url(
        keywords=["robot learning", "diffusion policy"],
        max_results=25,
    )

    assert "export.arxiv.org/api/query" in url
    assert "all%3A%22robot+learning%22" in url
    assert "all%3A%22diffusion+policy%22" in url
    assert "cat%3A" not in url
    assert "max_results=25" in url


def test_parse_arxiv_atom_creates_paper_from_non_robotics_subject():
    atom = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:arxiv="http://arxiv.org/schemas/atom">
      <entry>
        <id>http://arxiv.org/abs/2606.22222v1</id>
        <updated>2026-06-21T09:30:00Z</updated>
        <published>2026-06-21T09:30:00Z</published>
        <title>Diffusion Policy for Dexterous Robot Manipulation</title>
        <summary>We learn contact-rich manipulation policies for a robot hand.</summary>
        <author><name>Ada Lovelace</name></author>
        <arxiv:primary_category term="cs.LG" />
        <category term="cs.LG" />
        <link href="https://arxiv.org/abs/2606.22222v1" rel="alternate" type="text/html" />
        <link href="https://arxiv.org/pdf/2606.22222v1" rel="related" type="application/pdf" />
      </entry>
    </feed>
    """

    papers = parse_arxiv_atom(atom, feed_name="arXiv wide discovery")

    assert len(papers) == 1
    paper = papers[0]
    assert paper.arxiv_id == "2606.22222v1"
    assert paper.source_kind == "arXiv"
    assert paper.feed_names == ["arXiv wide discovery"]
    assert paper.pdf_url == "https://arxiv.org/pdf/2606.22222v1"
    assert "Robot Learning / Policy" in classify_research_domains(paper)
    assert "Manipulation / Dexterous Hands" in classify_research_domains(paper)


def test_merge_paper_candidates_deduplicates_wide_discovery_against_existing_sources():
    freshrss = Paper(
        arxiv_id="2606.22222v1",
        title="FreshRSS title",
        abstract="short",
        date=10,
        entry_ids=[1],
        feed_names=["arXiv cs.RO"],
    )
    wide = Paper(
        arxiv_id="2606.22222v1",
        title="Wide title",
        abstract="longer abstract from arXiv API",
        date=12,
        feed_names=["arXiv wide discovery"],
        feed_urls=["https://export.arxiv.org/api/query?..."],
    )

    merged = merge_paper_candidates([freshrss], [wide])

    assert len(merged) == 1
    assert merged[0].title == "Wide title"
    assert merged[0].abstract == "longer abstract from arXiv API"
    assert merged[0].entry_ids == [1]
    assert merged[0].feed_names == ["arXiv cs.RO", "arXiv wide discovery"]


def test_filter_relevant_wide_arxiv_papers_uses_content_not_subject():
    robot = Paper(
        arxiv_id="2606.22222v1",
        title="Robot Hands from Human Demonstrations",
        abstract="We learn dexterous manipulation policies from human videos.",
        feed_names=["arXiv wide discovery"],
    )
    unrelated = Paper(
        arxiv_id="2606.33333v1",
        title="A Four-Section Bracket for the 48-team World Cup",
        abstract="We study tournament design, ranking manipulation, and bracket navigation.",
        feed_names=["arXiv wide discovery"],
    )

    filtered = filter_relevant_wide_arxiv_papers([robot, unrelated])

    assert filtered == [robot]
