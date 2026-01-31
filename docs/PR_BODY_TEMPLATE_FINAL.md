# PR Body Template (Copy-Paste Ready)

**Tags**: `echo_gateway`, `phase2`, `ci`, `no-true`, `ready-to-merge`

---

## ✅ Echo Gateway Phase 2 — Ready to Merge

### What's included
- ✅ **Auth Profile Failover** (multi-key, cooldown, last-success preference)
- ✅ **Tool Sandbox** (path traversal defense, workspace isolation, symlink handling)
- ✅ **BCDSI Middleware** (local/http adapter, 5-level intervention, fail-closed for tools)
- ✅ **Integration Tests** (Phase 2: 5/5 passing locally)
- ✅ **Docs** (design plan + patches + checklists + reports)

### Why this matters
This PR ports the **Gateway orchestration pattern** (OpenClaw-inspired) into a minimal, security-first Python runtime, and integrates **Echo Autonomy's BCDSI safety layer** as a first-class middleware.

### CI / Testing policy
- ✅ **No `|| true`** — failures are not suppressed (no hidden test failures).
- ✅ E2E tests are designed to **skip gracefully** when server endpoints are not available yet (until Phase 3/4), using internal `pytest.skip()` rather than shell suppression.

### Verification (local)
```bash
pytest tests/test_gateway_integration.py -v
pytest tests/test_e2e.py -v
```

### Security notes
- **No plaintext secrets** in repo: keys referenced via `ENV:` only (config uses ENV indirection).
- **Fail-closed default for tool execution** when safety engine is missing/unreachable.
- **Sandbox isolation** prevents workspace escape (path traversal + optional symlink hardening).

### License & attribution
- Inspired by the Gateway pattern from **OpenClaw (MIT)**.
- Independent Python reimplementation (no source code copying).
- Echo Autonomy codebase remains **Apache 2.0** compatible.

### Merge recommendation
✅ **Squash & merge** is recommended to keep main history clean.

**Tags**: `echo_gateway`, `phase2`, `ci`, `no-true`, `ready-to-merge`
