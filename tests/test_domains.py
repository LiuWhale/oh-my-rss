from oh_my_rss.arxiv import Paper
from oh_my_rss.domains import classify_research_domains


def test_classify_research_domains_combines_robotics_topics_from_title_and_abstract():
    paper = Paper(
        arxiv_id="2606.11184v1",
        title="Diffusion Policy for Dexterous Humanoid Manipulation",
        abstract=(
            "We study vision-language-action policies for robot manipulation "
            "with humanoid whole-body control and reinforcement learning."
        ),
        feed_names=["arXiv Robotics latest (cs.RO)"],
    )

    domains = classify_research_domains(paper)

    assert domains[:4] == [
        "Robot Learning / Policy",
        "Manipulation / Dexterous Hands",
        "Humanoid / Legged Robots",
        "Vision-Language-Action",
    ]
    assert "Robotics / Embodied AI" in domains


def test_classify_research_domains_preserves_specific_arxiv_topic_when_no_keyword_matches():
    paper = Paper(
        arxiv_id="2606.11185v1",
        title="A theorem about graph spectra",
        abstract="We study eigenvalues of sparse graphs.",
        feed_names=["arXiv Machine Learning (cs.LG)"],
    )

    domains = classify_research_domains(paper)

    assert domains == ["Machine Learning (cs.LG)"]
