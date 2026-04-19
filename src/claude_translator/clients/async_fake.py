"""Fake async translation client for testing."""

from __future__ import annotations


class AsyncFakeClient:
    """Returns deterministic translations: ``[{lang}] {text}``."""

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        return f"[{target_lang}] {text}"
