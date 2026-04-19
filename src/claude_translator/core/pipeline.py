"""Helpers for running the discover -> translate -> inject sync pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from claude_translator.core.injector import inject_translation
from claude_translator.core.models import Inventory, Record
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


def _build_allowed_paths(inventory: Inventory) -> frozenset[Path]:
    return frozenset(Path(record.source_path).resolve() for record in inventory.records)


def _should_cjk_skip(record: Record, expected_script: str | None, chain: TranslationChain) -> bool:
    return bool(
        expected_script
        and record.current_description
        and detect_script(record.current_description) == expected_script
        and not chain.has_override(record.canonical_id)
    )


def run_sync(
    inventory: Inventory,
    chain: TranslationChain,
    target_lang: str,
    dry_run: bool = False,
) -> SyncReport:
    """Run translation and injection for all discovered records."""
    report = SyncReport()
    expected_script = script_tag_for_lang(target_lang)
    allowed_paths = _build_allowed_paths(inventory)

    for record in inventory.records:
        if _should_cjk_skip(record, expected_script, chain):
            report = report.bump("skip")
            continue

        translated = chain.translate(record)

        if translated.status == "empty":
            report = report.bump("empty")
            continue

        if translated.status == "original":
            report = report.bump("failed")
            continue

        if translated.matched_translation == record.current_description:
            report = report.bump("skip")
            continue

        if not dry_run:
            inject_translation(translated, allowed_paths=allowed_paths)

        report = report.bump(translated.status)

    return report


async def run_async(
    inventory: Inventory,
    chain: TranslationChain,
    target_lang: str,
    *,
    concurrency: int = 5,
    dry_run: bool = False,
    progress: Any | None = None,
    progress_task_id: Any = None,
) -> SyncReport:
    import asyncio

    report = SyncReport()
    expected_script = script_tag_for_lang(target_lang)
    allowed_paths = _build_allowed_paths(inventory)
    semaphore = asyncio.Semaphore(max(1, concurrency))

    async def process_one(record: Record) -> tuple[str, Record | None]:
        if _should_cjk_skip(record, expected_script, chain):
            return "skip", None

        async with semaphore:
            translated = await chain.translate_async(record)

        if translated.status == "empty":
            return "empty", None

        if translated.status == "original":
            return "failed", None

        if translated.matched_translation == record.current_description:
            return "skip", None

        if not dry_run:
            await asyncio.to_thread(inject_translation, translated, allowed_paths=allowed_paths)

        return translated.status, translated

    tasks = [asyncio.create_task(process_one(record)) for record in inventory.records]

    for task in asyncio.as_completed(tasks):
        bucket, _ = await task
        report = report.bump(bucket)
        if progress is not None:
            progress.advance(progress_task_id, 1)

    return report
