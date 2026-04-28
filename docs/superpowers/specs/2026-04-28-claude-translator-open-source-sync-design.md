# Claude Translator Open Source Sync Design

## Goal

Turn `I:/claude-docs/my-project/opensource/claude-translator` into the GitHub publishing source for Claude Translator, derived from the local development repository at `I:/claude-docs/my-project/claude-translator`.

The local repository remains the complete development and dogfooding workspace. The open-source repository should contain only public, relevant, release-ready project files.

## Current State

- Local development repository: `I:/claude-docs/my-project/claude-translator`
- Open-source publishing repository: `I:/claude-docs/my-project/opensource/claude-translator`
- Both repositories currently point at release commit `48c16221062d5add70a3d1ecb02162bfe1850c21` for `v0.5.0`.
- The local repository currently has post-release cleanup changes in README files, version fallback, and tests.
- The open-source repository is currently a full development clone, including `tests/`, `.github/`, and `docs/`.
- The desired open-source repository is not a full mirror. It is a curated publishing source.

## Repository Roles

### Local Development Repository

Keep the full engineering workspace here:

- `src/`
- `tests/`
- `docs/`
- `.github/`
- four README files
- development dependencies and quality gates
- local dogfooding workflows

This repository is where full validation runs:

- pytest
- ruff check
- ruff format check
- coverage
- CLI dogfooding checks

### Open-source Publishing Repository

Keep only public release files here:

- `src/`
- `pyproject.toml`
- `README.md`
- `README.zh-CN.md`
- `README.ja.md`
- `README.ko.md`
- `LICENSE`
- `CHANGELOG.md`

Exclude development-only or local-only content:

- `tests/`
- `docs/`
- `.github/`
- `.coverage`
- `htmlcov/`
- `.pytest_cache/`
- `.ruff_cache/`
- `*.egg-info/`
- `.env`
- local configuration files
- local absolute paths
- private Claude Code or dogfooding configuration

## Sync Strategy

Use a whitelist sync from the local repository to the open-source repository.

Allowed files and directories:

```text
src/
pyproject.toml
README.md
README.zh-CN.md
README.ja.md
README.ko.md
LICENSE
CHANGELOG.md
```

Do not mirror the full directory. Do not use destructive mirror sync such as `robocopy /MIR` on the whole repository. If cleanup is needed, delete only known disallowed paths in the open-source repository after a backup and status check.

## README Strategy

Keep all four README files in the open-source repository:

- `README.md`
- `README.zh-CN.md`
- `README.ja.md`
- `README.ko.md`

They should be copied from the latest local development repository state, then reviewed for public-facing clarity and safety.

Each README must contain the recent release history in newest-first order:

```text
v0.5.0
v0.4.0
v0.3.0
v0.2.0
```

README files must not include local machine paths, private configuration, API keys, tokens, or internal-only dogfooding notes.

## Test Strategy

`tests/` remains in the local development repository only.

The open-source publishing repository does not keep tests because the user's current goal is a clean public publishing source rather than an external contributor development workspace.

Validation split:

- Local development repository: run full tests, lint, format, coverage.
- Open-source repository: run structure, import, CLI version, README order, metadata, and security checks.

## Open-source Verification

After syncing, verify the open-source repository with these checks:

1. Structure check
   - Required public files exist.
   - Disallowed paths do not exist.

2. Metadata check
   - `pyproject.toml` version is current.
   - script entry point is `claude_translator.cli:main`.
   - fallback `__version__` literal matches the project version.

3. Runtime smoke check
   - `PYTHONPATH=<opensource>/src python -m claude_translator --version` reports the expected version.
   - Importing `claude_translator` from the open-source source tree succeeds.

4. README check
   - All four README files exist.
   - Recent versions appear in newest-first order.

5. Security check
   - No `.env` files.
   - No likely API keys, tokens, secrets, or passwords.
   - No local absolute paths such as `C:\`, `I:\`, `G:\`, `/c/Users`, or `Users\Windows11`.
   - No `.claude` private configuration.
   - No coverage or cache output.

6. Git check
   - Open-source repository status shows only expected tracked changes.
   - No untracked generated artifacts are present.

## Publishing Rule

GitHub publishing should use the open-source repository as the source of truth.

Do not publish directly from the local development repository.

Before any push or release, the open-source repository must pass:

- structure check
- metadata check
- runtime smoke check
- README check
- security check
- git status review

## Non-goals

- Do not mutate the existing `v0.5.0` tag or release during this cleanup.
- Do not force-push.
- Do not delete local development tests.
- Do not remove README translations.
- Do not publish generated coverage output.
- Do not copy local private configuration into the open-source repository.

## Approval

The user approved the direction: whitelist sync, keep four README files, exclude tests from the open-source repository, retain `CHANGELOG.md`, and run a safety review before treating the open-source folder as publishable.
