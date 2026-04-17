"""Immutable data models for claude-translator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Status = Literal["override", "cache", "llm", "original", "empty", ""]


@dataclass(frozen=True)
class Record:
    """A single translatable item discovered from the plugin ecosystem."""

    canonical_id: str
    kind: str
    scope: str
    source_path: str
    relative_path: str
    plugin_key: str = ""
    current_description: str = ""
    status: Status = ""
    matched_translation: str = ""
    frontmatter_present: bool = True


@dataclass(frozen=True)
class Inventory:
    """Immutable collection of discovered Records."""

    records: tuple[Record, ...]

    def find_by_canonical_id(self, cid: str) -> Record | None:
        for r in self.records:
            if r.canonical_id == cid:
                return r
        return None

    def size(self) -> int:
        return len(self.records)


@dataclass(frozen=True)
class TranslationMapping:
    """A single translation result with metadata."""

    canonical_id: str
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str
