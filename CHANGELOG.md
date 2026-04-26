# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-04-27

### Added

- **Recursive entrypoint discovery** -- user agents, nested commands, and nested skill bundle `SKILL.md` files are now discovered for complex Claude Code configurations
- **Plugin nested entry discovery** -- plugin commands, agents, and skill bundles now support recursive entrypoints while preserving latest-version registry deduplication
- **Discovery audit mode** -- `discover --audit` summarizes scope/kind counts, dogfooding categories, missing frontmatter, and empty descriptions

### Fixed

- **Namespaced canonical IDs** -- canonical ID parsing now supports command and agent names containing namespace colons such as `gsd:add-backlog` and `ce:brainstorm`

## [0.4.0] - 2026-04-21

### Added

- **Shared atomic storage helper** -- introduced `storage._io.atomic_write_text` and regression tests for atomic write edge cases across cache, overrides, and legacy migration flows
- **Broader client and language coverage** -- expanded sync/async OpenAI client tests and re-exported shared CJK helper functions from `lang.detect`
- **Release-grade CI coverage** -- PR validation now runs on Python 3.10, 3.11, 3.12, and 3.13 with a 93% coverage gate, and `master` pushes now trigger the same CI workflow

### Fixed

- **Editable install metadata** -- moved `[project.urls]` after direct `project` fields so clean `pip install -e ".[dev]"` runs no longer fail metadata validation
- **Atomic write consistency** -- cache, overrides, and legacy migration paths now use the same atomic writer instead of duplicating file-write logic

### Security

- **Prompt tag breakout hardening** -- XML meta characters in wrapped user text are escaped before sending content to the LLM, preventing user payloads from breaking out of `<text_to_translate>`

## [0.3.0] - 2026-04-19

### Added

- **Async translation stack** -- introduced `AsyncLLMClient`, async OpenAI-compatible and fake clients, plus `TranslationChain.translate_async`
- **Concurrent pipeline execution** -- added `run_async()` with bounded concurrency, cache-write locking, and CLI `--concurrency` / `--async` controls
- **Rich progress feedback** -- async `sync` now renders progress with `rich.progress` for large batches
- **Safer reporting and tests** -- added dedicated `empty` reporting and regression coverage for Phase 1/2 changes

### Fixed

- **Empty translation accounting** -- blank model output is now counted as `empty` instead of being merged into `skip`
- **Pipeline branch cleanup** -- removed dead fallback logic and kept matched-translation checks on the only reachable path
- **Frontmatter diagnostics** -- malformed YAML frontmatter now emits a warning instead of failing silently
- **Write-path hardening** -- translation injection now enforces an `allowed_paths` whitelist before mutating files
- **Prompt injection isolation** -- user text is wrapped inside `<text_to_translate>` tags before being sent to the LLM
- **OpenAI API key fail-fast** -- client construction now stops early with an explicit error when no API key is configured

## [0.2.0] - 2026-04-17

### Changed

- **Safe YAML frontmatter handling** -- replaced regex-style parsing with `ruamel.yaml` round-trip loading/writing for quoted values, colons, and multiline content
- **Translation pipeline hardening** -- added LLM response cleaning, OpenAI client timeout/retry settings, explicit sync reporting, and `sync --dry-run`
- **Storage and discovery fixes** -- translation paths no longer create directories on read, cache/overrides writes are atomic, and v2 plugin registry keys are used when available
- **Verification improvements** -- `verify` now checks actual frontmatter content for zh/ja/ko targets instead of assuming cache/override coverage
- **Docs and tests aligned** -- version strings updated to 0.2.0 and unsupported coverage claims removed

## [0.1.2] - 2025-04-17

### Changed

- **README enrichment** -- added Table of Contents, Prerequisites table, 6-step Usage Walkthrough, Quick Reference Table, What's New section, Contributing guide, and GitHub Release badge
- **4-language sync** -- all READMEs (EN/ZH/JA/KO) expanded from 270 to 452 lines with consistent structure

## [0.1.1] - 2025-04-17

### Fixed

- **Multi-line frontmatter parsing** -- continuation lines (indented) are now correctly captured instead of silently dropped
- **Quote stripping** -- `"quoted"` and `'quoted'` frontmatter values are properly unquoted
- **UTF-8 BOM preservation** -- files with BOM prefix no longer lose it after injection
- **Plugin discovery** -- corrected registry path (`~/.claude/plugins/`) and v2 format parsing

## [0.1.0] - 2025-04-17

### Added

- **4 CLI commands**: `init`, `discover`, `sync`, `verify`
- **Auto discovery** of plugins, skills, commands, and agents from `~/.claude/`
- **4-level translation fallback**: user override → cache → LLM → original
- **Manual overrides** via `overrides-{lang}.json`
- **Multi-version dedup** -- same plugin at different versions, only latest translated
- **CJK support** -- built-in Chinese, Japanese, Korean script detection
- **OpenAI-compatible client** -- works with OpenAI, Ollama, vLLM, etc.
- **CRLF-safe injection** -- preserves line endings on Windows
- **Legacy migration** -- auto-migrates `descriptions-overrides.json` to new format
- **Config cascade** -- CLI args → env vars → config file → defaults
- **Per-language storage** -- `overrides-{lang}.json`, `cache-{lang}.json`
- **YAML frontmatter parser** -- read/write description field without corrupting content
- **Canonical ID system** -- `plugin.<key>.<kind>:<name>` / `user.<kind>:<name>`
- **Immutable data models** -- frozen dataclasses throughout

[0.5.0]: https://github.com/debug-zhuweijian/claude-translator/releases/tag/v0.5.0
[0.4.0]: https://github.com/debug-zhuweijian/claude-translator/releases/tag/v0.4.0
[0.2.0]: https://github.com/debug-zhuweijian/claude-translator/releases/tag/v0.2.0
[0.3.0]: https://github.com/debug-zhuweijian/claude-translator/releases/tag/v0.3.0
[0.1.2]: https://github.com/debug-zhuweijian/claude-translator/releases/tag/v0.1.2
[0.1.1]: https://github.com/debug-zhuweijian/claude-translator/releases/tag/v0.1.1
[0.1.0]: https://github.com/debug-zhuweijian/claude-translator/releases/tag/v0.1.0
