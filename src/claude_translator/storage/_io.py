"""Shared filesystem helpers for storage modules."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, content: str) -> None:
    """Write text atomically by replacing the target with a temp file."""
    fd, temp_path = tempfile.mkstemp(dir=path.parent, prefix=f"{path.name}.", suffix=".tmp")
    temp = Path(temp_path)

    try:
        try:
            handle = os.fdopen(fd, "w", encoding="utf-8", newline="")
        except Exception:
            os.close(fd)
            raise

        with handle:
            handle.write(content)

        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()
