<div align="center">

# Claude Translator

**Claude Code プラグイン説明の多言語翻訳ツール**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)](CHANGELOG.md) [![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

[English](README.md) | [中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md)

</div>

## なぜ Claude Translator が必要か？

Claude Code には何百ものコミュニティプラグインがありますが、その説明はほぼすべて英語です。日本語や中国語、韓国語で作業している場合、未翻訳の説明を毎日読むことになります。

Claude Translator が解決します：**スキャン → 翻訳 → 注入**、すべて自動。コマンド一つで、すべてのプラグイン説明があなたの言語に。

## 何が変わるか

変換前：

```yaml
---
name: brainstorm
description: Brainstorm ideas collaboratively
---
# Brainstorm
```

変換後：

```yaml
---
name: brainstorm
description: 協力的なブレインストーミングでアイデアを生成
---
# Brainstorm
```

元の英語は保持され、翻訳された説明が frontmatter に直接注入されます。Claude Code がすぐに反映します。

## 仕組み

```mermaid
flowchart LR
    A[~/.claude/ をスキャン] --> B[各項目を処理]
    B --> C{オーバーライドあり?}
    C -->|はい| D[オーバーライドを使用]
    C -->|いいえ| E{キャッシュあり?}
    E -->|はい| F[キャッシュを使用]
    E -->|いいえ| G{LLM 利用可能?}
    G -->|はい| H[翻訳してキャッシュ]
    G -->|いいえ| I[原文を保持]
    D --> J[Markdown に注入]
    F --> J
    H --> J
    I --> J
```

## クイックスタート

### 1. インストール

```bash
git clone https://github.com/debug-zhuweijian/claude-translator.git
cd claude-translator
pip install .
```

確認：

```
$ claude-translator --version
claude-translator, version 0.1.0
```

### 2. 初期化

対象言語を設定します。`~/.claude/translations/config.json` が作成されます：

```bash
$ claude-translator init --lang ja
Created config at C:\Users\you\.claude\translations\config.json (target: ja)
```

### 3. 検出

翻訳可能な項目を確認します。ユーザー技能/コマンドとインストール済みプラグインの**両方**をスキャンします：

```
$ claude-translator discover
Scanning C:\Users\you\.claude ...
Found 440 translatable items (target: ja)
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

各行の内容：ステータス（`ok` = frontmatter あり、`no` = なし）、スコープ（`[user]` または `[plugin]`）、正規 ID。

### 4. 翻訳実行

翻訳を実行します。各項目に 4 段階フォールバックを使用します：

```
$ claude-translator sync
Scanning C:\Users\you\.claude ...
Translating 440 items to ja ...
  [override] plugin.codex.agent:codex-rescue
  [cache] plugin.superpowers.skill:brainstorm
  [llm] plugin.compound-engineering.skill:code-review
  [llm] plugin.everything-claude-code.agent:build-error-resolver
  [skip] user.skill:my-custom-skill
  ...
Sync complete.
```

ステータスラベル：
- `[override]` — 手動 `overrides-ja.json` から
- `[cache]` — 以前に LLM で翻訳済み、`cache-ja.json` に保存
- `[llm]` — 今回 LLM で新規翻訳、自動キャッシュ
- `[skip]` — 変更不要（翻訳済みまたは空）

### 5. 検証

同期後にカバレッジを確認：

```
$ claude-translator verify
  MISSING: plugin.new-tool.skill:deploy
Coverage: 439/440 (99.8%) — 1 missing
```

## 設定

### 優先度カスケード

```
CLI 引数  >  環境変数  >  config.json  >  デフォルト
```

### 環境変数

| 変数 | 用途 | フォールバック |
|------|------|----------------|
| `CLAUDE_TRANSLATE_LANG` | 対象言語 | 設定ファイルまたは `zh-CN` |
| `CLAUDE_TRANSLATE_LLM_BASE_URL` | API エンドポイント | `OPENAI_BASE_URL` |
| `CLAUDE_TRANSLATE_LLM_API_KEY` | API キー | `OPENAI_API_KEY` |
| `CLAUDE_TRANSLATE_LLM_MODEL` | モデル名 | `OPENAI_MODEL` または `gpt-4o-mini` |

### データファイル

`~/.claude/translations/` に保存：

| ファイル | 用途 |
|----------|------|
| `config.json` | 設定ファイル（`init` で作成） |
| `overrides-ja.json` | 手動翻訳オーバーライド（最高優先度） |
| `cache-ja.json` | LLM 翻訳の自動キャッシュ |

### ローカルモデルの使用

OpenAI キーなしでもローカルモデルで利用可能：

```bash
# Ollama
export CLAUDE_TRANSLATE_LLM_BASE_URL="http://localhost:11434/v1"
export CLAUDE_TRANSLATE_LLM_API_KEY="ollama"
export CLAUDE_TRANSLATE_LLM_MODEL="qwen2.5:7b"

# vLLM
export CLAUDE_TRANSLATE_LLM_BASE_URL="http://localhost:8000/v1"
export CLAUDE_TRANSLATE_LLM_MODEL="Qwen/Qwen2.5-7B-Instruct"
```

### 手動オーバーライド

`~/.claude/translations/overrides-ja.json` を編集して翻訳を修正：

```json
{
  "plugin.superpowers.skill:brainstorm": "協力的なブレインストーミングでアイデアを生成"
}
```

オーバーライドは最優先 — `sync` で上書きされることはありません。

## スキャン対象

| ソース | パス | 例 |
|--------|------|-----|
| ユーザー技能 | `~/.claude/skills/**/*.md` | `SKILL.md`、`my-skill.md` |
| ユーザーコマンド | `~/.claude/commands/**/*.md` | `commit.md`、`review.md` |
| プラグイン技能 | `<plugin>/skills/**/*.md` | プラグインごとの技能定義 |
| プラグインコマンド | `<plugin>/commands/**/*.md` | プラグインごとのスラッシュコマンド |
| プラグインエージェント | `<plugin>/agents/**/*.md` | プラグインごとの Agent 定義 |

プラグインレジストリは `~/.claude/plugins/installed_plugins.json`（v2 形式）から読み取り、`~/.claude/installed_plugins.json`（v1 形式）にフォールバックします。複数バージョンのプラグインは自動的に重複排除 — 最新バージョンのみ翻訳されます。

## 機能

| 機能 | 説明 |
|------|------|
| **自動検出** | `~/.claude/` 内のすべてのプラグイン、スキル、コマンド、エージェントをスキャン |
| **4 段階フォールバック** | ユーザーオーバーライド → キャッシュ → LLM 翻訳 → 原文 |
| **手動オーバーライド** | `overrides-{lang}.json` で個別に微調整 |
| **マルチバージョン重複排除** | 同一プラグインの複数バージョンは最新のみ翻訳 |
| **CJK サポート** | 中国語・日本語・韓国語のスクリプト検出を内蔵 |
| **OpenAI 互換** | OpenAI、Ollama、vLLM などで動作 |
| **CRLF セーフ** | Windows で改行コードを保持、ファイルを破損しません |
| **レガシー移行** | 初回実行時に旧形式データを自動移行 |
| **設定カスケード** | CLI 引数 → 環境変数 → 設定ファイル → デフォルト |

## CLI コマンド

| コマンド | 説明 |
|----------|------|
| `init --lang LANG` | 対象言語を指定して設定を作成 |
| `discover [--lang LANG]` | 翻訳可能な項目とステータスを一覧表示 |
| `sync [--lang LANG]` | 翻訳を実行してファイルに書き込み |
| `verify [--lang LANG]` | カバレッジを確認、未翻訳項目を報告 |

## アーキテクチャ

```mermaid
graph TB
    CLI[CLI - Click] --> DISC[Discovery]
    CLI --> TRANS[TranslationChain]
    CLI --> INJ[Injector]
    CLI --> MIGR[Migration]

    DISC --> |v2 形式| V2["plugins/installed_plugins.json"]
    DISC --> |v1 フォールバック| V1["installed_plugins.json"]
    DISC --> |ユーザー級検出| USER["~/.claude/skills/"]
    DISC --> |ユーザー級検出| USERC["~/.claude/commands/"]

    TRANS --> |1st| OV["overrides-{lang}.json"]
    TRANS --> |2nd| CACHE["cache-{lang}.json"]
    TRANS --> |3rd| LLM[LLM Client]

    INJ --> |書き込み| FM[YAML Frontmatter]
    MIGR --> |移行| OV

    LLM -.-> |OpenAI 互換| API[API Server]
```

## 対応言語

LLM が対応する任意の言語をサポート。内蔵プロンプトテンプレート：

英語 → 中国語（簡体/繁体） / 日本語 / 韓国語、中国語 → 日本語 / 韓国語

## 開発

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
ruff check src/ tests/
```

## ライセンス

[MIT](LICENSE)
