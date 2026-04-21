import sys
import types

import pytest

import claude_translator.clients.openai_compat as openai_module
from claude_translator.clients.base import LLMClient
from claude_translator.clients.fake import FakeClient
from claude_translator.clients.openai_compat import OpenAICompatClient


def _build_response(content):
    return types.SimpleNamespace(
        choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=content))]
    )


class _DummyCompletions:
    def __init__(self, owner):
        self._owner = owner

    def create(self, **kwargs):
        self._owner.create_kwargs = kwargs
        if self._owner.raise_error is not None:
            raise self._owner.raise_error
        return _build_response(self._owner.response_content)


class _DummyOpenAI:
    response_content = '"你好世界"'
    raise_error = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.create_kwargs = None
        self.chat = types.SimpleNamespace(completions=_DummyCompletions(self))


def _install_fake_openai(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=_DummyOpenAI))


def test_fake_client_returns_prefix():
    assert FakeClient().translate("hello", "en", "zh-CN") == "[zh-CN] hello"


def test_fake_client_different_langs():
    c = FakeClient()
    assert "ja" in c.translate("test", "en", "ja")
    assert "ko" in c.translate("test", "en", "ko")


def test_llm_client_is_protocol():
    client: LLMClient = FakeClient()
    assert hasattr(client, "translate")


def test_openai_compat_init(monkeypatch):
    _install_fake_openai(monkeypatch)
    c = OpenAICompatClient(
        base_url="https://api.example.com/v1",
        api_key="test-key",
        model="test-model",
    )
    assert c._model == "test-model"
    assert c._client.kwargs["timeout"] == 30.0
    assert c._client.kwargs["max_retries"] == 2


def test_openai_compat_init_from_env(monkeypatch):
    _install_fake_openai(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://env.example.com/v1")
    c = OpenAICompatClient(model="gpt-4")
    assert c._model == "gpt-4"
    assert c._client.kwargs["base_url"] == "https://env.example.com/v1"


def test_openai_compat_translate_success(monkeypatch):
    _install_fake_openai(monkeypatch)
    monkeypatch.setattr(openai_module, "get_prompt", lambda source, target: "SYSTEM PROMPT")
    monkeypatch.setattr(
        openai_module,
        "wrap_user_content",
        lambda text: f"<wrapped>{text}</wrapped>",
    )

    client = OpenAICompatClient(model="gpt-4o-mini", api_key="test-key")

    result = client.translate("hello", "en", "zh-CN")

    assert result == "你好世界"
    assert client._client.create_kwargs["messages"] == [
        {"role": "system", "content": "SYSTEM PROMPT"},
        {"role": "user", "content": "<wrapped>hello</wrapped>"},
    ]


def test_openai_compat_translate_empty_response_raises(monkeypatch):
    _install_fake_openai(monkeypatch)
    monkeypatch.setattr(_DummyOpenAI, "response_content", None)
    client = OpenAICompatClient(model="gpt-4o-mini", api_key="test-key")

    with pytest.raises(RuntimeError, match="empty response"):
        client.translate("hello", "en", "zh-CN")


def test_openai_compat_translate_propagates_sdk_error(monkeypatch):
    _install_fake_openai(monkeypatch)
    monkeypatch.setattr(_DummyOpenAI, "raise_error", RuntimeError("boom"))
    client = OpenAICompatClient(model="gpt-4o-mini", api_key="test-key")

    with pytest.raises(RuntimeError, match="boom"):
        client.translate("hello", "en", "zh-CN")
