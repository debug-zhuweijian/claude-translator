# Claude Translator 项目审查报告

## 概述

**项目定位**：`claude-translator` 是一个将 Claude Code 插件/技能/命令中英文 frontmatter description 翻译到用户目标语言的 CLI 工具。设计清晰、职责分明、测试完备（126 个测试全部通过，ruff lint/format 也通过）。整体工程素质优于一般的个人工具。

**版本**：0.2.0 · Python 3.10+ · 以 `pyproject.toml` + hatchling 管理

---

## 一、架构亮点（做得好的地方）

### 1. 清晰的分层

```
cli.py              # 入口 / 命令编排
├── config/         # pydantic 配置模型 + 级联加载 (CLI > ENV > file > defaults)
├── core/
│   ├── discovery   # 发现可翻译项
│   ├── canonical   # 生成稳定 ID
│   ├── translator  # 4 级 fallback 翻译链
│   ├── pipeline    # 总编排
│   ├── frontmatter # ruamel.yaml 读写
│   └── injector    # 原子回写（保 BOM、保换行风格）
├── clients/        # LLMClient Protocol + OpenAI/Fake 实现
├── storage/        # cache / overrides / paths（原子写）
└── lang/           # prompts / cleaner / CJK detect
```

每一层的依赖方向干净，`clients/base.py` 用 `Protocol` 抽象 LLM 后端，`FakeClient` 让 CLI 测试不依赖外部服务 — 这点很专业。

### 2. 翻译链的 4 级 fallback

`src/claude_translator/core/translator.py` 中 `TranslationChain.resolve` 的顺序：

```
override → cache → LLM → fallback(原文)
```

这个顺序保证了：用户手改的 override 最高优先；cache 避免重复花 API 费用；LLM 失败时降级到原文而不是抛错。设计是正确的。

### 3. 文件写入的健壮性

`src/claude_translator/storage/cache.py` 中的 `_atomic_write_text`：

```python
def _atomic_write_text(path: Path, content: str) -> None:
    fd, temp_path = tempfile.mkstemp(dir=path.parent, prefix=f"{path.name}.", suffix=".tmp")
    try:
        with open(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        Path(temp_path).replace(path)
    finally:
        temp = Path(temp_path)
        if temp.exists():
            temp.unlink()
```

同目录 tempfile → `os.replace`，在 Windows 上也能原子替换。`injector.py` 则保留 BOM 和换行风格（`\r\n` vs `\n`），这是很多工具会忽略的细节。

### 4. LLM 响应清洗

`src/claude_translator/lang/cleaner.py` 对 LLM 输出做反引号、多行、`---` 分隔符等检查。如果 LLM 吐出来的东西会破坏 frontmatter，直接拒绝而不是写入文件 — 这是对的，防御性很好。

### 5. 测试覆盖

126 个测试分布：
- `test_cli.py`：CLI 命令集成
- `test_cache.py` / `test_overrides.py`：存储层
- `test_translator.py`：4 级 fallback 的所有路径
- `test_cleaner.py`：LLM 响应清洗的边界
- `test_canonical.py`：ID 往返
- `test_performance.py`：基本性能基线

覆盖面是完整的。

---

## 二、发现的问题（按严重性排序）

### P1 · CI 不跑测试 — **最严重**

`.github/workflows/ci.yml` 只有 `ruff check` 和 `ruff format --check`，**没有** `pytest` 步骤。项目有 126 个测试，CI 却完全不执行它们 — 这意味着 PR 合并时没有任何自动化的正确性保障。

**修复**：在 `ci.yml` 的 steps 末尾追加：

```yaml
      - name: Install project with dev extras
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest
```

（当前的 install 步骤只装了基础依赖，没装 `[dev]` 里的 pytest。）

---

### P2 · `parse_canonical_id` 对含点的 plugin key 解析错误 — **已验证**

实际跑了一次验证：

```
输入：generate_canonical_id('skill', 'foo', 'plugin', 'pua.skills')
生成：'plugin.pua.skills.skill:foo'
解析回：('plugin', 'pua', 'skills.skill', 'foo')   ← 错误
期望：('plugin', 'pua.skills', 'skill', 'foo')
```

问题在 `src/claude_translator/core/canonical.py`：

```python
key_and_rest = without_prefix.split(".", 1)  # 只按第一个点切
```

**影响范围**：`parse_canonical_id` 目前**只在测试中使用**（grep 确认），所以线上 pipeline 不会踩到这个雷。但它是公开函数，语义上和 `generate_canonical_id` 形成不对称 — 生成可以接受任意 plugin key，但解析会丢信息。

**修复建议**：改成从右侧寻找 `:`，中间整段按最后一个 `.` 切：

```python
def parse_canonical_id(cid: str) -> tuple[str, str, str, str]:
    if not cid.startswith("plugin."):
        # ... user-level 分支保持不变
        ...
    without_prefix = cid[len("plugin."):]
    if ":" not in without_prefix:
        raise ConfigError(f"Invalid plugin canonical ID: {cid!r}")
    key_and_kind, name = without_prefix.rsplit(":", 1)
    if "." not in key_and_kind:
        raise ConfigError(f"Invalid plugin canonical ID: {cid!r}")
    plugin_key, kind = key_and_kind.rsplit(".", 1)
    return "plugin", plugin_key, kind, name
```

并在 `test_canonical.py` 里加一个 round-trip 测试覆盖 `plugin_key` 含点的情况。

---

### P3 · `__init__.py` 读版本的路径脆弱

```python
pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
```

这依赖 `src/claude_translator/__init__.py` 到 `pyproject.toml` 恰好是两级。在以下场景会失败（返回 `"unknown"`）：
- `pip install .`（非 editable）后包被复制到 site-packages，`parents[2]` 不再指向 repo 根
- 被打包成 wheel 后重新安装

**更好的做法**：优先用 `importlib.metadata`，fallback 才读本地文件：

```python
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("claude-translator")
except PackageNotFoundError:
    __version__ = _read_local_version() or "unknown"
```

这样 editable install 和 wheel install 都能正确拿到版本。

---

### P4 · `tempfile` 在无写权限目录会暴露 OSError

`_atomic_write_text` 把 tempfile 放在目标文件同目录（这是原子替换的必要条件），但如果 `translations/` 目录只读（例如 Windows 上用户权限问题），`mkstemp` 会抛 `FileNotFoundError` 或 `PermissionError`，而上层没有针对性捕获。目前只会冒泡出成 CLI 的栈 trace。

**建议**：在 `_atomic_write_text` 外层或 `save_cache` / `save_overrides` 里捕获 `OSError`，转成 `FileSystemError`（已有这个异常类型），给出友好提示。

---

### P5 · `discovery` 对插件多版本去重依赖 semver 假设

`src/claude_translator/core/discovery.py` 在同一个 plugin 出现多个版本目录时只保留最新。如果版本号不是标准 semver（例如 `"1.2.3-beta"` 或手动打的 tag），比较可能出错。这在 Claude 插件生态下目前不是高风险，但值得加个防御。

---

### P6 · `cleaner.py` 的单行约束可能过于严苛

`TranslationCleaner` 拒绝多行输出，但某些目标语言（比如日语正式表达）偶尔会有复合句式。LLM 倾向于保持单行，但一旦出现换行就 fallback 到原文。如果用户在海外用日文/韩文版本遇到 description 无法翻译，可能要追溯到这里。

**建议**：保留"拒绝 `---`"这一硬红线（会破坏 frontmatter），但对内部换行可以考虑合并为空格而非拒绝。当然这是 policy 决定，按当前"保守优于破坏"思路也是合理的。

---

### P7 · 缺少 `__main__.py`

包里没有 `src/claude_translator/__main__.py`，所以 `python -m claude_translator` 不工作，只能通过 `claude-translator` entry point。对一个 CLI 工具来说，支持 `python -m` 调用是很常见的期待。

**修复**：加一个极简的 `__main__.py`：

```python
from claude_translator.cli import main

if __name__ == "__main__":
    main()
```

---

## 三、小建议（Nice-to-have）

1. **`README.md` 缺一份示例 `config.toml`**：用户通过 `init` 命令可以生成，但 README 里直接给一段范例能降低上手门槛。
2. **`pyproject.toml` 可以加 `[project.urls]`**：homepage / repository / issues，以后上 PyPI 会有用。
3. **日志级别没有 CLI 开关**：`--verbose` / `--quiet` 可以直接映射到 `logging.DEBUG/WARNING`。目前 logger 是配置好的但没有暴露给用户。
4. **`cache-{lang}.json` 没有 schema 版本号**：未来格式演进会比较痛苦。可以在 JSON 根上加 `"_schema_version": 1`。
5. **`prompts.py` 里的语言提示词是硬编码字符串**：考虑放到外部 `.toml` 或 `resources/` 目录，方便非开发者贡献新语言。

---

## 四、整体评价

| 维度 | 评分 | 说明 |
|------|------|------|
| 架构设计 | A | 分层清晰、Protocol 抽象、依赖方向正确 |
| 代码质量 | A- | 函数短小、命名清晰、有类型注解；ruff 全过 |
| 健壮性 | B+ | 原子写/BOM/换行处理到位；但 CI 不跑测试、版本读取脆弱拉低分 |
| 测试覆盖 | A | 126 个测试，覆盖 CLI、核心链、存储、清洗、CJK |
| 文档 | B | README 结构清晰但缺少完整配置示例 |
| 生态契合度 | A | 对 Claude Code 插件/技能的目录结构理解准确 |

**总体**：这是一份质量不错的、有经过认真思考的工程作品。三个值得立刻修的问题按优先级是：

1. **CI 加 `pytest`**（5 分钟工作量，收益最大）
2. **`parse_canonical_id` 修 round-trip 对称性 + 测试**（20 分钟）
3. **版本读取改用 `importlib.metadata`**（10 分钟）

其余都属于渐进式打磨。

---

*审查日期：2026-04-18*
