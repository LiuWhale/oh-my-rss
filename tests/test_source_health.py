import json
from xml.etree import ElementTree

from oh_my_rss.publisher import publish_source_health_report
from oh_my_rss.source_health import (
    build_source_health_report,
    record_source_health_snapshot,
)


def test_build_source_health_report_flags_zero_errors_and_stale_year():
    current = [
        {
            "name": "ICRA",
            "kind": "ieee-search",
            "candidate_count": 0,
            "status": "ok",
            "configured_year": 2025,
        },
        {
            "name": "RSS",
            "kind": "conference-page",
            "candidate_count": 12,
            "status": "error",
            "error": "HTTP 500",
            "configured_year": 2026,
        },
    ]
    previous = [
        {
            "name": "ICRA",
            "kind": "ieee-search",
            "candidate_count": 17,
            "status": "ok",
            "configured_year": 2025,
        }
    ]

    report = build_source_health_report(
        current,
        previous_records=previous,
        generated_at="2026-06-21T23:50:00+08:00",
        current_year=2026,
    )

    icra = report["sources"][0]
    rss = report["sources"][1]
    assert icra["warning_codes"] == ["zero_after_nonzero", "stale_year"]
    assert "上一轮 17 篇，这一轮 0 篇" in icra["warnings"][0]
    assert "配置年份 2025 早于当前年份 2026" in icra["warnings"][1]
    assert rss["warning_codes"] == ["fetch_error"]
    assert "HTTP 500" in rss["warnings"][0]
    assert report["warning_count"] == 3
    assert report["ok"] is False


def test_record_source_health_snapshot_keeps_latest_and_daily_history():
    state = {
        "source_health": {
            "history": {
                f"2026-05-{day:02d}": {"sources": []}
                for day in range(1, 33)
            }
        }
    }
    report = build_source_health_report(
        [
            {
                "name": "arXiv",
                "kind": "arxiv-api",
                "candidate_count": 148,
                "status": "ok",
            }
        ],
        generated_at="2026-06-21T23:50:00+08:00",
        current_year=2026,
    )

    record_source_health_snapshot(state, report, max_days=31)

    assert state["source_health"]["latest"]["sources"][0]["name"] == "arXiv"
    assert "2026-06-21" in state["source_health"]["history"]
    assert len(state["source_health"]["history"]) == 31


def test_publish_source_health_report_writes_html_json_and_rss(tmp_path):
    report = build_source_health_report(
        [
            {
                "name": "ICRA",
                "kind": "ieee-search",
                "candidate_count": 0,
                "status": "ok",
            }
        ],
        previous_records=[
            {
                "name": "ICRA",
                "kind": "ieee-search",
                "candidate_count": 3,
                "status": "ok",
            }
        ],
        generated_at="2026-06-21T23:50:00+08:00",
        current_year=2026,
    )

    record = publish_source_health_report(
        report,
        output_dir=tmp_path,
        public_base_url="https://example.com/summaries",
        generated_at="2026-06-21T23:50:00+08:00",
    )

    assert record["url"] == "https://example.com/summaries/reports/source-health/index.html"
    assert (tmp_path / "reports" / "source-health" / "index.html").exists()
    assert (tmp_path / "reports" / "source-health" / "index.json").exists()
    assert (tmp_path / "reports" / "source-health.xml").exists()

    data = json.loads((tmp_path / "reports" / "source-health" / "index.json").read_text())
    assert data["warning_count"] == 1
    assert data["sources"][0]["warning_codes"] == ["zero_after_nonzero"]

    html = (tmp_path / "reports" / "source-health" / "index.html").read_text(encoding="utf-8")
    assert "源健康检查" in html
    assert "ICRA" in html
    assert "上一轮 3 篇，这一轮 0 篇" in html

    root = ElementTree.parse(tmp_path / "reports" / "source-health.xml").getroot()
    assert root.findtext("channel/title") == "Oh My RSS Source Health Radar"
    assert root.findtext("channel/item/link") == "https://example.com/summaries/reports/source-health/index.html"
    assert "查看网页" in (root.findtext("channel/item/description") or "")
