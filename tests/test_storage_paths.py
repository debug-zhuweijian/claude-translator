from pathlib import Path

from claude_translator.storage.paths import (
    ensure_translations_dir,
    get_cache_path,
    get_claude_dir,
    get_config_path,
    get_overrides_path,
    get_translations_dir,
)


def test_get_claude_dir_default(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = get_claude_dir()
    assert result == tmp_path / ".claude"


def test_get_claude_dir_env_override(tmp_path: Path, monkeypatch):
    custom = tmp_path / "custom-claude"
    custom.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(custom))
    result = get_claude_dir()
    assert result == custom


def test_get_translations_dir(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = get_translations_dir()
    assert result == tmp_path / ".claude" / "translations"
    assert not result.exists()


def test_ensure_translations_dir(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = ensure_translations_dir()
    assert result == tmp_path / ".claude" / "translations"
    assert result.exists()


def test_get_overrides_path(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = get_overrides_path("zh-CN")
    assert result.name == "overrides-zh-CN.json"


def test_get_cache_path(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = get_cache_path("ja")
    assert result.name == "cache-ja.json"


def test_get_config_path(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    result = get_config_path()
    assert result.name == "config.json"
