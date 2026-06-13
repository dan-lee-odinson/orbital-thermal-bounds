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
        a = sink.orbital_effective_sink_temperature(550, 0, 180, tilt_deg=0, assume_sun_shielded=True,
                                            emissivity=0.91, solar_absorptivity=0.20)
        b = sink.orbital_effective_sink_temperature(550, 0, 180, tilt_deg=0, assume_sun_shielded=True,
                                            emissivity=0.5, solar_absorptivity=0.9)
        assert a == pytest.approx(b, rel=1e-12)

    def test_ir_floor_matches_closed_form(self):
        # Nadir, night side: sigma*T^4 = E_ir*VF_nadir + sigma*T_space^4.
        vf = env.nadir_view_factor(550)
        expected = ((sink.EARTH_IR_FLUX * vf) / SIGMA_SB + sink.T_SPACE_K**4) ** 0.25
        got = sink.orbital_effective_sink_temperature(550, 0, 180, tilt_deg=0, assume_sun_shielded=True)
        assert got == pytest.approx(expected, rel=1e-12)

    def test_subpoint_approx_no_albedo_swing_at_terminator(self):
        # APPROXIMATION BEHAVIOR, not physics: under the SUBPOINT albedo
        # approximation the sub-satellite point is never sunlit at beta = 90
        # (cos(zeta)=0 for all u), so the modeled sink is flat at the IR floor.
        # The real disk-integrated albedo is nonzero around a terminator orbit
        # (see TestPhysicalAlbedoFacts). This test pins the approximation, not a
        # physical truth.
        u, T = sink.sink_profile(550, 90.0, tilt_deg=0, assume_sun_shielded=True)
        assert np.ptp(T) == pytest.approx(0.0, abs=1e-9)

    def test_dayside_hotter_than_nightside(self):
        day = sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0, assume_sun_shielded=True)
        night = sink.orbital_effective_sink_temperature(550, 0, 180, tilt_deg=0, assume_sun_shielded=True)
        assert day > night

    def test_albedo_swing_shrinks_with_beta(self):
        # Peak-to-night difference at orbit noon should decrease as beta rises.
        def swing(beta):
            noon = sink.orbital_effective_sink_temperature(550, beta, 0, tilt_deg=0, assume_sun_shielded=True)
            night = sink.orbital_effective_sink_temperature(550, beta, 180, tilt_deg=0, assume_sun_shielded=True)
            return noon - night
        swings = [swing(b) for b in (0, 30, 60, 90)]
        assert all(a >= b - 1e-9 for a, b in zip(swings, swings[1:]))
        # NB swings[-1] == 0 is subpoint-approximation behavior, not physics
        # (see TestPhysicalAlbedoFacts); the trend toward smaller swing is real.
        assert swings[-1] == pytest.approx(0.0, abs=1e-9)

    def test_space_facing_approaches_cmb(self):
        # A zenith-facing radiator sees almost no Earth -> sink near CMB.
        T = sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=180, assume_sun_shielded=True)
        assert T == pytest.approx(sink.T_SPACE_K, abs=0.5)

    def test_pure_ir_independent_of_orbit_position(self):
        # With zero solar absorptivity, only Earth IR remains -> flat profile.
        u, T = sink.sink_profile(550, 0.0, tilt_deg=0, solar_absorptivity=0.0, assume_sun_shielded=True)
        assert np.ptp(T) == pytest.approx(0.0, abs=1e-9)

    def test_nadir_floor_anchor_value(self):
        # Documented anchor: nadir-facing IR floor at 550 km ~ 244 K.
        assert sink.orbital_effective_sink_temperature(550, 0, 180, tilt_deg=0, assume_sun_shielded=True) == pytest.approx(
            243.95, abs=0.5
        )

    def test_zero_emissivity_rejected(self):
        with pytest.raises(ValueError):
            sink.orbital_effective_sink_temperature(550, 0, 0, emissivity=0.0, assume_sun_shielded=True)

    def test_shielding_flag_is_required(self):
        # No default: omitting the explicit sun-shielded choice is an error
        # (audit re-review P1-b -- the omission can no longer be silent).
        with pytest.raises(TypeError):
            sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0)
        # Provided explicitly, it computes normally.
        sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0, assume_sun_shielded=True)

    def test_unshielded_raises(self):
        # Asking for a general (non-sun-shielded) sink is refused, not faked.
        with pytest.raises(NotImplementedError):
            sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0, assume_sun_shielded=False)

    def test_shielding_flag_must_be_strict_boolean(self):
        # Truthy non-booleans must NOT assert shielding (audit re-review P1-2).
        for bad in ("false", "true", "no", 1, 0, [1], None):
            with pytest.raises(TypeError):
                sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0,
                                                assume_sun_shielded=bad)
        # the genuine booleans behave as specified
        sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0, assume_sun_shielded=True)
        with pytest.raises(NotImplementedError):
            sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0, assume_sun_shielded=False)

    def test_flag_flows_through_profile(self):
        with pytest.raises(NotImplementedError):
            sink.sink_profile(550, 0.0, tilt_deg=0, assume_sun_shielded=False)


class TestEclipse:
    def test_night_anti_solar_point_in_eclipse_at_beta0(self):
        assert sink.in_eclipse(550, 0.0, 180.0) is True

    def test_dayside_not_in_eclipse(self):
        assert sink.in_eclipse(550, 0.0, 0.0) is False

    def test_terminator_orbit_never_eclipsed(self):
        assert all(not sink.in_eclipse(550, 90.0, u) for u in range(0, 360, 10))


class TestOrbitAverage:
    def test_t4_weighted_average_between_min_and_max(self):
        u, T = sink.sink_profile(550, 0.0, tilt_deg=0, assume_sun_shielded=True)
        avg = sink.orbit_averaged_sink(550, 0.0, tilt_deg=0, assume_sun_shielded=True)
        assert T.min() <= avg <= T.max()

    def test_average_excludes_duplicated_endpoint(self):
        # orbit_averaged_sink must drop the duplicated 360deg point; it should
        # equal the endpoint-excluded T^4 mean, not the all-points mean.
        _, T = sink.sink_profile(550, 0.0, tilt_deg=0, n=720, assume_sun_shielded=True)
        excl = float(np.mean(T[:-1] ** 4) ** 0.25)
        incl = float(np.mean(T ** 4) ** 0.25)
        avg = sink.orbit_averaged_sink(550, 0.0, tilt_deg=0, n=720, assume_sun_shielded=True)
        assert avg == pytest.approx(excl, rel=1e-12)
        assert abs(avg - incl) > 1e-3      # the duplicate really did bias it

    def test_subpoint_approx_average_equals_floor_at_terminator(self):
        # APPROXIMATION BEHAVIOR, not physics: because the subpoint albedo
        # approximation nulls all albedo at beta = 90, the orbit-averaged sink
        # collapses to the IR floor. A disk-integrated model would sit above it.
        avg = sink.orbit_averaged_sink(550, 90.0, tilt_deg=0, assume_sun_shielded=True)
        floor = sink.orbital_effective_sink_temperature(550, 90, 180, tilt_deg=0, assume_sun_shielded=True)
        assert avg == pytest.approx(floor, rel=1e-9)


class TestPhysicalAlbedoFacts:
    """Physical truths the future DISK-INTEGRATED albedo model must satisfy.

    These target ``sink.disk_integrated_albedo_factor`` -- NOT the subpoint helper,
    whose documented approximation semantics will not change. They xfail today
    because that function is unimplemented (NotImplementedError); being strict,
    each will fail the build as an upgrade reminder the day a correct disk-integrated
    model lands and makes the assertion pass (audit re-review P2-a).
    """

    @pytest.mark.xfail(reason="disk_integrated_albedo_factor not yet implemented; "
                              "terminator orbit still sees sunlit Earth (P2-a)",
                       raises=NotImplementedError, strict=True)
    def test_beta90_orbit_has_nonzero_disk_integrated_albedo(self):
        # A terminator (beta=90) orbit at noon flies over sunlit Earth off-nadir,
        # so the disk-integrated reflected-solar drive is nonzero.
        assert sink.disk_integrated_albedo_factor(550, 90.0, 0.0) > 1e-6

    @pytest.mark.xfail(reason="disk_integrated_albedo_factor not yet implemented; "
                              "a dark subpoint still leaves a sunlit disk (P2-a)",
                       raises=NotImplementedError, strict=True)
    def test_subpoint_darkness_does_not_imply_dark_disk(self):
        # Subpoint dark at (beta=0, u=100): the approximation nulls albedo, yet a
        # sunlit crescent of Earth remains visible to the radiator.
        assert sink.subpoint_albedo_factor(0.0, 100.0) == 0.0
        assert sink.disk_integrated_albedo_factor(550, 0.0, 100.0) > 1e-6

    @pytest.mark.xfail(reason="disk_integrated_albedo_factor not yet implemented; "
                              "off-opposition eclipse keeps a sunlit crescent (P2-a)",
                       raises=NotImplementedError, strict=True)
    def test_eclipse_off_opposition_has_nonzero_albedo(self):
        # In eclipse but NOT at exact opposition (beta=0, u=120): the Lambertian
        # phase function is nonzero (it vanishes only at exact opposition u=180),
        # so a sunlit crescent contributes. The previous u=180 assertion was WRONG
        # -- Phi(pi)=0 makes disk-integrated albedo genuinely zero there.
        assert sink.in_eclipse(550, 0.0, 120.0) is True
        assert sink.disk_integrated_albedo_factor(550, 0.0, 120.0) > 1e-6


class TestSubpointAlbedoApproximation:
    """Ordinary passing tests of the SUBPOINT approximation helper's defined
    behavior: factor = max(0, cos(beta) cos(u)). Not physics placeholders."""

    def test_orbit_noon_equatorial_is_unity(self):
        assert sink.subpoint_albedo_factor(0.0, 0.0) == pytest.approx(1.0)

    def test_nulls_on_night_side_and_terminator(self):
        assert sink.subpoint_albedo_factor(0.0, 180.0) == 0.0                 # midnight
        assert sink.subpoint_albedo_factor(90.0, 0.0) == pytest.approx(0.0, abs=1e-12)
        assert sink.subpoint_albedo_factor(0.0, 120.0) == 0.0                 # cos(120)<0

    def test_matches_clamped_cosine(self):
        for beta, u in [(0, 0), (30, 45), (60, 80), (0, 95)]:
            expect = max(0.0, np.cos(np.radians(beta)) * np.cos(np.radians(u)))
            assert sink.subpoint_albedo_factor(beta, u) == pytest.approx(expect, abs=1e-12)


class TestDeprecatedAlias:
    def test_alias_warns_and_matches(self):
        # sink.effective_sink_temperature is a deprecated alias (audit P2-9).
        with pytest.warns(DeprecationWarning):
            got = sink.effective_sink_temperature(550, 0, 180, tilt_deg=0,
                                                  assume_sun_shielded=True)
        ref = sink.orbital_effective_sink_temperature(550, 0, 180, tilt_deg=0,
                                                      assume_sun_shielded=True)
        assert got == ref


class TestInputDomain:
    """Centralized physical-domain validation (audit re-review P3-a)."""

    def test_emissivity_must_be_in_unit_interval(self):
        with pytest.raises(ValueError):
            sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0,
                                            assume_sun_shielded=True, emissivity=1.5)

    def test_absorptivity_must_be_in_unit_interval(self):
        with pytest.raises(ValueError):
            sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0,
                                            assume_sun_shielded=True, solar_absorptivity=1.5)
        with pytest.raises(ValueError):
            sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0,
                                            assume_sun_shielded=True, solar_absorptivity=-0.1)

    def test_sink_profile_requires_two_points(self):
        with pytest.raises(ValueError):
            sink.sink_profile(550, 0.0, tilt_deg=0, n=1, assume_sun_shielded=True)

    def test_negative_or_nonfinite_fluxes_rejected(self):
        with pytest.raises(ValueError):
            sink.orbital_effective_sink_temperature(550, 0, 0, assume_sun_shielded=True, earth_ir=-1000.0)
        with pytest.raises(ValueError):
            sink.orbital_effective_sink_temperature(550, 0, 0, assume_sun_shielded=True, solar_constant=-1.0)
