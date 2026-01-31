# PR Body Template (Copy-Paste Ready)

**Tags**: `echo_gateway`, `phase2`, `ci`, `no-true`, `ready-to-merge`

---

## ✅ Echo Gateway Phase 2 — Ready to Merge

### Summary
This PR delivers **Phase 2 patches** for Echo Gateway:
- ✅ Auth Profile Failover (multi-key, cooldown, last_success preference)
- ✅ Tool Sandbox (path traversal + symlink defense, workspace isolation)
- ✅ BCDSI Middleware integration (local/http, 5-level intervention, fail-closed for tools)
- ✅ Integration tests (5/5 passed locally)
- ✅ Comprehensive docs & merge checklist

### What changed
**Implementation**
- `gateway/auth_profiles.py` — multi-key failover with cooldown, ENV-only key refs
- `tools/sandbox.py` — path traversal prevention + symlink blocking
- `middleware/bcdsi_integration.py` — pluggable safety adapter (local/http), consistent decision schema

**Tests**
- `tests/test_gateway_integration.py` — 5/5 passing (auth failover, sandbox, BCDSI allow/block, fail-closed, summary)
- `tests/test_e2e.py` — graceful skip until Phase 3/4 server endpoints exist

**Docs**
- Design plan, phase2 patch guide, merge checklists, test/final status reports

### Security & Safety
- **No plaintext secrets**: auth profiles use `ENV:` references only
- **Fail-closed for tool execution** when safety engine is unavailable (BLOCK)
- Inbound prompts default to WARNING/MONITOR when engine missing (configurable)

### CI (Decision: no `|| true`)
A workflow is prepared as `.github/workflows/tests.yml`.
- **No `|| true` used** (failures are not hidden)
- E2E tests rely on internal `pytest.skip()` when server is not running

### How to test locally
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest tests/test_gateway_integration.py -v
pytest tests/test_e2e.py -v
```

### Merge recommendation
✅ **Squash & merge** (keeps history clean for a design+impl bundle)

### Post-merge next step (Phase 3)
Create `phase3-protocol` branch and implement protocol layer:
`echo_gateway/protocol/{envelope.py, schemas.py, validator.py}` + unit tests.
