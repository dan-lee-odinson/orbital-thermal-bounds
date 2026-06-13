#!/usr/bin/env python3
"""Enforce oracle-freeze (audit re-review P2-e).

Two independent checks, run in CI:

1. SHA-256 pin -- the committed vendored source (math.js, generate_oracle.js) and
   the frozen oracle (expected_outputs.json) must match the SHA-256 values in
   PINS.json. This catches ANY edit to the frozen artifacts, which is the actual
   "never edited to make a test pass" guarantee for a snapshot.
2. Reproducibility -- regenerate the oracle from the vendored math.js with Node and
   compare to the committed file SEMANTICALLY: parsed numbers must agree to a tight
   relative tolerance, ignoring environment-dependent _meta fields (node_version,
   generated_on) and V8's version-dependent float text formatting. (A byte-for-byte
   compare is brittle: the same float64 serializes with different digit counts
   across Node/V8 versions.)

Exit code is nonzero on any mismatch. Requires Node on PATH for check 2; if Node is
absent the reproducibility check is skipped with a warning (the SHA pin still runs).
"""

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PINS = json.loads((HERE / "PINS.json").read_text())
VOLATILE_META = {"node_version", "generated_on"}


def check_sha256() -> list[str]:
    errs = []
    for name, want in PINS["sha256"].items():
        got = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        if got != want:
            errs.append(f"SHA-256 mismatch for {name}: got {got}, pinned {want}")
    return errs


def _diff_numbers(a, b, path=""):
    errs = []
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            errs.append(f"{path}: key set differs")
        for k in set(a) & set(b):
            errs += _diff_numbers(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            errs.append(f"{path}: length {len(a)} != {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            errs += _diff_numbers(x, y, f"{path}[{i}]")
    elif isinstance(a, bool) or isinstance(b, bool):
        if a != b:
            errs.append(f"{path}: {a!r} != {b!r}")
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12):
            errs.append(f"{path}: {a!r} !~= {b!r}")
    else:
        if a != b:
            errs.append(f"{path}: {a!r} != {b!r}")
    return errs


def _strip_volatile(meta):
    return {k: v for k, v in meta.items() if k not in VOLATILE_META}


def check_reproducible():
    """(errors, ran). Regenerate the oracle from the vendored math.js and compare
    semantically. If Node is unavailable: skip (warn) normally, or fail when strict
    (ORACLE_REQUIRE_EXTERNAL=1) -- audit re-review P2-3."""
    strict = os.environ.get("ORACLE_REQUIRE_EXTERNAL") == "1"
    if shutil.which("node") is None:
        msg = "node not found; cannot regenerate the oracle"
        if strict:
            return ([f"regeneration required but {msg} (ORACLE_REQUIRE_EXTERNAL=1)"], False)
        print(f"WARNING: skipping regeneration -- {msg} (SHA pins still enforced)")
        return ([], False)
    out = subprocess.run(["node", "generate_oracle.js"], cwd=HERE,
                         capture_output=True, text=True)
    if out.returncode != 0:
        return ([f"node generate_oracle.js failed: {out.stderr.strip()}"], True)
    regen = json.loads(out.stdout)
    committed = json.loads((HERE / "expected_outputs.json").read_text())
    regen["_meta"] = _strip_volatile(regen.get("_meta", {}))
    committed["_meta"] = _strip_volatile(committed.get("_meta", {}))
    return (_diff_numbers(regen, committed, "oracle"), True)


def check_external():
    """(errors, ran). Attest the vendored math.js against the raw blob at the recorded
    EXTERNAL pinned commit (not self-referential). Network-lenient by default; set
    ORACLE_REQUIRE_EXTERNAL=1 to make an unreachable source a hard failure. Never
    reports a match unless the fetch actually ran (audit re-review P2-3)."""
    strict = os.environ.get("ORACLE_REQUIRE_EXTERNAL") == "1"
    repo = PINS.get("source_repo")
    path = PINS.get("source_path")
    if not (repo and path):
        return (["PINS.json missing source_repo/source_path for external attestation"], True)
    url = f"https://raw.githubusercontent.com/{repo}/{PINS['pinned_commit']}/{path}"
    try:
        data = urllib.request.urlopen(url, timeout=30).read()
    except Exception as exc:  # network/proxy/offline
        msg = f"could not fetch external blob ({type(exc).__name__}: {exc}); {url}"
        if strict:
            return ([f"external attestation required but {msg}"], False)
        print(f"WARNING: skipping external attestation -- {msg}")
        return ([], False)
    ext_sha = hashlib.sha256(data).hexdigest()
    want = PINS["sha256"].get("math.js")
    if ext_sha != want:
        return ([f"vendored math.js SHA {want} != external blob SHA {ext_sha} at "
                 f"{PINS['pinned_commit']}"], True)
    return ([], True)


def main() -> int:
    checks = [("SHA-256 pins", check_sha256(), True)]
    checks.append(("oracle regeneration", *check_reproducible()))
    checks.append(("external attestation", *check_external()))
    errs = [e for _, el, _ in checks for e in el]
    print("oracle-freeze checks:")
    for name, el, ran in checks:
        print(f"  - {name}: {'FAILED' if el else ('OK' if ran else 'SKIPPED')}")
    if errs:
        print("ORACLE-FREEZE VIOLATION:")
        for e in errs:
            print("  -", e)
        return 1
    parts = ["SHA-256 pins match"]
    parts.append("regeneration reproduces the oracle" if checks[1][2]
                 else "regeneration SKIPPED (node unavailable)")
    parts.append("external blob attested" if checks[2][2]
                 else "external attestation SKIPPED (no network)")
    print("oracle-freeze OK: " + "; ".join(parts) + ". Enforces repository "
          "consistency, accidental-drift detection, and (when it actually runs) "
          "external-blob attestation; not, by itself, proof the oracle was never "
          "historically edited.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
