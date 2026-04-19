"""Async LLM client protocol and implementations."""

from __future__ import annotations

import sys
import types

import pytest

from claude_translator.clients.async_fake import AsyncFakeClient
from claude_translator.clients.async_openai import AsyncOpenAICompatClient
from claude_translator.clients.base import AsyncLLMClient
from tests.async_helpers import run_coro


class _DummyAsyncOpenAI:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


@pytest.fixture
def fake_async_openai(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "openai",
        types.SimpleNamespace(AsyncOpenAI=_DummyAsyncOpenAI, OpenAI=_DummyAsyncOpenAI),
    )


def test_async_fake_returns_prefix():
    result = run_coro(AsyncFakeClient().translate("hello", "en", "zh-CN"))
    assert result == "[zh-CN] hello"


def test_async_fake_is_protocol_compatible():
    client: AsyncLLMClient = AsyncFakeClient()
    assert hasattr(client, "translate")


def test_async_openai_missing_key_fails_fast(monkeypatch, fake_async_openai):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OpenAI API key"):
        AsyncOpenAICompatClient(model="gpt-4o-mini")


def test_async_openai_accepts_env_key(monkeypatch, fake_async_openai):
    monkeypatch.setenv("OPENAI_API_KEY", "env-secret")
    client = AsyncOpenAICompatClient(model="gpt-4o-mini")
    assert client._client.kwargs["api_key"] == "env-secret"


def test_async_openai_explicit_key(monkeypatch, fake_async_openai):
    monkeypatch.setenv("OPENAI_API_KEY", "env-secret")
    client = AsyncOpenAICompatClient(model="gpt-4o-mini", api_key="explicit")
    assert client._client.kwargs["api_key"] == "explicit"
