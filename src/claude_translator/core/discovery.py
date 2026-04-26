"""Auto-discover Claude Code plugins and user-level skills, commands, and agents."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from packaging.version import InvalidVersion, Version

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

    for dir_name, kind in [("skills", "skill"), ("commands", "command"), ("agents", "agent")]:
        base = claude_dir / dir_name
        if not base.is_dir():
            continue
        records.extend(_scan_root(base, kind=kind, scope="user", plugin_key="", parser=parser))

    return records


def _discover_plugins(claude_dir: Path) -> list[Record]:
    # Try both known locations for the plugin registry
    candidates = [
        claude_dir / "plugins" / "installed_plugins.json",  # Claude Code v2+
        claude_dir / "installed_plugins.json",  # legacy / custom
    ]
    plugins_file: Path | None = None
    for c in candidates:
        if c.exists():
            plugins_file = c
            break

    if plugins_file is None:
        logger.info("No installed_plugins.json found")
        return []

    try:
        data = json.loads(plugins_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to read installed_plugins.json: %s", e)
        return []

    # Support both formats:
    #   v2: {"version": 2, "plugins": {"key@market": [{installPath: "..."}]}}
    #   v1: [{installation_path: "..."}, ...]
    entries: list[dict] = []
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict) and "plugins" in data:
        for registry_key, install_list in data["plugins"].items():
            if isinstance(install_list, list):
                for entry in install_list:
                    merged = dict(entry)
                    merged["_registry_plugin_key"] = _plugin_key_from_registry_key(registry_key)
                    entries.append(merged)

    if not entries:
        return []

    # Deduplicate: keep only latest version per plugin_key
    latest: dict[str, tuple[dict, Path]] = {}
    for entry in entries:
        # Support both "installPath" (v2) and "installation_path" (v1)
        path_str = entry.get("installPath") or entry.get("installation_path", "")
        if not path_str:
            continue
        plugin_dir = Path(path_str)
        if not plugin_dir.is_dir():
            continue
        plugin_key = str(entry.get("_registry_plugin_key") or _extract_plugin_key(plugin_dir))
        existing = latest.get(plugin_key)
        if existing is None or _extract_version(plugin_dir) > _extract_version(existing[1]):
            latest[plugin_key] = (entry, plugin_dir)

    records: list[Record] = []
    parser = FrontmatterParser()
    for plugin_key, (_, plugin_dir) in latest.items():
        records.extend(_scan_plugin_dir(plugin_dir, plugin_key, parser))

    return records


def _extract_version(path: Path) -> Version:
    """Extract version number from plugin path (e.g., .../1.0.0 → Version('1.0.0'))."""
    try:
        return Version(path.name)
    except InvalidVersion:
        return Version("0")


def _plugin_key_from_registry_key(registry_key: str) -> str:
    return registry_key.split("@", 1)[0]


def _extract_plugin_key(plugin_dir: Path) -> str:
    return plugin_dir.parent.name


def _scan_plugin_dir(plugin_dir: Path, plugin_key: str, parser: FrontmatterParser) -> list[Record]:
    records: list[Record] = []

    for dir_name, kind in DIR_KIND_MAP.items():
        target_dir = plugin_dir / dir_name
        if not target_dir.is_dir():
            continue
        records.extend(
            _scan_root(target_dir, kind=kind, scope="plugin", plugin_key=plugin_key, parser=parser)
        )

    return records


def _scan_root(
    root: Path,
    *,
    kind: str,
    scope: str,
    plugin_key: str,
    parser: FrontmatterParser,
) -> list[Record]:
    records: list[Record] = []

    for md_file in sorted(root.rglob("*.md")):
        relative = md_file.relative_to(root)
        name = _name_from_entrypoint(relative, kind)
        if name is None:
            continue

        cid = generate_canonical_id(kind=kind, name=name, scope=scope, plugin_key=plugin_key)
        content = md_file.read_text(encoding="utf-8")
        fm, _ = parser.parse(content)
        desc = parser.get_description(fm) or ""

        records.append(
            Record(
                canonical_id=cid,
                kind=kind,
                scope=scope,
                source_path=str(md_file),
                relative_path=normalize_path(str(relative)),
                plugin_key=plugin_key,
                current_description=desc,
                frontmatter_present=bool(fm),
            )
        )

    return records


def _name_from_entrypoint(relative: Path, kind: str) -> str | None:
    parts = relative.parts
    if not parts:
        return None

    if kind == "skill":
        if len(parts) == 1:
            return name_from_filename(parts[0])
        if parts[-1] == "SKILL.md":
            return ":".join(parts[:-1])
        return None

    if kind in {"command", "agent"}:
        return ":".join((*parts[:-1], name_from_filename(parts[-1])))

    return None
