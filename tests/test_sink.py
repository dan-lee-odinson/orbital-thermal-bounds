"""Tests for the time-resolved effective sink temperature module."""

import numpy as np
import pytest

from orbital_thermal import sink
from orbital_thermal import environment as env
from orbital_thermal.constants import SIGMA_SB


class TestEffectiveSink:
    def test_ir_floor_is_property_independent(self):
        # On the night side albedo vanishes, so the sink is pure Earth IR and
        # must NOT depend on emissivity or solar absorptivity.
        a = sink.effective_sink_temperature(550, 0, 180, tilt_deg=0,
                                            emissivity=0.91, solar_absorptivity=0.20)
        b = sink.effective_sink_temperature(550, 0, 180, tilt_deg=0,
                                            emissivity=0.5, solar_absorptivity=0.9)
        assert a == pytest.approx(b, rel=1e-12)

    def test_ir_floor_matches_closed_form(self):
        # Nadir, night side: sigma*T^4 = E_ir*VF_nadir + sigma*T_space^4.
        vf = env.nadir_view_factor(550)
        expected = ((sink.EARTH_IR_FLUX * vf) / SIGMA_SB + sink.T_SPACE_K**4) ** 0.25
        got = sink.effective_sink_temperature(550, 0, 180, tilt_deg=0)
        assert got == pytest.approx(expected, rel=1e-12)

    def test_terminator_orbit_has_no_albedo_swing(self):
        # At beta = 90 the sub-satellite point is never sunlit: cos(zeta)=0 for
        # all u, so the sink is flat at the IR floor around the whole orbit.
        u, T = sink.sink_profile(550, 90.0, tilt_deg=0)
        assert np.ptp(T) == pytest.approx(0.0, abs=1e-9)

    def test_dayside_hotter_than_nightside(self):
        day = sink.effective_sink_temperature(550, 0, 0, tilt_deg=0)
        night = sink.effective_sink_temperature(550, 0, 180, tilt_deg=0)
        assert day > night

    def test_albedo_swing_shrinks_with_beta(self):
        # Peak-to-night difference at orbit noon should decrease as beta rises.
        def swing(beta):
            noon = sink.effective_sink_temperature(550, beta, 0, tilt_deg=0)
            night = sink.effective_sink_temperature(550, beta, 180, tilt_deg=0)
            return noon - night
        swings = [swing(b) for b in (0, 30, 60, 90)]
        assert all(a >= b - 1e-9 for a, b in zip(swings, swings[1:]))
        assert swings[-1] == pytest.approx(0.0, abs=1e-9)

    def test_space_facing_approaches_cmb(self):
        # A zenith-facing radiator sees almost no Earth -> sink near CMB.
        T = sink.effective_sink_temperature(550, 0, 0, tilt_deg=180)
        assert T == pytest.approx(sink.T_SPACE_K, abs=0.5)

    def test_pure_ir_independent_of_orbit_position(self):
        # With zero solar absorptivity, only Earth IR remains -> flat profile.
        u, T = sink.sink_profile(550, 0.0, tilt_deg=0, solar_absorptivity=0.0)
        assert np.ptp(T) == pytest.approx(0.0, abs=1e-9)

    def test_nadir_floor_anchor_value(self):
        # Documented anchor: nadir-facing IR floor at 550 km ~ 244 K.
        assert sink.effective_sink_temperature(550, 0, 180, tilt_deg=0) == pytest.approx(
            243.95, abs=0.5
        )

    def test_zero_emissivity_rejected(self):
        with pytest.raises(ValueError):
            sink.effective_sink_temperature(550, 0, 0, emissivity=0.0)


class TestEclipse:
    def test_night_anti_solar_point_in_eclipse_at_beta0(self):
        assert sink.in_eclipse(550, 0.0, 180.0) is True

    def test_dayside_not_in_eclipse(self):
        assert sink.in_eclipse(550, 0.0, 0.0) is False

    def test_terminator_orbit_never_eclipsed(self):
        assert all(not sink.in_eclipse(550, 90.0, u) for u in range(0, 360, 10))


class TestOrbitAverage:
    def test_t4_weighted_average_between_min_and_max(self):
        u, T = sink.sink_profile(550, 0.0, tilt_deg=0)
        avg = sink.orbit_averaged_sink(550, 0.0, tilt_deg=0)
        assert T.min() <= avg <= T.max()

    def test_average_equals_floor_at_terminator(self):
        avg = sink.orbit_averaged_sink(550, 90.0, tilt_deg=0)
        floor = sink.effective_sink_temperature(550, 90, 180, tilt_deg=0)
        assert avg == pytest.approx(floor, rel=1e-9)
