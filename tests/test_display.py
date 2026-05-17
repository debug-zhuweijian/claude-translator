from claude_translator.core.display import (
    DisplayKey,
    display_key_for_record,
    find_duplicate_display_groups,
    group_by_display_key,
)
from claude_translator.core.models import Record


def _record(canonical_id: str, *, kind: str = "skill", scope: str = "user") -> Record:
    return Record(
        canonical_id=canonical_id,
        kind=kind,
        scope=scope,
        source_path=f"/tmp/{canonical_id}.md",
        relative_path="entry.md",
        current_description="描述文本",
    )


def test_display_key_uses_visible_kind_and_name_not_canonical_scope():
    user_record = _record("user.skill:nature-data", scope="user")
    plugin_record = _record("plugin.nature-skills.skill:nature-data", scope="plugin")

    assert display_key_for_record(user_record) == DisplayKey(kind="skill", name="nature-data")
    assert display_key_for_record(plugin_record) == DisplayKey(kind="skill", name="nature-data")


def test_group_by_display_key_keeps_different_kinds_separate():
    skill = _record("user.skill:deploy", kind="skill")
    command = _record("user.command:deploy", kind="command")

    groups = group_by_display_key((skill, command))

    assert set(groups) == {
        DisplayKey(kind="skill", name="deploy"),
        DisplayKey(kind="command", name="deploy"),
    }


def test_find_duplicate_display_groups_reports_all_visible_duplicates():
    user_record = _record("user.skill:nature-data", scope="user")
    plugin_record = _record("plugin.nature-skills.skill:nature-data", scope="plugin")
    other = _record("plugin.other.skill:nature-figure", scope="plugin")

    duplicates = find_duplicate_display_groups((user_record, plugin_record, other))

    assert len(duplicates) == 1
    group = duplicates[0]
    assert group.display_key == DisplayKey(kind="skill", name="nature-data")
    assert group.records == (user_record, plugin_record)
