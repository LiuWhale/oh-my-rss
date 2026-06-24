from datetime import datetime, timedelta, timezone

from oh_my_rss.state import expire_stale_running_records


def test_expire_stale_running_records_marks_only_old_running_records():
    state = {
        "papers": {
            "old": {
                "status": "running",
                "updated_at": "2026-06-23T00:00:00+08:00",
            },
            "fresh": {
                "status": "running",
                "updated_at": "2026-06-23T14:00:00+08:00",
            },
            "done": {
                "status": "done",
                "updated_at": "2026-06-20T00:00:00+08:00",
            },
        }
    }

    expired = expire_stale_running_records(
        state,
        now=datetime(2026, 6, 23, 7, 0, tzinfo=timezone.utc),
        max_age=timedelta(hours=6),
    )

    assert expired == 1
    assert state["papers"]["old"]["status"] == "error"
    assert "stale running record" in state["papers"]["old"]["error"]
    assert state["papers"]["old"]["stale_running_recovered_at"] == "2026-06-23T15:00:00+08:00"
    assert state["papers"]["fresh"]["status"] == "running"
    assert state["papers"]["done"]["status"] == "done"


def test_expire_stale_running_records_recovers_missing_timestamps():
    state = {"papers": {"unknown": {"status": "running"}}}

    expired = expire_stale_running_records(
        state,
        now=datetime(2026, 6, 23, 7, 0, tzinfo=timezone.utc),
    )

    assert expired == 1
    assert state["papers"]["unknown"]["status"] == "error"
    assert state["papers"]["unknown"]["updated_at"] == "2026-06-23T07:00:00+00:00"
