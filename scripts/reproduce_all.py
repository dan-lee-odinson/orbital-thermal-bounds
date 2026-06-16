#!/usr/bin/env python3
"""One-command reproduction of the orbital-thermal-bounds published artifacts.

Runs, in order:
  1. the three numerical verification suites (verify_suite, verify_paper3,
     verify_ai1);
  2. the package test suite (pytest); and
  3. regeneration of the figures and the ammonia property table.

Steps whose optional dependency is missing (matplotlib for the figures, CoolProp
for the ammonia table) are SKIPPED with a notice rather than failing, so this is
useful in a minimal numpy-only install as well as a full one.

Exit status is 0 only if every step that ran PASSED; any failure yields a
non-zero exit, so this can gate CI.

Usage:
    python scripts/reproduce_all.py            # everything available
    python scripts/reproduce_all.py --quick    # verification + tests only
    python scripts/reproduce_all.py --list     # list the steps and exit
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _have(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


class Step:
    def __init__(self, name, argv, *, cwd=None, needs=None):
        self.name = name
        self.argv = argv
        self.cwd = cwd or REPO_ROOT
        self.needs = needs  # optional module required at runtime, or None


def build_steps(quick: bool) -> list[Step]:
    py = [sys.executable]
    steps = [
        Step("verify_suite (theory bounds)", py + ["verify_suite.py"]),
        Step("verify_paper3 (edge-on +6.35 K)", py + ["verify_paper3.py"]),
        Step("verify_ai1 (AI1 design point)", py + ["verify_ai1.py"],
             cwd=REPO_ROOT / "companion"),
        Step("pytest (package test suite)", py + ["-m", "pytest", "-q"]),
    ]
    if not quick:
        steps += [
            Step("figure: edge-on geometry",
                 py + ["scripts/plot_edge_on_geometry.py"], needs="matplotlib"),
            Step("figure: effective sink vs orbit",
                 py + ["scripts/plot_effective_sink.py"], needs="matplotlib"),
            Step("figure: McCalip beta correction",
                 py + ["scripts/plot_mccalip_correction.py"], needs="matplotlib"),
            Step("figure: transient temperature",
                 py + ["scripts/plot_transient.py"], needs="matplotlib"),
            Step("table: ammonia properties",
                 py + ["scripts/generate_ammonia_table.py"], needs="CoolProp"),
        ]
    return steps


def check_version() -> None:
    try:
        from importlib.metadata import version
        v = version("orbital-thermal")
    except Exception:
        print("!  orbital-thermal is not installed. Run: pip install -e .")
        return
    flag = "" if v == "1.0.0" else "   (verify_paper3.py is pinned to 1.0.0)"
    print(f"   orbital-thermal == {v}{flag}")


def run(steps: list[Step]) -> list[tuple[str, str, float]]:
    width = max(len(s.name) for s in steps)
    results = []
    for s in steps:
        if s.needs and not _have(s.needs):
            print(f"SKIP  {s.name:<{width}}  (needs {s.needs})")
            results.append((s.name, "SKIP", 0.0))
            continue
        print(f"RUN   {s.name} ...", flush=True)
        t0 = time.time()
        proc = subprocess.run(s.argv, cwd=s.cwd)
        dt = time.time() - t0
        status = "PASS" if proc.returncode == 0 else "FAIL"
        print(f"{status}  {s.name:<{width}}  ({dt:.1f}s)")
        results.append((s.name, status, dt))
    return results


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true",
                    help="verification + tests only; skip figure/table regeneration")
    ap.add_argument("--list", action="store_true", help="list the steps and exit")
    args = ap.parse_args()

    steps = build_steps(args.quick)
    if args.list:
        for s in steps:
            extra = f"   (needs {s.needs})" if s.needs else ""
            print(f"  {s.name}{extra}")
        return 0

    print(f"Reproducing orbital-thermal-bounds from {REPO_ROOT}")
    check_version()
    print()
    results = run(steps)

    print("\n==================== summary ====================")
    for name, status, dt in results:
        tail = "skipped" if status == "SKIP" else f"{dt:.1f}s"
        print(f"  {status:<4}  {name}  ({tail})")
    npass = sum(r[1] == "PASS" for r in results)
    nfail = sum(r[1] == "FAIL" for r in results)
    nskip = sum(r[1] == "SKIP" for r in results)
    print(f"\n{npass} passed, {nfail} failed, {nskip} skipped")
    if nfail:
        print("REPRODUCTION FAILED")
        return 1
    print("REPRODUCTION OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
