import pytest

from claude_translator.core.canonical import (
    generate_canonical_id,
    name_from_filename,
    parse_canonical_id,
)
from claude_translator.errors import ConfigError


def test_generate_plugin_id():
    assert (
        generate_canonical_id("skill", "brainstorm", "plugin", "superpowers")
        == "plugin.superpowers.skill:brainstorm"
    )


def test_generate_user_id():
    assert generate_canonical_id("command", "commit", "user", "") == "user.command:commit"


def test_parse_plugin_id():
    scope, pk, kind, name = parse_canonical_id("plugin.superpowers.skill:brainstorm")
    assert (scope, pk, kind, name) == ("plugin", "superpowers", "skill", "brainstorm")


def test_parse_user_id():
    scope, pk, kind, name = parse_canonical_id("user.command:commit")
    assert (scope, pk, kind, name) == ("user", "", "command", "commit")


def test_roundtrip():
    cid = generate_canonical_id("skill", "test-skill", "plugin", "my-plugin")
    scope, pk, kind, name = parse_canonical_id(cid)
    assert scope == "plugin" and pk == "my-plugin" and kind == "skill" and name == "test-skill"


def test_roundtrip_dotted_plugin_key():
    """Dotted plugin keys like 'pua.skills' must survive round-trip."""
    cid = generate_canonical_id("skill", "foo", "plugin", "pua.skills")
    assert cid == "plugin.pua.skills.skill:foo"
    scope, pk, kind, name = parse_canonical_id(cid)
    assert (scope, pk, kind, name) == ("plugin", "pua.skills", "skill", "foo")


def test_roundtrip_deeply_nested_plugin_key():
    """Multi-dot plugin keys like 'compound-engineering.context7'."""
    cid = generate_canonical_id("skill", "bar", "plugin", "compound-engineering.context7")
    assert cid == "plugin.compound-engineering.context7.skill:bar"
    scope, pk, kind, name = parse_canonical_id(cid)
    assert (scope, pk, kind, name) == ("plugin", "compound-engineering.context7", "skill", "bar")


def test_roundtrip_user_namespaced_command():
    cid = generate_canonical_id("command", "gsd:add-backlog", "user")
    assert cid == "user.command:gsd:add-backlog"
    scope, pk, kind, name = parse_canonical_id(cid)
    assert (scope, pk, kind, name) == ("user", "", "command", "gsd:add-backlog")


def test_roundtrip_plugin_namespaced_command():
    cid = generate_canonical_id("command", "ce:brainstorm", "plugin", "compound-engineering")
    assert cid == "plugin.compound-engineering.command:ce:brainstorm"
    scope, pk, kind, name = parse_canonical_id(cid)
    assert (scope, pk, kind, name) == ("plugin", "compound-engineering", "command", "ce:brainstorm")


def test_name_from_filename():
    assert name_from_filename("brainstorm.md") == "brainstorm"
    assert name_from_filename("SKILL.md") == "SKILL"
    assert name_from_filename("noext") == "noext"


def test_parse_invalid_id_raises_config_error():
    with pytest.raises(ConfigError):
        parse_canonical_id("bad")
