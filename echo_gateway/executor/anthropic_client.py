"""
Anthropic (Claude) LLM Client Adapter

Key differences from OpenAI:
- System prompts must be passed as separate 'system' parameter
- Different streaming event structure
- Different error handling approach
"""
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from anthropic import AsyncAnthropic, APIStatusError, RateLimitError, AuthenticationError

from echo_gateway.executor.llm_client import LLMClient

logger = logging.getLogger(__name__)


class AnthropicClient(LLMClient):
    """
    Adapter for Anthropic API (Claude).
    
    Handles message format translation:
    - Extracts 'system' role messages → separate system parameter
    - Translates streaming events to unified format
    - Fail-closed error handling
    """
    
    def __init__(self, cfg):
        """
        Initialize Anthropic client from LLMConfig.
        
        Args:
            cfg: LLMConfig instance with provider='anthropic'
        """
        if not cfg.api_key:
            raise ValueError("Anthropic API key required (fail-closed)")
            
        self.cfg = cfg
        self.client = AsyncAnthropic(
            api_key=cfg.api_key,
            timeout=cfg.request_timeout_s,
            base_url=cfg.base_url
        )

    def _prepare_messages(self, messages: List[Dict[str, Any]]):
        """
        Extract 'system' message as separate parameter (Anthropic requirement).
        
        OpenAI format: [{"role": "system", "content": "..."}, {"role": "user", ...}]
        Anthropic format: system="...", messages=[{"role": "user", ...}]
        
        Returns: (system_prompt, filtered_messages)
        """
        system_prompt = None
        filtered_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                # Extract system content (take last if multiple)
                system_prompt = msg["content"]
            else:
                filtered_messages.append(msg)
                
        return system_prompt, filtered_messages

    async def complete(
        self, 
        messages: List[Dict[str, Any]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Non-streaming completion with Anthropic API.
        
        Returns unified format:
        {
            "content": str,
            "tool_calls": Optional[List],  # Phase 7.4
            "finish_reason": str
        }
        """
        system, clean_msgs = self._prepare_messages(messages)
        
        try:
            # Build request parameters
            params = {
                "model": self.cfg.model,
                "messages": clean_msgs,
                "max_tokens": self.cfg.max_tokens,
                "temperature": temperature if temperature is not None else self.cfg.temperature,
            }
            
            # Add system prompt if present
            if system:
                params["system"] = system
                
            # TODO: Tool support integration in Phase 7.4
            
            response = await self.client.messages.create(**params)
            
            # Convert to unified format
            return {
                "content": response.content[0].text if response.content else "",
                "tool_calls": None,  # Phase 7.4
                "finish_reason": response.stop_reason
            }

        except AuthenticationError:
            logger.error("Anthropic authentication failed")
            raise ValueError("Invalid Anthropic API Key")
        except RateLimitError:
            logger.error("Anthropic rate limit exceeded")
            raise RuntimeError("Anthropic Rate Limit Exceeded")
        except APIStatusError as e:
            logger.error(f"Anthropic API error: {e}")
            raise RuntimeError(f"Anthropic API Error: {e}")

    async def stream(
        self, 
        messages: List[Dict[str, Any]], 
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Streaming completion with event translation.
        
        Anthropic events:
        - content_block_delta → text delta
        - message_delta → finish reason
        
        Yields unified format matching OpenAI structure.
        """
        system, clean_msgs = self._prepare_messages(messages)
        
        try:
            params = {
                "model": self.cfg.model,
                "messages": clean_msgs,
                "max_tokens": self.cfg.max_tokens,
                "temperature": temperature if temperature is not None else self.cfg.temperature,
                "stream": True
            }
            
            if system:
                params["system"] = system

            # Create streaming request
            async with self.client.messages.stream(**params) as stream:
                async for event in stream:
                    # Map Anthropic events to standard delta format
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'text'):
                            yield {
                                "content": event.delta.text,
                                "tool_calls": None,
                                "finish_reason": None
                            }
                    elif event.type == "message_delta":
                        if hasattr(event.delta, 'stop_reason'):
                            yield {
                                "content": "",
                                "tool_calls": None,
                                "finish_reason": event.delta.stop_reason
                            }
                    
        except APIStatusError as e:
            logger.error(f"Anthropic stream failed: {e}")
            raise RuntimeError(f"Anthropic Stream Failed: {e}")
