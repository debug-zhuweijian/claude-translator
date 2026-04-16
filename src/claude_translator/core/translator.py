"""Translation chain with 4-level fallback."""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Callable

from claude_translator.clients.base import LLMClient
from claude_translator.core.models import Record

logger = logging.getLogger(__name__)


class TranslationChain:
    def __init__(
        self,
        overrides_loader: Callable[[str], dict[str, str]],
        cache_loader: Callable[[str], dict[str, str]],
        cache_updater: Callable[[str, str, str], None],
        client: LLMClient,
        target_lang: str,
    ) -> None:
        self._overrides_loader = overrides_loader
        self._cache_loader = cache_loader
        self._cache_updater = cache_updater
        self._client = client
        self._target_lang = target_lang

    # NOTE: translate() loads overrides and cache per item (N+1 pattern).
    # Measured cost: ~0.16s for 440 items — negligible vs LLM latency.
    # A batch-load optimization would add complexity without benefit at current scale.
    def translate(self, record: Record) -> Record:
        cid = record.canonical_id
        desc = record.current_description

        if not desc:
            return replace(record, matched_translation="", status="empty")

        overrides = self._overrides_loader(self._target_lang)
        if cid in overrides:
            return replace(record, matched_translation=overrides[cid], status="override")

        cache = self._cache_loader(self._target_lang)
        if cid in cache:
            return replace(record, matched_translation=cache[cid], status="cache")

        try:
            translation = self._client.translate(desc, "en", self._target_lang)
            self._cache_updater(self._target_lang, cid, translation)
            return replace(record, matched_translation=translation, status="llm")
        except Exception:
            logger.warning("LLM translation failed for %s, falling back to original", cid)

        return replace(record, matched_translation=desc, status="original")
