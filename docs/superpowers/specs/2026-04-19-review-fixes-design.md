# Claude Translator Review Fixes Design

> Date: 2026-04-19
> Source: REVIEW.md (2026-04-18 review)
> Scope: P1-P7 (P7 already fixed) + 4 Nice-to-have items
> Approach: Per-issue fix with independent verification

## Summary

Fix all issues identified in the code review, plus 4 nice-to-have improvements. Each fix is independent and verified individually before moving on. P7 is excluded (already fixed).

---

## P1: CI Add pytest

**File**: `.github/workflows/ci.yml`

**Change**: Append two steps after the existing `ruff format --check` step:

```yaml
      - name: Install project with dev extras
        run: pip install -e ".[dev]"

      - name: Run tests
        run: pytest
```

Also change the existing `pip install -e .` step to not duplicate (remove it since the new step installs with `[dev]`).

**Verification**: Push to PR, confirm pytest runs in CI.

---

## P2: Canonical round-trip fix for dotted plugin keys

**File**: `src/claude_translator/core/canonical.py`

**Problem**: `parse_canonical_id` uses `split(".", 1)` which breaks when `plugin_key` contains dots (e.g., `pua.skills`).

```
generate: 'plugin.pua.skills.skill:foo'
parse back: ('plugin', 'pua', 'skills.skill', 'foo')  ← wrong
expected:  ('plugin', 'pua.skills', 'skill', 'foo')
```

**Fix**: Use `rsplit` from the right side:

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

**New test** (`tests/test_canonical.py`): `test_roundtrip_dotted_plugin_key` — verify `generate → parse` symmetry for keys like `pua.skills`, `compound-engineering.context7`.

**Verification**: `pytest tests/test_canonical.py`

---

## P3: Version reading simplification

**File**: `src/claude_translator/__init__.py`

**Current**: Uses `importlib.metadata` but with convoluted `else` branch that prefers local file over metadata.

**Fix**: Simplify to prefer metadata, fallback to local file only on `PackageNotFoundError`:

```python
from importlib.metadata import version, PackageNotFoundError

def _read_local_version() -> str | None:
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if not pyproject.exists():
        return None
    match = _VERSION_RE.search(pyproject.read_text(encoding="utf-8"))
    return match.group(1) if match else None

try:
    __version__ = version("claude-translator")
except PackageNotFoundError:
    __version__ = _read_local_version() or "0.2.0"
```

Remove `_local_version` module-level variable and `else` branch.

**Verification**: `pytest` (existing test covers version reading)

---

## P4: Atomic write OSError handling

**File**: `src/claude_translator/storage/cache.py`, `src/claude_translator/storage/overrides.py`

**Problem**: `_atomic_write_text` can raise `OSError` (permission, read-only directory) without friendly message.

**Fix**: Wrap `_atomic_write_text` calls in try/except, convert to `FileSystemError`:

```python
try:
    _atomic_write_text(path, content)
except OSError as e:
    raise FileSystemError(f"Cannot write to {path}: {e}") from e
```

Apply same pattern in both `save_cache` and `save_overrides`.

**Verification**: `pytest tests/test_cache.py tests/test_overrides.py`

---

## P5: Discovery multi-version dedup defense

**File**: `src/claude_translator/core/discovery.py`

**Problem**: Version comparison assumes semver; non-standard versions (e.g., `1.2.3-beta`) may crash.

**Fix**: Wrap version comparison in try/except:

```python
from packaging.version import InvalidVersion

try:
    latest = max(versions, key=lambda v: Version(v))
except InvalidVersion:
    latest = sorted(versions)[-1]  # fallback to lexicographic order
```

**Verification**: `pytest tests/test_discovery.py`

---

## P6: Cleaner newline handling

**File**: `src/claude_translator/lang/cleaner.py`

**Policy change**: Instead of rejecting all multi-line output, merge internal newlines to spaces. Hard-reject only `---` (which would break frontmatter).

```python
import re

# Before: if "\n" in text: return None
# After:
text = re.sub(r"\s*\n\s*", " ", text.strip())
if "---" in text:
    return None
```

**New tests** (`tests/test_cleaner.py`):
- `test_merge_internal_newline`: `"hello\nworld"` → `"hello world"`
- `test_merge_multiple_newlines`: `"hello\n\nworld"` → `"hello world"`
- `test_reject_separator_still_works`: text with `---` still rejected

**Verification**: `pytest tests/test_cleaner.py`

---

## P7: `__main__.py` — ALREADY FIXED

File exists at `src/claude_translator/__main__.py` with correct content. No action needed.

---

## Nice-to-have 1: README config.toml example

**File**: `README.md`

Add a complete `config.toml` example in the Configuration section showing:
- `target_language`
- `llm.model`
- `llm.api_key` (with env var reference)
- `llm.base_url`
- `plugins_dirs`

---

## Nice-to-have 2: pyproject.toml project URLs

**File**: `pyproject.toml`

Add:

```toml
[project.urls]
Homepage = "https://github.com/debug-zhuweijian/claude-translator"
Repository = "https://github.com/debug-zhuweijian/claude-translator"
Issues = "https://github.com/debug-zhuweijian/claude-translator/issues"
```

---

## Nice-to-have 3: CLI log level switches

**File**: `src/claude_translator/cli.py`

Add `--verbose` / `--quiet` options using Click:

```python
@click.option("-v", "--verbose", count=True, help="Increase verbosity")
@click.option("-q", "--quiet", count=True, help="Decrease verbosity")
```

Map to logging levels:
- `-v` / `--verbose`: `logging.DEBUG`
- default: `logging.INFO`
- `-q` / `--quiet`: `logging.WARNING`
- `-qq`: `logging.ERROR`

Apply the higher of verbose/quiet adjustments. Add a helper function:

```python
def _configure_logging(verbose: int, quiet: int) -> None:
    level = logging.INFO - 10 * verbose + 10 * quiet
    level = max(logging.DEBUG, min(logging.CRITICAL, level))
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
```

---

## Nice-to-have 4: Cache schema version

**File**: `src/claude_translator/storage/cache.py`

On write: add `"_schema_version": 1` to the JSON root.

On read: check `_schema_version`. If missing or mismatched, log a warning and rebuild cache (treat as empty).

```python
SCHEMA_VERSION = 1

def load_cache(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("_schema_version") != SCHEMA_VERSION:
        logger.warning("Cache schema mismatch (%s vs %s), rebuilding",
                       data.get("_schema_version"), SCHEMA_VERSION)
        return {}
    return data

def save_cache(path: Path, data: dict) -> None:
    data["_schema_version"] = SCHEMA_VERSION
    ...
```

**Verification**: `pytest tests/test_cache.py`

---

## Execution Order

1. P1 (CI) — independent
2. P2 (canonical) — independent
3. P3 (version) — independent
4. P4 (OSError) — independent
5. P5 (discovery) — independent
6. P6 (cleaner) — independent
7. ~~P7~~ — skip (already done)
8. Nice-1 (README) — independent
9. Nice-2 (pyproject URLs) — independent
10. Nice-3 (CLI logging) — touches cli.py
11. Nice-4 (cache schema) — touches cache.py, may affect P4

**Note**: Nice-4 should be done after P4 since both touch `cache.py`.

## Version Bump

After all fixes: bump to `0.2.1` in `pyproject.toml` and `__init__.py` fallback version.
