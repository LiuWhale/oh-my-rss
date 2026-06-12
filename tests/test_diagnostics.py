import json
import sys

from oh_my_rss.cli import main
from oh_my_rss.diagnostics import run_doctor


def write_config(tmp_path, *, db_path, command=None):
    command = command or [sys.executable, "--version"]
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        f"""
freshrss:
  db_path: {db_path}
  category: 论文
site:
  public_base_url: https://example.com/summaries
  output_dir: site
codex:
  command: {command}
runtime:
  state_dir: state
  curl_bin: {sys.executable}
  pdftotext_bin: {sys.executable}
""",
        encoding="utf-8",
    )
    return config_path


def checks_by_name(result):
    return {item["name"]: item for item in result["checks"]}


def test_run_doctor_accepts_valid_local_config(tmp_path):
    db_path = tmp_path / "db.sqlite"
    db_path.write_text("", encoding="utf-8")
    config_path = write_config(tmp_path, db_path=db_path)

    result = run_doctor(config_path)
    checks = checks_by_name(result)

    assert result["ok"] is True
    assert checks["config"]["ok"] is True
    assert checks["freshrss_db"]["ok"] is True
    assert checks["site_output_parent"]["ok"] is True
    assert checks["curl"]["ok"] is True
    assert checks["pdftotext"]["ok"] is True
    assert checks["codex_command"]["ok"] is True


def test_run_doctor_reports_missing_database_and_command(tmp_path):
    missing_db = tmp_path / "missing.sqlite"
    config_path = write_config(tmp_path, db_path=missing_db, command=["missing-oh-my-rss-command"])

    result = run_doctor(config_path)
    checks = checks_by_name(result)

    assert result["ok"] is False
    assert checks["freshrss_db"]["ok"] is False
    assert checks["codex_command"]["ok"] is False
    assert "missing.sqlite" in checks["freshrss_db"]["message"]
    assert "missing-oh-my-rss-command" in checks["codex_command"]["message"]


def test_doctor_cli_returns_nonzero_for_failed_checks(tmp_path, capsys):
    config_path = write_config(tmp_path, db_path=tmp_path / "missing.sqlite")

    exit_code = main(["doctor", "--config", str(config_path)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["ok"] is False
    assert checks_by_name(output)["freshrss_db"]["ok"] is False
