"""Fake LLM client for testing."""

from __future__ import annotations


class FakeClient:
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        return f"[{target_lang}] {text}"
