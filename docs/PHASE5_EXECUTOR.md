# Echo Gateway Phase 5 — Real Executor (LLM + Tools + Streaming)

## Overview

Phase 5 implements **real executor orchestration**:
- LLM integration (provider-agnostic client protocol)
- Tool execution with sandboxed runtime
- Streaming support (HTTP SSE + WebSocket)
- Tool-call loop (LLM → tool → LLM → final)

---

## Architecture

### Components

#### 1. LLM Client (`echo_gateway/executor/llm_client.py`)
- **Protocol**: `LLMClient` (provider-agnostic)
- **Methods**: `complete` (non-streaming), `stream` (streaming)
- **Phase 5**: `FakeLLMClient` for testing (no external API calls)
- **Future**: OpenAI, Anthropic, or custom adapters

#### 2. Tool System
- **Registry** (`tool_registry.py`): Register, lookup, schema validation
- **Runtime** (`tool_runtime.py`): Execute tools with sandbox boundary
- **Tool Protocol**: `ToolSpec` + `async run` method

#### 3. Orchestrator (`orchestrator.py`)
- **run_message**: Non-streaming execution
- **stream_message**: Streaming execution with delta/tool_call/final events
- **Tool-call loop**: Max iterations (default 5)

#### 4. Streaming (`streaming.py`)
- **StreamEvent**: Unified event type
- **Event types**: delta, tool_call, tool_result, final, error, debug

#### 5. Prompt Builder (`prompt_builder.py`)
- Converts session state to LLM messages
- Phase 5: system + user only
- Future: full conversation history

---

## Request/Response Flow

### Non-Streaming (run_message)

```
1. User message → Orchestrator.run_message()
2. Build messages from session (PromptBuilder)
3. Call LLM.complete(messages, tools)
4. If tool_calls:
   a. Execute tool(s) via ToolRuntime
   b. Append tool result to messages
   c. Loop back to step 3
5. Return final response dict
```

### Streaming (stream_message)

```
1. User message → Orchestrator.stream_message()
2. Build messages from session
3. Call LLM.stream(messages, tools)
4. For each chunk:
   a. If delta → yield StreamEvent(type="delta")
   b. If tool_calls → yield StreamEvent(type="tool_call")
5. If tool_calls:
   a. Execute tool(s)
   b. Yield StreamEvent(type="tool_result")
   c. Loop back to step 3
6. Yield StreamEvent(type="final")
```

---

## Tool-Call Loop State Machine

```
┌────────────────┐
│ User Message   │
└────────┬───────┘
         │
         ▼
┌────────────────┐
│ Build Messages │
└────────┬───────┘
         │
         ▼
    ┌────────┐
    │LLM Call│
    └───┬────┘
        │
        ├──────► finish_reason="stop" ──► Final Response
        │
        └──────► finish_reason="tool_calls"
                      │
                      ▼
                ┌──────────────┐
                │ Execute Tools│
                └──────┬───────┘
                       │
                       ├──► Tool Error ──► Error Response
                       │
                       └──► Tool Success
                            │
                            └─────► Loop (max 5 iterations)
```

---

## Safety Policy

### Fail-Closed Defaults
- Unknown tool → **BLOCK** (ValueError)
- Invalid tool arguments → **BLOCK** (schema validation error)
- Tool runtime exception → **ERROR** (returned as error dict)
- Max iterations exceeded → **ERROR**

### BCDSI Stages
- **inbound**: Gateway pipeline (Phase 4)
- **tool**: Stricter checks before tool execution (Phase 4)
- Phase 5: Executor honors fail-closed policy

### No `|| true`
- Tool errors are not suppressed
- LLM errors are not suppressed
- Orchestrator exceptions → StreamEvent(type="error")

---

## Streaming Event Types

### delta
```json
{
  "type": "delta",
  "data": {"delta": "text chunk"},
  "error": null
}
```

### tool_call
```json
{
  "type": "tool_call",
  "data": {
    "tool_calls": [
      {
        "id": "call_123",
        "type": "function",
        "function": {"name": "tool_name", "arguments": "{...}"}
      }
    ]
  },
  "error": null
}
```

### tool_result
```json
{
  "type": "tool_result",
  "data": {
    "tool_name": "tool_name",
    "result": {"result": "...", "error": null}
  },
  "error": null
}
```

### final
```json
{
  "type": "final",
  "data": {
    "content": "final response text",
    "finish_reason": "stop",
    "iterations": 2
  },
  "error": null
}
```

### error
```json
{
  "type": "error",
  "data": {},
  "error": "error message"
}
```

---

## Test Summary

### Unit Tests (15/15 passing)
- **tool_registry**: register, lookup, duplicate, to_llm_tools
- **tool_runtime**: execute, validation, error handling
- **orchestrator_message**: no tools, unknown tool, max iterations
- **orchestrator_stream**: delta, tool_call, tool_result, final, error

### Integration Tests (Future)
- HTTP SSE: `/api/stream`
- WebSocket stream: `rpc.stream`

---

## Usage Examples

### Non-Streaming

```python
from echo_gateway.executor import (
    Orchestrator,
    FakeLLMClient,
    ToolRegistry,
    ToolRuntime,
    PromptBuilder,
)
from echo_gateway.session import SessionStore

llm = FakeLLMClient(mode="echo")
registry = ToolRegistry()
runtime = ToolRuntime()
builder = PromptBuilder()
store = SessionStore()

orch = Orchestrator(
    llm=llm,
    tool_registry=registry,
    tool_runtime=runtime,
    prompt_builder=builder,
    session_store=store,
)

result = await orch.run_message(
    session_id="test-session",
    content="Hello",
    metadata={}
)
# {"status": "success", "data": {"content": "Echo: Hello", ...}, "error": None}
```

### Streaming

```python
async for event in orch.stream_message(
    session_id="test-session",
    content="Hello",
    metadata={}
):
    if event.type == "delta":
        print(event.data["delta"], end="", flush=True)
    elif event.type == "final":
        print("\nDone:", event.data)
    elif event.type == "error":
        print("\nError:", event.error)
```

---

## Tool Definition Example

```python
from echo_gateway.executor import ToolSpec

class CalculatorTool:
    spec = ToolSpec(
        name="calculator",
        description="Perform arithmetic operations",
        input_schema={
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add", "subtract"]},
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "required": ["operation", "a", "b"]
        }
    )

    async def run(self, *, arguments, session_id):
        op = arguments["operation"]
        a = arguments["a"]
        b = arguments["b"]

        if op == "add":
            result = a + b
        elif op == "subtract":
            result = a - b
        else:
            return {"result": None, "error": "Unknown operation"}

        return {"result": result, "error": None}

# Register
registry.register(CalculatorTool())
```

---

## Future Enhancements (Phase 6+)

### Real LLM Clients
- OpenAI adapter (openai_compat.py)
- Anthropic adapter
- Local model adapters (Ollama, vLLM)

### Session Memory
- Full conversation history
- Tool execution log
- Context window management

### Advanced Tool Features
- Tool chaining
- Tool approval workflows
- Tool rate limiting

### Streaming Optimizations
- Server-sent events (SSE) endpoint
- WebSocket stream protocol
- Backpressure handling

---

## File Tree

```
echo_gateway/
  executor/
    __init__.py
    interface.py              # Executor protocol (Phase 4)
    local.py                  # LocalExecutor stub (Phase 4)
    llm_client.py             # LLMClient protocol
    fake_llm_client.py        # Fake LLM for testing
    prompt_builder.py         # Session → messages
    tool_registry.py          # Tool registration + lookup
    tool_runtime.py           # Tool execution boundary
    orchestrator.py           # Tool-call loop + streaming
    streaming.py              # StreamEvent standard
tests/
  executor/
    test_tool_registry.py
    test_tool_runtime.py
    test_orchestrator_message.py
    test_orchestrator_stream.py
docs/
  PHASE5_EXECUTOR.md        # (this file)
```

---

## Summary

Phase 5 delivers:
- ✅ Real executor orchestration (LLM + tools)
- ✅ Tool-call loop with max iterations
- ✅ Streaming support (delta/tool_call/final)
- ✅ Fail-closed safety policy
- ✅ Provider-agnostic LLM client protocol
- ✅ 15/15 unit tests passing
- ✅ No external API calls (FakeLLMClient for testing)

**Next**: Phase 6 — Real LLM adapters + HTTP SSE/WS stream endpoints
