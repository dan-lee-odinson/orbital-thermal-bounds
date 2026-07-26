"""S3 (OTB-G002): pressure drop, condenser energy boundary, pump-inlet feasibility.

**R1 class-level regression.** The class S3 guards is *"a constraint the source states
but the artifact does not carry"* — the same family OTB-G001 opened, now reaching the
pressure-drop leg. Four sibling instances plus two controls:

| Sibling | The constraint |
|---|---|
| composition | LM was developed for **two-component** flow; this loop is single-component |
| orientation | LM was developed for **horizontal** flow; this loop is not |
| pressure | "close to atmospheric" is qualitative — no number may be attributed |
| gravity | the static term **is** gravity; D12 makes it an enforced axis, not an omission |

Controls: a case that genuinely satisfies the declared basis must still evaluate, and
the two B1 entries implemented in a module must not be demoted by the DIR-02 rule.

The headline result of this milestone is a **negative** one, and it is asserted here:
no bore in the registry-derived band produces an applicable pressure drop for this
loop, because the reference correlation does not apply to it at all.
"""

from __future__ import annotations

import math
from itertools import pairwise

import pytest

from orbital_thermal import two_phase_loop as loop
from orbital_thermal.registry import NotRankEligibleError, get
from orbital_thermal.registry.applicability import Axis, Consequence
from orbital_thermal.registry.two_phase import (
    GEOMETRY_VOCABULARY,
    STANDARD_GRAVITY_M_S2,
    accelerational_pressure_drop,
    chisholm_C,
    geometry_is_defined,
    lockhart_martinelli_phi_f2,
    lockhart_martinelli_phi_g2,
    martinelli_parameter_X,
    pump_inlet_subcooling_margin,
    static_pressure_drop,
)
from orbital_thermal.registry.two_phase import (
    LOCKHART_MARTINELLI_APPLICABILITY as LM_SPEC,
)

G0 = STANDARD_GRAVITY_M_S2

# A case that satisfies LM's declared basis: two-component, horizontal, round tube.
IN_BASIS = dict(
    composition="two_component", geometry_shape="round_tube", orientation="horizontal"
)
#: The same case in the Applicability.check() vocabulary, which names the key
#: `geometry` where the loop module names it `geometry_shape`.
IN_BASIS_SPEC = dict(
    composition="two_component", geometry="round_tube", orientation="horizontal"
)
# This project's loop: single-component ammonia, not horizontal.
OTB_LOOP = dict(
    composition="single_component",
    geometry_shape="round_tube",
    orientation="vertical_upflow",
)

DP_KW = dict(
    dp_dz_liquid_Pa_m=50.0,
    dp_dz_gas_Pa_m=5.0,
    liquid_regime="turbulent",
    gas_regime="turbulent",
    length_m=1.0,
    mass_flux_kg_m2s=300.0,
    quality_in=0.05,
    quality_out=0.40,
    rho_f=600.0,
    rho_g=8.0,
    pressure_Pa=1.0e6,
)


# =============================================================================
# The sourced maths — established from the source, not recalled
# =============================================================================


def test_the_multiplier_identity_that_establishes_eq_2_68():
    """``phi_g^2 = phi_f^2 X^2`` — how the illegible (2.68) was established.

    (2.68)'s operators are lost in the source's text layer. It is not reconstructed
    from memory: by definition ``phi_f^2 = (dp/dz)_TP/(dp/dz)_f`` and
    ``phi_g^2 = (dp/dz)_TP/(dp/dz)_g``, so with the legible (2.67) the legible (2.69)
    forces ``phi_f^2 = 1 + C/X + 1/X^2``. This asserts that identity holds in the
    implementation, which is what makes the derivation checkable rather than asserted.
    """
    for X in (0.05, 0.5, 1.0, 3.0, 20.0):
        for C in (5.0, 10.0, 12.0, 20.0):
            assert lockhart_martinelli_phi_g2(X, C) == pytest.approx(
                lockhart_martinelli_phi_f2(X, C) * X**2, rel=1e-12
            )


def test_the_chisholm_constants_match_the_source_table():
    """The p. 53 table, and it agrees with the value pinned at S1."""
    assert chisholm_C("turbulent", "turbulent") == 20.0
    assert chisholm_C("laminar", "turbulent") == 12.0
    assert chisholm_C("turbulent", "laminar") == 10.0
    assert chisholm_C("laminar", "laminar") == 5.0
    with pytest.raises(ValueError, match=r"no Chisholm C"):
        chisholm_C("turbulent", "supersonic")


def test_the_multiplier_exceeds_unity_and_falls_with_X():
    """Two-phase friction always exceeds liquid-alone, and more so at low X."""
    values = [lockhart_martinelli_phi_f2(X, 20.0) for X in (0.1, 0.5, 2.0, 10.0)]
    assert all(v > 1.0 for v in values)
    assert all(b < a for a, b in pairwise(values))


def test_martinelli_parameter_requires_two_positive_gradients():
    assert martinelli_parameter_X(50.0, 5.0) == pytest.approx(math.sqrt(10.0))
    for bad in ((0.0, 5.0), (50.0, 0.0), (-1.0, 5.0)):
        with pytest.raises(ValueError, match=r"must be positive"):
            martinelli_parameter_X(*bad)


# =============================================================================
# SIBLING 1 — composition: two-component is a declared basis, and it bites
# =============================================================================


def test_sibling_composition_single_component_is_outside_the_basis():
    v = LM_SPEC.check(**{**IN_BASIS_SPEC, "composition": "single_component"}, gravity_m_s2=G0)
    assert [x.axis for x in v] == [Axis.COMPOSITION]
    assert v[0].consequence is Consequence.DE_RANK
    assert "TWO-COMPONENT" in v[0].detail


def test_sibling_composition_unstated_blocks():
    """Silence is not consent, on this axis as on the others."""
    v = LM_SPEC.check(**{**IN_BASIS_SPEC, "composition": None}, gravity_m_s2=G0)
    assert v and v[0].axis is Axis.COMPOSITION
    assert v[0].consequence is Consequence.BLOCK


# =============================================================================
# SIBLING 2 — orientation: horizontal is a declared basis
# =============================================================================


def test_sibling_orientation_vertical_is_outside_the_basis():
    v = LM_SPEC.check(**{**IN_BASIS_SPEC, "orientation": "vertical_upflow"}, gravity_m_s2=G0)
    assert [x.axis for x in v] == [Axis.ORIENTATION]
    assert v[0].consequence is Consequence.DE_RANK


# =============================================================================
# SIBLING 3 — pressure: the ceiling is unattributable and says so
# =============================================================================


def test_sibling_pressure_ceiling_is_labelled_unattributable():
    """"Close to atmospheric" is qualitative, so no number is attributed to the source."""
    caveats = LM_SPEC.provenance_caveats()
    assert any("NOT traceable" in c for c in caveats)
    assert any("none is invented" in c for c in caveats)

    # ...and the numeric guard is nonetheless enforced.
    entry = get(loop.DP_ID)
    assert entry.domain.ranges["P_Pa"] == (0.1e6, 2.0e6)
    with pytest.raises(NotRankEligibleError, match=r"validity domain"):
        loop.two_phase_pressure_drop(**DP_KW | {"pressure_Pa": 5.0e6}, **IN_BASIS)


# =============================================================================
# SIBLING 4 — gravity: the static term IS gravity (ruling D12)
# =============================================================================


def test_sibling_gravity_static_term_is_computed_not_dropped():
    """``rho g h`` at 1 g is a real contribution, not an omitted one."""
    assert static_pressure_drop(
        rho_mixture_kg_m3=500.0, height_m=2.0, gravity_m_s2=G0
    ) == pytest.approx(500.0 * G0 * 2.0)


def test_sibling_gravity_zero_g_refuses_rather_than_contributing_zero():
    """The rejected option, refused loudly.

    Omitting the static term in microgravity is exact — and that is precisely the
    problem: it would build a microgravity model out of a 1g-derived frictional
    correlation, leaving a model exact in one term and terrestrial in the next with
    nothing marking the seam. So the term refuses instead of quietly returning zero.
    """
    with pytest.raises(ValueError, match=r"free fall|out of applicability"):
        static_pressure_drop(rho_mixture_kg_m3=500.0, height_m=2.0, gravity_m_s2=0.0)


def test_sibling_gravity_is_a_declared_axis_consistent_with_shah_1987():
    """D12 asks for consistency between the two legs, so it is asserted."""
    shah_spec = get("two_phase.chf.shah_1987").applicability_spec
    assert LM_SPEC.reference_gravity_m_s2 == shah_spec.reference_gravity_m_s2 == G0
    v = LM_SPEC.check(**IN_BASIS_SPEC, gravity_m_s2=1.0e-6)
    assert any(x.axis is Axis.ORIENTATION for x in v)


# =============================================================================
# CONTROLS
# =============================================================================


def test_control_a_case_inside_the_declared_basis_evaluates_cleanly():
    """Enforcement that refuses everything is breakage, not rigour."""
    result = loop.two_phase_pressure_drop(**DP_KW, **IN_BASIS)
    assert result.violations == ()
    assert result.is_applicable
    assert result.total_Pa > 0.0
    assert result.frictional_Pa > 0.0


def test_control_the_components_sum_to_the_total():
    r = loop.two_phase_pressure_drop(**DP_KW, **IN_BASIS, height_m=1.5)
    assert r.total_Pa == pytest.approx(
        r.frictional_Pa + r.accelerational_Pa + r.static_Pa
    )
    assert r.static_Pa > 0.0, "a 1.5 m rise at 1 g contributes real static head"


# =============================================================================
# The headline: this loop is outside the reference correlation entirely
# =============================================================================


def test_this_loop_violates_the_correlation_on_two_axes_at_once():
    r = loop.two_phase_pressure_drop(**DP_KW, **OTB_LOOP)
    axes = {v.axis for v in r.violations}
    assert axes == {Axis.COMPOSITION, Axis.ORIENTATION}
    assert not r.is_applicable
    assert r.total_Pa > 0.0, "the number is still computed — it is reported, not ranked"


def test_the_negative_result_is_the_result():
    """No bore in the band produces an applicable pressure drop (ruling D7)."""
    sweep = loop.sweep_bore(
        diameters_m=(2.0e-3, 8.0e-3, 2.0e-2),
        duty_W=1000.0,
        mass_flow_kg_s=0.01,
        h_in_J_kg=0.0,
        h_out_J_kg=1.0e5,
        wall_flux_W_m2=5.0e4,
        dp_dz_liquid_Pa_m=50.0,
        dp_dz_gas_Pa_m=5.0,
        liquid_regime="turbulent",
        gas_regime="turbulent",
        mass_flux_kg_m2s=300.0,
        quality_in=0.05,
        quality_out=0.40,
        rho_f=600.0,
        rho_g=8.0,
        pressure_Pa=1.0e6,
        **OTB_LOOP,
    )
    assert sweep.any_applicable is False
    summary = sweep.summary()
    assert "NEGATIVE RESULT" in summary
    # Ruling D11: the provenance-unestablished label must travel INTO the reported
    # output, not sit in a comment. The mutation witness caught that this test checked
    # only for the negative-result line and would have passed with the label dropped.
    assert "PROVENANCE-UNESTABLISHED" in summary
    assert "DEBTS D-1" in summary


# =============================================================================
# The bore band is DERIVED, and length is too (ruling D11)
# =============================================================================


def test_the_bore_band_is_read_from_the_registry_not_hard_coded():
    band = loop.bore_band()
    gw = get("two_phase.htc.gungor_winterton").domain.ranges["D_m"]
    shah = get("two_phase.chf.shah_1987").domain.ranges["D_m"]
    assert band.min_m == max(gw[0], shah[0])
    assert band.max_m == min(gw[1], shah[1])
    assert band.binding_entry_id == "two_phase.htc.gungor_winterton", "GW86 binds both ends"


def test_the_band_carries_its_provenance_label_into_the_output():
    """Ruling D11: the label appears in the reported result, not a comment."""
    band = loop.bore_band()
    assert "PROVENANCE-UNESTABLISHED" in band.provenance_label
    assert "DEBTS D-1" in band.provenance_label


def test_length_is_derived_from_duty_and_checked_against_the_enthalpy_rise():
    length = loop.required_length_m(
        duty_W=1000.0,
        mass_flow_kg_s=0.01,
        h_in_J_kg=0.0,
        h_out_J_kg=1.0e5,
        diameter_m=8.0e-3,
        wall_flux_W_m2=5.0e4,
    )
    assert length == pytest.approx((1000.0 / 5.0e4) / (math.pi * 8.0e-3))

    # A duty that disagrees with the enthalpy rise it claims is refused, not averaged.
    with pytest.raises(ValueError, match=r"disagrees with the enthalpy rise"):
        loop.required_length_m(
            duty_W=5000.0,
            mass_flow_kg_s=0.01,
            h_in_J_kg=0.0,
            h_out_J_kg=1.0e5,
            diameter_m=8.0e-3,
            wall_flux_W_m2=5.0e4,
        )


def test_a_bore_outside_the_band_is_recorded_not_dropped():
    """A sweep that silently omitted its failures could not report a negative result."""
    sweep = loop.sweep_bore(
        diameters_m=(0.5e-3, 8.0e-3),  # first is below the band
        duty_W=1000.0,
        mass_flow_kg_s=0.01,
        h_in_J_kg=0.0,
        h_out_J_kg=1.0e5,
        wall_flux_W_m2=5.0e4,
        dp_dz_liquid_Pa_m=50.0,
        dp_dz_gas_Pa_m=5.0,
        liquid_regime="turbulent",
        gas_regime="turbulent",
        mass_flux_kg_m2s=300.0,
        quality_in=0.05,
        quality_out=0.40,
        rho_f=600.0,
        rho_g=8.0,
        pressure_Pa=1.0e6,
        **IN_BASIS,
    )
    assert len(sweep.points) == 2
    assert not sweep.points[0].evaluated
    assert "outside the registry-derived band" in sweep.points[0].blocked_reason
    assert sweep.points[1].evaluated


# =============================================================================
# The condenser is an ENERGY BOUNDARY (ruling D10)
# =============================================================================


def test_the_condenser_closes_its_energy_books():
    c = loop.condenser_energy_boundary(
        mass_flow_kg_s=0.01,
        h_in_J_kg=1.2e5,
        h_out_J_kg=2.0e4,
        sink_temperature_K=250.0,
        saturation_temperature_K=300.0,
        outlet_is_liquid=True,
    )
    assert c.duty_W == pytest.approx(0.01 * (1.2e5 - 2.0e4))
    assert c.energy_closes
    assert c.rejects_to_a_colder_sink


def test_the_condenser_refuses_to_size_itself():
    """No condensation coefficient is computed or estimated at S3 (D10, DEBTS D-11)."""
    c = loop.condenser_energy_boundary(
        mass_flow_kg_s=0.01,
        h_in_J_kg=1.2e5,
        h_out_J_kg=2.0e4,
        sink_temperature_K=250.0,
        saturation_temperature_K=300.0,
        outlet_is_liquid=True,
    )
    with pytest.raises(NotRankEligibleError, match=r"condensation heat-transfer"):
        c.required_area_m2()


def test_no_condensation_entry_was_added_to_the_registry():
    """D10 defers condensation to S4; adding a placeholder entry is excluded."""
    from orbital_thermal.registry import TWO_PHASE_CORRELATIONS

    assert not [c for c in TWO_PHASE_CORRELATIONS if "condens" in c.id.lower()]
    assert not [c for c in TWO_PHASE_CORRELATIONS if c.kind == "condensation"]


def test_a_condenser_that_adds_heat_is_refused():
    with pytest.raises(ValueError, match=r"removes heat"):
        loop.condenser_energy_boundary(
            mass_flow_kg_s=0.01,
            h_in_J_kg=2.0e4,
            h_out_J_kg=1.2e5,
            sink_temperature_K=250.0,
            saturation_temperature_K=300.0,
            outlet_is_liquid=True,
        )


# =============================================================================
# Pump-inlet feasibility is a SUBCOOLING margin (ruling D8)
# =============================================================================


def test_pump_inlet_subcooled_liquid_is_feasible():
    v = loop.pump_inlet_feasibility(
        saturation_temperature_K=300.0, inlet_temperature_K=285.0, inlet_is_liquid=True
    )
    assert v.subcooling_margin_K == pytest.approx(15.0)
    assert v.feasible


def test_pump_inlet_at_saturation_is_the_cavitation_condition():
    v = loop.pump_inlet_feasibility(
        saturation_temperature_K=300.0, inlet_temperature_K=300.0, inlet_is_liquid=True
    )
    assert v.subcooling_margin_K == pytest.approx(0.0)
    assert not v.feasible
    assert "cavitation" in v.reason


def test_pump_inlet_vapour_is_refused_regardless_of_margin():
    v = loop.pump_inlet_feasibility(
        saturation_temperature_K=300.0, inlet_temperature_K=250.0, inlet_is_liquid=False
    )
    assert v.subcooling_margin_K > 0.0
    assert not v.feasible
    assert "not liquid" in v.reason


def test_no_non_zero_subcooling_default_is_invented():
    """AMS-02 establishes the criterion, not a number; choosing one would be a guess."""
    import inspect

    sig = inspect.signature(loop.pump_inlet_feasibility)
    assert sig.parameters["required_margin_K"].default == 0.0
    assert pump_inlet_subcooling_margin(
        saturation_temperature_K=300.0, inlet_temperature_K=290.0
    ) == pytest.approx(10.0)


# =============================================================================
# DIR-01 — the geometry vocabulary is defined
# =============================================================================


def test_dir01_round_tube_and_channel_are_defined_and_disjoint():
    """A 2.6 mm bore cannot be simultaneously inside and outside a declared basis."""
    assert geometry_is_defined("round_tube")
    assert geometry_is_defined("channel")
    assert not geometry_is_defined("cold_plate")

    assert "circular" in GEOMETRY_VOCABULARY["round_tube"].lower()
    assert "non-circular" in GEOMETRY_VOCABULARY["channel"].lower().replace("–", "-")
    assert "disjoint" in GEOMETRY_VOCABULARY["channel"].lower()


def test_dir01_small_bore_is_not_a_separate_geometry():
    """D9's family is the small-bore round tube; 'small-bore' describes the bore."""
    assert "NOT a separate geometry" in GEOMETRY_VOCABULARY["round_tube"]


def test_dir01_the_corrected_note_no_longer_claims_the_evaporator_is_channels():
    entry = get("two_phase.chf.shah_2015")
    assert "The S2 evaporator geometry is channels" not in entry.source.note
    assert "DIR-01 CORRECTION" in entry.source.note


# =============================================================================
# Acceleration term
# =============================================================================


def test_acceleration_term_is_positive_when_evaporating():
    dp = accelerational_pressure_drop(
        mass_flux_kg_m2s=300.0, quality_in=0.05, quality_out=0.4, rho_f=600.0, rho_g=8.0
    )
    assert dp > 0.0


def test_acceleration_term_is_zero_at_constant_quality():
    assert accelerational_pressure_drop(
        mass_flux_kg_m2s=300.0, quality_in=0.3, quality_out=0.3, rho_f=600.0, rho_g=8.0
    ) == pytest.approx(0.0)
