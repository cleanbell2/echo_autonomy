from __future__ import annotations
from dataclasses import dataclass
import os
from typing import Literal, Optional

Provider = Literal["fake", "openai", "anthropic"]

@dataclass(frozen=True)
class LLMConfig:
    provider: Provider = "fake"
    model: str = "gpt-4o-mini"
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024
    request_timeout_s: float = 30.0

    @classmethod
    def from_env(cls) -> "LLMConfig":
        provider = os.getenv("LLM_PROVIDER", "fake").strip().lower()
        model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
        base_url = (os.getenv("LLM_BASE_URL") or "").strip() or None
        api_key = (os.getenv("LLM_API_KEY") or "").strip() or None

        temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1024"))
        request_timeout_s = float(os.getenv("LLM_TIMEOUT_S", "30"))

        if provider not in ("fake", "openai", "anthropic"):
            raise ValueError(f"Unsupported LLM_PROVIDER: {provider!r}")

        if provider != "fake" and not api_key:
            raise ValueError("LLM_API_KEY is required when LLM_PROVIDER is not 'fake'")

        return cls(
            provider=provider,  # type: ignore[arg-type]
            model=model,
            base_url=base_url,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            request_timeout_s=request_timeout_s,
        )
