from dataclasses import FrozenInstanceError

from claude_translator.core.models import Inventory, Record, TranslationMapping


def test_record_is_frozen():
    r = Record(
        canonical_id="plugin.superpowers.skill:brainstorm",
        kind="skill",
        scope="plugin",
        source_path="/path/to/file.md",
        relative_path="skills/brainstorm/SKILL.md",
    )
    try:
        r.canonical_id = "changed"  # type: ignore[misc]
        assert False, "Should raise FrozenInstanceError"
    except FrozenInstanceError:
        pass


def test_record_defaults():
    r = Record(
        canonical_id="user.skill:test",
        kind="skill",
        scope="user",
        source_path="/path",
        relative_path="test.md",
    )
    assert r.plugin_key == ""
    assert r.current_description == ""
    assert r.status == ""
    assert r.matched_translation == ""
    assert r.frontmatter_present is True


def test_inventory_find_by_canonical_id():
    r1 = Record("plugin.a.skill:x", "skill", "plugin", "/a", "a.md", plugin_key="a")
    r2 = Record("user.skill:y", "skill", "user", "/b", "b.md")
    inv = Inventory((r1, r2))
    assert inv.find_by_canonical_id("plugin.a.skill:x") is r1
    assert inv.find_by_canonical_id("user.skill:y") is r2
    assert inv.find_by_canonical_id("nonexistent") is None


def test_inventory_size():
    inv = Inventory(tuple(
        Record(f"plugin.a.skill:{i}", "skill", "plugin", f"/{i}", f"{i}.md")
        for i in range(5)
    ))
    assert inv.size() == 5


def test_translation_mapping():
    m = TranslationMapping(
        canonical_id="plugin.a.skill:x",
        source_text="Hello",
        translated_text="你好",
        source_lang="en",
        target_lang="zh-CN",
    )
    assert m.translated_text == "你好"
