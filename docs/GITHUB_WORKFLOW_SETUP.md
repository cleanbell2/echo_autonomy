# GitHub Actions Workflow Setup

Due to GitHub App permissions, the workflow file needs to be created manually via GitHub UI.

## Steps:

1. **Go to your repository on GitHub:**
   https://github.com/cleanbell2/echo_autonomy

2. **Navigate to Actions tab**
   - Click on "Actions" in the top menu
   - Click "New workflow" or "set up a workflow yourself"

3. **Create the workflow file:**
   - Name: `tests.yml`
   - Location: `.github/workflows/tests.yml`
   - Content: (see below)

4. **Commit directly to main branch**

---

## Workflow File Content:

```yaml
name: Tests

on:
  push:
  pull_request:

jobs:
  pytest:
    strategy:
      fail-fast: false
      matrix:
        os: [windows-latest, ubuntu-latest]
        python-version: ["3.13"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install
        run: |
          python -m pip install -U pip
          python -m pip install -r requirements-dev.txt
      - name: Test (Release Check)
        run: |
          python -B -m pytest -q
```

---

## What This Enables:

✅ **Automated testing** on every push  
✅ **Pull request validation**  
✅ **Tests badge** in README (activates after first run)  
✅ **Cross-platform testing** (Windows + Ubuntu)  
✅ **CI/CD foundation** for releases  

## Expected Result:

```
53 passed, 1 skipped in ~6-8s
```

---

## After Setup:

The Tests badge in README will automatically activate:

```markdown
![Tests](https://github.com/cleanbell2/echo_autonomy/actions/workflows/tests.yml/badge.svg)
```

---

**Note:** The workflow file is also available locally at `.github/workflows/tests.yml` but cannot be pushed due to GitHub App restrictions.
