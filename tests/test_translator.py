from dataclasses import replace
from claude_translator.core.models import Record
from claude_translator.core.translator import TranslationChain
from claude_translator.clients.fake import FakeClient


def _make_record(desc: str = "Hello") -> Record:
    return Record(
        canonical_id="plugin.test.skill:demo",
        kind="skill", scope="plugin",
        source_path="/path/demo.md",
        relative_path="skills/demo/SKILL.md",
        plugin_key="test",
        current_description=desc,
    )


def test_override_hit():
    chain = TranslationChain(
        overrides_loader=lambda lang: {"plugin.test.skill:demo": "用户覆盖"},
        cache_loader=lambda lang: {},
        cache_updater=lambda lang, cid, text: None,
        client=FakeClient(), target_lang="zh-CN",
    )
    r = chain.translate(_make_record())
    assert r.matched_translation == "用户覆盖"
    assert r.status == "override"


def test_cache_hit():
    chain = TranslationChain(
        overrides_loader=lambda lang: {},
        cache_loader=lambda lang: {"plugin.test.skill:demo": "缓存翻译"},
        cache_updater=lambda lang, cid, text: None,
        client=FakeClient(), target_lang="zh-CN",
    )
    r = chain.translate(_make_record())
    assert r.matched_translation == "缓存翻译"
    assert r.status == "cache"


def test_llm_hit():
    updated: dict[str, str] = {}
    chain = TranslationChain(
        overrides_loader=lambda lang: {},
        cache_loader=lambda lang: {},
        cache_updater=lambda lang, cid, text: updated.__setitem__(cid, text),
        client=FakeClient(), target_lang="zh-CN",
    )
    r = chain.translate(_make_record())
    assert r.matched_translation == "[zh-CN] Hello"
    assert r.status == "llm"
    assert "plugin.test.skill:demo" in updated


def test_fallback_original():
    class BrokenClient:
        def translate(self, text: str, sl: str, tl: str) -> str:
            raise RuntimeError("API down")

    chain = TranslationChain(
        overrides_loader=lambda lang: {},
        cache_loader=lambda lang: {},
        cache_updater=lambda lang, cid, text: None,
        client=BrokenClient(), target_lang="zh-CN",
    )
    r = chain.translate(_make_record("Original text"))
    assert r.matched_translation == "Original text"
    assert r.status == "original"


def test_translate_immutably():
    original = _make_record()
    chain = TranslationChain(
        overrides_loader=lambda lang: {},
        cache_loader=lambda lang: {},
        cache_updater=lambda lang, cid, text: None,
        client=FakeClient(), target_lang="ja",
    )
    result = chain.translate(original)
    assert original.matched_translation == ""
    assert result.matched_translation != ""


def test_empty_description():
    chain = TranslationChain(
        overrides_loader=lambda lang: {},
        cache_loader=lambda lang: {},
        cache_updater=lambda lang, cid, text: None,
        client=FakeClient(), target_lang="zh-CN",
    )
    r = chain.translate(_make_record(""))
    assert r.status == "empty"
    assert r.matched_translation == ""
