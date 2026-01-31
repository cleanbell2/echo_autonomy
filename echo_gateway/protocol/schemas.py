# echo_gateway/protocol/schemas.py
from __future__ import annotations

from typing import Any, Dict, Literal, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

# -----------------------------
# Base
# -----------------------------
class _BaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)


# -----------------------------
# Request Schemas
# -----------------------------
class MessageRequest(_BaseSchema):
    type: Literal["message"] = "message"
    content: str = Field(..., min_length=1, max_length=100_000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolCallRequest(_BaseSchema):
    type: Literal["tool_call"] = "tool_call"
    tool_name: str = Field(..., min_length=1, max_length=200)
    arguments: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StatusRequest(_BaseSchema):
    type: Literal["status"] = "status"
    status: Literal["ping", "ready", "busy", "shutdown"]
    metadata: Dict[str, Any] = Field(default_factory=dict)


RequestSchema = Union[MessageRequest, ToolCallRequest, StatusRequest]


# -----------------------------
# Response Schemas
# -----------------------------
class MessageResponse(_BaseSchema):
    status: Literal["success", "error", "pending"]
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    @model_validator(mode="after")
    def _error_rules(self) -> "MessageResponse":
        # error 상태면 error 메시지는 있어야 한다.
        if self.status == "error" and (self.error is None or self.error.strip() == ""):
            raise ValueError("error status requires non-empty 'error'")
        # success/pending면 error는 없어야 한다(헷갈림 방지)
        if self.status in ("success", "pending") and self.error is not None:
            raise ValueError("non-error status must not include 'error'")
        return self


# -----------------------------
# Helpers
# -----------------------------
def parse_request(payload: Dict[str, Any]) -> RequestSchema:
    """
    Dict payload를 type 디스패치로 안전하게 파싱.
    extra=forbid 설정이라 미정 필드는 즉시 거부.
    """
    t = payload.get("type")
    if t == "message":
        return MessageRequest.model_validate(payload)
    if t == "tool_call":
        return ToolCallRequest.model_validate(payload)
    if t == "status":
        return StatusRequest.model_validate(payload)
    raise ValueError(f"unknown request type: {t!r}")
