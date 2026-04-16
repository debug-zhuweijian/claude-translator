# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-04-17

### Added

- **4 CLI commands**: `init`, `discover`, `sync`, `verify`
- **Auto discovery** of plugins, skills, commands, and agents from `~/.claude/`
- **4-level translation fallback**: user override → cache → LLM → original
- **Manual overrides** via `overrides-{lang}.json`
- **Multi-version dedup** — same plugin at different versions, only latest translated
- **CJK support** — built-in Chinese, Japanese, Korean script detection
- **OpenAI-compatible client** — works with OpenAI, Ollama, vLLM, etc.
- **CRLF-safe injection** — preserves line endings on Windows
- **Legacy migration** — auto-migrates `descriptions-overrides.json` to new format
- **Config cascade** — CLI args → env vars → config file → defaults
- **Per-language storage** — `overrides-{lang}.json`, `cache-{lang}.json`
- **YAML frontmatter parser** — read/write description field without corrupting content
- **Canonical ID system** — `plugin.<key>.<kind>:<name>` / `user.<kind>:<name>`
- **Immutable data models** — frozen dataclasses throughout
- 108 tests with full coverage

[0.1.0]: https://github.com/debug-zhuweijian/claude-translator/releases/tag/v0.1.0
