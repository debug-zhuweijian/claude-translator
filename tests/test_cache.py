import json
from pathlib import Path
from unittest.mock import patch

import pytest

import claude_translator.storage.cache as cache_module
from claude_translator.errors import FileSystemError
from claude_translator.storage.cache import load_cache, save_cache, update_cache


def _patch_cache_paths(monkeypatch, translations_dir: Path) -> None:
    monkeypatch.setattr(
        cache_module,
        "get_cache_path",
        lambda lang: translations_dir / f"cache-{lang}.json",
    )
    monkeypatch.setattr(cache_module, "ensure_translations_dir", lambda: translations_dir)


def test_save_and_load(tmp_path: Path, monkeypatch):
    td = tmp_path / "translations"
    td.mkdir()
    _patch_cache_paths(monkeypatch, td)
    save_cache("zh-CN", {"plugin.a.skill:x": "翻译"})
    assert load_cache("zh-CN") == {"plugin.a.skill:x": "翻译"}


def test_load_empty(tmp_path: Path, monkeypatch):
    td = tmp_path / "translations"
    td.mkdir()
    _patch_cache_paths(monkeypatch, td)
    assert load_cache("ja") == {}


def test_update_cache_appends(tmp_path: Path, monkeypatch):
    td = tmp_path / "translations"
    td.mkdir()
    _patch_cache_paths(monkeypatch, td)
    update_cache("zh-CN", "plugin.a.skill:x", "翻译A")
    update_cache("zh-CN", "user.skill:y", "翻译B")
    assert load_cache("zh-CN") == {"plugin.a.skill:x": "翻译A", "user.skill:y": "翻译B"}


def test_update_cache_overwrites_existing(tmp_path: Path, monkeypatch):
    td = tmp_path / "translations"
    td.mkdir()
    _patch_cache_paths(monkeypatch, td)
    update_cache("zh-CN", "plugin.a.skill:x", "旧翻译")
    update_cache("zh-CN", "plugin.a.skill:x", "新翻译")
    assert load_cache("zh-CN") == {"plugin.a.skill:x": "新翻译"}


def test_load_corrupted_json(tmp_path: Path, monkeypatch):
    """T11: Corrupted JSON returns empty dict, no crash."""
    td = tmp_path / "translations"
    td.mkdir()
    bad_file = td / "cache-zh-CN.json"
    bad_file.write_text("not json at all", encoding="utf-8")
    _patch_cache_paths(monkeypatch, td)
    result = load_cache("zh-CN")
    assert result == {}


def test_save_cache_permission_error(tmp_path: Path, monkeypatch):
    """OSError during atomic write is converted to FileSystemError."""
    td = tmp_path / "translations"
    td.mkdir()
    _patch_cache_paths(monkeypatch, td)
    with patch(
        "claude_translator.storage.cache.atomic_write_text",
        side_effect=PermissionError("denied"),
    ):
        with pytest.raises(FileSystemError, match="Cannot write"):
            save_cache("zh-CN", {"a": "b"})


def test_cache_schema_version_written(tmp_path: Path, monkeypatch):
    """Saved cache includes _schema_version."""
    td = tmp_path / "translations"
    td.mkdir()
    _patch_cache_paths(monkeypatch, td)
    save_cache("zh-CN", {"a": "b"})
    raw = json.loads((td / "cache-zh-CN.json").read_text(encoding="utf-8"))
    assert raw["_schema_version"] == 1
    assert raw["a"] == "b"


def test_cache_schema_version_not_in_loaded_data(tmp_path: Path, monkeypatch):
    """load_cache strips _schema_version from returned dict."""
    td = tmp_path / "translations"
    td.mkdir()
    _patch_cache_paths(monkeypatch, td)
    save_cache("zh-CN", {"a": "b"})
    result = load_cache("zh-CN")
    assert "_schema_version" not in result
    assert result == {"a": "b"}


def test_cache_schema_mismatch_rebuilds(tmp_path: Path, monkeypatch):
    """Schema mismatch triggers rebuild (returns empty dict)."""
    td = tmp_path / "translations"
    td.mkdir()
    bad_file = td / "cache-zh-CN.json"
    bad_file.write_text('{"_schema_version": 99, "a": "b"}', encoding="utf-8")
    _patch_cache_paths(monkeypatch, td)
    result = load_cache("zh-CN")
    assert result == {}


def test_cache_no_schema_version_rebuilds(tmp_path: Path, monkeypatch):
    """Missing schema version triggers rebuild."""
    td = tmp_path / "translations"
    td.mkdir()
    old_file = td / "cache-zh-CN.json"
    old_file.write_text('{"a": "b"}', encoding="utf-8")
    _patch_cache_paths(monkeypatch, td)
    result = load_cache("zh-CN")
    assert result == {}
