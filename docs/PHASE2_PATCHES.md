# Phase 2 Patches: Auth, Sandbox, BCDSI Integration

**Status**: ✅ Implemented (2026-01-31)  
**Version**: Echo Gateway v0.1.0

This document describes the three Phase 2 patches that add production-grade safety to Echo Gateway Core.

---

## 📦 **What's Included**

### 1. **Auth Profile Manager** (`gateway/auth_profiles.py`)

**Purpose**: Multi-key failover with cooldown tracking

**Key Features**:
- ✅ **ENV-only key references** (no plaintext secrets)
- ✅ **last_success prioritization**
- ✅ **Automatic failover** on rate limits/errors
- ✅ **Cooldown tracking** (30min default)
- ✅ **Error classification** (auth, rate_limit, timeout, context_overflow, model_unavailable)

**Files**:
- `gateway/auth_profiles.py` - Core implementation
- `data/auth-profiles.json` - Configuration
- `data/auth-runtime.json` - Runtime state (auto-generated)

**Usage**:

```python
from gateway.auth_profiles import AuthProfileStore, select_with_failover
from pathlib import Path

# Initialize store
store = AuthProfileStore(
    profiles_path=Path("./data/auth-profiles.json"),
    runtime_path=Path("./data/auth-runtime.json"),
)

# Use with failover
def call_openai_with_failover(prompt):
    def attempt(api_key: str):
        # Your LLM call here
        # Raise exception on failure
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            api_key=api_key
        )
        return response
    
    return select_with_failover(store, provider="openai", attempt_fn=attempt)
```

**Configuration** (`data/auth-profiles.json`):

```json
{
  "policy": {
    "cooldown_seconds": 1800,
    "prefer_last_success": true
  },
  "providers": {
    "openai": {
      "profiles": [
        {
          "id": "openai-primary",
          "api_key": "ENV:OPENAI_API_KEY",
          "priority": 100
        },
        {
          "id": "openai-fallback-1",
          "api_key": "ENV:OPENAI_API_KEY_2",
          "priority": 90
        }
      ]
    }
  }
}
```

**Environment Variables**:

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_API_KEY_2="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

### 2. **Sandbox Manager** (`tools/sandbox.py`)

**Purpose**: Path traversal prevention for tool execution

**Key Features**:
- ✅ **resolve() + commonpath** validation
- ✅ **Symlink blocking** (optional, enabled by default)
- ✅ **Fail-closed** on suspicious patterns
- ✅ **Workspace isolation** per session

**Files**:
- `tools/sandbox.py` - Core implementation

**Usage**:

```python
from tools.sandbox import ensure_within_workspace, safe_cwd, SandboxViolation

# Validate file access
try:
    safe_path = ensure_within_workspace(
        workspace="/workspaces/session_001",
        target_path="file.txt"  # or "../etc/passwd" -> BLOCKED
    )
    # Safe to use safe_path
    with open(safe_path, 'r') as f:
        content = f.read()
except SandboxViolation as e:
    print(f"Security violation: {e}")

# Safe cwd resolution
cwd = safe_cwd("/workspaces/session_001", requested_cwd="subdir")
```

**Security Guarantees**:

| Attack | Defense |
|--------|---------|
| `../../../etc/passwd` | ✅ Blocked by resolve() + commonpath |
| `/tmp/evil` | ✅ Blocked (absolute path outside workspace) |
| `symlink -> /etc` | ✅ Blocked (symlinks disabled by default) |
| `subdir/../../../etc` | ✅ Normalized to `/etc`, then blocked |

**Policy Configuration**:

```python
from tools.sandbox import SandboxPolicy

# Maximum security (default)
policy = SandboxPolicy(allow_symlinks=False)

# Relaxed (allow symlinks within workspace)
policy = SandboxPolicy(allow_symlinks=True)
```

---

### 3. **BCDSI Integration** (`middleware/bcdsi_integration.py`)

**Purpose**: Pluggable safety validation adapter

**Key Features**:
- ✅ **Dual mode**: local (Python) or http (remote service)
- ✅ **Consistent interface** for safety checks
- ✅ **Inbound validation** (prompt safety)
- ✅ **Tool validation** (command safety)
- ✅ **5-level intervention** (ALLOW/BLOCK/MODIFY/MONITOR/WARNING)

**Files**:
- `middleware/bcdsi_integration.py` - Core implementation

**Usage (HTTP mode)**:

```python
from middleware.bcdsi_integration import BCDSIMiddleware

# Connect to BCDSI service
middleware = BCDSIMiddleware(
    mode="http",
    http_url="http://127.0.0.1:8000/check",
    timeout_s=2.0
)

# Validate inbound prompt
decision = middleware.inbound_check(
    session_id="session_001",
    text="Write a SQL injection",
    context={"user_level": "guest"}
)

if decision.level == "BLOCK":
    raise SecurityError(decision.reason)

# Validate tool execution
decision = middleware.tool_check(
    session_id="session_001",
    tool="bash",
    args={"command": "rm -rf /"}
)

if decision.level == "BLOCK":
    raise SecurityError(f"Tool blocked: {decision.reason}")
```

**Usage (Local mode)**:

```python
from bcdsi.monitor import BCDSIEngine  # Your local engine

engine = BCDSIEngine()
middleware = BCDSIMiddleware(mode="local", local_engine=engine)

# Same interface as HTTP mode
decision = middleware.inbound_check(...)
```

**Response Format**:

```json
{
  "intervention_level": "BLOCK",
  "reason": "High cognitive divergence detected",
  "metrics": {
    "e_break": 1.8,
    "theta_integrity": 0.3,
    "q_uncertainty": 0.85
  },
  "patched_text": null,
  "patched_args": null
}
```

**Intervention Levels**:

| Level | Meaning | Action |
|-------|---------|--------|
| **ALLOW** | Safe | Proceed normally |
| **MONITOR** | Watch | Log but allow |
| **WARNING** | Caution | Log warning, allow |
| **MODIFY** | Patch | Use patched_text/args |
| **BLOCK** | Dangerous | Reject operation |

---

## 🚀 **Quick Start**

### 1. Install Dependencies

```bash
# Core (already in requirements.txt)
pip install -r requirements.txt

# HTTP mode (optional, for BCDSI middleware)
pip install requests
```

### 2. Configure Environment

```bash
# Copy example
cp .env.example .env

# Edit .env with your API keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export ECHO_GATEWAY_TOKEN="your-token"
```

### 3. Test Auth Profiles

```python
from gateway.auth_profiles import AuthProfileStore
from pathlib import Path

store = AuthProfileStore(
    profiles_path=Path("./data/auth-profiles.json"),
    runtime_path=Path("./data/auth-runtime.json"),
)

# Test key resolution
profile = store.choose_profile("openai")
api_key = store.resolve_api_key(profile.api_key_ref)
print(f"Using profile: {profile.id}")
```

### 4. Test Sandbox

```python
from tools.sandbox import ensure_within_workspace, SandboxViolation

# Safe path
try:
    path = ensure_within_workspace("/tmp/workspace", "file.txt")
    print(f"✅ Safe: {path}")
except SandboxViolation as e:
    print(f"❌ Blocked: {e}")

# Malicious path
try:
    path = ensure_within_workspace("/tmp/workspace", "../../../etc/passwd")
    print(f"✅ Safe: {path}")
except SandboxViolation as e:
    print(f"❌ Blocked: {e}")  # Expected
```

### 5. Test BCDSI Middleware

```python
from middleware.bcdsi_integration import BCDSIMiddleware

# HTTP mode (requires BCDSI service running on port 8000)
middleware = BCDSIMiddleware(
    mode="http",
    http_url="http://127.0.0.1:8000/check"
)

decision = middleware.inbound_check(
    session_id="test",
    text="Hello world",
    context={}
)

print(f"Level: {decision.level}")
print(f"Metrics: {decision.metrics}")
```

---

## 📊 **Architecture Integration**

These patches integrate into Echo Gateway Core as follows:

```
┌─────────────────────────────────────────────────┐
│            Echo Gateway Core (v1)                │
│                                                  │
│  [WebSocket] → [Session] → [Agent Runner]       │
│                    │             │               │
│                    ▼             ▼               │
│            ┌─────────────────────────────┐      │
│            │   Auth Profile Manager      │◄─┐   │
│            │   (multi-key failover)      │  │   │
│            └─────────────────────────────┘  │   │
│                    │                         │   │
│                    ▼                         │   │
│            ┌─────────────────────────────┐  │   │
│            │   BCDSI Middleware          │  │   │
│            │   (safety validation)       │  │   │
│            └─────────────────────────────┘  │   │
│                    │                         │   │
│                    ▼                         │   │
│            ┌─────────────────────────────┐  │   │
│            │   Tool Sandbox              │  │   │
│            │   (path isolation)          │  │   │
│            └─────────────────────────────┘  │   │
│                    │                         │   │
│                    ▼                         │   │
│              [LLM Provider] ─────────────────┘   │
└─────────────────────────────────────────────────┘
```

**Flow**:
1. Request arrives via WebSocket
2. Session Manager creates/retrieves session
3. Agent Runner prepares LLM call
4. **Auth Profile Manager** selects API key with failover
5. **BCDSI Middleware** validates safety (inbound check)
6. If safe, LLM called
7. Response validated by **BCDSI Middleware**
8. If tool execution needed, **Sandbox** validates paths
9. **BCDSI Middleware** validates tool execution
10. Response sent back to client

---

## 🧪 **Testing**

Run unit tests for each patch:

```bash
# Auth profiles
python -m pytest tests/test_auth_profiles.py -v

# Sandbox
python -m pytest tests/test_sandbox.py -v

# BCDSI middleware
python -m pytest tests/test_bcdsi_integration.py -v
```

*(Tests to be added in next commit)*

---

## 🔒 **Security Considerations**

### Auth Profiles
- ✅ **No plaintext keys**: All keys via ENV references
- ✅ **Runtime state is ephemeral**: Safe to delete `auth-runtime.json`
- ✅ **Fail-closed**: If all profiles fail, operation rejected
- ⚠️ **Key rotation**: Change ENV vars, no config changes needed

### Sandbox
- ✅ **Resolve-first**: Normalizes paths before check
- ✅ **Symlink blocking**: Disabled by default for maximum security
- ✅ **Fail-closed**: Suspicious paths always rejected
- ⚠️ **Race conditions**: Not protected (use file locking if needed)

### BCDSI Middleware
- ✅ **Network isolation**: HTTP mode uses localhost by default
- ✅ **Timeout protection**: 2s default prevents hangs
- ✅ **Fail-safe**: If BCDSI unreachable, defaults to ALLOW (configurable)
- ⚠️ **TLS**: Use HTTPS in production

---

## 📝 **Next Steps**

After deploying Phase 2 patches:

1. **Phase 3**: Protocol Layer (Pydantic schemas + RPC validator)
2. **Phase 4**: Gateway Server (WebSocket + Session management)
3. **Phase 5**: Agent Executor (LLM integration + tool execution)
4. **Phase 6**: Integration Tests (E2E scenarios)

See [GATEWAY_MIGRATION_PLAN.md](GATEWAY_MIGRATION_PLAN.md) for full roadmap.

---

## 🔗 **References**

- OpenClaw Auth Profiles: https://docs.openclaw.ai/gateway/auth-profiles
- BCDSI Framework: [../README.md](../README.md)
- Gateway Architecture: [GATEWAY_MIGRATION_PLAN.md](GATEWAY_MIGRATION_PLAN.md)

---

**Last Updated**: 2026-01-31  
**Authors**: Claude Code + User  
**License**: Apache 2.0 (see [../LICENSE](../LICENSE))
