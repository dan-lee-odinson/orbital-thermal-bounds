"""External reference case: Biswas/Suncatcher v1.2 Part I passive thermal baseline.

Pins the byte-identical vendored upstream script and its reproduced outputs so CI fails if
either drifts. This is an EXTERNAL REFERENCE ONLY: not validation of the Biswas/Suncatcher
physics, not a comparison to or ranking against orbital-thermal-bounds, and not harmonized to
orbital-thermal-bounds conventions (harmonization is Track-R milestone R3). See
external_models/biswas_suncatcher/ (PINS.json, provenance.md, R1-reproduction.md).
"""
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

# Vendored, byte-identical copy of report-1/report_one_thermal.py from the pinned upstream
# release v1.2 (commit 23053beeff53); the SHA-256 below is the pinned upstream file's hash.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_VENDORED = _REPO_ROOT / "external_models" / "biswas_suncatcher" / "report_one_thermal.py"
_PINNED_SHA256 = "52b2f7af90e99e9aa2bb4c4de479c03ef742622c9a153d7867f1bfbeece02d8c"

# Reproduced R1 baseline, in the author's OWN conventions (see R1-reproduction.md).
_TOL_C = 0.05  # temperature tolerance [C]
_TOL_R = 0.001  # resistance tolerance [K/W]


def _load_script():
    """Import the vendored script by file path.

    Its main() does not run on import (guarded by __name__ == "__main__"), so importing has
    no side effects; it only exposes the module's functions and constants.
    """
    spec = importlib.util.spec_from_file_location("biswas_report_one_thermal", _VENDORED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_vendored_script_byte_identical():
    """The vendored script must stay byte-identical to the pinned upstream file.

    Verifies the SHA-256 of the file *as checked out on this platform*. The pinned
    upstream file is LF-only; a CRLF checkout (git autocrlf on Windows) changes the
    raw bytes and breaks the hash. `.gitattributes` pins this path to `text eol=lf`
    so the checkout is LF everywhere; the explicit CRLF assertion below turns an
    otherwise-opaque hash mismatch into an actionable line-ending diagnostic.
    """
    raw = _VENDORED.read_bytes()
    assert b"\r\n" not in raw, (
        "vendored script was checked out with CRLF line endings; it must be LF. "
        "Confirm `.gitattributes` pins it to `text eol=lf`, then re-normalize with "
        "`git add --renormalize external_models/biswas_suncatcher/report_one_thermal.py`."
    )
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == _PINNED_SHA256


def test_vendored_script_selfcheck_passes():
    """Run the byte-identical script unchanged; its built-in self-check must pass.

    A short timeout guards CI: the script is dependency-free (stdlib only) and returns in
    well under a second.
    """
    result = subprocess.run(
        [sys.executable, str(_VENDORED)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "checks ok" in result.stdout


def test_reproduced_reference_values():
    """Reproduced Part I baseline (external reference), in Biswas-script convention."""
    module = _load_script()

    # The Biswas script's total MODELED THERMAL LOAD = 1.2 kW compute (4 x 300 W TPUs)
    # + 150 W avionics + 100 W parasitic = 1450 W. The 1450 W is the total thermal load the
    # radiator must reject; it is NOT a change to the 1.2 kW compute input. Both are asserted
    # so the distinction is explicit and machine-checked.
    compute, total_load = module.heat_load()
    assert compute == 1200.0  # 4 x 300 W TPU compute input
    assert total_load == 1450.0  # total modeled thermal load (compute + avionics + parasitic)

    t_rad = module.radiator_temperature(total_load, module.AREA)
    assert abs(t_rad - 21.34) <= _TOL_C

    r_before, _ = module.resistance_chain()
    r_after, _ = module.resistance_chain(r_tim=0.020, r_pipe=0.050)
    assert abs(r_before - 0.350) <= _TOL_R
    assert abs(r_after - 0.300) <= _TOL_R

    t_j = module.junction_temp(t_rad, module.P_TPU, r_after)
    assert abs(t_j - 111.3) <= _TOL_C

    d_r = 0.080 * (8 / 7 - 1)  # one heat pipe out (8 -> 7)
    t_j_fail = module.junction_temp(t_rad, module.P_TPU, r_after + d_r)
    assert abs(t_j_fail - 114.8) <= _TOL_C
