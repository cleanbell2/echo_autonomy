# gateway/auth_profiles.py
"""
Auth Profile Manager with Failover & Cooldown.

Key principles:
- ENV references only (no plaintext keys in config)
- last_success prioritization
- cooldown tracking per profile
- automatic failover on errors

Based on OpenClaw's auth profile system with safety enhancements.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, TypeVar

FailReason = Literal[
    "auth",
    "rate_limit",
    "timeout",
    "context_overflow",
    "model_unavailable",
    "unknown",
]


@dataclass(frozen=True)
class AuthProfile:
    """Immutable auth profile configuration."""

    id: str
    provider: str
    api_key_ref: str  # e.g. "ENV:OPENAI_KEY_1"
    priority: int = 0


@dataclass
class ProviderPolicy:
    """Policy for provider failover behavior."""

    cooldown_seconds: int = 1800  # 30 minutes default
    prefer_last_success: bool = True


class AuthProfilesError(RuntimeError):
    """Auth profile related errors."""

    pass


class AuthProfileStore:
    """
    Auth profile storage with runtime state management.

    Files:
    - auth-profiles.json: static config (profiles, priorities)
    - auth-runtime.json: runtime state (last_success, cooldowns)

    Security:
    - API keys MUST be ENV references (ENV:NAME)
    - No plaintext secrets in config files
    - Runtime state is ephemeral (safe to delete)
    """

    def __init__(self, profiles_path: Path, runtime_path: Path):
        self.profiles_path = profiles_path
        self.runtime_path = runtime_path
        self._profiles_cache: Dict[str, List[AuthProfile]] = {}
        self._policy: ProviderPolicy = ProviderPolicy()
        self._runtime: Dict[str, Any] = {"last_success": {}, "cooldowns": {}}
        self.reload()

    # -------------------------
    # Load / Save
    # -------------------------
    def reload(self) -> None:
        """Reload configuration from disk."""
        self._profiles_cache = {}
        self._policy = ProviderPolicy()
        self._runtime = {"last_success": {}, "cooldowns": {}}

        if not self.profiles_path.exists():
            raise AuthProfilesError(f"missing profiles config: {self.profiles_path}")

        cfg = json.loads(self.profiles_path.read_text(encoding="utf-8"))
        policy = cfg.get("policy", {}) or {}
        self._policy = ProviderPolicy(
            cooldown_seconds=int(policy.get("cooldown_seconds", 1800)),
            prefer_last_success=bool(policy.get("prefer_last_success", True)),
        )

        providers = cfg.get("providers") or {}
        for provider, p in providers.items():
            profiles = []
            for x in p.get("profiles") or []:
                profiles.append(
                    AuthProfile(
                        id=str(x["id"]),
                        provider=str(provider),
                        api_key_ref=str(x["api_key"]),
                        priority=int(x.get("priority", 0)),
                    )
                )
            # Sort by priority desc (higher priority first)
            profiles.sort(key=lambda z: z.priority, reverse=True)
            self._profiles_cache[provider] = profiles

        if self.runtime_path.exists():
            try:
                self._runtime = json.loads(
                    self.runtime_path.read_text(encoding="utf-8")
                )
            except Exception:
                # Fail-closed: if runtime corrupted, start fresh (but do not crash)
                self._runtime = {"last_success": {}, "cooldowns": {}}
        else:
            self._save_runtime()

        # Normalize
        self._runtime.setdefault("last_success", {})
        self._runtime.setdefault("cooldowns", {})

    def _save_runtime(self) -> None:
        """Persist runtime state to disk."""
        self.runtime_path.parent.mkdir(parents=True, exist_ok=True)
        self.runtime_path.write_text(
            json.dumps(self._runtime, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # -------------------------
    # Key resolution (ENV only)
    # -------------------------
    def resolve_api_key(self, api_key_ref: str) -> str:
        """
        Resolve API key from ENV reference.

        Only supports ENV:<NAME> format.
        This prevents accidental persistence of secrets in repo/files.

        Args:
            api_key_ref: Reference string (e.g. "ENV:OPENAI_KEY_1")

        Returns:
            Resolved API key from environment

        Raises:
            AuthProfilesError: If not ENV reference or env var missing
        """
        if not api_key_ref.startswith("ENV:"):
            raise AuthProfilesError(
                "api_key must be ENV:<NAME> reference (no plaintext keys)."
            )
        env_name = api_key_ref.split(":", 1)[1].strip()
        val = os.environ.get(env_name, "")
        if not val:
            raise AuthProfilesError(f"missing env var for api key: {env_name}")
        return val

    # -------------------------
    # Cooldown
    # -------------------------
    def is_in_cooldown(self, profile_id: str, now: Optional[float] = None) -> bool:
        """Check if profile is currently in cooldown."""
        now = time.time() if now is None else now
        cd = (self._runtime.get("cooldowns") or {}).get(profile_id)
        if not cd:
            return False
        return float(cd.get("until", 0)) > now

    def set_cooldown(
        self, profile_id: str, reason: FailReason, seconds: Optional[int] = None
    ) -> None:
        """
        Put profile into cooldown.

        Args:
            profile_id: Profile identifier
            reason: Failure reason for tracking
            seconds: Cooldown duration (uses policy default if None)
        """
        seconds = self._policy.cooldown_seconds if seconds is None else int(seconds)
        until = time.time() + seconds
        self._runtime["cooldowns"][profile_id] = {"until": until, "reason": reason}
        self._save_runtime()

    def clear_cooldown(self, profile_id: str) -> None:
        """Remove profile from cooldown."""
        if profile_id in (self._runtime.get("cooldowns") or {}):
            del self._runtime["cooldowns"][profile_id]
            self._save_runtime()

    # -------------------------
    # Selection / Failover
    # -------------------------
    def get_candidates(self, provider: str) -> List[AuthProfile]:
        """
        Get ordered list of profiles for provider.

        If prefer_last_success=True, last successful profile is first.
        Otherwise ordered by priority.

        Args:
            provider: Provider name (e.g. "openai")

        Returns:
            Ordered list of profiles

        Raises:
            AuthProfilesError: If no profiles for provider
        """
        profiles = list(self._profiles_cache.get(provider, []))
        if not profiles:
            raise AuthProfilesError(f"no profiles for provider: {provider}")

        if self._policy.prefer_last_success:
            last = (self._runtime.get("last_success") or {}).get(provider)
            if last:
                # Sort: last_success first, then by priority
                profiles.sort(key=lambda p: (0 if p.id == last else 1, -p.priority))

        return profiles

    def mark_success(self, provider: str, profile_id: str) -> None:
        """
        Mark profile as successful.

        Clears cooldown and updates last_success.

        Args:
            provider: Provider name
            profile_id: Profile identifier
        """
        self._runtime["last_success"][provider] = profile_id
        self.clear_cooldown(profile_id)
        self._save_runtime()

    # -------------------------
    # Error classification (minimal, safe)
    # -------------------------
    @staticmethod
    def classify_error(error_text: str) -> FailReason:
        """
        Classify error into failure reason.

        Args:
            error_text: Error message from LLM provider

        Returns:
            Classified failure reason
        """
        t = (error_text or "").lower()

        if any(
            k in t
            for k in [
                "invalid api key",
                "incorrect api key",
                "unauthorized",
                "forbidden",
                "401",
                "403",
            ]
        ):
            return "auth"
        if any(k in t for k in ["rate limit", "too many requests", "429"]):
            return "rate_limit"
        if any(k in t for k in ["timeout", "timed out", "deadline exceeded"]):
            return "timeout"
        if any(
            k in t
            for k in [
                "context length",
                "maximum context",
                "context window",
                "too long",
                "token limit",
            ]
        ):
            return "context_overflow"
        if any(
            k in t
            for k in [
                "model not found",
                "model unavailable",
                "not available",
                "overloaded",
                "503",
            ]
        ):
            return "model_unavailable"
        return "unknown"

    def choose_profile(self, provider: str) -> AuthProfile:
        """
        Choose next available profile for provider.

        Skips profiles in cooldown.

        Args:
            provider: Provider name

        Returns:
            Next available profile

        Raises:
            AuthProfilesError: If all profiles in cooldown
        """
        now = time.time()
        for p in self.get_candidates(provider):
            if self.is_in_cooldown(p.id, now=now):
                continue
            return p
        raise AuthProfilesError(f"all profiles in cooldown for provider: {provider}")

    def failover_next(
        self, provider: str, failed_profile_id: str
    ) -> Optional[AuthProfile]:
        """
        Get next profile after failure.

        Returns next available profile (not in cooldown) after failed profile.

        Args:
            provider: Provider name
            failed_profile_id: ID of profile that just failed

        Returns:
            Next available profile, or None if all exhausted
        """
        now = time.time()
        candidates = self.get_candidates(provider)

        # Locate failed profile index
        idx = next(
            (i for i, p in enumerate(candidates) if p.id == failed_profile_id), -1
        )

        # Try remaining profiles
        for j in range(idx + 1, len(candidates)):
            p = candidates[j]
            if self.is_in_cooldown(p.id, now=now):
                continue
            return p
        return None


# -------------------------
# Convenience wrapper
# -------------------------
T = TypeVar("T")


def select_with_failover(
    store: AuthProfileStore,
    provider: str,
    attempt_fn: Callable[[str], T],
) -> T:
    """
    Execute operation with automatic failover.

    Args:
        store: Auth profile store
        provider: Provider name
        attempt_fn: Function that takes api_key and returns result
                   Should raise exception on failure

    Returns:
        Result from successful attempt

    Raises:
        AuthProfilesError: If all profiles exhausted

    Example:
        >>> def call_openai(api_key: str):
        ...     # openai.chat.completions.create(...)
        ...     pass
        >>> result = select_with_failover(store, "openai", call_openai)
    """
    profile = store.choose_profile(provider)
    last_err: Optional[Exception] = None

    while True:
        try:
            api_key = store.resolve_api_key(profile.api_key_ref)
            result = attempt_fn(api_key)
            store.mark_success(provider, profile.id)
            return result
        except Exception as e:
            last_err = e
            reason = store.classify_error(str(e))
            store.set_cooldown(profile.id, reason=reason)
            nxt = store.failover_next(provider, failed_profile_id=profile.id)
            if not nxt:
                raise AuthProfilesError(
                    f"provider={provider} all profiles failed; last_reason={reason}"
                ) from last_err
            profile = nxt
