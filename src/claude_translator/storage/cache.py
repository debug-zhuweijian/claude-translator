"""LLM-generated translation cache — cache-{lang}.json."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from claude_translator.storage.paths import ensure_translations_dir, get_cache_path


def load_cache(lang: str) -> dict[str, str]:
    path = get_cache_path(lang)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_cache(lang: str, mapping: dict[str, str]) -> None:
    path = ensure_translations_dir() / f"cache-{lang}.json"
    _atomic_write_text(path, json.dumps(mapping, ensure_ascii=False, indent=2) + "\n")


def update_cache(lang: str, canonical_id: str, translation: str) -> None:
    cache = load_cache(lang)
    updated = {**cache, canonical_id: translation}
    save_cache(lang, updated)


def _atomic_write_text(path: Path, content: str) -> None:
    fd, temp_path = tempfile.mkstemp(dir=path.parent, prefix=f"{path.name}.", suffix=".tmp")
    try:
        with open(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        Path(temp_path).replace(path)
    finally:
        temp = Path(temp_path)
        if temp.exists():
            temp.unlink()
