"""Path utility functions."""

from __future__ import annotations


def normalize_path(path: str) -> str:
    """Normalize path separators to forward slashes."""
    return path.replace("\\", "/")


def detect_newline(content: str) -> str:
    """Detect the newline style used in content. Defaults to LF."""
    if "\r\n" in content:
        return "\r\n"
    return "\n"
