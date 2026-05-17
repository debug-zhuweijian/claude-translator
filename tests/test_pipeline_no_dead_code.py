"""Guard against re-introducing dead code in pipeline."""

from pathlib import Path

from claude_translator.core.models import Inventory, Record
from claude_translator.core.pipeline import run_sync
from claude_translator.core.translator import TranslationChain


def test_same_translation_as_original_skips(tmp_path: Path):
    md = tmp_path / "identity.md"
    md.write_text("---\ndescription: Hello\n---\n# Body\n", encoding="utf-8")

    record = Record(
        canonical_id="plugin.demo.skill:identity",
        kind="skill",
        scope="plugin",
        source_path=str(md),
        relative_path="skills/identity/SKILL.md",
        plugin_key="demo",
        current_description="Hello",
        frontmatter_present=True,
    )
    inventory = Inventory((record,))

    class IdentityClient:
        def translate(self, text: str, source_lang: str, target_lang: str) -> str:
            return text

    chain = TranslationChain(
        overrides={},
        cache={},
        on_cache_update=lambda lang, cid, text: None,
        client=IdentityClient(),
        target_lang="zh-CN",
    )

    report = run_sync(inventory, chain, "zh-CN", dry_run=True)

    assert report.skip == 1
    assert report.llm == 0
    assert report.total == 1
