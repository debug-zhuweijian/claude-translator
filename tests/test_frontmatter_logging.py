"""Ensure YAML parse failures are logged."""

import logging

from claude_translator.core.frontmatter import FrontmatterParser


def test_invalid_yaml_logs_warning(caplog):
    bad_content = "---\ndescription: : : : broken :\n---\nbody"

    parser = FrontmatterParser()
    with caplog.at_level(logging.WARNING, logger="claude_translator.core.frontmatter"):
        fm, body = parser.parse(bad_content)

    assert fm == {}
    assert body == bad_content
    assert any("Failed to parse YAML frontmatter" in rec.message for rec in caplog.records)


def test_valid_yaml_no_warning(caplog):
    parser = FrontmatterParser()
    with caplog.at_level(logging.WARNING, logger="claude_translator.core.frontmatter"):
        parser.parse("---\ndescription: fine\n---\nbody")

    assert not caplog.records
