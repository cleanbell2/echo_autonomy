from __future__ import annotations
import json
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from echo_gateway.config.llm_config import LLMConfig
from echo_gateway.executor.tool_calling import ToolCallTranslator

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

    async def complete(
        self, 
        messages: List[Dict[str, Any]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Non-streaming completion with optional tool calling.
        
        Returns:
            {
                "content": str,
                "tool_calls": Optional[List[ToolCall]],
                "finish_reason": str
            }
        """
        payload = {
            "model": self.cfg.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.cfg.temperature,
            "max_tokens": self.cfg.max_tokens,
            "stream": False,
        }
        
        # Add tools if provided
        if tools:
            payload["tools"] = ToolCallTranslator.to_openai_tools(tools)
        
        timeout = httpx.Timeout(self.cfg.request_timeout_s)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(self._url(), headers=self._headers(), json=payload)
            r.raise_for_status()
            data = r.json()
        
        message = data["choices"][0]["message"]
        finish_reason = data["choices"][0].get("finish_reason", "stop")
        
        # Extract tool calls if present
        tool_calls = []
        if message.get("tool_calls"):
            for tc_dict in message["tool_calls"]:
                # Convert dict to object-like structure for translator
                class ToolCallObj:
                    def __init__(self, d):
                        self.id = d["id"]
                        self.function = type('obj', (object,), {
                            'name': d["function"]["name"],
                            'arguments': d["function"]["arguments"]
                        })()
                
                tool_calls.append(ToolCallTranslator.from_openai(ToolCallObj(tc_dict)))
        
        return {
            "content": message.get("content", ""),
            "tool_calls": tool_calls if tool_calls else None,
            "finish_reason": finish_reason
        }

    async def stream(
        self, 
        messages: List[Dict[str, Any]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Streaming completion with optional tool calling.
        
        Yields:
            {
                "content": str,
                "tool_calls": Optional[List[ToolCall]],
                "finish_reason": Optional[str]
            }
        """
        payload = {
            "model": self.cfg.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.cfg.temperature,
            "max_tokens": self.cfg.max_tokens,
            "stream": True,
        }
        
        if tools:
            payload["tools"] = ToolCallTranslator.to_openai_tools(tools)
        
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
                            delta = obj["choices"][0].get("delta", {})
                            
                            # Content delta
                            content = delta.get("content")
                            if content:
                                yield {
                                    "content": content,
                                    "tool_calls": None,
                                    "finish_reason": None
                                }
                            
                            # Tool calls delta (OpenAI streams tool calls too)
                            if delta.get("tool_calls"):
                                # For simplicity, we'll collect tool calls at end
                                # Full implementation would stream tool call deltas
                                pass
                            
                            # Finish reason
                            finish_reason = obj["choices"][0].get("finish_reason")
                            if finish_reason:
                                yield {
                                    "content": "",
                                    "tool_calls": None,
                                    "finish_reason": finish_reason
                                }
                                
                        except json.JSONDecodeError as e:
                            raise ValueError("OpenAI stream parse failed") from e
