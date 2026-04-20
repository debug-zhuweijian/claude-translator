"""Script detection for CJK languages."""

from __future__ import annotations

import re
from typing import Literal

_KO_RE = re.compile(r"[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]")
_KANA_RE = re.compile(r"[\u3040-\u309f\u30a0-\u30ff]")
_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")


def has_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text))


def has_ja(text: str) -> bool:
    return bool(_KANA_RE.search(text))


def has_ko(text: str) -> bool:
    return bool(_KO_RE.search(text))


def detect_script(text: str) -> Literal["ko", "ja", "zh", "unknown"]:
    """Detect dominant CJK script. Returns: "ko", "ja", "zh", or "unknown"."""
    if has_ko(text):
        return "ko"
    if has_ja(text):
        return "ja"
    if has_cjk(text):
        return "zh"
    return "unknown"
