"""Starcloud vs AI1 -- harmonized orbital comparison (Milestone A5).

Both architectures are evaluated under ONE orbital environment and ONE set of
conventions (exact view factor, package OLR/albedo/solar constants, Kirchhoff
spectral split, SI sigma). These tests pin the harmonized-module contract:

  * AI1's solar absorptivity is NEVER invented -- its albedo and full net stay
    unresolved at EVERY beta, including the dawn-dusk endpoint (90 deg);
  * the model-limited albedo regime (sub-point model nulling near beta = 90 deg)
    never yields a reportable physical zero -- the reportable albedo/net are None
    while the raw model value is retained separately for figures;
  * the shielded/edge-on comparison sets sunlit_faces = 0 for BOTH;
  * Starcloud's architecture-specific case keeps sunlit_faces = 1 (alpha = 0.09);
  * the beta sweep includes 90 deg and warns about the albedo-model limitation;
  * Earth albedo and Earth IR are reported separately;
  * the published Starcloud environmental load is preserved;
  * A2/A3/A4 outputs are unchanged.
"""

import warnings

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


class TestNoInventionAtEveryBeta:
    """Review item 1: an unpublished optical property stays unresolved at every
    beta, INCLUDING the dawn-dusk endpoint where the albedo model is limited."""

    def test_ai1_has_no_published_solar_absorptivity(self):
        assert not hasattr(AI1_DESIGN_POINT, "absorptivity_solar")

    def test_ai1_default_alpha_is_not_published(self):
        assert h.ai1_harmonized_balance(45.0, warn=False).solar_absorptivity is NOT_PUBLISHED

    @pytest.mark.parametrize("beta", [0.0, 45.0, 90.0])
    def test_ai1_albedo_and_full_net_unresolved(self, beta):
        # Requirements 1 & 2: AI1 albedo AND full net are None at every beta,
        # including 90 deg (the model-limited endpoint must NOT bypass this).
        b = h.ai1_harmonized_balance(beta, warn=False)
        assert b.earth_albedo_absorbed_W_m2 is None
        assert b.earth_albedo_model_W_m2 is None
        assert b.net_rejection_W_m2 is None
        assert b.net_rejection_model_W_m2 is None

    @pytest.mark.parametrize("beta", [0.0, 45.0, 90.0])
    def test_ai1_net_excluding_albedo_available(self, beta):
        # Requirement 3: the IR-only net (needs emissivity, not alpha) is always there.
        b = h.ai1_harmonized_balance(beta, warn=False)
        assert b.net_excluding_albedo_W_m2 == pytest.approx(1277.07, abs=0.1)

    def test_parametric_alpha_is_sensitivity_only(self):
        # Requirement 5: a supplied alpha is an explicit, labelled sensitivity.
        b = h.ai1_harmonized_balance(45.0, solar_absorptivity=0.09, warn=False)
        assert b.earth_albedo_absorbed_W_m2 == pytest.approx(2.13, abs=0.01)
        assert "sensitivity" in b.notes.lower()


class TestModelLimitedNeverReportsPhysicalZero:
    """Review item 4: Starcloud's beta = 90 deg result is explicitly model-limited,
    not silently presented as a physical zero-albedo load."""

    def test_starcloud_endpoint_albedo_not_reportable(self):
        b = h.starcloud_harmonized_balance(90.0, sunlit_faces=0, warn=False)
        assert b.albedo_model_limited is True
        # Reportable albedo / full net are None (not 0.0) at the model-limited endpoint.
        assert b.earth_albedo_absorbed_W_m2 is None
        assert b.net_rejection_W_m2 is None
        # The raw model value is retained separately (for figures), ~0 at beta=90.
        assert b.earth_albedo_model_W_m2 == pytest.approx(0.0, abs=1e-6)
        assert b.net_rejection_model_W_m2 == pytest.approx(714.32, abs=0.1)

    def test_starcloud_offendpoint_albedo_is_reportable(self):
        b = h.starcloud_harmonized_balance(45.0, sunlit_faces=0, warn=False)
        assert b.albedo_model_limited is False
        assert b.earth_albedo_absorbed_W_m2 == pytest.approx(2.13, abs=0.01)
        assert b.net_rejection_W_m2 == pytest.approx(712.19, abs=0.1)
        assert b.net_rejection_W_m2 == b.net_rejection_model_W_m2


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
        assert b.direct_solar_absorbed_W_m2 == pytest.approx(0.09 * 1361.0, abs=0.01)
        assert b.solar_absorptivity == 0.09

    def test_ai1_sunlit_requires_assumed_alpha(self):
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
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            h.harmonized_environment(45.0, warn=True)  # must not raise


class TestAlbedoAndIrSeparated:
    def test_separate_fields_at_midrange_beta(self):
        b = h.starcloud_harmonized_balance(45.0, sunlit_faces=0, warn=False)
        assert b.earth_ir_absorbed_W_m2 == pytest.approx(56.20, abs=0.1)
        assert b.earth_albedo_absorbed_W_m2 == pytest.approx(2.13, abs=0.01)
        assert b.earth_ir_absorbed_W_m2 != b.earth_albedo_absorbed_W_m2

    def test_endpoint_ir_present_albedo_model_limited(self):
        # At beta=90 the IR term is a real load; the albedo is model-limited (None
        # reportable), with the raw model value ~0 retained separately.
        b = h.starcloud_harmonized_balance(90.0, sunlit_faces=0, warn=False)
        assert b.earth_ir_absorbed_W_m2 > 0.0
        assert b.earth_albedo_absorbed_W_m2 is None
        assert b.earth_albedo_model_W_m2 == pytest.approx(0.0, abs=1e-6)


class TestPublishedEnvironmentPreserved:
    def test_published_load_available_alongside_sweep(self):
        pub = h.published_starcloud_environment()
        assert pub.earth_albedo_absorbed_W_m2 == pytest.approx(9.22, abs=0.01)
        assert pub.earth_ir_absorbed_W_m2 == pytest.approx(5.24, abs=0.01)
        assert pub.earth_combined_absorbed_W_m2 == pytest.approx(14.46, abs=0.01)


class TestEarlierMilestonesUnchanged:
    """Review requirement 6: A2/A3/A4 frozen results are unchanged."""

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
