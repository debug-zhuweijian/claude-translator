"""Configuration loader with cascade: CLI > env > file > defaults."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from claude_translator.config.defaults import DEFAULT_TARGET_LANG
from claude_translator.config.models import LLMConfig, TranslatorConfig

logger = logging.getLogger(__name__)


def load_config(
    config_path: Path,
    target_lang: str | None = None,
) -> TranslatorConfig:
    """Load configuration with cascade resolution.

    Priority: CLI override > env var > config file > defaults.
    """
    # Start with defaults
    file_data: dict = {}

    # Layer 1: config file
    if config_path.exists():
        try:
            file_data = json.loads(config_path.read_text(encoding="utf-8"))
            logger.info("Loaded config from %s", config_path)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read config file %s: %s", config_path, e)

    # Layer 2: env overrides for LLM
    env_base_url = os.getenv("CLAUDE_TRANSLATE_LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
    env_api_key = os.getenv("CLAUDE_TRANSLATE_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    env_model = os.getenv("CLAUDE_TRANSLATE_LLM_MODEL") or os.getenv("OPENAI_MODEL")

    llm_data = dict(file_data.get("llm", {}))
    if env_base_url:
        llm_data["base_url"] = env_base_url
    if env_api_key:
        llm_data["api_key"] = env_api_key
    if env_model:
        llm_data["model"] = env_model

    # Layer 2b: env override for target_lang
    env_lang = os.getenv("CLAUDE_TRANSLATE_LANG")

    # Layer 3: CLI override for target_lang (highest priority)
    effective_lang = target_lang or env_lang or file_data.get("target_lang") or DEFAULT_TARGET_LANG

    return TranslatorConfig(
        target_lang=effective_lang,
        llm=LLMConfig(**llm_data) if llm_data else LLMConfig(),
    )
