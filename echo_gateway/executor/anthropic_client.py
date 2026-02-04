from __future__ import annotations
from typing import Any, Dict, List, AsyncIterator
from echo_gateway.config.llm_config import LLMConfig

class AnthropicClient:
    def __init__(self, cfg: LLMConfig):
        self.cfg = cfg
        if not cfg.api_key:
            raise ValueError("LLM_API_KEY missing (fail-closed)")

    async def complete(self, messages: List[Dict[str, Any]]) -> str:
        raise NotImplementedError("Anthropic complete() will be implemented in Phase 7.2")

    async def stream(self, messages: List[Dict[str, Any]]) -> AsyncIterator[str]:
        raise NotImplementedError("Anthropic stream() will be implemented in Phase 7.2")
