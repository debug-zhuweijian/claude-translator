# Claude Translator Open Source Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert `I:/claude-docs/my-project/opensource/claude-translator` into a clean GitHub publishing source derived from the local development repository.

**Architecture:** The local repository remains the complete development workspace with tests, CI, docs, and dogfooding workflows. The open-source repository is curated by whitelist sync and then verified with structure, metadata, runtime smoke, README, security, and git checks.

**Tech Stack:** Python 3.10+, Click CLI, `src/` Python package layout, Git, Python standard library scripts for copy and verification.

---

## File Structure

### Local development repository

Root: `I:/claude-docs/my-project/claude-translator`

Files read or used as sync sources:

- `src/` — public package source copied to open-source repository.
- `pyproject.toml` — package metadata and CLI entry point copied to open-source repository.
- `README.md` — English README copied to open-source repository.
- `README.zh-CN.md` — Chinese README copied to open-source repository.
- `README.ja.md` — Japanese README copied to open-source repository.
- `README.ko.md` — Korean README copied to open-source repository.
- `LICENSE` — copied to open-source repository.
- `CHANGELOG.md` — copied to open-source repository.
- `docs/superpowers/specs/2026-04-28-claude-translator-open-source-sync-design.md` — source design spec.

Expected local-only files that must not be copied as publishable content:

- `tests/`
- `docs/`
- `.github/`
- `.coverage`
- `htmlcov/`
- `.pytest_cache/`
- `.ruff_cache/`

### Open-source publishing repository

Root: `I:/claude-docs/my-project/opensource/claude-translator`

Allowed final top-level content:

- `.git/`
- `src/`
- `pyproject.toml`
- `README.md`
- `README.zh-CN.md`
- `README.ja.md`
- `README.ko.md`
- `LICENSE`
- `CHANGELOG.md`

Disallowed final top-level content:

- `tests/`
- `docs/`
- `.github/`
- `.coverage`
- `htmlcov/`
- `.pytest_cache/`
- `.ruff_cache/`
- `*.egg-info/`
- `.env`

---

## Task 1: Preflight Status and Backup

**Files:**
- Read: `I:/claude-docs/my-project/claude-translator`
- Read/backup: `I:/claude-docs/my-project/opensource/claude-translator`
- Create: `I:/claude-docs/backup/manual/claude-translator/2026-04-28-opensource-whitelist-sync/`

- [ ] **Step 1: Verify both repositories exist and inspect status**

Run:

```bash
git -C "I:/claude-docs/my-project/claude-translator" status --short --branch
git -C "I:/claude-docs/my-project/opensource/claude-translator" status --short --branch
git -C "I:/claude-docs/my-project/opensource/claude-translator" stash list
```

Expected:

```text
local repository may show approved post-release changes
open-source repository is clean before sync
open-source stash list is empty
```

- [ ] **Step 2: Verify release refs are not being changed**

Run:

```bash
git -C "I:/claude-docs/my-project/claude-translator" rev-parse HEAD origin/master refs/tags/v0.5.0
git -C "I:/claude-docs/my-project/opensource/claude-translator" rev-parse HEAD origin/master refs/tags/v0.5.0
gh release view v0.5.0 --repo debug-zhuweijian/claude-translator --json tagName,targetCommitish,isDraft,isPrerelease,url
```

Expected:

```text
all local and open-source refs resolve to 48c16221062d5add70a3d1ecb02162bfe1850c21
GitHub release targetCommitish is 48c16221062d5add70a3d1ecb02162bfe1850c21
isDraft is false
isPrerelease is false
```

- [ ] **Step 3: Create backup directory**

Run:

```bash
BACKUP_DIR="/i/claude-docs/backup/manual/claude-translator/2026-04-28-opensource-whitelist-sync"
if [ -e "$BACKUP_DIR" ]; then
  echo "BACKUP_EXISTS $BACKUP_DIR"
  exit 1
fi
mkdir -p "$BACKUP_DIR"
```

Expected:

```text
command exits 0 and creates an empty backup directory
```

- [ ] **Step 4: Archive current open-source repository working tree**

Run:

```bash
BACKUP_DIR="/i/claude-docs/backup/manual/claude-translator/2026-04-28-opensource-whitelist-sync"
tar -C "I:/claude-docs/my-project/opensource" -cf "$BACKUP_DIR/claude-translator-before-sync.tar" "claude-translator"
git -C "I:/claude-docs/my-project/opensource/claude-translator" status --short --branch > "$BACKUP_DIR/status.before.txt"
git -C "I:/claude-docs/my-project/opensource/claude-translator" ls-files > "$BACKUP_DIR/tracked-files.before.txt"
sha256sum "$BACKUP_DIR"/* > "$BACKUP_DIR/checksums.before.sha256"
```

Expected:

```text
backup tar exists
status.before.txt exists
tracked-files.before.txt exists
checksums.before.sha256 exists
```

- [ ] **Step 5: Verify backup artifacts**

Run:

```bash
BACKUP_DIR="/i/claude-docs/backup/manual/claude-translator/2026-04-28-opensource-whitelist-sync"
ls -lh "$BACKUP_DIR"
sha256sum -c "$BACKUP_DIR/checksums.before.sha256"
```

Expected:

```text
all checksum entries report OK
```

---

## Task 2: Apply Whitelist Sync to Open-source Repository

**Files:**
- Copy from local: `src/`
- Copy from local: `pyproject.toml`
- Copy from local: `README.md`
- Copy from local: `README.zh-CN.md`
- Copy from local: `README.ja.md`
- Copy from local: `README.ko.md`
- Copy from local: `LICENSE`
- Copy from local: `CHANGELOG.md`
- Remove from open-source: `tests/`
- Remove from open-source: `docs/`
- Remove from open-source: `.github/`

- [ ] **Step 1: Run whitelist sync script**

Run:

```bash
python - <<'PY'
from pathlib import Path
import shutil

local = Path(r"I:/claude-docs/my-project/claude-translator")
opensource = Path(r"I:/claude-docs/my-project/opensource/claude-translator")

allowed_files = [
    "pyproject.toml",
    "README.md",
    "README.zh-CN.md",
    "README.ja.md",
    "README.ko.md",
    "LICENSE",
    "CHANGELOG.md",
]
allowed_dirs = ["src"]
disallowed_dirs = [
    "tests",
    "docs",
    ".github",
    "htmlcov",
    ".pytest_cache",
    ".ruff_cache",
]
disallowed_files = [".coverage", ".env"]

for relative in disallowed_dirs:
    target = opensource / relative
    if target.exists():
        shutil.rmtree(target)
        print(f"removed_dir {relative}")

for relative in disallowed_files:
    target = opensource / relative
    if target.exists():
        target.unlink()
        print(f"removed_file {relative}")

for relative in allowed_dirs:
    source = local / relative
    target = opensource / relative
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
    print(f"copied_dir {relative}")

for relative in allowed_files:
    source = local / relative
    target = opensource / relative
    shutil.copy2(source, target)
    print(f"copied_file {relative}")
PY
```

Expected output includes:

```text
removed_dir tests
removed_dir docs
removed_dir .github
copied_dir src
copied_file pyproject.toml
copied_file README.md
copied_file README.zh-CN.md
copied_file README.ja.md
copied_file README.ko.md
copied_file LICENSE
copied_file CHANGELOG.md
```

- [ ] **Step 2: Inspect open-source git status**

Run:

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" status --short
```

Expected:

```text
README files and src/__init__.py may be modified
removed paths include tests/, docs/, and .github/
no .coverage/htmlcov/cache files appear as untracked content
```

---

## Task 3: Structure Verification

**Files:**
- Verify: `I:/claude-docs/my-project/opensource/claude-translator`

- [ ] **Step 1: Run structure check**

Run:

```bash
python - <<'PY'
from pathlib import Path

root = Path(r"I:/claude-docs/my-project/opensource/claude-translator")
required = [
    "src",
    "pyproject.toml",
    "README.md",
    "README.zh-CN.md",
    "README.ja.md",
    "README.ko.md",
    "LICENSE",
    "CHANGELOG.md",
]
disallowed = [
    "tests",
    "docs",
    ".github",
    ".coverage",
    "htmlcov",
    ".pytest_cache",
    ".ruff_cache",
    ".env",
]
missing = [name for name in required if not (root / name).exists()]
present_disallowed = [name for name in disallowed if (root / name).exists()]
if missing:
    print("MISSING", missing)
if present_disallowed:
    print("DISALLOWED", present_disallowed)
if missing or present_disallowed:
    raise SystemExit(1)
print("structure ok")
PY
```

Expected:

```text
structure ok
```

- [ ] **Step 2: List final top-level files**

Run:

```bash
python - <<'PY'
from pathlib import Path
root = Path(r"I:/claude-docs/my-project/opensource/claude-translator")
for path in sorted(root.iterdir(), key=lambda p: p.name.lower()):
    if path.name == ".git":
        continue
    kind = "dir" if path.is_dir() else "file"
    print(f"{kind} {path.name}")
PY
```

Expected:

```text
file CHANGELOG.md
file LICENSE
file README.ja.md
file README.ko.md
file README.md
file README.zh-CN.md
file pyproject.toml
dir src
```

---

## Task 4: Metadata and Runtime Smoke Verification

**Files:**
- Verify: `pyproject.toml`
- Verify: `src/claude_translator/__init__.py`
- Verify: `src/claude_translator/__main__.py`

- [ ] **Step 1: Run metadata consistency check**

Run:

```bash
python - <<'PY'
from pathlib import Path
import re
import tomllib

root = Path(r"I:/claude-docs/my-project/opensource/claude-translator")
pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
version = pyproject["project"]["version"]
script = pyproject["project"]["scripts"]["claude-translator"]
init_text = (root / "src/claude_translator/__init__.py").read_text(encoding="utf-8")
main_file = root / "src/claude_translator/__main__.py"
assert version == "0.5.0", version
assert script == "claude_translator.cli:main", script
assert re.search(r'__version__\s*=\s*"0\.5\.0"', init_text), "fallback __version__ is not 0.5.0"
assert main_file.exists(), "__main__.py missing"
print("metadata ok")
PY
```

Expected:

```text
metadata ok
```

- [ ] **Step 2: Run CLI version smoke test from open-source source tree**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="I:/claude-docs/my-project/opensource/claude-translator/src" python -m claude_translator --version
```

Expected:

```text
python -m claude_translator, version 0.5.0
```

- [ ] **Step 3: Run import smoke test from open-source source tree**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="I:/claude-docs/my-project/opensource/claude-translator/src" python - <<'PY'
import claude_translator
print(claude_translator.__version__)
PY
```

Expected:

```text
0.5.0
```

---

## Task 5: README Verification

**Files:**
- Verify: `README.md`
- Verify: `README.zh-CN.md`
- Verify: `README.ja.md`
- Verify: `README.ko.md`

- [ ] **Step 1: Verify README version order**

Run:

```bash
python - <<'PY'
from pathlib import Path
root = Path(r"I:/claude-docs/my-project/opensource/claude-translator")
versions = ["v0.5.0", "v0.4.0", "v0.3.0", "v0.2.0"]
for name in ["README.md", "README.zh-CN.md", "README.ja.md", "README.ko.md"]:
    text = (root / name).read_text(encoding="utf-8")
    missing = [version for version in versions if version not in text]
    if missing:
        raise SystemExit(f"{name} missing {missing}")
    positions = [text.index(version) for version in versions]
    if positions != sorted(positions):
        raise SystemExit(f"{name} version order invalid: {positions}")
    print(f"{name} ok")
PY
```

Expected:

```text
README.md ok
README.zh-CN.md ok
README.ja.md ok
README.ko.md ok
```

---

## Task 6: Security and Privacy Scan

**Files:**
- Scan: `I:/claude-docs/my-project/opensource/claude-translator`

- [ ] **Step 1: Scan for local paths and private configuration markers**

Run:

```bash
python - <<'PY'
from pathlib import Path

root = Path(r"I:/claude-docs/my-project/opensource/claude-translator")
patterns = [
    "C:\\",
    "I:\\",
    "G:\\",
    "/c/Users",
    "Users\\Windows11",
    ".claude",
    "CLAUDE.md",
]
allowed_dirs = {".git"}
violations = []
for path in root.rglob("*"):
    if any(part in allowed_dirs for part in path.relative_to(root).parts):
        continue
    if path.is_dir():
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for pattern in patterns:
        if pattern in text:
            violations.append((path.relative_to(root).as_posix(), pattern))
if violations:
    for file, pattern in violations:
        print(f"VIOLATION {file}: {pattern}")
    raise SystemExit(1)
print("local path scan ok")
PY
```

Expected:

```text
local path scan ok
```

- [ ] **Step 2: Scan for likely secrets**

Run:

```bash
python - <<'PY'
from pathlib import Path
import re

root = Path(r"I:/claude-docs/my-project/opensource/claude-translator")
secret_patterns = {
    "generic_assignment": re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    "openai_key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
}
allowed_dirs = {".git"}
violations = []
for path in root.rglob("*"):
    if any(part in allowed_dirs for part in path.relative_to(root).parts):
        continue
    if path.is_dir():
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for name, pattern in secret_patterns.items():
        if pattern.search(text):
            violations.append((path.relative_to(root).as_posix(), name))
if violations:
    for file, name in violations:
        print(f"SECRET_LIKE {file}: {name}")
    raise SystemExit(1)
print("secret scan ok")
PY
```

Expected:

```text
secret scan ok
```

- [ ] **Step 3: Verify no generated or cache artifacts are present**

Run:

```bash
python - <<'PY'
from pathlib import Path
root = Path(r"I:/claude-docs/my-project/opensource/claude-translator")
forbidden = []
for path in root.rglob("*"):
    rel = path.relative_to(root).as_posix()
    if ".git/" in rel or rel == ".git":
        continue
    if path.name in {".coverage", ".pytest_cache", ".ruff_cache", "htmlcov", "__pycache__"}:
        forbidden.append(rel)
    if path.suffix in {".pyc", ".pyo"}:
        forbidden.append(rel)
if forbidden:
    for rel in forbidden:
        print(f"FORBIDDEN_ARTIFACT {rel}")
    raise SystemExit(1)
print("artifact scan ok")
PY
```

Expected:

```text
artifact scan ok
```

---

## Task 7: Final Git Review and No-Publish Gate

**Files:**
- Review: open-source repository git diff
- Review: local development repository git diff

- [ ] **Step 1: Review open-source repository changes**

Run:

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" status --short
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --stat
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --name-status
```

Expected:

```text
changes are limited to allowed whitelist sync and deletion of disallowed directories
no push is performed
```

- [ ] **Step 2: Review local development repository changes**

Run:

```bash
git -C "I:/claude-docs/my-project/claude-translator" status --short
git -C "I:/claude-docs/my-project/claude-translator" diff --stat
```

Expected:

```text
local repository includes existing post-release cleanup changes and the new design/plan documents
no local tests are deleted
```

- [ ] **Step 3: Confirm release state remains unchanged**

Run:

```bash
gh release view v0.5.0 --repo debug-zhuweijian/claude-translator --json tagName,targetCommitish,isDraft,isPrerelease,url
```

Expected:

```text
tagName is v0.5.0
targetCommitish is 48c16221062d5add70a3d1ecb02162bfe1850c21
isDraft is false
isPrerelease is false
```

- [ ] **Step 4: Stop before commit or push**

Do not commit, push, tag, or edit GitHub releases in this plan unless the user gives a separate explicit instruction.

Expected final report:

```text
open-source folder structure is clean
README files are current
metadata is current
CLI smoke test passes
security scans pass
no release mutation occurred
ready for user decision on commit/push
```

---

## Self-Review

Spec coverage:

- Local development repository remains complete: covered by Task 7 Step 2.
- Open-source repository whitelist content: covered by Task 2 and Task 3.
- Four README files retained and checked: covered by Task 2 and Task 5.
- Tests excluded from open-source repository: covered by Task 2 and Task 3.
- `CHANGELOG.md` retained: covered by Task 2 and Task 3.
- Safety review before treating open-source as publishable: covered by Task 6.
- No tag/release mutation: covered by Task 1, Task 7, and no-publish gate.

Placeholder scan:

- No TBD, TODO, placeholder, or unspecified implementation steps remain.

Type and command consistency:

- Paths consistently use `I:/claude-docs/my-project/claude-translator` and `I:/claude-docs/my-project/opensource/claude-translator`.
- Version consistently uses `0.5.0` and release commit `48c16221062d5add70a3d1ecb02162bfe1850c21`.
