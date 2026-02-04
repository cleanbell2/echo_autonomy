# Phase 7 — Real LLM Integration

## Phase 7.1: Config + Factory (MERGED ✅)
- LLMConfig.from_env(): env 기반 설정 (Fail-Closed)
- build_llm_client(): provider factory
- OpenAI-compatible REST client + SSE stream parser
- Anthropic client skeleton
- Tests: 외부 네트워크 없이 config/factory만 검증

## Phase 7.2: Orchestrator Wiring (MERGED ✅)

Gateway Orchestrator는 환경변수 기반 LLM 설정을 읽어 Factory로 주입한다.

### ✅ Implemented Changes
1. **Dynamic Wiring**: `echo_gateway/gateway/wiring.py` updated
   - Removed hard-coded `FakeLLMClient`
   - Added `LLMConfig.from_env()` → `build_llm_client()`
   - Brain selection now driven by `.env` configuration

2. **OpenAI Mock Tests**: `tests/executor/test_openai_client.py` (6 tests)
   - ✅ test_openai_complete_success
   - ✅ test_openai_stream_success
   - ✅ test_openai_complete_http_error
   - ✅ test_openai_stream_parse_error
   - ✅ test_openai_client_requires_api_key
   - ✅ test_openai_stream_empty_lines

3. **Test Results**: 95 passed, 6 skipped

## Phase 7.3: Claude Integration (IMPLEMENTED ✅)

**벨이 가장 신뢰하는 Claude Sonnet 4.5**를 에코에 연결하는 단계.

### ✅ Implemented Changes

1. **AnthropicClient** (`echo_gateway/executor/anthropic_client.py`)
   - **System Prompt Translation**: OpenAI 형식 (`role: system`) → Anthropic 형식 (`system=` 파라미터)
   - **Streaming Event Translation**: Anthropic events → unified delta format
   - **Fail-Closed Error Handling**: Auth, Rate Limit, API errors
   - **Config-Based Initialization**: Uses `LLMConfig` for consistency

2. **Message Format Translation**
   ```python
   # OpenAI Format (input)
   [
     {"role": "system", "content": "You are Echo"},
     {"role": "user", "content": "Hello"}
   ]
   
   # Anthropic Format (output)
   system="You are Echo"
   messages=[{"role": "user", "content": "Hello"}]
   ```

3. **Streaming Event Translation**
   ```python
   # Anthropic Events
   content_block_delta → {"content": "text", "tool_calls": None, "finish_reason": None}
   message_delta       → {"content": "", "tool_calls": None, "finish_reason": "end_turn"}
   ```

4. **Tests** (`tests/executor/test_anthropic_client.py` — 7 tests)
   - ✅ test_anthropic_system_prompt_extraction
   - ✅ test_anthropic_complete_success
   - ✅ test_anthropic_complete_no_system_prompt
   - ✅ test_anthropic_auth_error
   - ✅ test_anthropic_rate_limit_error
   - ✅ test_anthropic_streaming_event_translation
   - ✅ test_anthropic_client_requires_api_key

5. **Test Results**: 102 passed, 6 skipped
   - Phase 1-6: 89 tests
   - Phase 7.1: 6 tests (config + factory)
   - Phase 7.2: 6 tests (OpenAI mocks)
   - Phase 7.3: 7 tests (Anthropic mocks)

### Architecture
```
Environment Variables (.env)
    ↓
LLMConfig.from_env()
    ↓
build_llm_client(cfg)
    ↓
[FakeLLMClient | OpenAIClient | AnthropicClient]
    ↓
Orchestrator (The Brain)
```

### Environment Variables
```bash
# Provider Selection
LLM_PROVIDER=fake           # fake | openai | anthropic (default: fake)

# Credentials (required for real providers)
LLM_API_KEY=sk-...          # OpenAI: sk-... | Anthropic: sk-ant-...

# Model Configuration
LLM_MODEL=gpt-4o-mini                    # OpenAI models
# LLM_MODEL=claude-3-5-sonnet-20240620   # Anthropic models (Sonnet 4.5)
# LLM_MODEL=claude-3-opus-20240229       # Claude Opus

LLM_BASE_URL=               # Optional (default: https://api.openai.com)
LLM_TEMPERATURE=0.7         # Sampling temperature (0.0 - 2.0)
LLM_MAX_TOKENS=1024         # Max tokens per request
LLM_TIMEOUT_S=30            # Request timeout in seconds
```

### Usage Examples

#### OpenAI (GPT-4)
```bash
LLM_PROVIDER=openai
LLM_API_KEY=sk-proj-...
LLM_MODEL=gpt-4-turbo-preview
```

#### Anthropic (Claude Sonnet 4.5) — 벨의 선택
```bash
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-api03-...
LLM_MODEL=claude-3-5-sonnet-20240620
LLM_MAX_TOKENS=4096
```

#### Development (Fake LLM)
```bash
LLM_PROVIDER=fake
# No API key required
```

### Wiring Implementation
**File:** `echo_gateway/gateway/wiring.py`

```python
from echo_gateway.config.llm_config import LLMConfig
from echo_gateway.executor.llm_factory import build_llm_client

def create_orchestrator(session_store: SessionStore) -> Orchestrator:
    # Load config from environment
    cfg = LLMConfig.from_env()
    
    # Build LLM client (factory pattern)
    llm = build_llm_client(cfg)
    
    # Wire up orchestrator
    return Orchestrator(
        llm=llm,
        tool_registry=ToolRegistry(),
        tool_runtime=ToolRuntime(),
        prompt_builder=PromptBuilder(),
        session_store=session_store,
    )
```

### Testing Policy (Zero-Cost)
- **CI/Unit Tests**: No real API calls, only mocks
- **Integration Tests**: Marked with `@pytest.mark.integration`, opt-in only
- **Mock Strategy**: Use `unittest.mock` or `pytest-mock` for HTTP calls

**Example:** `tests/executor/test_openai_client.py`
- Mocks `httpx.AsyncClient` for complete() and stream()
- Verifies request/response format without network calls
- Tests error handling (auth, parsing, HTTP errors)

### Running Tests
```bash
# Phase 7 executor tests (all LLM adapters)
pytest tests/executor -v

# Specific adapter tests
pytest tests/executor/test_openai_client.py -v      # OpenAI (6 tests)
pytest tests/executor/test_anthropic_client.py -v   # Anthropic (7 tests)

# Full test suite
pytest tests/ -v  # 102 passed, 6 skipped

# Test with specific provider (local only, requires API key)
LLM_PROVIDER=openai LLM_API_KEY=sk-... pytest tests/executor/test_orchestrator_*.py -v
LLM_PROVIDER=anthropic LLM_API_KEY=sk-ant-... pytest tests/executor/test_orchestrator_*.py -v
```

## Phase 7 Summary (Complete ✅)

### What We Built
1. **Config Layer** (Phase 7.1)
   - Environment-driven LLM configuration
   - Fail-closed credential validation
   - Type-safe Pydantic models

2. **Dynamic Wiring** (Phase 7.2)
   - Factory pattern for brain selection
   - Removed hard-coded FakeLLM
   - `.env` controls brain type

3. **Dual Brain Support** (Phase 7.3)
   - **OpenAI**: GPT-4, GPT-3.5, etc.
   - **Anthropic**: Claude Sonnet 4.5, Opus, etc.
   - Message format translation
   - Streaming event unification

### Architecture Achievement
```
Echo Autonomy is now Brain-Agnostic:
  - OpenAI for speed and cost efficiency
  - Anthropic (Claude) for insight and reasoning depth
  - Fake LLM for development and testing
  
Switch brains with ONE environment variable: LLM_PROVIDER
```

### Test Coverage
- **102 tests passing** (6 skipped E2E)
- **Zero network calls** in CI (all mocked)
- **Fail-closed** error handling throughout
- **Coverage**: Config, Factory, OpenAI, Anthropic, Orchestrator, Gateway, Streaming

### Security Properties
- ✅ No hardcoded secrets
- ✅ Fail-closed: missing keys → ValueError
- ✅ Type safety: Pydantic validation
- ✅ CI-safe: mock-based testing

## Next Steps (Phase 7.4+)
- [ ] Tool calling integration (OpenAI function calling)
- [ ] Tool calling for Anthropic (Claude tool use)
- [ ] Streaming alignment with Phase 6 SSE/WebSocket
- [ ] Production observability (request_id, latency)
- [ ] Rate limiting and retry strategies
- [ ] Multi-provider fallback chains
