<div align="center">

# Claude Translator

**Claude Code 插件描述多语言翻译工具**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)](CHANGELOG.md) [![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/) [![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

[English](README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md)

</div>

## 为什么需要 Claude Translator？

Claude Code 有数百个社区插件——但描述几乎全是英文。如果你的团队使用中文、日文或韩文，每天都在阅读未翻译的描述。

Claude Translator 一键解决：**扫描 → 翻译 → 注入**，自动完成。一条命令，所有插件描述变成你的语言。

## 它做了什么

把这样的 Markdown 文件：

```yaml
---
name: brainstorm
description: Brainstorm ideas collaboratively
---
# Brainstorm
```

变成这样：

```yaml
---
name: brainstorm
description: 协作式头脑风暴创意生成
---
# Brainstorm
```

原始英文保留，翻译后的描述直接注入 frontmatter——Claude Code 立即生效。

## 工作原理

```mermaid
flowchart LR
    A[扫描 ~/.claude/] --> B[逐项处理]
    B --> C{有覆盖翻译?}
    C -->|是| D[使用覆盖]
    C -->|否| E{有缓存翻译?}
    E -->|是| F[使用缓存]
    E -->|否| G{LLM 可用?}
    G -->|是| H[翻译并缓存]
    G -->|否| I[保留原文]
    D --> J[注入 Markdown]
    F --> J
    H --> J
    I --> J
```

```mermaid
graph LR
    A[发现] --> B[翻译]
    B --> C[注入]
    C --> D[验证]
```

## 快速开始

### 安装

```bash
git clone https://github.com/debug-zhuweijian/claude-translator.git
cd claude-translator
pip install .
```

### 初始化

```bash
$ claude-translator init --lang zh-CN
Created config at ~/.claude/translations/config.json (target: zh-CN)
```

### 发现

```bash
$ claude-translator discover
Scanning /home/user/.claude ...
Found 47 translatable items (target: zh-CN)
  ok [plugin] plugin.codex.agent:codex-rescue
  ok [plugin] plugin.superpowers.skill:brainstorm
  no [user] user.skill:my-custom-skill
  ...
```

### 翻译

```bash
$ claude-translator sync
Scanning /home/user/.claude ...
Translating 47 items to zh-CN ...
  [override] plugin.codex.agent:codex-rescue
  [cache] plugin.superpowers.skill:brainstorm
  [llm] plugin.ecc-skills.command:commit
  [skip] user.skill:my-custom-skill
Sync complete.
```

### 验证

```bash
$ claude-translator verify
  MISSING: plugin.new-tool.skill:deploy
Coverage: 46/47 (97.9%) — 1 missing
```

## 功能特性

| 特性 | 说明 |
|------|------|
| **自动发现** | 扫描 `~/.claude/` 下所有插件、技能、命令和 Agent |
| **4 级回退** | 用户覆盖 → 缓存翻译 → LLM 翻译 → 原文 |
| **人工覆盖** | 通过 `overrides-{lang}.json` 精调任意翻译 |
| **多版本去重** | 同一插件多个版本？只翻译最新版 |
| **CJK 支持** | 内置中文、日文、韩文脚本检测 |
| **OpenAI 兼容** | 支持 OpenAI、Ollama、vLLM 等任何兼容 API |
| **换行安全** | Windows 下保留 CRLF，不破坏文件 |
| **旧版迁移** | 首次运行自动迁移旧格式翻译数据 |
| **配置级联** | CLI 参数 → 环境变量 → 配置文件 → 默认值 |

## CLI 命令参考

| 命令 | 说明 |
|------|------|
| `init --lang LANG` | 创建配置，指定目标语言 |
| `discover [--lang LANG]` | 列出可翻译项及状态 |
| `sync [--lang LANG]` | 执行翻译并写入文件 |
| `verify [--lang LANG]` | 检查覆盖率，报告缺失项 |

## 配置

### 配置级联

```
CLI 参数  >  环境变量  >  config.json  >  默认值
```

### 环境变量

| 变量 | 用途 | 备选 |
|------|------|------|
| `CLAUDE_TRANSLATE_LANG` | 目标语言 | 配置文件或 `zh-CN` |
| `CLAUDE_TRANSLATE_LLM_BASE_URL` | API 地址 | `OPENAI_BASE_URL` |
| `CLAUDE_TRANSLATE_LLM_API_KEY` | API 密钥 | `OPENAI_API_KEY` |
| `CLAUDE_TRANSLATE_LLM_MODEL` | 模型名称 | `OPENAI_MODEL` 或 `gpt-4o-mini` |

### 数据文件

所有数据存储在 `~/.claude/translations/` 下：

| 文件 | 用途 |
|------|------|
| `config.json` | 配置文件（由 `init` 创建） |
| `overrides-zh-CN.json` | 人工翻译覆盖（最高优先级） |
| `cache-zh-CN.json` | LLM 翻译缓存 |

### 使用本地模型

```bash
# Ollama
export CLAUDE_TRANSLATE_LLM_BASE_URL="http://localhost:11434/v1"
export CLAUDE_TRANSLATE_LLM_API_KEY="ollama"
export CLAUDE_TRANSLATE_LLM_MODEL="qwen2.5:7b"

# vLLM
export CLAUDE_TRANSLATE_LLM_BASE_URL="http://localhost:8000/v1"
export CLAUDE_TRANSLATE_LLM_MODEL="Qwen/Qwen2.5-7B-Instruct"
```

## 架构

```mermaid
graph TB
    CLI[CLI - Click] --> DISC[Discovery]
    CLI --> TRANS[TranslationChain]
    CLI --> INJ[Injector]
    CLI --> MIGR[Migration]

    DISC --> |扫描插件| PLUGIN[installed_plugins.json]
    DISC --> |扫描用户级| USER[~/.claude/skills/]
    DISC --> |扫描用户级| USERC[~/.claude/commands/]

    TRANS --> |1st| OV[overrides-{lang}.json]
    TRANS --> |2nd| CACHE[cache-{lang}.json]
    TRANS --> |3rd| LLM[LLM Client]

    INJ --> |写入| FM[YAML Frontmatter]
    MIGR --> |迁移| OV

    LLM -.-> |OpenAI 兼容| API[API Server]
```

## 支持的语言

支持 LLM 能处理的任何语言。内置 prompt 模板：

英语 → 中文 / 日语 / 韩语，中文 → 日语 / 韩语

## 开发

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
ruff check src/ tests/
```

## 许可证

[MIT](LICENSE)
