"""
Message Envelope - Protocol Layer Core

모든 요청/응답의 공통 프레임:
- session_id: 세션 식별자
- timestamp: Unix timestamp (ms)
- payload: 실제 메시지 (Pydantic model)
- signature: 무결성 검증 (선택)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
from datetime import datetime


@dataclass
class Envelope:
    """Message envelope wrapper"""
    session_id: str
    timestamp: float
    payload: Dict[str, Any]
    signature: str | None = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "signature": self.signature
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Envelope:
        """Deserialize from dict"""
        return cls(
            session_id=data["session_id"],
            timestamp=data["timestamp"],
            payload=data["payload"],
            signature=data.get("signature")
        )
    
    def validate(self) -> bool:
        """Validate envelope integrity"""
        # Basic validation
        if not self.session_id:
            return False
        if self.timestamp <= 0:
            return False
        if not isinstance(self.payload, dict):
            return False
        
        # Timestamp recency check (within 5 minutes)
        now = datetime.now().timestamp()
        if abs(now - self.timestamp) > 300:
            return False
        
        return True
