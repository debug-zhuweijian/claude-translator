"""Strict target-language checks for visible descriptions."""

from __future__ import annotations

import re
from dataclasses import dataclass

from claude_translator.core.models import Inventory, Record
from claude_translator.lang.detect import detect_script

_ENGLISH_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
_ENGLISH_SENTENCE_RE = re.compile(
    r"(?:^|[。！？.!?]\s+|[一-鿿]\s*)"
    r"[A-Z][A-Za-z0-9,;:'()\-/ ]{12,}[.!?]"
)
_ALLOWED_TECH_TOKENS = frozenset(
    {
        "API",
        "CLI",
        "CSS",
        "CSV",
        "HTML",
        "HTTP",
        "HTTPS",
        "JSON",
        "LLM",
        "MCP",
        "PDF",
        "PR",
        "REST",
        "SDK",
        "SQL",
        "SVG",
        "TIFF",
        "UI",
        "URL",
        "UX",
        "XML",
        "YAML",
    }
)


@dataclass(frozen=True)
class LanguageViolation:
    canonical_id: str
    reason: str
    text_excerpt: str


def _excerpt(text: str) -> str:
    return text.strip().replace("\n", " ")[:120]


def _english_tokens(text: str) -> tuple[str, ...]:
    return tuple(match.group(0) for match in _ENGLISH_WORD_RE.finditer(text))


def _has_disallowed_english_tokens(text: str) -> bool:
    tokens = _english_tokens(text)
    return any(token.upper() not in _ALLOWED_TECH_TOKENS for token in tokens)


def check_description_language(record: Record, target_lang: str) -> tuple[LanguageViolation, ...]:
    text = record.current_description.strip()
    if not text:
        return (LanguageViolation(record.canonical_id, "empty", ""),)

    if not target_lang.startswith("zh"):
        return ()

    script = detect_script(text)
    if script != "zh":
        reason = "english_only" if _english_tokens(text) else "target_script_missing"
        return (LanguageViolation(record.canonical_id, reason, _excerpt(text)),)

    if _ENGLISH_SENTENCE_RE.search(text):
        return (LanguageViolation(record.canonical_id, "english_sentence_residue", _excerpt(text)),)

    return ()


def is_description_strict(record: Record, target_lang: str) -> bool:
    return not check_description_language(record, target_lang)


def check_inventory_language(
    inventory: Inventory, target_lang: str
) -> tuple[LanguageViolation, ...]:
    violations: tuple[LanguageViolation, ...] = ()
    for record in inventory.records:
        violations = (*violations, *check_description_language(record, target_lang))
    return violations
