"""LLM client protocol for translation backends."""

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    def translate(self, text: str, source_lang: str, target_lang: str) -> str: ...
