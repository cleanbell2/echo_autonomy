# Merge Guide — Echo Gateway Phase 2 (Copy-Paste Ready)

**Tags**: `echo_gateway`, `phase2`, `ci`, `no-true`, `ready-to-merge`

---

## ✅ Merge Guide — Echo Gateway Phase 2

### 0) Pre-merge (5-minute checklist)
1. **Local tests pass**
   - `pytest tests/test_gateway_integration.py -v`
2. **No secrets committed**
   - `.env` is gitignored
   - configs use `ENV:` references (no plaintext keys)
3. **Fail-closed confirmed**
   - tool stage + engine missing → **BLOCK**
   - inbound stage + engine missing → **WARNING** (monitoring)
4. **Sandbox protection confirmed**
   - traversal + absolute paths blocked
   - symlink tests are OS-conditional (should not skip entire suite)
5. **Dependencies present**
   - `pytest`, `pytest-asyncio`, `httpx`, `websockets` in dev deps
6. **CI policy enforced**
   - **No `|| true`** in workflow; failures must surface

---

### 1) Optional: Enable CI workflow first (recommended)
Add/update `.github/workflows/tests.yml` with:
- Python matrix (e.g., 3.10/3.11/3.12)
- Install `requirements.txt` + `requirements-dev.txt`
- Run:
  - `pytest tests/test_gateway_integration.py -v`
  - `pytest tests/test_e2e.py -v`

**Important**
- E2E is expected to **skip gracefully** if the server is not running yet.
- Do **not** use `|| true`. Skips should come from `pytest.skip()`.

---

### 2) Merge (recommended: squash)
From GitHub UI:
- Select **Squash and merge**
- Delete branch after merge (optional)

From CLI (example):
- `gh pr merge <PR_NUMBER> --squash --delete-branch`

---

### 3) Post-merge (Day 1)
- Sync main:
  - `git checkout main && git pull`
- Start Phase 3 branch (example name):
  - `git checkout -b phase3-protocol`
- Create protocol scaffolding:
  - `mkdir -p echo_gateway/protocol`

---

### 4) Notes on E2E tests
- E2E tests should **not** be forced to pass when the server is not implemented yet.
- The correct behavior is:
  - server missing → `pytest.skip()` (exit 0)
  - real failures → test fails (exit != 0)
- This ensures **failures are not suppressed** and CI remains trustworthy.
