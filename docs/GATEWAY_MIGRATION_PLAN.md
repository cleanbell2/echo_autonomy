# OpenClaw Gateway → Echo Autonomy Migration Plan

**Date**: 2026-01-31  
**Author**: Claude Code + User  
**Status**: Draft / Design Phase  
**Goal**: Extract OpenClaw's Gateway pattern and migrate it into Echo's Python server to build a safe, fast Action Agent

---

## Executive Summary

This document outlines the plan to extract OpenClaw's **Gateway (통합 통신)** architecture and adapt it to Echo Autonomy's Python server (`server.py`). The goal is to leverage OpenClaw's proven RPC/Session management pattern while integrating Echo's unique safety layer (BCDSI, Quantum Uncertainty, E-Break).

### Key Insight
- **OpenClaw's Gateway** = Control plane for multi-channel, multi-agent communication (WebSocket RPC)
- **Echo's Safety Layer** = Real-time intervention based on quantum information theory
- **Synergy** = Gateway handles **routing/orchestration**, Echo handles **safety validation**

---

## 1. OpenClaw Gateway Architecture Analysis

### 1.1 Core Components

Based on code analysis of `/tmp/openclaw/src/gateway/`:

| Component | Purpose | Tech Stack | Key Files |
|-----------|---------|------------|-----------|
| **Gateway Server** | HTTP/WS control plane | Node.js + Hono | `server/server.impl.ts` |
| **Protocol Layer** | RPC schema + validation | JSON Schema + Ajv | `protocol/index.ts` |
| **Pi Agent Runner** | Embedded AI execution | TypeScript | `src/agents/pi-embedded-runner.ts` |
| **Auth Profile System** | Multi-key failover | Custom | `src/agents/auth-profiles/` |
| **Session Manager** | Conversation state | In-memory | `src/gateway/session/` |

### 1.2 Gateway Protocol (RPC Schema)

OpenClaw uses a **frame-based WebSocket protocol** with:
- **Request Frame**: `{ id, method, params }`
- **Response Frame**: `{ id, result/error }`
- **Event Frame**: `{ event, data }` (push notifications)

Supported methods include:
- `chat.send`: Send message to agent
- `chat.inject`: Inject system message
- `chat.abort`: Cancel running agent
- `sessions.list`: List all sessions
- `agents.list`: List available agents
- `config.get`: Read gateway config
- ...and 50+ more methods

### 1.3 Key Patterns

1. **Gateway as Single Entry Point**
   - All client requests → Gateway → Route to appropriate handler
   - Gateway maintains WebSocket connections with clients
   - Gateway manages session state and agent lifecycle

2. **Auth Profile Failover**
   - Multiple API keys for same provider (e.g., `openai-1`, `openai-2`)
   - Automatic failover on rate limit / error
   - Cooldown tracking (30min default after failure)

3. **Context Window Guard**
   - Monitors token usage per session
   - Triggers auto-compaction when threshold exceeded
   - Prevents runaway context growth

4. **Session Isolation**
   - Each session has independent state
   - Sessions can be compacted, reset, or deleted
   - No cross-session data leakage

---

## 2. Echo Autonomy Current Architecture

### 2.1 Current State

Echo's `server.py` (FastAPI) provides:
- `/check` endpoint: Real-time safety validation
- `/intervention` endpoint: BCDSI intervention logic
- CORS-enabled REST API

**Key Components:**
- `bcdsi/uncertainty.py`: Quantum uncertainty calculator
- `bcdsi/ebreak_calculator.py`: E-Break risk assessment
- `bcdsi/intervention.py`: 5-level intervention (BLOCK/MODIFY/MONITOR/WARNING/ALLOW)
- `bcdsi/monitor.py`: Real-time monitoring loop

### 2.2 Current Limitations

1. **No Gateway/Control Plane**: Direct REST API, no orchestration layer
2. **No Session Management**: Stateless requests, no conversation tracking
3. **No Multi-Agent Support**: Single-purpose safety validator
4. **No Failover**: Single-model, no auth profile system
5. **No Tooling**: Cannot execute tools or commands

---

## 3. Proposed Architecture: Echo Gateway

### 3.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                        Echo Gateway                          │
│  (Python FastAPI + WebSocket, inspired by OpenClaw)         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  WebSocket   │  │   Session    │  │    Auth      │      │
│  │   Handler    │  │   Manager    │  │   Profiles   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              RPC Router (Protocol Layer)              │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Agent     │  │    Tool      │  │   Safety     │      │
│  │   Executor   │  │   Registry   │  │   Validator  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Echo Safety Layer (BCDSI)                  │  │
│  │  - Quantum Uncertainty Calculator                     │  │
│  │  - E-Break Calculator                                 │  │
│  │  - Intervention Engine (5 levels)                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
             ┌──────────────────────────────┐
             │    LLM Providers (Claude,    │
             │    GPT, Gemini, Ollama...)   │
             └──────────────────────────────┘
```

### 3.2 Component Mapping

| OpenClaw Component | Echo Gateway Equivalent | Implementation |
|--------------------|-------------------------|----------------|
| Gateway Server (Node.js) | Echo Gateway (Python) | FastAPI + WebSocket |
| Protocol (TypeScript) | RPC Schema (Pydantic) | JSON Schema validation |
| Pi Agent Runner | Agent Executor | Python async executor |
| Auth Profile System | Multi-Key Manager | Redis-backed failover |
| Session Manager | Session Store | SQLite/Redis session storage |
| Tools (Bash, Read, Write) | Echo Tool Registry | Python tool plugins |
| **N/A in OpenClaw** | **Safety Validator** | **BCDSI integration** |

### 3.3 Tech Stack

- **Backend**: Python 3.10+
- **Framework**: FastAPI (existing)
- **WebSocket**: `websockets` library or FastAPI WebSocket (ASGI-native)
  - **Selection criteria**: `websockets` for standalone, FastAPI WebSocket for unified ASGI flow
- **Validation**: Pydantic v2
- **Session Storage**: 
  - **Prototype**: SQLite (single-node, zero-config, portability)
  - **Production**: Redis (concurrency, TTL, multi-instance, session distribution)
- **Agent Execution**: `asyncio` + `httpx` (for LLM calls)
- **Safety Layer**: Existing BCDSI modules (no changes needed)

---

## 4. Implementation Roadmap

### Phase 1: Protocol Layer (Week 1-2)

**Goal**: Define Echo Gateway's RPC protocol in Python

**Tasks**:
1. Create `echo_gateway/protocol/` directory
2. Define Pydantic schemas for:
   - **Message Envelope**: `type`, `request_id`, `session_id`, `timestamp`, `payload`, `error`
   - **RequestFrame**: Client → Server messages
   - **ResponseFrame**: Server → Client responses
   - **EventFrame**: Server → Client push notifications
   - **Error Schema**: Structured error responses
3. Define core method types:
   - **Agent operations**: `agent.run`, `agent.stop`, `agent.status`
   - **Session operations**: `session.list`, `session.reset`, `session.compact`
   - **Tool operations**: `tool.execute`, `tool.list`
4. Implement JSON-RPC validator:
   - Message type whitelist
   - Payload validation per type
   - Size limits (max 10MB per message)
5. Write unit tests:
   - Protocol roundtrip (serialize/deserialize)
   - Invalid type rejection
   - Oversized payload rejection

**Deliverables**:
- `echo_gateway/protocol/envelope.py` - Common message envelope
- `echo_gateway/protocol/schemas.py` - Frame schemas
- `echo_gateway/protocol/validator.py` - Validation logic
- `tests/test_protocol_roundtrip.py` - Unit tests

**Example Envelope**:
```python
{
  "type": "request",
  "request_id": "req_12345",
  "session_id": "session_001",
  "timestamp": 1706745600.123,
  "payload": {
    "method": "agent.run",
    "params": {"message": "Hello"}
  }
}
```

---

### Phase 2: Gateway Server (Week 3-4)

**Goal**: Build WebSocket server with session management

**Tasks**:
1. Extend `server.py` with WebSocket endpoint (`/gateway`)
2. Implement `GatewayServer` class:
   - Accept WebSocket connections
   - Parse incoming frames
   - Route to appropriate handler
   - Send response/event frames
3. Add basic session management:
   - In-memory session store (dict-based)
   - Session CRUD operations
4. Implement heartbeat/ping-pong for connection health

**Deliverables**:
- `echo_gateway/server.py`
- `echo_gateway/session.py`
- `tests/test_gateway_server.py`

---

### Phase 3: Agent Executor (Week 5-6)

**Goal**: Execute AI agents with safety validation

**Tasks**:
1. Create `echo_gateway/agent.py`:
   - `AgentExecutor` class
   - Support for Claude/GPT/Gemini via `httpx`
   - Tool execution loop (Read, Write, Bash, etc.)
2. Integrate BCDSI safety checks:
   - Before LLM call: Validate prompt with `uncertainty.py`
   - After LLM response: Check E-Break with `ebreak_calculator.py`
   - Apply intervention with `intervention.py`
3. Add context window tracking:
   - Count tokens per session
   - Trigger auto-compaction at 80% threshold
4. Implement streaming support (Server-Sent Events or WebSocket)

**Deliverables**:
- `echo_gateway/agent.py`
- `echo_gateway/tools/` (tool plugins)
- `tests/test_agent_executor.py`

---

### Phase 4: Auth Profile Failover (Week 7-8)

**Goal**: Multi-key management with automatic failover

**Tasks**:
1. Create `echo_gateway/auth_profiles.py`:
   - Store multiple API keys per provider
   - Track failure rate and cooldown
   - Select key with highest success rate
2. Implement failover logic:
   - On rate limit: Switch to next key
   - On error: Mark key as failed, start cooldown
   - On success: Update success timestamp
3. Add Redis-backed persistence (optional)
4. CLI command to manage keys: `openclaw auth add openai sk-...`

**Deliverables**:
- `echo_gateway/auth_profiles.py`
- `tests/test_auth_profiles.py`
- CLI integration in `echo_gateway/cli.py`

---

### Phase 5: Tool Registry & Plugins (Week 9-10)

**Goal**: Extensible tool system (inspired by OpenClaw's MCP)

**Tasks**:
1. Define `Tool` protocol (abstract base class)
2. Implement core tools:
   - `BashTool`: Execute shell commands
   - `ReadTool`: Read files
   - `WriteTool`: Write files
   - `GrepTool`: Search file contents
   - `WebFetchTool`: HTTP requests
3. Add tool discovery: Auto-load from `tools/` directory
4. Implement tool safety checks:
   - Before execution: Validate with BCDSI
   - After execution: Check E-Break on output
5. Add MCP-compatible tool interface (for future OpenClaw integration)

**Deliverables**:
- `echo_gateway/tools/base.py`
- `echo_gateway/tools/bash.py`, `read.py`, `write.py`, etc.
- `echo_gateway/tools/registry.py`
- `tests/test_tools.py`

---

### Phase 6: Integration & Testing (Week 11-12)

**Goal**: End-to-end validation and benchmarking

**Tasks**:
1. Write integration tests:
   - Full agent execution flow (prompt → LLM → tools → response)
   - Safety intervention scenarios (BLOCK/MODIFY/MONITOR)
   - Failover scenarios (rate limit, timeout, error)
2. Performance benchmarking:
   - Latency: WebSocket RTT, agent execution time
   - Throughput: Concurrent sessions, messages/sec
   - Memory: Session storage overhead
3. Security audit:
   - Input validation (SQL injection, XSS, command injection)
   - Session isolation (no cross-session leakage)
   - Auth key storage (encrypted at rest)
4. Documentation:
   - API reference (OpenAPI spec)
   - Developer guide (how to add tools/agents)
   - Deployment guide (Docker, systemd)

**Deliverables**:
- `tests/integration/test_e2e.py`
- `docs/API_REFERENCE.md`
- `docs/DEVELOPER_GUIDE.md`
- `benchmark/results.md`

---

## 5. License & IP Considerations

### 5.1 OpenClaw License

OpenClaw is **MIT licensed** (confirmed in `/tmp/openclaw/LICENSE`).

**Implications**:
- ✅ We can study and learn from OpenClaw's architecture
- ✅ We can reimplement the **Gateway pattern** (architecture/design) in Python
- ✅ We can reference OpenClaw in documentation (with attribution)
- ❌ We cannot copy OpenClaw's **source code** directly (different language anyway)

### 5.2 Echo Autonomy License

Echo Autonomy is **Apache 2.0** (includes patent grant provisions as defined in the Apache 2.0 License).

**Strategy**:
- Keep Echo's Apache 2.0 license
- Add attribution to OpenClaw in README:
  ```markdown
  ## Acknowledgments
  
  Echo Gateway's architecture is inspired by [OpenClaw](https://github.com/openclaw/openclaw)'s 
  Gateway pattern. OpenClaw is MIT licensed. Echo Gateway reimplements these patterns 
  independently in Python with no source code copying.
  ```
- Document design decisions in `docs/ARCHITECTURE.md`
- No license conflicts: MIT (OpenClaw) → Apache 2.0 (Echo) is compatible
- Different implementation: Python vs Node.js, plus unique BCDSI safety layer

### 5.3 Dependency Licenses

All Python dependencies must be compatible with Apache 2.0:
- FastAPI (MIT) ✅
- Pydantic (MIT) ✅
- Redis (BSD-3) ✅
- httpx (BSD-3) ✅
- websockets (BSD-3) ✅

**No GPL dependencies allowed** (would force GPL viral license).

---

## 6. Differentiation: Echo vs OpenClaw

### 6.1 Unique Features in Echo Gateway

| Feature | OpenClaw | Echo Gateway |
|---------|----------|--------------|
| **Safety Layer** | ❌ None | ✅ BCDSI + Quantum Uncertainty + E-Break |
| **Intervention Levels** | ❌ None | ✅ 5 levels (BLOCK/MODIFY/MONITOR/WARNING/ALLOW) |
| **Mathematical Foundation** | ❌ None | ✅ Shannon Entropy, Purity, JSD Distance |
| **Real-time Risk Assessment** | ❌ None | ✅ O(1) E-Break calculation |
| **Hallucination Detection** | ❌ None | ✅ Cognitive divergence via uncertainty |
| **Context Overflow** | ✅ Auto-compaction | ✅ Auto-compaction + Safety check |
| **Auth Failover** | ✅ Multi-key | ✅ Multi-key (same pattern) |
| **Tool Safety** | ❌ None | ✅ Pre/post-execution BCDSI validation |

### 6.2 Target Use Case

- **OpenClaw**: Personal AI assistant (productivity, automation)
- **Echo Gateway**: Production-grade safe AI agent (enterprise, critical systems)

**Positioning**: Echo Gateway combines OpenClaw's orchestration patterns with production-grade safety validation through BCDSI

---

## 7. Success Metrics (Target Goals)

### 7.1 Technical Targets

**Performance Goals**:
- **Latency**: WebSocket RTT < 50ms (target), Agent execution < 2s at 95th percentile
- **Throughput**: 100+ concurrent sessions, 1000+ msg/sec (target)
- **Availability**: 99.9% uptime with failover (production target)

**Safety Goals**:
- **Hallucination Detection**: 99%+ detection rate (target)
  - Measured using **Echo Autonomy Benchmark** (internal test suite)
  - Baseline: cognitive divergence scenarios from existing BCDSI test corpus
  - Future: Public benchmark suite with labeled datasets
- **False Positive Rate**: < 5% (target, to be validated in Phase 6)
- **Intervention Accuracy**: 95%+ correct level assignment (target)

### 7.2 Adoption Targets

- **GitHub Stars**: 1000+ in 6 months (target)
- **Docker Pulls**: 10K+ in 6 months (target)
- **Contributors**: 10+ active contributors (target)
- **ArXiv Citations**: 50+ citations in 1 year (target)

**Note**: All metrics are aspirational targets based on project goals, not guarantees.

---

## 8. Next Steps (This Week)

### Immediate Actions (Today)

1. ✅ Complete this design document
2. [ ] Review with stakeholder (user approval)
3. [ ] Create project structure:
   ```bash
   mkdir -p echo_gateway/{protocol,tools,tests}
   touch echo_gateway/{__init__.py,server.py,agent.py,session.py}
   touch echo_gateway/protocol/{__init__.py,schemas.py,validator.py}
   touch echo_gateway/tools/{__init__.py,base.py,bash.py}
   ```
4. [ ] Add to README:
   - New section: "🌐 Echo Gateway (Action Agent)"
   - Acknowledge OpenClaw inspiration
5. [ ] Commit changes:
   ```bash
   git add .
   git commit -m "docs: Add Gateway migration plan (OpenClaw-inspired)"
   ```

### Week 1 Goals

- Implement Phase 1 (Protocol Layer)
- Write unit tests for protocol schemas
- Document API design in `docs/API_DESIGN.md`

---

## 9. Open Questions

1. **Session Storage**: Redis or SQLite? (Redis for multi-instance, SQLite for simplicity)
2. **Streaming**: Server-Sent Events (SSE) or WebSocket for agent responses?
3. **Tool Isolation**: Run tools in Docker containers for safety?
4. **MCP Compatibility**: Should Echo Gateway expose MCP-compatible tools?
5. **Multi-tenancy**: Support multiple users/orgs in single Gateway instance?

---

## 10. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Complexity Creep** | High | Start minimal (Phase 1-3 only), defer fancy features |
| **Performance Bottleneck** | Medium | Profile early, optimize hot paths (asyncio, caching) |
| **Security Vulnerabilities** | High | Security audit in Phase 6, follow OWASP guidelines |
| **License Violation** | Critical | Legal review before release, clear attribution |
| **Feature Parity Pressure** | Medium | Focus on differentiation (safety), not copying OpenClaw |

---

## Appendix A: Glossary

- **Gateway**: Control plane for routing AI agent requests
- **Bridge**: RPC adapter layer (abstraction over WebSocket/HTTP)
- **Session**: Isolated conversation state (context + history)
- **Pi Agent**: OpenClaw's embedded AI agent runtime
- **BCDSI**: Bounded Cognitive Divergence Safety Intervention
- **E-Break**: Emergency brake risk metric (0.0-1.5 scale)
- **MCP**: Model Context Protocol (tool integration standard)

---

## Appendix B: References

1. OpenClaw GitHub: https://github.com/openclaw/openclaw
2. OpenClaw Docs: https://docs.openclaw.ai/
3. OpenCode: https://github.com/anomalyco/opencode
4. Echo Autonomy GitHub: https://github.com/cleanbell2/echo_autonomy
5. FastAPI Docs: https://fastapi.tiangolo.com/
6. Pydantic Docs: https://docs.pydantic.dev/

---

**Document Status**: Ready for review  
**Next Action**: User approval → Begin Phase 1 implementation  
**ETA for MVP**: 12 weeks (assuming 1 FTE developer)
