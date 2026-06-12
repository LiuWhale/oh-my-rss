from oh_my_rss.cli import main


def test_run_dry_run_does_not_require_pdf_tools(monkeypatch, tmp_path, capsys):
    from oh_my_rss import app, cli, config

    class FakeConfig:
        pass

    def fake_run_once(config_obj, **kwargs):
        assert isinstance(config_obj, FakeConfig)
        assert kwargs["dry_run"] is True
        return [{"title": "Preview paper"}]

    monkeypatch.setattr(cli.shutil, "which", lambda name: None)
    monkeypatch.setattr(config.AppConfig, "from_yaml", classmethod(lambda cls, path: FakeConfig()))
    monkeypatch.setattr(app, "run_once", fake_run_once)

    exit_code = main(["run", "--config", str(tmp_path / "config.yaml"), "--dry-run"])

    assert exit_code == 0
    assert "Preview paper" in capsys.readouterr().out
