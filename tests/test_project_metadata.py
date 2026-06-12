from pathlib import Path
import tomllib


def test_github_actions_runs_lint_and_tests():
    workflow = Path(".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "ruff check ." in workflow
    assert "pytest -q" in workflow


def test_package_description_matches_generic_research_feed_scope():
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    description = metadata["project"]["description"]
    assert "research feeds" in description
    assert "arXiv" not in description
