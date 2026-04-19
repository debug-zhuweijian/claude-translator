"""Async TranslationChain."""

from __future__ import annotations

from claude_translator.clients.async_fake import AsyncFakeClient
from claude_translator.core.models import Record
from claude_translator.core.translator import TranslationChain
from tests.async_helpers import install_fake_asyncio, run_coro


def _record(cid: str, desc: str) -> Record:
    return Record(
        canonical_id=cid,
        kind="skill",
        scope="plugin",
        source_path=f"/tmp/{cid}.md",
        relative_path=f"{cid}.md",
        plugin_key="demo",
        current_description=desc,
    )


def test_translate_async_llm_path(monkeypatch):
    install_fake_asyncio(monkeypatch)
    updates = []

    async def run():
        chain = TranslationChain(
            overrides={},
            cache={},
            on_cache_update=lambda lang, cid, text: updates.append((lang, cid, text)),
            async_client=AsyncFakeClient(),
            target_lang="zh-CN",
        )
        result = await chain.translate_async(_record("a", "Hello"))
        assert result.status == "llm"
        assert result.matched_translation == "[zh-CN] Hello"

    run_coro(run())
    assert updates == [("zh-CN", "a", "[zh-CN] Hello")]


def test_translate_async_override_path(monkeypatch):
    install_fake_asyncio(monkeypatch)
    async def run():
        chain = TranslationChain(
            overrides={"a": "手动翻译"},
            cache={},
            on_cache_update=lambda lang, cid, text: None,
            async_client=AsyncFakeClient(),
            target_lang="zh-CN",
        )
        result = await chain.translate_async(_record("a", "Hello"))
        assert result.status == "override"
        assert result.matched_translation == "手动翻译"

    run_coro(run())


def test_translate_async_cache_path(monkeypatch):
    install_fake_asyncio(monkeypatch)
    async def run():
        chain = TranslationChain(
            overrides={},
            cache={"a": "缓存翻译"},
            on_cache_update=lambda lang, cid, text: None,
            async_client=AsyncFakeClient(),
            target_lang="zh-CN",
        )
        result = await chain.translate_async(_record("a", "Hello"))
        assert result.status == "cache"
        assert result.matched_translation == "缓存翻译"

    run_coro(run())


def test_translate_async_empty_desc(monkeypatch):
    install_fake_asyncio(monkeypatch)
    async def run():
        chain = TranslationChain(
            overrides={},
            cache={},
            on_cache_update=lambda lang, cid, text: None,
            async_client=AsyncFakeClient(),
            target_lang="zh-CN",
        )
        result = await chain.translate_async(_record("a", ""))
        assert result.status == "empty"

    run_coro(run())


def test_translate_async_concurrent_cache_safe(monkeypatch):
    fake_asyncio = install_fake_asyncio(monkeypatch)

    class SlowFake:
        async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
            await fake_asyncio.sleep(0.01)
            return f"[{target_lang}] {text}"

    async def run():
        cache: dict[str, str] = {}
        chain = TranslationChain(
            overrides={},
            cache=cache,
            on_cache_update=lambda lang, cid, text: None,
            async_client=SlowFake(),
            target_lang="zh-CN",
        )
        records = [_record(f"a{i}", f"Hello {i}") for i in range(20)]
        results = [await chain.translate_async(record) for record in records]

        assert all(result.status == "llm" for result in results)
        assert len(cache) == 20
        for i in range(20):
            assert cache[f"a{i}"] == f"[zh-CN] Hello {i}"

    run_coro(run())


def test_translate_async_failure_records_and_returns_original(monkeypatch):
    install_fake_asyncio(monkeypatch)

    class BoomClient:
        async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
            raise RuntimeError("boom")

    async def run():
        chain = TranslationChain(
            overrides={},
            cache={},
            on_cache_update=lambda lang, cid, text: None,
            async_client=BoomClient(),
            target_lang="zh-CN",
        )
        result = await chain.translate_async(_record("a", "Hello"))
        assert result.status == "original"
        assert len(chain.failures) == 1

    run_coro(run())
