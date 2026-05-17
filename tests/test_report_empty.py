"""Tests for SyncReport.empty field."""

from pathlib import Path

from claude_translator.clients.fake import FakeClient
from claude_translator.core.models import Inventory, Record
from claude_translator.core.pipeline import run_sync
from claude_translator.core.report import SyncReport
from claude_translator.core.translator import TranslationChain


def test_sync_report_has_empty_field():
    report = SyncReport()
    assert report.empty == 0


def test_bump_empty_increments_empty():
    report = SyncReport().bump("empty")
    assert report.empty == 1
    assert report.total == 1
    assert report.skip == 0


def test_summary_line_includes_empty():
    report = SyncReport().bump("empty")
    assert "empty=1" in report.summary_line()


def test_pipeline_empty_description_counts_as_empty(tmp_path: Path):
    md = tmp_path / "empty.md"
    md.write_text("---\ndescription: \n---\n# Body\n", encoding="utf-8")

    record = Record(
        canonical_id="plugin.demo.skill:empty",
        kind="skill",
        scope="plugin",
        source_path=str(md),
        relative_path="skills/empty/SKILL.md",
        plugin_key="demo",
        current_description="",
        frontmatter_present=True,
    )
    inventory = Inventory((record,))
    chain = TranslationChain(
        overrides={},
        cache={},
        on_cache_update=lambda lang, cid, text: None,
        client=FakeClient(),
        target_lang="zh-CN",
    )

    report = run_sync(inventory, chain, "zh-CN", dry_run=True)

    assert report.empty == 1
    assert report.skip == 0
    assert report.total == 1
