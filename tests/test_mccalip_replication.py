"""Replication tests: Python port vs the frozen McCalip Node oracle.

ORACLE-FREEZE RULE: ``expected_outputs.json`` is generated from McCalip's pinned
JavaScript (commit d1e4238) and is never edited to make a test pass. If his model
changes, the oracle is regenerated wholesale and provenance.md is updated.

These tests assert three separable things:
  * Replication  -- the port reproduces his JS numbers to floating-point roundoff.
  * Verification -- where his model uses approximations/constants that differ from
    the exact core package, the divergence is bounded and explained (not hidden).
"""

import hashlib
import json
from pathlib import Path

import pytest

from orbital_thermal import mccalip_replication as mc
from orbital_thermal import environment as env
from orbital_thermal.constants import SIGMA_SB

ORACLE_PATH = (Path(__file__).resolve().parents[1]
               / "external_models" / "mccalip_thoughts" / "expected_outputs.json")


def _overrides(label):
    if label == "defaults":
        return {}
    if label.startswith("beta_"):
        return {"betaAngle": float(label.split("_")[1])}
    if label.startswith("alt_"):
        return {"orbitalAltitudeKm": float(label.split("_")[1].replace("km", ""))}
    if label.startswith("eRad_"):
        return {"emissivityRad": float(label.split("_")[1])}
    raise ValueError(label)


@pytest.fixture(scope="module")
def oracle():
    return json.loads(ORACLE_PATH.read_text())


class TestReplication:
    def test_oracle_present_and_pinned(self, oracle):
        assert oracle["_meta"]["pinned_commit"] == "d1e4238d3d3f4924e5ca65bafbd4ba5b39af2eb8"
        assert len(oracle["cases"]) == 11

    def test_every_field_matches_oracle(self, oracle):
        for case in oracle["cases"]:
            got = mc.run_case(_overrides(case["label"]))
            for section in ("geometry", "thermal", "orbital"):
                for k, exp in case[section].items():
                    g = got[section][k]
                    if isinstance(exp, bool):
                        assert g == exp, f"{case['label']}.{section}.{k}"
                    else:
                        assert g == pytest.approx(exp, rel=1e-9, abs=1e-9), \
                            f"{case['label']}.{section}.{k}"
            assert got["breakeven_launch_cost_per_kg"] == pytest.approx(
                case["breakeven_launch_cost_per_kg"], rel=1e-9)

    def test_default_eqtemp_anchor(self, oracle):
        got = mc.run_case({})["thermal"]["eqTempK"]
        assert got == pytest.approx(oracle["cases"][0]["thermal"]["eqTempK"], rel=1e-9)
        assert got == pytest.approx(335.75, abs=0.01)


class TestVerificationGap:
    """Where McCalip's model differs from the exact core package -- bounded and
    explained, not silently reconciled."""

    def test_nadir_view_factor_agrees_with_core(self):
        for alt in (400.0, 550.0, 800.0):
            assert mc.nadir_view_factor(alt) == pytest.approx(
                env.nadir_view_factor(alt), rel=1e-12)

    def test_sigma_convention_differs(self):
        assert mc.SIGMA != SIGMA_SB
        assert mc.SIGMA == pytest.approx(SIGMA_SB, rel=1e-3)

    def test_tilted_vf_approximation_departs_from_exact(self):
        alt, tilt = 550.0, 90.0
        approx = mc._tilted_vf_from_cos(alt, 0.0)
        exact = env.sphere_view_factor(alt, 90.0)
        assert abs(approx - exact) > 0.10



class TestOracleFreeze:
    """Enforce oracle-freeze (audit re-review P2-e): the vendored source and frozen
    oracle must match pinned SHA-256 values, and the recorded commit must be the
    full 40-char SHA. The CI job additionally regenerates the oracle from math.js
    and compares it semantically (see verify_oracle_reproducible.py)."""

    def _pins(self):
        return json.loads((ORACLE_PATH.parent / "PINS.json").read_text())

    def test_pinned_sha256_unchanged(self):
        pins = self._pins()
        for name, want in pins["sha256"].items():
            got = hashlib.sha256((ORACLE_PATH.parent / name).read_bytes()).hexdigest()
            assert got == want, f"{name} SHA-256 changed -- oracle-freeze violation"

    def test_meta_records_full_commit_sha(self, oracle):
        pins = self._pins()
        assert len(pins["pinned_commit"]) == 40
        assert oracle["_meta"]["pinned_commit"] == pins["pinned_commit"]
