"""Tests for the one-node transient radiator model and averaging bias.

The integrator is checked against the analytic steady state it must reproduce in
the constant-sink limit, against energy-conserving periodicity, and for the
physically required monotonic damping with thermal mass.
"""

import numpy as np
import pytest

from orbital_thermal import transient as tr
from orbital_thermal import sink as sink_mod
from orbital_thermal.constants import SIGMA_SB

EPS = 0.91
Q_LOAD = EPS * SIGMA_SB * (337.1**4 - 220.0**4)

SIM = dict(n_orbits=25, steps_per_orbit=720)


class TestSteadyState:
    def test_reproduces_paper_operating_point(self):
        assert tr.steady_state_temperature(Q_LOAD, 220.0, EPS) == pytest.approx(337.1, abs=0.05)

    def test_matches_stefan_boltzmann_closed_form(self):
        T = tr.steady_state_temperature(500.0, 250.0, EPS)
        assert EPS * SIGMA_SB * (T**4 - 250.0**4) == pytest.approx(500.0, rel=1e-12)


class TestTimeConstant:
    def test_positive_and_linear_in_capacity(self):
        t1 = tr.thermal_time_constant(4000.0, 337.0, EPS)
        t2 = tr.thermal_time_constant(8000.0, 337.0, EPS)
        assert t1 > 0
        assert t2 == pytest.approx(2 * t1, rel=1e-12)


class TestTransient:
    def test_flat_sink_converges_to_analytic_steady(self):
        t, T, Ts = tr.simulate(550, 90.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM)
        steady = tr.steady_state_temperature(Q_LOAD, float(Ts.mean()), EPS)
        assert np.ptp(Ts) == pytest.approx(0.0, abs=1e-9)
        assert T.mean() == pytest.approx(steady, abs=1e-3)
        assert (T.max() - T.min()) == pytest.approx(0.0, abs=1e-3)

    def test_periodic_closure(self):
        t, T, Ts = tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM)
        assert T[0] == pytest.approx(T[-1], abs=1e-3)

    def test_swing_decreases_with_thermal_mass(self):
        swings = []
        for C in (2000.0, 8000.0, 40000.0):
            _, T, _ = tr.simulate(550, 0.0, Q_LOAD, C, tilt_deg=0, **SIM)
            swings.append(T.max() - T.min())
        assert swings[0] > swings[1] > swings[2]

    def test_panel_hotter_than_sink(self):
        _, T, Ts = tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM)
        assert np.all(T > Ts)


class TestAveragingBias:
    def test_mean_bias_is_nonpositive(self):
        # At periodic steady state <T^4> = T_steady^4; since x^(1/4) is concave
        # the arithmetic mean is <= T_steady, so the averaged-sink steady solution
        # does NOT under-predict the mean. bias_K must be <= 0 up to numerical
        # slack (and only marginally below, since the ripple is small).
        b = tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM)
        assert b["bias_K"] <= 1e-3
        assert b["bias_K"] > -0.5

    def test_periodic_steady_state_energy_balance(self):
        # Exact identity at periodic SS: <T^4> = q_load/(eps*sigma) + <Tsink^4>,
        # equivalently <T^4> = T_steady^4. Holds across thermal masses.
        import numpy as np
        for C in (2000.0, 8000.0, 40000.0):
            _, T, Ts = tr.simulate(550, 0.0, Q_LOAD, C, tilt_deg=0, **SIM)
            lhs = float(np.mean(T[:-1] ** 4))
            rhs = Q_LOAD / (EPS * SIGMA_SB) + float(np.mean(Ts[:-1] ** 4))
            assert lhs == pytest.approx(rhs, rel=1e-5)
            steady = tr.steady_state_temperature(
                Q_LOAD, float(np.mean(Ts[:-1] ** 4)) ** 0.25, EPS)
            assert lhs ** 0.25 == pytest.approx(steady, abs=1e-3)

    def test_peak_exceeds_steady(self):
        b = tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM)
        assert b["peak_excess_over_steady_K"] > 1.0
        assert b["transient_peak_K"] > b["steady_avg_sink_K"]

    def test_no_bias_or_swing_at_terminator(self):
        b = tr.averaging_bias(550, 90.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM)
        assert b["swing_K"] == pytest.approx(0.0, abs=1e-3)
        assert b["bias_K"] == pytest.approx(0.0, abs=1e-3)
        assert b["peak_excess_over_steady_K"] == pytest.approx(0.0, abs=1e-3)

    def test_sink_avg_matches_sink_module(self):
        b = tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM)
        ref = sink_mod.orbit_averaged_sink(550, 0.0, tilt_deg=0)
        assert b["sink_avg_K"] == pytest.approx(ref, abs=0.2)
