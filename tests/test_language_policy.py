from claude_translator.core.language_policy import (
    check_description_language,
    check_inventory_language,
)
from claude_translator.core.models import Inventory, Record


def _record(description: str, canonical_id: str = "user.skill:test") -> Record:
    return Record(
        canonical_id=canonical_id,
        kind="skill",
        scope="user",
        source_path="/tmp/test.md",
        relative_path="test/SKILL.md",
        current_description=description,
    )


def test_strict_zh_cn_accepts_chinese_with_allowed_technical_tokens():
    record = _record("用于 Claude Code 的 API 配置检查，支持 JSON 输出。")

    assert check_description_language(record, "zh-CN") == ()


def test_strict_zh_cn_accepts_chinese_with_short_product_name():
    record = _record("使用 Cursor 编辑代码")

    assert check_description_language(record, "zh-CN") == ()


def test_strict_ja_and_ko_locale_variants_detect_expected_script():
    assert check_description_language(_record("日本語の説明"), "ja-JP") == ()
    assert check_description_language(_record("한국어 설명"), "ko-KR") == ()

    assert check_description_language(_record("English only"), "ja-JP")[0].reason == "english_only"
    assert check_description_language(_record("English only"), "ko-KR")[0].reason == "english_only"


def test_strict_zh_cn_rejects_empty_description():
    violations = check_description_language(_record(""), "zh-CN")

    assert len(violations) == 1
    assert violations[0].reason == "empty"


def test_strict_zh_cn_rejects_english_only_description():
    violations = check_description_language(
        _record("Prepare Nature-ready data availability statements."), "zh-CN"
    )

    assert len(violations) == 1
    assert violations[0].reason == "english_only"


def test_strict_zh_cn_rejects_english_sentence_residue_after_chinese():
    violations = check_description_language(
        _record("为稿件准备数据可用性声明。 Prepare Nature-ready statements."), "zh-CN"
    )

    assert len(violations) == 1
    assert violations[0].reason == "english_sentence_residue"


def test_strict_zh_cn_rejects_english_heavy_description_with_cjk_triggers():
    violations = check_description_language(
        _record(
            "12-agent academic paper writing pipeline. 10 modes "
            "(full/plan/outline/revision). Triggers: write paper, "
            "academic paper, 寫論文, 學術論文."
        ),
        "zh-CN",
    )

    assert len(violations) == 1
    assert violations[0].reason == "english_text_residue"


def test_strict_zh_cn_accepts_slash_commands_and_trigger_phrases():
    record = _record(
        "PUA KPI 报告卡 — 生成段位和绩效报告。/pua:kpi。"
        "触发关键词：'/pua:kpi'、'pua kpi'、'performance report'、'generate kpi'。"
    )

    assert check_description_language(record, "zh-CN") == ()


def test_strict_zh_cn_accepts_command_usage_and_long_trigger_list():
    record = _record(
        "PUA 我们不养闲Agent。"
        "/pua:pua [p7|p9|p10|pro|yes|mama|loop|on|off|kpi|survey|flavor|任务描述]，"
        "或直接子命令 /pua:p7 /pua:p9 /pua:p10 /pua:pro /pua:yes /pua:mama "
        "/pua:pua-loop /pua:on /pua:off /pua:kpi /pua:survey /pua:flavor "
        "/pua:cancel-pua-loop。"
        "触发关键词：'/pua:pua'、'/pua:pua yes'、'/pua:pua mama'、"
        "'/pua:pua p7'、'pua yes'、'pua p7'、'pua mama'。"
    )

    assert check_description_language(record, "zh-CN") == ()


def test_strict_zh_cn_still_rejects_english_before_trigger_list():
    violations = check_description_language(
        _record(
            "12-agent academic paper writing pipeline. 10 modes. "
            "触发关键词：'/academic-paper'、'write paper'、'academic paper'。"
        ),
        "zh-CN",
    )

    assert len(violations) == 1
    assert violations[0].reason == "english_text_residue"


def test_check_inventory_language_reports_each_bad_record():
    inventory = Inventory(
        (
            _record("中文说明", "user.skill:ok"),
            _record("English only", "user.skill:bad"),
            _record("", "user.skill:empty"),
        )
    )

    violations = check_inventory_language(inventory, "zh-CN")

    assert [violation.canonical_id for violation in violations] == [
        "user.skill:bad",
        "user.skill:empty",
    ]
