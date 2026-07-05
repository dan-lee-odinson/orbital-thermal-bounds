"""B7: the end-to-end example runs cleanly -- the full path when CoolProp is present, and a
guarded exit-0 skip when it is not (so the numpy-only CI 'run examples' job stays green)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "04_chip_to_radiator.py"


def test_example_04_runs_cleanly():
    r = subprocess.run([sys.executable, str(_EXAMPLE)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    pytest.importorskip("CoolProp", reason="numpy-only path only reaches the guarded skip")
    # with CoolProp present, the example walks the full Stage-1 path
    assert "modeled component mass (incomplete Stage-1 accounting)" in r.stdout
    assert "rank-eligible" in r.stdout
    assert "solved outputs" in r.stdout
