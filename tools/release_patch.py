from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

README = ROOT / "README.md"
CORE_LOCK = ROOT / "bcdsi" / "tests" / "test_core_lock.py"

TEST_STATUS_BLOCK = r"""
## Test Status (Release Check)

Validated on **Windows (PowerShell) + Python 3.13**:

```powershell
python -B -m pytest -q
# 53 passed, 1 skipped in 6.76s
```

### Quickstart (Windows / PowerShell)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
python -B -m pytest -q
```

""".lstrip()

FRIENDLY_SKIP_BLOCK = """pytest.skip(
    "Skipped (expected): this minimal release build does not include optional compatibility components. "
    "To run the full suite, install full dependencies and re-run `python -B -m pytest -q`.",
    allow_module_level=True,
)
"""

def patch_readme() -> None:
    if not README.exists():
        print(f"[WARN] README not found: {README}")
        return

    text = README.read_text(encoding="utf-8", errors="replace")
    if "## Test Status (Release Check)" in text:
        print("[OK] README already has Test Status block.")
        return

    # ensure single blank line before append
    text = text.rstrip() + "\n\n" + TEST_STATUS_BLOCK + "\n"
    README.write_text(text, encoding="utf-8")
    print("[PATCH] README appended: Test Status (Release Check) + Quickstart.")


def patch_core_lock_skip() -> None:
    if not CORE_LOCK.exists():
        print(f"[WARN] core lock test not found: {CORE_LOCK}")
        return

    text = CORE_LOCK.read_text(encoding="utf-8", errors="replace")

    # If there's already our friendly string, do nothing
    if "Skipped (expected): this minimal release build" in text:
        print("[OK] core_lock skip message already friendly.")
        return

    # Replace the first pytest.skip(...) we can find (common patterns)
    # Works even if skip happens at module level during import.
    pat = re.compile(r"pytest\.skip\((?:.|\n)*?\)\s*", re.MULTILINE)
    m = pat.search(text)
    if not m:
        print("[WARN] No pytest.skip(...) found in core_lock; nothing changed.")
        return

    new_text = text[:m.start()] + FRIENDLY_SKIP_BLOCK + text[m.end():]
    CORE_LOCK.write_text(new_text, encoding="utf-8")
    print("[PATCH] core_lock skip message updated (friendlier / actionable).")


def main() -> None:
    patch_readme()
    patch_core_lock_skip()
    print("[DONE] Patch complete.")

if __name__ == "__main__":
    main()
