---
title: chore: Claude Translator opensource release closeout
type: chore
status: active
date: 2026-04-28
origin: docs/superpowers/specs/2026-04-28-claude-translator-open-source-sync-design.md
---

# chore: Claude Translator opensource release closeout

## Enhancement Summary

**Deepened on:** 2026-04-29
**Purpose:** Strengthen this document as a release closeout runbook. This deepening does not execute release closeout, stage files, commit, push, edit tags, or mutate GitHub releases.

**Sections enhanced:** Current Evidence Baseline, Proposed Solution, Technical Considerations, System-Wide Impact, Implementation Plan, Acceptance Criteria, Dependencies & Risks, Rollback Plan, Sources & References.

**Review inputs used:**

- Target plan selection from read-only exploration.
- Runbook-quality planning review.
- Technical review findings on security scanning, generated artifact recursion, push-gate fetch boundaries, `.gitignore` absence, and line-ending residual handling.

**Key improvements:**

1. Separated plan-deepening from release execution.
2. Added phase-level preconditions, allowed actions, stop conditions, evidence records, and approval boundaries.
3. Replaced broad security-marker blocking with a high-confidence blocker plus false-positive review model.
4. Required recursive generated-artifact scanning.
5. Added explicit line-ending residual stop/continue criteria.
6. Preserved push as a separate approval gate and release/tag mutation as out of scope.
7. Kept local development repository closeout as a separate follow-up track.

**Non-negotiable constraints:**

- Do not push automatically.
- Do not edit GitHub release metadata.
- Do not edit, move, recreate, or delete tags.
- Do not force push.
- Do not use `git add -A`.
- Do not mix local development repository changes into the open-source publishing commit.
- Do not reintroduce `.gitignore` unless a separate design change is approved.

## Overview

Close out the post-sync release governance work for Claude Translator by turning the already-verified open-source publishing repository into a committed, reviewable state, then optionally pushing it to GitHub under a separate explicit gate.

This plan does not redesign the sync. The whitelist sync has already been executed and verified. The remaining work is release-chain closure: precise staging, commit hygiene, optional remote push, post-push verification, and local development repository separation.

This plan is a runbook for a future execution step. Plan deepening itself only improves this document; it does not perform commit, push, tag, release, cleanup, test, install, or smoke-test actions.

## Problem Statement / Motivation

Claude Translator currently has two deliberately different repositories:

- Local development repository: `I:/claude-docs/my-project/claude-translator`
- Open-source publishing repository: `I:/claude-docs/my-project/opensource/claude-translator`

The development repository is the full engineering workspace with tests, docs, CI, plans, dogfooding artifacts, and local validation. The open-source repository is the public GitHub publishing source and must contain only release-ready public content.

The open-source repository has been transformed into the desired whitelist shape, but the transformation is still uncommitted. Until it is committed and optionally pushed, the work is locally valid but not durable or visible on GitHub.

Do not confuse the two roles. The development repository is allowed to carry tests, docs, plans, and governance files. The open-source publishing repository is intentionally curated and should not be treated as a full mirror.

## Current Evidence Baseline

Fresh verification before this plan showed:

- Open-source top-level whitelist is valid:
  - `CHANGELOG.md`
  - `LICENSE`
  - `pyproject.toml`
  - `README.md`
  - `README.zh-CN.md`
  - `README.ja.md`
  - `README.ko.md`
  - `src/`
- Four README files preserve newest-first release order:
  - `v0.5.0`
  - `v0.4.0`
  - `v0.3.0`
  - `v0.2.0`
- Python metadata is aligned:
  - `pyproject.toml` version is `0.5.0`
  - CLI script is `claude_translator.cli:main`
  - `src/claude_translator/__init__.py` fallback is `0.5.0`
  - `src/claude_translator/__main__.py` exists
- CLI smoke test passed with local open-source source tree:
  - `python -m claude_translator, version 0.5.0`
- GitHub release state is unchanged:
  - `tagName=v0.5.0`
  - `targetCommitish=48c16221062d5add70a3d1ecb02162bfe1850c21`
  - `isDraft=false`
  - `isPrerelease=false`
- Security scan excluding `.git` passed:
  - `secret_literal_hits: 0`
  - `private_path_hits: 0`
- Independent review found generated `__pycache__` files; they were removed and rechecked:
  - no `__pycache__`
  - no `*.pyc`
- No commit or push has been performed during this closeout.

### Research Insights

Evidence freshness decays. The bullets above are a baseline, not permission to commit or push. Every execution of this runbook must rerun the relevant status, diff, structure, README, metadata, security, and release checks.

Treat verification output as scoped evidence:

- A structure check proves only the current filesystem shape at that moment.
- A metadata check proves only the current source tree metadata at that moment.
- A CLI smoke test can create bytecode unless `PYTHONDONTWRITEBYTECODE=1` is set.
- A GitHub release view is read-only evidence and must not become a release edit step.

If any future check differs from the baseline, stop and re-audit before staging.

## Proposed Solution

Use a two-track closeout:

1. **Open-source publishing repository closeout**
   - Precisely stage only the intended public publishing-tree transformation.
   - Commit it locally.
   - Re-run structure, metadata, README, security, and git checks.
   - Stop before push unless explicitly approved.

2. **Local development repository closeout**
   - Keep development-only changes separate.
   - Commit README/version/test/design-plan changes only after the publishing repository is safe.
   - Do not mix local development governance artifacts into the open-source publishing commit.

### Research Insights

Use four explicit lanes so the operator never blends planning, commit, push, and local development follow-up:

| Lane | Purpose | Allowed actions | Approval boundary |
| --- | --- | --- | --- |
| Plan deepening | Improve this runbook only | Edit the target plan file | No release execution |
| Open-source local commit | Commit publishing-tree cleanup | Precise staging and local commit after verification | No push |
| Push gate | Update GitHub branch | Push only after explicit approval and remote-state check | No release/tag mutation |
| Local dev follow-up | Commit development repo docs/tests | Separate local development commit after separate verification | Never mixed with open-source commit |

The recommended order is: finish the open-source local commit first, verify it, then stop. Push and local development commit are separate decisions.

## Scope

### In scope

- Verify the open-source repository still matches the whitelist structure.
- Ensure generated caches are absent before staging.
- Stage and commit the open-source repository changes if approved.
- Keep push as a separate explicit gate.
- Verify the GitHub release is not mutated.
- Verify local development repository still keeps tests/docs.
- Record local development repository cleanup as a separate follow-up track; do not execute it inside the open-source closeout unless separately approved.
- Verify remote branch state immediately before any push gate.

### Out of scope

- No GitHub release edit.
- No tag edit.
- No force push.
- No release re-upload.
- No `v0.5.1` release unless separately planned.
- No mirror sync.
- No deletion of local development tests/docs.
- No broad refactor or new feature work.
- No restoration of `.gitignore` unless a separate design change is approved.

## Technical Considerations

### Repository roles

`I:/claude-docs/my-project/claude-translator` remains complete and may contain:

- `tests/`
- `docs/`
- `.github/`
- development plans/specs
- validation-only files

`I:/claude-docs/my-project/opensource/claude-translator` should contain only:

- package source under `src/`
- package metadata
- four README files
- license
- changelog

### Line-ending noise

Fresh status showed `src/claude_translator/clients/async_fake.py`, `src/claude_translator/clients/base.py`, `src/claude_translator/core/pipeline.py`, and `src/claude_translator/core/translator.py` as modified in the open-source repository, but `git diff --numstat` and `git diff --summary` for those files emitted no substantive changes. Treat them as Git for Windows line-ending noise unless a final diff proves otherwise.

Do not stage line-ending-only files just because they appear in `git status`.

### `.gitignore` deletion

The open-source repository whitelist intentionally excludes `.gitignore`. This is acceptable only if every pre-commit check confirms no generated files remain untracked. Because no `.gitignore` will protect the repository, the closeout must explicitly scan for:

- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`
- `.ruff_cache/`
- `.mypy_cache/`
- `.coverage`
- `htmlcov/`
- `build/`
- `dist/`
- `*.egg-info/`
- `.pypirc`
- `*.pem`
- `*.key`
- `.env`

Do not reintroduce `.gitignore` during this runbook. If a minimal `.gitignore` becomes desirable later, treat that as a separate design change and approval gate.

### CHANGELOG behavior

`CHANGELOG.md` is allowed in the open-source repository. If it appears modified only because of line endings, avoid staging it unless the diff contains real intended content.

### Research Insights

**Line-ending residuals:** If `git status` shows `M` but `git diff --numstat` and `git diff --summary` are empty for a file, classify it as a line-ending residual and do not stage it. If line-level diff appears, re-audit whether the file belongs in the closeout commit.

**Generated artifacts:** Use recursive traversal (`rglob` or equivalent `**/` patterns), not only top-level globs. Generated files can appear under nested package directories after Python smoke tests.

**Bytecode safety:** Every CLI or import smoke command must include `PYTHONDONTWRITEBYTECODE=1`. This is especially important because `.gitignore` is intentionally absent.

**Security scan model:** Do not fail the runbook solely because README or code contains field names like `OPENAI_API_KEY`, `api_key`, `token`, or `secret`. Split findings into:

- **High-confidence blockers:** real key-like values, `sk-...` style secrets, Bearer token values, private key file contents, `.pypirc`, `*.pem`, `*.key`, private absolute paths such as the operator's machine paths.
- **Reviewable false positives:** public environment variable names, configuration field names, example placeholders, and documentation text.

Only high-confidence blockers should stop immediately. Reviewable false positives must be listed and explained.

## System-Wide Impact

### Interaction graph

1. Local development changes feed into the open-source publishing repository by whitelist sync.
2. Open-source repository commit becomes the GitHub repository state after push.
3. GitHub release `v0.5.0` remains pointed at the existing release commit unless a separate release workflow changes it.
4. Users browsing the GitHub repository after push see the cleaned publishing tree, but existing release artifacts/tags remain unchanged.

```text
local dev repo -> whitelist sync -> local opensource repo commit -> optional push -> GitHub branch
                                           |
                                           v
                                GitHub release/tag unchanged
```

### Error and failure propagation

- If staging includes line-ending noise, the commit may become harder to review and may obscure the intended publishing-tree transformation.
- If generated caches are present, GitHub may receive Python runtime artifacts.
- If push happens before local commit verification, the remote may expose incomplete cleanup.
- If a release edit happens accidentally, published release semantics become ambiguous.

### State lifecycle risks

- Partial commit risk: deleting tests/docs without README/version changes would leave a reduced repository with stale documentation.
- Push-before-review risk: remote branch changes become visible before validating the tree.
- Local/open-source mixing risk: committing local development specs into the publishing repository would leak process artifacts.

### API surface parity

No runtime API change is intended in this closeout. The only source change expected in open-source content is `src/claude_translator/__init__.py` fallback version alignment to `0.5.0`, plus any already-synced public source content that has substantive diff.

### Integration test scenarios

- Install/import smoke uses `PYTHONPATH` pointed to the open-source `src/` tree.
- CLI version smoke runs with `PYTHONDONTWRITEBYTECODE=1` to avoid generating `__pycache__`.
- README order check covers all four language variants.
- Security scan excludes `.git` and checks non-git files for real secrets/private paths.

### Research Insights

Cleaning the GitHub repository branch does not change the immutable meaning of the already-created `v0.5.0` release. A push affects the branch view and future visitors browsing the repository. It does not rewrite the tag or release artifact unless a separate tag/release command is run.

Therefore, release/tag commands must remain absent from this runbook except read-only `gh release view` checks.

## Implementation Plan

### Phase 1: Pre-commit evidence gate for open-source repository

**Preconditions:** The operator is ready to inspect the open-source repository but has not staged anything for the closeout commit.
**Allowed actions:** Read-only git status and diff inspection.
**Stop if:** Untracked generated artifacts appear, unexpected private/local files appear, or deletions extend beyond intended excluded content.
**Evidence to record:** `status --short --branch --untracked-files=normal`, `diff --stat`, and `diff --name-status`.
**Approval boundary:** This phase does not stage, commit, or push.

Run from any directory using explicit `git -C` paths.

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" status --short --branch --untracked-files=normal
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --stat
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --name-status
```

Pass conditions:

- Untracked generated artifacts are absent.
- Deletions are limited to intended excluded content.
- README and fallback changes are present.
- No unexpected private/local files appear.

### Phase 2: Structure and cache gate

**Preconditions:** Phase 1 has no unexpected files or scope drift.
**Allowed actions:** Read-only filesystem scan.
**Stop if:** Top-level whitelist differs, or any generated/private artifact exists at any depth.
**Evidence to record:** Whitelist result and generated artifact counts.
**Approval boundary:** This phase does not clean files automatically; cleanup requires a separate deliberate action.

Run:

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
assert entries == allowed, {"unexpected": sorted(entries - allowed), "missing": sorted(allowed - entries)}
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
    assert not matches, (pattern, [str(p.relative_to(root)) for p in matches[:20]])
print("structure and cache gate ok")
PY
```

### Phase 3: README and metadata gate

**Preconditions:** Structure and generated artifact checks passed.
**Allowed actions:** Read-only README and metadata inspection; bytecode-disabled CLI smoke.
**Stop if:** README version order differs, metadata is not `0.5.0`, CLI entry point differs, fallback version differs, or CLI smoke writes generated artifacts.
**Evidence to record:** README order result, metadata result, CLI version output.
**Approval boundary:** This phase does not edit README, metadata, or source files.

Run:

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
    assert positions == sorted(positions), (name, positions)
pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
assert pyproject["project"]["version"] == "0.5.0"
assert pyproject["project"]["scripts"]["claude-translator"] == "claude_translator.cli:main"
init_text = (root / "src/claude_translator/__init__.py").read_text(encoding="utf-8")
assert re.search(r'__version__\s*=\s*"0\.5\.0"', init_text)
assert (root / "src/claude_translator/__main__.py").exists()
print("README and metadata gate ok")
PY
```

Run CLI smoke without bytecode writes:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="I:/claude-docs/my-project/opensource/claude-translator/src" python -m claude_translator --version
```

Expected:

```text
python -m claude_translator, version 0.5.0
```

After the CLI smoke, rerun Phase 2 generated-artifact checks.

### Phase 4: Security gate

**Preconditions:** Structure, generated artifacts, README, metadata, and CLI checks passed.
**Allowed actions:** Read-only scan of non-`.git` files.
**Stop if:** A high-confidence secret, private key, private path, `.pypirc`, `*.pem`, or `*.key` is found.
**Evidence to record:** High-confidence blocker count and reviewable false-positive count.
**Approval boundary:** This phase does not edit or redact files automatically.

Run a two-layer scan that avoids regex backslash pitfalls and avoids blocking on harmless field names:

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

Reviewable mentions are acceptable only when they are public documentation labels, configuration field names, or placeholder examples. Record the explanation in the operator report.

### Phase 5: Precise staging and local commit

**Preconditions:** Phases 1-4 passed, including post-CLI generated artifact scan.
**Allowed actions:** Precise staging, staged diff review, local commit.
**Stop if:** Staged diff includes generated files, private files, line-ending-only noise, unrelated source changes, or local development artifacts.
**Evidence to record:** Pre-stage diff, staged diff stat, staged name-status, staged whitespace check, commit SHA.
**Approval boundary:** This phase creates a local commit only; it does not push.

Before staging, inspect substantive diff for allowed files:

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff -- README.md README.zh-CN.md README.ja.md README.ko.md src/claude_translator/__init__.py
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --name-status -- .github .gitignore REVIEW.md docs tests
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --numstat -- CHANGELOG.md src/claude_translator/clients/async_fake.py src/claude_translator/clients/base.py src/claude_translator/core/pipeline.py src/claude_translator/core/translator.py
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --summary -- CHANGELOG.md src/claude_translator/clients/async_fake.py src/claude_translator/clients/base.py src/claude_translator/core/pipeline.py src/claude_translator/core/translator.py
```

Stage only intended paths. Do not use `git add -A`.

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" add README.md README.zh-CN.md README.ja.md README.ko.md src/claude_translator/__init__.py
git -C "I:/claude-docs/my-project/opensource/claude-translator" add -u .github .gitignore REVIEW.md docs tests
```

If `CHANGELOG.md` has a substantive intended diff, stage it explicitly. If it is line-ending-only, do not stage it.

Then review staged content:

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --cached --stat
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --cached --name-status
git -C "I:/claude-docs/my-project/opensource/claude-translator" diff --cached --check
```

Commit with:

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" commit -m "$(cat <<'EOF'
chore: clean open-source publishing tree

Keep the public publishing repository limited to release-ready source, metadata, license, changelog, and multilingual README files.
EOF
)"
```

### Phase 6: Post-commit open-source verification

**Preconditions:** Phase 5 local commit succeeded.
**Allowed actions:** Read-only post-commit verification.
**Stop if:** Working tree contains unexpected changes, generated artifacts return, metadata drifts, or the last commit is not the intended closeout commit.
**Evidence to record:** Working tree status, last commit, repeated structure/cache/README/metadata/security results.
**Approval boundary:** This phase does not push.

Run:

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" status --short --branch --untracked-files=normal
git -C "I:/claude-docs/my-project/opensource/claude-translator" log -1 --oneline
```

Repeat Phases 2, 3, and 4 after commit.

Pass conditions:

- No generated files are present.
- Working tree is clean except acceptable line-ending residuals only if unavoidable and unstaged.
- The last commit is the open-source publishing-tree closeout commit.

### Phase 7: Push gate, only after explicit approval

**Preconditions:** Phase 6 passed and the user explicitly approves push.
**Allowed actions before push approval:** Read-only local status; future push gate may run `git fetch` to update remote-tracking refs.
**Stop if:** `origin/master` advanced unexpectedly, local branch is not exactly the intended closeout delta ahead, or release/tag state differs.
**Evidence to record:** Pre-push `HEAD` SHA, `origin/master` SHA, last commits, release view.
**Approval boundary:** Push is not automatic and must be approved separately from the local commit.

Do not push automatically.

The future push gate intentionally includes a remote-tracking update equivalent to `git fetch origin master --prune`; do not run that command during plan-deepening.

Before asking for push approval, record the local and remote state:

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" fetch origin master --prune
git -C "I:/claude-docs/my-project/opensource/claude-translator" status --short --branch
git -C "I:/claude-docs/my-project/opensource/claude-translator" rev-parse HEAD origin/master
git -C "I:/claude-docs/my-project/opensource/claude-translator" log --oneline --decorate -3
```

Pass conditions before push:

- `HEAD` is exactly one intended closeout commit ahead of `origin/master`, or the difference is explicitly explained.
- `origin/master` has not advanced unexpectedly since the last verification.
- The pre-push `HEAD` SHA is recorded in the operator report.

If the user explicitly approves push:

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" push origin master
```

Then verify:

```bash
git -C "I:/claude-docs/my-project/opensource/claude-translator" status --short --branch
git -C "I:/claude-docs/my-project/opensource/claude-translator" rev-parse HEAD origin/master
git -C "I:/claude-docs/my-project/opensource/claude-translator" log --oneline --decorate -3
gh release view v0.5.0 --repo debug-zhuweijian/claude-translator --json tagName,targetCommitish,isDraft,isPrerelease,url
```

Pass conditions:

- `HEAD` and `origin/master` match after push.
- GitHub release remains unchanged unless a separate release workflow is approved.

### Phase 8: Local development repository follow-up, separate from open-source closeout

**Preconditions:** Open-source local commit is safe; optionally, push gate has completed if the user chose to push.
**Allowed actions:** Separate local development verification and a separate local development commit only after approval.
**Stop if:** Local development changes are mixed with open-source publishing commit scope.
**Evidence to record:** Local development repository status, diff, tests, lint, format, CLI version.
**Approval boundary:** This phase is not part of the open-source publishing commit and requires a separate commit decision.

This phase is intentionally a follow-up, not part of the open-source publishing commit. Execute it only after the open-source repository is committed and verified, and only if the user approves a separate local development repository commit.

Expected local development changes:

- `README.md`
- `README.zh-CN.md`
- `README.ja.md`
- `README.ko.md`
- `src/claude_translator/__init__.py`
- `tests/test_async_translator.py`
- `tests/test_cli.py`
- `docs/superpowers/specs/2026-04-28-claude-translator-open-source-sync-design.md`
- `docs/superpowers/plans/2026-04-28-claude-translator-open-source-sync.md`
- this plan file under `docs/plans/`

Run local tests before local development commit:

```bash
PROJECT_ROOT="I:/claude-docs/my-project/claude-translator"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PROJECT_ROOT/src" python -m pytest "$PROJECT_ROOT/tests" -q -p no:cacheprovider
python -m ruff check --no-cache "$PROJECT_ROOT/src" "$PROJECT_ROOT/tests"
python -m ruff format --check --no-cache "$PROJECT_ROOT/src" "$PROJECT_ROOT/tests"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PROJECT_ROOT/src" python -m claude_translator --version
```

Stage local development changes only after fresh `git status` and `git diff` review.

## Acceptance Criteria

- [ ] Open-source repository top-level content remains limited to the approved whitelist.
- [ ] Open-source repository contains no `__pycache__`, `*.pyc`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache`, `.coverage`, `htmlcov`, `build`, `dist`, `*.egg-info`, `.pypirc`, `*.pem`, `*.key`, or `.env`.
- [ ] Open-source repository README files all include `v0.5.0`, `v0.4.0`, `v0.3.0`, and `v0.2.0` in newest-first order.
- [ ] Open-source metadata reports version `0.5.0` consistently.
- [ ] Open-source CLI smoke test reports `0.5.0` without generating bytecode files.
- [ ] Open-source security scan finds no high-confidence secret literals or private local paths; reviewable field-name/documentation mentions are explained, not blindly blocked.
- [ ] Open-source commit is created only after staged diff review.
- [ ] No push occurs without explicit approval.
- [ ] GitHub release `v0.5.0` remains unchanged unless a separate release plan is approved.
- [ ] Local development repository changes are committed separately from open-source publishing closeout.
- [ ] Every high-risk phase has explicit stop conditions and evidence records.
- [ ] Plan deepening changes only this runbook, not repository source, metadata, README, tests, release, or tag state.

## Dependencies & Risks

### Dependencies

- Git CLI available.
- Python available with `tomllib` support.
- GitHub CLI available for release verification.
- Current repository paths remain unchanged.

### Risks and mitigations

| Risk | Severity | Trigger | Impact | Mitigation | Verification signal |
| --- | --- | --- | --- | --- | --- |
| Accidental broad staging | High | `git add -A` or broad directory add | Private or noisy files enter commit | Use explicit path staging only | `diff --cached --name-status` contains only expected paths |
| Generated Python cache returns | High | CLI/import smoke without bytecode guard | Public repo gets runtime artifacts | Use `PYTHONDONTWRITEBYTECODE=1`; recursive scan before/after commit | Generated artifact scan reports no matches |
| Line-ending noise pollutes commit | Medium | Status shows `M` for line-ending residuals | Review becomes noisy | Inspect `diff --numstat` and `diff --summary`; do not stage empty numstat files | Numstat/summary prove whether a file has substantive diff |
| Security false positive blocks progress | Medium | Scanner sees field names like `api_key` | Legit docs/config fields treated as secrets | Split high-confidence blockers from reviewable mentions | Operator report explains reviewable mentions |
| Security false negative leaks secret | High | Scanner only searches shallow patterns | Secret/private file reaches public repo | Check key-like values, private paths, sensitive filenames, and private key blocks | `high_confidence_blockers: 0` |
| Push before verification | High | Push immediately after commit | GitHub shows incomplete cleanup | Commit locally, verify, then ask separately for push | Post-commit gates pass before push prompt |
| Remote advanced before push | Medium | `origin/master` changes after local verification | Local push may reject or target unexpected base | Run future push-gate `git fetch`, compare `HEAD` and `origin/master`, record pre-push SHA | Recorded SHAs match expected topology |
| Release mutation | High | Tag/release command is run | Published `v0.5.0` semantics become ambiguous | Only read release state; no release edit/tag commands | `gh release view` output unchanged |
| Local and open-source commits mixed | High | Local dev docs/tests staged in publishing repo | Boundary becomes unclear | Commit repositories separately | Git status/diff reviewed per repo |
| `.gitignore` absence permits future generated files | Medium | Python command creates untracked files | Runtime artifacts appear in publishing repo | Keep `.gitignore` absent per design, but always scan generated artifacts | Untracked/generated scan is clean |

## Rollback Plan

### Plan-deepening rollback

If this document-deepening step is wrong, revert only the target plan file diff. Do not touch source, README, metadata, tests, tags, releases, or the open-source repository as part of plan rollback.

### Future release-closeout rollback

Before push:

- If the commit is wrong, create a corrective commit or reset only after explicit approval.
- Prefer a new corrective commit over destructive history edits.

After push:

- Do not force push by default.
- Revert with a new commit if the public tree needs correction.
- Use the existing manual backup if deleted content must be recovered:
  - `I:/claude-docs/backup/manual/claude-translator/2026-04-28-opensource-whitelist-sync/`

## Success Metrics

- Open-source repository can be explained in one sentence: public source, metadata, license, changelog, and four README files only.
- A fresh clone or GitHub browser view does not expose local tests, docs, CI, private paths, caches, or operator artifacts.
- GitHub release remains stable while repository source becomes clean for future visitors.
- Local development repository remains fully capable of tests and dogfooding.
- An operator can tell from each phase whether to continue, stop, ask for approval, or record evidence.

## Sources & References

### Origin documents

- `docs/superpowers/specs/2026-04-28-claude-translator-open-source-sync-design.md` — defines repository roles and whitelist boundary.
- `docs/superpowers/plans/2026-04-28-claude-translator-open-source-sync.md` — executed whitelist sync and verification plan.

### Institutional learnings

- Release closure must include local open-source copy, push, release metadata, and README alignment.
- Multilingual README updates must keep all language variants consistent.
- Beta GitHub releases must use `--prerelease`; not applicable to current stable `v0.5.0`, but relevant for future releases.
- `pyproject.toml` table order must remain valid for package builds.

### Deepening inputs

- Read-only exploration identified this release closeout plan as the correct `/deepen-plan` target.
- Runbook planning review recommended adding preconditions, allowed actions, stop conditions, evidence records, and approval boundaries.
- Technical review required: high-confidence security scanning, recursive generated artifact scanning, fetch boundary separation, `.gitignore` decision preservation, and line-ending residual stop criteria.

### Fresh verification evidence

- `structure ok`
- `readme order ok`
- `metadata ok`
- `python -m claude_translator, version 0.5.0`
- `secret_literal_hits: 0`
- `private_path_hits: 0`
- `sanitized scan ok`
- `v0.5.0` release target remains `48c16221062d5add70a3d1ecb02162bfe1850c21`
