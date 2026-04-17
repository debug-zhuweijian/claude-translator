"""Canonical ID generation and parsing."""

from __future__ import annotations

from claude_translator.errors import ConfigError


def generate_canonical_id(kind: str, name: str, scope: str, plugin_key: str = "") -> str:
    if scope == "user":
        return f"user.{kind}:{name}"
    return f"plugin.{plugin_key}.{kind}:{name}"


def parse_canonical_id(cid: str) -> tuple[str, str, str, str]:
    """Parse a canonical ID into (scope, plugin_key, kind, name)."""
    if not cid:
        raise ConfigError("Canonical ID cannot be empty")

    if cid.startswith("user."):
        rest = cid[5:]
        if ":" not in rest:
            raise ConfigError(f"Invalid user canonical ID: {cid!r}")
        kind, name = rest.split(":", 1)
        return "user", "", kind, name

    if not cid.startswith("plugin."):
        raise ConfigError(f"Unknown canonical ID format: {cid!r}")

    without_prefix = cid[7:]  # strip "plugin."
    if "." not in without_prefix or ":" not in without_prefix:
        raise ConfigError(f"Invalid plugin canonical ID: {cid!r}")
    key_and_rest = without_prefix.split(".", 1)
    plugin_key = key_and_rest[0]
    kind, name = key_and_rest[1].split(":", 1)
    return "plugin", plugin_key, kind, name


def name_from_filename(filename: str) -> str:
    if filename.endswith(".md"):
        return filename[:-3]
    return filename
