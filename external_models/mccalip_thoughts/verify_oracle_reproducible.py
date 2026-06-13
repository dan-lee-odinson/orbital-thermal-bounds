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


def check_reproducible() -> list[str]:
    if shutil.which("node") is None:
        print("WARNING: node not found; skipping reproducibility check (SHA pin still enforced)")
        return []
    out = subprocess.run(["node", "generate_oracle.js"], cwd=HERE,
                         capture_output=True, text=True)
    if out.returncode != 0:
        return [f"node generate_oracle.js failed: {out.stderr.strip()}"]
    regen = json.loads(out.stdout)
    committed = json.loads((HERE / "expected_outputs.json").read_text())
    regen["_meta"] = _strip_volatile(regen.get("_meta", {}))
    committed["_meta"] = _strip_volatile(committed.get("_meta", {}))
    return _diff_numbers(regen, committed, "oracle")


def check_external() -> list[str]:
    """Attest that the vendored math.js equals the file at the recorded EXTERNAL
    pinned commit, so oracle-freeze is not purely self-referential (audit re-review
    P2-8). Fetches the raw blob from GitHub at PINS['pinned_commit']. Network-lenient:
    on a fetch error it warns and skips (set ORACLE_REQUIRE_EXTERNAL=1 to make an
    unreachable external source a hard failure, e.g. for a release gate)."""
    repo = PINS.get("source_repo")
    path = PINS.get("source_path")
    if not (repo and path):
        return ["PINS.json missing source_repo/source_path for external attestation"]
    url = f"https://raw.githubusercontent.com/{repo}/{PINS['pinned_commit']}/{path}"
    try:
        data = urllib.request.urlopen(url, timeout=30).read()
    except Exception as exc:  # network/proxy/offline
        msg = f"could not fetch external blob ({type(exc).__name__}: {exc}); {url}"
        if os.environ.get("ORACLE_REQUIRE_EXTERNAL") == "1":
            return [f"external attestation required but {msg}"]
        print(f"WARNING: skipping external attestation -- {msg}")
        return []
    ext_sha = hashlib.sha256(data).hexdigest()
    want = PINS["sha256"].get("math.js")
    if ext_sha != want:
        return [f"vendored math.js SHA {want} != external blob SHA {ext_sha} at "
                f"{PINS['pinned_commit']}"]
    print(f"external attestation OK: vendored math.js matches {repo}@"
          f"{PINS['pinned_commit'][:12]}:{path}")
    return []


def main() -> int:
    errs = check_sha256() + check_reproducible() + check_external()
    if errs:
        print("ORACLE-FREEZE VIOLATION:")
        for e in errs:
            print("  -", e)
        return 1
    print("oracle-freeze OK: SHA-256 pins match; regeneration reproduces the oracle "
          "(semantic, version-independent); vendored source matches the external "
          "pinned commit. This enforces repository consistency, accidental-drift "
          "detection, and external-blob attestation -- it is not, by itself, proof "
          "that the oracle was historically never edited.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
