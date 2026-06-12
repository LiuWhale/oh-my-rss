from oh_my_rss.cli import main
from oh_my_rss.scheduling import build_cron_line


def test_build_cron_line_quotes_paths_and_uses_flock():
    line = build_cron_line(
        cwd="/opt/Oh My RSS",
        config="config files/config.yaml",
        limit=2,
        interval_minutes=15,
        log_path="state dir/cron.log",
        lock_path="/tmp/oh-my-rss.lock",
        venv_path="/opt/Oh My RSS/.venv",
    )

    assert line == (
        "*/15 * * * * cd '/opt/Oh My RSS' && "
        ". '/opt/Oh My RSS/.venv/bin/activate' && "
        "flock -n /tmp/oh-my-rss.lock oh-my-rss run --config "
        "'config files/config.yaml' --limit 2 >> 'state dir/cron.log' 2>&1"
    )


def test_build_cron_line_can_skip_virtualenv_activation():
    line = build_cron_line(
        cwd="/opt/oh-my-rss",
        config="config.yaml",
        limit=1,
        interval_minutes=1,
        log_path="state/cron.log",
        lock_path="/tmp/oh-my-rss.lock",
        venv_path=None,
    )

    assert line == (
        "* * * * * cd /opt/oh-my-rss && "
        "flock -n /tmp/oh-my-rss.lock oh-my-rss run --config config.yaml "
        "--limit 1 >> state/cron.log 2>&1"
    )


def test_print_cron_cli_outputs_safe_cron_line(capsys):
    exit_code = main(
        [
            "print-cron",
            "--cwd",
            "/opt/oh-my-rss",
            "--config",
            "config.yaml",
            "--limit",
            "3",
            "--interval-minutes",
            "5",
            "--log-path",
            "state/cron.log",
            "--lock-path",
            "/tmp/oh-my-rss.lock",
            "--venv",
            ".venv",
        ]
    )

    assert exit_code == 0
    assert capsys.readouterr().out == (
        "*/5 * * * * cd /opt/oh-my-rss && . .venv/bin/activate && "
        "flock -n /tmp/oh-my-rss.lock oh-my-rss run --config config.yaml "
        "--limit 3 >> state/cron.log 2>&1\n"
    )
