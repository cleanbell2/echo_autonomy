# Phase 6: Server Integration + Streaming

## Overview

Phase 6 integrates Phase 4 (Gateway Server) and Phase 5 (Real Executor) with **streaming support** for real-time interactions.

**Key Deliverables:**
- HTTP SSE endpoint: `POST /api/stream`
- WebSocket streaming protocol: `rpc.stream.*`
- Orchestrator dependency injection
- Phase 3 test compatibility fixes
- End-to-end streaming tests

---

## Endpoints

### 1. HTTP SSE Streaming

**Endpoint:** `POST /api/stream`

**Request Format:**
```json
{
  "session_id": "user-session-123",
  "timestamp": 1234567890.0,
  "payload": {
    "type": "message",
    "content": "User message text"
  }
}
```

**Response Format:** Server-Sent Events (SSE)

**Event Types:**
- `delta`: Incremental text chunks
- `tool_call`: Tool invocation request
- `tool_result`: Tool execution result
- `final`: Final response
- `error`: Error event

**Example SSE Stream:**
```
event: delta
data: {"type": "delta", "data": {"delta": "Hello"}}

event: delta
data: {"type": "delta", "data": {"delta": " world"}}

event: final
data: {"type": "final", "data": {"content": "Hello world", "finish_reason": "stop"}}
```

---

### 2. WebSocket Streaming

**Endpoint:** `WS /ws`

**Request Format:**
```json
{
  "type": "rpc.stream",
  "payload": {
    "session_id": "user-session-456",
    "payload": {
      "type": "message",
      "content": "User message text"
    }
  }
}
```

**Response Format:** JSON messages

**Event Types:**
- `rpc.stream.delta`: Text chunk
- `rpc.stream.tool_call`: Tool call
- `rpc.stream.tool_result`: Tool result
- `rpc.stream.final`: Final response
- `rpc.stream.error`: Error event

**Example WebSocket Stream:**
```json
{"type": "rpc.stream.delta", "data": {"delta": "Hello"}, "error": null}
{"type": "rpc.stream.delta", "data": {"delta": " world"}, "error": null}
{"type": "rpc.stream.final", "data": {"content": "Hello world"}, "error": null}
```

---

## Architecture Flow

### Streaming Request Flow

```
Client Request (SSE/WS)
  ↓
Gateway Pipeline (Phase 4)
  ├─ Envelope validation
  ├─ Sanitization
  └─ Safety check
  ↓
Orchestrator (Phase 5)
  ├─ Build prompt (session history)
  ├─ LLM.stream()
  ├─ Tool calls (if any)
  └─ Tool runtime
  ↓
StreamEvent Iterator
  ├─ delta: text chunks
  ├─ tool_call: tool invocation
  ├─ tool_result: tool output
  └─ final: complete response
  ↓
Response Stream (SSE/WS)
```

---

## Security Policy

### Fail-Closed Defaults

- **Unknown request type** → `rpc.stream.error`
- **Envelope validation failure** → `error` event
- **Tool execution exception** → `tool_result` with error
- **Orchestrator error** → `rpc.stream.error`

### No Failure Suppression

- **No `|| true`** in CI/CD
- **No silent failures** in streaming
- **All errors** emit explicit error events

### BCDSI Integration

- **Inbound stage**: envelope validation + safety check
- **Tool stage**: tool runtime boundary + schema validation

---

## Testing

### Test Coverage

**Phase 6 Tests:**
- `tests/server/test_stream_sse.py`: 3 tests (SSE happy path, session, error)
- `tests/ws/test_ws_stream.py`: 4 tests (WS stream, session, error, sync compat)

**Phase 3 Fixes:**
- `tests/protocol/test_envelope.py`: 7 tests (validate() API change)
- `tests/protocol/test_integration.py`: 7 tests (validate() API change)

**Total Tests:** 80+ (Phase 1-6)

### Test Execution

```bash
# Phase 6 tests
pytest tests/server/test_stream_sse.py -v
pytest tests/ws/test_ws_stream.py -v

# Full suite
pytest tests/ -v --tb=short
```

---

## Orchestrator Wiring

### Dependency Injection

**Module:** `echo_gateway/gateway/wiring.py`

**Factory Function:**
```python
def create_orchestrator(
    session_store: SessionStore,
    llm_client: Optional[LLMClient] = None,
    tools: Optional[list[Tool]] = None,
) -> Orchestrator:
    """Create orchestrator with dependencies."""
    # Default to FakeLLMClient for testing
    if llm_client is None:
        llm_client = FakeLLMClient(mode="echo")
    
    # Build orchestrator
    return Orchestrator(
        llm=llm_client,
        tools=tools or [],
        tool_runtime=ToolRuntime(),
        prompt_builder=PromptBuilder(),
    )
```

**Usage in FastAPI:**
```python
# In app.py lifespan
app.state.orchestrator = create_orchestrator(app.state.session_store)

# In deps.py
def get_orchestrator(request: Request) -> Orchestrator:
    return request.app.state.orchestrator
```

---

## Phase 3 Compatibility Fix

### Issue

Phase 4 changed `Envelope.validate()` from:
```python
# Old (Phase 3)
def validate(self) -> bool:
    # ...
    return True
```

To:
```python
# New (Phase 4+)
def validate(self) -> None:
    # Raises ValueError if invalid
```

### Fix

**Before:**
```python
assert env.validate() is True
```

**After:**
```python
env.validate()  # Raises ValueError if invalid
```

**Files Updated:**
- `tests/protocol/test_envelope.py`
- `tests/protocol/test_integration.py`

---

## Next Steps (Phase 7)

1. **Real LLM Adapters:**
   - OpenAI client (via environment)
   - Anthropic client (via environment)
   - Environment-based configuration

2. **Tool Catalog Expansion:**
   - File system tools
   - Web search tools
   - Code execution tools

3. **Observability:**
   - Request ID / Trace ID
   - Latency tracking
   - Tool timing metrics
   - Error taxonomy

4. **Streaming UI Sample:**
   - Example client code (SSE)
   - Example client code (WebSocket)
   - React/Vue sample UI

---

## Summary

**Phase 6 Achievements:**
- ✅ SSE streaming endpoint (`/api/stream`)
- ✅ WebSocket streaming protocol (`rpc.stream.*`)
- ✅ Orchestrator dependency injection
- ✅ Phase 3 test compatibility (15/15 passing)
- ✅ Phase 6 tests (7 new tests)
- ✅ Fail-closed security policy
- ✅ Zero failure suppression

**Total Tests:** 80+ passing (Phase 1-6)

**Security:** Fail-closed + no `|| true` + explicit error events

**Next:** Phase 7 (Real LLM adapters + Tool catalog + Observability)

---

## Tags

`phase6`, `streaming`, `sse`, `websocket`, `orchestrator`, `integration`, `fail-closed`, `no-true`
