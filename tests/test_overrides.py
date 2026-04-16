from pathlib import Path
from unittest.mock import patch

from claude_translator.storage.overrides import load_overrides, save_overrides


def test_save_and_load(tmp_path: Path):
    td = tmp_path / "translations"
    td.mkdir()
    with patch("claude_translator.storage.paths.get_translations_dir", return_value=td):
        save_overrides("zh-CN", {"plugin.a.skill:x": "翻译文本"})
        result = load_overrides("zh-CN")
    assert result == {"plugin.a.skill:x": "翻译文本"}


def test_load_empty(tmp_path: Path):
    td = tmp_path / "translations"
    td.mkdir()
    with patch("claude_translator.storage.paths.get_translations_dir", return_value=td):
        assert load_overrides("ja") == {}


def test_save_creates_file(tmp_path: Path):
    td = tmp_path / "translations"
    td.mkdir()
    with patch("claude_translator.storage.paths.get_translations_dir", return_value=td):
        save_overrides("ko", {"user.skill:test": "한국어"})
    assert (td / "overrides-ko.json").exists()


def test_multi_language_isolation(tmp_path: Path):
    td = tmp_path / "translations"
    td.mkdir()
    with patch("claude_translator.storage.paths.get_translations_dir", return_value=td):
        save_overrides("zh-CN", {"a": "中文"})
        save_overrides("ja", {"a": "日本語"})
        assert load_overrides("zh-CN") == {"a": "中文"}
        assert load_overrides("ja") == {"a": "日本語"}
