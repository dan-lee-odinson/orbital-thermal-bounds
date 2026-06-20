"""Starcloud 2024 white-paper -- spectrally-separated heat balance (A3).

Milestone A3 implements the spectral-property alternative flagged in the
implementation brief: for a spectrally selective coating, the absorptivity to
Earth's thermal IR (long-wave) need not equal the absorptivity to sunlight
(short-wave). Setting the IR-band absorptivity equal to the thermal emissivity
(Kirchhoff, 0.92) raises the absorbed Earth-IR term and lowers net rejection
to ~584.76 W/m^2.

This is a SENSITIVITY case, not a claim the published design is wrong. The
expected values are the implementation brief's targets; only the Earth-IR
absorptivity differs from the published (as-written) case.
"""

import pytest

from orbital_thermal.constants import SIGMA_SB
from orbital_thermal.reference_architectures import (
    SIGMA_WHITEPAPER,
    STARCLOUD_2024_PUBLISHED,
    STARCLOUD_2024_SPECTRAL,
    starcloud_published_balance,
    starcloud_spectral_balance,
)


class TestSpectralCaseInputs:
    def test_only_earth_ir_absorptivity_changes(self):
        pub, spec = STARCLOUD_2024_PUBLISHED, STARCLOUD_2024_SPECTRAL
        # Long-wave absorptivity is Kirchhoff-set to the emissivity...
        assert spec.absorptivity_earth_ir == spec.emissivity_thermal == 0.92
        # ...while short-wave (solar/albedo) absorptivity is unchanged.
        assert spec.absorptivity_solar == pub.absorptivity_solar == 0.09
        # Every other physical input is identical to the published case.
        for field in (
            "radiator_temperature_K", "emissivity_thermal", "earth_view_factor",
            "earth_albedo", "solar_irradiance_W_m2", "earth_temperature_K",
            "emitting_faces", "sunlit_faces",
        ):
            assert getattr(spec, field) == getattr(pub, field)


class TestSpectralBalance:
    # Brief targets; 2-decimal display, assert to +/- 0.01 W/m^2 with rounded sigma.
    def test_emitted_unchanged(self):
        assert starcloud_spectral_balance().emitted_W_m2 == pytest.approx(770.48, abs=0.01)

    def test_solar_unchanged(self):
        assert starcloud_spectral_balance().direct_solar_absorbed_W_m2 == pytest.approx(
            122.94, abs=0.01
        )

    def test_albedo_unchanged_short_wave(self):
        # Albedo uses the SOLAR absorptivity, so it is identical to the published case.
        assert starcloud_spectral_balance().earth_albedo_absorbed_W_m2 == pytest.approx(
            9.22, abs=0.01
        )

    def test_earth_ir_raised_by_kirchhoff(self):
        assert starcloud_spectral_balance().earth_ir_absorbed_W_m2 == pytest.approx(
            53.56, abs=0.01
        )

    def test_earth_combined(self):
        assert starcloud_spectral_balance().earth_combined_absorbed_W_m2 == pytest.approx(
            62.78, abs=0.01
        )

    def test_net_rejection_is_584_76(self):
        # The headline spectral-separation result.
        assert starcloud_spectral_balance().net_rejection_W_m2 == pytest.approx(
            584.76, abs=0.01
        )


class TestSpectralVsPublished:
    def test_difference_is_extra_earth_ir_absorption(self):
        pub = starcloud_published_balance()
        spec = starcloud_spectral_balance()
        # The whole net change comes from the extra absorbed Earth IR.
        delta_net = pub.net_rejection_W_m2 - spec.net_rejection_W_m2
        delta_ir = spec.earth_ir_absorbed_W_m2 - pub.earth_ir_absorbed_W_m2
        assert delta_net == pytest.approx(delta_ir, rel=1e-12)
        assert delta_net == pytest.approx(48.32, abs=0.02)

    def test_spectral_net_is_lower(self):
        assert (
            starcloud_spectral_balance().net_rejection_W_m2
            < starcloud_published_balance().net_rejection_W_m2
        )


class TestSpectralConstantSensitivity:
    def test_si_derived_sigma_shift_under_0_1(self):
        r_wp = starcloud_spectral_balance(sigma=SIGMA_WHITEPAPER)
        r_si = starcloud_spectral_balance(sigma=SIGMA_SB)
        assert r_si.net_rejection_W_m2 == pytest.approx(584.81, abs=0.02)
        assert abs(r_si.net_rejection_W_m2 - r_wp.net_rejection_W_m2) < 0.1


class TestSpectralAreaChecks:
    # Required planform area = heat_load / net (derived, not printed in source).
    def test_area_120kW_spectral_net(self):
        assert starcloud_spectral_balance().required_planform_area_m2(
            120e3
        ) == pytest.approx(205.21, abs=0.05)

    def test_area_150kW_spectral_net(self):
        assert starcloud_spectral_balance().required_planform_area_m2(
            150e3
        ) == pytest.approx(256.52, abs=0.05)
