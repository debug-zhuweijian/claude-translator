"""Script detection for CJK languages."""

from __future__ import annotations

import re

_KO_RE = re.compile(r"[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]")
_KANA_RE = re.compile(r"[\u3040-\u309f\u30a0-\u30ff]")
_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")


def detect_script(text: str) -> str:
    """Detect dominant CJK script. Returns: "ko", "ja", "zh", or "unknown"."""
    if _KO_RE.search(text):
        return "ko"
    if _KANA_RE.search(text):
        return "ja"
    if _CJK_RE.search(text):
        return "zh"
    return "unknown"
