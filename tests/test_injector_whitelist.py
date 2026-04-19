"""Whitelist-based path validation for injector."""

import logging
from pathlib import Path

from claude_translator.core.injector import inject_translation
from claude_translator.core.models import Record


def _record(path: Path, translation: str = "翻译") -> Record:
    return Record(
        canonical_id="plugin.demo.skill:t",
        kind="skill",
        scope="plugin",
        source_path=str(path),
        relative_path="skills/t/SKILL.md",
        matched_translation=translation,
        current_description="Hello",
        frontmatter_present=True,
    )


def test_inject_allows_whitelisted_path(tmp_path: Path):
    md = tmp_path / "ok.md"
    md.write_text("---\ndescription: Old\n---\nBody", encoding="utf-8")

    record = _record(md, "新翻译")
    allowed = frozenset({md.resolve()})

    result = inject_translation(record, allowed_paths=allowed)

    assert "新翻译" in md.read_text(encoding="utf-8")
    assert result.frontmatter_present is True


def test_inject_rejects_path_outside_whitelist(tmp_path: Path, caplog):
    target = tmp_path / "attack.md"
    target.write_text("---\ndescription: Orig\n---\nBody", encoding="utf-8")
    original = target.read_bytes()

    record = _record(target, "恶意翻译")
    allowed = frozenset({(tmp_path / "whitelisted.md").resolve()})

    with caplog.at_level(logging.WARNING, logger="claude_translator.core.injector"):
        result = inject_translation(record, allowed_paths=allowed)

    assert target.read_bytes() == original
    assert result.frontmatter_present is True
    assert any(
        "not in allowed_paths" in rec.message.lower() or "allowed_paths" in rec.message.lower()
        for rec in caplog.records
    )


def test_inject_rejects_traversal_attempt(tmp_path: Path):
    legitimate = tmp_path / "legit.md"
    legitimate.write_text("---\ndescription: X\n---\nBody", encoding="utf-8")

    sneaky_parent = tmp_path / "sub"
    sneaky_parent.mkdir()
    sneaky = sneaky_parent / ".." / "legit.md"

    allowed = frozenset({(tmp_path / "other.md").resolve()})
    record = _record(sneaky, "X")

    original = legitimate.read_bytes()
    inject_translation(record, allowed_paths=allowed)

    assert legitimate.read_bytes() == original
