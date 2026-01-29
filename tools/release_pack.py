from __future__ import annotations

from pathlib import Path
import ast
import re
import sys
from importlib import metadata

ROOT = Path(__file__).resolve().parents[1]

REPO_OWNER = "cleanbell2"
REPO_NAME  = "echo_autonomy"

README = ROOT / "README.md"
REQ = ROOT / "requirements.txt"
REQ_DEV = ROOT / "requirements-dev.txt"
WF = ROOT / ".github" / "workflows" / "tests.yml"
RELEASE_TPL = ROOT / ".github" / "RELEASE_TEMPLATE.md"

EXCLUDE_DIRS = {
    ".venv", ".venv-1", ".git", "__pycache__", ".pytest_cache",
    "artifacts", "자가발전논문",
}
EXCLUDE_FILES = {
    "non_unitarity_original.py",
}

# import-name -> pip-name mapping (minimal common set)
PIP_NAME_MAP = {
    "PIL": "Pillow",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
}

DEV_DEPS = {
    "pytest", "pluggy", "anyio", "coverage", "hypothesis",
}

def _is_excluded(path: Path) -> bool:
    # path.parts is a tuple of strings
    for p in path.parts:
        if p in EXCLUDE_DIRS:
            return True
    if path.name in EXCLUDE_FILES:
        return True
    return False

def repo_local_toplevel() -> set[str]:
    local = set()
    # top-level .py modules
    for p in ROOT.glob("*.py"):
        local.add(p.stem)

    # packages (dir with __init__.py)
    for d in ROOT.iterdir():
        if d.is_dir() and (d / "__init__.py").exists():
            local.add(d.name)
    return local

def stdlib_modules() -> set[str]:
    # Python 3.10+ provides stdlib_module_names
    s = set(getattr(sys, "stdlib_module_names", ()))
    # plus builtins-ish
    s |= {"__future__", "typing", "dataclasses"}
    return s

def iter_py_files() -> list[Path]:
    files = []
    for p in ROOT.rglob("*.py"):
        if _is_excluded(p):
            continue
        # skip venvs explicitly
        if any(seg in EXCLUDE_DIRS for seg in p.parts):
            continue
        files.append(p)
    return files

def collect_import_roots() -> set[str]:
    roots: set[str] = set()
    for f in iter_py_files():
        try:
            src = f.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src)
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    roots.add(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    roots.add(node.module.split(".")[0])
    return roots

def to_pip_name(import_name: str) -> str:
    return PIP_NAME_MAP.get(import_name, import_name)

def pinned_req(pip_name: str) -> str:
    # Try to pin to installed version for reproducibility
    try:
        v = metadata.version(pip_name)
        return f"{pip_name}>={v}"
    except Exception:
        # Some distributions have different metadata names; try import-name as fallback
        try:
            v = metadata.version(pip_name.replace("-", "_"))
            return f"{pip_name}>={v}"
        except Exception:
            return pip_name

def write_requirements() -> None:
    imports = collect_import_roots()
    local = repo_local_toplevel()
    stdlib = stdlib_modules()

    third_party = sorted(
        x for x in imports
        if x not in local and x not in stdlib
    )

    pip_names = [to_pip_name(x) for x in third_party]

    runtime = []
    dev = []

    for name in pip_names:
        key = name.lower().replace("_", "-")
        if key in DEV_DEPS:
            dev.append(pinned_req(name))
        else:
            runtime.append(pinned_req(name))

    # Always ensure pytest in dev for test runs
    if not any(r.lower().startswith("pytest") for r in dev):
        dev.append(pinned_req("pytest"))

    runtime = sorted(set(runtime), key=str.lower)
    dev = sorted(set(dev), key=str.lower)

    # Write requirements.txt
    REQ.write_text("\n".join(runtime) + ("\n" if runtime else ""), encoding="utf-8")

    # Write requirements-dev.txt
    dev_text = ["-r requirements.txt"] + dev
    REQ_DEV.write_text("\n".join(dev_text) + "\n", encoding="utf-8")

    print(f"[PATCH] requirements.txt written ({len(runtime)} pkgs)")
    print(f"[PATCH] requirements-dev.txt written ({len(dev)} dev pkgs)")

def patch_readme() -> None:
    if not README.exists():
        print(f"[WARN] README not found: {README}")
        return

    text = README.read_text(encoding="utf-8", errors="replace")

    badge = f"![Tests](https://github.com/{REPO_OWNER}/{REPO_NAME}/actions/workflows/tests.yml/badge.svg)"
    if badge not in text:
        # insert after first H1
        lines = text.splitlines()
        out = []
        inserted = False
        for i, line in enumerate(lines):
            out.append(line)
            if not inserted and re.match(r"^#\s+\S+", line):
                out.append("")
                out.append(badge)
                inserted = True
        text = "\n".join(out) + "\n"
        print("[PATCH] README: badge inserted.")

    support_block = r"""
## Support

- **OS:** Windows (PowerShell), macOS, Linux
- **Python:** 3.13+
- **Quick check:** `python -B -m pytest -q`
""".lstrip()

    limitations_block = r"""
## Known limitations

- **1 skipped is expected** in the minimal release build:
  - Some optional/compatibility components are intentionally excluded.
  - Run `python -B -m pytest -q` after installing full dependencies if you want the full suite.
""".lstrip()

    if "## Support" not in text:
        text = text.rstrip() + "\n\n" + support_block + "\n"
        print("[PATCH] README: Support section appended.")

    if "## Known limitations" not in text:
        text = text.rstrip() + "\n\n" + limitations_block + "\n"
        print("[PATCH] README: Known limitations section appended.")

    README.write_text(text, encoding="utf-8")

def write_workflow() -> None:
    wf = f"""name: Tests

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
    runs-on: ${{{{ matrix.os }}}}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{{{ matrix.python-version }}}}
      - name: Install
        run: |
          python -m pip install -U pip
          python -m pip install -r requirements-dev.txt
      - name: Test (Release Check)
        run: |
          python -B -m pytest -q
"""
    WF.write_text(wf, encoding="utf-8")
    print("[PATCH] .github/workflows/tests.yml written.")

def write_release_template() -> None:
    tpl = """# Release Notes

## Summary
- 

## Highlights
- 

## Test Status (Release Check)
- Command: `python -B -m pytest -q`
- Result: `53 passed, 1 skipped` (update numbers if changed)

## Compatibility
- Windows (PowerShell) + Python 3.13
- Ubuntu + Python 3.13

## Breaking changes
- None

## Notes
- 
"""
    RELEASE_TPL.write_text(tpl, encoding="utf-8")
    print("[PATCH] .github/RELEASE_TEMPLATE.md written.")

def main() -> None:
    write_requirements()
    patch_readme()
    write_workflow()
    write_release_template()
    print("[DONE] Release pack complete.")

if __name__ == "__main__":
    main()
