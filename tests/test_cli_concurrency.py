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


def _record(
    tmp_path: Path,
    name: str,
    description: str,
    *,
    frontmatter_present: bool = True,
) -> Record:
    md = tmp_path / f"{name}.md"
    md.write_text(f"---\ndescription: {description}\n---\n# Body\n", encoding="utf-8")
    return Record(
        canonical_id=f"plugin.demo.skill:{name}",
        kind="skill",
        scope="plugin",
        source_path=str(md),
        relative_path=f"skills/{name}/SKILL.md",
        plugin_key="demo",
        current_description=description,
        frontmatter_present=frontmatter_present,
    )


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


def test_discover_lists_records(tmp_path: Path, monkeypatch):
    inventory = Inventory(
        (
            _record(tmp_path, "brainstorm", "Brainstorm ideas"),
            _record(tmp_path, "draft", "Draft docs", frontmatter_present=False),
        )
    )
    monkeypatch.setattr(cli_module, "discover_all", lambda _: inventory)

    runner = CliRunner()
    result = runner.invoke(main, ["discover", "--lang", "ja"])

    assert result.exit_code == 0, result.output
    assert "Found 2 translatable items (target: ja)" in result.output
    assert "ok [plugin] plugin.demo.skill:brainstorm" in result.output
    assert "no [plugin] plugin.demo.skill:draft" in result.output


def test_sync_exits_early_when_inventory_is_empty(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(cli_module, "discover_all", lambda _: Inventory(()))
    save_calls: list[tuple[str, dict[str, str]]] = []
    monkeypatch.setattr(
        cli_module,
        "save_cache",
        lambda lang, data: save_calls.append((lang, data)),
    )

    runner = CliRunner()
    result = runner.invoke(main, ["sync", "--no-async"])

    assert result.exit_code == 0, result.output
    assert "No translatable items found." in result.output
    assert save_calls == []


def test_sync_saves_cache_and_reports_failures(tmp_path: Path, monkeypatch):
    record = _record(tmp_path, "brainstorm", "Brainstorm ideas")
    monkeypatch.setattr(cli_module, "discover_all", lambda _: Inventory((record,)))
    saved: list[tuple[str, dict[str, str]]] = []
    monkeypatch.setattr(
        cli_module,
        "save_cache",
        lambda lang, data: saved.append((lang, dict(data))),
    )

    def fake_run_sync(inventory, chain, target_lang, dry_run=False):
        chain._on_cache_update(target_lang, record.canonical_id, "头脑风暴")
        chain._failures.append((record, RuntimeError("boom")))
        return SyncReport(total=1, failed=1)

    monkeypatch.setattr(cli_module, "run_sync", fake_run_sync)
    runner = CliRunner()
    result = runner.invoke(main, ["sync", "--no-async"])

    assert result.exit_code == 1
    assert "Sync complete: total=1, failed=1" in result.output
    assert "FAILED: plugin.demo.skill:brainstorm - boom" in result.output
    assert saved == [("zh-CN", {record.canonical_id: "头脑风暴"})]


def test_verify_rejects_non_cjk_targets(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(cli_module, "discover_all", lambda _: _inventory(tmp_path))

    runner = CliRunner()
    result = runner.invoke(main, ["verify", "--lang", "fr"])

    assert result.exit_code == 0, result.output
    assert "Verification by script is only supported for zh/ja/ko targets; got fr." in result.output


def test_verify_reports_covered_and_missing_records(tmp_path: Path, monkeypatch):
    covered = tmp_path / "covered.md"
    covered.write_text("---\ndescription: 中文描述\n---\n# Body\n", encoding="utf-8")
    missing = tmp_path / "missing.md"
    missing.write_text("---\ndescription: English text\n---\n# Body\n", encoding="utf-8")
    inventory = Inventory(
        (
            Record(
                canonical_id="plugin.demo.skill:covered",
                kind="skill",
                scope="plugin",
                source_path=str(covered),
                relative_path="skills/covered/SKILL.md",
                plugin_key="demo",
                current_description="Brainstorm ideas",
                frontmatter_present=True,
            ),
            Record(
                canonical_id="plugin.demo.skill:missing",
                kind="skill",
                scope="plugin",
                source_path=str(missing),
                relative_path="skills/missing/SKILL.md",
                plugin_key="demo",
                current_description="Draft docs",
                frontmatter_present=True,
            ),
        )
    )
    monkeypatch.setattr(cli_module, "discover_all", lambda _: inventory)

    runner = CliRunner()
    result = runner.invoke(main, ["verify"])

    assert result.exit_code == 0, result.output
    assert "MISSING: plugin.demo.skill:missing" in result.output
    assert "Coverage: 1/2 (50.0%)" in result.output
