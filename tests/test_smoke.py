"""Smoke tests: a handful of canonical published anchors.

These only prove the package installs and the core functions reproduce
known values. The full published-results regression suite is a separate
task (tests/test_published_results.py) and supersedes nothing here --
smoke tests stay fast and minimal.
"""

import pytest

from orbital_thermal import (
    area_ratio,
    effective_sink_temperature,
    equilibrium_temperature,
    net_flux,
    radiative_capacity,
    required_area,
)


def test_corollary_1_2_one_megawatt_at_room_temperature():
    # 1 MW at 293 K, emissivity 0.91, zero sink -> 2,630 m^2 emitting area.
    assert required_area(1e6, 293.0, 0.91) == pytest.approx(2630.0, abs=0.5)


def test_corollary_1_1_exact_area_ratio():
    # 293 -> 600 K with T_s = 220 K: exactly 6697760000/264604779 (~25.312).
    assert area_ratio(293.0, 600.0, 220.0) == pytest.approx(
        6697760000 / 264604779, rel=1e-12
    )


def test_ai1_sustained_two_sided_primary_operating_point():
    # 120 kW through 220 m^2 emitting, emissivity 0.91, T_s^eff = 220 K.
    assert equilibrium_temperature(120e3, 220.0, 0.91, 220.0) == pytest.approx(
        337.1004, abs=1e-3
    )


def test_capacity_inverts_equilibrium_temperature():
    # The two companion-paper functions must be exact inverses.
    T = equilibrium_temperature(150e3, 220.0, 0.91, 220.0)
    assert radiative_capacity(T, 220.0, 0.91, 220.0) == pytest.approx(
        150e3, rel=1e-12
    )


def test_effective_sink_quarter_power_law():
    assert effective_sink_temperature(1.0, 220.0) == 220.0
    # F = 1/16 -> factor (1/16)^(1/4) = 1/2.
    assert effective_sink_temperature(0.0625, 220.0) == pytest.approx(110.0)


def test_rejects_nonphysical_inputs():
    with pytest.raises(ValueError):
        net_flux(200.0, 0.91, T_sink=220.0)  # radiator colder than sink
    with pytest.raises(ValueError):
        net_flux(300.0, 1.5)  # emissivity above 1
    with pytest.raises(ValueError):
        required_area(-5.0, 293.0, 0.91)  # negative heat load



def test_version_is_single_sourced():
    # __version__ must come from the installed package metadata (pyproject),
    # not a hardcoded string that can drift (audit item 11a).
    import orbital_thermal
    from importlib.metadata import version
    assert orbital_thermal.__version__ == version("orbital-thermal")


def test_sigma_sb_is_binary64_si_derived():
    # SIGMA_SB is the binary64 of sigma = 2 pi^5 k_B^4 / (15 h^3 c^2) using the
    # exact 2019-SI defining constants -- not the truncated CODATA-printed value
    # (audit re-review P2-c).
    import math
    from orbital_thermal.constants import SIGMA_SB
    kB, h, c = 1.380649e-23, 6.62607015e-34, 299792458.0
    sigma_si = 2 * math.pi**5 * kB**4 / (15 * h**3 * c**2)
    assert SIGMA_SB == pytest.approx(sigma_si, rel=1e-12)
    assert SIGMA_SB != 5.670374419e-8
    assert abs(SIGMA_SB - 5.670374419e-8) / SIGMA_SB == pytest.approx(3.25e-11, rel=0.1)


def test_standalone_verify_suites_lock_full_precision_sigma():
    # Audit r6 P3: the standalone manuscript suites must independently use the full
    # binary64 SI-derived sigma, not the truncated 5.670374419e-8 literal, so they
    # lock the exact-sigma ground rule rather than relying on the package tests.
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    for rel in ("verify_suite.py", "companion/verify_ai1.py"):
        text = (root / rel).read_text()
        assert "5.670374419184429e-8" in text, rel
        assert "sigma = 5.670374419e-8" not in text, rel
    wl = (root / "verify_suite.wl").read_text()
    assert "5670374419184429*10^-23" in wl
    assert "5670374419*10^-17" not in wl
