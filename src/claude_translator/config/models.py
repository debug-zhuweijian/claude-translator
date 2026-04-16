"""Pydantic configuration models."""

from __future__ import annotations

from pydantic import BaseModel

from claude_translator.config.defaults import (
    DEFAULT_LLM_API_KEY,
    DEFAULT_LLM_BASE_URL,
    DEFAULT_LLM_MODEL,
    DEFAULT_TARGET_LANG,
)


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    model: str = DEFAULT_LLM_MODEL
    base_url: str | None = DEFAULT_LLM_BASE_URL
    api_key: str | None = DEFAULT_LLM_API_KEY


class TranslatorConfig(BaseModel):
    """Top-level translator configuration."""

    target_lang: str = DEFAULT_TARGET_LANG
    llm: LLMConfig = LLMConfig()
