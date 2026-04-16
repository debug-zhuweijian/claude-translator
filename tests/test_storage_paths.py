import os
from pathlib import Path
from unittest.mock import patch

from claude_translator.storage.paths import (
    get_cache_path,
    get_claude_dir,
    get_config_path,
    get_overrides_path,
    get_translations_dir,
)


def test_get_claude_dir_default(tmp_path: Path):
    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = get_claude_dir()
    assert result == tmp_path / ".claude"


def test_get_claude_dir_env_override(tmp_path: Path):
    custom = tmp_path / "custom-claude"
    custom.mkdir()
    with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(custom)}):
        result = get_claude_dir()
    assert result == custom


def test_get_translations_dir(tmp_path: Path):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = get_translations_dir()
    assert result == claude_dir / "translations"
    assert result.exists()


def test_get_overrides_path(tmp_path: Path):
    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = get_overrides_path("zh-CN")
    assert result.name == "overrides-zh-CN.json"


def test_get_cache_path(tmp_path: Path):
    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = get_cache_path("ja")
    assert result.name == "cache-ja.json"


def test_get_config_path(tmp_path: Path):
    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = get_config_path()
    assert result.name == "config.json"
