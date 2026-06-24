from oh_my_rss.arxiv import Paper
from oh_my_rss.domains import classify_record_domains, classify_research_domains


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


def test_classify_research_domains_does_not_use_source_feed_without_explicit_evidence():
    paper = Paper(
        arxiv_id="2606.11185v1",
        title="A theorem about graph spectra",
        abstract="We study eigenvalues of sparse graphs.",
        feed_names=["arXiv Machine Learning (cs.LG)"],
    )

    domains = classify_research_domains(paper)

    assert domains == ["Uncategorized"]


def test_generic_navigation_planning_terms_do_not_match_without_domain_objects():
    paper = Paper(
        arxiv_id="2606.11192v1",
        title="Navigation Strategies for Legal Document Search",
        abstract=(
            "We study navigation and planning policies for browsing legal archives "
            "and controlling query expansion in a web search interface."
        ),
        feed_names=["arXiv"],
    )

    domains = classify_research_domains(paper)

    assert "Navigation / Planning" not in domains
    assert "Robot Learning / Policy" not in domains
    assert "Robotics / Embodied AI" not in domains


def test_ranking_manipulation_does_not_match_robot_manipulation():
    paper = Paper(
        arxiv_id="2606.11193v1",
        title="Ranking Manipulation in Tournament Search Systems",
        abstract="We analyze manipulation attacks against ranking and recommendation systems.",
        feed_names=["arXiv"],
    )

    domains = classify_research_domains(paper)

    assert "Manipulation / Dexterous Hands" not in domains
    assert "Robotics / Embodied AI" not in domains


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


def test_cloth_manipulation_is_not_slam_from_stale_discovery_feed():
    paper = Paper(
        arxiv_id="2606.24552v1",
        title="Enabling Robust Cloth Manipulation via Inference-Time Simulator-in-the-Loop Refinement",
        abstract=(
            "We refine a robot manipulation policy for deformable cloth tasks using "
            "inference-time simulator-in-the-loop rollouts and real robot feedback."
        ),
        feed_names=["arXiv SLAM定位建图 / Perception", "arXiv 操作抓取 / Manipulation"],
    )

    domains = classify_research_domains(paper)

    assert "Manipulation / Dexterous Hands" in domains
    assert "Robot Learning / Policy" in domains
    assert "SLAM / Mapping / Localization" not in domains
    assert "Vision-Language-Action" not in domains


def test_open_vocabulary_relocalization_is_not_vla_without_action_evidence():
    paper = Paper(
        arxiv_id="2606.24767v1",
        title="Compact Object-Level Representations with Open-Vocabulary Understanding for Indoor Visual Relocalization",
        abstract=(
            "The method builds object-level scene representations for indoor visual "
            "relocalization and pose estimation from open-vocabulary perception."
        ),
        feed_names=["arXiv VLA / Vision-Language-Action"],
    )

    domains = classify_research_domains(paper)

    assert "SLAM / Mapping / Localization" in domains
    assert "3D Vision / Perception" in domains
    assert "Vision-Language-Action" not in domains


def test_stale_record_domains_are_recomputed_from_summary_excerpt():
    record = {
        "title": (
            "One Polyp Identifies All: One-Shot Polyp Segmentation with SAM via "
            "Cascaded Priors and Iterative Prompt Evolution"
        ),
        "summary_excerpt": "A medical image segmentation method for polyp masks using SAM priors.",
        "research_domains": ["VLA / Multimodal Agents"],
        "feed_names": ["VLA / Multimodal Agents"],
    }

    domains = classify_record_domains(record)

    assert "3D Vision / Perception" in domains
    assert "Vision-Language-Action" not in domains


def test_summary_excerpt_can_recover_precise_domains_when_abstract_is_missing():
    record = {
        "title": "FT-WBC: Learning Fault-Tolerant Whole-Body Control for Legged Loco-Manipulation",
        "summary_excerpt": (
            "The paper learns fault-tolerant whole-body control for legged robot "
            "loco-manipulation with robust control and sim-to-real evaluation."
        ),
        "research_domains": ["Robotics / Embodied AI", "Reinforcement Learning / Control"],
        "feed_names": ["arXiv SLAM定位建图 / Perception"],
    }

    domains = classify_record_domains(record)

    assert "Humanoid / Legged Robots" in domains
    assert "Safety / Control" in domains
    assert "SLAM / Mapping / Localization" not in domains


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


def test_vla_matching_accepts_abbreviation_full_name_and_separators():
    titles = [
        "A VLA Flow Model for General Robot Control",
        "Vision Language Action Policies for Robot Manipulation",
        "Vision/Language/Action Controllers for Mobile Manipulation",
        "Vision–Language–Action Model for Robot Control",
    ]

    for index, title in enumerate(titles):
        paper = Paper(
            arxiv_id=f"2606.1120{index}v1",
            title=title,
            abstract="We study robot policies for manipulation and control.",
            feed_names=["arXiv"],
        )

        domains = classify_research_domains(paper)

        assert "Vision-Language-Action" in domains


def test_vlm_action_understanding_without_robot_policy_context_is_not_vla():
    paper = Paper(
        arxiv_id="2606.11210v1",
        title="Self-guided Visual Reasoning in VLM for Fine-grained Action Understanding",
        abstract="We study video action understanding and visual reasoning.",
        feed_names=["arXiv"],
    )

    domains = classify_research_domains(paper)

    assert "Vision-Language-Action" not in domains
    assert "Robotics / Embodied AI" not in domains


def test_navigation_world_model_with_multimodal_action_prediction_is_not_vla():
    paper = Paper(
        arxiv_id="2606.24101v1",
        title="NavWM: A Unified Navigation World Model for Foresight-Driven Planning",
        abstract=(
            "Conventional visual navigation policies often struggle with myopic decision-making. "
            "NavWM is a unified navigation world model that integrates latent world reasoning, "
            "multimodal action prediction, and "
            "controllable visual generation for robot control. An anchor-based multimodal "
            "trajectory forecasting framework generates diverse actions, and visual foresight "
            "selects the optimal path for closed-loop planning."
        ),
        feed_names=["arXiv"],
    )

    domains = classify_research_domains(paper)

    assert "Vision-Language-Action" not in domains
    assert "Navigation / Planning" in domains
    assert "Robot Learning / Policy" in domains
    assert "Embodied AI / Foundation Models" in domains


def test_vlm_scene_graph_robotics_application_is_not_vla():
    paper = Paper(
        arxiv_id="2606.23312v1",
        title=(
            "From Pixels to Concepts: Growing Rich 3D Semantic Scene Graph Forests "
            "utilizing Foundation Models"
        ),
        abstract=(
            "Operating in complex real-world environments requires robots to understand "
            "their surroundings on a functional semantic level. Hierarchical 3D scene "
            "graphs integrate geometric, semantic, and relational data within a unified "
            "spatial framework. This paper explores foundation models to build forests "
            "of 3D scene graphs with open semantic relationships to improve scene "
            "understanding and robotic task execution. Instance-specific concept-nodes "
            "and relationships are first identified by a VLM and extended upon by a LLM. "
            "Downstream suitability is demonstrated in an open-vocabulary object-retrieval "
            "task using ScanNet data and a real-world indoor deployment using a Boston "
            "Dynamics Spot."
        ),
        feed_names=["arXiv VLA / Vision-Language-Action"],
    )

    domains = classify_research_domains(paper)

    assert "Vision-Language-Action" not in domains
    assert "3D Vision / Perception" in domains
    assert "Embodied AI / Foundation Models" in domains
    assert "Robotics / Embodied AI" in domains


def test_vla_title_without_abstract_or_keyword_support_is_not_enough():
    paper = Paper(
        arxiv_id="2606.11212v1",
        title="Vision-Language-Action Model for Fine-grained Action Understanding",
        abstract="We study video action recognition and temporal visual reasoning in web videos.",
        feed_names=["arXiv"],
    )

    domains = classify_research_domains(paper)

    assert "Vision-Language-Action" not in domains
    assert "Robotics / Embodied AI" not in domains


def test_keywords_are_strong_classification_evidence():
    paper = Paper(
        arxiv_id="2606.11213v1",
        title="Policy Distillation at Scale",
        abstract="We evaluate a scalable learning system.",
        feed_names=["arXiv"],
        keywords=["robot learning", "imitation learning", "robot manipulation"],
    )

    domains = classify_research_domains(paper)

    assert "Robot Learning / Policy" in domains
    assert "Manipulation / Dexterous Hands" in domains
    assert "Robotics / Embodied AI" in domains


def test_record_keyword_fields_are_used_when_research_domains_are_missing():
    record = {
        "title": "A Generalist Policy",
        "summary_excerpt": "We evaluate the model on manipulation tasks.",
        "keywords": ["VLA", "vision-language-action", "robot manipulation"],
        "feed_names": ["arXiv"],
    }

    domains = classify_record_domains(record)

    assert "Vision-Language-Action" in domains
    assert "Manipulation / Dexterous Hands" in domains
    assert "Robotics / Embodied AI" in domains


def test_biological_locomotion_without_robot_context_is_not_robotics():
    paper = Paper(
        arxiv_id="2606.11211v1",
        title="Data-driven Geometric Phase in Biological Locomotion",
        abstract="We analyze locomotion patterns in biological systems.",
        feed_names=["arXiv"],
    )

    domains = classify_research_domains(paper)

    assert "Robotics / Embodied AI" not in domains
    assert "Humanoid / Legged Robots" not in domains
