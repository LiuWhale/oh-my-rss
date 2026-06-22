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


def test_classify_research_domains_does_not_reinforce_stale_vla_feed_label():
    paper = Paper(
        arxiv_id="cvf-iccv-2025-81cb3839b2bf25e2",
        title=(
            "One Polyp Identifies All: One-Shot Polyp Segmentation with SAM via "
            "Cascaded Priors and Iterative Prompt Evolution"
        ),
        abstract="We study one-shot medical polyp segmentation with SAM priors.",
        feed_names=["VLA / Multimodal Agents"],
    )

    domains = classify_research_domains(paper)

    assert all("VLA" not in domain and "Vision-Language-Action" not in domain for domain in domains)
    assert "3D Vision / Perception" in domains


def test_classify_research_domains_keeps_explicit_vla_papers():
    paper = Paper(
        arxiv_id="2606.11186v1",
        title="OpenVLA: An Open-Source Vision-Language-Action Model",
        abstract="We train a vision-language-action policy for general robot control.",
        feed_names=["arXiv"],
    )

    domains = classify_research_domains(paper)

    assert "Vision-Language-Action" in domains


def test_policy_word_without_robot_learning_context_does_not_match_robot_policy():
    paper = Paper(
        arxiv_id="2606.11187v1",
        title="A Data Retention Policy for Web Search Logs",
        abstract="We analyze privacy policies and log retention for search systems.",
        feed_names=["arXiv"],
    )

    domains = classify_research_domains(paper)

    assert "Robot Learning / Policy" not in domains


def test_safety_word_in_plain_evaluation_does_not_match_safety_control():
    paper = Paper(
        arxiv_id="2606.11188v1",
        title="Safety Evaluation of Image Captioning Models",
        abstract="We provide a benchmark dataset and evaluation protocol for caption quality.",
        feed_names=["arXiv"],
    )

    domains = classify_research_domains(paper)

    assert "Safety / Control" not in domains
    assert "Benchmark / Dataset / Evaluation" in domains


def test_plain_llm_foundation_model_does_not_match_embodied_ai():
    paper = Paper(
        arxiv_id="2606.11189v1",
        title="A Foundation Model for Text Reasoning",
        abstract="We train a large language model for mathematical question answering.",
        feed_names=["arXiv"],
    )

    domains = classify_research_domains(paper)

    assert "Embodied AI / Foundation Models" not in domains


def test_cbf_and_safe_control_still_match_safety_control():
    paper = Paper(
        arxiv_id="2606.11190v1",
        title="Control Barrier Functions for Safe Robot Navigation",
        abstract="We use CBF constraints for safe control of mobile robots.",
        feed_names=["arXiv"],
    )

    domains = classify_research_domains(paper)

    assert "Safety / Control" in domains
    assert "Robotics / Embodied AI" in domains


def test_robot_imitation_learning_still_matches_robot_policy():
    paper = Paper(
        arxiv_id="2606.11191v1",
        title="Imitation Learning for Bimanual Robot Manipulation",
        abstract="We learn a manipulation policy from demonstrations for robotic arms.",
        feed_names=["arXiv"],
    )

    domains = classify_research_domains(paper)

    assert "Robot Learning / Policy" in domains
    assert "Manipulation / Dexterous Hands" in domains
    assert "Robotics / Embodied AI" in domains
