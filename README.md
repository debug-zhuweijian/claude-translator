<div align="center">

# Claude Translator

**Multi-language plugin description translator for Claude Code**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)](CHANGELOG.md) [![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

[English](README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md)

</div>

## Why Claude Translator?

Claude Code has hundreds of community plugins — but their descriptions are almost all in English. If your team works in Chinese, Japanese, or Korean, you're reading untranslated descriptions every day.

Claude Translator fixes this: **scan → translate → inject**, automatically. One command, all your plugin descriptions are in your language.

## What It Does

Before:

```yaml
---
name: brainstorm
description: Brainstorm ideas collaboratively
---
# Brainstorm
```

After:

```yaml
---
name: brainstorm
description: 协作式头脑风暴创意生成
---
# Brainstorm
```

The original English is preserved. The translated description is injected directly into the frontmatter — Claude Code picks it up instantly.

## How It Works

```mermaid
flowchart LR
    A[Scan ~/.claude/] --> B[For each item]
    B --> C{Override?}
    C -->|Yes| D[Use override]
    C -->|No| E{Cached?}
    E -->|Yes| F[Use cache]
    E -->|No| G{LLM available?}
    G -->|Yes| H[Translate & cache]
    G -->|No| I[Keep original]
    D --> J[Inject into Markdown]
    F --> J
    H --> J
    I --> J
```

## Quick Start

### 1. Install

```bash
git clone https://github.com/debug-zhuweijian/claude-translator.git
cd claude-translator
pip install .
```

Verify:

```
$ claude-translator --version
claude-translator, version 0.1.0
```

### 2. Initialize

Set your target language. This creates `~/.claude/translations/config.json`:

```bash
$ claude-translator init --lang zh-CN
Created config at C:\Users\you\.claude\translations\config.json (target: zh-CN)
```

### 3. Discover

See what can be translated. This scans **both** user-level skills/commands and installed plugins:

```
$ claude-translator discover
Scanning C:\Users\you\.claude ...
Found 440 translatable items (target: zh-CN)
  ok [user] user.skill:academic-writing
  ok [user] user.skill:brainstorming
  ok [user] user.command:commit
  ok [plugin] plugin.superpowers.skill:brainstorm
  ok [plugin] plugin.superpowers.skill:tdd-guide
  ok [plugin] plugin.compound-engineering.skill:code-review
  ok [plugin] plugin.everything-claude-code.agent:build-error-resolver
  ok [plugin] plugin.everything-claude-code.skill:e2e
  ...
```

Each line shows: status (`ok` = has frontmatter, `no` = missing), scope (`[user]` or `[plugin]`), and canonical ID.

### 4. Translate

Run the translation. It uses a 4-level fallback per item — override, cache, LLM, or original:

```
$ claude-translator sync
Scanning C:\Users\you\.claude ...
Translating 440 items to zh-CN ...
  [override] plugin.codex.agent:codex-rescue
  [cache] plugin.superpowers.skill:brainstorm
  [llm] plugin.compound-engineering.skill:code-review
  [llm] plugin.everything-claude-code.agent:build-error-resolver
  [skip] user.skill:my-custom-skill
  ...
Sync complete.
```

Labels:
- `[override]` — from your manual `overrides-zh-CN.json`
- `[cache]` — previously translated by LLM, saved in `cache-zh-CN.json`
- `[llm]` — freshly translated by the LLM, then cached
- `[skip]` — no change needed (already translated or empty)

### 5. Verify

Check coverage after sync:

```
$ claude-translator verify
  MISSING: plugin.new-tool.skill:deploy
Coverage: 439/440 (99.8%) — 1 missing
```

## Configuration

### Config Cascade

```
CLI args  >  Environment variables  >  config.json  >  Defaults
```

### Environment Variables

| Variable | Purpose | Fallback |
|----------|---------|----------|
| `CLAUDE_TRANSLATE_LANG` | Target language | config or `zh-CN` |
| `CLAUDE_TRANSLATE_LLM_BASE_URL` | API endpoint | `OPENAI_BASE_URL` |
| `CLAUDE_TRANSLATE_LLM_API_KEY` | API key | `OPENAI_API_KEY` |
| `CLAUDE_TRANSLATE_LLM_MODEL` | Model name | `OPENAI_MODEL` or `gpt-4o-mini` |

### Data Files

All stored in `~/.claude/translations/`:

| File | Purpose |
|------|---------|
| `config.json` | Configuration (created by `init`) |
| `overrides-zh-CN.json` | Your manual translations (highest priority) |
| `cache-zh-CN.json` | LLM translations cache |

### Using Local Models

No OpenAI key? Use a local model:

```bash
# Ollama
export CLAUDE_TRANSLATE_LLM_BASE_URL="http://localhost:11434/v1"
export CLAUDE_TRANSLATE_LLM_API_KEY="ollama"
export CLAUDE_TRANSLATE_LLM_MODEL="qwen2.5:7b"

# vLLM
export CLAUDE_TRANSLATE_LLM_BASE_URL="http://localhost:8000/v1"
export CLAUDE_TRANSLATE_LLM_MODEL="Qwen/Qwen2.5-7B-Instruct"
```

### Manual Overrides

Edit `~/.claude/translations/overrides-zh-CN.json` to fix any translation:

```json
{
  "plugin.superpowers.skill:brainstorm": "协作式头脑风暴创意生成"
}
```

Overrides always win — they're never overwritten by `sync`.

## What Gets Scanned

| Source | Path | Examples |
|--------|------|----------|
| User skills | `~/.claude/skills/**/*.md` | `SKILL.md`, `my-skill.md` |
| User commands | `~/.claude/commands/**/*.md` | `commit.md`, `review.md` |
| Plugin skills | `<plugin>/skills/**/*.md` | Per-plugin skill definitions |
| Plugin commands | `<plugin>/commands/**/*.md` | Per-plugin slash commands |
| Plugin agents | `<plugin>/agents/**/*.md` | Per-plugin agent definitions |

Plugin registry is read from `~/.claude/plugins/installed_plugins.json` (v2 format) with fallback to `~/.claude/installed_plugins.json` (v1 format). Multi-version plugins are deduplicated — only the latest version is translated.

## Features

| Feature | Description |
|---------|-------------|
| **Auto Discovery** | Scans all plugins, skills, commands, and agents from `~/.claude/` |
| **4-Level Fallback** | User override → cached translation → LLM translation → original text |
| **Manual Overrides** | Fine-tune any translation via `overrides-{lang}.json` |
| **Multi-Version Dedup** | Same plugin at different versions? Only the latest is translated |
| **CJK Support** | Built-in detection for Chinese, Japanese, and Korean scripts |
| **OpenAI-Compatible** | Works with OpenAI, Ollama, vLLM, or any compatible API |
| **CRLF Safe** | Preserves line endings on Windows — no file corruption |
| **Legacy Migration** | Auto-migrates old-format translation data on first run |
| **Config Cascade** | CLI args → env vars → config file → defaults |

## CLI Reference

| Command | Description |
|---------|-------------|
| `init --lang LANG` | Create config with target language |
| `discover [--lang LANG]` | List translatable items and status |
| `sync [--lang LANG]` | Translate descriptions and write to files |
| `verify [--lang LANG]` | Check coverage, report missing items |

## Architecture

```mermaid
graph TB
    CLI[CLI - Click] --> DISC[Discovery]
    CLI --> TRANS[TranslationChain]
    CLI --> INJ[Injector]
    CLI --> MIGR[Migration]

    DISC --> |v2 format| V2["plugins/installed_plugins.json"]
    DISC --> |v1 fallback| V1["installed_plugins.json"]
    DISC --> |user-level| USER["~/.claude/skills/"]
    DISC --> |user-level| USERC["~/.claude/commands/"]

    TRANS --> |1st| OV["overrides-{lang}.json"]
    TRANS --> |2nd| CACHE["cache-{lang}.json"]
    TRANS --> |3rd| LLM[LLM Client]

    INJ --> |write| FM[YAML Frontmatter]
    MIGR --> |migrate| OV

    LLM -.-> |OpenAI compat| API[API Server]
```

## Supported Languages

Any language your LLM supports. Built-in prompts for:

English → Chinese (Simplified/Traditional) / Japanese / Korean, Chinese → Japanese / Korean

## Development

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
ruff check src/ tests/
```

## License

[MIT](LICENSE)
