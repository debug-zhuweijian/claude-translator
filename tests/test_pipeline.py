from pathlib import Path

from claude_translator.clients.fake import FakeClient
from claude_translator.core.models import Inventory, Record
from claude_translator.core.pipeline import run_sync
from claude_translator.core.translator import TranslationChain


def _record(path: Path, description: str) -> Record:
    path.write_text(f"---\ndescription: {description}\n---\n# Body\n", encoding="utf-8")
    return Record(
        canonical_id="plugin.demo.skill:test",
        kind="skill",
        scope="plugin",
        source_path=str(path),
        relative_path="skills/test/SKILL.md",
        plugin_key="demo",
        current_description=description,
        frontmatter_present=True,
    )


def test_run_sync_dry_run_does_not_write(tmp_path: Path):
    md_file = tmp_path / "demo.md"
    record = _record(md_file, "Hello")
    inventory = Inventory((record,))
    chain = TranslationChain(
        overrides={},
        cache={},
        on_cache_update=lambda lang, cid, text: None,
        client=FakeClient(),
        target_lang="zh-CN",
    )

    report = run_sync(inventory, chain, "zh-CN", dry_run=True)

    assert report.llm == 1
    assert "Hello" in md_file.read_text(encoding="utf-8")


def test_run_sync_skips_existing_target_script(tmp_path: Path):
    md_file = tmp_path / "demo.md"
    record = _record(md_file, "你好")
    inventory = Inventory((record,))
    chain = TranslationChain(
        overrides={},
        cache={},
        on_cache_update=lambda lang, cid, text: None,
        client=FakeClient(),
        target_lang="zh-CN",
    )

    report = run_sync(inventory, chain, "zh-CN", dry_run=True)

    assert report.skip == 1
    assert report.total == 1
