"""Tests for legacy data migration."""

import json
from pathlib import Path

from claude_translator.core.migration import migrate_legacy


def test_migrate_overrides_flat(tmp_path: Path):
    """descriptions-overrides.json (flat, compatible keys) → overrides-zh-CN.json."""
    legacy = {"plugin.foo.skill:bar": "翻译1", "plugin.baz.command:qux": "翻译2"}
    (tmp_path / "descriptions-overrides.json").write_text(
        json.dumps(legacy, ensure_ascii=False), encoding="utf-8"
    )

    migrate_legacy(tmp_path, "zh-CN")

    new_file = tmp_path / "overrides-zh-CN.json"
    assert new_file.exists()
    data = json.loads(new_file.read_text(encoding="utf-8"))
    assert data == legacy


def test_migrate_skip_if_new_exists(tmp_path: Path):
    """新版文件已存在时不覆盖."""
    new_data = {"plugin.foo.skill:bar": "新翻译"}
    (tmp_path / "overrides-zh-CN.json").write_text(
        json.dumps(new_data, ensure_ascii=False), encoding="utf-8"
    )
    legacy = {"plugin.foo.skill:bar": "旧翻译"}
    (tmp_path / "descriptions-overrides.json").write_text(
        json.dumps(legacy, ensure_ascii=False), encoding="utf-8"
    )

    migrate_legacy(tmp_path, "zh-CN")

    data = json.loads((tmp_path / "overrides-zh-CN.json").read_text(encoding="utf-8"))
    assert data == new_data  # 不被旧版覆盖


def test_migrate_no_legacy_files(tmp_path: Path):
    """无旧版文件时不崩溃，不创建任何文件."""
    migrate_legacy(tmp_path, "zh-CN")
    assert not (tmp_path / "overrides-zh-CN.json").exists()


def test_migrate_corrupted_legacy_json(tmp_path: Path):
    """损坏的旧版 JSON 不崩溃，跳过迁移."""
    (tmp_path / "descriptions-overrides.json").write_text("{invalid json", encoding="utf-8")

    migrate_legacy(tmp_path, "zh-CN")
    assert not (tmp_path / "overrides-zh-CN.json").exists()
