import json
from pathlib import Path

from claude_translator.core.discovery import discover_all


def _write_plugins_json(claude_dir: Path, plugins: list[dict]) -> None:
    claude_dir.mkdir(parents=True, exist_ok=True)
    (claude_dir / "installed_plugins.json").write_text(json.dumps(plugins), encoding="utf-8")


def test_discover_standard_structure(tmp_path: Path):
    claude_dir = tmp_path / ".claude"
    plugin_dir = tmp_path / "cache" / "market" / "my-plugin" / "1.0.0"
    skills = plugin_dir / "skills" / "brainstorm"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text("---\ndescription: Brainstorm ideas\n---\n# Brainstorm\n")
    commands = plugin_dir / "commands"
    commands.mkdir()
    (commands / "commit.md").write_text("---\ndescription: Create commit\n---\n# Commit\n")

    _write_plugins_json(claude_dir, [{"installation_path": str(plugin_dir)}])
    inv = discover_all(claude_dir)
    assert inv.size() == 2
    ids = {r.canonical_id for r in inv.records}
    assert "plugin.my-plugin.skill:brainstorm" in ids
    assert "plugin.my-plugin.command:commit" in ids


def test_discover_skips_nonstandard_dirs(tmp_path: Path):
    claude_dir = tmp_path / ".claude"
    plugin_dir = tmp_path / "cache" / "market" / "my-plugin" / "1.0.0"
    weird = plugin_dir / "random_stuff"
    weird.mkdir(parents=True)
    (weird / "file.md").write_text("# Random")
    skills = plugin_dir / "skills" / "real"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text("---\ndescription: Real\n---\n# Real\n")

    _write_plugins_json(claude_dir, [{"installation_path": str(plugin_dir)}])
    inv = discover_all(claude_dir)
    assert inv.size() == 1
    assert inv.records[0].canonical_id == "plugin.my-plugin.skill:real"


def test_discover_top_level_only(tmp_path: Path):
    claude_dir = tmp_path / ".claude"
    plugin_dir = tmp_path / "cache" / "market" / "my-plugin" / "1.0.0"
    skill = plugin_dir / "skills" / "brainstorm"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\ndescription: Main\n---\n# Main\n")
    ref = skill / "reference"
    ref.mkdir()
    (ref / "detail.md").write_text("---\ndescription: Detail\n---\n# Detail\n")

    _write_plugins_json(claude_dir, [{"installation_path": str(plugin_dir)}])
    inv = discover_all(claude_dir)
    assert inv.size() == 1
    assert inv.records[0].canonical_id == "plugin.my-plugin.skill:brainstorm"


def test_discover_no_plugins_json(tmp_path: Path):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True)
    inv = discover_all(claude_dir)
    assert inv.size() == 0


def test_discover_user_scope(tmp_path: Path):
    claude_dir = tmp_path / ".claude"
    user_skills = claude_dir / "skills" / "my-skill"
    user_skills.mkdir(parents=True)
    (user_skills / "SKILL.md").write_text("---\ndescription: My custom skill\n---\n# My Skill\n")
    user_commands = claude_dir / "commands"
    user_commands.mkdir()
    (user_commands / "review.md").write_text("---\ndescription: Review code\n---\n# Review\n")

    inv = discover_all(claude_dir)
    ids = {r.canonical_id for r in inv.records}
    assert "user.skill:my-skill" in ids
    assert "user.command:review" in ids
