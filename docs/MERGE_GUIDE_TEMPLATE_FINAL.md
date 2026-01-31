# Echo Gateway Phase 2 — Merge Guide (Final)

**Tags**: `echo_gateway`, `phase2`, `ci`, `no-true`, `ready-to-merge`

---

## Decision
- CI에서 `|| true` 금지
- 최종 `.github/workflows/tests.yml` 확정 (E2E는 pytest.skip 기반 graceful handling)

---

## Pre-merge (5-minute checklist)

### 1. Local tests pass
```bash
pytest tests/test_gateway_integration.py -v
pytest tests/test_e2e.py -v
```

### 2. No secrets committed
- `.env` is gitignored
- auth profiles use `ENV:` references only

### 3. Fail-closed confirmed
- Tool stage + engine missing → **BLOCK**
- Inbound stage + engine missing → **WARNING/MONITOR**

### 4. Dependencies included
- `pytest`, `pytest-asyncio`, `httpx`, `websockets` in dev requirements

---

## CI setup (recommended order)

### Option A (best): Enable CI first, then merge
1. Go to GitHub Actions page
2. Create workflow using `.github/workflows/tests.yml` content (already prepared)
3. Commit to `main`
4. Merge PR

### Option B: Merge now, enable CI right after
- Merge PR first (local tests already passing)
- Add workflow in a follow-up PR

---

## Merge command (Squash)

```bash
gh pr merge 1 --squash --delete-branch
```

---

## Post-merge (Day 1)

```bash
git checkout main
git pull origin main
git checkout -b phase3-protocol
mkdir -p echo_gateway/protocol
```

---

## Tags
`echo_gateway`, `phase2`, `ci`, `no-true`, `ready-to-merge`
