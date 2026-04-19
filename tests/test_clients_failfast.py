"""Fail-fast validation of OpenAI API key."""

import sys
import types

import pytest

from claude_translator.clients.openai_compat import OpenAICompatClient


class _DummyOpenAI:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


@pytest.fixture
def fake_openai(monkeypatch):
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=_DummyOpenAI))


def test_missing_api_key_raises(monkeypatch, fake_openai):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OpenAI API key"):
        OpenAICompatClient(model="gpt-4o-mini")


def test_empty_string_api_key_raises(monkeypatch, fake_openai):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OpenAI API key"):
        OpenAICompatClient(model="gpt-4o-mini", api_key="")


def test_env_key_accepted(monkeypatch, fake_openai):
    monkeypatch.setenv("OPENAI_API_KEY", "env-secret")
    client = OpenAICompatClient(model="gpt-4o-mini")
    assert client._client.kwargs["api_key"] == "env-secret"


def test_explicit_key_overrides_env(monkeypatch, fake_openai):
    monkeypatch.setenv("OPENAI_API_KEY", "env-secret")
    client = OpenAICompatClient(model="gpt-4o-mini", api_key="explicit")
    assert client._client.kwargs["api_key"] == "explicit"
