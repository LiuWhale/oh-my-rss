from pathlib import Path
import tomllib

import oh_my_rss


def test_github_actions_runs_lint_and_tests():
    workflow = Path(".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "ruff check ." in workflow
    assert "pytest -q" in workflow


def test_package_description_matches_generic_research_feed_scope():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    description = metadata["project"]["description"]
    assert "research feeds" in description
    assert "arXiv" not in description


def test_runtime_version_matches_package_metadata():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert oh_my_rss.__version__ == metadata["project"]["version"]


def test_env_example_documents_compose_runtime_variables():
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "CONFIG_PATH=/app/config.yaml" in env_example
    assert "RUN_LIMIT=1" in env_example
    assert "RUN_SINCE_DAYS=7" in env_example
    assert "RUN_LOOKBACK=1000" in env_example


def test_synology_installer_uses_cron_helper_instead_of_stale_raw_command():
    script = Path("scripts/install-synology.sh").read_text(encoding="utf-8")

    assert "oh-my-rss print-cron" in script
    assert "--interval-minutes 10" in script
    assert "flock -n" not in script
