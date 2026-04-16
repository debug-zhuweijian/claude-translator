from pathlib import Path
from unittest.mock import patch

from claude_translator.storage.cache import load_cache, save_cache, update_cache


def test_save_and_load(tmp_path: Path):
    td = tmp_path / "translations"
    td.mkdir()
    with patch("claude_translator.storage.paths.get_translations_dir", return_value=td):
        save_cache("zh-CN", {"plugin.a.skill:x": "翻译"})
        assert load_cache("zh-CN") == {"plugin.a.skill:x": "翻译"}


def test_load_empty(tmp_path: Path):
    td = tmp_path / "translations"
    td.mkdir()
    with patch("claude_translator.storage.paths.get_translations_dir", return_value=td):
        assert load_cache("ja") == {}


def test_update_cache_appends(tmp_path: Path):
    td = tmp_path / "translations"
    td.mkdir()
    with patch("claude_translator.storage.paths.get_translations_dir", return_value=td):
        update_cache("zh-CN", "plugin.a.skill:x", "翻译A")
        update_cache("zh-CN", "user.skill:y", "翻译B")
        assert load_cache("zh-CN") == {"plugin.a.skill:x": "翻译A", "user.skill:y": "翻译B"}


def test_update_cache_overwrites_existing(tmp_path: Path):
    td = tmp_path / "translations"
    td.mkdir()
    with patch("claude_translator.storage.paths.get_translations_dir", return_value=td):
        update_cache("zh-CN", "plugin.a.skill:x", "旧翻译")
        update_cache("zh-CN", "plugin.a.skill:x", "新翻译")
        assert load_cache("zh-CN") == {"plugin.a.skill:x": "新翻译"}
