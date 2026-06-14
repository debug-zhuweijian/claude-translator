"""Strict target-language checks for visible descriptions."""

from __future__ import annotations

import re
from dataclasses import dataclass

from claude_translator.core.models import Inventory, Record
from claude_translator.core.patterns import SLASH_COMMAND_RE
from claude_translator.lang.detect import detect_script

_ENGLISH_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
_ENGLISH_SENTENCE_RE = re.compile(
    r"(?:^|[。！？.!?]\s+|[一-鿿]\s*)"
    r"[A-Z][A-Za-z0-9,;:'()\-/ ]{12,}[.!?]"
)
_CJK_CHAR_RE = re.compile(r"[一-鿿㐀-䶿]")
_BRACKET_OPTIONS_RE = re.compile(r"\[[A-Za-z0-9|:_\-<> /]+\]")
_PAREN_STRUCTURAL_LIST_RE = re.compile(r"[（(][^）)]*[A-Za-z][^）)]*[，,、/|][^）)]*[）)]")
_QUOTED_TRIGGER_RE = re.compile(r"['\"][^'\"]*[A-Za-z][^'\"]*['\"]")
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


def _strip_structural_tokens(text: str) -> str:
    result = SLASH_COMMAND_RE.sub(" ", text)
    result = _BRACKET_OPTIONS_RE.sub(" ", result)
    result = _PAREN_STRUCTURAL_LIST_RE.sub(" ", result)
    result = _QUOTED_TRIGGER_RE.sub(" ", result)
    return result


def _has_english_text_residue(text: str) -> bool:
    prose_text = _strip_structural_tokens(text)
    if not _has_disallowed_english_tokens(prose_text):
        return False
    prose_tokens = tuple(
        token
        for token in _english_tokens(prose_text)
        if token.islower() and len(token) >= 3 and token.upper() not in _ALLOWED_TECH_TOKENS
    )
    prose_chars = sum(len(token) for token in prose_tokens)
    cjk_chars = len(_CJK_CHAR_RE.findall(prose_text))
    return len(prose_tokens) >= 4 and prose_chars >= max(32, cjk_chars * 2)


def _script_tag_for_lang(target_lang: str) -> str | None:
    if target_lang.startswith("zh"):
        return "zh"
    if target_lang.startswith("ja"):
        return "ja"
    if target_lang.startswith("ko"):
        return "ko"
    return None


def check_description_language(record: Record, target_lang: str) -> tuple[LanguageViolation, ...]:
    text = record.current_description.strip()
    if not text:
        return (LanguageViolation(record.canonical_id, "empty", ""),)

    expected_script = _script_tag_for_lang(target_lang)
    if expected_script is None:
        return ()

    script = detect_script(text)
    if script != expected_script:
        reason = "english_only" if _english_tokens(text) else "target_script_missing"
        return (LanguageViolation(record.canonical_id, reason, _excerpt(text)),)

    if _ENGLISH_SENTENCE_RE.search(text):
        return (LanguageViolation(record.canonical_id, "english_sentence_residue", _excerpt(text)),)

    if _has_english_text_residue(text):
        return (LanguageViolation(record.canonical_id, "english_text_residue", _excerpt(text)),)

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
