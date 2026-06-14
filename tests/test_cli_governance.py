from pathlib import Path

from click.testing import CliRunner

import claude_translator.cli as cli_module
from claude_translator.cli import main


def _write_entrypoint(path: Path, description: str, title: str = "Entrypoint") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ndescription: {description}\n---\n# {title}\n", encoding="utf-8")


def _write_skill(path: Path, description: str) -> None:
    _write_entrypoint(path, description, "Skill")


def _prepare_claude_dir(tmp_path: Path, description: str = "English only") -> tuple[Path, Path]:
    claude_dir = tmp_path / ".claude"
    skill = claude_dir / "skills" / "demo" / "SKILL.md"
    _write_skill(skill, description)
    (claude_dir / "translations").mkdir(parents=True, exist_ok=True)
    return claude_dir, skill


def _patch_paths(monkeypatch, claude_dir: Path) -> None:
    translations_dir = claude_dir / "translations"
    monkeypatch.setattr(cli_module, "get_claude_dir", lambda: claude_dir)
    monkeypatch.setattr(cli_module, "get_translations_dir", lambda: translations_dir)
    monkeypatch.setattr(cli_module, "ensure_translations_dir", lambda: translations_dir)
    monkeypatch.setattr(cli_module, "get_config_path", lambda: translations_dir / "config.json")


def test_cli_help_lists_govern_and_restore():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "govern" in result.output
    assert "restore" in result.output


def test_govern_defaults_to_dry_run_and_does_not_change_files(tmp_path: Path, monkeypatch):
    claude_dir, skill = _prepare_claude_dir(tmp_path)
    _patch_paths(monkeypatch, claude_dir)

    result = CliRunner().invoke(main, ["govern", "--lang", "zh-CN"])

    assert result.exit_code == 0
    assert "No files changed" in result.output
    assert "strict_language_violations=1" in result.output
    assert "planned_description_rewrites=0" in result.output
    assert "description: English only" in skill.read_text(encoding="utf-8")


def test_govern_accepts_explicit_dry_run_and_does_not_change_files(tmp_path: Path, monkeypatch):
    claude_dir, skill = _prepare_claude_dir(tmp_path)
    _patch_paths(monkeypatch, claude_dir)

    result = CliRunner().invoke(main, ["govern", "--lang", "zh-CN", "--dry-run"])

    assert result.exit_code == 0
    assert "No files changed" in result.output
    assert "strict_language_violations=1" in result.output
    assert "planned_description_rewrites=0" in result.output
    assert "description: English only" in skill.read_text(encoding="utf-8")


def test_govern_apply_writes_manifest_and_changes_file(tmp_path: Path, monkeypatch):
    claude_dir, skill = _prepare_claude_dir(tmp_path)
    _patch_paths(monkeypatch, claude_dir)

    result = CliRunner().invoke(
        main,
        ["govern", "--lang", "zh-CN", "--translation", "user.skill:demo=中文翻译", "--apply"],
    )

    assert result.exit_code == 0
    assert "backup_manifest=" in result.output
    assert "description: 中文翻译" in skill.read_text(encoding="utf-8")


def test_govern_apply_uses_existing_cache_translation(tmp_path: Path, monkeypatch):
    claude_dir, skill = _prepare_claude_dir(tmp_path)
    translations_dir = claude_dir / "translations"
    (translations_dir / "cache-zh-CN.json").write_text(
        '{"_schema_version": 1, "user.skill:demo": "缓存中文"}',
        encoding="utf-8",
    )
    _patch_paths(monkeypatch, claude_dir)

    result = CliRunner().invoke(main, ["govern", "--lang", "zh-CN", "--apply"])

    assert result.exit_code == 0
    assert "backup_manifest=" in result.output
    assert "description: 缓存中文" in skill.read_text(encoding="utf-8")


def test_restore_defaults_to_dry_run_and_apply_restores_file(tmp_path: Path, monkeypatch):
    claude_dir, skill = _prepare_claude_dir(tmp_path)
    _patch_paths(monkeypatch, claude_dir)
    apply_result = CliRunner().invoke(
        main,
        ["govern", "--lang", "zh-CN", "--translation", "user.skill:demo=中文翻译", "--apply"],
    )
    manifest_line = next(
        line for line in apply_result.output.splitlines() if "backup_manifest=" in line
    )
    manifest_path = manifest_line.split("backup_manifest=", 1)[1].split(",", 1)[0].strip()

    dry_run = CliRunner().invoke(main, ["restore", "--manifest", manifest_path])
    assert dry_run.exit_code == 0
    assert "restored=0" in dry_run.output
    assert "description: 中文翻译" in skill.read_text(encoding="utf-8")

    restored = CliRunner().invoke(main, ["restore", "--manifest", manifest_path, "--apply"])
    assert restored.exit_code == 0
    assert "restored=1" in restored.output
    assert "description: English only" in skill.read_text(encoding="utf-8")


def test_verify_strict_fails_on_translated_command_name(tmp_path: Path, monkeypatch):
    claude_dir = tmp_path / ".claude"
    command = claude_dir / "commands" / "code-review.md"
    command.parent.mkdir(parents=True)
    command.write_text(
        "---\nname: 代码审查\ndescription: 中文说明\n---\n# Code Review\n",
        encoding="utf-8",
    )
    (claude_dir / "translations").mkdir(parents=True, exist_ok=True)
    _patch_paths(monkeypatch, claude_dir)

    result = CliRunner().invoke(main, ["verify", "--lang", "zh-CN", "--strict"])

    assert result.exit_code == 1
    assert "NAME_MISMATCH" in result.output
    assert "user.command:code-review" in result.output


def test_verify_strict_fails_on_language_violation(tmp_path: Path, monkeypatch):
    claude_dir, _ = _prepare_claude_dir(tmp_path)
    _patch_paths(monkeypatch, claude_dir)

    result = CliRunner().invoke(main, ["verify", "--lang", "zh-CN", "--strict"])

    assert result.exit_code == 1
    assert "STRICT_LANGUAGE" in result.output
    assert "user.skill:demo" in result.output


def test_verify_strict_fails_on_duplicate_display_group(tmp_path: Path, monkeypatch):
    claude_dir, _ = _prepare_claude_dir(tmp_path, "中文说明")
    plugin_dir = tmp_path / "cache" / "market" / "demo-plugin" / "1.0.0"
    _write_skill(plugin_dir / "skills" / "demo" / "SKILL.md", "中文说明")
    plugins_dir = claude_dir / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    (plugins_dir / "installed_plugins.json").write_text(
        '{"version": 2, "plugins": {"demo-plugin@market": [{"installPath": "'
        + str(plugin_dir).replace("\\", "\\\\")
        + '", "version": "1.0.0"}]}}',
        encoding="utf-8",
    )
    _patch_paths(monkeypatch, claude_dir)

    result = CliRunner().invoke(main, ["verify", "--lang", "zh-CN", "--strict"])

    assert result.exit_code == 1
    assert "DUPLICATE_DISPLAY" in result.output
    assert "skill:demo" in result.output


def test_verify_strict_fails_on_unknown_plugin_dotted_entrypoint(tmp_path: Path, monkeypatch):
    claude_dir, _ = _prepare_claude_dir(tmp_path, "中文说明")
    plugin_dir = tmp_path / "cache" / "market" / "demo-plugin" / "1.0.0"
    hidden_command = plugin_dir / ".unknown" / "commands"
    hidden_command.mkdir(parents=True)
    (hidden_command / "promote.md").write_text(
        "---\ndescription: Hidden command\n---\n# Promote\n",
        encoding="utf-8",
    )
    plugins_dir = claude_dir / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    (plugins_dir / "installed_plugins.json").write_text(
        '{"version": 2, "plugins": {"demo-plugin@market": [{"installPath": "'
        + str(plugin_dir).replace("\\", "\\\\")
        + '", "version": "1.0.0"}]}}',
        encoding="utf-8",
    )
    _patch_paths(monkeypatch, claude_dir)

    result = CliRunner().invoke(main, ["verify", "--lang", "zh-CN", "--strict"])

    assert result.exit_code == 1
    assert "UNKNOWN_DOTTED_ENTRYPOINT" in result.output
    assert ".unknown" in result.output
    assert "Unknown dotted plugin entrypoint directory" in result.output


def test_verify_non_strict_allows_unknown_plugin_dotted_entrypoint(tmp_path: Path, monkeypatch):
    claude_dir, _ = _prepare_claude_dir(tmp_path, "中文说明")
    plugin_dir = tmp_path / "cache" / "market" / "demo-plugin" / "1.0.0"
    hidden_command = plugin_dir / ".unknown" / "commands"
    hidden_command.mkdir(parents=True)
    (hidden_command / "promote.md").write_text(
        "---\ndescription: Hidden command\n---\n# Promote\n",
        encoding="utf-8",
    )
    plugins_dir = claude_dir / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    (plugins_dir / "installed_plugins.json").write_text(
        '{"version": 2, "plugins": {"demo-plugin@market": [{"installPath": "'
        + str(plugin_dir).replace("\\", "\\\\")
        + '", "version": "1.0.0"}]}}',
        encoding="utf-8",
    )
    _patch_paths(monkeypatch, claude_dir)

    result = CliRunner().invoke(main, ["verify", "--lang", "zh-CN"])

    assert result.exit_code == 0
    assert "UNKNOWN_DOTTED_ENTRYPOINT" not in result.output


def test_govern_apply_ignores_plugin_compatibility_mirrors(tmp_path: Path, monkeypatch):
    claude_dir, _ = _prepare_claude_dir(tmp_path, "中文说明")
    user_command = claude_dir / "commands" / "promote.md"
    _write_entrypoint(user_command, "中文说明")
    plugin_dir = tmp_path / "cache" / "market" / "demo-plugin" / "1.0.0"
    _write_skill(plugin_dir / "skills" / "demo" / "SKILL.md", "中文说明")
    _write_skill(plugin_dir / ".agents" / "skills" / "demo" / "SKILL.md", "English mirror")
    _write_entrypoint(plugin_dir / "commands" / "promote.md", "中文说明")
    _write_entrypoint(plugin_dir / ".opencode" / "commands" / "promote.md", "English mirror")
    plugins_dir = claude_dir / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    (plugins_dir / "installed_plugins.json").write_text(
        '{"version": 2, "plugins": {"demo-plugin@market": [{"installPath": "'
        + str(plugin_dir).replace("\\", "\\\\")
        + '", "version": "1.0.0"}]}}',
        encoding="utf-8",
    )
    _patch_paths(monkeypatch, claude_dir)

    result = CliRunner().invoke(main, ["govern", "--lang", "zh-CN", "--apply"])
    verified = CliRunner().invoke(main, ["verify", "--lang", "zh-CN", "--strict"])

    assert result.exit_code == 0
    assert verified.exit_code == 0


def test_discover_audit_reports_duplicate_display_groups(tmp_path: Path, monkeypatch):
    claude_dir, _ = _prepare_claude_dir(tmp_path, "中文说明")
    plugin_dir = tmp_path / "cache" / "market" / "demo-plugin" / "1.0.0"
    _write_skill(plugin_dir / "skills" / "demo" / "SKILL.md", "中文说明")
    plugins_dir = claude_dir / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    (plugins_dir / "installed_plugins.json").write_text(
        '{"version": 2, "plugins": {"demo-plugin@market": [{"installPath": "'
        + str(plugin_dir).replace("\\", "\\\\")
        + '", "version": "1.0.0"}]}}',
        encoding="utf-8",
    )
    _patch_paths(monkeypatch, claude_dir)

    result = CliRunner().invoke(main, ["discover", "--lang", "zh-CN", "--audit"])

    assert result.exit_code == 0
    assert "duplicate display groups: 1" in result.output


def test_govern_apply_autofills_missing_descriptions_and_suppresses_duplicates(
    tmp_path: Path, monkeypatch
):
    claude_dir, skill = _prepare_claude_dir(tmp_path)
    command = claude_dir / "commands" / "demo.md"
    _write_entrypoint(command, "")
    plugin_dir = tmp_path / "cache" / "market" / "demo-plugin" / "1.0.0"
    plugin_skill = plugin_dir / "skills" / "demo" / "SKILL.md"
    _write_skill(plugin_skill, "中文说明")
    plugins_dir = claude_dir / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    (plugins_dir / "installed_plugins.json").write_text(
        '{"version": 2, "plugins": {"demo-plugin@market": [{"installPath": "'
        + str(plugin_dir).replace("\\", "\\\\")
        + '", "version": "1.0.0"}]}}',
        encoding="utf-8",
    )
    translations_dir = claude_dir / "translations"
    (translations_dir / "cache-zh-CN.json").write_text(
        '{"_schema_version": 1, "user.skill:demo": "缓存中文", "user.command:demo": "命令中文"}',
        encoding="utf-8",
    )
    _patch_paths(monkeypatch, claude_dir)

    result = CliRunner().invoke(main, ["govern", "--lang", "zh-CN", "--apply"])
    verified = CliRunner().invoke(main, ["verify", "--lang", "zh-CN", "--strict"])

    assert result.exit_code == 0
    assert "applied_description_rewrites=2" in result.output
    assert "applied_duplicate_suppressions=1" in result.output
    assert verified.exit_code == 0
    assert "description: 缓存中文" in skill.read_text(encoding="utf-8")
    suppressed_plugin_skill = plugin_skill.with_name("SKILL.md.claude-translator-disabled")
    assert "description: 命令中文" in command.read_text(encoding="utf-8")
    assert not plugin_skill.exists()
    assert suppressed_plugin_skill.exists()

    manifest_line = next(line for line in result.output.splitlines() if "backup_manifest=" in line)
    manifest_path = manifest_line.split("backup_manifest=", 1)[1].split(",", 1)[0].strip()
    suppressed_plugin_skill.unlink()
    restored = CliRunner().invoke(main, ["restore", "--manifest", manifest_path, "--apply"])

    assert restored.exit_code == 0
    assert "restored=3" in restored.output
    assert plugin_skill.exists()
    assert not suppressed_plugin_skill.exists()
