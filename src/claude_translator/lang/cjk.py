"""Unicode range checks for CJK scripts."""

from __future__ import annotations

import re

_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
_HIRAGANA_RE = re.compile(r"[\u3040-\u309f]")
_KATAKANA_RE = re.compile(r"[\u30a0-\u30ff]")
_HANGUL_RE = re.compile(r"[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]")


def has_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text))


def has_ja(text: str) -> bool:
    return bool(_HIRAGANA_RE.search(text) or _KATAKANA_RE.search(text))


def has_ko(text: str) -> bool:
    return bool(_HANGUL_RE.search(text))
