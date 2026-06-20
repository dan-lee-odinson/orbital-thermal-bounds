"""Starcloud vs AI1 -- harmonized orbital comparison (Milestone A5).

Both architectures are evaluated under ONE orbital environment and ONE set of
conventions (exact view factor, package OLR/albedo/solar constants, Kirchhoff
spectral split, SI sigma). These tests pin the harmonized-module contract that
matters for defensibility:

  * AI1's solar absorptivity is NEVER invented;
  * the shielded/edge-on comparison sets sunlit_faces = 0 for BOTH;
  * Starcloud's architecture-specific case keeps sunlit_faces = 1 with the
    published alpha_solar = 0.09;
  * the beta sweep includes the dawn-dusk endpoint (90 deg) and warns about the
    albedo-model limitation there;
  * Earth albedo and Earth IR are reported separately;
  * the published Starcloud environmental load is preserved;
  * A2/A3/A4 outputs are unchanged.
"""

import pytest

from orbital_thermal import harmonized_comparison as h
from orbital_thermal.architecture_comparison import (
    AI1_DESIGN_POINT,
    NOT_PUBLISHED,
    compare_as_published,
)
from orbital_thermal.reference_architectures import (
    starcloud_published_balance,
    starcloud_spectral_balance,
)


class TestHarmonizedEnvironment:
    def test_view_factor_matches_paper_geometry(self):
        # tilt=90 (edge-on) at 550 km gives F = 0.258 ~ the paper's assumed 0.25.
        e = h.harmonized_environment(45.0, warn=False)
        assert e.view_factor == pytest.approx(0.258, abs=0.005)

    def test_separated_constants_present(self):
        e = h.harmonized_environment(45.0, warn=False)
        assert e.earth_ir_flux_W_m2 == 237.0
        assert e.solar_constant_W_m2 == 1361.0
        assert e.earth_albedo == 0.30


class TestAI1SolarAbsorptivityNotInvented:
    def test_ai1_has_no_published_solar_absorptivity(self):
        # The AI1 design point carries no absorptivity field at all.
        assert not hasattr(AI1_DESIGN_POINT, "absorptivity_solar")

    def test_default_is_not_published(self):
        b = h.ai1_harmonized_balance(45.0, warn=False)
        assert b.solar_absorptivity is NOT_PUBLISHED

    def test_albedo_left_uncomputed_when_unpublished(self):
        # At beta where albedo != 0, AI1's albedo and full net are None...
        b = h.ai1_harmonized_balance(45.0, warn=False)
        assert b.earth_albedo_absorbed_W_m2 is None
        assert b.net_rejection_W_m2 is None
        # ...but the IR-only net is always available (IR uses emissivity, not alpha).
        assert b.net_excluding_albedo_W_m2 == pytest.approx(1277.07, abs=0.1)

    def test_parametric_value_is_sensitivity_only(self):
        b = h.ai1_harmonized_balance(45.0, solar_absorptivity=0.09, warn=False)
        assert b.earth_albedo_absorbed_W_m2 == pytest.approx(2.132, abs=0.01)
        assert "sensitivity" in b.notes.lower()


class TestShieldedSetsZeroSunlitFacesForBoth:
    def test_both_shielded(self):
        cmp = h.shielded_comparison(90.0, warn=False)
        assert cmp["ai1"].sunlit_faces == 0
        assert cmp["starcloud"].sunlit_faces == 0
        assert cmp["ai1"].direct_solar_absorbed_W_m2 == 0.0
        assert cmp["starcloud"].direct_solar_absorbed_W_m2 == 0.0


class TestStarcloudArchitectureSpecificSunlit:
    def test_sunlit_faces_one_preserved(self):
        b = h.starcloud_harmonized_balance(90.0, sunlit_faces=1, warn=False)
        assert b.sunlit_faces == 1
        # Published short-wave absorptivity 0.09 against the package solar constant.
        assert b.direct_solar_absorbed_W_m2 == pytest.approx(0.09 * 1361.0, abs=0.01)
        assert b.solar_absorptivity == 0.09

    def test_ai1_sunlit_requires_assumed_alpha(self):
        # One-side-sunlit AI1 with no alpha cannot compute direct solar (not invented).
        b = h.ai1_harmonized_balance(90.0, sunlit_faces=1, warn=False)
        assert b.direct_solar_absorbed_W_m2 is None


class TestBetaSweepIncludesEndpointWithWarning:
    def test_sweep_spans_zero_to_ninety(self):
        sweep = h.beta_sweep(
            h.starcloud_harmonized_balance, warn_at_endpoint=False, sunlit_faces=0
        )
        betas = [b.beta_deg for b in sweep]
        assert betas[0] == 0 and betas[-1] == 90
        assert 90 in betas

    def test_endpoint_emits_albedo_limitation_warning(self):
        with pytest.warns(RuntimeWarning, match="albedo"):
            h.harmonized_environment(90.0)

    def test_endpoint_flagged_as_dawn_dusk(self):
        e = h.harmonized_environment(90.0, warn=False)
        assert e.is_dawn_dusk_endpoint is True
        assert e.albedo_model_limited is True

    def test_no_warning_away_from_endpoint(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            h.harmonized_environment(45.0, warn=True)  # must not raise


class TestAlbedoAndIrSeparated:
    def test_separate_fields_at_midrange_beta(self):
        b = h.starcloud_harmonized_balance(45.0, sunlit_faces=0, warn=False)
        assert b.earth_ir_absorbed_W_m2 == pytest.approx(56.20, abs=0.1)
        assert b.earth_albedo_absorbed_W_m2 == pytest.approx(2.132, abs=0.01)
        assert b.earth_ir_absorbed_W_m2 != b.earth_albedo_absorbed_W_m2

    def test_endpoint_ir_nonzero_albedo_zero(self):
        b = h.starcloud_harmonized_balance(90.0, sunlit_faces=0, warn=False)
        assert b.earth_ir_absorbed_W_m2 > 0.0
        assert b.earth_albedo_absorbed_W_m2 == 0.0


class TestPublishedEnvironmentPreserved:
    def test_published_load_available_alongside_sweep(self):
        # The beta=90 albedo null must not erase the paper's environmental load.
        pub = h.published_starcloud_environment()
        assert pub.earth_albedo_absorbed_W_m2 == pytest.approx(9.22, abs=0.01)
        assert pub.earth_ir_absorbed_W_m2 == pytest.approx(5.24, abs=0.01)
        assert pub.earth_combined_absorbed_W_m2 == pytest.approx(14.46, abs=0.01)


class TestEarlierMilestonesUnchanged:
    def test_a2_published_still_633(self):
        assert starcloud_published_balance().net_rejection_W_m2 == pytest.approx(
            633.08, abs=0.01
        )

    def test_a3_spectral_still_585(self):
        assert starcloud_spectral_balance().net_rejection_W_m2 == pytest.approx(
            584.76, abs=0.01
        )

    def test_a4_comparison_still_as_published(self):
        cmp = compare_as_published(120e3)
        assert cmp.basis == "as_published"
        assert cmp.row("radiator_temperature_K").ai1 == pytest.approx(337.10, abs=0.01)
        assert cmp.row("radiator_temperature_K").starcloud == pytest.approx(293.15, abs=0.01)
