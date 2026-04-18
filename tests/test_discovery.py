import json
from pathlib import Path

from claude_translator.core.discovery import discover_all


def _write_plugins_json(claude_dir: Path, plugins: list[dict]) -> None:
    claude_dir.mkdir(parents=True, exist_ok=True)
    (claude_dir / "installed_plugins.json").write_text(json.dumps(plugins), encoding="utf-8")


def _write_plugins_v2_json(claude_dir: Path, plugins: dict) -> None:
    """Write v2 format: {"version": 2, "plugins": {...}} to plugins/installed_plugins.json."""
    plugins_dir = claude_dir / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    (plugins_dir / "installed_plugins.json").write_text(
        json.dumps({"version": 2, "plugins": plugins}), encoding="utf-8"
    )


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


def test_discover_multi_version_dedup(tmp_path: Path):
    """T17: Same plugin at 1.0.0 and 2.0.0 — only latest version discovered."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    v1 = tmp_path / "cache" / "market" / "my-plugin" / "1.0.0"
    v1_skills = v1 / "skills" / "old-skill"
    v1_skills.mkdir(parents=True)
    (v1_skills / "SKILL.md").write_text("---\ndescription: Old version\n---\n# Old\n")

    v2 = tmp_path / "cache" / "market" / "my-plugin" / "2.0.0"
    v2_skills = v2 / "skills" / "new-skill"
    v2_skills.mkdir(parents=True)
    (v2_skills / "SKILL.md").write_text("---\ndescription: New version\n---\n# New\n")

    _write_plugins_json(
        claude_dir,
        [
            {"installation_path": str(v1)},
            {"installation_path": str(v2)},
        ],
    )
    inv = discover_all(claude_dir)
    assert inv.size() == 1
    assert inv.records[0].canonical_id == "plugin.my-plugin.skill:new-skill"
    assert inv.records[0].current_description == "New version"


def test_discover_empty_env(tmp_path: Path):
    """T1: No .claude dir at all — should return empty inventory, no crash."""
    nonexistent = tmp_path / "no_such_dir"
    inv = discover_all(nonexistent)
    assert inv.size() == 0


def test_discover_v2_format(tmp_path: Path):
    """v2 format: plugins/installed_plugins.json with nested dict + installPath."""
    claude_dir = tmp_path / ".claude"
    plugin_dir = tmp_path / "cache" / "superpowers-marketplace" / "brainstorming" / "5.0.7"
    skills = plugin_dir / "skills" / "brainstorm"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text("---\ndescription: Brainstorm ideas\n---\n# Brainstorm\n")

    _write_plugins_v2_json(
        claude_dir,
        {
            "brainstorming@superpowers-marketplace": [
                {
                    "scope": "user",
                    "installPath": str(plugin_dir),
                    "version": "5.0.7",
                }
            ]
        },
    )
    inv = discover_all(claude_dir)
    assert inv.size() == 1
    assert inv.records[0].canonical_id == "plugin.brainstorming.skill:brainstorm"
    assert inv.records[0].current_description == "Brainstorm ideas"


def test_discover_prefers_plugins_subdir(tmp_path: Path):
    """Both locations exist — plugins/installed_plugins.json takes priority."""
    claude_dir = tmp_path / ".claude"

    # v1 format in root (empty list)
    _write_plugins_json(claude_dir, [])

    # v2 format in plugins/ (has real data)
    plugin_dir = tmp_path / "cache" / "market" / "my-plugin" / "1.0.0"
    skills = plugin_dir / "skills" / "test-skill"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text("---\ndescription: Test\n---\n# Test\n")

    _write_plugins_v2_json(
        claude_dir, {"my-plugin@market": [{"installPath": str(plugin_dir), "version": "1.0.0"}]}
    )
    inv = discover_all(claude_dir)
    assert inv.size() == 1
    assert inv.records[0].canonical_id == "plugin.my-plugin.skill:test-skill"
