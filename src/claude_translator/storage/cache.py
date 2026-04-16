"""LLM-generated translation cache — cache-{lang}.json."""

from __future__ import annotations

import json

from claude_translator.storage.paths import get_cache_path


def load_cache(lang: str) -> dict[str, str]:
    path = get_cache_path(lang)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(lang: str, mapping: dict[str, str]) -> None:
    path = get_cache_path(lang)
    path.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def update_cache(lang: str, canonical_id: str, translation: str) -> None:
    cache = load_cache(lang)
    updated = {**cache, canonical_id: translation}
    save_cache(lang, updated)
