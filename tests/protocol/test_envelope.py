"""
Envelope 테스트

Message envelope의 생성, 검증, 직렬화를 테스트합니다.
"""

import pytest
from datetime import datetime
from echo_gateway.protocol.envelope import Envelope


def test_envelope_creation():
    """Envelope 생성 테스트"""
    env = Envelope(
        session_id="test-123",
        timestamp=datetime.now().timestamp(),
        payload={"type": "message", "text": "hello"}
    )
    
    assert env.session_id == "test-123"
    assert env.payload["type"] == "message"
    assert env.payload["text"] == "hello"


def test_envelope_validation():
    """Envelope 검증 테스트"""
    # Valid envelope
    env = Envelope(
        session_id="test-123",
        timestamp=datetime.now().timestamp(),
        payload={"type": "message"}
    )
    assert env.validate() == True
    
    # Invalid: empty session_id
    env_no_session = Envelope(
        session_id="",
        timestamp=datetime.now().timestamp(),
        payload={"type": "message"}
    )
    assert env_no_session.validate() == False
    
    # Invalid: old timestamp (6 minutes ago)
    env_old = Envelope(
        session_id="test-123",
        timestamp=datetime.now().timestamp() - 400,
        payload={"type": "message"}
    )
    assert env_old.validate() == False
    
    # Invalid: negative timestamp
    env_negative = Envelope(
        session_id="test-123",
        timestamp=-1,
        payload={"type": "message"}
    )
    assert env_negative.validate() == False


def test_envelope_serialization():
    """Envelope 직렬화 테스트"""
    env = Envelope(
        session_id="test-123",
        timestamp=datetime.now().timestamp(),
        payload={"type": "message", "data": {"key": "value"}}
    )
    
    # to_dict
    data = env.to_dict()
    assert data["session_id"] == "test-123"
    assert data["payload"]["type"] == "message"
    assert data["payload"]["data"]["key"] == "value"
    
    # from_dict
    env2 = Envelope.from_dict(data)
    assert env2.session_id == env.session_id
    assert env2.timestamp == env.timestamp
    assert env2.payload == env.payload


def test_envelope_roundtrip():
    """Envelope 왕복 변환 테스트"""
    original = Envelope(
        session_id="roundtrip-test",
        timestamp=datetime.now().timestamp(),
        payload={"complex": {"nested": {"data": [1, 2, 3]}}},
        signature="test-signature"
    )
    
    # Serialize
    data = original.to_dict()
    
    # Deserialize
    restored = Envelope.from_dict(data)
    
    # Verify
    assert restored.session_id == original.session_id
    assert restored.timestamp == original.timestamp
    assert restored.payload == original.payload
    assert restored.signature == original.signature


def test_envelope_with_signature():
    """Signature 포함 Envelope 테스트"""
    env = Envelope(
        session_id="signed-123",
        timestamp=datetime.now().timestamp(),
        payload={"type": "secure_message"},
        signature="sha256:abc123"
    )
    
    assert env.signature == "sha256:abc123"
    assert env.validate() == True
    
    # Signature in serialization
    data = env.to_dict()
    assert data["signature"] == "sha256:abc123"
    
    # Restore with signature
    restored = Envelope.from_dict(data)
    assert restored.signature == "sha256:abc123"


def test_envelope_without_signature():
    """Signature 없는 Envelope 테스트"""
    env = Envelope(
        session_id="unsigned-123",
        timestamp=datetime.now().timestamp(),
        payload={"type": "message"}
    )
    
    assert env.signature is None
    
    # Serialization without signature
    data = env.to_dict()
    assert data["signature"] is None
    
    # Restore without signature
    restored = Envelope.from_dict(data)
    assert restored.signature is None
