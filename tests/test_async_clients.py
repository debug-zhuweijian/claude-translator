"""Async LLM client protocol and implementations."""

from __future__ import annotations

import sys
import types

import pytest

import claude_translator.clients.async_openai as async_openai_module
from claude_translator.clients.async_fake import AsyncFakeClient
from claude_translator.clients.async_openai import AsyncOpenAICompatClient
from claude_translator.clients.base import AsyncLLMClient
from tests.async_helpers import run_coro


def _build_response(content):
    return types.SimpleNamespace(
        choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=content))]
    )


class _DummyAsyncCompletions:
    def __init__(self, owner):
        self._owner = owner

    async def create(self, **kwargs):
        self._owner.create_kwargs = kwargs
        if self._owner.raise_error is not None:
            raise self._owner.raise_error
        return _build_response(self._owner.response_content)


class _DummyAsyncOpenAI:
    response_content = '"번역 결과"'
    raise_error = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.create_kwargs = None
        self.chat = types.SimpleNamespace(completions=_DummyAsyncCompletions(self))


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


def test_async_openai_uses_env_base_url(monkeypatch, fake_async_openai):
    monkeypatch.setenv("OPENAI_API_KEY", "env-secret")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://env.example.com/v1")
    client = AsyncOpenAICompatClient(model="gpt-4o-mini")
    assert client._client.kwargs["base_url"] == "https://env.example.com/v1"


def test_async_openai_translate_success(monkeypatch, fake_async_openai):
    monkeypatch.setenv("OPENAI_API_KEY", "env-secret")
    monkeypatch.setattr(async_openai_module, "get_prompt", lambda source, target: "SYSTEM PROMPT")
    monkeypatch.setattr(
        async_openai_module,
        "wrap_user_content",
        lambda text: f"<wrapped>{text}</wrapped>",
    )

    client = AsyncOpenAICompatClient(model="gpt-4o-mini")

    result = run_coro(client.translate("hello", "en", "ko"))

    assert result == "번역 결과"
    assert client._client.create_kwargs["messages"] == [
        {"role": "system", "content": "SYSTEM PROMPT"},
        {"role": "user", "content": "<wrapped>hello</wrapped>"},
    ]


def test_async_openai_translate_empty_response_raises(monkeypatch, fake_async_openai):
    monkeypatch.setenv("OPENAI_API_KEY", "env-secret")
    monkeypatch.setattr(_DummyAsyncOpenAI, "response_content", None)
    client = AsyncOpenAICompatClient(model="gpt-4o-mini")

    with pytest.raises(RuntimeError, match="empty response"):
        run_coro(client.translate("hello", "en", "ko"))


def test_async_openai_translate_propagates_sdk_error(monkeypatch, fake_async_openai):
    monkeypatch.setenv("OPENAI_API_KEY", "env-secret")
    monkeypatch.setattr(_DummyAsyncOpenAI, "raise_error", RuntimeError("boom"))
    client = AsyncOpenAICompatClient(model="gpt-4o-mini")

    with pytest.raises(RuntimeError, match="boom"):
        run_coro(client.translate("hello", "en", "ko"))
