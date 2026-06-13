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
