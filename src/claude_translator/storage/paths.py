"""CLAUDE_CONFIG_DIR-aware path resolution."""

from __future__ import annotations

import os
from pathlib import Path


def get_claude_dir() -> Path:
    """Return the Claude config directory, respecting CLAUDE_CONFIG_DIR env."""
    env_path = os.getenv("CLAUDE_CONFIG_DIR")
    if env_path:
        return Path(env_path).expanduser()
    return Path.home() / ".claude"


def get_translations_dir() -> Path:
    """Return the translations directory path without creating it."""
    return get_claude_dir() / "translations"


def ensure_translations_dir() -> Path:
    """Create and return the translations directory."""
    translations_dir = get_translations_dir()
    translations_dir.mkdir(parents=True, exist_ok=True)
    return translations_dir


def get_overrides_path(lang: str) -> Path:
    """Return path to overrides-{lang}.json."""
    return get_translations_dir() / f"overrides-{lang}.json"


def get_cache_path(lang: str) -> Path:
    """Return path to cache-{lang}.json."""
    return get_translations_dir() / f"cache-{lang}.json"


def get_config_path() -> Path:
    """Return path to translations config.json."""
    return get_translations_dir() / "config.json"
