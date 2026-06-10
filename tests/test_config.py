from pathlib import Path

from freshrss_arxiv_summarizer.config import AppConfig


def test_config_loads_yaml_and_expands_paths(tmp_path: Path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
freshrss:
  db_path: /data/users/example/db.sqlite
  category: Papers
site:
  public_base_url: https://example.com/summaries
  output_dir: ./site
codex:
  command: [codex, -a, never, -s, read-only, exec]
""",
        encoding="utf-8",
    )

    config = AppConfig.from_yaml(config_path)

    assert config.freshrss.category == "Papers"
    assert config.site.output_dir == tmp_path / "site"
    assert config.codex.command[:2] == ["codex", "-a"]
