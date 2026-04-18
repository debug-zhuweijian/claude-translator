# Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all P1-P6 code review issues (P5 and P7 already fixed) plus 4 nice-to-have improvements for claude-translator.

**Architecture:** Per-issue fix with independent verification. Each task modifies 1-2 files, adds tests, and commits independently.

**Tech Stack:** Python 3.10+, pytest, Click, ruamel.yaml, ruff

**Project root:** `I:\claude-docs\my-project\claude-translator\`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `.github/workflows/ci.yml` | Modify | Add pytest step |
| `src/claude_translator/core/canonical.py:29-35` | Modify | Fix rsplit for dotted keys |
| `tests/test_canonical.py` | Modify | Add round-trip test for dotted keys |
| `src/claude_translator/__init__.py:17-25` | Modify | Simplify version reading |
| `src/claude_translator/errors.py` | Modify | Add FileSystemError |
| `src/claude_translator/storage/cache.py:22-24` | Modify | Wrap OSError |
| `src/claude_translator/storage/overrides.py:21-23` | Modify | Wrap OSError |
| `tests/test_cache.py` | Modify | Add permission error test |
| `tests/test_overrides.py` | Modify | Add permission error test |
| `src/claude_translator/lang/cleaner.py:35-36` | Modify | Merge newlines instead of reject |
| `tests/test_cleaner.py:15-17` | Modify | Update multiline test + add new tests |
| `README.md` | Modify | Add config.toml example |
| `pyproject.toml` | Modify | Add project.urls + version bump |
| `src/claude_translator/cli.py:33-37` | Modify | Add --verbose/--quiet |
| `src/claude_translator/storage/cache.py:12-19,22-24` | Modify | Add schema version |

---

## Task 1: P1 — CI Add pytest

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Update ci.yml to install dev extras and run pytest**

Replace the existing install step and add test steps. The final file should be:

```yaml
name: CI

on:
  push:
    branches:
      - main
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"

      - name: Run Ruff check
        run: python -m ruff check src/

      - name: Run Ruff format check
        run: python -m ruff format --check src/

  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install project with dev extras
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"

      - name: Run tests
        run: pytest
```

Key changes:
- Changed `pip install -e .` to `pip install -e ".[dev]"` in the lint job (installs pytest, pyfakefs, ruff)
- Added a new `test` job that installs dev extras and runs `pytest`

- [ ] **Step 2: Verify locally**

Run: `cd I:\claude-docs\my-project\claude-translator && pip install -e ".[dev]" && pytest -q`
Expected: All 126+ tests pass

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add pytest job to CI workflow"
```

---

## Task 2: P2 — Canonical round-trip fix for dotted plugin keys

**Files:**
- Modify: `src/claude_translator/core/canonical.py:29-35`
- Modify: `tests/test_canonical.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_canonical.py` after the existing `test_roundtrip` function:

```python
def test_roundtrip_dotted_plugin_key():
    """Dotted plugin keys like 'pua.skills' must survive round-trip."""
    cid = generate_canonical_id("skill", "foo", "plugin", "pua.skills")
    assert cid == "plugin.pua.skills.skill:foo"
    scope, pk, kind, name = parse_canonical_id(cid)
    assert (scope, pk, kind, name) == ("plugin", "pua.skills", "skill", "foo")


def test_roundtrip_deeply_nested_plugin_key():
    """Multi-dot plugin keys like 'compound-engineering.context7'."""
    cid = generate_canonical_id("skill", "bar", "plugin", "compound-engineering.context7")
    assert cid == "plugin.compound-engineering.context7.skill:bar"
    scope, pk, kind, name = parse_canonical_id(cid)
    assert (scope, pk, kind, name) == ("plugin", "compound-engineering.context7", "skill", "bar")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd I:\claude-docs\my-project\claude-translator && python -m pytest tests/test_canonical.py::test_roundtrip_dotted_plugin_key -v`
Expected: FAIL — `parse_canonical_id` returns `("plugin", "pua", "skills.skill", "foo")` instead of `("plugin", "pua.skills", "skill", "foo")`

- [ ] **Step 3: Fix `parse_canonical_id` in `src/claude_translator/core/canonical.py`**

Replace lines 29-35 (the plugin branch of `parse_canonical_id`):

```python
    without_prefix = cid[7:]  # strip "plugin."
    if ":" not in without_prefix:
        raise ConfigError(f"Invalid plugin canonical ID: {cid!r}")
    key_and_kind, name = without_prefix.rsplit(":", 1)
    if "." not in key_and_kind:
        raise ConfigError(f"Invalid plugin canonical ID: {cid!r}")
    plugin_key, kind = key_and_kind.rsplit(".", 1)
    return "plugin", plugin_key, kind, name
```

The key change: use `rsplit` from the right instead of `split(".", 1)` from the left. This lets the `plugin_key` portion contain dots.

- [ ] **Step 4: Run all canonical tests**

Run: `cd I:\claude-docs\my-project\claude-translator && python -m pytest tests/test_canonical.py -v`
Expected: ALL PASS (including the two new round-trip tests)

- [ ] **Step 5: Commit**

```bash
git add src/claude_translator/core/canonical.py tests/test_canonical.py
git commit -m "fix: parse_canonical_id handles dotted plugin keys correctly"
```

---

## Task 3: P3 — Version reading simplification

**Files:**
- Modify: `src/claude_translator/__init__.py`

- [ ] **Step 1: Simplify `__init__.py`**

Replace the entire file content:

```python
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


try:
    __version__ = _pkg_version("claude-translator")
except PackageNotFoundError:
    __version__ = _read_local_version() or "0.2.0"
```

Changes from current:
- Removed `_local_version` module-level variable
- Removed `else` branch that preferred local file over metadata
- `_read_local_version()` is only called on `PackageNotFoundError` (when not installed)

- [ ] **Step 2: Verify version is still readable**

Run: `cd I:\claude-docs\my-project\claude-translator && python -c "from claude_translator import __version__; print(__version__)"`
Expected: `0.2.0`

- [ ] **Step 3: Run full test suite**

Run: `cd I:\claude-docs\my-project\claude-translator && python -m pytest -q`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add src/claude_translator/__init__.py
git commit -m "refactor: simplify version reading to prefer importlib.metadata"
```

---

## Task 4: P4 — Atomic write OSError handling

**Files:**
- Modify: `src/claude_translator/errors.py`
- Modify: `src/claude_translator/storage/cache.py:22-24`
- Modify: `src/claude_translator/storage/overrides.py:21-23`
- Modify: `tests/test_cache.py`
- Modify: `tests/test_overrides.py`

- [ ] **Step 1: Add `FileSystemError` to `src/claude_translator/errors.py`**

Add after the `PathError` class (line 18):

```python
class FileSystemError(UserError):
    """File system operation failed (permissions, disk, etc.)."""
```

- [ ] **Step 2: Write failing test for cache permission error**

Add to `tests/test_cache.py`:

```python
from unittest.mock import patch
from claude_translator.errors import FileSystemError


def test_save_cache_permission_error(tmp_path: Path, monkeypatch):
    """OSError during atomic write is converted to FileSystemError."""
    td = tmp_path / "translations"
    td.mkdir()
    _patch_cache_paths(monkeypatch, td)
    with patch("claude_translator.storage.cache._atomic_write_text", side_effect=PermissionError("denied")):
        with pytest.raises(FileSystemError, match="Cannot write"):
            save_cache("zh-CN", {"a": "b"})
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd I:\claude-docs\my-project\claude-translator && python -m pytest tests/test_cache.py::test_save_cache_permission_error -v`
Expected: FAIL — `PermissionError` is not caught

- [ ] **Step 4: Fix `save_cache` in `src/claude_translator/storage/cache.py`**

Add import at the top (after existing imports):

```python
from claude_translator.errors import FileSystemError
```

Replace `save_cache` function (lines 22-24):

```python
def save_cache(lang: str, mapping: dict[str, str]) -> None:
    path = ensure_translations_dir() / f"cache-{lang}.json"
    try:
        _atomic_write_text(path, json.dumps(mapping, ensure_ascii=False, indent=2) + "\n")
    except OSError as e:
        raise FileSystemError(f"Cannot write to {path}: {e}") from e
```

- [ ] **Step 5: Fix `save_overrides` in `src/claude_translator/storage/overrides.py`**

Add import (after existing imports):

```python
from claude_translator.errors import FileSystemError
```

Replace `save_overrides` function (lines 21-23):

```python
def save_overrides(lang: str, mapping: dict[str, str]) -> None:
    path = ensure_translations_dir() / f"overrides-{lang}.json"
    try:
        _atomic_write_text(path, json.dumps(mapping, ensure_ascii=False, indent=2) + "\n")
    except OSError as e:
        raise FileSystemError(f"Cannot write to {path}: {e}") from e
```

- [ ] **Step 6: Add test for overrides permission error**

Add to `tests/test_overrides.py`:

```python
from unittest.mock import patch
from claude_translator.errors import FileSystemError


def test_save_overrides_permission_error(tmp_path: Path, monkeypatch):
    """OSError during atomic write is converted to FileSystemError."""
    td = tmp_path / "translations"
    td.mkdir()
    _patch_override_paths(monkeypatch, td)
    with patch("claude_translator.storage.overrides._atomic_write_text", side_effect=PermissionError("denied")):
        with pytest.raises(FileSystemError, match="Cannot write"):
            save_overrides("zh-CN", {"a": "b"})
```

- [ ] **Step 7: Run all affected tests**

Run: `cd I:\claude-docs\my-project\claude-translator && python -m pytest tests/test_cache.py tests/test_overrides.py -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add src/claude_translator/errors.py src/claude_translator/storage/cache.py src/claude_translator/storage/overrides.py tests/test_cache.py tests/test_overrides.py
git commit -m "fix: convert OSError to FileSystemError in atomic writes"
```

---

## Task 5: P6 — Cleaner newline merging

**Files:**
- Modify: `src/claude_translator/lang/cleaner.py:35-36`
- Modify: `tests/test_cleaner.py:15-17`

- [ ] **Step 1: Update `cleaner.py` to merge newlines**

In `src/claude_translator/lang/cleaner.py`, replace the `clean` method body. The full updated method:

```python
    def clean(self, text: str) -> str:
        result = text.strip()

        for _ in range(2):
            result = self._strip_paired_quotes(result)

        result = _PREFIX_RE.sub("", result).strip()

        if not result:
            raise TranslatorError("LLM returned an empty translation")
        # Merge internal newlines to spaces (some languages use compound sentences)
        result = re.sub(r"\s*[\r\n]+\s*", " ", result).strip()
        if "---" in result:
            raise TranslatorError("LLM returned content that would break frontmatter")

        return result
```

Key change: the `if "\n" in result or "\r" in result` check is replaced with `re.sub` that merges newlines to spaces. The `---` rejection remains.

- [ ] **Step 2: Update `test_cleaner_rejects_multiline_output` test**

In `tests/test_cleaner.py`, replace the existing test:

```python
def test_cleaner_merges_multiline_output():
    """Internal newlines are merged to spaces."""
    assert clean_llm_response("line one\nline two") == "line one line two"


def test_cleaner_merges_multiple_newlines():
    """Multiple consecutive newlines collapse to a single space."""
    assert clean_llm_response("line one\n\n\nline two") == "line one line two"


def test_cleaner_merges_carriage_returns():
    """CRLF is also merged."""
    assert clean_llm_response("line one\r\nline two") == "line one line two"
```

Note: The old `test_cleaner_rejects_multiline_output` is completely replaced by the three new tests above.

- [ ] **Step 3: Run cleaner tests**

Run: `cd I:\claude-docs\my-project\claude-translator && python -m pytest tests/test_cleaner.py -v`
Expected: ALL PASS (5 tests: strips_quotes, strips_prefix, merges_multiline, merges_multiple, rejects_frontmatter_boundary)

- [ ] **Step 4: Run full test suite**

Run: `cd I:\claude-docs\my-project\claude-translator && python -m pytest -q`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add src/claude_translator/lang/cleaner.py tests/test_cleaner.py
git commit -m "fix: merge LLM response newlines to spaces instead of rejecting"
```

---

## Task 6: Nice-1 — README config.toml example

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add config.toml example to README**

In `README.md`, after the "Config Cascade" section (after line 298 "```"), add:

`````markdown

### Example Configuration

`~/.claude/translations/config.json`:

```json
{
  "target_lang": "zh-CN",
  "llm": {
    "model": "gpt-4o-mini",
    "base_url": "https://api.openai.com/v1",
    "api_key": null
  },
  "plugins_dirs": []
}
```

Key options:
- `target_lang`: Target language code (e.g., `zh-CN`, `ja`, `ko`)
- `llm.model`: Any OpenAI-compatible model name
- `llm.base_url`: Set to use local models (Ollama, vLLM, etc.)
- `llm.api_key`: Leave `null` to use `OPENAI_API_KEY` environment variable
`````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add example config.json to README"
```

---

## Task 7: Nice-2 — pyproject.toml project URLs

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add `[project.urls]` section**

Add after line 8 (`description = "Multi-language plugin description translator for Claude Code"`):

```toml

[project.urls]
Homepage = "https://github.com/debug-zhuweijian/claude-translator"
Repository = "https://github.com/debug-zhuweijian/claude-translator"
Issues = "https://github.com/debug-zhuweijian/claude-translator/issues"
```

- [ ] **Step 2: Verify project metadata**

Run: `cd I:\claude-docs\my-project\claude-translator && python -c "from importlib.metadata import metadata; m = metadata('claude-translator'); print(m.get('Home-page', 'N/A'))"`
Expected: Shows the homepage URL (after reinstall)

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "docs: add project URLs to pyproject.toml"
```

---

## Task 8: Nice-3 — CLI log level switches

**Files:**
- Modify: `src/claude_translator/cli.py:33-37`

- [ ] **Step 1: Add verbose/quiet options to main group**

Add import for `_configure_logging` helper. Replace lines 33-37 in `src/claude_translator/cli.py`:

```python
def _configure_logging(verbose: int, quiet: int) -> None:
    """Map -v/-q flags to logging levels."""
    level = logging.INFO - 10 * verbose + 10 * quiet
    level = max(logging.DEBUG, min(logging.CRITICAL, level))
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


@click.group()
@click.version_option(version=__version__)
@click.option("-v", "--verbose", count=True, help="Increase verbosity")
@click.option("-q", "--quiet", count=True, help="Decrease verbosity")
def main(verbose: int, quiet: int) -> None:
    """Claude Description Translator — multi-language plugin description translator."""
    _configure_logging(verbose, quiet)
```

Changes:
- New `_configure_logging` helper maps `-v`/`-q` to logging levels
- `main` group now accepts `--verbose` and `--quiet` count options
- Removed inline `logging.basicConfig` call

- [ ] **Step 2: Run CLI tests**

Run: `cd I:\claude-docs\my-project\claude-translator && python -m pytest tests/test_cli.py -v`
Expected: ALL PASS

- [ ] **Step 3: Verify manually**

Run: `cd I:\claude-docs\my-project\claude-translator && python -m claude_translator --version`
Expected: `claude-translator, version 0.2.0`

Run: `cd I:\claude-docs\my-project\claude-translator && python -m claude_translator -v discover 2>&1 | head -1`
Expected: Output with DEBUG-level logging visible

- [ ] **Step 4: Commit**

```bash
git add src/claude_translator/cli.py
git commit -m "feat: add --verbose/--quiet CLI logging switches"
```

---

## Task 9: Nice-4 — Cache schema version

**Files:**
- Modify: `src/claude_translator/storage/cache.py`
- Modify: `tests/test_cache.py`

- [ ] **Step 1: Add schema version to cache module**

Update `src/claude_translator/storage/cache.py` with full replacement:

```python
"""LLM-generated translation cache — cache-{lang}.json."""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path

from claude_translator.errors import FileSystemError
from claude_translator.storage.paths import ensure_translations_dir, get_cache_path

logger = logging.getLogger(__name__)

CACHE_SCHEMA_VERSION = 1


def load_cache(lang: str) -> dict[str, str]:
    path = get_cache_path(lang)
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if raw.get("_schema_version") != CACHE_SCHEMA_VERSION:
        logger.warning(
            "Cache schema mismatch (got %s, expected %s), rebuilding",
            raw.get("_schema_version"),
            CACHE_SCHEMA_VERSION,
        )
        return {}
    return {k: v for k, v in raw.items() if k != "_schema_version"}


def save_cache(lang: str, mapping: dict[str, str]) -> None:
    path = ensure_translations_dir() / f"cache-{lang}.json"
    data = {"_schema_version": CACHE_SCHEMA_VERSION, **mapping}
    try:
        _atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    except OSError as e:
        raise FileSystemError(f"Cannot write to {path}: {e}") from e


def update_cache(lang: str, canonical_id: str, translation: str) -> None:
    cache = load_cache(lang)
    updated = {**cache, canonical_id: translation}
    save_cache(lang, updated)


def _atomic_write_text(path: Path, content: str) -> None:
    fd, temp_path = tempfile.mkstemp(dir=path.parent, prefix=f"{path.name}.", suffix=".tmp")
    try:
        with open(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        Path(temp_path).replace(path)
    finally:
        temp = Path(temp_path)
        if temp.exists():
            temp.unlink()
```

Key changes from current:
- `CACHE_SCHEMA_VERSION = 1` constant
- `load_cache`: checks `_schema_version`, strips it from returned dict, logs warning on mismatch
- `save_cache`: adds `_schema_version` to JSON before writing

- [ ] **Step 2: Add schema version tests to `tests/test_cache.py`**

Add to the end of `tests/test_cache.py`:

```python
def test_cache_schema_version_written(tmp_path: Path, monkeypatch):
    """Saved cache includes _schema_version."""
    td = tmp_path / "translations"
    td.mkdir()
    _patch_cache_paths(monkeypatch, td)
    save_cache("zh-CN", {"a": "b"})
    import json
    raw = json.loads((td / "cache-zh-CN.json").read_text(encoding="utf-8"))
    assert raw["_schema_version"] == 1
    assert raw["a"] == "b"


def test_cache_schema_version_not_in_loaded_data(tmp_path: Path, monkeypatch):
    """load_cache strips _schema_version from returned dict."""
    td = tmp_path / "translations"
    td.mkdir()
    _patch_cache_paths(monkeypatch, td)
    save_cache("zh-CN", {"a": "b"})
    result = load_cache("zh-CN")
    assert "_schema_version" not in result
    assert result == {"a": "b"}


def test_cache_schema_mismatch_rebuilds(tmp_path: Path, monkeypatch):
    """Schema mismatch triggers rebuild (returns empty dict)."""
    td = tmp_path / "translations"
    td.mkdir()
    bad_file = td / "cache-zh-CN.json"
    bad_file.write_text('{"_schema_version": 99, "a": "b"}', encoding="utf-8")
    _patch_cache_paths(monkeypatch, td)
    result = load_cache("zh-CN")
    assert result == {}


def test_cache_no_schema_version_rebuilds(tmp_path: Path, monkeypatch):
    """Missing schema version triggers rebuild."""
    td = tmp_path / "translations"
    td.mkdir()
    old_file = td / "cache-zh-CN.json"
    old_file.write_text('{"a": "b"}', encoding="utf-8")
    _patch_cache_paths(monkeypatch, td)
    result = load_cache("zh-CN")
    assert result == {}
```

- [ ] **Step 3: Run all cache tests**

Run: `cd I:\claude-docs\my-project\claude-translator && python -m pytest tests/test_cache.py -v`
Expected: ALL PASS (including 4 new schema tests + 1 permission test from Task 4)

- [ ] **Step 4: Run full test suite**

Run: `cd I:\claude-docs\my-project\claude-translator && python -m pytest -q`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add src/claude_translator/storage/cache.py tests/test_cache.py
git commit -m "feat: add schema version to translation cache"
```

---

## Task 10: Version bump to 0.2.1

**Files:**
- Modify: `pyproject.toml:7`
- Modify: `src/claude_translator/__init__.py:24`

- [ ] **Step 1: Bump version in `pyproject.toml`**

Change line 7 from `version = "0.2.0"` to `version = "0.2.1"`

- [ ] **Step 2: Bump fallback version in `__init__.py`**

Change the fallback in the except clause from `"0.2.0"` to `"0.2.1"`:

```python
except PackageNotFoundError:
    __version__ = _read_local_version() or "0.2.1"
```

- [ ] **Step 3: Verify version**

Run: `cd I:\claude-docs\my-project\claude-translator && python -c "from claude_translator import __version__; print(__version__)"`
Expected: `0.2.1`

- [ ] **Step 4: Run full test suite**

Run: `cd I:\claude-docs\my-project\claude-translator && python -m pytest -q`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/claude_translator/__init__.py
git commit -m "chore: bump version to 0.2.1"
```

---

## Self-Review

### Spec Coverage Check

| Spec Requirement | Task |
|-----------------|------|
| P1: CI add pytest | Task 1 |
| P2: Canonical round-trip fix | Task 2 |
| P3: Version reading simplification | Task 3 |
| P4: OSError handling | Task 4 |
| P5: Discovery semver defense | **SKIP** — already handled by `_extract_version` at discovery.py:149-154 |
| P6: Cleaner newline merging | Task 5 |
| P7: __main__.py | **SKIP** — already exists |
| Nice-1: README config example | Task 6 |
| Nice-2: pyproject URLs | Task 7 |
| Nice-3: CLI logging switches | Task 8 |
| Nice-4: Cache schema version | Task 9 |
| Version bump | Task 10 |

### Placeholder Scan

No TBD, TODO, or vague instructions found. All steps contain exact code.

### Type Consistency Check

- `FileSystemError` defined in Task 4 (errors.py) and used in Tasks 4 and 9 — consistent
- `CACHE_SCHEMA_VERSION = 1` defined in Task 9 — used consistently in load/save
- `_configure_logging` defined and used in Task 8 — consistent
- `parse_canonical_id` return type unchanged: `tuple[str, str, str, str]` — consistent with tests
- `load_cache` return type unchanged: `dict[str, str]` — schema_version stripped before return
