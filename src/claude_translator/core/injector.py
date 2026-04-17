"""Frontmatter injection and update for translated descriptions."""

from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path

from claude_translator.core.frontmatter import FrontmatterParser
from claude_translator.core.models import Record
from claude_translator.utils.paths import detect_newline

logger = logging.getLogger(__name__)


def inject_translation(record: Record) -> Record:
    if not record.matched_translation:
        return record

    file_path = Path(record.source_path)
    if not file_path.exists():
        logger.warning("File not found: %s", file_path)
        return record

    raw_bytes = file_path.read_bytes()
    has_bom = raw_bytes.startswith(b"\xef\xbb\xbf")
    content = raw_bytes.decode("utf-8-sig" if has_bom else "utf-8")
    newline = detect_newline(content)
    parser = FrontmatterParser()

    fm, body = parser.parse(content)
    parser.set_description(fm, record.matched_translation)
    new_content = parser.build(fm, body)

    new_content = new_content.replace("\r\n", "\n").replace("\n", newline)
    out_bytes = new_content.encode("utf-8")
    if has_bom:
        out_bytes = b"\xef\xbb\xbf" + out_bytes
    file_path.write_bytes(out_bytes)

    return replace(record, frontmatter_present=True)
