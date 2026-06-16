"""Starcloud 2024 white-paper -- published (as-written) heat balance.

Milestone A2: reproduce the paper's Thermal Management arithmetic (p. 9 of
"Why we should train AI in space", v1.03) from the page-cited provenance record
``data/reference_architectures/starcloud_2024.yaml``.

ORACLE-FREEZE: the expected values are the white paper's OWN printed numbers
(770.48 / 122.94 / 14.46 / 633.08 W/m^2) and must never be edited to make a
test pass. The paper prints a rounded Stefan-Boltzmann constant (5.67e-8); the
balance is reproduced with that constant, and the ~0.05 W/m^2 offset from the
SI-derived constant is asserted separately as a documented sensitivity.
"""

import pytest

from orbital_thermal import spectral_radiation as sr
from orbital_thermal.constants import SIGMA_SB
from orbital_thermal.reference_architectures import (
    SIGMA_WHITEPAPER,
    STARCLOUD_2024_PUBLISHED,
    starcloud_published_balance,
)


class TestPublishedBalanceAsWritten:
    # The paper displays two decimals; assert to +/- 0.01 W/m^2 with its rounded
    # constant -- an exact match to the printed digits.
    def test_emitted_two_sided(self):
        assert starcloud_published_balance().emitted_W_m2 == pytest.approx(
            770.48, abs=0.01
        )

    def test_direct_solar_absorbed(self):
        assert starcloud_published_balance().direct_solar_absorbed_W_m2 == pytest.approx(
            122.94, abs=0.01
        )

    def test_earth_combined_absorbed(self):
        assert starcloud_published_balance().earth_combined_absorbed_W_m2 == pytest.approx(
            14.46, abs=0.01
        )

    def test_net_rejection_is_633_08(self):
        # The headline as-written result.
        assert starcloud_published_balance().net_rejection_W_m2 == pytest.approx(
            633.08, abs=0.01
        )

    def test_earth_subterms(self):
        r = starcloud_published_balance()
        assert r.earth_albedo_absorbed_W_m2 == pytest.approx(9.22, abs=0.01)
        assert r.earth_ir_absorbed_W_m2 == pytest.approx(5.24, abs=0.01)
        assert (
            r.earth_albedo_absorbed_W_m2 + r.earth_ir_absorbed_W_m2
        ) == pytest.approx(r.earth_combined_absorbed_W_m2, rel=1e-12)

    def test_net_is_emitted_minus_absorbed(self):
        r = starcloud_published_balance()
        assert r.net_rejection_W_m2 == pytest.approx(
            r.emitted_W_m2
            - r.direct_solar_absorbed_W_m2
            - r.earth_combined_absorbed_W_m2,
            rel=1e-12,
        )

    def test_published_case_uses_single_absorptivity(self):
        # Guards the as-written contract: solar and IR absorptivities are equal.
        c = STARCLOUD_2024_PUBLISHED
        assert c.absorptivity_solar == c.absorptivity_earth_ir == 0.09


class TestConstantSensitivity:
    def test_si_derived_sigma_shifts_net_by_under_0_1(self):
        r_wp = starcloud_published_balance(sigma=SIGMA_WHITEPAPER)
        r_si = starcloud_published_balance(sigma=SIGMA_SB)
        assert r_si.net_rejection_W_m2 == pytest.approx(633.13, abs=0.02)
        assert abs(r_si.net_rejection_W_m2 - r_wp.net_rejection_W_m2) < 0.1


class TestPublishedAreaChecks:
    # Required planform area = heat_load / net. 120 kW is the paper's per-rack
    # power density (p. 11); 150 kW is a forward projection. Area values are
    # derived (not printed in the source) -- see the A1 record.
    def test_area_120kW_published_net(self):
        assert starcloud_published_balance().required_planform_area_m2(
            120e3
        ) == pytest.approx(189.55, abs=0.05)

    def test_area_150kW_published_net(self):
        assert starcloud_published_balance().required_planform_area_m2(
            150e3
        ) == pytest.approx(236.94, abs=0.05)

    def test_area_rejects_nonpositive_load(self):
        r = starcloud_published_balance()
        with pytest.raises(ValueError):
            r.required_planform_area_m2(0.0)
        with pytest.raises(ValueError):
            r.required_planform_area_m2(-1.0)


class TestSpectralBuildingBlocks:
    # Exercise the general spectral_radiation helpers at the published inputs.
    def test_components_individually(self):
        c = STARCLOUD_2024_PUBLISHED
        assert sr.emitted_flux(
            c.radiator_temperature_K, c.emissivity_thermal, SIGMA_WHITEPAPER,
            c.emitting_faces,
        ) == pytest.approx(770.48, abs=0.01)
        assert sr.solar_absorbed_flux(
            c.absorptivity_solar, c.solar_irradiance_W_m2, c.sunlit_faces
        ) == pytest.approx(122.94, abs=0.01)
        assert sr.earth_albedo_absorbed_flux(
            c.absorptivity_solar, c.earth_view_factor, c.earth_albedo,
            c.solar_irradiance_W_m2,
        ) == pytest.approx(9.22, abs=0.01)
        assert sr.earth_ir_absorbed_flux(
            c.absorptivity_earth_ir, c.earth_view_factor, SIGMA_WHITEPAPER,
            c.earth_temperature_K,
        ) == pytest.approx(5.24, abs=0.01)

    def test_input_validation(self):
        with pytest.raises(ValueError):
            sr.emitted_flux(293.15, 1.5, SIGMA_WHITEPAPER)          # emissivity > 1
        with pytest.raises(ValueError):
            sr.earth_ir_absorbed_flux(0.92, 1.2, SIGMA_WHITEPAPER, 253.15)  # F > 1
        with pytest.raises(ValueError):
            sr.emitted_flux(293.15, 0.92, 0.0)                     # sigma not > 0
