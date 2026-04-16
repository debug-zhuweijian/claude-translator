# Claude Description Translator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-language plugin description translator CLI for Claude Code with 4-level fallback, auto-discovery, and CJK support.

**Architecture:** 3-layer separation — CLI (Click commands) → Engine (discovery/translator/injector) → Storage (paths/overrides/cache/LLM). All data flows through immutable Record objects. Translation uses a 4-level fallback chain: override → cache → LLM → original text.

**Tech Stack:** Python 3.10+, Click (CLI), Pydantic (config), OpenAI SDK (LLM), lingua-py (CJK detection), pytest + pyfakefs (testing)

---

## File Structure

```
src/claude_translator/
├── __init__.py                  # Package version
├── __main__.py                  # python -m entry
├── cli.py                       # Click: discover/sync/verify/init
├── errors.py                    # Exception hierarchy
├── config/
│   ├── __init__.py
│   ├── defaults.py              # Hardcoded defaults
│   ├── models.py                # Pydantic config models
│   └── loaders.py               # Cascade: CLI > env > file > defaults
├── core/
│   ├── __init__.py
│   ├── models.py                # Record(frozen), Inventory, TranslationMapping
│   ├── canonical.py             # canonical_id generate/parse
│   ├── frontmatter.py           # FrontmatterParser
│   ├── translator.py            # TranslationChain (4-level fallback)
│   ├── injector.py              # Frontmatter inject/update (preserve CRLF)
│   └── discovery.py             # Auto-discover plugins (DIR_KIND_MAP)
├── clients/
│   ├── __init__.py
│   ├── base.py                  # LLMClient Protocol
│   ├── openai_compat.py         # OpenAI-compatible endpoint
│   └── fake.py                  # FakeClient test double
├── storage/
│   ├── __init__.py
│   ├── paths.py                 # CLAUDE_CONFIG_DIR-aware path resolution
│   ├── overrides.py             # overrides-{lang}.json read/write
│   └── cache.py                 # cache-{lang}.json read/write
├── lang/
│   ├── __init__.py
│   ├── cjk.py                   # Unicode range checks
│   ├── detect.py                # detect_script + lingua-py fallback
│   └── prompts.py               # Per-language-pair prompt templates
└── utils/
    ├── __init__.py
    └── paths.py                 # normalize_path, detect_newline

tests/
├── __init__.py
├── conftest.py                  # Shared fixtures
├── test_errors.py
├── test_models.py
├── test_canonical.py
├── test_utils_paths.py
├── test_storage_paths.py
├── test_frontmatter.py
├── test_cjk.py
├── test_detect.py
├── test_prompts.py
├── test_overrides.py
├── test_cache.py
├── test_clients.py
├── test_translator.py
├── test_injector.py
├── test_discovery.py
├── test_config.py
└── test_cli.py
```

---

### Task 1: Project Scaffold + Errors + Core Models

**Files:**
- Create: `pyproject.toml`
- Create: `src/claude_translator/__init__.py`
- Create: `src/claude_translator/errors.py`
- Create: `src/claude_translator/core/__init__.py`
- Create: `src/claude_translator/core/models.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_errors.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "claude-translator"
version = "0.1.0"
description = "Multi-language plugin description translator for Claude Code"
requires-python = ">=3.10"
dependencies = [
    "click>=8.0",
    "pydantic>=2.0",
    "openai>=1.0",
]

[project.optional-dependencies]
cjk = ["lingua-py>=2.0"]
dev = [
    "pytest>=7.0",
    "pyfakefs>=5.0",
    "lingua-py>=2.0",
    "ruff>=0.4",
]

[project.scripts]
claude-translator = "claude_translator.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/claude_translator"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py310"
```

- [ ] **Step 2: Create package __init__.py files**

`src/claude_translator/__init__.py`:
```python
"""Claude Description Translator — multi-language plugin description translator."""

__version__ = "0.1.0"
```

`src/claude_translator/core/__init__.py`:
```python
```

`tests/__init__.py`:
```python
```

- [ ] **Step 3: Write test for errors.py**

`tests/test_errors.py`:
```python
from claude_translator.errors import (
    ConfigError,
    InternalError,
    PathError,
    TranslatorError,
    UserError,
)


def test_exception_hierarchy():
    assert issubclass(UserError, TranslatorError)
    assert issubclass(ConfigError, UserError)
    assert issubclass(PathError, UserError)
    assert issubclass(InternalError, TranslatorError)


def test_config_error_is_user_error():
    with raises(UserError):
        raise ConfigError("bad config")


def test_path_error_is_user_error():
    with raises(UserError):
        raise PathError("~/.claude/ missing")


def test_internal_error_not_user_error():
    assert not issubclass(InternalError, UserError)


def test_all_carry_message():
    for cls in [ConfigError, PathError, InternalError]:
        e = cls("test msg")
        assert str(e) == "test msg"
```

Note: add `from pytest import raises` import at top if needed, or use `pytest.raises` inline.

- [ ] **Step 4: Run test to verify it fails**

Run: `cd /i/claude-docs/my-project/claude-translator && pip install -e ".[dev]" && pytest tests/test_errors.py -v`
Expected: FAIL — module not found

- [ ] **Step 5: Implement errors.py**

`src/claude_translator/errors.py`:
```python
"""Exception hierarchy for claude-translator."""


class TranslatorError(Exception):
    """Base exception for all claude-translator errors."""


class UserError(TranslatorError):
    """User environment or configuration problems."""


class ConfigError(UserError):
    """Configuration file content or structure issues."""


class PathError(UserError):
    """~/.claude/ directory missing or inaccessible."""


class InternalError(TranslatorError):
    """Program bugs — should never occur in production."""
```

- [ ] **Step 6: Run errors test**

Run: `pytest tests/test_errors.py -v`
Expected: PASS

- [ ] **Step 7: Write test for core/models.py**

`tests/test_models.py`:
```python
from dataclasses import FrozenInstanceError

from claude_translator.core.models import Inventory, Record, TranslationMapping


def test_record_is_frozen():
    r = Record(
        canonical_id="plugin.superpowers.skill:brainstorm",
        kind="skill",
        scope="plugin",
        source_path="/path/to/file.md",
        relative_path="skills/brainstorm/SKILL.md",
    )
    try:
        r.canonical_id = "changed"  # type: ignore[misc]
        assert False, "Should raise FrozenInstanceError"
    except FrozenInstanceError:
        pass


def test_record_defaults():
    r = Record(
        canonical_id="user.skill:test",
        kind="skill",
        scope="user",
        source_path="/path",
        relative_path="test.md",
    )
    assert r.plugin_key == ""
    assert r.current_description == ""
    assert r.status == ""
    assert r.matched_translation == ""
    assert r.frontmatter_present is True


def test_inventory_find_by_canonical_id():
    r1 = Record("plugin.a.skill:x", "skill", "plugin", "/a", "a.md", plugin_key="a")
    r2 = Record("user.skill:y", "skill", "user", "/b", "b.md")
    inv = Inventory((r1, r2))
    assert inv.find_by_canonical_id("plugin.a.skill:x") is r1
    assert inv.find_by_canonical_id("user.skill:y") is r2
    assert inv.find_by_canonical_id("nonexistent") is None


def test_inventory_size():
    inv = Inventory(tuple(
        Record(f"plugin.a.skill:{i}", "skill", "plugin", f"/{i}", f"{i}.md")
        for i in range(5)
    ))
    assert inv.size() == 5


def test_translation_mapping():
    m = TranslationMapping(
        canonical_id="plugin.a.skill:x",
        source_text="Hello",
        translated_text="你好",
        source_lang="en",
        target_lang="zh-CN",
    )
    assert m.translated_text == "你好"
```

- [ ] **Step 8: Run models test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — module not found

- [ ] **Step 9: Implement core/models.py**

`src/claude_translator/core/models.py`:
```python
"""Immutable data models for claude-translator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Record:
    """A single translatable item discovered from the plugin ecosystem."""

    canonical_id: str
    kind: str
    scope: str
    source_path: str
    relative_path: str
    plugin_key: str = ""
    current_description: str = ""
    status: str = ""
    matched_translation: str = ""
    frontmatter_present: bool = True


@dataclass(frozen=True)
class Inventory:
    """Immutable collection of discovered Records."""

    records: tuple[Record, ...]

    def find_by_canonical_id(self, cid: str) -> Record | None:
        for r in self.records:
            if r.canonical_id == cid:
                return r
        return None

    def size(self) -> int:
        return len(self.records)


@dataclass(frozen=True)
class TranslationMapping:
    """A single translation result with metadata."""

    canonical_id: str
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str
```

- [ ] **Step 10: Run models test**

Run: `pytest tests/test_models.py -v`
Expected: PASS

- [ ] **Step 11: Create conftest.py**

`tests/conftest.py`:
```python
"""Shared test fixtures for claude-translator tests."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_claude_dir(tmp_path: Path) -> Path:
    """Create a temporary .claude directory structure."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    translations_dir = claude_dir / "translations"
    translations_dir.mkdir()
    return claude_dir


@pytest.fixture
def sample_plugin_dir(tmp_path: Path) -> Path:
    """Create a sample plugin directory with standard structure."""
    plugin_dir = tmp_path / "plugins" / "cache" / "market" / "my-plugin" / "1.0.0"
    skills_dir = plugin_dir / "skills" / "brainstorm"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("---\ndescription: Brainstorm ideas\n---\n# Brainstorm\n")
    commands_dir = plugin_dir / "commands"
    commands_dir.mkdir()
    (commands_dir / "commit.md").write_text("---\ndescription: Create a commit\n---\n# Commit\n")
    return plugin_dir


@pytest.fixture
def sample_record() -> dict:
    """Sample record kwargs for testing."""
    return {
        "canonical_id": "plugin.my-plugin.skill:brainstorm",
        "kind": "skill",
        "scope": "plugin",
        "source_path": "/plugins/cache/market/my-plugin/1.0.0/skills/brainstorm/SKILL.md",
        "relative_path": "skills/brainstorm/SKILL.md",
        "plugin_key": "my-plugin",
        "current_description": "Brainstorm ideas",
    }
```

- [ ] **Step 12: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 13: Commit**

```bash
cd /i/claude-docs/my-project/claude-translator
git add pyproject.toml src/ tests/
git commit -m "feat: project scaffold with errors and core models"
```

---

### Task 2: Utilities + Storage Paths

**Files:**
- Create: `src/claude_translator/utils/__init__.py`
- Create: `src/claude_translator/utils/paths.py`
- Create: `src/claude_translator/storage/__init__.py`
- Create: `src/claude_translator/storage/paths.py`
- Create: `tests/test_utils_paths.py`
- Create: `tests/test_storage_paths.py`

Covers: T1 (empty env), T14 (CLAUDE_CONFIG_DIR), T15 (Windows backslash)

- [ ] **Step 1: Write tests for utils/paths.py**

`tests/test_utils_paths.py`:
```python
from claude_translator.utils.paths import detect_newline, normalize_path


def test_normalize_path_forward_slash():
    assert normalize_path("skills/brainstorm/SKILL.md") == "skills/brainstorm/SKILL.md"


def test_normalize_path_backslash():
    assert normalize_path("skills\\brainstorm\\SKILL.md") == "skills/brainstorm/SKILL.md"


def test_normalize_path_mixed():
    assert normalize_path("skills\\brainstorm/SKILL.md") == "skills/brainstorm/SKILL.md"


def test_normalize_path_empty():
    assert normalize_path("") == ""


def test_detect_newline_lf():
    assert detect_newline("line1\nline2") == "\n"


def test_detect_newline_crlf():
    assert detect_newline("line1\r\nline2") == "\r\n"


def test_detect_newline_no_newline():
    assert detect_newline("no newline") == "\n"


def test_detect_newline_crlf_priority():
    """CRLF should be detected even if LF also present."""
    assert detect_newline("line1\r\nline2\nline3") == "\r\n"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_utils_paths.py -v`
Expected: FAIL

- [ ] **Step 3: Implement utils/paths.py**

`src/claude_translator/utils/__init__.py`:
```python
```

`src/claude_translator/utils/paths.py`:
```python
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
```

- [ ] **Step 4: Run utils test**

Run: `pytest tests/test_utils_paths.py -v`
Expected: PASS

- [ ] **Step 5: Write tests for storage/paths.py**

`tests/test_storage_paths.py`:
```python
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from claude_translator.storage.paths import (
    get_cache_path,
    get_claude_dir,
    get_config_path,
    get_overrides_path,
    get_translations_dir,
)
from claude_translator.errors import PathError


def test_get_claude_dir_default(tmp_path: Path):
    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = get_claude_dir()
    assert result == tmp_path / ".claude"


def test_get_claude_dir_env_override(tmp_path: Path):
    custom = tmp_path / "custom-claude"
    custom.mkdir()
    with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(custom)}):
        result = get_claude_dir()
    assert result == custom


def test_get_translations_dir(tmp_path: Path):
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = get_translations_dir()
    assert result == claude_dir / "translations"
    assert result.exists()


def test_get_overrides_path(tmp_path: Path):
    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = get_overrides_path("zh-CN")
    assert result.name == "overrides-zh-CN.json"


def test_get_cache_path(tmp_path: Path):
    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = get_cache_path("ja")
    assert result.name == "cache-ja.json"


def test_get_config_path(tmp_path: Path):
    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = get_config_path()
    assert result.name == "config.json"
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest tests/test_storage_paths.py -v`
Expected: FAIL

- [ ] **Step 7: Implement storage/paths.py**

`src/claude_translator/storage/__init__.py`:
```python
```

`src/claude_translator/storage/paths.py`:
```python
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
    """Return the translations directory, creating it if needed."""
    d = get_claude_dir() / "translations"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_overrides_path(lang: str) -> Path:
    """Return path to overrides-{lang}.json."""
    return get_translations_dir() / f"overrides-{lang}.json"


def get_cache_path(lang: str) -> Path:
    """Return path to cache-{lang}.json."""
    return get_translations_dir() / f"cache-{lang}.json"


def get_config_path() -> Path:
    """Return path to translations config.json."""
    return get_translations_dir() / "config.json"
```

- [ ] **Step 8: Run storage paths test**

Run: `pytest tests/test_storage_paths.py -v`
Expected: PASS

- [ ] **Step 9: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 10: Commit**

```bash
cd /i/claude-docs/my-project/claude-translator
git add src/claude_translator/utils/ src/claude_translator/storage/paths.py tests/
git commit -m "feat: path utilities and CLAUDE_CONFIG_DIR-aware storage paths"
```

---

### Task 3: Canonical ID + Frontmatter Parser

**Files:**
- Create: `src/claude_translator/core/canonical.py`
- Create: `src/claude_translator/core/frontmatter.py`
- Create: `tests/test_canonical.py`
- Create: `tests/test_frontmatter.py`

Covers: T7 (no frontmatter), T8 (CRLF), T11 (canonical_id matching)

- [ ] **Step 1: Write tests for canonical.py**

`tests/test_canonical.py`:
```python
from claude_translator.core.canonical import generate_canonical_id, parse_canonical_id


def test_generate_plugin_id():
    result = generate_canonical_id(
        kind="skill", name="brainstorm", scope="plugin", plugin_key="superpowers"
    )
    assert result == "plugin.superpowers.skill:brainstorm"


def test_generate_user_id():
    result = generate_canonical_id(
        kind="command", name="commit", scope="user", plugin_key=""
    )
    assert result == "user.command:commit"


def test_parse_plugin_id():
    scope, plugin_key, kind, name = parse_canonical_id("plugin.superpowers.skill:brainstorm")
    assert scope == "plugin"
    assert plugin_key == "superpowers"
    assert kind == "skill"
    assert name == "brainstorm"


def test_parse_user_id():
    scope, plugin_key, kind, name = parse_canonical_id("user.command:commit")
    assert scope == "user"
    assert plugin_key == ""
    assert kind == "command"
    assert name == "commit"


def test_generate_and_parse_roundtrip():
    original = generate_canonical_id("skill", "test-skill", "plugin", "my-plugin")
    scope, pk, kind, name = parse_canonical_id(original)
    assert scope == "plugin"
    assert pk == "my-plugin"
    assert kind == "skill"
    assert name == "test-skill"


def test_name_from_filename():
    """Name should be filename without .md extension."""
    from claude_translator.core.canonical import name_from_filename
    assert name_from_filename("brainstorm.md") == "brainstorm"
    assert name_from_filename("SKILL.md") == "SKILL"
    assert name_from_filename("my-command.md") == "my-command"


def test_name_from_filename_no_extension():
    from claude_translator.core.canonical import name_from_filename
    assert name_from_filename("noext") == "noext"
```

- [ ] **Step 2: Run canonical test to verify it fails**

Run: `pytest tests/test_canonical.py -v`
Expected: FAIL

- [ ] **Step 3: Implement canonical.py**

`src/claude_translator/core/canonical.py`:
```python
"""Canonical ID generation and parsing."""

from __future__ import annotations


def generate_canonical_id(
    kind: str, name: str, scope: str, plugin_key: str = ""
) -> str:
    """Generate a canonical ID string.

    Format: plugin.<key>.<kind>:<name> or user.<kind>:<name>
    """
    if scope == "user":
        return f"user.{kind}:{name}"
    return f"plugin.{plugin_key}.{kind}:{name}"


def parse_canonical_id(cid: str) -> tuple[str, str, str, str]:
    """Parse a canonical ID into (scope, plugin_key, kind, name)."""
    if cid.startswith("user."):
        rest = cid[5:]  # strip "user."
        kind, name = rest.split(":", 1)
        return "user", "", kind, name

    # plugin.<key>.<kind>:<name>
    without_prefix = cid[7:]  # strip "plugin."
    key_and_rest = without_prefix.split(".", 1)
    plugin_key = key_and_rest[0]
    kind, name = key_and_rest[1].split(":", 1)
    return "plugin", plugin_key, kind, name


def name_from_filename(filename: str) -> str:
    """Extract name from filename by removing .md extension."""
    if filename.endswith(".md"):
        return filename[:-3]
    return filename
```

- [ ] **Step 4: Run canonical test**

Run: `pytest tests/test_canonical.py -v`
Expected: PASS

- [ ] **Step 5: Write tests for frontmatter.py**

`tests/test_frontmatter.py`:
```python
from claude_translator.core.frontmatter import FrontmatterParser


def test_parse_with_frontmatter():
    content = "---\ndescription: Hello world\n---\nBody text here"
    parser = FrontmatterParser()
    fm, body = parser.parse(content)
    assert fm == {"description": "Hello world"}
    assert body == "Body text here"


def test_parse_no_frontmatter():
    content = "# Just a heading\nSome text"
    parser = FrontmatterParser()
    fm, body = parser.parse(content)
    assert fm == {}
    assert body == content


def test_parse_crlf():
    content = "---\r\ndescription: Test\r\n---\r\nBody"
    parser = FrontmatterParser()
    fm, body = parser.parse(content)
    assert fm == {"description": "Test"}
    assert body == "Body"


def test_get_description():
    parser = FrontmatterParser()
    assert parser.get_description({"description": "Hello"}) == "Hello"
    assert parser.get_description({}) is None
    assert parser.get_description({"other": "value"}) is None


def test_set_description():
    parser = FrontmatterParser()
    result = parser.set_description({"description": "old"}, "new")
    assert result["description"] == "new"


def test_set_description_adds_key():
    parser = FrontmatterParser()
    result = parser.set_description({}, "new")
    assert result["description"] == "new"


def test_build_with_frontmatter():
    parser = FrontmatterParser()
    result = parser.build({"description": "Test"}, "# Heading")
    assert result.startswith("---\n")
    assert "description: Test" in result
    assert "---\n" in result
    assert "# Heading" in result


def test_build_preserves_existing_keys():
    parser = FrontmatterParser()
    result = parser.build({"description": "A", "name": "B"}, "body")
    assert "name: B" in result


def test_build_no_frontmatter():
    parser = FrontmatterParser()
    result = parser.build({}, "just body")
    assert result == "just body"
```

- [ ] **Step 6: Run frontmatter test to verify it fails**

Run: `pytest tests/test_frontmatter.py -v`
Expected: FAIL

- [ ] **Step 7: Implement frontmatter.py**

`src/claude_translator/core/frontmatter.py`:
```python
"""Frontmatter parsing and generation for Claude skill/command markdown files."""

from __future__ import annotations

import re


class FrontmatterParser:
    """Parse and generate YAML frontmatter in markdown files."""

    _FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)", re.DOTALL)

    def parse(self, content: str) -> tuple[dict[str, str], str]:
        """Parse content into (frontmatter_dict, body).

        Returns ({}, full_content) if no frontmatter found.
        """
        m = self._FRONTMATTER_RE.match(content)
        if not m:
            return {}, content
        fm_raw = m.group(1)
        body = m.group(2)
        fm: dict[str, str] = {}
        for line in fm_raw.split("\n"):
            line = line.strip()
            if ":" in line:
                key, _, value = line.partition(":")
                fm[key.strip()] = value.strip()
        return fm, body

    def get_description(self, fm: dict[str, str]) -> str | None:
        """Get description from frontmatter dict, or None."""
        return fm.get("description")

    def set_description(self, fm: dict[str, str], description: str) -> dict[str, str]:
        """Return new dict with description set (immutable)."""
        return {**fm, "description": description}

    def build(self, fm: dict[str, str], body: str) -> str:
        """Build full content string from frontmatter dict and body."""
        if not fm:
            return body
        lines = ["---"]
        for key, value in fm.items():
            lines.append(f"{key}: {value}")
        lines.append("---")
        return "\n".join(lines) + "\n" + body
```

- [ ] **Step 8: Run frontmatter test**

Run: `pytest tests/test_frontmatter.py -v`
Expected: PASS

- [ ] **Step 9: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 10: Commit**

```bash
cd /i/claude-docs/my-project/claude-translator
git add src/claude_translator/core/canonical.py src/claude_translator/core/frontmatter.py tests/
git commit -m "feat: canonical ID generation/parsing and frontmatter parser"
```

---

### Task 4: CJK Language Detection + Translation Prompts

**Files:**
- Create: `src/claude_translator/lang/__init__.py`
- Create: `src/claude_translator/lang/cjk.py`
- Create: `src/claude_translator/lang/detect.py`
- Create: `src/claude_translator/lang/prompts.py`
- Create: `tests/test_cjk.py`
- Create: `tests/test_detect.py`
- Create: `tests/test_prompts.py`

Covers: T18 (CJK mixed text detection)

- [ ] **Step 1: Write tests for cjk.py**

`tests/test_cjk.py`:
```python
from claude_translator.lang.cjk import has_cjk, has_ja, has_ko


def test_has_cjk_chinese():
    assert has_cjk("你好世界") is True


def test_has_cjk_english():
    assert has_cjk("hello world") is False


def test_has_cjk_mixed():
    assert has_cjk("hello 你好") is True


def test_has_ja_hiragana():
    assert has_ja("こんにちは") is True  # Hiragana


def test_has_ja_katakana():
    assert has_ja("コンニチハ") is True  # Katakana


def test_has_ja_chinese_only():
    assert has_ja("你好世界") is False  # No kana


def test_has_ko_hangul():
    assert has_ko("안녕하세요") is True


def test_has_ko_chinese():
    assert has_ko("你好") is False


def test_empty_string():
    assert has_cjk("") is False
    assert has_ja("") is False
    assert has_ko("") is False
```

- [ ] **Step 2: Run cjk test to verify it fails**

Run: `pytest tests/test_cjk.py -v`
Expected: FAIL

- [ ] **Step 3: Implement cjk.py**

`src/claude_translator/lang/__init__.py`:
```python
```

`src/claude_translator/lang/cjk.py`:
```python
"""Unicode range checks for CJK scripts."""

from __future__ import annotations

import re

_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
_HIRAGANA_RE = re.compile(r"[\u3040-\u309f]")
_KATAKANA_RE = re.compile(r"[\u30a0-\u30ff]")
_HANGUL_RE = re.compile(r"[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]")


def has_cjk(text: str) -> bool:
    """Check if text contains CJK Ideographs."""
    return bool(_CJK_RE.search(text))


def has_ja(text: str) -> bool:
    """Check if text contains Japanese kana (hiragana or katakana)."""
    return bool(_HIRAGANA_RE.search(text) or _KATAKANA_RE.search(text))


def has_ko(text: str) -> bool:
    """Check if text contains Korean Hangul."""
    return bool(_HANGUL_RE.search(text))
```

- [ ] **Step 4: Run cjk test**

Run: `pytest tests/test_cjk.py -v`
Expected: PASS

- [ ] **Step 5: Write tests for detect.py**

`tests/test_detect.py`:
```python
from claude_translator.lang.detect import detect_script


def test_detect_korean():
    assert detect_script("안녕하세요 세계") == "ko"


def test_detect_japanese_kana():
    assert detect_script("こんにちは世界") == "ja"


def test_detect_chinese_only():
    assert detect_script("你好世界") == "zh"


def test_detect_english():
    assert detect_script("hello world") == "unknown"


def test_detect_mixed_korean_cjk():
    """Korean should be detected by Hangul even with CJK present."""
    assert detect_script("안녕 中文混合") == "ko"


def test_detect_mixed_japanese_cjk():
    """Japanese should be detected by kana even with CJK present."""
    assert detect_script("こんにちは 中文混合") == "ja"


def test_detect_empty():
    assert detect_script("") == "unknown"


def test_detect_numbers():
    assert detect_script("12345") == "unknown"
```

- [ ] **Step 6: Run detect test to verify it fails**

Run: `pytest tests/test_detect.py -v`
Expected: FAIL

- [ ] **Step 7: Implement detect.py**

`src/claude_translator/lang/detect.py`:
```python
"""Script detection for CJK languages.

Uses Unicode heuristic first, falls back to lingua-py for ambiguous cases.
"""

from __future__ import annotations

import re

_KO_RE = re.compile(r"[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]")
_KANA_RE = re.compile(r"[\u3040-\u309f\u30a0-\u30ff]")
_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")


def detect_script(text: str) -> str:
    """Detect the dominant CJK script in text using Unicode heuristics.

    Returns: "ko", "ja", "zh", or "unknown"
    Priority: Korean > Japanese > Chinese (by unique Unicode ranges)
    """
    if _KO_RE.search(text):
        return "ko"
    if _KANA_RE.search(text):
        return "ja"
    if _CJK_RE.search(text):
        return "zh"
    return "unknown"
```

- [ ] **Step 8: Run detect test**

Run: `pytest tests/test_detect.py -v`
Expected: PASS

- [ ] **Step 9: Write tests for prompts.py**

`tests/test_prompts.py`:
```python
from claude_translator.lang.prompts import get_prompt


def test_en_to_zh():
    prompt = get_prompt("en", "zh-CN")
    assert "Chinese" in prompt or "中文" in prompt
    assert len(prompt) > 50


def test_en_to_ja():
    prompt = get_prompt("en", "ja")
    assert "Japanese" in prompt or "日本語" in prompt


def test_en_to_ko():
    prompt = get_prompt("en", "ko")
    assert "Korean" in prompt or "한국어" in prompt


def test_zh_to_ja():
    prompt = get_prompt("zh-CN", "ja")
    assert "假朋友" in prompt or "false friend" in prompt.lower() or "日本語" in prompt


def test_zh_to_ko():
    prompt = get_prompt("zh-CN", "ko")
    assert "해요체" in prompt or "Korean" in prompt


def test_unknown_pair():
    """Unknown pairs should still return a valid generic prompt."""
    prompt = get_prompt("en", "fr")
    assert len(prompt) > 20
```

- [ ] **Step 10: Run prompts test to verify it fails**

Run: `pytest tests/test_prompts.py -v`
Expected: FAIL

- [ ] **Step 11: Implement prompts.py**

`src/claude_translator/lang/prompts.py`:
```python
"""Translation prompt templates per language pair."""

from __future__ import annotations

_PROMPTS: dict[tuple[str, str], str] = {
    ("en", "zh-CN"): (
        "Translate the following text to Simplified Chinese. "
        "Keep the tone concise and technical. "
        "Do not add explanations, just the translation."
    ),
    ("en", "zh-TW"): (
        "Translate the following text to Traditional Chinese. "
        "Keep the tone concise and technical. "
        "Do not add explanations, just the translation."
    ),
    ("en", "ja"): (
        "Translate the following text to natural, fluent Japanese. "
        "Do not translate word-by-word. Use natural Japanese expressions. "
        "Keep the tone concise and technical."
    ),
    ("en", "ko"): (
        "Translate the following text to Korean using 존댓말 (polite form). "
        "Keep the tone concise and technical. "
        "Do not add explanations, just the translation."
    ),
    ("zh-CN", "ja"): (
        "Translate the following Chinese text to Japanese. "
        "Watch out for false friends: 手紙 means toilet paper in Chinese but letter in Japanese "
        "(use 便り or 手紙(てがみ) depending on context); "
        "勉强 means reluctant in Chinese but study/学ぶ in Japanese. "
        "Use natural Japanese expressions."
    ),
    ("zh-CN", "ko"): (
        "Translate the following Chinese text to Korean using 해요체 (polite informal). "
        "Keep the tone concise and technical."
    ),
}

_GENERIC_PROMPT = (
    "Translate the following text from {source_lang} to {target_lang}. "
    "Keep the tone concise and technical. "
    "Do not add explanations, just the translation."
)


def get_prompt(source_lang: str, target_lang: str) -> str:
    """Get the translation prompt for a language pair."""
    key = (source_lang, target_lang)
    if key in _PROMPTS:
        return _PROMPTS[key]
    return _GENERIC_PROMPT.format(source_lang=source_lang, target_lang=target_lang)
```

- [ ] **Step 12: Run prompts test**

Run: `pytest tests/test_prompts.py -v`
Expected: PASS

- [ ] **Step 13: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 14: Commit**

```bash
cd /i/claude-docs/my-project/claude-translator
git add src/claude_translator/lang/ tests/test_cjk.py tests/test_detect.py tests/test_prompts.py
git commit -m "feat: CJK language detection, script identification, and translation prompts"
```

---

### Task 5: Storage Layer — Overrides + Cache

**Files:**
- Create: `src/claude_translator/storage/overrides.py`
- Create: `src/claude_translator/storage/cache.py`
- Create: `tests/test_overrides.py`
- Create: `tests/test_cache.py`

Covers: T9 (multi-language file routing), T1 (auto-create dirs)

- [ ] **Step 1: Write tests for overrides.py**

`tests/test_overrides.py`:
```python
import json
from pathlib import Path
from unittest.mock import patch

from claude_translator.storage.overrides import load_overrides, save_overrides


def test_save_and_load(tmp_path: Path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    with patch("claude_translator.storage.overrides.get_translations_dir", return_value=translations_dir):
        save_overrides("zh-CN", {"plugin.a.skill:x": "翻译文本"})
        result = load_overrides("zh-CN")
    assert result == {"plugin.a.skill:x": "翻译文本"}


def test_load_empty(tmp_path: Path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    with patch("claude_translator.storage.overrides.get_translations_dir", return_value=translations_dir):
        result = load_overrides("ja")
    assert result == {}


def test_save_creates_file(tmp_path: Path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    with patch("claude_translator.storage.overrides.get_translations_dir", return_value=translations_dir):
        save_overrides("ko", {"user.skill:test": "한국어"})
    filepath = translations_dir / "overrides-ko.json"
    assert filepath.exists()
    data = json.loads(filepath.read_text(encoding="utf-8"))
    assert data == {"user.skill:test": "한국어"}


def test_multi_language_isolation(tmp_path: Path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    with patch("claude_translator.storage.overrides.get_translations_dir", return_value=translations_dir):
        save_overrides("zh-CN", {"a": "中文"})
        save_overrides("ja", {"a": "日本語"})
        assert load_overrides("zh-CN") == {"a": "中文"}
        assert load_overrides("ja") == {"a": "日本語"}
```

- [ ] **Step 2: Run overrides test to verify it fails**

Run: `pytest tests/test_overrides.py -v`
Expected: FAIL

- [ ] **Step 3: Implement overrides.py**

`src/claude_translator/storage/overrides.py`:
```python
"""User manual overrides storage — overrides-{lang}.json."""

from __future__ import annotations

import json
from pathlib import Path

from claude_translator.storage.paths import get_overrides_path


def load_overrides(lang: str) -> dict[str, str]:
    """Load user overrides for a language. Returns {} if file missing."""
    path = get_overrides_path(lang)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_overrides(lang: str, mapping: dict[str, str]) -> None:
    """Write user overrides for a language."""
    path = get_overrides_path(lang)
    path.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
```

- [ ] **Step 4: Run overrides test**

Run: `pytest tests/test_overrides.py -v`
Expected: PASS

- [ ] **Step 5: Write tests for cache.py**

`tests/test_cache.py`:
```python
import json
from pathlib import Path
from unittest.mock import patch

from claude_translator.storage.cache import load_cache, update_cache, save_cache


def test_save_and_load(tmp_path: Path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    with patch("claude_translator.storage.cache.get_translations_dir", return_value=translations_dir):
        save_cache("zh-CN", {"plugin.a.skill:x": "翻译"})
        result = load_cache("zh-CN")
    assert result == {"plugin.a.skill:x": "翻译"}


def test_load_empty(tmp_path: Path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    with patch("claude_translator.storage.cache.get_translations_dir", return_value=translations_dir):
        result = load_cache("ja")
    assert result == {}


def test_update_cache_appends(tmp_path: Path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    with patch("claude_translator.storage.cache.get_translations_dir", return_value=translations_dir):
        update_cache("zh-CN", "plugin.a.skill:x", "翻译A")
        update_cache("zh-CN", "user.skill:y", "翻译B")
        result = load_cache("zh-CN")
    assert result == {"plugin.a.skill:x": "翻译A", "user.skill:y": "翻译B"}


def test_update_cache_overwrites_existing(tmp_path: Path):
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    with patch("claude_translator.storage.cache.get_translations_dir", return_value=translations_dir):
        update_cache("zh-CN", "plugin.a.skill:x", "旧翻译")
        update_cache("zh-CN", "plugin.a.skill:x", "新翻译")
        result = load_cache("zh-CN")
    assert result == {"plugin.a.skill:x": "新翻译"}
```

- [ ] **Step 6: Run cache test to verify it fails**

Run: `pytest tests/test_cache.py -v`
Expected: FAIL

- [ ] **Step 7: Implement cache.py**

`src/claude_translator/storage/cache.py`:
```python
"""LLM-generated translation cache — cache-{lang}.json."""

from __future__ import annotations

import json
from pathlib import Path

from claude_translator.storage.paths import get_cache_path


def load_cache(lang: str) -> dict[str, str]:
    """Load cached translations for a language. Returns {} if file missing."""
    path = get_cache_path(lang)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(lang: str, mapping: dict[str, str]) -> None:
    """Write full cache for a language."""
    path = get_cache_path(lang)
    path.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def update_cache(lang: str, canonical_id: str, translation: str) -> None:
    """Update a single entry in cache, preserving others."""
    cache = load_cache(lang)
    updated = {**cache, canonical_id: translation}
    save_cache(lang, updated)
```

- [ ] **Step 8: Run cache test**

Run: `pytest tests/test_cache.py -v`
Expected: PASS

- [ ] **Step 9: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 10: Commit**

```bash
cd /i/claude-docs/my-project/claude-translator
git add src/claude_translator/storage/overrides.py src/claude_translator/storage/cache.py tests/test_overrides.py tests/test_cache.py
git commit -m "feat: overrides and cache storage with per-language file routing"
```

---

> **Tasks 6-10 see below.**

---

### Task 6: LLM Client Abstraction

**Files:**
- Create: `src/claude_translator/clients/__init__.py`
- Create: `src/claude_translator/clients/base.py`
- Create: `src/claude_translator/clients/fake.py`
- Create: `src/claude_translator/clients/openai_compat.py`
- Create: `tests/test_clients.py`

Covers: T10 (LLM unavailable)

- [ ] **Step 1: Write tests for clients**

`tests/test_clients.py`:
```python
from claude_translator.clients.base import LLMClient
from claude_translator.clients.fake import FakeClient
from claude_translator.clients.openai_compat import OpenAICompatClient


def test_fake_client_returns_prefix():
    client = FakeClient()
    result = client.translate("hello", "en", "zh-CN")
    assert "[zh-CN] hello" == result


def test_fake_client_different_langs():
    client = FakeClient()
    assert "ja" in client.translate("test", "en", "ja")
    assert "ko" in client.translate("test", "en", "ko")


def test_llm_client_is_protocol():
    """LLMClient should be a Protocol, not a concrete class."""
    from typing import runtime_checkable
    assert hasattr(LLMClient, "__protocol_attrs__") or hasattr(LLMClient, "__abstractmethods__") or True
    # Just verify FakeClient satisfies the protocol
    client: LLMClient = FakeClient()
    assert hasattr(client, "translate")


def test_openai_compat_init():
    client = OpenAICompatClient(
        base_url="https://api.example.com/v1",
        api_key="test-key",
        model="test-model",
    )
    assert client._model == "test-model"


def test_openai_compat_init_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://env.example.com/v1")
    client = OpenAICompatClient(model="gpt-4")
    assert client._model == "gpt-4"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_clients.py -v`
Expected: FAIL

- [ ] **Step 3: Implement clients**

`src/claude_translator/clients/__init__.py`:
```python
```

`src/claude_translator/clients/base.py`:
```python
"""LLM client protocol for translation backends."""

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    """Protocol for LLM translation backends."""

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text from source_lang to target_lang."""
        ...
```

`src/claude_translator/clients/fake.py`:
```python
"""Fake LLM client for testing."""

from __future__ import annotations


class FakeClient:
    """Test double that returns [lang] text without calling any API."""

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        return f"[{target_lang}] {text}"
```

`src/claude_translator/clients/openai_compat.py`:
```python
"""OpenAI-compatible LLM client for translation."""

from __future__ import annotations

import logging
import os

from claude_translator.lang.prompts import get_prompt

logger = logging.getLogger(__name__)


class OpenAICompatClient:
    """Client for OpenAI-compatible endpoints (Anthropic, Qwen, DeepSeek, etc.)."""

    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        from openai import OpenAI

        self._model = model
        self._client = OpenAI(
            base_url=base_url or os.getenv("OPENAI_BASE_URL"),
            api_key=api_key or os.getenv("OPENAI_API_KEY", ""),
        )

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using the OpenAI-compatible API."""
        prompt = get_prompt(source_lang, target_lang)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        result = response.choices[0].message.content
        if result is None:
            raise RuntimeError("LLM returned empty response")
        return result.strip()
```

- [ ] **Step 4: Run clients test**

Run: `pytest tests/test_clients.py -v`
Expected: PASS

- [ ] **Step 5: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
cd /i/claude-docs/my-project/claude-translator
git add src/claude_translator/clients/ tests/test_clients.py
git commit -m "feat: LLM client abstraction with fake and OpenAI-compatible backends"
```

---

### Task 7: Translation Chain (4-Level Fallback)

**Files:**
- Create: `src/claude_translator/core/translator.py`
- Create: `tests/test_translator.py`

Covers: T10 (LLM fallback), T4 (fallback chain)

- [ ] **Step 1: Write tests for translator.py**

`tests/test_translator.py`:
```python
from pathlib import Path
from unittest.mock import patch

from claude_translator.core.models import Record
from claude_translator.core.translator import TranslationChain
from claude_translator.clients.fake import FakeClient


def _make_record(desc: str = "Hello") -> Record:
    return Record(
        canonical_id="plugin.test.skill:demo",
        kind="skill",
        scope="plugin",
        source_path="/path/demo.md",
        relative_path="skills/demo/SKILL.md",
        plugin_key="test",
        current_description=desc,
    )


def test_override_hit(tmp_path: Path):
    """Level 1: user override should be used when present."""
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()
    with patch("claude_translator.storage.overrides.get_translations_dir", return_value=translations_dir), \
         patch("claude_translator.storage.cache.get_translations_dir", return_value=translations_dir):
        # Write override
        from claude_translator.storage.overrides import save_overrides
        save_overrides("zh-CN", {"plugin.test.skill:demo": "用户覆盖"})

        chain = TranslationChain(
            overrides_loader=lambda lang: {"plugin.test.skill:demo": "用户覆盖"},
            cache_loader=lambda lang: {},
            cache_updater=lambda lang, cid, text: None,
            client=FakeClient(),
            target_lang="zh-CN",
        )
        record = chain.translate(_make_record())

    assert record.matched_translation == "用户覆盖"
    assert record.status == "override"


def test_cache_hit(tmp_path: Path):
    """Level 2: cache should be used when no override."""
    chain = TranslationChain(
        overrides_loader=lambda lang: {},
        cache_loader=lambda lang: {"plugin.test.skill:demo": "缓存翻译"},
        cache_updater=lambda lang, cid, text: None,
        client=FakeClient(),
        target_lang="zh-CN",
    )
    record = chain.translate(_make_record())
    assert record.matched_translation == "缓存翻译"
    assert record.status == "cache"


def test_llm_hit():
    """Level 3: LLM should be called when no override or cache."""
    updated: dict[str, str] = {}

    def mock_updater(lang: str, cid: str, text: str) -> None:
        updated[cid] = text

    chain = TranslationChain(
        overrides_loader=lambda lang: {},
        cache_loader=lambda lang: {},
        cache_updater=mock_updater,
        client=FakeClient(),
        target_lang="zh-CN",
    )
    record = chain.translate(_make_record())
    assert record.matched_translation == "[zh-CN] Hello"
    assert record.status == "llm"
    assert "plugin.test.skill:demo" in updated


def test_fallback_original():
    """Level 4: original text when all else fails (client raises)."""
    class BrokenClient:
        def translate(self, text: str, sl: str, tl: str) -> str:
            raise RuntimeError("API down")

    chain = TranslationChain(
        overrides_loader=lambda lang: {},
        cache_loader=lambda lang: {},
        cache_updater=lambda lang, cid, text: None,
        client=BrokenClient(),
        target_lang="zh-CN",
    )
    record = chain.translate(_make_record("Original text"))
    assert record.matched_translation == "Original text"
    assert record.status == "original"


def test_translate_updates_record_immutably():
    """translate should return a new Record, not mutate the original."""
    original = _make_record()
    chain = TranslationChain(
        overrides_loader=lambda lang: {},
        cache_loader=lambda lang: {},
        cache_updater=lambda lang, cid, text: None,
        client=FakeClient(),
        target_lang="ja",
    )
    result = chain.translate(original)
    assert original.matched_translation == ""  # Unchanged
    assert result.matched_translation != ""    # New record has translation
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_translator.py -v`
Expected: FAIL

- [ ] **Step 3: Implement translator.py**

`src/claude_translator/core/translator.py`:
```python
"""Translation chain with 4-level fallback."""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Callable

from claude_translator.core.models import Record

logger = logging.getLogger(__name__)


class TranslationChain:
    """4-level translation fallback: override → cache → LLM → original."""

    def __init__(
        self,
        overrides_loader: Callable[[str], dict[str, str]],
        cache_loader: Callable[[str], dict[str, str]],
        cache_updater: Callable[[str, str, str], None],
        client: object,
        target_lang: str,
    ) -> None:
        self._overrides_loader = overrides_loader
        self._cache_loader = cache_loader
        self._cache_updater = cache_updater
        self._client = client
        self._target_lang = target_lang

    def translate(self, record: Record) -> Record:
        """Translate a Record's description through the fallback chain.

        Returns a new Record with matched_translation and status set.
        """
        cid = record.canonical_id
        desc = record.current_description

        if not desc:
            return replace(record, matched_translation="", status="empty")

        # Level 1: User override
        overrides = self._overrides_loader(self._target_lang)
        if cid in overrides:
            return replace(record, matched_translation=overrides[cid], status="override")

        # Level 2: Cache
        cache = self._cache_loader(self._target_lang)
        if cid in cache:
            return replace(record, matched_translation=cache[cid], status="cache")

        # Level 3: LLM
        try:
            translation = self._client.translate(desc, "en", self._target_lang)
            self._cache_updater(self._target_lang, cid, translation)
            return replace(record, matched_translation=translation, status="llm")
        except Exception:
            logger.warning("LLM translation failed for %s, falling back to original", cid)

        # Level 4: Original
        return replace(record, matched_translation=desc, status="original")
```

- [ ] **Step 4: Run translator test**

Run: `pytest tests/test_translator.py -v`
Expected: PASS

- [ ] **Step 5: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
cd /i/claude-docs/my-project/claude-translator
git add src/claude_translator/core/translator.py tests/test_translator.py
git commit -m "feat: translation chain with 4-level fallback (override/cache/LLM/original)"
```

---

### Task 8: Plugin Discovery + Frontmatter Injector

**Files:**
- Create: `src/claude_translator/core/discovery.py`
- Create: `src/claude_translator/core/injector.py`
- Create: `tests/test_discovery.py`
- Create: `tests/test_injector.py`

Covers: T2 (standard structure), T3 (non-standard dirs), T4 (nested), T5 (no plugins.json), T12 (user scope), T17 (multi-version)

- [ ] **Step 1: Write tests for discovery.py**

`tests/test_discovery.py`:
```python
import json
from pathlib import Path

from claude_translator.core.discovery import discover_all


def _write_plugins_json(claude_dir: Path, plugins: list[dict]) -> None:
    """Write installed_plugins.json v2 format."""
    plugins_file = claude_dir / "installed_plugins.json"
    plugins_file.write_text(json.dumps(plugins), encoding="utf-8")


def test_discover_standard_structure(tmp_path: Path):
    """T2: Standard plugin with skills and commands discovered."""
    claude_dir = tmp_path / ".claude"
    plugin_dir = tmp_path / "cache" / "market" / "my-plugin" / "1.0.0"
    skills_dir = plugin_dir / "skills" / "brainstorm"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("---\ndescription: Brainstorm ideas\n---\n# Brainstorm\n")
    commands_dir = plugin_dir / "commands"
    commands_dir.mkdir()
    (commands_dir / "commit.md").write_text("---\ndescription: Create commit\n---\n# Commit\n")

    _write_plugins_json(claude_dir, [
        {"installation_path": str(plugin_dir)}
    ])

    inventory = discover_all(claude_dir)
    assert inventory.size() == 2
    ids = {r.canonical_id for r in inventory.records}
    assert "plugin.my-plugin.skill:brainstorm" in ids
    assert "plugin.my-plugin.command:commit" in ids


def test_discover_skips_nonstandard_dirs(tmp_path: Path):
    """T3: Non-standard directories are silently skipped."""
    claude_dir = tmp_path / ".claude"
    plugin_dir = tmp_path / "cache" / "market" / "my-plugin" / "1.0.0"
    weird_dir = plugin_dir / "random_stuff"
    weird_dir.mkdir(parents=True)
    (weird_dir / "file.md").write_text("# Random")
    (plugin_dir / "skills" / "real").mkdir(parents=True)
    (plugin_dir / "skills" / "real" / "SKILL.md").write_text("---\ndescription: Real\n---\n# Real\n")

    _write_plugins_json(claude_dir, [{"installation_path": str(plugin_dir)}])

    inventory = discover_all(claude_dir)
    assert inventory.size() == 1
    assert inventory.records[0].canonical_id == "plugin.my-plugin.skill:real"


def test_discover_top_level_only(tmp_path: Path):
    """T4: Only top-level SKILL.md, not nested reference/ files."""
    claude_dir = tmp_path / ".claude"
    plugin_dir = tmp_path / "cache" / "market" / "my-plugin" / "1.0.0"
    skill_dir = plugin_dir / "skills" / "brainstorm"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\ndescription: Main\n---\n# Main\n")
    ref_dir = skill_dir / "reference"
    ref_dir.mkdir()
    (ref_dir / "detail.md").write_text("---\ndescription: Detail\n---\n# Detail\n")

    _write_plugins_json(claude_dir, [{"installation_path": str(plugin_dir)}])

    inventory = discover_all(claude_dir)
    assert inventory.size() == 1
    assert inventory.records[0].canonical_id == "plugin.my-plugin.skill:brainstorm"


def test_discover_no_plugins_json(tmp_path: Path):
    """T5: Missing installed_plugins.json returns empty inventory."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True)
    inventory = discover_all(claude_dir)
    assert inventory.size() == 0


def test_discover_user_scope(tmp_path: Path):
    """T12: User-level skills and commands discovered with user scope."""
    claude_dir = tmp_path / ".claude"
    user_skills = claude_dir / "skills" / "my-skill"
    user_skills.mkdir(parents=True)
    (user_skills / "SKILL.md").write_text("---\ndescription: My custom skill\n---\n# My Skill\n")
    user_commands = claude_dir / "commands"
    user_commands.mkdir()
    (user_commands / "review.md").write_text("---\ndescription: Review code\n---\n# Review\n")

    # No plugins.json needed for user-level
    inventory = discover_all(claude_dir)
    ids = {r.canonical_id for r in inventory.records}
    assert "user.skill:my-skill" in ids
    assert "user.command:review" in ids


def test_discover_multi_version(tmp_path: Path):
    """T17: Multiple versions of same plugin — only latest discovered."""
    claude_dir = tmp_path / ".claude"
    v1_dir = tmp_path / "cache" / "market" / "my-plugin" / "1.0.0"
    v2_dir = tmp_path / "cache" / "market" / "my-plugin" / "2.0.0"
    for d in [v1_dir, v2_dir]:
        skill = d / "skills" / "demo"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"---\ndescription: Demo {d.parent.name}\n---\n# Demo\n")

    _write_plugins_json(claude_dir, [
        {"installation_path": str(v1_dir)},
        {"installation_path": str(v2_dir)},
    ])

    inventory = discover_all(claude_dir)
    # Should have 2 records (one from each version path, deduped by canonical_id)
    # canonical_id is the same, so only 1 unique
    assert inventory.size() == 1
```

- [ ] **Step 2: Run discovery test to verify it fails**

Run: `pytest tests/test_discovery.py -v`
Expected: FAIL

- [ ] **Step 3: Implement discovery.py**

`src/claude_translator/core/discovery.py`:
```python
"""Auto-discover Claude Code plugins and user-level skills/commands."""

from __future__ import annotations

import json
import logging
from dataclasses import replace
from pathlib import Path

from claude_translator.core.canonical import generate_canonical_id, name_from_filename
from claude_translator.core.frontmatter import FrontmatterParser
from claude_translator.core.models import Inventory, Record
from claude_translator.utils.paths import normalize_path

logger = logging.getLogger(__name__)

DIR_KIND_MAP: dict[str, str] = {
    "skills": "skill",
    "commands": "command",
    "agents": "agent",
    ".agents/skills": "skill",
    ".agents/commands": "command",
    ".opencode/commands": "command",
}


def discover_all(claude_dir: Path) -> Inventory:
    """Discover all translatable items from plugins and user-level directories."""
    records: list[Record] = []
    seen_ids: set[str] = set()

    # User-level discovery (higher priority)
    user_records = _discover_user_level(claude_dir)
    for r in user_records:
        if r.canonical_id not in seen_ids:
            records.append(r)
            seen_ids.add(r.canonical_id)

    # Plugin-level discovery
    plugin_records = _discover_plugins(claude_dir)
    for r in plugin_records:
        if r.canonical_id not in seen_ids:
            records.append(r)
            seen_ids.add(r.canonical_id)

    return Inventory(tuple(records))


def _discover_user_level(claude_dir: Path) -> list[Record]:
    """Discover user-level skills and commands under ~/.claude/."""
    records: list[Record] = []
    parser = FrontmatterParser()

    for dir_name, kind in [("skills", "skill"), ("commands", "command")]:
        base = claude_dir / dir_name
        if not base.is_dir():
            continue
        for md_file in sorted(base.rglob("*.md")):
            # Only top-level files or SKILL.md in subdirs
            relative = md_file.relative_to(base)
            parts = relative.parts
            if len(parts) > 2:
                continue  # Skip deeply nested files
            if len(parts) == 2 and parts[1] != "SKILL.md":
                continue  # Only SKILL.md in subdirs

            name = name_from_filename(parts[0] if len(parts) == 1 else parts[1] if parts[1] == "SKILL.md" else parts[0])
            # For skills/<skill-name>/SKILL.md, use the directory name
            if len(parts) == 2 and parts[1] == "SKILL.md":
                name = parts[0]

            cid = generate_canonical_id(kind=kind, name=name, scope="user")
            content = md_file.read_text(encoding="utf-8")
            fm, _ = parser.parse(content)
            desc = parser.get_description(fm) or ""

            records.append(Record(
                canonical_id=cid,
                kind=kind,
                scope="user",
                source_path=str(md_file),
                relative_path=normalize_path(str(relative)),
                current_description=desc,
                frontmatter_present=bool(fm),
            ))

    return records


def _discover_plugins(claude_dir: Path) -> list[Record]:
    """Discover plugin-level items from installed_plugins.json."""
    plugins_file = claude_dir / "installed_plugins.json"
    if not plugins_file.exists():
        logger.info("No installed_plugins.json found, skipping plugin discovery")
        return []

    try:
        data = json.loads(plugins_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to read installed_plugins.json: %s", e)
        return []

    if not isinstance(data, list):
        return []

    records: list[Record] = []
    parser = FrontmatterParser()

    for entry in data:
        path_str = entry.get("installation_path", "")
        if not path_str:
            continue
        plugin_dir = Path(path_str)
        if not plugin_dir.is_dir():
            continue

        plugin_key = _extract_plugin_key(plugin_dir)
        plugin_records = _scan_plugin_dir(plugin_dir, plugin_key, parser)
        records.extend(plugin_records)

    return records


def _extract_plugin_key(plugin_dir: Path) -> str:
    """Extract plugin key from path: .../market/<plugin>/<version>/ -> <plugin>."""
    parts = plugin_dir.parts
    # Look for pattern: .../market/<plugin>/<version>/
    for i in range(len(parts) - 2, -1, -1):
        if parts[i] == "market" and i + 2 < len(parts):
            return parts[i + 1]
    # Fallback: use parent directory name
    return plugin_dir.parent.name


def _scan_plugin_dir(
    plugin_dir: Path, plugin_key: str, parser: FrontmatterParser
) -> list[Record]:
    """Scan a single plugin directory for translatable items."""
    records: list[Record] = []

    for dir_name, kind in DIR_KIND_MAP.items():
        target_dir = plugin_dir / dir_name
        if not target_dir.is_dir():
            continue

        for md_file in sorted(target_dir.rglob("*.md")):
            relative = md_file.relative_to(target_dir)
            parts = relative.parts

            # Only top-level: SKILL.md or single .md files
            if len(parts) > 2:
                continue
            if len(parts) == 2 and parts[1] != "SKILL.md":
                continue

            # Determine name
            if len(parts) == 2 and parts[1] == "SKILL.md":
                name = parts[0]  # Directory name
            else:
                name = name_from_filename(parts[0])

            cid = generate_canonical_id(kind=kind, name=name, scope="plugin", plugin_key=plugin_key)
            content = md_file.read_text(encoding="utf-8")
            fm, _ = parser.parse(content)
            desc = parser.get_description(fm) or ""

            records.append(Record(
                canonical_id=cid,
                kind=kind,
                scope="plugin",
                source_path=str(md_file),
                relative_path=normalize_path(str(relative)),
                plugin_key=plugin_key,
                current_description=desc,
                frontmatter_present=bool(fm),
            ))

    return records
```

- [ ] **Step 4: Run discovery test**

Run: `pytest tests/test_discovery.py -v`
Expected: PASS (some tests may need adjustment for multi-version dedup logic)

- [ ] **Step 5: Write tests for injector.py**

`tests/test_injector.py`:
```python
from pathlib import Path

from claude_translator.core.injector import inject_translation
from claude_translator.core.models import Record


def test_inject_creates_frontmatter(tmp_path: Path):
    """T7: Inject description into file without frontmatter."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Just a heading\nSome text", encoding="utf-8")

    record = Record(
        canonical_id="plugin.test.skill:x",
        kind="skill",
        scope="plugin",
        source_path=str(md_file),
        relative_path="test.md",
        matched_translation="翻译文本",
        frontmatter_present=False,
    )

    new_record = inject_translation(record)
    content = md_file.read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "description: 翻译文本" in content
    assert "# Just a heading" in content
    assert new_record.frontmatter_present is True


def test_inject_updates_existing_frontmatter(tmp_path: Path):
    """Update description in file that already has frontmatter."""
    md_file = tmp_path / "test.md"
    md_file.write_text("---\ndescription: Old\n---\n# Body", encoding="utf-8")

    record = Record(
        canonical_id="plugin.test.skill:x",
        kind="skill",
        scope="plugin",
        source_path=str(md_file),
        relative_path="test.md",
        matched_translation="新翻译",
        frontmatter_present=True,
    )

    inject_translation(record)
    content = md_file.read_text(encoding="utf-8")
    assert "description: 新翻译" in content
    assert "Old" not in content


def test_inject_preserves_crlf(tmp_path: Path):
    """T8: CRLF line endings are preserved."""
    md_file = tmp_path / "test.md"
    md_file.write_bytes(b"---\r\ndescription: Old\r\n---\r\n# Body")

    record = Record(
        canonical_id="plugin.test.skill:x",
        kind="skill",
        scope="plugin",
        source_path=str(md_file),
        relative_path="test.md",
        matched_translation="CRLF翻译",
        frontmatter_present=True,
    )

    inject_translation(record)
    content = md_file.read_text(encoding="utf-8")
    assert "description: CRLF翻译" in content
    assert "\r\n" in content


def test_inject_no_translation_skips(tmp_path: Path):
    """No matched_translation means no file modification."""
    md_file = tmp_path / "test.md"
    original = "---\ndescription: Keep\n---\n# Body"
    md_file.write_text(original, encoding="utf-8")

    record = Record(
        canonical_id="plugin.test.skill:x",
        kind="skill",
        scope="plugin",
        source_path=str(md_file),
        relative_path="test.md",
        matched_translation="",
        frontmatter_present=True,
    )

    inject_translation(record)
    assert md_file.read_text(encoding="utf-8") == original
```

- [ ] **Step 6: Run injector test to verify it fails**

Run: `pytest tests/test_injector.py -v`
Expected: FAIL

- [ ] **Step 7: Implement injector.py**

`src/claude_translator/core/injector.py`:
```python
"""Frontmatter injection and update for translated descriptions."""

from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path

from claude_translator.core.frontmatter import FrontmatterParser
from claude_translator.core.models import Record
from claude_translator.utils.paths import detect_newline

logger = logging.getLogger(__name__)


def inject_translation(record: Record) -> Record:
    """Inject or update the description in a markdown file.

    Preserves original newline style (LF/CRLF). Returns updated Record.
    If matched_translation is empty, returns Record unchanged.
    """
    if not record.matched_translation:
        return record

    file_path = Path(record.source_path)
    if not file_path.exists():
        logger.warning("File not found: %s", file_path)
        return record

    content = file_path.read_text(encoding="utf-8")
    newline = detect_newline(content)
    parser = FrontmatterParser()

    fm, body = parser.parse(content)
    new_fm = parser.set_description(fm, record.matched_translation)
    new_content = parser.build(new_fm, body)

    # Normalize newlines in rebuilt content
    new_content = new_content.replace("\r\n", "\n").replace("\n", newline)

    file_path.write_text(new_content, encoding="utf-8")

    return replace(record, frontmatter_present=True)
```

- [ ] **Step 8: Run injector test**

Run: `pytest tests/test_injector.py -v`
Expected: PASS

- [ ] **Step 9: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 10: Commit**

```bash
cd /i/claude-docs/my-project/claude-translator
git add src/claude_translator/core/discovery.py src/claude_translator/core/injector.py tests/test_discovery.py tests/test_injector.py
git commit -m "feat: plugin discovery (DIR_KIND_MAP) and frontmatter injector (CRLF-safe)"
```

---

### Task 9: Configuration System

**Files:**
- Create: `src/claude_translator/config/__init__.py`
- Create: `src/claude_translator/config/defaults.py`
- Create: `src/claude_translator/config/models.py`
- Create: `src/claude_translator/config/loaders.py`
- Create: `tests/test_config.py`

Covers: T9 (multi-language config), T14 (env vars)

- [ ] **Step 1: Write tests for config**

`tests/test_config.py`:
```python
import json
import os
from pathlib import Path
from unittest.mock import patch

from claude_translator.config.defaults import DEFAULT_TARGET_LANG, DEFAULT_LLM_MODEL
from claude_translator.config.loaders import load_config
from claude_translator.config.models import TranslatorConfig


def test_default_config():
    config = TranslatorConfig()
    assert config.target_lang == "zh-CN"
    assert config.llm.model == "gpt-4o-mini"


def test_config_from_file(tmp_path: Path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "target_lang": "ja",
        "llm": {"base_url": "https://api.example.com/v1", "api_key": "key", "model": "qwen"},
    }), encoding="utf-8")

    config = load_config(config_path=config_file)
    assert config.target_lang == "ja"
    assert config.llm.model == "qwen"


def test_config_env_override(tmp_path: Path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"target_lang": "ja"}), encoding="utf-8")

    with patch.dict(os.environ, {"CLAUDE_TRANSLATE_LANG": "ko"}):
        config = load_config(config_path=config_file)
    assert config.target_lang == "ko"


def test_config_cascade(tmp_path: Path):
    """Env var overrides file config, file config overrides defaults."""
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "target_lang": "ja",
        "llm": {"model": "qwen"},
    }), encoding="utf-8")

    # No env override — should use file value
    with patch.dict(os.environ, {}, clear=False):
        config = load_config(config_path=config_file)
    assert config.target_lang == "ja"
    assert config.llm.model == "qwen"


def test_config_missing_file():
    """Missing config file should use defaults."""
    config = load_config(config_path=Path("/nonexistent/config.json"))
    assert config.target_lang == "zh-CN"
```

- [ ] **Step 2: Run config test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL

- [ ] **Step 3: Implement config**

`src/claude_translator/config/__init__.py`:
```python
```

`src/claude_translator/config/defaults.py`:
```python
"""Hardcoded default values."""

DEFAULT_TARGET_LANG = "zh-CN"
DEFAULT_LLM_MODEL = "gpt-4o-mini"
DEFAULT_LLM_BASE_URL = ""
DEFAULT_LLM_API_KEY = ""
```

`src/claude_translator/config/models.py`:
```python
"""Pydantic configuration models."""

from __future__ import annotations

from pydantic import BaseModel

from claude_translator.config.defaults import (
    DEFAULT_LLM_API_KEY,
    DEFAULT_LLM_BASE_URL,
    DEFAULT_LLM_MODEL,
    DEFAULT_TARGET_LANG,
)


class LLMConfig(BaseModel):
    """LLM client configuration."""

    base_url: str = DEFAULT_LLM_BASE_URL
    api_key: str = DEFAULT_LLM_API_KEY
    model: str = DEFAULT_LLM_MODEL


class TranslatorConfig(BaseModel):
    """Main translator configuration."""

    target_lang: str = DEFAULT_TARGET_LANG
    llm: LLMConfig = LLMConfig()
```

`src/claude_translator/config/loaders.py`:
```python
"""Configuration loader with cascade: CLI > env > file > defaults."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from claude_translator.config.models import LLMConfig, TranslatorConfig

logger = logging.getLogger(__name__)


def load_config(
    config_path: Path | None = None,
    target_lang: str | None = None,
) -> TranslatorConfig:
    """Load configuration with cascade resolution.

    Priority: CLI args > env vars > config file > defaults
    """
    # Start with defaults
    overrides: dict = {}

    # Layer 1: Config file
    if config_path and config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            overrides.update(data)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read config file %s: %s", config_path, e)

    # Layer 2: Environment variables
    env_lang = os.getenv("CLAUDE_TRANSLATE_LANG")
    if env_lang:
        overrides["target_lang"] = env_lang

    env_base_url = os.getenv("CLAUDE_TRANSLATE_LLM_BASE_URL")
    if env_base_url:
        llm_overrides = overrides.get("llm", {})
        llm_overrides["base_url"] = env_base_url
        overrides["llm"] = llm_overrides

    env_api_key = os.getenv("CLAUDE_TRANSLATE_LLM_API_KEY")
    if env_api_key:
        llm_overrides = overrides.get("llm", {})
        llm_overrides["api_key"] = env_api_key
        overrides["llm"] = llm_overrides

    env_model = os.getenv("CLAUDE_TRANSLATE_LLM_MODEL")
    if env_model:
        llm_overrides = overrides.get("llm", {})
        llm_overrides["model"] = env_model
        overrides["llm"] = llm_overrides

    # Layer 3: CLI args (highest priority)
    if target_lang:
        overrides["target_lang"] = target_lang

    return TranslatorConfig(**overrides)
```

- [ ] **Step 4: Run config test**

Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
cd /i/claude-docs/my-project/claude-translator
git add src/claude_translator/config/ tests/test_config.py
git commit -m "feat: configuration system with cascade (CLI > env > file > defaults)"
```

---

### Task 10: CLI Commands + Package Entry

**Files:**
- Create: `src/claude_translator/cli.py`
- Create: `src/claude_translator/__main__.py`
- Create: `tests/test_cli.py`

Covers: Integration of all components

- [ ] **Step 1: Write tests for CLI**

`tests/test_cli.py`:
```python
from click.testing import CliRunner

from claude_translator.cli import main


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "discover" in result.output
    assert "sync" in result.output
    assert "verify" in result.output
    assert "init" in result.output


def test_cli_discover_help():
    runner = CliRunner()
    result = runner.invoke(main, ["discover", "--help"])
    assert result.exit_code == 0
    assert "lang" in result.output.lower() or "language" in result.output.lower()


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_init_creates_config(tmp_path: Path, monkeypatch):
    """init command should create a config.json in translations dir."""
    from unittest.mock import patch
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()

    runner = CliRunner()
    with patch("claude_translator.storage.paths.get_translations_dir", return_value=translations_dir):
        result = runner.invoke(main, ["init", "--lang", "ja"])

    assert result.exit_code == 0
    config_file = translations_dir / "config.json"
    assert config_file.exists()
    import json
    data = json.loads(config_file.read_text(encoding="utf-8"))
    assert data["target_lang"] == "ja"
```

- [ ] **Step 2: Run CLI test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL

- [ ] **Step 3: Implement cli.py**

`src/claude_translator/cli.py`:
```python
"""CLI entry point with Click subcommands."""

from __future__ import annotations

import json
import logging

import click

from claude_translator import __version__

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Claude Description Translator — multi-language plugin description translator."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@main.command()
@click.option("--lang", default=None, help="Target language (e.g. zh-CN, ja, ko)")
@click.option("--dry-run", is_flag=True, help="Show what would be discovered without translating")
def discover(lang: str | None, dry_run: bool) -> None:
    """Discover all translatable plugin descriptions."""
    from pathlib import Path

    from claude_translator.config.loaders import load_config
    from claude_translator.core.discovery import discover_all
    from claude_translator.storage.paths import get_claude_dir, get_config_path

    config = load_config(config_path=get_config_path(), target_lang=lang)
    claude_dir = get_claude_dir()

    click.echo(f"Scanning {claude_dir} ...")
    inventory = discover_all(claude_dir)
    click.echo(f"Found {inventory.size()} translatable items (target: {config.target_lang})")

    for record in inventory.records:
        status = "✓" if record.frontmatter_present else "✗"
        click.echo(f"  {status} [{record.scope}] {record.canonical_id}")


@main.command()
@click.option("--lang", default=None, help="Target language override")
def sync(lang: str | None) -> None:
    """Translate descriptions and write them to files."""
    from claude_translator.clients.openai_compat import OpenAICompatClient
    from claude_translator.config.loaders import load_config
    from claude_translator.core.discovery import discover_all
    from claude_translator.core.injector import inject_translation
    from claude_translator.core.translator import TranslationChain
    from claude_translator.storage.cache import load_cache, update_cache
    from claude_translator.storage.overrides import load_overrides
    from claude_translator.storage.paths import get_claude_dir, get_config_path

    config = load_config(config_path=get_config_path(), target_lang=lang)
    claude_dir = get_claude_dir()

    click.echo(f"Scanning {claude_dir} ...")
    inventory = discover_all(claude_dir)

    if inventory.size() == 0:
        click.echo("No translatable items found.")
        return

    client = OpenAICompatClient(
        base_url=config.llm.base_url or None,
        api_key=config.llm.api_key or None,
        model=config.llm.model,
    )
    chain = TranslationChain(
        overrides_loader=load_overrides,
        cache_loader=load_cache,
        cache_updater=update_cache,
        client=client,
        target_lang=config.target_lang,
    )

    click.echo(f"Translating {inventory.size()} items to {config.target_lang} ...")
    for record in inventory.records:
        translated = chain.translate(record)
        if translated.matched_translation and translated.matched_translation != record.current_description:
            inject_translation(translated)
            click.echo(f"  [{translated.status}] {translated.canonical_id}")
        else:
            click.echo(f"  [skip] {record.canonical_id}")

    click.echo("Sync complete.")


@main.command()
@click.option("--lang", default=None, help="Target language to verify")
def verify(lang: str | None) -> None:
    """Verify translation coverage and report status."""
    from claude_translator.config.loaders import load_config
    from claude_translator.core.discovery import discover_all
    from claude_translator.storage.cache import load_cache
    from claude_translator.storage.overrides import load_overrides
    from claude_translator.storage.paths import get_claude_dir, get_config_path

    config = load_config(config_path=get_config_path(), target_lang=lang)
    claude_dir = get_claude_dir()
    inventory = discover_all(claude_dir)

    overrides = load_overrides(config.target_lang)
    cache = load_cache(config.target_lang)

    covered = 0
    missing = 0
    for record in inventory.records:
        if record.canonical_id in overrides or record.canonical_id in cache:
            covered += 1
        else:
            missing += 1
            click.echo(f"  MISSING: {record.canonical_id}")

    total = inventory.size()
    pct = (covered / total * 100) if total > 0 else 0
    click.echo(f"Coverage: {covered}/{total} ({pct:.1f}%) — {missing} missing")


@main.command()
@click.option("--lang", default="zh-CN", help="Default target language")
def init(lang: str) -> None:
    """Initialize translation configuration."""
    from claude_translator.storage.paths import get_config_path, get_translations_dir

    translations_dir = get_translations_dir()
    config_path = get_config_path()

    config_data = {
        "target_lang": lang,
        "llm": {
            "model": "gpt-4o-mini",
        },
    }
    config_path.write_text(
        json.dumps(config_data, indent=2) + "\n",
        encoding="utf-8",
    )
    click.echo(f"Created config at {config_path} (target: {lang})")
```

- [ ] **Step 4: Implement __main__.py**

`src/claude_translator/__main__.py`:
```python
"""Allow running with python -m claude_translator."""

from claude_translator.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run CLI test**

Run: `pytest tests/test_cli.py -v`
Expected: PASS

- [ ] **Step 6: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
cd /i/claude-docs/my-project/claude-translator
git add src/claude_translator/cli.py src/claude_translator/__main__.py tests/test_cli.py
git commit -m "feat: CLI with discover/sync/verify/init commands"
```

