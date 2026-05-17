"""Shared test fixtures for claude-translator tests."""

from pathlib import Path

import pytest


def pytest_addoption(parser):
    """Allow asyncio_mode config even when pytest-asyncio is unavailable locally."""
    parser.addini("asyncio_mode", "Async test mode", default="auto")


@pytest.fixture
def tmp_claude_dir(tmp_path: Path) -> Path:
    """Create a temporary .claude directory structure."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    translations_dir = claude_dir / "translations"
    translations_dir.mkdir()
    return claude_dir


@pytest.fixture
def sample_plugin_dir(tmp_path: Path) -> Path:
    """Create a sample plugin directory with standard structure."""
    plugin_dir = tmp_path / "plugins" / "cache" / "market" / "my-plugin" / "1.0.0"
    skills_dir = plugin_dir / "skills" / "brainstorm"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("---\ndescription: Brainstorm ideas\n---\n# Brainstorm\n")
    commands_dir = plugin_dir / "commands"
    commands_dir.mkdir()
    (commands_dir / "commit.md").write_text("---\ndescription: Create a commit\n---\n# Commit\n")
    return plugin_dir


@pytest.fixture
def sample_record() -> dict:
    """Sample record kwargs for testing."""
    return {
        "canonical_id": "plugin.my-plugin.skill:brainstorm",
        "kind": "skill",
        "scope": "plugin",
        "source_path": "/plugins/cache/market/my-plugin/1.0.0/skills/brainstorm/SKILL.md",
        "relative_path": "skills/brainstorm/SKILL.md",
        "plugin_key": "my-plugin",
        "current_description": "Brainstorm ideas",
    }
