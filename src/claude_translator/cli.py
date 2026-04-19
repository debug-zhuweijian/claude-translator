"""CLI entry point with Click subcommands."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

from claude_translator import __version__
from claude_translator.clients.async_openai import AsyncOpenAICompatClient
from claude_translator.clients.openai_compat import OpenAICompatClient
from claude_translator.config.loaders import load_config
from claude_translator.core.discovery import discover_all
from claude_translator.core.frontmatter import FrontmatterParser
from claude_translator.core.migration import migrate_legacy
from claude_translator.core.pipeline import run_async, run_sync, script_tag_for_lang
from claude_translator.core.translator import TranslationChain
from claude_translator.lang.detect import detect_script
from claude_translator.storage.cache import load_cache, save_cache
from claude_translator.storage.overrides import load_overrides
from claude_translator.storage.paths import (
    ensure_translations_dir,
    get_claude_dir,
    get_config_path,
    get_translations_dir,
)

logger = logging.getLogger(__name__)


def _configure_logging(verbose: int, quiet: int) -> None:
    """Map -v/-q flags to logging levels."""
    level = logging.INFO - 10 * verbose + 10 * quiet
    level = max(logging.DEBUG, min(logging.CRITICAL, level))
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


@click.group()
@click.version_option(version=__version__)
@click.option("-v", "--verbose", count=True, help="Increase verbosity")
@click.option("-q", "--quiet", count=True, help="Decrease verbosity")
def main(verbose: int, quiet: int) -> None:
    """Claude Description Translator — multi-language plugin description translator."""
    _configure_logging(verbose, quiet)


@main.command()
@click.option("--lang", default=None, help="Target language (e.g. zh-CN, ja, ko)")
def discover(lang: str | None) -> None:
    """Discover all translatable plugin descriptions."""
    config = load_config(config_path=get_config_path(), target_lang=lang)
    claude_dir = get_claude_dir()

    click.echo(f"Scanning {claude_dir} ...")
    inventory = discover_all(claude_dir)
    click.echo(f"Found {inventory.size()} translatable items (target: {config.target_lang})")

    for record in inventory.records:
        status = "ok" if record.frontmatter_present else "no"
        click.echo(f"  {status} [{record.scope}] {record.canonical_id}")


@main.command()
@click.option("--lang", default=None, help="Target language override")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview changes without writing files",
)
@click.option(
    "-c",
    "--concurrency",
    type=click.IntRange(min=1, max=64),
    default=5,
    show_default=True,
    help="Max concurrent LLM calls (async mode only)",
)
@click.option(
    "--async/--no-async",
    "async_mode",
    default=True,
    show_default=True,
    help="Use async pipeline with concurrency (disable for sync fallback)",
)
def sync(lang: str | None, dry_run: bool, concurrency: int, async_mode: bool) -> None:
    """Translate descriptions and write them to files."""
    config = load_config(config_path=get_config_path(), target_lang=lang)
    translations_dir = ensure_translations_dir()
    migrate_legacy(translations_dir, config.target_lang)

    claude_dir = get_claude_dir()

    click.echo(f"Scanning {claude_dir} ...")
    inventory = discover_all(claude_dir)

    if inventory.size() == 0:
        click.echo("No translatable items found.")
        return

    overrides = load_overrides(config.target_lang)
    cache = load_cache(config.target_lang)
    updated_cache = dict(cache)

    def on_cache_update(_lang: str, cid: str, text: str) -> None:
        updated_cache[cid] = text

    chain = TranslationChain(
        overrides=overrides,
        cache=cache,
        on_cache_update=on_cache_update,
        # Delay OpenAI import until the first true LLM miss.
        client_factory=lambda: OpenAICompatClient(
            base_url=config.llm.base_url or None,
            api_key=config.llm.api_key or None,
            model=config.llm.model,
        ),
        async_client_factory=lambda: AsyncOpenAICompatClient(
            base_url=config.llm.base_url or None,
            api_key=config.llm.api_key or None,
            model=config.llm.model,
        ),
        target_lang=config.target_lang,
    )

    click.echo(
        f"Translating {inventory.size()} items to {config.target_lang} "
        f"(mode={'async' if async_mode else 'sync'}, "
        f"concurrency={concurrency if async_mode else 1}) ..."
    )

    if async_mode:
        try:
            import asyncio
        except Exception as exc:
            raise click.ClickException(
                f"Async mode is unavailable in the current Python environment: {exc}. "
                "Retry with --no-async."
            ) from exc

        try:
            from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
        except Exception as exc:
            raise click.ClickException(
                f"rich is required for async progress rendering: {exc}"
            ) from exc

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
        ) as progress:
            task_id = progress.add_task("Translating", total=inventory.size())
            report = asyncio.run(
                run_async(
                    inventory,
                    chain,
                    config.target_lang,
                    concurrency=concurrency,
                    dry_run=dry_run,
                    progress=progress,
                    progress_task_id=task_id,
                )
            )
    else:
        report = run_sync(inventory, chain, config.target_lang, dry_run=dry_run)

    if not dry_run and updated_cache != cache:
        save_cache(config.target_lang, updated_cache)

    click.echo(report.summary_line())
    for failed_record, exc in chain.failures:
        click.echo(f"  FAILED: {failed_record.canonical_id} - {exc}", err=True)
    if report.has_failures:
        sys.exit(1)


@main.command()
@click.option("--lang", default=None, help="Target language to verify")
def verify(lang: str | None) -> None:
    """Verify translation coverage and report status."""
    config = load_config(config_path=get_config_path(), target_lang=lang)
    migrate_legacy(get_translations_dir(), config.target_lang)

    claude_dir = get_claude_dir()
    inventory = discover_all(claude_dir)
    parser = FrontmatterParser()
    expected_script = script_tag_for_lang(config.target_lang)

    if expected_script is None:
        click.echo(
            "Verification by script is only supported for zh/ja/ko targets; "
            f"got {config.target_lang}."
        )
        return

    covered = 0
    missing = 0
    for record in inventory.records:
        content = Path(record.source_path).read_text(encoding="utf-8-sig")
        fm, _ = parser.parse(content)
        description = parser.get_description(fm) or ""
        if description and detect_script(description) == expected_script:
            covered += 1
        else:
            missing += 1
            click.echo(f"  MISSING: {record.canonical_id}")

    total = inventory.size()
    pct = (covered / total * 100) if total > 0 else 0
    click.echo(f"Coverage: {covered}/{total} ({pct:.1f}%) — {missing} missing")


@main.command()
@click.option("--lang", default="zh-CN", help="Default target language")
def init(lang: str) -> None:
    """Initialize translation configuration."""
    ensure_translations_dir()
    config_path = get_config_path()

    config_data = {
        "target_lang": lang,
        "llm": {
            "model": "gpt-4o-mini",
        },
    }
    config_path.write_text(
        json.dumps(config_data, indent=2) + "\n",
        encoding="utf-8",
    )
    click.echo(f"Created config at {config_path} (target: {lang})")
