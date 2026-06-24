from pathlib import Path
import json

from oh_my_rss.app import run_once
from oh_my_rss.arxiv import Paper
from oh_my_rss.config import AppConfig, ArxivDiscoveryConfig, FreshRSSConfig, RuntimeConfig, SiteConfig


def test_run_once_dry_run_merges_wide_arxiv_discovery(monkeypatch, tmp_path: Path):
    config = AppConfig(
        freshrss=FreshRSSConfig(db_path=tmp_path / "db.sqlite", category="论文"),
        runtime=RuntimeConfig(state_dir=tmp_path / "state"),
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


def test_run_once_publishes_source_health_report(monkeypatch, tmp_path: Path):
    config = AppConfig(
        freshrss=FreshRSSConfig(db_path=tmp_path / "db.sqlite", category="论文"),
        runtime=RuntimeConfig(state_dir=tmp_path / "state"),
        site=SiteConfig(public_base_url="https://example.com", output_dir=tmp_path / "site"),
    )
    state_path = config.runtime.state_dir / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "papers": {},
                "source_health": {
                    "latest": {
                        "sources": [
                            {
                                "name": "FreshRSS: 论文",
                                "kind": "freshrss",
                                "candidate_count": 4,
                                "status": "ok",
                            }
                        ]
                    },
                    "history": {},
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("oh_my_rss.app.fetch_freshrss_entries", lambda *args, **kwargs: [])

    changed = run_once(config, write_freshrss_links=False, use_pdf=False)

    assert changed == []
    state = json.loads(state_path.read_text(encoding="utf-8"))
    latest = state["source_health"]["latest"]
    assert latest["warning_count"] == 1
    assert latest["sources"][0]["name"] == "FreshRSS: 论文"
    assert latest["sources"][0]["warning_codes"] == ["zero_after_nonzero"]
    assert (tmp_path / "site" / "reports" / "source-health" / "index.html").exists()
    assert (tmp_path / "site" / "reports" / "source-health.xml").exists()


def test_run_once_rebuilds_main_feed_after_each_generated_summary(monkeypatch, tmp_path: Path):
    config = AppConfig(
        freshrss=FreshRSSConfig(db_path=tmp_path / "db.sqlite", category="论文"),
        runtime=RuntimeConfig(state_dir=tmp_path / "state"),
        site=SiteConfig(public_base_url="https://example.com", output_dir=tmp_path / "site"),
    )

    def fake_fetch_freshrss_entries(*args, **kwargs):
        return [
            {
                "id": 1,
                "guid": "https://arxiv.org/abs/2606.11111v1",
                "link": "https://arxiv.org/abs/2606.11111v1",
                "title": "First Robot Paper",
                "author": "Ada",
                "content": "Robot learning.",
                "date": 200,
                "feed_name": "arXiv cs.RO",
                "feed_url": "https://export.arxiv.org/rss/cs.RO",
            },
            {
                "id": 2,
                "guid": "https://arxiv.org/abs/2606.22222v1",
                "link": "https://arxiv.org/abs/2606.22222v1",
                "title": "Second Robot Paper",
                "author": "Grace",
                "content": "Robot manipulation.",
                "date": 100,
                "feed_name": "arXiv cs.RO",
                "feed_url": "https://export.arxiv.org/rss/cs.RO",
            },
        ]

    feed_snapshots: list[list[str]] = []

    def spy_publish_feed(records, *args, **kwargs):
        feed_snapshots.append([record["title"] for record in records])

    monkeypatch.setattr("oh_my_rss.app.fetch_freshrss_entries", fake_fetch_freshrss_entries)
    monkeypatch.setattr("oh_my_rss.app.run_codex_summary", lambda **kwargs: "# Summary\n\nText")
    monkeypatch.setattr("oh_my_rss.app.publish_feed", spy_publish_feed)
    monkeypatch.setattr("oh_my_rss.app.time.sleep", lambda seconds: None)

    changed = run_once(config, limit=2, write_freshrss_links=False, use_pdf=False)

    assert [record["title"] for record in changed] == ["First Robot Paper", "Second Robot Paper"]
    assert feed_snapshots == [
        ["First Robot Paper"],
        ["First Robot Paper", "Second Robot Paper"],
    ]
