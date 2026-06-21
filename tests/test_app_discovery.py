from pathlib import Path

from oh_my_rss.app import run_once
from oh_my_rss.arxiv import Paper
from oh_my_rss.config import AppConfig, ArxivDiscoveryConfig, FreshRSSConfig, SiteConfig


def test_run_once_dry_run_merges_wide_arxiv_discovery(monkeypatch, tmp_path: Path):
    config = AppConfig(
        freshrss=FreshRSSConfig(db_path=tmp_path / "db.sqlite", category="论文"),
        site=SiteConfig(public_base_url="https://example.com", output_dir=tmp_path / "site"),
        arxiv_discovery=ArxivDiscoveryConfig(enabled=True, keywords=["robot learning"], max_results=10),
    )

    def fake_fetch_freshrss_entries(*args, **kwargs):
        return [
            {
                "id": 1,
                "guid": "https://arxiv.org/abs/2606.11111v1",
                "link": "https://arxiv.org/abs/2606.11111v1",
                "title": "FreshRSS Robot Paper",
                "author": "Ada",
                "content": "Robot learning from subscribed feeds.",
                "date": 100,
                "feed_name": "arXiv cs.RO",
                "feed_url": "https://export.arxiv.org/rss/cs.RO",
            }
        ]

    def fake_fetch_wide_arxiv_papers(*, keywords, max_results):
        assert keywords == ["robot learning"]
        assert max_results == 10
        return [
            Paper(
                arxiv_id="2606.22222v1",
                title="arXiv Robot Paper",
                abstract="Robot manipulation from a non-subscribed arXiv area.",
                date=200,
                feed_names=["arXiv"],
            )
        ]

    monkeypatch.setattr("oh_my_rss.app.fetch_freshrss_entries", fake_fetch_freshrss_entries)
    monkeypatch.setattr("oh_my_rss.app.fetch_wide_arxiv_papers", fake_fetch_wide_arxiv_papers)

    papers = run_once(config, dry_run=True, limit=10)

    assert [paper["arxiv_id"] for paper in papers] == ["2606.22222v1", "2606.11111v1"]
