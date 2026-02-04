from echo_gateway.config.llm_config import LLMConfig
from echo_gateway.executor.llm_factory import build_llm_client

def test_factory_fake():
    cfg = LLMConfig(provider="fake")
    client = build_llm_client(cfg)
    assert client.__class__.__name__.lower().startswith("fake")

def test_factory_openai():
    cfg = LLMConfig(provider="openai", api_key="x", base_url="https://api.openai.com")
    client = build_llm_client(cfg)
    assert client.__class__.__name__ == "OpenAIClient"

def test_factory_anthropic():
    cfg = LLMConfig(provider="anthropic", api_key="x")
    client = build_llm_client(cfg)
    assert client.__class__.__name__ == "AnthropicClient"
