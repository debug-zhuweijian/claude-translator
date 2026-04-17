"""Helpers for running the discover -> translate -> inject sync pipeline."""

from __future__ import annotations

from claude_translator.core.injector import inject_translation
from claude_translator.core.models import Inventory
from claude_translator.core.report import SyncReport
from claude_translator.core.translator import TranslationChain
from claude_translator.lang.detect import detect_script


def script_tag_for_lang(lang: str) -> str | None:
    """Map configured target language to the detectable CJK script tag."""
    if lang.startswith("zh"):
        return "zh"
    if lang == "ja":
        return "ja"
    if lang == "ko":
        return "ko"
    return None


def run_sync(
    inventory: Inventory,
    chain: TranslationChain,
    target_lang: str,
    dry_run: bool = False,
) -> SyncReport:
    """Run translation and injection for all discovered records."""
    report = SyncReport()
    expected_script = script_tag_for_lang(target_lang)

    for record in inventory.records:
        if (
            expected_script
            and record.current_description
            and detect_script(record.current_description) == expected_script
            and not chain.has_override(record.canonical_id)
        ):
            report = report.bump("skip")
            continue

        translated = chain.translate(record)

        if translated.status == "empty":
            report = report.bump("skip")
            continue

        if translated.status == "original":
            report = report.bump("failed")
            continue

        if not translated.matched_translation or (
            translated.matched_translation == record.current_description
        ):
            report = report.bump("skip")
            continue

        if not dry_run:
            inject_translation(translated)

        report = report.bump(translated.status)

    return report
