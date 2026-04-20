"""LLM-generated translation cache — cache-{lang}.json."""

from __future__ import annotations

import json
import logging

from claude_translator.errors import FileSystemError
from claude_translator.storage._io import atomic_write_text
from claude_translator.storage.paths import ensure_translations_dir, get_cache_path

logger = logging.getLogger(__name__)

CACHE_SCHEMA_VERSION = 1


def load_cache(lang: str) -> dict[str, str]:
    path = get_cache_path(lang)
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if raw.get("_schema_version") != CACHE_SCHEMA_VERSION:
        logger.warning(
            "Cache schema mismatch (got %s, expected %s), rebuilding",
            raw.get("_schema_version"),
            CACHE_SCHEMA_VERSION,
        )
        return {}
    return {k: v for k, v in raw.items() if k != "_schema_version"}


def save_cache(lang: str, mapping: dict[str, str]) -> None:
    path = ensure_translations_dir() / f"cache-{lang}.json"
    try:
        data = {"_schema_version": CACHE_SCHEMA_VERSION, **mapping}
        atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    except OSError as e:
        raise FileSystemError(f"Cannot write to {path}: {e}") from e


def update_cache(lang: str, canonical_id: str, translation: str) -> None:
    cache = load_cache(lang)
    updated = {**cache, canonical_id: translation}
    save_cache(lang, updated)
