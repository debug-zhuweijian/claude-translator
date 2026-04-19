"""CLI --concurrency and --async/--no-async flags."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from click.testing import CliRunner

import claude_translator.cli as cli_module
from claude_translator.cli import main
from claude_translator.core.models import Inventory, Record
from claude_translator.core.report import SyncReport
from tests.async_helpers import install_fake_asyncio, run_coro


def _inventory(tmp_path: Path) -> Inventory:
    md = tmp_path / "demo.md"
    md.write_text("---\ndescription: Brainstorm ideas\n---\n# Body\n", encoding="utf-8")
    record = Record(
        canonical_id="plugin.demo.skill:brainstorm",
        kind="skill",
        scope="plugin",
        source_path=str(md),
        relative_path="skills/brainstorm/SKILL.md",
        plugin_key="demo",
        current_description="Brainstorm ideas",
        frontmatter_present=True,
    )
    return Inventory((record,))


@pytest.fixture(autouse=True)
def fake_environment(tmp_path: Path, monkeypatch):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    monkeypatch.setattr(cli_module, "ensure_translations_dir", lambda: translations_dir)
    monkeypatch.setattr(cli_module, "get_config_path", lambda: translations_dir / "config.json")
    monkeypatch.setattr(cli_module, "get_claude_dir", lambda: tmp_path / ".claude")
    monkeypatch.setattr(
        cli_module,
        "load_config",
        lambda config_path, target_lang=None: type(
            "Cfg",
            (),
            {
                "target_lang": target_lang or "zh-CN",
                "llm": type(
                    "LLM",
                    (),
                    {"base_url": None, "api_key": "test-key", "model": "gpt-4o-mini"},
                )(),
            },
        )(),
    )
    monkeypatch.setattr(cli_module, "load_overrides", lambda lang: {})
    monkeypatch.setattr(cli_module, "load_cache", lambda lang: {})
    monkeypatch.setattr(cli_module, "save_cache", lambda lang, data: None)
    monkeypatch.setattr(cli_module, "migrate_legacy", lambda *args, **kwargs: None)


def test_sync_has_concurrency_option():
    runner = CliRunner()
    result = runner.invoke(main, ["sync", "--help"])
    assert result.exit_code == 0
    assert "--concurrency" in result.output
    assert "--async" in result.output
    assert "--no-async" in result.output


def test_sync_dispatches_sync_mode(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(cli_module, "discover_all", lambda _: _inventory(tmp_path))
    called = {}

    def fake_run_sync(inventory, chain, target_lang, dry_run=False):
        called["mode"] = "sync"
        called["dry_run"] = dry_run
        return SyncReport(total=1, llm=1)

    monkeypatch.setattr(cli_module, "run_sync", fake_run_sync)
    runner = CliRunner()
    result = runner.invoke(main, ["sync", "--dry-run", "--no-async", "-c", "3"])

    assert result.exit_code == 0, result.output
    assert called == {"mode": "sync", "dry_run": True}


def test_sync_dispatches_async_mode(tmp_path: Path, monkeypatch):
    fake_asyncio = install_fake_asyncio(monkeypatch)
    monkeypatch.setattr(cli_module, "discover_all", lambda _: _inventory(tmp_path))
    called = {}

    async def fake_run_async(inventory, chain, target_lang, **kwargs):
        called["mode"] = "async"
        called["kwargs"] = kwargs
        return SyncReport(total=1, llm=1)

    monkeypatch.setattr(cli_module, "run_async", fake_run_async)
    fake_asyncio.run = run_coro

    class DummyProgress:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def add_task(self, description, total):
            return "task-1"

        def advance(self, task_id, amount=1):
            return None

    monkeypatch.setitem(
        sys.modules,
        "rich.progress",
        types.SimpleNamespace(
            Progress=DummyProgress,
            BarColumn=lambda: None,
            TextColumn=lambda *args, **kwargs: None,
            TimeElapsedColumn=lambda: None,
        ),
    )

    runner = CliRunner()
    result = runner.invoke(main, ["sync", "--dry-run", "--async", "-c", "3"])

    assert result.exit_code == 0, result.output
    assert called["mode"] == "async"
    assert called["kwargs"]["concurrency"] == 3
    assert called["kwargs"]["dry_run"] is True
