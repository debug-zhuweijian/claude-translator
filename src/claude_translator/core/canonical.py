"""Canonical ID generation and parsing."""

from __future__ import annotations


def generate_canonical_id(
    kind: str, name: str, scope: str, plugin_key: str = ""
) -> str:
    if scope == "user":
        return f"user.{kind}:{name}"
    return f"plugin.{plugin_key}.{kind}:{name}"


def parse_canonical_id(cid: str) -> tuple[str, str, str, str]:
    """Parse a canonical ID into (scope, plugin_key, kind, name)."""
    if cid.startswith("user."):
        rest = cid[5:]
        kind, name = rest.split(":", 1)
        return "user", "", kind, name
    without_prefix = cid[7:]  # strip "plugin."
    key_and_rest = without_prefix.split(".", 1)
    plugin_key = key_and_rest[0]
    kind, name = key_and_rest[1].split(":", 1)
    return "plugin", plugin_key, kind, name


def name_from_filename(filename: str) -> str:
    if filename.endswith(".md"):
        return filename[:-3]
    return filename
