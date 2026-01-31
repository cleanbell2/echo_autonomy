# PR Body Template (Copy-Paste Ready)

**Tags**: `echo_gateway`, `phase2`, `ci`, `no-true`, `ready-to-merge`

---

## ✅ Echo Gateway Phase 2 — Ready to Merge

### Summary
This PR adds Phase 2 safety patches and supporting docs for Echo Gateway (OpenClaw-inspired architecture, independently reimplemented).

**Included**
- ✅ Auth Profiles: multi-key failover + cooldown (ENV-only key references)
- ✅ Tool Sandbox: path traversal defense + workspace isolation (symlink handling included)
- ✅ BCDSI Middleware: pluggable adapter (local/http), 5-level intervention
- ✅ Integration tests: Phase 2 coverage (auth/sandbox/bcdsi + fail-closed behavior)
- ✅ Documentation: migration plan, patch guide, merge checklist, status reports

### Security Notes
- **No plaintext secrets**: config uses `ENV:` references only
- **Fail-closed default for tools**: if safety engine is unavailable, tool execution is blocked (safer default)
- **Path traversal defense**: normalized/validated paths; suspicious paths rejected

### Tests
- Integration tests are expected to pass locally and in CI.
- E2E tests are designed to **skip gracefully** when the server endpoints are not available yet (until the relevant phase), using **internal `pytest.skip()`**.

### CI Policy (Decision: no `|| true`)
- ✅ **No `|| true`**: failures are not suppressed
- ✅ E2E "no server yet" is handled via **pytest skip**, not shell suppression

### Merge Recommendation
- ✅ **Squash & merge** recommended (keeps history clean)
- No breaking changes intended (additive patches + docs)

### References / Attribution
- Inspired by OpenClaw Gateway pattern (MIT).  
- This is an independent Python implementation (no source code copying).
