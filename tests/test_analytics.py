from oh_my_rss.analytics import build_monthly_reports


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
