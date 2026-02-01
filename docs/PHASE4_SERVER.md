# Echo Gateway Phase 4 — Gateway Server + WebSocket

## Overview

Phase 4 implements the **gateway server** that orchestrates:
- HTTP routes (`/health`, `/api/message`)
- WebSocket RPC endpoint (`/ws`)
- Session management (in-memory store + TTL)
- Gateway pipeline (envelope → validate → parse → safety → execute)
- Executor interface + stub implementation

---

## Architecture

### Components

#### 1. Server (`echo_gateway/server/`)
- **app.py**: FastAPI application factory + lifecycle
- **routes.py**: HTTP routes
- **deps.py**: Dependency injection (session store, executor, safety check)

#### 2. WebSocket (`echo_gateway/ws/`)
- **router.py**: `/ws` endpoint for bi-directional JSON-RPC

#### 3. Session (`echo_gateway/session/`)
- **store.py**: In-memory session store with TTL
- **model.py**: SessionState dataclass (created_at, last_seen, data)

#### 4. Executor (`echo_gateway/executor/`)
- **interface.py**: Executor protocol (handle_message, handle_tool_call, handle_status)
- **local.py**: LocalExecutor stub (echoes requests back)

#### 5. Gateway (`echo_gateway/gateway/`)
- **pipeline.py**: `handle_inbound` orchestration
- **safety.py**: Stub safety check (Phase 4 always returns ALLOW)

---

## Endpoints

### HTTP

#### `GET /health`
```json
{
  "ok": true,
  "service": "echo_gateway",
  "phase": 4
}
```

#### `POST /api/message`
Request:
```json
{
  "session_id": "session-123",
  "timestamp": 1706789123.456,
  "payload": {
    "type": "message",
    "content": "Hello gateway",
    "metadata": {}
  }
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "echo": "Hello gateway",
    "session_id": "session-123",
    "metadata": {}
  },
  "error": null
}
```

### WebSocket

#### `WS /ws`
Bi-directional JSON-RPC:
```json
// Client → Server
{
  "session_id": "ws-session",
  "timestamp": 1706789123.456,
  "payload": {
    "type": "tool_call",
    "tool_name": "calculator",
    "arguments": {"op": "add", "a": 1, "b": 2}
  }
}

// Server → Client
{
  "status": "success",
  "data": {
    "tool_name": "calculator",
    "arguments": {"op": "add", "a": 1, "b": 2},
    "session_id": "ws-session",
    "note": "Phase 4 stub — no real tool execution"
  },
  "error": null
}
```

---

## Session Management

### SessionStore
- **TTL**: Default 3600 seconds (1 hour)
- **get_or_create**: Fetch or create session, update last_seen
- **sweep**: Remove idle sessions exceeding TTL

### SessionState
```python
@dataclass
class SessionState:
    session_id: str
    created_at: float  # epoch seconds
    last_seen: float   # epoch seconds
    data: Dict[str, Any]  # arbitrary session data
```

---

## Gateway Pipeline

### Flow
1. **Parse envelope**: Extract session_id, timestamp, payload
2. **Sanitize**: Clean session_id, validate timestamp recency
3. **Sanitize payload**: Remove unsafe keys, check size/depth
4. **Parse request**: Dispatch to MessageRequest | ToolCallRequest | StatusRequest
5. **Safety check (inbound)**: BCDSI gate (Phase 4 stub)
6. **Execute**: Call executor (handle_message / handle_tool_call / handle_status)
7. **Safety check (tool stage)**: Stricter check for tool calls
8. **Response**: Return `{"status", "data", "error"}`

### Error Handling
- Fail-closed: unknown request types → error
- Invalid envelope → error
- Safety BLOCK → error
- Executor exceptions → error

---

## Executor Interface

```python
class Executor(Protocol):
    async def handle_message(
        self, session_id: str, content: str, metadata: Dict[str, Any]
    ) -> ExecResult: ...

    async def handle_tool_call(
        self, session_id: str, tool_name: str, arguments: Dict[str, Any]
    ) -> ExecResult: ...

    async def handle_status(
        self, session_id: str, status: str
    ) -> ExecResult: ...
```

### LocalExecutor (Phase 4)
Stub implementation that echoes requests back.  
Future phases will integrate real LLM/tool execution.

---

## Safety Checks

### stub_safety_check (Phase 4)
Always returns `SafetyDecision(level="ALLOW")`.

Future phases:
- Integrate BCDSI
- Stage-specific policies (inbound vs tool)
- Content moderation

---

## Testing

### Test Coverage
- **test_health.py**: Health endpoint
- **test_http_message.py**: POST /api/message (happy path + errors)
- **test_ws_rpc.py**: WebSocket /ws (happy path + multi-message + errors)
- **test_session_ttl.py**: Session TTL + sweep
- **test_pipeline.py**: Gateway pipeline (validate → parse → safety → execute)

### Running Tests
```bash
pytest tests/server -v
```

---

## Running the Server

```bash
uvicorn echo_gateway.server.app:create_app --factory --reload --host 0.0.0.0 --port 8000
```

### Quick Test
```bash
# Health check
curl http://localhost:8000/health

# Message endpoint
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test",
    "timestamp": 1706789123.456,
    "payload": {
      "type": "message",
      "content": "Hello",
      "metadata": {}
    }
  }'
```

### WebSocket Test (Python)
```python
import asyncio
import time
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as ws:
        envelope = {
            "session_id": "ws-test",
            "timestamp": time.time(),
            "payload": {
                "type": "message",
                "content": "Hello WS",
                "metadata": {}
            }
        }
        await ws.send(json.dumps(envelope))
        response = await ws.recv()
        print(json.loads(response))

asyncio.run(test_ws())
```

---

## CI Policy

- **No `|| true`**: Failures are not suppressed
- **Fail-closed**: Unknown types/errors → error response
- **Test-first**: All routes + pipeline paths tested

---

## Future Phases

### Phase 5: Real Executor Integration
- LLM backend (OpenAI, Anthropic, etc.)
- Tool execution framework
- Streaming support

### Phase 6: Persistent Sessions
- Redis/DB backend
- Session migration
- Multi-instance support

### Phase 7: BCDSI Integration
- Real safety checks
- Content moderation
- Rate limiting

---

## Dependencies

### Added in Phase 4
```txt
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
websockets>=12.0
```

### Testing
```txt
pytest-asyncio>=0.23.0
httpx  # for TestClient
```

---

## File Tree

```
echo_gateway/
  server/
    __init__.py
    app.py              # FastAPI app factory
    routes.py           # HTTP routes
    deps.py             # dependency injection
  ws/
    __init__.py
    router.py           # WebSocket endpoint
  session/
    __init__.py
    store.py            # SessionStore
    model.py            # SessionState
  executor/
    __init__.py
    interface.py        # Executor protocol
    local.py            # LocalExecutor stub
  gateway/
    __init__.py
    pipeline.py         # handle_inbound
    safety.py           # stub safety check
tests/
  server/
    test_health.py
    test_http_message.py
    test_ws_rpc.py
    test_session_ttl.py
    test_pipeline.py
docs/
  PHASE4_SERVER.md    # (this file)
```

---

## Summary

Phase 4 delivers:
- ✅ FastAPI server with HTTP + WebSocket
- ✅ Session management (in-memory + TTL)
- ✅ Gateway pipeline (envelope → execute → response)
- ✅ Executor interface + stub implementation
- ✅ Comprehensive tests (5 test files, 20+ test cases)
- ✅ Fail-closed error handling
- ✅ No `|| true` policy

**Next**: Phase 5 — Real executor integration (LLM + tools)
