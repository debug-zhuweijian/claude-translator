# Claude Description Translator — Product Design Spec

## Summary

将现有 `~/.claude/translations/` 翻译系统重构为开源、跨平台、多语言的产品级 CLI 工具。自动发现 Claude Code 插件结构，支持中英日韩四语言，LLM 辅助首次翻译，四级 fallback 翻译链，18 场景测试矩阵覆盖。

## Context

- 现有系统：`apply-descriptions.py` (854行) + `scanner.py` (196行)
- 硬编码 11 个插件别名表，仅支持中文，路径耦合 `Path.home()`
- 翻译覆盖 1501/1501 (100%)，自愈机制已验证

## Architecture

### 三层分离

```
CLI Layer          入口 + Skill 命令注册
Engine Layer       Discovery / Translator / Injector / Canonical
Storage Layer      PathResolver / FileStore / LLMClient
```

### 目录结构

```
src/claude_translator/
├── __init__.py
├── __main__.py
├── cli.py                      # Click 子命令: discover/sync/verify/init
├── config/
│   ├── defaults.py             # 硬编码默认值
│   ├── loaders.py              # config file → env vars → CLI args 层叠
│   └── models.py               # Pydantic 配置模型
├── core/
│   ├── discovery.py            # 自动发现插件（DIR_KIND_MAP 驱动）
│   ├── canonical.py            # canonical_id 生成/解析
│   ├── frontmatter.py          # FrontmatterParser 类
│   ├── translator.py           # TranslationChain 四级 fallback
│   ├── injector.py             # frontmatter 注入/更新（保持 CRLF）
│   └── models.py               # Record(frozen), Inventory, TranslationMapping
├── clients/
│   ├── base.py                 # LLMClient Protocol
│   ├── openai_compat.py        # OpenAI 兼容端点（Anthropic/Qwen/DeepSeek）
│   └── fake.py                 # FakeClient 测试双
├── storage/
│   ├── paths.py                # CLAUDE_CONFIG_DIR 感知路径解析
│   ├── overrides.py            # overrides-{lang}.json 读写
│   └── cache.py                # cache-{lang}.json 读写
├── lang/
│   ├── detect.py               # CJK 语言检测（启发式 + lingua-py）
│   ├── cjk.py                  # Unicode 范围 + has_cjk/has_ja/has_ko
│   └── prompts.py              # 按语言对的翻译 prompt 模板
├── errors.py                   # UserError / InternalError 异常层级
└── utils/
    └── paths.py                # normalize_path, detect_newline
```

## Decisions

### 1. 插件发现：约定优于配置，零配置

**插件级**：从 `installed_plugins.json` 读取插件路径 → 扫描 DIR_KIND_MAP 子目录 → 生成 `plugin.<key>.<kind>:<name>` canonical_id

**用户级**：扫描 `~/.claude/skills/` 和 `~/.claude/commands/` → 生成 `user.<kind>:<name>` canonical_id

优先级：用户级 > 插件级（同名时用户级覆盖）

删除 `PLUGIN_SECTION_ALIASES` 和 `MIRROR_DIR_PLUGIN_OVERRIDES`。替换为标准目录名映射：

```python
DIR_KIND_MAP = {
    "skills": "skill",
    "commands": "command",
    "agents": "agent",
    ".agents/skills": "skill",
    ".agents/commands": "command",
    ".opencode/commands": "command",
}
```

扫描逻辑：
1. 从 `installed_plugins.json` 读取插件安装路径
2. 对每个插件根目录，检查 `DIR_KIND_MAP` 中列出的子目录
3. 只取标准目录内的文件，非标准目录静默跳过
4. 只取顶层 SKILL.md 或 .md，不取 reference/ 子文件

### canonical_id 格式

```
plugin.<plugin_key>.<kind>:<name>     # 插件级
user.<kind>:<name>                    # 用户级（~/.claude/ 下的 skill/command）
```

- `plugin_key`: 从 `installed_plugins.json` 的插件目录名派生（如 `superpowers`）
- `kind`: `skill` | `command` | `agent`
- `name`: 文件名去掉 `.md` 后缀

### 2. 路径解析：CLAUDE_CONFIG_DIR 优先

```python
def get_claude_dir() -> Path:
    if env_path := os.getenv("CLAUDE_CONFIG_DIR"):
        return Path(env_path).expanduser()
    return Path.home() / ".claude"
```

### 3. 多语言：按语言分文件

```
~/.claude/translations/
├── config.json                  # { "target_lang": "zh-CN", "llm": { ... } }
├── overrides-zh-CN.json         # 用户手动覆盖
├── overrides-ja.json
├── overrides-ko.json
├── cache-zh-CN.json             # LLM 生成缓存
├── cache-ja.json
├── cache-ko.json
├── runtime-inventory.json
└── last-runtime-fingerprint.json
```

支持的语言：
| 代码 | 语言 | Unicode 检测 |
|------|------|-------------|
| `zh-CN` | 简体中文 | CJK Ideographs (无假名/谚文) |
| `zh-TW` | 繁体中文 | 同 zh-CN（地区标记区分） |
| `ja` | 日语 | Hiragana + Katakana + Kanji |
| `ko` | 韩语 | Hangul |
| `en` | 英语 | 默认源语言 |

### 4. 翻译链：四级 fallback

```
用户 override (overrides-{lang}.json)
    ↓ miss
本地缓存 (cache-{lang}.json)
    ↓ miss
LLM 生成 (OpenAI 兼容 API)
    ↓ 不可用
返回原文
```

每次 LLM 生成后自动写入 cache。用户可手动编辑 overrides 修正 LLM 翻译质量。

### 5. CJK 语言检测：启发式 + lingua-py

```python
def detect_script(text: str) -> str:
    if re.search(r'[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]', text):
        return "ko"
    if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
        return "ja"
    if re.search(r'[\u4e00-\u9fff\u3400-\u4dbf]', text):
        return "zh"
    return "unknown"
```

纯汉字场景（中日共享）用 lingua-py 做统计检测，限制候选语言为 zh/ja 提高准确率。

### 6. LLM 翻译 prompt：按语言对定制

- 中→日：提醒假朋友（手紙→便り、勉强→学ぶ）
- 中→韩：要求使用해요체（礼貌体）
- 英→日：要求自然流畅，不逐字翻译
- 英→韩：要求使用존댓말

### 7. 异常层级

```python
class TranslatorError(Exception): pass           # Base
class UserError(TranslatorError): pass            # 用户环境问题
class ConfigError(UserError): pass                # 配置问题
class PathError(UserError): pass                  # ~/.claude/ 缺失或不可访问
class InternalError(TranslatorError): pass        # 程序 bug
```

### 8. Record 不可变

```python
@dataclass(frozen=True)
class Record:
    canonical_id: str
    kind: str
    scope: str
    source_path: str
    relative_path: str
    plugin_key: str = ""
    current_description: str = ""
    status: str = ""
    matched_translation: str = ""
    frontmatter_present: bool = True
```

所有操作返回新 Record，不原地变异。

### 9. 配置层叠

```
CLI args > 环境变量 > config.json > 硬编码默认值
```

环境变量前缀：`CLAUDE_TRANSLATE_*`

### 10. 交付形式

Python CLI + Skill 命令。用户 clone 后：
```bash
# 安装
pip install -e .
# 或直接
python -m claude_translator discover

# 注册为 Claude Code 命令
cp commands/translate-descriptions.md ~/.claude/commands/
```

## Test Matrix

| # | 场景 | 策略 | 预期 |
|---|------|------|------|
| T1 | 空环境（无 .claude） | tmp_path 空目录 | 自动创建，不崩溃 |
| T2 | 标准插件结构 | tmp_path 构造标准树 | 全部发现 |
| T3 | 非标准目录名 | 跳过 | 静默跳过 |
| T4 | 嵌套子目录 | 只取 SKILL.md 顶层 | 不取子文件 |
| T5 | 无 installed_plugins.json | fallback marketplaces/ | 降级不崩 |
| T6 | macOS/Linux 路径 | pyfakefs 模拟 | 正确解析 |
| T7 | 无 frontmatter | inject_frontmatter | 自动注入 |
| T8 | CRLF 换行 | detect_newline | 保持原格式 |
| T9 | 多语言 (--lang ja) | 文件路由 | 正确读写 |
| T10 | LLM 不可用 | FakeClient mock | 降级为 override+cache |
| T11 | 插件更新 description 变了 | canonical_id 匹配 | 自愈恢复 |
| T12 | 用户自定义 skill | user scope | user.skill:name |
| T13 | 50+ 插件性能 | 计时断言 | 扫描 < 5s |
| T14 | CLAUDE_CONFIG_DIR 覆盖 | env mock | 路径正确 |
| T15 | Windows 反斜杠路径 | normalize_path | 统一为 / |
| T16 | 权限不足 | pyfakefs readonly | 优雅报错 |
| T17 | 同一插件多版本 | cache 目录扫描 | 只取最新版 |
| T18 | CJK 混合文本检测 | 各语言样本 | 准确率 > 95% |

## Migration Plan

| 现有文件 | 处理 |
|---------|------|
| `descriptions-overrides.json` | 迁移为 `overrides-zh-CN.json`，运行时自动检测并迁移 |
| `descriptions-zh-CN.json` (legacy) | 保留读取兼容，新架构不再写入 |
| `PLUGIN_SECTION_ALIASES` | 删除 |
| `MIRROR_DIR_PLUGIN_OVERRIDES` | 删除 |
| `scanner.py` 依赖注入 | 保留，扩展为 discovery.py |
| `parse_frontmatter` / `detect_newline` | 保留，提取到 frontmatter.py / utils |
| `_batch_138.py` | 不迁移（一次性脚本） |
| `update-plugins.py` | 合并为 `cli.py sync` 子命令 |

## Out of Scope

- npm/pip 包发布（先 CLI + Skill，后续可加）
- 实时翻译（只做首次生成 + 缓存）
- 图形界面
- Windows 以外平台的 CI（先本地测试覆盖）
