import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

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
    assert "0.1.0" in result.output


def test_cli_init_creates_config(tmp_path: Path, monkeypatch):
    """init command should create a config.json in translations dir."""
    translations_dir = tmp_path / "translations"
    translations_dir.mkdir()

    runner = CliRunner()
    with patch("claude_translator.storage.paths.get_translations_dir", return_value=translations_dir):
        with patch("claude_translator.storage.paths.get_config_path", return_value=translations_dir / "config.json"):
            result = runner.invoke(main, ["init", "--lang", "ja"])

    assert result.exit_code == 0
    config_file = translations_dir / "config.json"
    assert config_file.exists()
    data = json.loads(config_file.read_text(encoding="utf-8"))
    assert data["target_lang"] == "ja"
