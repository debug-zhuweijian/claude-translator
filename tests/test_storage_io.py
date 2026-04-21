from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

import claude_translator.storage._io as io_module
from claude_translator.storage._io import atomic_write_text


def test_atomic_write_text_writes_content(tmp_path: Path):
    path = tmp_path / "cache.json"

    atomic_write_text(path, '{"a":"b"}\n')

    assert path.read_text(encoding="utf-8") == '{"a":"b"}\n'
    assert list(tmp_path.glob("*.tmp")) == []


def test_atomic_write_text_cleans_temp_file_when_fdopen_fails(tmp_path: Path, monkeypatch):
    fd, temp_path = tempfile.mkstemp(dir=tmp_path, prefix="cache.json.", suffix=".tmp")
    monkeypatch.setattr(io_module.tempfile, "mkstemp", lambda **kwargs: (fd, temp_path))

    close_calls: list[int] = []
    real_close = io_module.os.close

    def _spy_close(handle: int) -> None:
        close_calls.append(handle)
        real_close(handle)

    monkeypatch.setattr(io_module.os, "close", _spy_close)
    monkeypatch.setattr(
        io_module.os,
        "fdopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("fdopen failed")),
    )

    with pytest.raises(OSError, match="fdopen failed"):
        atomic_write_text(tmp_path / "cache.json", "content")

    assert close_calls == [fd]
    assert not Path(temp_path).exists()


def test_atomic_write_text_cleans_temp_file_when_replace_fails(tmp_path: Path, monkeypatch):
    real_replace = io_module.Path.replace

    def _failing_replace(self: Path, target: Path) -> Path:
        if self.parent == tmp_path and self.name.endswith(".tmp"):
            raise OSError("replace failed")
        return real_replace(self, target)

    monkeypatch.setattr(io_module.Path, "replace", _failing_replace)

    with pytest.raises(OSError, match="replace failed"):
        atomic_write_text(tmp_path / "cache.json", "content")

    assert list(tmp_path.glob("*.tmp")) == []
