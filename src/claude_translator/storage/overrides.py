"""User manual overrides storage — overrides-{lang}.json."""

from __future__ import annotations

import json

from claude_translator.storage.paths import get_overrides_path


def load_overrides(lang: str) -> dict[str, str]:
    path = get_overrides_path(lang)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_overrides(lang: str, mapping: dict[str, str]) -> None:
    path = get_overrides_path(lang)
    path.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
