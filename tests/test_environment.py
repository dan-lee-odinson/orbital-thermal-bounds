"""Tests for the analytic orbital environment module.

Each function is checked against an independent reference: closed-form special
cases, textbook orbital values, and -- for the exact view factor -- a brute-force
2-D numerical integrator that shares no code with the implementation.
"""

import numpy as np
import pytest

from orbital_thermal import environment as env


# ---------------------------------------------------------------------------
# Orbit geometry
# ---------------------------------------------------------------------------

class TestOrbitGeometry:
    def test_period_550km_is_about_95_minutes(self):
        # LEO at 550 km: ~95.6 min. Independent value from Kepler's third law.
        T = env.orbital_period(550.0)
        assert T / 60.0 == pytest.approx(95.6, abs=0.3)

    def test_velocity_550km_is_about_7_6_kms(self):
        assert env.orbital_velocity(550.0) == pytest.approx(7.59, abs=0.02)

    def test_period_velocity_consistency(self):
        # v * T should equal orbit circumference 2*pi*r.
        for alt in (400.0, 550.0, 800.0):
            r = env.orbital_radius(alt)
            assert env.orbital_velocity(alt) * env.orbital_period(alt) == pytest.approx(
                2 * np.pi * r, rel=1e-12
            )

    def test_higher_orbit_is_slower_and_longer(self):
        assert env.orbital_velocity(800.0) < env.orbital_velocity(400.0)
        assert env.orbital_period(800.0) > env.orbital_period(400.0)

    def test_negative_altitude_rejected(self):
        with pytest.raises(ValueError):
            env.orbital_radius(-10.0)


# ---------------------------------------------------------------------------
# Eclipse
# ---------------------------------------------------------------------------

class TestEclipse:
    def test_leo_beta0_fraction_about_0_37(self):
        # Classic LEO result: ~37% of the orbit in shadow at beta = 0.
        assert env.eclipse_fraction(550.0, 0.0) == pytest.approx(0.372, abs=0.005)

    def test_terminator_orbit_no_eclipse(self):
        # Above beta_critical the orbit is in continuous sun.
        assert env.eclipse_fraction(550.0, 90.0) == 0.0
        assert env.eclipse_fraction(550.0, 89.0) == 0.0

    def test_beta_critical_equals_earth_angular_radius(self):
        bc = env.beta_critical(550.0)
        # Just below: still some eclipse; just above: none.
        assert env.eclipse_fraction(550.0, bc - 0.5) > 0.0
        assert env.eclipse_fraction(550.0, bc + 0.5) == 0.0

    def test_eclipse_monotonic_decreasing_in_beta(self):
        fracs = [env.eclipse_fraction(550.0, b) for b in range(0, 70, 5)]
        assert all(a >= b - 1e-12 for a, b in zip(fracs, fracs[1:]))

    def test_duration_matches_fraction_times_period(self):
        f = env.eclipse_fraction(550.0, 30.0)
        assert env.eclipse_duration(550.0, 30.0) == pytest.approx(
            f * env.orbital_period(550.0), rel=1e-12
        )

    def test_beta_out_of_range_rejected(self):
        with pytest.raises(ValueError):
            env.eclipse_fraction(550.0, -5.0)
        with pytest.raises(ValueError):
            env.eclipse_fraction(550.0, 120.0)


# ---------------------------------------------------------------------------
# View factors
# ---------------------------------------------------------------------------

def _vf_brute(altitude_km, tilt_deg, R_e=env.EARTH_RADIUS_KM, n=2500):
    """Independent brute-force VF: grid integration of cos(alpha)+ over Earth's
    disk. Shares no logic with sphere_view_factor."""
    r = R_e + altitude_km
    theta = np.arcsin(R_e / r)
    gamma = np.radians(tilt_deg)
    psis = np.linspace(0, theta, n)
    phis = np.linspace(0, 2 * np.pi, n, endpoint=False)
    PSI, PHI = np.meshgrid(psis, phis, indexing="ij")
    sx, sz = np.sin(PSI) * np.cos(PHI), np.cos(PSI)
    dz = sx * np.sin(gamma) + sz * np.cos(gamma)
    integrand = np.where(dz > 0, dz, 0.0) * np.sin(PSI)
    return np.sum(integrand) * (theta / (n - 1)) * (2 * np.pi / n) / np.pi


class TestViewFactor:
    def test_nadir_matches_sin_squared_theta(self):
        for alt in (400.0, 550.0, 800.0):
            theta = env.earth_angular_radius(alt)
            assert env.sphere_view_factor(alt, 0.0) == pytest.approx(
                np.sin(theta) ** 2, rel=1e-12
            )

    def test_nadir_matches_mccalip_anchor(self):
        # McCalip's stated VF_nadir = 0.847 at 550 km.
        assert env.nadir_view_factor(550.0) == pytest.approx(0.847, abs=0.001)

    def test_region1_is_exact_cosine_law(self):
        # Below the horizon-crossing tilt, F = cos(tilt) * sin^2(theta) exactly.
        alt, tilt = 550.0, 15.0
        theta = env.earth_angular_radius(alt)
        assert env.sphere_view_factor(alt, tilt) == pytest.approx(
            np.cos(np.radians(tilt)) * np.sin(theta) ** 2, rel=1e-12
        )

    def test_zenith_facing_is_zero(self):
        assert env.sphere_view_factor(550.0, 180.0) == 0.0

    def test_edge_on_is_nonzero_due_to_large_earth(self):
        # At 90deg tilt the plate is edge-on to nadir, but Earth's 67deg angular
        # radius means part of the disk is still above the horizon.
        assert env.sphere_view_factor(550.0, 90.0) > 0.20

    @pytest.mark.parametrize("alt", [400.0, 550.0, 800.0])
    @pytest.mark.parametrize("tilt", [10, 40, 67, 95, 120, 150])
    def test_matches_brute_force_integrator(self, alt, tilt):
        assert env.sphere_view_factor(alt, tilt) == pytest.approx(
            _vf_brute(alt, tilt), abs=3e-4
        )

    def test_monotonic_decreasing_in_tilt(self):
        vals = [env.sphere_view_factor(550.0, t) for t in range(0, 181, 10)]
        assert all(a >= b - 1e-12 for a, b in zip(vals, vals[1:]))

    def test_tilt_out_of_range_rejected(self):
        with pytest.raises(ValueError):
            env.sphere_view_factor(550.0, 200.0)
