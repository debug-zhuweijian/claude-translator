"""Auto-discover Claude Code plugins and user-level skills/commands."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_translator.core.canonical import generate_canonical_id, name_from_filename
from claude_translator.core.frontmatter import FrontmatterParser
from claude_translator.core.models import Inventory, Record
from claude_translator.utils.paths import normalize_path

logger = logging.getLogger(__name__)

DIR_KIND_MAP: dict[str, str] = {
    "skills": "skill",
    "commands": "command",
    "agents": "agent",
    ".agents/skills": "skill",
    ".agents/commands": "command",
    ".opencode/commands": "command",
}


def discover_all(claude_dir: Path) -> Inventory:
    """Discover all translatable items from plugins and user-level directories."""
    records: list[Record] = []
    seen_ids: set[str] = set()

    for r in _discover_user_level(claude_dir):
        if r.canonical_id not in seen_ids:
            records.append(r)
            seen_ids.add(r.canonical_id)

    for r in _discover_plugins(claude_dir):
        if r.canonical_id not in seen_ids:
            records.append(r)
            seen_ids.add(r.canonical_id)

    return Inventory(tuple(records))


def _discover_user_level(claude_dir: Path) -> list[Record]:
    records: list[Record] = []
    parser = FrontmatterParser()

    for dir_name, kind in [("skills", "skill"), ("commands", "command")]:
        base = claude_dir / dir_name
        if not base.is_dir():
            continue
        for md_file in sorted(base.rglob("*.md")):
            relative = md_file.relative_to(base)
            parts = relative.parts
            if len(parts) > 2:
                continue
            if len(parts) == 2 and parts[1] != "SKILL.md":
                continue

            if len(parts) == 2 and parts[1] == "SKILL.md":
                name = parts[0]
            else:
                name = name_from_filename(parts[0])

            cid = generate_canonical_id(kind=kind, name=name, scope="user")
            content = md_file.read_text(encoding="utf-8")
            fm, _ = parser.parse(content)
            desc = parser.get_description(fm) or ""

            records.append(Record(
                canonical_id=cid, kind=kind, scope="user",
                source_path=str(md_file),
                relative_path=normalize_path(str(relative)),
                current_description=desc,
                frontmatter_present=bool(fm),
            ))

    return records


def _discover_plugins(claude_dir: Path) -> list[Record]:
    plugins_file = claude_dir / "installed_plugins.json"
    if not plugins_file.exists():
        logger.info("No installed_plugins.json found")
        return []

    try:
        data = json.loads(plugins_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to read installed_plugins.json: %s", e)
        return []

    if not isinstance(data, list):
        return []

    records: list[Record] = []
    parser = FrontmatterParser()

    for entry in data:
        path_str = entry.get("installation_path", "")
        if not path_str:
            continue
        plugin_dir = Path(path_str)
        if not plugin_dir.is_dir():
            continue

        plugin_key = _extract_plugin_key(plugin_dir)
        records.extend(_scan_plugin_dir(plugin_dir, plugin_key, parser))

    return records


def _extract_plugin_key(plugin_dir: Path) -> str:
    parts = plugin_dir.parts
    for i in range(len(parts) - 2, -1, -1):
        if parts[i] == "market" and i + 2 < len(parts):
            return parts[i + 1]
    return plugin_dir.parent.name


def _scan_plugin_dir(plugin_dir: Path, plugin_key: str, parser: FrontmatterParser) -> list[Record]:
    records: list[Record] = []

    for dir_name, kind in DIR_KIND_MAP.items():
        target_dir = plugin_dir / dir_name
        if not target_dir.is_dir():
            continue

        for md_file in sorted(target_dir.rglob("*.md")):
            relative = md_file.relative_to(target_dir)
            parts = relative.parts

            if len(parts) > 2:
                continue
            if len(parts) == 2 and parts[1] != "SKILL.md":
                continue

            if len(parts) == 2 and parts[1] == "SKILL.md":
                name = parts[0]
            else:
                name = name_from_filename(parts[0])

            cid = generate_canonical_id(kind=kind, name=name, scope="plugin", plugin_key=plugin_key)
            content = md_file.read_text(encoding="utf-8")
            fm, _ = parser.parse(content)
            desc = parser.get_description(fm) or ""

            records.append(Record(
                canonical_id=cid, kind=kind, scope="plugin",
                source_path=str(md_file),
                relative_path=normalize_path(str(relative)),
                plugin_key=plugin_key,
                current_description=desc,
                frontmatter_present=bool(fm),
            ))

    return records
