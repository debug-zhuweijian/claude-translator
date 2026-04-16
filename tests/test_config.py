import json
import os
from pathlib import Path
from unittest.mock import patch

from claude_translator.config.defaults import DEFAULT_TARGET_LANG, DEFAULT_LLM_MODEL
from claude_translator.config.loaders import load_config
from claude_translator.config.models import TranslatorConfig


def test_default_config():
    config = TranslatorConfig()
    assert config.target_lang == "zh-CN"
    assert config.llm.model == "gpt-4o-mini"


def test_config_from_file(tmp_path: Path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "target_lang": "ja",
        "llm": {"base_url": "https://api.example.com/v1", "api_key": "key", "model": "qwen"},
    }), encoding="utf-8")

    config = load_config(config_path=config_file)
    assert config.target_lang == "ja"
    assert config.llm.model == "qwen"


def test_config_env_override(tmp_path: Path):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"target_lang": "ja"}), encoding="utf-8")

    with patch.dict(os.environ, {"CLAUDE_TRANSLATE_LANG": "ko"}):
        config = load_config(config_path=config_file)
    assert config.target_lang == "ko"


def test_config_cascade(tmp_path: Path):
    """Env var overrides file config, file config overrides defaults."""
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "target_lang": "ja",
        "llm": {"model": "qwen"},
    }), encoding="utf-8")

    # No env override — should use file value
    with patch.dict(os.environ, {}, clear=False):
        config = load_config(config_path=config_file)
    assert config.target_lang == "ja"
    assert config.llm.model == "qwen"


def test_config_missing_file():
    """Missing config file should use defaults."""
    config = load_config(config_path=Path("/nonexistent/config.json"))
    assert config.target_lang == "zh-CN"
