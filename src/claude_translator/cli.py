"""CLI entry point with Click subcommands."""

from __future__ import annotations

import json
import logging

import click

from claude_translator import __version__

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
    from pathlib import Path

    from claude_translator.config.loaders import load_config
    from claude_translator.core.discovery import discover_all
    from claude_translator.storage.paths import get_claude_dir, get_config_path

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
def sync(lang: str | None) -> None:
    """Translate descriptions and write them to files."""
    from claude_translator.clients.openai_compat import OpenAICompatClient
    from claude_translator.config.loaders import load_config
    from claude_translator.core.discovery import discover_all
    from claude_translator.core.injector import inject_translation
    from claude_translator.core.translator import TranslationChain
    from claude_translator.storage.cache import load_cache, update_cache
    from claude_translator.storage.overrides import load_overrides
    from claude_translator.storage.paths import get_claude_dir, get_config_path

    config = load_config(config_path=get_config_path(), target_lang=lang)

    from claude_translator.core.migration import migrate_legacy
    from claude_translator.storage.paths import get_translations_dir
    migrate_legacy(get_translations_dir(), config.target_lang)

    claude_dir = get_claude_dir()

    click.echo(f"Scanning {claude_dir} ...")
    inventory = discover_all(claude_dir)

    if inventory.size() == 0:
        click.echo("No translatable items found.")
        return

    client = OpenAICompatClient(
        base_url=config.llm.base_url or None,
        api_key=config.llm.api_key or None,
        model=config.llm.model,
    )
    chain = TranslationChain(
        overrides_loader=load_overrides,
        cache_loader=load_cache,
        cache_updater=update_cache,
        client=client,
        target_lang=config.target_lang,
    )

    click.echo(f"Translating {inventory.size()} items to {config.target_lang} ...")
    for record in inventory.records:
        translated = chain.translate(record)
        if translated.matched_translation and translated.matched_translation != record.current_description:
            inject_translation(translated)
            click.echo(f"  [{translated.status}] {translated.canonical_id}")
        else:
            click.echo(f"  [skip] {record.canonical_id}")

    click.echo("Sync complete.")


@main.command()
@click.option("--lang", default=None, help="Target language to verify")
def verify(lang: str | None) -> None:
    """Verify translation coverage and report status."""
    from claude_translator.config.loaders import load_config
    from claude_translator.core.discovery import discover_all
    from claude_translator.storage.cache import load_cache
    from claude_translator.storage.overrides import load_overrides
    from claude_translator.storage.paths import get_claude_dir, get_config_path

    config = load_config(config_path=get_config_path(), target_lang=lang)

    from claude_translator.core.migration import migrate_legacy
    from claude_translator.storage.paths import get_translations_dir
    migrate_legacy(get_translations_dir(), config.target_lang)

    claude_dir = get_claude_dir()
    inventory = discover_all(claude_dir)

    overrides = load_overrides(config.target_lang)
    cache = load_cache(config.target_lang)

    covered = 0
    missing = 0
    for record in inventory.records:
        if record.canonical_id in overrides or record.canonical_id in cache:
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
    from claude_translator.storage.paths import get_config_path, get_translations_dir

    translations_dir = get_translations_dir()
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
