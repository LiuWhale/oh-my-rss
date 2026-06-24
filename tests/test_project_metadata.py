from pathlib import Path
import tomllib

import oh_my_rss


def test_github_actions_runs_lint_and_tests():
    workflow = Path(".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "ruff check ." in workflow
    assert "pytest -q" in workflow
    assert "python -m build" in workflow


def test_package_description_matches_generic_research_feed_scope():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    description = metadata["project"]["description"]
    assert "research feeds" in description
    assert "arXiv" not in description


def test_dev_dependencies_include_package_build_tool():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    dev_dependencies = metadata["project"]["optional-dependencies"]["dev"]
    assert any(item.startswith("build>=") for item in dev_dependencies)


def test_package_license_uses_spdx_string():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert metadata["project"]["license"] == "MIT"


def test_readme_references_existing_github_cover():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "assets/github-cover.png" in readme
    assert Path("assets/github-cover.png").is_file()


def test_readme_supports_english_and_simplified_chinese():
    english = Path("README.md").read_text(encoding="utf-8")
    chinese_path = Path("README.zh-CN.md")
    chinese = chinese_path.read_text(encoding="utf-8")

    assert chinese_path.is_file()
    assert "README.zh-CN.md" in english
    assert "README.md" in chinese
    assert "RSS 原生 AI 科研雷达" in chinese
    assert "快速开始" in chinese


def test_source_distribution_manifest_includes_cover_assets():
    manifest = Path("MANIFEST.in").read_text(encoding="utf-8")

    assert "graft assets" in manifest
    assert "README.zh-CN.md" in manifest
    assert "scripts/make-github-cover.py" in manifest


def test_runtime_version_matches_package_metadata():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert oh_my_rss.__version__ == metadata["project"]["version"]


def test_changelog_contains_current_package_version():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")

    assert f"## [{metadata['project']['version']}]" in changelog


def test_env_example_documents_compose_runtime_variables():
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "CONFIG_PATH=/app/config.yaml" in env_example
    assert "RUN_LIMIT=1" in env_example
    assert "RUN_SINCE_DAYS=7" in env_example
    assert "RUN_LOOKBACK=1000" in env_example


def test_docker_compose_uses_documented_config_path_variable():
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "${CONFIG_PATH:-/app/config.yaml}" in compose
    assert "CONFIG_PATH=/app/config.yaml" in Path(".env.example").read_text(encoding="utf-8")
    assert "env_file:" not in compose


def test_dockerignore_excludes_local_state_and_secret_files():
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8").splitlines()
    patterns = {line.strip() for line in dockerignore if line.strip() and not line.startswith("#")}

    for pattern in {
        ".git",
        ".venv",
        ".env",
        "config.yaml",
        "state",
        "site",
        "*.sqlite",
        "*.sqlite-*",
    }:
        assert pattern in patterns


def test_synology_installer_uses_cron_helper_instead_of_stale_raw_command():
    script = Path("scripts/install-synology.sh").read_text(encoding="utf-8")

    assert "oh-my-rss print-cron" in script
    assert "--interval-minutes 10" in script
    assert "flock -n" not in script
