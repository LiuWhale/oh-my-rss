import json
from xml.etree import ElementTree

from oh_my_rss.analytics import build_keyword_trends, build_monthly_reports, build_trending_topics
from oh_my_rss.arxiv import Paper
from oh_my_rss.publisher import (
    category_slug,
    detail_filename,
    publish_detail,
    publish_category_feeds,
    publish_feed,
    publish_feed_directory,
    publish_keyword_trends,
    publish_monthly_reports,
    publish_site_discovery,
    publish_status,
    publish_subscription_opml,
    publish_trending_topics,
)


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
    assert root.findall("channel/item/category") == []


def test_category_slug_prefers_ascii_words_and_falls_back_to_hash():
    assert category_slug("导航规划 / Navigation") == "navigation"
    assert category_slug("机器人").startswith("category-")


def test_publish_detail_records_research_domains_for_category_and_monthly_reports(tmp_path):
    paper = Paper(
        arxiv_id="2606.11184v1",
        title="Safe Diffusion Policy for Mobile Manipulation",
        abstract="A robot learning paper for safe manipulation and navigation.",
        feed_names=["arXiv Robotics latest (cs.RO)"],
        keywords=["robot learning", "safe control"],
    )

    record = publish_detail(
        paper,
        "# Summary\n\nSafe robot manipulation.",
        output_dir=tmp_path,
        public_base_url="https://example.com/summaries",
        generated_at="2026-06-10T18:00:00+08:00",
    )

    assert "research_domains" in record
    assert "Robot Learning / Policy" in record["research_domains"]
    assert "Manipulation / Dexterous Hands" in record["research_domains"]
    assert "Robotics latest (cs.RO)" not in record["research_domains"]
    assert record["keywords"] == ["robot learning", "safe control"]


def test_publish_category_feeds_writes_one_feed_per_category(tmp_path):
    stale_categories = tmp_path / "categories"
    stale_categories.mkdir()
    (stale_categories / "arxiv-robotics-latest-cs-ro.xml").write_text("old", encoding="utf-8")
    (stale_categories / "arxiv-navigation.xml").write_text("old", encoding="utf-8")
    (stale_categories / "arxiv-vision.xml").write_text("old", encoding="utf-8")
    records = [
        {
            "title": "Robot Paper",
            "arxiv_id": "2606.11184v1",
            "url": "https://example.com/summaries/robot.html",
            "generated_at": "2026-06-10T18:00:00+08:00",
            "feed_names": ["arXiv Robotics latest (cs.RO)", "arXiv 导航规划 / Navigation"],
        },
        {
            "title": "Vision Paper",
            "arxiv_id": "2606.11185v1",
            "url": "https://example.com/summaries/vision.html",
            "generated_at": "2026-06-10T18:00:00+08:00",
            "feed_names": ["arXiv Vision"],
        },
    ]

    categories = publish_category_feeds(
        records,
        output_dir=tmp_path,
        public_base_url="https://example.com/summaries",
        generated_at="2026-06-10T18:01:00+08:00",
    )

    assert {item["slug"] for item in categories} == {
        "robotics-latest-cs-ro",
        "navigation",
        "vision",
    }

    robotics = ElementTree.parse(tmp_path / "categories" / "robotics-latest-cs-ro.xml")
    vision = ElementTree.parse(tmp_path / "categories" / "vision.xml")
    category_index = tmp_path / "categories" / "index.json"
    category_opml = tmp_path / "categories" / "opml.xml"

    assert robotics.findtext("./channel/title") == "Oh My RSS - Robotics latest (cs.RO)"
    assert robotics.findtext("./channel/item/title") == "Robot Paper"
    assert [item.text for item in robotics.findall("./channel/item/category")] == ["Robotics latest (cs.RO)"]
    assert vision.findtext("./channel/item/title") == "Vision Paper"
    assert [item.text for item in vision.findall("./channel/item/category")] == ["Vision"]
    assert not (tmp_path / "categories" / "arxiv-robotics-latest-cs-ro.xml").exists()
    assert not (tmp_path / "categories" / "arxiv-navigation.xml").exists()
    assert not (tmp_path / "categories" / "arxiv-vision.xml").exists()
    assert category_index.exists()
    assert category_opml.exists()

    opml = ElementTree.parse(category_opml)
    assert opml.getroot().tag == "opml"
    assert opml.getroot().attrib["version"] == "2.0"
    folder = opml.find("./body/outline")
    assert folder is not None
    assert folder.attrib["text"] == "Oh My RSS 论文分类"
    assert "type" not in folder.attrib
    outlines = {outline.attrib["text"]: outline.attrib for outline in folder.findall("./outline")}
    assert outlines["Robotics latest (cs.RO)"]["type"] == "rss"
    assert (
        outlines["Robotics latest (cs.RO)"]["xmlUrl"]
        == "https://example.com/summaries/categories/robotics-latest-cs-ro.xml"
    )
    assert (
        outlines["导航规划 / Navigation"]["xmlUrl"]
        == "https://example.com/summaries/categories/navigation.xml"
    )


def test_publish_category_feeds_keeps_duplicate_category_aliases_in_sync(tmp_path):
    records = [
        {
            "title": "Coarse robotics paper",
            "arxiv_id": "2606.11184v1",
            "url": "https://example.com/summaries/coarse.html",
            "generated_at": "2026-06-11T18:00:00+08:00",
            "research_domains": ["Robotics / Embodied AI"],
        },
        {
            "title": "Detailed robotics paper",
            "arxiv_id": "2606.11185v1",
            "url": "https://example.com/summaries/detailed.html",
            "generated_at": "2026-06-12T18:00:00+08:00",
            "research_domains": ["Robotics latest (cs.RO)"],
        },
    ]

    categories = publish_category_feeds(
        records,
        output_dir=tmp_path,
        public_base_url="https://example.com/summaries",
        generated_at="2026-06-12T18:01:00+08:00",
    )

    counts = {item["name"]: item["count"] for item in categories}
    assert counts["Robotics / Embodied AI"] == 2
    assert counts["Robotics latest (cs.RO)"] == 2

    coarse = ElementTree.parse(tmp_path / "categories" / "robotics-embodied-ai.xml")
    detailed = ElementTree.parse(tmp_path / "categories" / "robotics-latest-cs-ro.xml")
    coarse_titles = [item.text for item in coarse.findall("./channel/item/title")]
    detailed_titles = [item.text for item in detailed.findall("./channel/item/title")]

    assert coarse_titles == ["Detailed robotics paper", "Coarse robotics paper"]
    assert detailed_titles == coarse_titles


def test_publish_monthly_reports_writes_html_assets_json_and_feed(tmp_path):
    reports = build_monthly_reports(
        [
            {
                "title": "Humanoid paper",
                "url": "https://example.com/summaries/humanoid.html",
                "generated_at": "2026-06-10T18:00:00+08:00",
                "research_domains": ["Humanoid Robots"],
                "venue": "arXiv",
                "summary_excerpt": "A humanoid control paper.",
            },
            {
                "title": "Manipulation paper",
                "url": "https://example.com/summaries/manipulation.html",
                "generated_at": "2026-06-11T18:00:00+08:00",
                "research_domains": ["Manipulation"],
                "venue": "RAL",
                "summary_excerpt": "A robot manipulation paper.",
            },
        ],
        generated_at="2026-06-12T09:00:00+08:00",
    )

    published = publish_monthly_reports(
        reports,
        output_dir=tmp_path,
        public_base_url="https://example.com/summaries",
        generated_at="2026-06-12T09:00:00+08:00",
    )

    assert published[0]["url"] == "https://example.com/summaries/reports/monthly/2026-06.html"
    assert (tmp_path / "reports" / "monthly.xml").exists()
    assert (tmp_path / "reports" / "monthly" / "2026-06.html").exists()
    assert (tmp_path / "reports" / "monthly" / "2026-06.json").exists()
    assert (tmp_path / "reports" / "monthly" / "assets" / "2026-06-direction-bars.svg").exists()
    assert (tmp_path / "reports" / "monthly" / "assets" / "2026-06-source-donut.svg").exists()
    assert (tmp_path / "reports" / "monthly" / "assets" / "2026-06-trend-animated.svg").exists()

    root = ElementTree.parse(tmp_path / "reports" / "monthly.xml").getroot()
    assert root.findtext("channel/title") == "Oh My RSS Monthly Research Radar"
    assert root.findtext("channel/item/title") == "2026-06 研究趋势月报"
    assert (
        '<a href="https://example.com/summaries/reports/monthly/2026-06.html">查看网页</a>'
        in (root.findtext("channel/item/description") or "")
    )

    html = (tmp_path / "reports" / "monthly" / "2026-06.html").read_text(encoding="utf-8")
    assert "热门方向" in html
    assert "Humanoid Robots" in html
    assert "2026-06-trend-animated.svg" in html

    trend_svg = (
        tmp_path / "reports" / "monthly" / "assets" / "2026-06-trend-animated.svg"
    ).read_text(encoding="utf-8")
    assert "{top + chart_height}" not in trend_svg
    assert "<animate " in trend_svg


def test_publish_trending_topics_writes_topic_pages_json_and_feed(tmp_path):
    stale_html = tmp_path / "reports" / "trending" / "stale-topic.html"
    stale_html.parent.mkdir(parents=True, exist_ok=True)
    stale_html.write_text("old detail page", encoding="utf-8")

    topics = build_trending_topics(
        [
            {
                "title": "Humanoid paper",
                "url": "https://example.com/summaries/humanoid.html",
                "generated_at": "2026-06-10T18:00:00+08:00",
                "research_domains": ["Humanoid / Legged Robots"],
                "venue": "arXiv",
                "summary_excerpt": "A humanoid control paper.",
            },
            {
                "title": "Manipulation paper",
                "url": "https://example.com/summaries/manipulation.html",
                "generated_at": "2026-06-11T18:00:00+08:00",
                "research_domains": ["Manipulation / Dexterous Hands"],
                "venue": "RAL",
                "summary_excerpt": "A robot manipulation paper.",
            },
            {
                "title": "Dexterous paper",
                "url": "https://example.com/summaries/dexterous.html",
                "generated_at": "2026-06-12T18:00:00+08:00",
                "research_domains": ["Manipulation / Dexterous Hands"],
                "venue": "ICRA",
                "summary_excerpt": "A dexterous hand paper.",
            },
        ],
        generated_at="2026-06-12T09:00:00+08:00",
    )

    published = publish_trending_topics(
        topics,
        output_dir=tmp_path,
        public_base_url="https://example.com/summaries",
        generated_at="2026-06-12T09:00:00+08:00",
    )

    assert published[0]["url"] == (
        "https://example.com/summaries/reports/trending/index.html"
        "#topic-manipulation-dexterous-hands"
    )
    assert (tmp_path / "reports" / "trending.xml").exists()
    assert (tmp_path / "reports" / "trending" / "index.json").exists()
    assert (tmp_path / "reports" / "trending" / "index.html").exists()
    assert not (tmp_path / "reports" / "trending" / "manipulation-dexterous-hands.html").exists()
    assert not stale_html.exists()

    root = ElementTree.parse(tmp_path / "reports" / "trending.xml").getroot()
    assert root.findtext("channel/title") == "Oh My RSS Trending Research Topics"
    assert root.findtext("channel/link") == "https://example.com/summaries/reports/trending/index.html"
    assert root.findtext("channel/item/title") == "Manipulation / Dexterous Hands - 2026-06 热点方向"
    assert (
        '<a href="https://example.com/summaries/reports/trending/index.html#topic-manipulation-dexterous-hands">查看网页</a>'
        in (root.findtext("channel/item/description") or "")
    )

    html = (tmp_path / "reports" / "trending" / "index.html").read_text(encoding="utf-8")
    assert "热点方向" in html
    assert 'id="topic-manipulation-dexterous-hands"' in html
    assert "Manipulation paper" in html
    assert "Humanoid paper" in html
    assert "趋势月份" in html


def test_publish_keyword_trends_writes_keyword_pages_json_and_feed(tmp_path):
    stale_html = tmp_path / "reports" / "keywords" / "stale-keyword.html"
    stale_html.parent.mkdir(parents=True, exist_ok=True)
    stale_html.write_text("old detail page", encoding="utf-8")

    trends = build_keyword_trends(
        [
            {
                "title": "VLA Diffusion Policy",
                "url": "https://example.com/summaries/vla.html",
                "generated_at": "2026-06-10T18:00:00+08:00",
                "research_domains": ["Vision-Language-Action"],
                "venue": "arXiv",
                "summary_excerpt": "A VLA diffusion policy paper.",
            },
            {
                "title": "Humanoid VLA",
                "url": "https://example.com/summaries/humanoid-vla.html",
                "generated_at": "2026-06-11T18:00:00+08:00",
                "research_domains": ["Humanoid / Legged Robots", "Vision-Language-Action"],
                "venue": "RAL",
                "summary_excerpt": "A humanoid VLA paper.",
            },
        ],
        generated_at="2026-06-12T09:00:00+08:00",
    )

    published = publish_keyword_trends(
        trends,
        output_dir=tmp_path,
        public_base_url="https://example.com/summaries",
        generated_at="2026-06-12T09:00:00+08:00",
    )

    assert published[0]["url"] == "https://example.com/summaries/reports/keywords/index.html#keyword-vla"
    assert (tmp_path / "reports" / "keywords.xml").exists()
    assert (tmp_path / "reports" / "keywords" / "index.json").exists()
    assert (tmp_path / "reports" / "keywords" / "index.html").exists()
    assert not (tmp_path / "reports" / "keywords" / "vla.html").exists()
    assert not stale_html.exists()

    root = ElementTree.parse(tmp_path / "reports" / "keywords.xml").getroot()
    assert root.findtext("channel/title") == "Oh My RSS Trending Research Keywords"
    assert root.findtext("channel/link") == "https://example.com/summaries/reports/keywords/index.html"
    assert root.findtext("channel/item/title") == "VLA - 2026-06 关键词趋势"
    assert (
        '<a href="https://example.com/summaries/reports/keywords/index.html#keyword-vla">查看网页</a>'
        in (root.findtext("channel/item/description") or "")
    )

    html = (tmp_path / "reports" / "keywords" / "index.html").read_text(encoding="utf-8")
    assert "关键词趋势" in html
    assert 'id="keyword-vla"' in html
    assert "Humanoid VLA" in html
    assert "趋势月份" in html


def test_publish_subscription_opml_writes_complete_public_feed_bundle(tmp_path):
    category_records = [
        {
            "name": "Vision-Language-Action",
            "slug": "vision-language-action",
            "url": "https://example.com/summaries/categories/vision-language-action.xml",
            "count": 3,
        }
    ]

    publish_subscription_opml(
        category_records,
        output_dir=tmp_path,
        public_base_url="https://example.com/summaries",
    )

    opml_path = tmp_path / "opml.xml"
    assert opml_path.exists()

    opml = ElementTree.parse(opml_path)
    assert opml.getroot().tag == "opml"
    assert opml.findtext("./head/title") == "Oh My RSS subscription bundle"
    outlines = {outline.attrib["text"]: outline.attrib for outline in opml.findall("./body/outline")}

    assert outlines["Oh My RSS - All Summaries"]["xmlUrl"] == "https://example.com/summaries/feed.xml"
    assert outlines["Oh My RSS - Monthly Research Radar"]["xmlUrl"] == (
        "https://example.com/summaries/reports/monthly.xml"
    )
    assert outlines["Oh My RSS - Trending Research Topics"]["xmlUrl"] == (
        "https://example.com/summaries/reports/trending.xml"
    )
    assert outlines["Oh My RSS - Trending Research Keywords"]["xmlUrl"] == (
        "https://example.com/summaries/reports/keywords.xml"
    )
    assert outlines["Vision-Language-Action"]["xmlUrl"] == (
        "https://example.com/summaries/categories/vision-language-action.xml"
    )


def test_publish_feed_directory_writes_machine_readable_public_feed_list(tmp_path):
    category_records = [
        {
            "name": "Vision-Language-Action",
            "slug": "vision-language-action",
            "url": "https://example.com/summaries/categories/vision-language-action.xml",
            "count": 3,
        }
    ]

    publish_feed_directory(
        category_records,
        output_dir=tmp_path,
        public_base_url="https://example.com/summaries",
        generated_at="2026-06-12T15:30:00+08:00",
    )

    data = json.loads((tmp_path / "feeds.json").read_text(encoding="utf-8"))

    assert data["title"] == "Oh My RSS feed directory"
    assert data["generated_at"] == "2026-06-12T15:30:00+08:00"
    assert data["public_base_url"] == "https://example.com/summaries"
    assert data["feed_count"] == 8

    feeds = {item["name"]: item for item in data["feeds"]}
    assert feeds["Oh My RSS - All Summaries"]["url"] == "https://example.com/summaries/feed.xml"
    assert feeds["Oh My RSS - Subscription OPML"]["format"] == "opml"
    assert feeds["Oh My RSS - Trending Research Keywords"]["kind"] == "keyword-report"
    assert feeds["Oh My RSS - Source Health Radar"] == {
        "name": "Oh My RSS - Source Health Radar",
        "kind": "source-health-report",
        "format": "rss",
        "url": "https://example.com/summaries/reports/source-health.xml",
        "html_url": "https://example.com/summaries/reports/source-health/index.html",
    }
    assert feeds["Vision-Language-Action"] == {
        "name": "Vision-Language-Action",
        "kind": "category",
        "format": "rss",
        "url": "https://example.com/summaries/categories/vision-language-action.xml",
        "html_url": "https://example.com/summaries/categories/vision-language-action.xml",
        "slug": "vision-language-action",
        "count": 3,
    }


def test_publish_status_writes_public_service_health_summary(tmp_path):
    records = [
        {
            "title": "Older paper",
            "url": "https://example.com/summaries/older.html",
            "generated_at": "2026-06-10T10:00:00+08:00",
        },
        {
            "title": "Newest paper",
            "url": "https://example.com/summaries/newest.html",
            "generated_at": "2026-06-12T10:00:00+08:00",
        },
    ]
    category_records = [
        {
            "name": "Vision-Language-Action",
            "slug": "vision-language-action",
            "url": "https://example.com/summaries/categories/vision-language-action.xml",
            "count": 2,
        }
    ]

    publish_status(
        records,
        category_records=category_records,
        monthly_reports=[object()],
        trending_topics=[object(), object()],
        keyword_trends=[object(), object(), object()],
        output_dir=tmp_path,
        public_base_url="https://example.com/summaries",
        generated_at="2026-06-12T15:45:00+08:00",
    )

    data = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))

    assert data["ok"] is True
    assert data["title"] == "Oh My RSS status"
    assert data["generated_at"] == "2026-06-12T15:45:00+08:00"
    assert data["summary_count"] == 2
    assert data["category_count"] == 1
    assert data["monthly_report_count"] == 1
    assert data["trending_topic_count"] == 2
    assert data["keyword_trend_count"] == 3
    assert data["latest_summary"] == {
        "title": "Newest paper",
        "url": "https://example.com/summaries/newest.html",
        "generated_at": "2026-06-12T10:00:00+08:00",
    }
    assert data["feeds"]["feed_directory"] == "https://example.com/summaries/feeds.json"
    assert data["feeds"]["subscription_opml"] == "https://example.com/summaries/opml.xml"
    assert data["feeds"]["keywords"] == "https://example.com/summaries/reports/keywords.xml"
    assert data["feeds"]["source_health"] == "https://example.com/summaries/reports/source-health.xml"


def test_publish_site_discovery_writes_robots_and_sitemap(tmp_path):
    records = [
        {
            "title": "Paper",
            "url": "https://example.com/summaries/paper.html",
            "generated_at": "2026-06-11T10:00:00+08:00",
        }
    ]
    monthly_reports = build_monthly_reports(
        [
            {
                "title": "Paper",
                "url": "https://example.com/summaries/paper.html",
                "generated_at": "2026-06-11T10:00:00+08:00",
                "research_domains": ["Vision-Language-Action"],
            }
        ],
        generated_at="2026-06-12T15:50:00+08:00",
    )
    trending_topics = build_trending_topics(
        [
            {
                "title": "Paper",
                "url": "https://example.com/summaries/paper.html",
                "generated_at": "2026-06-11T10:00:00+08:00",
                "research_domains": ["Vision-Language-Action"],
            }
        ],
        generated_at="2026-06-12T15:50:00+08:00",
    )
    keyword_trends = build_keyword_trends(
        [
            {
                "title": "VLA paper",
                "url": "https://example.com/summaries/paper.html",
                "generated_at": "2026-06-11T10:00:00+08:00",
                "research_domains": ["Vision-Language-Action"],
            }
        ],
        generated_at="2026-06-12T15:50:00+08:00",
    )

    publish_site_discovery(
        records,
        monthly_reports=monthly_reports,
        trending_topics=trending_topics,
        keyword_trends=keyword_trends,
        output_dir=tmp_path,
        public_base_url="https://example.com/summaries",
        generated_at="2026-06-12T15:50:00+08:00",
    )

    robots = (tmp_path / "robots.txt").read_text(encoding="utf-8")
    assert "User-agent: *" in robots
    assert "Sitemap: https://example.com/summaries/sitemap.xml" in robots

    root = ElementTree.parse(tmp_path / "sitemap.xml").getroot()
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [item.text for item in root.findall("./sm:url/sm:loc", namespace)]

    assert "https://example.com/summaries/index.html" in urls
    assert "https://example.com/summaries/paper.html" in urls
    assert "https://example.com/summaries/reports/monthly/2026-06.html" in urls
    assert "https://example.com/summaries/reports/trending/index.html" in urls
    assert "https://example.com/summaries/reports/keywords/index.html" in urls
