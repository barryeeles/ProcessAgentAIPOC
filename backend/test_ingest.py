"""Quick ingestion smoke test — run with: uv run python test_ingest.py"""

import sys
import time

sys.path.insert(0, ".")

from ingestion.pipeline import run_ingestion

t = time.time()
with open("../EPIC.xlsx", "rb") as f:
    main_bytes = f.read()
with open("../EPIC Releases.xlsx", "rb") as f:
    rel_bytes = f.read()

result = run_ingestion(main_bytes, rel_bytes)
elapsed = time.time() - t

print("\n── Ingestion result ──────────────────────────────────")
skip = {"rekey_candidates", "warnings", "epics_active", "epics_initially_closed"}
for k, v in result.items():
    if k not in skip:
        print(f"  {k}: {v}")
print(f"  rekey_candidates: {len(result['rekey_candidates'])}")
print(f"  warnings: {len(result['warnings'])}")
print(f"\nElapsed: {elapsed:.2f}s")

# ── Verify against spec baseline ──────────────────────────────
print("\n── Spec baseline verification ────────────────────────")
checks = [
    ("EPICs in scope (all, incl. historical)", result["epics_in_scope"],      74,   "=="),
    ("EPICs active in dashboard",              result["epics_active"],         None, "info"),
    ("EPICs excluded (historical closed)",     result["epics_initially_closed"], None, "info"),
    ("Capabilities in scope",                 result["capabilities_in_scope"], 371,  "=="),
    ("Features in scope",                     result["features_in_scope"],     598,  "approx"),
    ("Features excluded",                     result["features_excluded"],     2116, "approx"),
]
all_pass = True
for label, actual, expected, mode in checks:
    if mode == "info":
        print(f"  INFO  {label}: {actual}")
        continue
    if mode == "==":
        ok = actual == expected
    else:  # approx: within 5%
        ok = abs(actual - expected) / max(expected, 1) < 0.05
    status = "PASS" if ok else "FAIL"
    if not ok:
        all_pass = False
    print(f"  {status}  {label}: {actual} (expected {expected})")

if result["warnings"]:
    print("\n── Warnings ──────────────────────────────────────────")
    for w in result["warnings"][:10]:
        print(f"  {w}")
    if len(result["warnings"]) > 10:
        print(f"  ... and {len(result['warnings']) - 10} more")

print("\n" + ("ALL CHECKS PASSED" if all_pass else "SOME CHECKS FAILED"))
