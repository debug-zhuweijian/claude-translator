from pathlib import Path
from unittest.mock import patch

import pytest

import claude_translator.storage.overrides as overrides_module
from claude_translator.errors import FileSystemError
from claude_translator.storage.overrides import load_overrides, save_overrides


def _patch_override_paths(monkeypatch, translations_dir: Path) -> None:
    monkeypatch.setattr(
        overrides_module,
        "get_overrides_path",
        lambda lang: translations_dir / f"overrides-{lang}.json",
    )
    monkeypatch.setattr(overrides_module, "ensure_translations_dir", lambda: translations_dir)


def test_save_and_load(tmp_path: Path, monkeypatch):
    td = tmp_path / "translations"
    td.mkdir()
    _patch_override_paths(monkeypatch, td)
    save_overrides("zh-CN", {"plugin.a.skill:x": "翻译文本"})
    result = load_overrides("zh-CN")
    assert result == {"plugin.a.skill:x": "翻译文本"}


def test_load_empty(tmp_path: Path, monkeypatch):
    td = tmp_path / "translations"
    td.mkdir()
    _patch_override_paths(monkeypatch, td)
    assert load_overrides("ja") == {}


def test_save_creates_file(tmp_path: Path, monkeypatch):
    td = tmp_path / "translations"
    td.mkdir()
    _patch_override_paths(monkeypatch, td)
    save_overrides("ko", {"user.skill:test": "한국어"})
    assert (td / "overrides-ko.json").exists()


def test_multi_language_isolation(tmp_path: Path, monkeypatch):
    td = tmp_path / "translations"
    td.mkdir()
    _patch_override_paths(monkeypatch, td)
    save_overrides("zh-CN", {"a": "中文"})
    save_overrides("ja", {"a": "日本語"})
    assert load_overrides("zh-CN") == {"a": "中文"}
    assert load_overrides("ja") == {"a": "日本語"}


def test_load_corrupted_json(tmp_path: Path, monkeypatch):
    """T11: Corrupted JSON returns empty dict, no crash."""
    td = tmp_path / "translations"
    td.mkdir()
    bad_file = td / "overrides-zh-CN.json"
    bad_file.write_text("{invalid json content!!!", encoding="utf-8")
    _patch_override_paths(monkeypatch, td)
    result = load_overrides("zh-CN")
    assert result == {}


def test_save_overrides_permission_error(tmp_path: Path, monkeypatch):
    """OSError during atomic write is converted to FileSystemError."""
    td = tmp_path / "translations"
    td.mkdir()
    _patch_override_paths(monkeypatch, td)
    with patch("claude_translator.storage.overrides._atomic_write_text", side_effect=PermissionError("denied")):
        with pytest.raises(FileSystemError, match="Cannot write"):
            save_overrides("zh-CN", {"a": "b"})
