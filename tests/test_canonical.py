from claude_translator.core.canonical import generate_canonical_id, name_from_filename, parse_canonical_id


def test_generate_plugin_id():
    assert generate_canonical_id("skill", "brainstorm", "plugin", "superpowers") == "plugin.superpowers.skill:brainstorm"

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

def test_name_from_filename():
    assert name_from_filename("brainstorm.md") == "brainstorm"
    assert name_from_filename("SKILL.md") == "SKILL"
    assert name_from_filename("noext") == "noext"
