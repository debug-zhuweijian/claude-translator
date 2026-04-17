"""Clean and validate LLM translation responses before frontmatter injection."""

from __future__ import annotations

import re

from claude_translator.errors import TranslatorError

_PAIRED_QUOTES = [
    ('"', '"'),
    ("'", "'"),
    ("\u300c", "\u300d"),
    ("\u300e", "\u300f"),
]

_PREFIX_RE = re.compile(
    r"^(?:(?:translation|translated text|here is the translation|翻译|译文)[：:\s-]*)+",
    re.IGNORECASE,
)


class TranslationCleaner:
    """Normalize common LLM response wrappers and reject dangerous output."""

    def clean(self, text: str) -> str:
        result = text.strip()

        for _ in range(2):
            result = self._strip_paired_quotes(result)

        result = _PREFIX_RE.sub("", result).strip()

        if not result:
            raise TranslatorError("LLM returned an empty translation")
        if "\n" in result or "\r" in result:
            raise TranslatorError("LLM returned a multi-line translation")
        if "---" in result:
            raise TranslatorError("LLM returned content that would break frontmatter")

        return result

    @staticmethod
    def _strip_paired_quotes(text: str) -> str:
        for open_quote, close_quote in _PAIRED_QUOTES:
            if len(text) >= 2 and text.startswith(open_quote) and text.endswith(close_quote):
                return text[len(open_quote) : -len(close_quote)].strip()
        return text


clean_llm_response = TranslationCleaner().clean
