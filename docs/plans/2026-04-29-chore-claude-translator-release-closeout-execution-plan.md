---
title: chore: Claude Translator release closeout execution
type: chore
status: active
date: 2026-04-29
origin: docs/plans/2026-04-28-chore-claude-translator-opensource-release-closeout-plan.md
---

# chore: Claude Translator release closeout execution

## Overview

Execute the Claude Translator release closeout at the repository-state level. The prior sync and runbook documents established what the clean public repository should look like. This plan covers the actual execution sequence: verify the open-source publishing repository, create a precise local commit, verify that commit, stop before push, then handle push and local development follow-up only through separate gates.

This is not a new feature and not a new release. It is a release-chain governance closeout for the already-published `v0.5.0` state.

## Problem Statement / Motivation

The current state is split across two repositories:

- Local development repository: `I:/claude-docs/my-project/claude-translator`
- Open-source publishing repository: `I:/claude-docs/my-project/opensource/claude-translator`

The open-source publishing repository has already been transformed into a whitelist-shaped public candidate, but those changes are still pending locally. Until the open-source repository receives a reviewed local commit, the cleaned publishing tree is not durable. Until a separately approved push occurs, GitHub does not reflect the cleaned tree.

The goal of this execution plan is to close that gap without accidentally mutating tags, releases, unrelated files, or the local development repository.

## Current Evidence Baseline

Fresh read-only evidence before writing this plan showed:

### Open-source publishing repository

```text
## master
D .github/workflows/ci.yml
D .gitignore
M CHANGELOG.md
M README.ja.md
M README.ko.md
M README.md
M README.zh-CN.md
D REVIEW.md
D docs/superpowers/plans/2026-04-19-architecture-optimization-codex-runbook.md
D docs/superpowers/plans/2026-04-19-review-fixes.md
D docs/superpowers/specs/2026-04-19-architecture-optimization-design.md
D docs/superpowers/specs/2026-04-19-review-fixes-design.md
M src/claude_translator/__init__.py
M src/claude_translator/clients/async_fake.py
M src/claude_translator/clients/base.py
M src/claude_translator/core/pipeline.py
M src/claude_translator/core/translator.py
D tests/...
```

Diff stat baseline:

```text
47 files changed, 85 insertions(+), 7067 deletions(-)
```

Known interpretation:

- README four-language updates are intended.
- `src/claude_translator/__init__.py` fallback version update is intended.
- `.github`, `.gitignore`, `REVIEW.md`, `docs`, and `tests` deletions are intended publishing-tree cleanup.
- `CHANGELOG.md` and four source files may be line-ending residuals unless substantive diff proves otherwise.

### Local development repository

```text
## master...origin/master
M README.ja.md
M README.ko.md
M README.md
M README.zh-CN.md
M src/claude_translator/__init__.py
M tests/test_async_translator.py
M tests/test_cli.py
?? docs/plans/
?? docs/superpowers/plans/2026-04-28-claude-translator-open-source-sync.md
?? docs/superpowers/specs/2026-04-28-claude-translator-open-source-sync-design.md
```

Known interpretation:

- Local development repository changes are valid follow-up work but must not be mixed into the open-source publishing commit.

## Proposed Solution

Execute in four lanes:

| Lane | Purpose | Execution status | Boundary |
| --- | --- | --- | --- |
| Lane 1: Open-source local commit | Commit cleaned public publishing tree locally | Execute first | No push |
| Lane 2: Post-commit verification | Prove local open-source commit is safe | Execute immediately after Lane 1 | No push |
| Lane 3: Push gate | Push to GitHub only if explicitly approved | Stop and ask before execution | No tag/release mutation |
| Lane 4: Local development follow-up | Commit local dev docs/tests separately | Separate future task | Never mixed into Lane 1 |

Recommended immediate target: complete Lane 1 and Lane 2 only, then stop.

## Scope

### In scope for this execution plan

- Verify open-source publishing repository status, structure, README order, metadata, generated artifacts, and security boundary.
- Stage the intended open-source publishing cleanup using explicit paths only.
- Create one local open-source commit if all gates pass.
- Verify the local open-source commit.
- Prepare but do not execute push without explicit approval.
- Record local development repository follow-up as separate work.

### Out of scope

- No automatic push.
- No GitHub release edit.
- No tag edit.
- No force push.
- No new `v0.5.1` release.
- No restoration of `.gitignore`.
- No local development repository commit inside the open-source commit.
- Do not use `git add -A`.
- No broad `git add -A`.
- No mirror sync.

## Execution Phases

### Phase 1: Open-source preflight gate

**Goal:** Prove the open-source publishing repository is still the same candidate previously reviewed.

**Commands:**

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" status --short --branch --untracked-files=normal
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --stat
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --name-status
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --check
```

**Pass conditions:**

- Pending files match the intended publishing cleanup.
- No untracked generated artifacts appear.
- No whitespace errors are reported.
- No unrelated private/local files appear.

**Stop if:**

- New untracked files appear.
- A diff touches files outside the intended cleanup boundary.
- `diff --check` reports errors.

## Phase 2: Structure and generated-artifact gate

**Goal:** Prove the filesystem matches the approved public whitelist and has no generated artifacts.

**Command:**

```bash
python - <<'PY'
from pathlib import Path

root = Path(r"I:/claude-docs/my-project/opensource/claude-translator")
allowed = {
    "CHANGELOG.md",
    "LICENSE",
    "pyproject.toml",
    "README.md",
    "README.zh-CN.md",
    "README.ja.md",
    "README.ko.md",
    "src",
}
entries = {p.name for p in root.iterdir() if p.name != ".git"}
print("unexpected:", sorted(entries - allowed))
print("missing:", sorted(allowed - entries))
assert entries == allowed
patterns = [
    "**/__pycache__",
    "**/*.pyc",
    "**/.pytest_cache",
    "**/.ruff_cache",
    "**/.mypy_cache",
    "**/.coverage",
    "**/htmlcov",
    "**/build",
    "**/dist",
    "**/*.egg-info",
    "**/.pypirc",
    "**/*.pem",
    "**/*.key",
    "**/.env",
]
for pattern in patterns:
    matches = list(root.glob(pattern))
    print(pattern, len(matches))
    assert not matches, (pattern, [str(p.relative_to(root)) for p in matches[:20]])
print("structure and generated-artifact gate ok")
PY
```

**Pass conditions:**

- `unexpected: []`
- `missing: []`
- all artifact pattern counts are `0`

**Stop if:** any generated artifact or non-whitelist file appears.

### Phase 3: README, metadata, and CLI gate

**Goal:** Prove the public documentation and package metadata are aligned to `0.5.0`.

**Commands:**

```bash
python - <<'PY'
from pathlib import Path
import re
import tomllib

root = Path(r"I:/claude-docs/my-project/opensource/claude-translator")
versions = ["v0.5.0", "v0.4.0", "v0.3.0", "v0.2.0"]
for name in ["README.md", "README.zh-CN.md", "README.ja.md", "README.ko.md"]:
    text = (root / name).read_text(encoding="utf-8")
    positions = [text.index(v) for v in versions]
    print(name, positions)
    assert positions == sorted(positions), (name, positions)
pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
assert pyproject["project"]["version"] == "0.5.0"
assert pyproject["project"]["scripts"]["claude-translator"] == "claude_translator.cli:main"
init_text = (root / "src/claude_translator/__init__.py").read_text(encoding="utf-8")
assert re.search(r'__version__\s*=\s*"0\.5\.0"', init_text)
assert (root / "src/claude_translator/__main__.py").exists()
print("README and metadata gate ok")
PY

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="I:/claude-docs/my-project/opensource/claude-translator/src" python -m claude_translator --version
```

**Pass conditions:**

- All README positions are sorted.
- Version and fallback are `0.5.0`.
- CLI outputs `python -m claude_translator, version 0.5.0`.
- Phase 2 generated-artifact gate still passes after CLI smoke.

**Stop if:** CLI smoke creates artifacts or any metadata differs.

### Phase 4: Security and privacy gate

**Goal:** Prove the public repository has no high-confidence secrets or private paths while not blocking on harmless documentation field names.

**Command:**

```bash
python - <<'PY'
from pathlib import Path
import re

root = Path(r"I:/claude-docs/my-project/opensource/claude-translator")
bs = chr(92)
private_markers = [
    f"C:{bs}Users{bs}Windows11",
    f"I:{bs}",
    f"G:{bs}",
    f"F:{bs}",
    f"E:{bs}",
    "/c/Users/Windows11",
    "/i/claude-docs",
]
high_confidence_patterns = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
review_terms = ["OPENAI_API_KEY", "CLAUDE_TRANSLATE_LLM_API_KEY", "api_key", "token", "secret", "password", "private_key"]
blockers = []
reviewable = []
for path in root.rglob("*"):
    if ".git" in path.parts or not path.is_file():
        continue
    relative = path.relative_to(root)
    if path.name in {".pypirc"} or path.suffix.lower() in {".pem", ".key"}:
        blockers.append(f"{relative}: sensitive file type")
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    for index, line in enumerate(text.splitlines(), 1):
        if any(marker in line for marker in private_markers):
            blockers.append(f"{relative}:{index}:{line[:160]}")
        elif any(pattern.search(line) for pattern in high_confidence_patterns):
            blockers.append(f"{relative}:{index}:{line[:160]}")
        elif any(term in line for term in review_terms):
            reviewable.append(f"{relative}:{index}:{line[:160]}")
print("high_confidence_blockers:", len(blockers))
for hit in blockers[:20]:
    print(hit)
print("reviewable_mentions:", len(reviewable))
for hit in reviewable[:20]:
    print(hit)
if blockers:
    raise SystemExit(1)
print("sanitized scan ok")
PY
```

**Pass conditions:**

- `high_confidence_blockers: 0`
- Reviewable mentions are documented examples/config names, not real secrets.

**Stop if:** any high-confidence blocker exists.

### Phase 5: Line-ending residual gate

**Goal:** Separate real content changes from Git for Windows line-ending residuals before staging.

**Commands:**

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --numstat -- CHANGELOG.md src/claude_translator/clients/async_fake.py src/claude_translator/clients/base.py src/claude_translator/core/pipeline.py src/claude_translator/core/translator.py
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --summary -- CHANGELOG.md src/claude_translator/clients/async_fake.py src/claude_translator/clients/base.py src/claude_translator/core/pipeline.py src/claude_translator/core/translator.py
```

**Pass conditions:**

- Files with status `M` but empty `numstat`/`summary` are treated as line-ending residuals and not staged.
- Any file with real numstat output must be reviewed before staging.

**Stop if:** a supposed residual file has substantive diff that is not part of the intended release closeout.

### Phase 6: Precise staging gate

**Goal:** Stage exactly the intended open-source cleanup and nothing else.

**Commands:**

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" add README.md README.zh-CN.md README.ja.md README.ko.md src/claude_translator/__init__.py
git -C "I:/claude-docs/my-project/opensource/claude-translator" add -u .github .gitignore REVIEW.md docs tests

git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --cached --stat
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --cached --name-status
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --cached --check
```

**Pass conditions:**

- Staged diff contains only intended README, fallback version, and deletion cleanup.
- No generated artifacts are staged.
- No line-ending residuals are staged.
- `diff --cached --check` is clean.

**Stop if:** staged diff includes unexpected files.

### Phase 7: Local open-source commit

**Goal:** Create the local durable commit for the cleaned publishing repository.

**Command:**

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" commit -m "$(cat <<'EOF'
chore: clean open-source publishing tree

Keep the public publishing repository limited to release-ready source, metadata, license, changelog, and multilingual README files.
EOF
)"
```

**Pass conditions:**

- Commit succeeds without bypassing hooks.
- Commit SHA is recorded.

**Stop if:** hooks fail or commit output indicates unstaged/invalid state. Fix underlying issue; do not use `--no-verify`.

### Phase 8: Post-commit verification

**Goal:** Prove the local open-source commit is safe before any push decision.

**Commands:**

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" status --short --branch --untracked-files=normal
git -C "I:/claude-docs/my-project/opensource/claude-translator" log -1 --oneline
```

Then rerun:

- Phase 2 structure/generated-artifact gate
- Phase 3 README/metadata/CLI gate
- Phase 4 security/privacy gate

**Pass conditions:**

- Last commit is `chore: clean open-source publishing tree`.
- No generated artifacts.
- README/metadata/security gates pass.
- Any remaining worktree changes are explained residuals, not missed staged content.

**Stop point:** stop here and report. Do not push unless the user explicitly authorizes push.

### Phase 9: Push gate, separate approval only

**Goal:** Push the already-verified local open-source commit to GitHub only after explicit approval.

**Precondition:** User explicitly says to push.

**Commands after approval:**

The push gate includes the remote-tracking update equivalent to `git fetch origin master --prune`.

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" fetch origin master --prune
git -C "I:/claude-docs/my-project/opensource/claude-translator" status --short --branch
git -C "I:/claude-docs/my-project/opensource/claude-translator" rev-parse HEAD origin/master
git -C "I:/claude-docs/my-project/opensource/claude-translator" log --oneline --decorate -3
```

If topology is correct, then:

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" push origin master
```

Post-push verification:

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" status --short --branch
git -C "I:/claude-docs/my-project/opensource/claude-translator" rev-parse HEAD origin/master
gh release view v0.5.0 --repo debug-zhuweijian/claude-translator --json tagName,targetCommitish,isDraft,isPrerelease,url
```

**Pass conditions:**

- `HEAD` equals `origin/master` after push.
- GitHub release remains unchanged unless a separate release workflow is approved.

**Stop if:** remote advanced unexpectedly, push is rejected, release metadata differs, or user has not explicitly approved push.

### Phase 10: Local development follow-up, separate plan/commit

**Goal:** Keep local development governance changes separate.

Expected local development changes include:

- four README files
- `src/claude_translator/__init__.py`
- `tests/test_async_translator.py`
- `tests/test_cli.py`
- `docs/plans/`
- `docs/superpowers/plans/2026-04-28-claude-translator-open-source-sync.md`
- `docs/superpowers/specs/2026-04-28-claude-translator-open-source-sync-design.md`

This follow-up should be planned or executed only after the open-source local commit is verified. It must use its own status/diff/test/lint gate and its own commit decision.

## Acceptance Criteria

### Functional requirements

- [ ] Open-source repository local commit is created for the cleaned publishing tree.
- [ ] Open-source commit excludes generated artifacts and private/local files.
- [ ] README files remain multilingual and newest-first for `v0.5.0`, `v0.4.0`, `v0.3.0`, `v0.2.0`.
- [ ] Metadata and CLI report `0.5.0` from the open-source source tree.
- [ ] Push is not performed without explicit approval.
- [ ] GitHub release/tag is not mutated.
- [ ] Local development repository follow-up remains separate.

### Quality gates

- [ ] `git status`, `diff --stat`, `diff --name-status`, and `diff --check` reviewed before staging.
- [ ] Structure/generated-artifact scan passes before and after CLI smoke.
- [ ] Security scan reports zero high-confidence blockers.
- [ ] Staged diff is reviewed before commit.
- [ ] Post-commit gates rerun before push is discussed.

## Stop Conditions

Stop immediately and report if any of these occur:

- Unexpected untracked file appears in open-source repository.
- Generated artifact exists after CLI smoke.
- Security scan finds a high-confidence blocker.
- Line-ending residual file has substantive diff outside expected scope.
- Staged diff contains unexpected files.
- Commit hook fails.
- Push is requested but remote branch advanced unexpectedly.
- Any command would require `--no-verify`, force push, tag mutation, or release mutation.

## Rollback Plan

Before local commit:

- Unstage with explicit paths if staging is wrong.
- Do not use broad destructive cleanup.

After local commit but before push:

- Prefer a corrective commit if the issue is small.
- Use reset only with explicit user approval.

After push:

- Prefer `git revert` with a new commit.
- Do not force push by default.
- Use backup archive if deleted content must be recovered:
  - `I:/claude-docs/backup/manual/claude-translator/2026-04-28-opensource-whitelist-sync/`

## Success Metrics

- Open-source publishing repository has one local closeout commit that is easy to review.
- GitHub is not changed until the user separately approves push.
- GitHub release `v0.5.0` remains stable.
- The repository boundary is preserved: open-source clean publishing tree, local development full engineering workspace.
- The next operator can execute push or local development follow-up without re-discovering the release boundary.

## Sources & References

- `docs/plans/2026-04-28-chore-claude-translator-opensource-release-closeout-plan.md` — deepened runbook and gate definitions.
- `docs/superpowers/plans/2026-04-28-claude-translator-open-source-sync.md` — executed whitelist sync plan.
- `docs/superpowers/specs/2026-04-28-claude-translator-open-source-sync-design.md` — repository role and whitelist design.
- Current read-only repo baseline captured while writing this plan.
- Institutional constraints: whitelist staging, no broad add, multilingual README consistency, no unverified test merge, push/release closure discipline.
