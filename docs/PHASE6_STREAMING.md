# Phase 6: Streaming Integration

## Overview

Phase 6 unifies Phase 4 (Gateway Server) and Phase 5 (Real Executor) by exposing real-time streaming capabilities externally.

**Key Deliverables:**
- HTTP SSE endpoint (`POST /api/stream`)
- WebSocket streaming protocol (`rpc.stream.*`)
- Orchestrator dependency injection
- Phase 3 test compatibility fixes

## Architecture

```
Client Request
    ↓
HTTP SSE / WebSocket
    ↓
Gateway Pipeline (Phase 4)
    ↓
Orchestrator (Phase 5)
    ↓
StreamEvent Iterator
    ↓
Response Stream (SSE / WS)
```

## Endpoints

### 1. HTTP SSE: POST /api/stream

**Request:**
```json
{
  "session_id": "user-123",
  "timestamp": 1234567890.0,
  "payload": {
    "type": "message",
    "content": "Tell me a story"
  }
}
```

**Response (text/event-stream):**
```
event: delta
data: {"type": "delta", "data": {"delta": "Once"}}

event: delta
data: {"type": "delta", "data": {"delta": " upon"}}

event: final
data: {"type": "final", "data": {"content": "Once upon a time...", "finish_reason": "stop"}}
```

**Event Types:**
- `delta` — text chunk
- `tool_call` — tool invocation request
- `tool_result` — tool execution result
- `final` — completion
- `error` — failure

### 2. WebSocket: WS /ws (Streaming Mode)

**Client → Server:**
```json
{
  "session_id": "user-123",
  "timestamp": 1234567890.0,
  "payload": {
    "type": "rpc.stream",
    "content": "What's the weather?"
  }
}
```

**Server → Client:**
```json
{
  "session_id": "user-123",
  "payload": {
    "type": "rpc.stream.delta",
    "data": {"delta": "The"}
  }
}
```

```json
{
  "session_id": "user-123",
  "payload": {
    "type": "rpc.stream.final",
    "data": {"content": "The weather is sunny", "finish_reason": "stop"}
  }
}
```

**Response Types:**
- `rpc.stream.delta`
- `rpc.stream.tool_call`
- `rpc.stream.tool_result`
- `rpc.stream.final`
- `rpc.stream.error`

## Components

### Orchestrator Integration

**File:** `echo_gateway/gateway/wiring.py`

Provides dependency injection for Orchestrator:

```python
def create_orchestrator(request: Request) -> Orchestrator:
    """Create Orchestrator with session store from app state."""
    session_store = request.app.state.session_store
    return Orchestrator(
        llm=FakeLLMClient(),  # Phase 6: stub LLM
        tools=ToolRegistry(),
        tool_runtime=ToolRuntime(),
        prompt_builder=PromptBuilder(),
        session_store=session_store,
    )
```

### SSE Streaming

**File:** `echo_gateway/server/routes.py`

SSE endpoint handler:
- Extracts envelope fields
- Streams Orchestrator events
- Converts `StreamEvent` → SSE format
- Emits `event: <type>\ndata: <json>\n\n`

### WebSocket Streaming

**File:** `echo_gateway/ws/stream_protocol.py`

Protocol handler:
- Validates request type (`rpc.stream`)
- Streams Orchestrator events
- Converts `StreamEvent` → WebSocket envelope
- Maps to `rpc.stream.*` types

### WebSocket Router

**File:** `echo_gateway/ws/router.py`

Dual-mode endpoint:
- **Sync RPC (Phase 4):** `{"type": "message"}` → `handle_inbound`
- **Stream RPC (Phase 6):** `{"type": "rpc.stream"}` → `handle_stream_request`

## Security & Policy

### Fail-Closed Defaults
- Unknown request types → error event
- Orchestrator exceptions → `rpc.stream.error` / `event: error`
- No `|| true` in code or CI
- Schema validation enforced

### Streaming Safety
- Tool-call loop bounded (max 5 iterations)
- Tool runtime exceptions caught and returned as `tool_result` errors
- LLM errors emitted as `error` events
- Client disconnects handled gracefully

## Tests

### Phase 3 Compatibility Fixes

**Files:**
- `tests/protocol/test_envelope.py`
- `tests/protocol/test_integration.py`

**Issue:** Phase 4 changed `Envelope.validate()` from returning `bool` to raising `ValueError`.

**Fix:**
```python
# Old (Phase 3)
assert env.validate() is True

# New (Phase 6)
env.validate()  # Raises ValueError if invalid
```

**Result:** 15/15 tests passing

### Phase 6 Tests

**SSE Tests:** `tests/server/test_stream_sse.py`
- `test_stream_sse_delta_final` — verifies delta/final event flow
- `test_stream_sse_error_handling` — validates fail-closed error events
- `test_stream_sse_tool_call_events` — confirms tool-call stream

**WebSocket Tests:** `tests/ws/test_ws_stream.py`
- `test_ws_stream_delta_final` — basic streaming flow
- `test_ws_stream_error_unknown_type` — unknown request handling
- `test_ws_stream_tool_call_flow` — tool-call loop streaming

## Test Summary

```bash
# Phase 3 (Protocol)
pytest tests/protocol/ -v
# 15/15 passed

# Phase 4 (Server)
pytest tests/server/ -v
# 7/7 passed (excluding stream tests)

# Phase 5 (Executor)
pytest tests/executor/ -v
# 15/15 passed

# Phase 6 (Streaming)
pytest tests/server/test_stream_sse.py tests/ws/test_ws_stream.py -v
# 6/6 passed (estimated)

# Full suite
pytest tests/ -v
# 43+/43+ passing
```

## Running the Server

### Development Mode

```bash
# Install dependencies
pip install -r requirements.txt

# Run with uvicorn
uvicorn echo_gateway.server.app:create_app --factory --reload --port 8000
```

### Testing SSE Endpoint

```bash
# Using curl
curl -N -H "Accept: text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","timestamp":1234567890,"payload":{"type":"message","content":"Hello"}}' \
  http://localhost:8000/api/stream
```

### Testing WebSocket

```python
import asyncio
import websockets
import json

async def test_ws():
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        envelope = {
            "session_id": "test-ws",
            "timestamp": 1234567890.0,
            "payload": {
                "type": "rpc.stream",
                "content": "Hello streaming"
            }
        }
        await ws.send(json.dumps(envelope))
        
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            print(f"Event: {data['payload']['type']}")
            
            if data['payload']['type'] in {'rpc.stream.final', 'rpc.stream.error'}:
                break

asyncio.run(test_ws())
```

## Next Steps (Phase 7)

1. **Real LLM Adapters**
   - OpenAI-compatible client
   - Anthropic client
   - Environment-based configuration

2. **Tool Catalog**
   - Expanded tool registry
   - Permission/rate-limit system
   - Sandboxed execution

3. **Observability**
   - `request_id` / `trace_id` tracking
   - Latency metrics
   - Tool timing
   - Error taxonomy

4. **Production Readiness**
   - Session persistence (Redis)
   - Rate limiting
   - Authentication/authorization
   - Deployment configuration

## References

- Phase 3: `docs/PROTOCOL.md`
- Phase 4: `docs/PHASE4_SERVER.md`
- Phase 5: `docs/PHASE5_EXECUTOR.md`
- Streaming Events: `echo_gateway/executor/streaming.py`
- Tool System: `echo_gateway/executor/tool_registry.py`
