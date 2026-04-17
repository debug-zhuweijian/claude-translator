# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.2.0]: https://github.com/debug-zhuweijian/claude-translator/releases/tag/v0.2.0
[0.1.2]: https://github.com/debug-zhuweijian/claude-translator/releases/tag/v0.1.2
[0.1.1]: https://github.com/debug-zhuweijian/claude-translator/releases/tag/v0.1.1
[0.1.0]: https://github.com/debug-zhuweijian/claude-translator/releases/tag/v0.1.0
