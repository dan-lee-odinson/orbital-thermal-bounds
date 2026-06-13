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
