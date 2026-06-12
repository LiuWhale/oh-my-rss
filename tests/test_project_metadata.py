from pathlib import Path


def test_github_actions_runs_lint_and_tests():
    workflow = Path(".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "ruff check ." in workflow
    assert "pytest -q" in workflow
