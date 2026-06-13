"""Tests for the one-node transient radiator model and averaging bias.

The integrator is checked against the analytic steady state it must reproduce in
the constant-sink limit, against energy-conserving periodicity, and for the
physically required monotonic damping with thermal mass.
"""

import warnings

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
        t, T, Ts = tr.simulate(550, 90.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        steady = tr.steady_state_temperature(Q_LOAD, float(Ts.mean()), EPS)
        assert np.ptp(Ts) == pytest.approx(0.0, abs=1e-9)
        assert T.mean() == pytest.approx(steady, abs=1e-3)
        assert (T.max() - T.min()) == pytest.approx(0.0, abs=1e-3)

    def test_periodic_closure(self):
        t, T, Ts = tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        assert T[0] == pytest.approx(T[-1], abs=1e-3)

    def test_swing_decreases_with_thermal_mass(self):
        swings = []
        for C in (2000.0, 8000.0, 40000.0):
            _, T, _ = tr.simulate(550, 0.0, Q_LOAD, C, tilt_deg=0, **SIM, assume_sun_shielded=True)
            swings.append(T.max() - T.min())
        assert swings[0] > swings[1] > swings[2]

    def test_panel_hotter_than_sink(self):
        _, T, Ts = tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        assert np.all(T > Ts)


class TestAveragingBias:
    def test_mean_bias_is_nonpositive(self):
        # At periodic steady state <T^4> = T_steady^4; since x^(1/4) is concave
        # the arithmetic mean is <= T_steady, so the averaged-sink steady solution
        # does NOT under-predict the mean. bias_K must be <= 0 up to numerical
        # slack (and only marginally below, since the ripple is small).
        b = tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        assert b["bias_K"] <= 1e-3
        assert b["bias_K"] > -0.5

    def test_periodic_steady_state_energy_balance(self):
        # Exact identity at periodic SS: <T^4> = q_load/(eps*sigma) + <Tsink^4>,
        # equivalently <T^4> = T_steady^4. Holds across thermal masses.
        import numpy as np
        for C in (2000.0, 8000.0, 40000.0):
            _, T, Ts = tr.simulate(550, 0.0, Q_LOAD, C, tilt_deg=0, **SIM, assume_sun_shielded=True)
            lhs = float(np.mean(T[:-1] ** 4))
            rhs = Q_LOAD / (EPS * SIGMA_SB) + float(np.mean(Ts[:-1] ** 4))
            assert lhs == pytest.approx(rhs, rel=1e-5)
            steady = tr.steady_state_temperature(
                Q_LOAD, float(np.mean(Ts[:-1] ** 4)) ** 0.25, EPS)
            assert lhs ** 0.25 == pytest.approx(steady, abs=1e-3)

    def test_peak_exceeds_steady(self):
        b = tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        assert b["peak_excess_over_steady_K"] > 1.0
        assert b["transient_peak_K"] > b["steady_avg_sink_K"]

    def test_no_bias_or_swing_at_terminator(self):
        b = tr.averaging_bias(550, 90.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        assert b["swing_K"] == pytest.approx(0.0, abs=1e-3)
        assert b["bias_K"] == pytest.approx(0.0, abs=1e-3)
        assert b["peak_excess_over_steady_K"] == pytest.approx(0.0, abs=1e-3)

    def test_raises_on_nonconvergence(self):
        # A non-converged transient must NOT be reported as a valid Jensen/peak
        # result (the sign can flip); averaging_bias raises by default.
        with pytest.raises(RuntimeError):
            tr.averaging_bias(550, 0.0, Q_LOAD, 500000.0, tilt_deg=0, assume_sun_shielded=True,
                              n_orbits=3, steps_per_orbit=360)

    def test_unconverged_inspectable_with_flag(self):
        with pytest.warns(RuntimeWarning):
            b = tr.averaging_bias(550, 0.0, Q_LOAD, 500000.0, tilt_deg=0, assume_sun_shielded=True,
                                  n_orbits=3, steps_per_orbit=360,
                                  require_convergence=False)
        assert b["converged"] is False

    def test_reports_convergence_diagnostics(self):
        b = tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        assert b["converged"] is True
        assert b["closure_error_K"] < 1e-3
        assert {"orbits_used", "energy_residual_W_m2"} <= set(b)

    def test_sink_avg_matches_sink_module(self):
        b = tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        ref = sink_mod.orbit_averaged_sink(550, 0.0, tilt_deg=0, assume_sun_shielded=True)
        assert b["sink_avg_K"] == pytest.approx(ref, abs=0.2)



class TestConvergence:
    def test_returns_three_tuple_by_default(self):
        # Backward compatibility: the default return is still (t, T, T_sink).
        out = tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        assert len(out) == 3

    def test_diagnostics_reported_and_converged(self):
        t, T, Ts, d = tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, assume_sun_shielded=True,
                                   return_diagnostics=True, **SIM)
        assert set(d) == {"converged", "orbits_used", "closure_error_K", "tol_K",
                          "energy_residual_W_m2", "energy_residual_K", "energy_tol_K"}
        assert d["converged"] is True
        assert d["closure_error_K"] < d["tol_K"]
        assert d["energy_residual_W_m2"] < 1e-1          # ~0 net flux at periodic SS

    def test_high_mass_needs_more_orbits(self):
        # Motivation for the change: heavier panels take more orbits to settle.
        _, _, _, lo = tr.simulate(550, 0.0, Q_LOAD, 2000.0, tilt_deg=0, assume_sun_shielded=True,
                                  return_diagnostics=True, **SIM)
        _, _, _, hi = tr.simulate(550, 0.0, Q_LOAD, 40000.0, tilt_deg=0, assume_sun_shielded=True,
                                  return_diagnostics=True, **SIM)
        assert hi["orbits_used"] > lo["orbits_used"]
        assert lo["converged"] and hi["converged"]

    def test_nonconvergence_warns_and_flags(self):
        # A very high thermal mass under a tight orbit cap cannot reach periodic
        # steady state: simulate must warn and report converged=False.
        with pytest.warns(RuntimeWarning):
            _, _, _, d = tr.simulate(550, 0.0, Q_LOAD, 500000.0, tilt_deg=0, assume_sun_shielded=True,
                                     n_orbits=3, steps_per_orbit=360,
                                     return_diagnostics=True)
        assert d["converged"] is False
        assert d["orbits_used"] == 3

    def test_high_thermal_mass_not_falsely_converged(self):
        # tau/P >> 1: per-orbit closure -> 0 while the panel is far from steady
        # state. Closure alone would falsely certify convergence; the energy-balance
        # gate must reject it (audit re-review P1-1).
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _, _, _, d = tr.simulate(550, 90, 545.0, 1e9, assume_sun_shielded=True,
                                     n_orbits=30, steps_per_orbit=200,
                                     return_diagnostics=True)
        assert d["closure_error_K"] < d["tol_K"]            # closure alone is satisfied
        assert d["energy_residual_K"] > d["energy_tol_K"]   # but energy dT_eq is not
        assert d["converged"] is False

    def test_high_thermal_mass_poor_guess_not_converged(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _, _, _, d = tr.simulate(550, 90, 545.0, 1e10, assume_sun_shielded=True,
                                     t0_guess=100.0, n_orbits=30, steps_per_orbit=200,
                                     return_diagnostics=True)
        assert d["converged"] is False
        assert d["energy_residual_K"] > d["energy_tol_K"]

    def test_low_load_deep_space_not_falsely_converged(self):
        # Audit P1-1: at low q_load / low T the flux->temperature slope 4*eps*sigma*T^3
        # is tiny, so a fixed W/m^2 floor hid many-kelvin errors. The temperature-
        # equivalent criterion (dT_eq) must reject this deep-space case.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _, _, _, d = tr.simulate(altitude_km=550, beta_deg=90, q_load=1e-3,
                                     areal_heat_capacity=1e9, tilt_deg=180,
                                     assume_sun_shielded=True, t0_guess=10.0,
                                     n_orbits=1, steps_per_orbit=100,
                                     return_diagnostics=True)
        assert d["closure_error_K"] < d["tol_K"]            # closure trivially small
        assert d["energy_residual_K"] > d["energy_tol_K"]   # ~2.4 K equivalent error
        assert d["converged"] is False

    def test_averaging_bias_raises_on_false_closure(self):
        # The high-mass false-closure case must NOT yield a (negative) peak excess.
        with pytest.raises(RuntimeError):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tr.averaging_bias(550, 90, 545.0, 1e9, assume_sun_shielded=True,
                                  n_orbits=30, steps_per_orbit=200)

    def test_nonconvergence_can_raise(self):
        with pytest.raises(RuntimeError):
            tr.simulate(550, 0.0, Q_LOAD, 500000.0, tilt_deg=0, assume_sun_shielded=True,
                        n_orbits=3, steps_per_orbit=360,
                        raise_on_nonconvergence=True)



class TestHeatCapacityProvenance:
    def test_areal_heat_capacity_sums_layers(self):
        # C_A = rho*cp*t for a single 2 mm aluminum layer.
        c = tr.areal_heat_capacity([("aluminum_6061", 0.002)])
        assert c == pytest.approx(2700.0 * 896.0 * 0.002, rel=1e-12)

    def test_builds_are_physically_plausible(self):
        vals = {k: tr.build_areal_heat_capacity(k) for k in tr.REPRESENTATIVE_BUILDS}
        # All bracket the illustrative 2000..40000 J/m^2/K range used in examples.
        assert all(1e3 < v < 5e4 for v in vals.values())
        # Adding a coolant inventory and compute mass raises C_A monotonically.
        assert (vals["pv_on_substrate"]
                < vals["radiator_with_coolant"]
                < vals["integrated_compute_radiator"])

    def test_unknown_material_and_build_raise(self):
        with pytest.raises(KeyError):
            tr.areal_heat_capacity([("unobtanium", 0.001)])
        with pytest.raises(KeyError):
            tr.build_areal_heat_capacity("warp_nacelle")
        with pytest.raises(ValueError):
            tr.areal_heat_capacity([("aluminum_6061", -0.001)])

    def test_derived_capacity_drives_the_transient(self):
        # A build-derived C_A runs the solver and reaches periodic steady state.
        C = tr.build_areal_heat_capacity("radiator_with_coolant")
        _, _, _, d = tr.simulate(550, 0.0, Q_LOAD, C, tilt_deg=0, assume_sun_shielded=True,
                                 return_diagnostics=True, **SIM)
        assert d["converged"] is True

    def test_materials_carry_provenance(self):
        keys = {"rho_kg_m3", "cp_J_kgK", "state", "source", "rel_uncertainty"}
        for name, m in tr.MATERIALS.items():
            assert keys <= set(m), name
            assert m["rho_kg_m3"] > 0 and m["cp_J_kgK"] > 0
            assert 0.0 < m["rel_uncertainty"] < 1.0

    def test_ammonia_entry_matches_coolprop_reference_state(self):
        pytest.importorskip("CoolProp")
        rho, cp = tr.coolant_rho_cp("Ammonia", 300.0)
        m = tr.MATERIALS["ammonia_liquid"]
        assert m["rho_kg_m3"] == pytest.approx(rho, rel=m["rel_uncertainty"])
        assert m["cp_J_kgK"] == pytest.approx(cp, rel=m["rel_uncertainty"])

    def test_ammonia_provenance_matches_backend(self):
        # The recorded CoolProp version + EOS key must match the installed backend
        # so the citation cannot drift from the numbers (audit re-review P2-6).
        pytest.importorskip("CoolProp")
        from orbital_thermal import fluids
        prov = fluids.provenance("Ammonia")
        m = tr.MATERIALS["ammonia_liquid"]
        assert prov["version"] == m["coolprop_version"]
        assert prov["eos_bibtex_key"] == m["eos_bibtex_key"]



class TestShieldingPropagation:
    """The sun-shield policy must be explicit and reach the transient path
    (audit re-review P1-b): simulate/averaging_bias no longer silently assume it."""

    def test_simulate_requires_flag(self):
        with pytest.raises(TypeError):
            tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM)

    def test_simulate_unshielded_raises(self):
        with pytest.raises(NotImplementedError):
            tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0,
                        assume_sun_shielded=False, **SIM)

    def test_averaging_bias_requires_flag(self):
        with pytest.raises(TypeError):
            tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM)

    def test_averaging_bias_unshielded_raises(self):
        with pytest.raises(NotImplementedError):
            tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0,
                              assume_sun_shielded=False, **SIM)


class TestInputDomainAndStability:
    """Input-domain validation and explicit-RK4 stability guards (P3-a)."""

    def test_rejects_nonpositive_heat_capacity(self):
        with pytest.raises(ValueError):
            tr.simulate(550, 0.0, Q_LOAD, 0.0, tilt_deg=0, assume_sun_shielded=True, **SIM)
        with pytest.raises(ValueError):
            tr.simulate(550, 0.0, Q_LOAD, -5.0, tilt_deg=0, assume_sun_shielded=True, **SIM)

    def test_rejects_bad_step_and_orbit_counts(self):
        with pytest.raises(ValueError):
            tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, assume_sun_shielded=True,
                        n_orbits=0, steps_per_orbit=720)
        with pytest.raises(ValueError):
            tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, assume_sun_shielded=True,
                        n_orbits=5, steps_per_orbit=0)

    def test_rk4_divergence_raises(self):
        # Tiny heat capacity + coarse steps -> dt >> tau -> explicit RK4 blows up.
        with pytest.raises(RuntimeError):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")  # ignore the stability RuntimeWarning
                tr.simulate(550, 0.0, Q_LOAD, 1.0, tilt_deg=0, assume_sun_shielded=True,
                            n_orbits=2, steps_per_orbit=100)

    def test_simulate_rejects_invalid_physical_inputs(self):
        # Early validation: degenerate/non-physical inputs raise before integrating
        # (audit re-review P2-7), not ZeroDivisionError or a silent profile.
        bad = dict(tilt_deg=0, assume_sun_shielded=True, n_orbits=2, steps_per_orbit=100)
        with pytest.raises(ValueError):
            tr.simulate(550, 0, Q_LOAD, 8000.0, emissivity=0.0, **bad)
        with pytest.raises(ValueError):
            tr.simulate(550, 0, -100.0, 8000.0, **bad)              # negative load
        with pytest.raises(ValueError):
            tr.simulate(550, 0, Q_LOAD, 8000.0, convergence_tol_K=float("nan"), **bad)
        with pytest.raises(ValueError):
            tr.simulate(550, 0, Q_LOAD, 8000.0, convergence_tol_K=-1.0, **bad)
        with pytest.raises(ValueError):
            tr.simulate(550, 0, Q_LOAD, 8000.0, t0_guess=-5.0, **bad)

    def test_rk4_negative_temperature_raises(self):
        # An unstable-but-finite run dipped to ~-332 K and was returned before;
        # any non-positive accepted state must now raise (audit re-review P1-3).
        with pytest.raises(RuntimeError):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tr.simulate(550, 0, 5000.0, 1000.0, assume_sun_shielded=True,
                            n_orbits=3, steps_per_orbit=50)

    def test_empty_layers_rejected(self):
        with pytest.raises(ValueError):
            tr.areal_heat_capacity([])
