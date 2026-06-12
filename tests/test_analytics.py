from oh_my_rss.analytics import build_keyword_trends, build_monthly_reports, build_trending_topics


def test_build_monthly_reports_counts_directions_sources_and_growth():
    records = [
        {
            "title": "June VLA paper",
            "url": "https://example.com/summaries/vla.html",
            "generated_at": "2026-06-10T10:00:00+08:00",
            "research_domains": ["Vision-Language-Action", "Robot Learning"],
            "venue": "arXiv",
            "summary_excerpt": "A VLA manipulation paper.",
        },
        {
            "title": "June manipulation paper",
            "url": "https://example.com/summaries/manipulation.html",
            "generated_at": "2026-06-11T10:00:00+08:00",
            "feed_names": ["RAL"],
            "summary_excerpt": "Dexterous manipulation.",
        },
        {
            "title": "May robot learning paper",
            "url": "https://example.com/summaries/may.html",
            "generated_at": "2026-05-21T10:00:00+08:00",
            "research_domains": ["Robot Learning"],
            "venue": "TRO",
            "summary_excerpt": "A previous robot learning paper.",
        },
    ]

    reports = build_monthly_reports(records, generated_at="2026-06-12T09:00:00+08:00")

    june = reports[0]
    assert june.month == "2026-06"
    assert june.total_papers == 2
    assert june.direction_counts["Robot Learning"] == 1
    assert june.direction_counts["Vision-Language-Action"] == 1
    assert june.source_counts["arXiv"] == 1
    assert june.source_counts["RAL"] == 1
    assert june.direction_growth["Vision-Language-Action"] == 1
    assert june.direction_growth["Robot Learning"] == 0
    assert june.top_papers[0].title == "June manipulation paper"
    assert june.trend_months == ["2026-05", "2026-06"]


def test_build_monthly_reports_infers_domains_when_record_has_no_research_domains():
    reports = build_monthly_reports(
        [
            {
                "title": "Humanoid Diffusion Policy for Mobile Manipulation",
                "url": "https://example.com/summaries/humanoid.html",
                "generated_at": "2026-06-11T10:00:00+08:00",
                "feed_names": ["arXiv Robotics latest (cs.RO)"],
                "summary_excerpt": "A robot learning system for humanoid manipulation.",
            },
        ],
        generated_at="2026-06-12T09:00:00+08:00",
    )

    domains = reports[0].direction_counts
    assert domains["Robot Learning / Policy"] == 1
    assert domains["Humanoid / Legged Robots"] == 1
    assert "Robotics latest (cs.RO)" not in domains


def test_build_trending_topics_ranks_hot_directions_with_representative_papers():
    records = [
        {
            "title": "May manipulation baseline",
            "url": "https://example.com/summaries/may-manipulation.html",
            "generated_at": "2026-05-08T10:00:00+08:00",
            "research_domains": ["Manipulation / Dexterous Hands"],
            "venue": "arXiv",
            "summary_excerpt": "Previous manipulation work.",
        },
        {
            "title": "June humanoid manipulation",
            "url": "https://example.com/summaries/humanoid.html",
            "generated_at": "2026-06-11T10:00:00+08:00",
            "research_domains": ["Humanoid / Legged Robots", "Manipulation / Dexterous Hands"],
            "venue": "RAL",
            "summary_excerpt": "A humanoid manipulation paper.",
        },
        {
            "title": "June VLA manipulation",
            "url": "https://example.com/summaries/vla.html",
            "generated_at": "2026-06-12T10:00:00+08:00",
            "research_domains": ["Vision-Language-Action", "Manipulation / Dexterous Hands"],
            "venue": "ICRA",
            "summary_excerpt": "A VLA manipulation paper.",
        },
    ]

    topics = build_trending_topics(records, generated_at="2026-06-12T12:00:00+08:00")

    assert topics[0].name == "Manipulation / Dexterous Hands"
    assert topics[0].month == "2026-06"
    assert topics[0].paper_count == 2
    assert topics[0].growth == 1
    assert topics[0].source_counts == {"ICRA": 1, "RAL": 1}
    assert [paper.title for paper in topics[0].papers] == [
        "June VLA manipulation",
        "June humanoid manipulation",
    ]
    assert topics[0].trend_months == ["2026-05", "2026-06"]
    assert topics[0].trend_counts == [1, 2]


def test_build_keyword_trends_extracts_specific_research_terms_and_growth():
    records = [
        {
            "title": "May Diffusion Policy for Dexterous Manipulation",
            "url": "https://example.com/summaries/may-dp.html",
            "generated_at": "2026-05-08T10:00:00+08:00",
            "research_domains": ["Manipulation / Dexterous Hands"],
            "venue": "arXiv",
            "summary_excerpt": "Previous diffusion policy baseline.",
        },
        {
            "title": "VLA Diffusion Policy for Humanoid Manipulation",
            "url": "https://example.com/summaries/vla-dp.html",
            "generated_at": "2026-06-11T10:00:00+08:00",
            "research_domains": ["Vision-Language-Action", "Humanoid / Legged Robots"],
            "venue": "RAL",
            "summary_excerpt": "A vision-language-action model with diffusion policy.",
        },
        {
            "title": "Humanoid VLA for Safety Filter Evaluation",
            "url": "https://example.com/summaries/humanoid-vla.html",
            "generated_at": "2026-06-12T10:00:00+08:00",
            "research_domains": ["Safety / Control", "Vision-Language-Action"],
            "venue": "ICRA",
            "summary_excerpt": "A safety filter benchmark for humanoid VLA systems.",
        },
    ]

    trends = build_keyword_trends(records, generated_at="2026-06-12T12:00:00+08:00")

    assert trends[0].keyword == "VLA"
    assert trends[0].month == "2026-06"
    assert trends[0].paper_count == 2
    assert trends[0].growth == 2
    assert trends[0].source_counts == {"ICRA": 1, "RAL": 1}
    assert [paper.title for paper in trends[0].papers] == [
        "Humanoid VLA for Safety Filter Evaluation",
        "VLA Diffusion Policy for Humanoid Manipulation",
    ]
    assert trends[0].trend_months == ["2026-05", "2026-06"]
    assert trends[0].trend_counts == [0, 2]
