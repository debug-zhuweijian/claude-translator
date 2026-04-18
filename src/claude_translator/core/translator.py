"""Translation chain with 4-level fallback."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace

from claude_translator.clients.base import LLMClient
from claude_translator.core.models import Record

logger = logging.getLogger(__name__)


class TranslationChain:
    def __init__(
        self,
        overrides: dict[str, str],
        cache: dict[str, str],
        on_cache_update: Callable[[str, str, str], None],
        *,
        client: LLMClient | None = None,
        client_factory: Callable[[], LLMClient] | None = None,
        target_lang: str,
    ) -> None:
        self._overrides = overrides
        self._cache = cache
        self._on_cache_update = on_cache_update
        self._client = client
        self._client_factory = client_factory
        self._target_lang = target_lang
        self._failures: list[tuple[Record, Exception]] = []
        if self._client is None and self._client_factory is None:
            raise ValueError("TranslationChain requires client or client_factory")

    @property
    def failures(self) -> list[tuple[Record, Exception]]:
        return list(self._failures)

    def has_override(self, canonical_id: str) -> bool:
        return canonical_id in self._overrides

    def _get_client(self) -> LLMClient:
        if self._client is not None:
            return self._client
        if self._client_factory is None:
            raise RuntimeError("LLM client factory is not configured")
        self._client = self._client_factory()
        return self._client

    def translate(self, record: Record) -> Record:
        cid = record.canonical_id
        desc = record.current_description

        if not desc:
            return replace(record, matched_translation="", status="empty")

        if cid in self._overrides:
            return replace(record, matched_translation=self._overrides[cid], status="override")

        if cid in self._cache:
            return replace(record, matched_translation=self._cache[cid], status="cache")

        try:
            translation = self._get_client().translate(desc, "en", self._target_lang)
            self._cache[cid] = translation
            self._on_cache_update(self._target_lang, cid, translation)
            return replace(record, matched_translation=translation, status="llm")
        except Exception as exc:
            logger.warning("LLM translation failed for %s, falling back to original: %s", cid, exc)
            self._failures.append((record, exc))

        return replace(record, matched_translation=desc, status="original")
