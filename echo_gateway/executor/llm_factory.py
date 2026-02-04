from __future__ import annotations
from typing import Any
from echo_gateway.config.llm_config import LLMConfig

try:
    from echo_gateway.executor.fake_llm_client import FakeLLMClient  # type: ignore
except Exception:  # pragma: no cover
    class FakeLLMClient:
        async def complete(self, *args: Any, **kwargs: Any) -> str:
            return "fake"
        async def stream(self, *args: Any, **kwargs: Any):
            if False:
                yield ""

from echo_gateway.executor.openai_client import OpenAIClient
from echo_gateway.executor.anthropic_client import AnthropicClient

def build_llm_client(cfg: LLMConfig):
    if cfg.provider == "fake":
        return FakeLLMClient()
    if cfg.provider == "openai":
        return OpenAIClient(cfg)
    if cfg.provider == "anthropic":
        return AnthropicClient(cfg)
    raise ValueError(f"Unsupported provider: {cfg.provider!r}")
