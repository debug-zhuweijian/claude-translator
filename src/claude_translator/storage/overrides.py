"""User manual overrides storage — overrides-{lang}.json."""

from __future__ import annotations

import json

from claude_translator.storage.cache import _atomic_write_text
from claude_translator.storage.paths import ensure_translations_dir, get_overrides_path


def load_overrides(lang: str) -> dict[str, str]:
    path = get_overrides_path(lang)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_overrides(lang: str, mapping: dict[str, str]) -> None:
    path = ensure_translations_dir() / f"overrides-{lang}.json"
    _atomic_write_text(path, json.dumps(mapping, ensure_ascii=False, indent=2) + "\n")
