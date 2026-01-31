# Merge Guide — Echo Gateway Phase 2 (Copy-Paste Ready)

**Tags**: `echo_gateway`, `phase2`, `ci`, `no-true`, `ready-to-merge`

---

## ✅ Merge Guide — Echo Gateway Phase 2

### Pre-merge (5-minute checklist)
1. **Local tests pass**
   ```bash
   pytest tests/test_gateway_integration.py -v
   pytest tests/test_e2e.py -v
   ```

2. **No secrets committed**
   - `.env` is gitignored
   - configs reference secrets via `ENV:` only

3. **Fail-closed defaults confirmed**
   - tool-stage safety check blocks when engine is missing/unreachable

4. **Dependencies are present**
   - dev deps include `pytest`, `pytest-asyncio`, `httpx`, `websockets`

---

### CI policy (important)
- ✅ **`|| true` is not allowed** in CI test commands.
- ✅ E2E uses internal `pytest.skip()` to avoid breaking CI when servers are not running.
- ✅ Failures are not suppressed (no hidden failures).

---

### CI setup options

**Option A (recommended): Enable CI first, then merge**
1. Add/update `.github/workflows/tests.yml` (example below)
2. Push the workflow (via GitHub UI or a normal commit)
3. Ensure Actions runs on PR and is green

**Option B: Merge now, enable CI immediately after**
1. Merge PR
2. Open a follow-up PR adding the workflow
3. Confirm Actions is green on the follow-up PR

---

### Merge command (GitHub CLI)
```bash
gh pr merge <PR_NUMBER> --squash --delete-branch
```

---

### Post-merge (Day 1)
```bash
git checkout main
git pull origin main
git checkout -b phase3-protocol
mkdir -p echo_gateway/protocol
```

Phase 3 next:
- `envelope.py`
- `schemas.py`
- `validator.py`
- protocol unit tests + API design doc

---

### Example CI workflow (no `|| true`)

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run Gateway integration tests
        run: |
          pytest tests/test_gateway_integration.py -v

      # E2E is expected to skip when server is not running (Phase 3/4 endpoints not implemented yet).
      # Do NOT use `|| true`; rely on pytest skips instead.
      - name: Run E2E tests (expected to skip if server not running)
        run: |
          pytest tests/test_e2e.py -v

      - name: Test summary
        if: always()
        run: |
          echo "✅ Gateway integration tests completed"
          echo "⏭️ E2E tests may be skipped when server is not running (expected)"
```

**Tags**: `echo_gateway`, `phase2`, `ci`, `no-true`, `ready-to-merge`
