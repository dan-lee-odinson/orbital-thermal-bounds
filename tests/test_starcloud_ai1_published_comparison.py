"""Starcloud vs AI1 -- as-published comparison (Milestone A4).

The comparison places each architecture under its OWN published assumptions
(no harmonization -- that is A5). These tests verify that:

  * AI1's operating point is DERIVED through the package implementation, not
    hardcoded (the comparison value must equal a direct equilibrium_temperature
    call);
  * quantities AI1 does not publish (solar absorptivity, Earth view factor) are
    marked "not separately published" rather than invented;
  * the published Starcloud numbers (633.08 W/m^2, 189.55 m^2 at 120 kW) and the
    AI1 anchors (337.10 / 353.16 K) are reproduced;
  * the result is framed as a trade, not a ranking.
"""

import pytest

from orbital_thermal.architecture_comparison import (
    AI1_DESIGN_POINT,
    NOT_PUBLISHED,
    compare_as_published,
)
from orbital_thermal.equilibrium import equilibrium_temperature
from orbital_thermal.reference_architectures import STARCLOUD_2024_PUBLISHED


class TestAI1SourcedFromPackage:
    def test_radiator_temperature_is_not_hardcoded(self):
        # The comparison's AI1 temperature must equal a direct package call.
        direct = equilibrium_temperature(120e3, 220.0, 0.91, 220.0)
        assert AI1_DESIGN_POINT.radiator_temperature_K(120e3) == direct

    def test_ai1_anchor_temperatures(self):
        # Companion-paper anchors (verify_ai1 B5).
        assert AI1_DESIGN_POINT.radiator_temperature_K(120e3) == pytest.approx(
            337.1004, abs=1e-3
        )
        assert AI1_DESIGN_POINT.radiator_temperature_K(150e3) == pytest.approx(
            353.1623, abs=1e-3
        )

    def test_ai1_net_flux_consistency(self):
        # Per-emitting via net_flux must equal load/emitting_area by construction.
        assert AI1_DESIGN_POINT.net_flux_per_emitting_m2(120e3) == pytest.approx(
            120e3 / 220.0, rel=1e-12
        )
        assert AI1_DESIGN_POINT.net_flux_per_planform_m2(120e3) == pytest.approx(
            120e3 / 110.0, rel=1e-12
        )


class TestComparisonContent:
    def setup_method(self):
        self.cmp = compare_as_published(120e3)

    def test_basis_is_as_published(self):
        assert self.cmp.basis == "as_published"
        assert self.cmp.heat_load_W == 120e3

    def test_temperature_row(self):
        r = self.cmp.row("radiator_temperature_K")
        assert r.ai1 == pytest.approx(337.10, abs=0.01)
        assert r.starcloud == pytest.approx(293.15, abs=0.01)

    def test_planform_area_row(self):
        r = self.cmp.row("planform_area")
        assert r.ai1 == pytest.approx(110.0, abs=1e-9)
        assert r.starcloud == pytest.approx(189.55, abs=0.05)

    def test_net_rejection_rows(self):
        rp = self.cmp.row("net_rejection_per_planform")
        assert rp.ai1 == pytest.approx(1090.91, abs=0.05)
        assert rp.starcloud == pytest.approx(633.08, abs=0.01)
        re_ = self.cmp.row("net_rejection_per_emitting")
        assert re_.ai1 == pytest.approx(545.45, abs=0.05)
        assert re_.starcloud == pytest.approx(316.54, abs=0.01)

    def test_emissivity_row(self):
        r = self.cmp.row("thermal_emissivity")
        assert r.ai1 == 0.91
        assert r.starcloud == STARCLOUD_2024_PUBLISHED.emissivity_thermal == 0.92


class TestUnpublishedQuantitiesNotInvented:
    def setup_method(self):
        self.cmp = compare_as_published(120e3)

    def test_solar_absorptivity_marked_not_published_for_ai1(self):
        r = self.cmp.row("solar_absorptivity")
        assert r.ai1 is NOT_PUBLISHED
        assert r.starcloud == 0.09

    def test_view_factor_marked_not_published_for_ai1(self):
        r = self.cmp.row("earth_view_factor")
        assert r.ai1 is NOT_PUBLISHED
        assert r.starcloud == 0.25


class TestFramedAsTradeNotRanking:
    def test_scope_note_states_insufficiency(self):
        note = compare_as_published().scope_note.lower()
        assert "insufficient" in note
        # No verdict language.
        for banned in ("is better", "is more efficient", "is wrong", "superior"):
            assert banned not in note

    def test_render_text_is_labelled(self):
        text = compare_as_published().render_text()
        assert "AS-PUBLISHED" in text
        assert "NOT" in text and "ranking" in text
        assert "not separately published" in text  # AI1 optical terms
