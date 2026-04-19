"""Claude Description Translator — multi-language plugin description translator."""

import re
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path

_VERSION_RE = re.compile(r'^version\s*=\s*"([^"]+)"\s*$', re.MULTILINE)


def _read_local_version() -> str | None:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if not pyproject.exists():
        return None
    match = _VERSION_RE.search(pyproject.read_text(encoding="utf-8"))
    return match.group(1) if match else None


_LOCAL_VERSION = _read_local_version()

if _LOCAL_VERSION is not None:
    __version__ = _LOCAL_VERSION
else:
    try:
        __version__ = _pkg_version("claude-translator")
    except PackageNotFoundError:
        __version__ = "0.3.0"
