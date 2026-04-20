"""Migrate legacy translation data to new per-language format."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_translator.storage._io import atomic_write_text

logger = logging.getLogger(__name__)


def migrate_legacy(translations_dir: Path, lang: str) -> None:
    """Auto-migrate legacy overrides file if new-format file doesn't exist.

    Only migrates descriptions-overrides.json → overrides-{lang}.json.
    Legacy cache (descriptions-zh-CN.json) is NOT migrated because its nested
    key format (section.name) cannot be mapped to canonical_id format
    (plugin.key.kind:name / user.kind:name).
    """
    new_path = translations_dir / f"overrides-{lang}.json"
    if new_path.exists():
        return

    legacy_path = translations_dir / "descriptions-overrides.json"
    if not legacy_path.exists():
        return

    try:
        data = json.loads(legacy_path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data:
            atomic_write_text(new_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
            logger.info("Migrated %d overrides from legacy to %s", len(data), new_path.name)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Skipping legacy overrides migration: %s", e)
