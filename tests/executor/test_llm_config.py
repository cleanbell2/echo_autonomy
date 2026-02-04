import pytest
from echo_gateway.config.llm_config import LLMConfig

def test_llm_config_default_fake(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    cfg = LLMConfig.from_env()
    assert cfg.provider == "fake"

def test_llm_config_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "weird")
    with pytest.raises(ValueError):
        LLMConfig.from_env()

def test_llm_config_fail_closed_requires_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(ValueError):
        LLMConfig.from_env()
