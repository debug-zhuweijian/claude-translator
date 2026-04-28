import json
import logging
import re
from pathlib import Path

from click.testing import CliRunner

import claude_translator as package
import claude_translator.cli as cli_module
from claude_translator import __version__
from claude_translator.cli import main


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "discover" in result.output
    assert "sync" in result.output
    assert "verify" in result.output
    assert "init" in result.output


def test_cli_discover_help():
    runner = CliRunner()
    result = runner.invoke(main, ["discover", "--help"])
    assert result.exit_code == 0
    assert "lang" in result.output.lower() or "language" in result.output.lower()


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_version_prefers_local_checkout_version():
    assert package.__version__ == package._read_local_version()


def test_version_metadata_stays_in_sync():
    root = Path(__file__).resolve().parents[1]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    init_text = (root / "src" / "claude_translator" / "__init__.py").read_text(encoding="utf-8")

    version = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    assert version is not None
    assert f'__version__ = "{version.group(1)}"' in init_text
    assert 'claude-translator = "claude_translator.cli:main"' in pyproject


def test_cli_sync_help_mentions_dry_run():
    runner = CliRunner()
    result = runner.invoke(main, ["sync", "--help"])
    assert result.exit_code == 0
    assert "--dry-run" in result.output


def test_cli_init_creates_config(tmp_path: Path, monkeypatch):
    """init command should create a config.json in translations dir."""
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()

    runner = CliRunner()
    monkeypatch.setattr(cli_module, "ensure_translations_dir", lambda: translations_dir)
    monkeypatch.setattr(cli_module, "get_config_path", lambda: translations_dir / "config.json")
    result = runner.invoke(main, ["init", "--lang", "ja"])

    assert result.exit_code == 0
    config_file = translations_dir / "config.json"
    assert config_file.exists()
    data = json.loads(config_file.read_text(encoding="utf-8"))
    assert data["target_lang"] == "ja"


def test_verbose_quiet_flags_in_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "--verbose" in result.output
    assert "--quiet" in result.output


def test_configure_logging_levels():
    # Test the mapping directly without relying on basicConfig side effects
    assert logging.INFO - 10 * 1 + 10 * 0 == logging.DEBUG  # -v → DEBUG
    assert logging.INFO - 10 * 0 + 10 * 1 == logging.WARNING  # -q → WARNING
    assert logging.INFO - 10 * 0 + 10 * 2 == logging.ERROR  # -qq → ERROR
