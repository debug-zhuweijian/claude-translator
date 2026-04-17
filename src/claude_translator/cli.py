"""CLI entry point with Click subcommands."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

from claude_translator import __version__
from claude_translator.clients.openai_compat import OpenAICompatClient
from claude_translator.config.loaders import load_config
from claude_translator.core.discovery import discover_all
from claude_translator.core.frontmatter import FrontmatterParser
from claude_translator.core.migration import migrate_legacy
from claude_translator.core.pipeline import run_sync, script_tag_for_lang
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


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Claude Description Translator — multi-language plugin description translator."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


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
def sync(lang: str | None, dry_run: bool) -> None:
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

    client = OpenAICompatClient(
        base_url=config.llm.base_url or None,
        api_key=config.llm.api_key or None,
        model=config.llm.model,
    )
    chain = TranslationChain(
        overrides=overrides,
        cache=cache,
        on_cache_update=on_cache_update,
        client=client,
        target_lang=config.target_lang,
    )

    click.echo(f"Translating {inventory.size()} items to {config.target_lang} ...")
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
