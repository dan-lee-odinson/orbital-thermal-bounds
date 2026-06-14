"""Cross-module finite/integer/range input validation (audit re-review P2-4).

Non-finite (NaN/inf), out-of-range, and wrong-type inputs must be rejected at
public boundaries rather than silently returning NaN, a coarse value, or hanging.
"""

import pytest

from orbital_thermal import bounds, environment as env
from orbital_thermal import equilibrium as eq
from orbital_thermal import radiation as rad
from orbital_thermal import sink as sk
from orbital_thermal import transient as tr

NAN = float("nan")
INF = float("inf")


class TestNonFiniteRejected:
    def test_radiation(self):
        with pytest.raises(ValueError):
            rad.net_flux(NAN, 0.91, 220.0)
        with pytest.raises(ValueError):
            rad.required_area(NAN, 293.0, 0.91)
        with pytest.raises(ValueError):
            rad.effective_sink_temperature(0.5, NAN)

    def test_equilibrium(self):
        with pytest.raises(ValueError):
            eq.equilibrium_temperature(NAN, 220.0, 0.91, 220.0)

    def test_environment(self):
        with pytest.raises(ValueError):
            env.orbital_period(NAN)

    def test_bounds(self):
        with pytest.raises(ValueError):
            bounds.heating_cop(NAN)
        with pytest.raises(ValueError):
            bounds.heat_pump_overhead(NAN)
        with pytest.raises(ValueError):
            bounds.nonzero_sink_optimum(600.0, 220.0, tol=INF)

    def test_sink(self):
        with pytest.raises(ValueError):
            sk.orbital_effective_sink_temperature(550, NAN, 0, assume_sun_shielded=True)
        with pytest.raises(ValueError):
            sk.orbital_effective_sink_temperature(550, 0, 0, assume_sun_shielded=True, t_space=NAN)
        with pytest.raises(ValueError):
            sk.sink_temperature_series(-1.0, 0, 0, assume_sun_shielded=True)   # view_factor
        with pytest.raises(ValueError):
            sk.orbital_effective_sink_temperature(550, 100.0, 0, assume_sun_shielded=True)  # beta>90


class TestRangeAndType:
    def test_sink_profile_requires_three_points(self):
        with pytest.raises(ValueError):
            sk.sink_profile(550, 0.0, assume_sun_shielded=True, n=2)

    def test_simulate_counts_must_be_int(self):
        with pytest.raises(TypeError):
            tr.simulate(550, 0, 545.0, 8000.0, assume_sun_shielded=True,
                        steps_per_orbit=720.0, n_orbits=2)
        with pytest.raises(TypeError):
            tr.simulate(550, 0, 545.0, 8000.0, assume_sun_shielded=True,
                        steps_per_orbit=720, n_orbits=2.0)

    def test_areal_heat_capacity_rejects_nonfinite_thickness(self):
        with pytest.raises(ValueError):
            tr.areal_heat_capacity([("aluminum_6061", NAN)])


class TestEntryPointsRejectNonFinite:
    """Audit r5 P2: entry points that previously accepted NaN/inf now use the
    shared validators (orbital_thermal._validate) and reject them."""

    def test_radiative_capacity_area(self):
        with pytest.raises(ValueError):
            eq.radiative_capacity(300.0, NAN, 0.91, 220.0)
        with pytest.raises(ValueError):
            eq.radiative_capacity(300.0, INF, 0.91, 220.0)

    def test_steady_state_temperature(self):
        with pytest.raises(ValueError):
            tr.steady_state_temperature(NAN, 220.0, 0.91)
        with pytest.raises(ValueError):
            tr.steady_state_temperature(545.0, 220.0, 0.0)

    def test_thermal_time_constant(self):
        with pytest.raises(ValueError):
            tr.thermal_time_constant(NAN, 337.0, 0.91)
        with pytest.raises(ValueError):
            tr.thermal_time_constant(8000.0, -300.0, 0.91)

    def test_subpoint_albedo_factor(self):
        with pytest.raises(ValueError):
            sk.subpoint_albedo_factor(NAN, 0.0)
        with pytest.raises(ValueError):
            sk.subpoint_albedo_factor(0.0, INF)

    def test_in_eclipse(self):
        with pytest.raises(ValueError):
            sk.in_eclipse(550, NAN, 0.0)
        with pytest.raises(ValueError):
            sk.in_eclipse(550, 100.0, 0.0)

    def test_sink_profile_non_integer_n(self):
        with pytest.raises(TypeError):
            sk.sink_profile(550, 0.0, assume_sun_shielded=True, n=3.5)

    def test_bounds_inf_and_zero(self):
        with pytest.raises(ValueError):
            bounds.fixed_work_area_per_watt(INF, 3.0, 2.7)
        with pytest.raises(ValueError):
            bounds.carnot_cop_cooling(353.0, INF)
        with pytest.raises(ValueError):
            bounds.quintic_residual(250.0, 0.0, 220.0)

    def test_boolean_contracts(self):
        with pytest.raises(TypeError):
            tr.simulate(550, 0, 545.0, 8000.0, assume_sun_shielded=True,
                        check_time_resolution=1)
        with pytest.raises(TypeError):
            tr.averaging_bias(550, 0, 545.0, 8000.0, assume_sun_shielded=True,
                              require_convergence="yes")


class TestRemainingPublicAPIs:
    """Audit r6 P2: validation extended to the public APIs that still admitted
    NaN/inf or non-integer counts (bounds edges, exact-VF module, fluids)."""

    def test_bounds_nonzero_sink_optimum_and_penalty(self):
        with pytest.raises(ValueError):
            bounds.nonzero_sink_optimum(INF, 220.0)
        with pytest.raises(ValueError):
            bounds.conversion_area_penalty(INF, 450.0, 0.2, 220.0)

    def test_exact_view_factor_counts_and_range(self):
        from orbital_thermal import mccalip_exact_vf as mx
        with pytest.raises(ValueError):
            mx.exact_per_face_view_factors(550, 90, n=0)
        with pytest.raises(TypeError):
            mx.exact_per_face_view_factors(550, 90, n=3.5)
        with pytest.raises(ValueError):
            mx.exact_per_face_view_factors(550, NAN, n=72)
        with pytest.raises(ValueError):
            mx.correction_table_vs_beta([NAN])

    def test_fluids_critical_margin_finite(self):
        pytest.importorskip("CoolProp")
        from orbital_thermal import fluids
        with pytest.raises(ValueError):
            fluids.critical_margin(NAN)
        with pytest.raises(ValueError):
            fluids.critical_margin(INF)


class TestRoundSevenValidation:
    """Audit r7 P2: validation for the new grid-free sink helper, the headline
    arbitrary-view-factor helper, and the fluids phase API."""

    def test_sink_fourth_power_mean_environment_and_shielding(self):
        from orbital_thermal import sink as sk
        with pytest.raises(ValueError):
            sk.sink_fourth_power_mean(0.5, 0, assume_sun_shielded=True, earth_ir=-1000.0)
        with pytest.raises(ValueError):
            sk.sink_fourth_power_mean(0.5, 0, assume_sun_shielded=True, albedo=NAN)
        with pytest.raises(ValueError):
            sk.sink_fourth_power_mean(0.5, 0, assume_sun_shielded=True, t_space=NAN)
        with pytest.raises(TypeError):
            sk.sink_fourth_power_mean(0.5, 0, emissivity=0.91)   # shielding required
        with pytest.raises(ValueError):
            sk.analytic_orbit_averaged_sink(550, 0, assume_sun_shielded=True, earth_ir=-1000.0)

    def test_equilibrium_temperature_with_view_factors_range(self):
        from orbital_thermal import mccalip_exact_vf as mx
        with pytest.raises(ValueError):
            mx.equilibrium_temperature_with_view_factors({}, -1.0, 0.2)
        with pytest.raises(ValueError):
            mx.equilibrium_temperature_with_view_factors({}, 0.2, 2.0)
        with pytest.raises(ValueError):
            mx.equilibrium_temperature_with_view_factors({}, NAN, 0.2)

    def test_fluids_phase_state_rejects_invalid_T_P(self):
        pytest.importorskip("CoolProp")
        from orbital_thermal import fluids
        with pytest.raises(ValueError):
            fluids.phase_state(NAN, 1e5)
        with pytest.raises(ValueError):
            fluids.phase_state(300.0, -1.0)

    def test_fluids_saturation_helpers_validate_T(self):
        # Audit r8 P3: saturation_pressure / saturated_densities require finite
        # positive T and reject T at/above the critical point with a clear contract.
        pytest.importorskip("CoolProp")
        from orbital_thermal import fluids
        with pytest.raises(ValueError):
            fluids.saturation_pressure(NAN)
        with pytest.raises(ValueError):
            fluids.saturation_pressure(-5.0)
        with pytest.raises(ValueError):
            fluids.saturated_densities(NAN)
        with pytest.raises(ValueError):
            fluids.saturated_densities(450.0)        # above ammonia critical (405.5 K)
