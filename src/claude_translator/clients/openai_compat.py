"""OpenAI-compatible LLM client for translation."""

from __future__ import annotations

import logging
import os

from claude_translator.lang.cleaner import clean_llm_response
from claude_translator.lang.prompts import get_prompt, wrap_user_content

logger = logging.getLogger(__name__)


class OpenAICompatClient:
    def __init__(self, model: str, base_url: str | None = None, api_key: str | None = None) -> None:
        from openai import OpenAI

        resolved_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not resolved_key:
            raise ValueError(
                "OpenAI API key is required. "
                "Set OPENAI_API_KEY env var or pass api_key in config."
            )

        self._model = model
        self._client = OpenAI(
            base_url=base_url or os.getenv("OPENAI_BASE_URL"),
            api_key=resolved_key,
            timeout=30.0,
            max_retries=2,
        )

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        prompt = get_prompt(source_lang, target_lang)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": wrap_user_content(text)},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        result = response.choices[0].message.content
        if result is None:
            raise RuntimeError("LLM returned empty response")
        return clean_llm_response(result)
