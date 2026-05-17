"""Performance benchmarks (T13)."""

import json
import time
from pathlib import Path

from claude_translator.core.discovery import discover_all


def test_scan_50_plugins_under_5s(tmp_path: Path):
    """T13: 50 plugins with 3 skills each should scan in under 5 seconds."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True)

    plugins = []
    for i in range(50):
        plugin_dir = tmp_path / "cache" / "market" / f"plugin-{i}" / "1.0.0"
        for skill_name in ["skill-a", "skill-b", "skill-c"]:
            skill_dir = plugin_dir / "skills" / skill_name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                f"---\ndescription: Plugin {i} {skill_name}\n---\n# Skill\n",
                encoding="utf-8",
            )
        plugins.append({"installation_path": str(plugin_dir)})

    (claude_dir / "installed_plugins.json").write_text(json.dumps(plugins), encoding="utf-8")

    start = time.monotonic()
    inv = discover_all(claude_dir)
    elapsed = time.monotonic() - start

    assert inv.size() == 150  # 50 plugins × 3 skills
    assert elapsed < 5.0, f"Scan took {elapsed:.2f}s, expected < 5s"
