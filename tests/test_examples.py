"""B7: the end-to-end example runs cleanly -- the full path when CoolProp is present, and a
guarded exit-0 skip when it is not (so the numpy-only CI 'run examples' job stays green)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "04_chip_to_radiator.py"


def _child_env() -> dict[str, str]:
    """Environment for the example subprocess, carrying this interpreter's import path.

    A subprocess does not inherit pytest's ``pythonpath`` setting, so from a bare tree
    with nothing installed the child would fail to import ``orbital_thermal`` even
    though the parent test session imports it fine. Passing ``sys.path`` through
    ``PYTHONPATH`` makes the child resolve the package the same way the parent did.

    Prepended rather than replacing any inherited ``PYTHONPATH``, so a caller's own
    setting still applies but cannot shadow the package under test.
    """
    inherited = os.environ.get("PYTHONPATH", "")
    entries = [p for p in sys.path if p]
    if inherited:
        entries.append(inherited)
    return {**os.environ, "PYTHONPATH": os.pathsep.join(entries)}


def test_example_04_runs_cleanly():
    r = subprocess.run(
        [sys.executable, str(_EXAMPLE)], capture_output=True, text=True, env=_child_env()
    )
    assert r.returncode == 0, r.stderr
    pytest.importorskip("CoolProp", reason="numpy-only path only reaches the guarded skip")
    # with CoolProp present, the example walks the full Stage-1 path
    assert "modeled component mass (incomplete Stage-1 accounting)" in r.stdout
    assert "rank-eligible" in r.stdout
    assert "solved outputs" in r.stdout
