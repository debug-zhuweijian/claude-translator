from claude_translator.clients.base import LLMClient
from claude_translator.clients.fake import FakeClient
from claude_translator.clients.openai_compat import OpenAICompatClient


def test_fake_client_returns_prefix():
    assert FakeClient().translate("hello", "en", "zh-CN") == "[zh-CN] hello"


def test_fake_client_different_langs():
    c = FakeClient()
    assert "ja" in c.translate("test", "en", "ja")
    assert "ko" in c.translate("test", "en", "ko")


def test_llm_client_is_protocol():
    client: LLMClient = FakeClient()
    assert hasattr(client, "translate")


def test_openai_compat_init():
    c = OpenAICompatClient(base_url="https://api.example.com/v1", api_key="test-key", model="test-model")
    assert c._model == "test-model"


def test_openai_compat_init_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "env-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://env.example.com/v1")
    c = OpenAICompatClient(model="gpt-4")
    assert c._model == "gpt-4"
