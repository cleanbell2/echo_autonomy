from __future__ import annotations
import json
from typing import Any, AsyncIterator, Dict, List

import httpx
from echo_gateway.config.llm_config import LLMConfig

class OpenAIClient:
    def __init__(self, cfg: LLMConfig):
        self.cfg = cfg
        self.base_url = (cfg.base_url or "https://api.openai.com").rstrip("/")
        if not cfg.api_key:
            raise ValueError("LLM_API_KEY missing (fail-closed)")
        self.api_key = cfg.api_key

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _url(self) -> str:
        return f"{self.base_url}/v1/chat/completions"

    async def complete(self, messages: List[Dict[str, Any]]) -> str:
        payload = {
            "model": self.cfg.model,
            "messages": messages,
            "temperature": self.cfg.temperature,
            "max_tokens": self.cfg.max_tokens,
            "stream": False,
        }
        timeout = httpx.Timeout(self.cfg.request_timeout_s)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(self._url(), headers=self._headers(), json=payload)
            r.raise_for_status()
            data = r.json()
        return data["choices"][0]["message"]["content"]

    async def stream(self, messages: List[Dict[str, Any]]) -> AsyncIterator[str]:
        payload = {
            "model": self.cfg.model,
            "messages": messages,
            "temperature": self.cfg.temperature,
            "max_tokens": self.cfg.max_tokens,
            "stream": True,
        }
        timeout = httpx.Timeout(self.cfg.request_timeout_s)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", self._url(), headers=self._headers(), json=payload) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        chunk = line[len("data:"):].strip()
                        if chunk == "[DONE]":
                            return
                        try:
                            obj = json.loads(chunk)
                            delta = obj["choices"][0].get("delta", {}).get("content")
                            if delta:
                                yield delta
                        except json.JSONDecodeError as e:
                            raise ValueError("OpenAI stream parse failed") from e
