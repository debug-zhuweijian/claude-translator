"""Async pipeline run_async."""

from __future__ import annotations

from pathlib import Path

from claude_translator.clients.async_fake import AsyncFakeClient
from claude_translator.core.models import Inventory, Record
from claude_translator.core.pipeline import run_async
from claude_translator.core.translator import TranslationChain
from tests.async_helpers import install_fake_asyncio, run_coro


def _record(path: Path, cid: str, description: str) -> Record:
    path.write_text(f"---\ndescription: {description}\n---\n# Body\n", encoding="utf-8")
    return Record(
        canonical_id=cid,
        kind="skill",
        scope="plugin",
        source_path=str(path),
        relative_path=f"skills/{cid}/SKILL.md",
        plugin_key="demo",
        current_description=description,
        frontmatter_present=True,
    )


def test_run_async_dry_run_counts_llm(tmp_path: Path, monkeypatch):
    install_fake_asyncio(monkeypatch)
    records = tuple(_record(tmp_path / f"r{i}.md", f"r{i}", f"Hello {i}") for i in range(3))
    inventory = Inventory(records)
    chain = TranslationChain(
        overrides={},
        cache={},
        on_cache_update=lambda lang, cid, text: None,
        async_client=AsyncFakeClient(),
        target_lang="zh-CN",
    )

    report = run_coro(run_async(inventory, chain, "zh-CN", concurrency=2, dry_run=True))
    assert report.llm == 3
    assert report.total == 3
    for record in records:
        assert "Hello" in Path(record.source_path).read_text(encoding="utf-8")


def test_run_async_injects_when_not_dry(tmp_path: Path, monkeypatch):
    install_fake_asyncio(monkeypatch)
    md = tmp_path / "r.md"
    record = _record(md, "r", "Hello")
    inventory = Inventory((record,))
    chain = TranslationChain(
        overrides={},
        cache={},
        on_cache_update=lambda lang, cid, text: None,
        async_client=AsyncFakeClient(),
        target_lang="zh-CN",
    )

    report = run_coro(run_async(inventory, chain, "zh-CN", concurrency=2, dry_run=False))
    assert report.llm == 1
    assert "[zh-CN] Hello" in md.read_text(encoding="utf-8")


def test_run_async_uses_requested_concurrency(tmp_path: Path, monkeypatch):
    fake_asyncio = install_fake_asyncio(monkeypatch)
    records = tuple(_record(tmp_path / f"r{i}.md", f"r{i}", f"Hello {i}") for i in range(4))
    inventory = Inventory(records)
    chain = TranslationChain(
        overrides={},
        cache={},
        on_cache_update=lambda lang, cid, text: None,
        async_client=AsyncFakeClient(),
        target_lang="zh-CN",
    )

    run_coro(run_async(inventory, chain, "zh-CN", concurrency=2, dry_run=True))
    assert fake_asyncio.semaphore_values == [2]


def test_run_async_cjk_skip(tmp_path: Path, monkeypatch):
    install_fake_asyncio(monkeypatch)
    md = tmp_path / "zh.md"
    record = _record(md, "zh", "你好")
    inventory = Inventory((record,))
    chain = TranslationChain(
        overrides={},
        cache={},
        on_cache_update=lambda lang, cid, text: None,
        async_client=AsyncFakeClient(),
        target_lang="zh-CN",
    )

    report = run_coro(run_async(inventory, chain, "zh-CN", concurrency=1, dry_run=True))
    assert report.skip == 1
    assert report.total == 1


def test_run_async_progress_callback(tmp_path: Path, monkeypatch):
    install_fake_asyncio(monkeypatch)
    advances = []

    class FakeProgress:
        def advance(self, task_id, amount=1):
            advances.append((task_id, amount))

    records = tuple(_record(tmp_path / f"r{i}.md", f"r{i}", f"Hello {i}") for i in range(5))
    inventory = Inventory(records)
    chain = TranslationChain(
        overrides={},
        cache={},
        on_cache_update=lambda lang, cid, text: None,
        async_client=AsyncFakeClient(),
        target_lang="zh-CN",
    )

    run_coro(
        run_async(
            inventory,
            chain,
            "zh-CN",
            concurrency=2,
            dry_run=True,
            progress=FakeProgress(),
            progress_task_id="task-42",
        )
    )
    assert len(advances) == 5
    assert all(task_id == "task-42" for task_id, _ in advances)


def test_run_async_injector_uses_whitelist(tmp_path: Path, monkeypatch):
    install_fake_asyncio(monkeypatch)
    md = tmp_path / "r.md"
    record = _record(md, "r", "Hello")
    inventory = Inventory((record,))
    chain = TranslationChain(
        overrides={},
        cache={},
        on_cache_update=lambda lang, cid, text: None,
        async_client=AsyncFakeClient(),
        target_lang="zh-CN",
    )

    report = run_coro(run_async(inventory, chain, "zh-CN", concurrency=1, dry_run=False))
    assert report.llm == 1
    assert "[zh-CN] Hello" in md.read_text(encoding="utf-8")
