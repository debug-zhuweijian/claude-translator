from pathlib import Path

from claude_translator.core.injector import inject_translation
from claude_translator.core.models import Record


def test_inject_creates_frontmatter(tmp_path: Path):
    md_file = tmp_path / "test.md"
    md_file.write_text("# Just a heading\nSome text", encoding="utf-8")

    record = Record(
        canonical_id="plugin.test.skill:x", kind="skill", scope="plugin",
        source_path=str(md_file), relative_path="test.md",
        matched_translation="翻译文本", frontmatter_present=False,
    )
    new_record = inject_translation(record)
    content = md_file.read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "description: 翻译文本" in content
    assert "# Just a heading" in content
    assert new_record.frontmatter_present is True


def test_inject_updates_existing_frontmatter(tmp_path: Path):
    md_file = tmp_path / "test.md"
    md_file.write_text("---\ndescription: Old\n---\n# Body", encoding="utf-8")

    record = Record(
        canonical_id="plugin.test.skill:x", kind="skill", scope="plugin",
        source_path=str(md_file), relative_path="test.md",
        matched_translation="新翻译", frontmatter_present=True,
    )
    inject_translation(record)
    content = md_file.read_text(encoding="utf-8")
    assert "description: 新翻译" in content
    assert "Old" not in content


def test_inject_preserves_crlf(tmp_path: Path):
    md_file = tmp_path / "test.md"
    md_file.write_bytes(b"---\r\ndescription: Old\r\n---\r\n# Body")

    record = Record(
        canonical_id="plugin.test.skill:x", kind="skill", scope="plugin",
        source_path=str(md_file), relative_path="test.md",
        matched_translation="CRLF翻译", frontmatter_present=True,
    )
    inject_translation(record)
    raw = md_file.read_bytes().decode("utf-8", errors="replace")
    assert "description: CRLF翻译" in raw or "description: CRLF" in raw
    assert b"\r\n" in md_file.read_bytes()


def test_inject_no_translation_skips(tmp_path: Path):
    md_file = tmp_path / "test.md"
    original = "---\ndescription: Keep\n---\n# Body"
    md_file.write_text(original, encoding="utf-8")

    record = Record(
        canonical_id="plugin.test.skill:x", kind="skill", scope="plugin",
        source_path=str(md_file), relative_path="test.md",
        matched_translation="", frontmatter_present=True,
    )
    inject_translation(record)
    assert md_file.read_text(encoding="utf-8") == original
