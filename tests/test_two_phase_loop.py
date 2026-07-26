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
import pathlib
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

# Physical inputs only. The hydraulic state -- mass flux, both phase Reynolds numbers,
# both regimes and both phase-alone gradients -- is DERIVED from the bore (F-01), and
# the regimes are computed, never declared (F-02).
DP_KW = dict(
    mass_flow_kg_s=0.01,
    diameter_m=8.0e-3,
    length_m=1.0,
    quality_in=0.05,
    quality_out=0.40,
    rho_f=600.0,
    rho_g=8.0,
    mu_f=1.3e-4,
    mu_g=9.0e-6,
    pressure_Pa=1.0e6,
)

# Physical inputs a bore sweep needs, minus the diameter it varies.
SWEEP_KW = dict(
    duty_W=1000.0,
    mass_flow_kg_s=0.01,
    h_in_J_kg=0.0,
    h_out_J_kg=1.0e5,
    wall_flux_W_m2=5.0e4,
    quality_in=0.05,
    quality_out=0.40,
    rho_f=600.0,
    rho_g=8.0,
    mu_f=1.3e-4,
    mu_g=9.0e-6,
    pressure_Pa=1.0e6,
)


# =============================================================================
# The sourced maths — established from the source, not recalled
# =============================================================================


def test_the_multiplier_identity_confirms_the_printed_eq_2_68():
    """``phi_g^2 = phi_f^2 X^2`` — an independent confirmation of the printed (2.68).

    Eq. (2.68) is **read from the printed page**: ``phi_f^2 = 1 + C/X + 1/X^2``. This
    identity is not its source; it is a cross-check that the printed (2.68) and the
    printed (2.69) are consistent with the definition of ``X`` in (2.67), which is
    worth having because it would catch a transcription slip in either one.

    (An earlier version of this docstring called (2.68) illegible. It is not — the
    PDF's *text layer* is degraded, the page is sharp. See V-02.)
    """
    for X in (0.05, 0.5, 1.0, 3.0, 20.0):
        for C in (5.0, 10.0, 12.0, 20.0):
            assert lockhart_martinelli_phi_g2(X, C) == pytest.approx(
                lockhart_martinelli_phi_f2(X, C) * X**2, rel=1e-12
            )


#: V-02 R1 regression. The class is *"the artifact says something false about the
#: source, in the fields whose job is to be true about it"*. The provenance fields are
#: the sibling set: the entry note, the applicability text, the module comment, the
#: implementation docstring and this test module. The control is that the true
#: limitation -- the degraded TEXT LAYER -- is still recorded, because deleting the
#: false claim must not also delete the real caveat.
_ILLEGIBILITY_CLAIMS = (
    "not legible",
    "NOT legible",
    "operators are lost",
    "operators lost",
    "rather than recalled",
    "derivation rather than recall",
)


def _provenance_text() -> dict[str, str]:
    entry = get(loop.DP_ID)
    import orbital_thermal.registry.two_phase as reg

    return {
        "entry.source.note": entry.source.note,
        "entry.applicability": entry.applicability,
        "entry.formula": entry.formula,
        "module docstring/comments": pathlib.Path(reg.__file__).read_text(
            encoding="utf-8"
        ),
        "phi_f2 docstring": lockhart_martinelli_phi_f2.__doc__ or "",
    }


@pytest.mark.parametrize("claim", _ILLEGIBILITY_CLAIMS)
def test_v02_no_provenance_field_claims_the_equation_was_illegible(claim):
    """Eq. (2.68) is sharply printed on p. 53. The artifact must not say otherwise.

    What was degraded is the PDF's embedded **text layer**, not the source. An
    automated extraction returning ``"1 + _ + _2"`` is a transcription -- just one
    nobody typed -- so describing it as the source was exactly the failure the "read
    the page" rule exists to prevent. It landed on the right number, which is why it
    needed catching: had it not, a false justification would have shipped attached to
    it and nothing would have prompted anyone to look at the page.
    """
    for where, text in _provenance_text().items():
        assert claim not in text, f"illegibility claim {claim!r} survives in {where}"


def test_v02_the_equation_is_recorded_as_read_from_the_page():
    text = _provenance_text()
    assert "READ FROM THE RENDERED PAGES" in text["entry.source.note"]
    assert "as printed" in text["entry.formula"]


def test_v02_control_the_true_limitation_is_still_recorded():
    """Removing the false claim must not remove the real caveat.

    The text layer *is* degraded, and that is worth knowing: it is why anything from
    this source must be read from the rendered page.
    """
    note = _provenance_text()["entry.source.note"]
    assert "text layer" in note
    assert "degraded" in note
    assert "rendered page" in note
    assert "transcription" in note


def test_v02_control_the_derivation_survives_relabelled_as_confirmation():
    """The cross-check is a good test and is kept -- as confirmation, not as source."""
    note = _provenance_text()["entry.source.note"]
    assert "INDEPENDENT CONFIRMATION" in note
    assert "not its source" in note


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
    """The three components sum, and a de-ranked case still reports all of them.

    Uses the non-horizontal loop deliberately: a *horizontal* case with a static height
    is now a self-contradiction (F-02), and this control was unknowingly depending on
    that being permitted.
    """
    r = loop.two_phase_pressure_drop(**DP_KW, **OTB_LOOP, height_m=1.5)
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
    """No bore in the band produces an applicable pressure drop for THIS loop (D7).

    Re-established on a sweep whose hydraulics actually move (F-01): mass flux, both
    phase Reynolds numbers, both regimes and both phase-alone gradients are now derived
    from the bore at every point. The refusal is the same and for the same sourced
    reason -- composition and orientation -- but it is now *earned*, because the space
    was explored rather than held constant.
    """
    sweep = loop.sweep_bore(
        diameters_m=(2.0e-3, 8.0e-3, 2.0e-2),
        **SWEEP_KW,
        **OTB_LOOP,
        fluid="Ammonia",
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
        **SWEEP_KW,
        **IN_BASIS,
    )
    assert len(sweep.points) == 2
    assert not sweep.points[0].evaluated
    assert "outside the registry-derived band" in sweep.points[0].blocked_reason
    assert sweep.points[1].evaluated


# =============================================================================
# F-01 — the sweep's hydraulic state is DERIVED from bore
#
# R1 class: "a swept variable that does not reach the physics it is supposed to move".
# Four siblings -- mass flux, both phase Reynolds numbers, the phase-alone gradients,
# and the acceleration term -- plus the control that the derivation is arithmetically
# right rather than merely varying.
# =============================================================================


PROPS = dict(rho_f=600.0, rho_g=8.0, mu_f=1.3e-4, mu_g=9.0e-6)


def _states(diameters, mass_flow=0.01, quality=0.225):
    return [
        loop.hydraulic_state_from_bore(
            mass_flow_kg_s=mass_flow, diameter_m=d, quality=quality, **PROPS
        )
        for d in diameters
    ]


def test_f01_mass_flux_moves_with_bore():
    """It is ``m_dot / (pi D^2 / 4)`` -- held constant, the sweep swept nothing.

    Measured on the adopted band at 0.01 kg/s: 8498.6 kg/m2s at 1.224 mm against
    12.4 at 32 mm, a factor of 683 that the build held at one value.
    """
    band = loop.bore_band()
    lo, hi = _states([band.min_m, band.max_m])
    assert lo.mass_flux_kg_m2s == pytest.approx(
        0.01 / (math.pi * band.min_m**2 / 4), rel=1e-12
    )
    assert lo.mass_flux_kg_m2s / hi.mass_flux_kg_m2s == pytest.approx(683.0, rel=0.01)


def test_f01_both_phase_reynolds_numbers_move_with_bore():
    states = _states([1.5e-3, 8.0e-3, 3.0e-2])
    assert all(b < a for a, b in pairwise([s.reynolds_liquid for s in states]))
    assert all(b < a for a, b in pairwise([s.reynolds_gas for s in states]))


def test_f01_both_phase_alone_gradients_move_with_bore():
    states = _states([1.5e-3, 8.0e-3, 3.0e-2])
    assert all(b < a for a, b in pairwise([s.dp_dz_liquid_Pa_m for s in states]))
    assert all(b < a for a, b in pairwise([s.dp_dz_gas_Pa_m for s in states]))


def test_f01_the_acceleration_term_now_moves_with_bore():
    """It did not vary with bore at all before, because it takes the mass flux."""
    totals = [
        accelerational_pressure_drop(
            mass_flux_kg_m2s=s.mass_flux_kg_m2s,
            quality_in=0.05,
            quality_out=0.40,
            rho_f=600.0,
            rho_g=8.0,
        )
        for s in _states([1.5e-3, 8.0e-3, 3.0e-2])
    ]
    assert all(b < a for a, b in pairwise(totals))


def test_f01_control_the_derivation_is_arithmetically_right():
    """Varying is not enough; the numbers must be the ones physics gives."""
    d, mdot, x = 8.0e-3, 0.01, 0.3
    s = _states([d], mass_flow=mdot, quality=x)[0]
    g = mdot / (math.pi * d**2 / 4)
    assert s.mass_flux_kg_m2s == pytest.approx(g, rel=1e-12)
    assert s.reynolds_liquid == pytest.approx(g * (1 - x) * d / PROPS["mu_f"], rel=1e-12)
    assert s.reynolds_gas == pytest.approx(g * x * d / PROPS["mu_g"], rel=1e-12)
    assert s.liquid_regime == ("laminar" if s.reynolds_liquid <= 2300 else "turbulent")


def test_f01_the_sweep_records_the_flux_it_used_at_every_point():
    """A sweep must be able to show that its hydraulics moved.

    Nothing in the old output could have revealed that they did not.
    """
    sweep = loop.sweep_bore(
        diameters_m=(1.5e-3, 8.0e-3, 3.0e-2), **SWEEP_KW, **OTB_LOOP, fluid="Ammonia"
    )
    fluxes = [p.mass_flux_kg_m2s for p in sweep.points]
    assert all(f is not None for f in fluxes)
    assert len(set(fluxes)) == 3, "every bore must have its own flux"
    assert all(b < a for a, b in pairwise(fluxes))


def test_f01_no_hydraulic_scalar_can_be_supplied_to_the_sweep():
    """The parameters that made the defect possible are gone from the signature."""
    import inspect

    params = inspect.signature(loop.sweep_bore).parameters
    for gone in (
        "mass_flux_kg_m2s",
        "dp_dz_liquid_Pa_m",
        "dp_dz_gas_Pa_m",
        "liquid_regime",
        "gas_regime",
    ):
        assert gone not in params, (
            f"{gone} must not be caller-supplied: it is derived from bore, and "
            "accepting it is what let the sweep hold it constant"
        )


# =============================================================================
# F-02 — regime is computed; the remaining declarations are cross-checked
# =============================================================================


def test_f02_flow_regime_is_computed_never_declared():
    """Reynolds number decides the regime, so the Chisholm C follows from the state."""
    import inspect

    params = inspect.signature(loop.two_phase_pressure_drop).parameters
    assert "liquid_regime" not in params and "gas_regime" not in params

    laminar = _states([3.0e-2], mass_flow=0.001)[0]
    turbulent = _states([2.0e-3], mass_flow=0.05)[0]
    assert laminar.liquid_regime == "laminar"
    assert turbulent.liquid_regime == "turbulent"


def test_f02_a_single_component_fluid_declared_two_component_is_a_contradiction():
    """Composition is not derivable from densities, but it is not freely assertable."""
    with pytest.raises(NotRankEligibleError, match=r"cannot both be true"):
        loop.two_phase_pressure_drop(
            **DP_KW,
            composition="two_component",
            geometry_shape="round_tube",
            orientation="horizontal",
            fluid="Ammonia",
        )


def test_f02_horizontal_with_a_static_height_is_a_contradiction():
    """The static head is identically zero in horizontal flow."""
    with pytest.raises(NotRankEligibleError, match=r"contradicts the label"):
        loop.two_phase_pressure_drop(**DP_KW, **IN_BASIS, height_m=1.5)


def test_f02_the_contradiction_check_is_at_the_boundary_not_the_sweep():
    """C9: enforcing in ``sweep_bore`` alone would not have closed the class."""
    from orbital_thermal.registry.applicability import case_contradictions

    assert case_contradictions(
        fluid="Ammonia",
        composition="two_component",
        single_component_fluids=loop.REGISTERED_SINGLE_COMPONENT_FLUIDS,
    )
    # ...and the sweep inherits it, because it goes through the same boundary.
    sweep = loop.sweep_bore(
        diameters_m=(8.0e-3,),
        **SWEEP_KW,
        composition="two_component",
        geometry_shape="round_tube",
        orientation="horizontal",
        fluid="Ammonia",
    )
    assert not sweep.points[0].evaluated
    assert "cannot both be true" in sweep.points[0].blocked_reason


def test_f02_control_a_consistent_case_is_not_obstructed():
    """Water in a horizontal two-component rig is contradictory; a mixture is not."""
    from orbital_thermal.registry.applicability import case_contradictions

    assert (
        case_contradictions(
            fluid="air-water",
            composition="two_component",
            orientation="horizontal",
            height_m=0.0,
            single_component_fluids=loop.REGISTERED_SINGLE_COMPONENT_FLUIDS,
        )
        == ()
    )


# =============================================================================
# F-03 — the settled x -> 0 limiting case, against the Stage-1 oracle
# =============================================================================


def test_f03_x_to_zero_recovers_the_stage1_single_phase_pressure_drop():
    """S0 settles it: as ``x -> 0``, ``phi^2 -> 1`` and dP recovers Stage-1's dP.

    Oracle is **Stage-1's own single-phase pressure drop**, not a literal, so the test
    cannot drift away from the thing it claims to recover. The limit already held; this
    is the missing test of correct behaviour, not a repair.
    """
    from orbital_thermal import pumped_loop as pl

    d, mdot, length = 8.0e-3, 0.01, 1.0
    rho_f, mu_f = PROPS["rho_f"], PROPS["mu_f"]

    area = math.pi * d**2 / 4
    g = mdot / area
    velocity = g / rho_f
    single_phase = pl.pressure_drop(
        pl.friction_factor(g * d / mu_f), length, d, rho_f, velocity
    )

    qualities = (1.0e-3, 1.0e-4, 1.0e-5, 1.0e-6, 1.0e-7, 1.0e-8)
    ratios = [
        loop.two_phase_pressure_drop(
            **DP_KW | {"quality_in": x, "quality_out": x}, **IN_BASIS
        ).frictional_Pa
        / single_phase
        for x in qualities
    ]

    assert all(b < a for a, b in pairwise(ratios)), (
        f"the frictional multiplier must fall monotonically toward 1; got {ratios}"
    )
    assert ratios[-1] == pytest.approx(1.0, rel=2.0e-3), (
        f"as x -> 0 the two-phase dP must recover the Stage-1 single-phase dP; "
        f"ratio at x = 1e-8 is {ratios[-1]:.6f}"
    )


def test_f03_the_approach_to_the_single_phase_limit_is_order_sqrt_x():
    """*How* it converges, not just that it does -- and the rate is a real prediction.

    Laminar gas friction gives ``f_g = 64/Re_g ~ 1/x`` and ``v_g ~ x``, so the gas-alone
    gradient vanishes as ``x`` and ``X ~ x^-1/2``. With ``phi_f^2 ~ 1 + C/X`` the excess
    over the single-phase drop must therefore fall as ``sqrt(x)``. Measured constant
    ``9.635``, stable to three figures across five decades -- a slow convergence, which is
    why a 1e-5 probe would read a 3% residual as a failure to recover.
    """
    from orbital_thermal import pumped_loop as pl

    d, mdot, length = 8.0e-3, 0.01, 1.0
    rho_f, mu_f = PROPS["rho_f"], PROPS["mu_f"]
    g = mdot / (math.pi * d**2 / 4)
    single_phase = pl.pressure_drop(
        pl.friction_factor(g * d / mu_f), length, d, rho_f, g / rho_f
    )

    constants = []
    for x in (1.0e-4, 1.0e-5, 1.0e-6, 1.0e-7, 1.0e-8):
        ratio = (
            loop.two_phase_pressure_drop(
                **DP_KW | {"quality_in": x, "quality_out": x}, **IN_BASIS
            ).frictional_Pa
            / single_phase
        )
        constants.append((ratio - 1.0) / math.sqrt(x))

    assert all(c == pytest.approx(9.635, rel=5.0e-3) for c in constants), (
        f"excess over the single-phase drop must scale as sqrt(x); got {constants}"
    )


def test_f03_the_multiplier_itself_tends_to_one():
    """The mechanism behind the limit: ``phi_f^2 -> 1`` as ``X -> infinity``."""
    values = [lockhart_martinelli_phi_f2(X, 20.0) for X in (10.0, 1.0e2, 1.0e4, 1.0e6)]
    assert all(b < a for a, b in pairwise(values))
    assert values[-1] == pytest.approx(1.0, abs=1e-4)


# =============================================================================
# F-04 — non-numbers and impossible qualities are refused
#
# R1 class: "a guard expressed as a sign test, which NaN passes". Four sibling input
# families -- gradient-driving inputs, mass flow, density, quality -- plus the control
# that a valid case still evaluates.
# =============================================================================


@pytest.mark.parametrize(
    "bad",
    [
        {"mass_flow_kg_s": float("nan")},
        {"diameter_m": float("nan")},
        {"rho_f": float("nan")},
        {"rho_g": float("nan")},
        {"mu_f": float("nan")},
        {"pressure_Pa": float("nan")},
        {"length_m": float("nan")},
        {"mass_flow_kg_s": float("inf")},
        {"rho_f": float("inf")},
    ],
)
def test_f04_a_non_finite_input_is_refused_not_returned_as_nan(bad):
    """NaN comparisons are always false, so ``> 0`` passed it straight through.

    The boundary returned ``total_Pa = nan`` marked applicable -- a number nobody can
    distinguish from a real one. Finiteness is now checked explicitly.
    """
    with pytest.raises(ValueError, match=r"must be finite|must be > 0"):
        loop.two_phase_pressure_drop(**DP_KW | bad, **IN_BASIS)


@pytest.mark.parametrize("quality", [1.7, -0.5, 1.0000001, -1e-9, float("nan")])
def test_f04_an_impossible_quality_is_refused(quality):
    """Quality is a mass fraction; 1.7 and -0.5 produced confident finite numbers."""
    with pytest.raises(ValueError, match=r"must be in|must be finite"):
        loop.two_phase_pressure_drop(
            **DP_KW | {"quality_in": quality, "quality_out": quality}, **IN_BASIS
        )


def test_f04_a_non_finite_gravity_or_height_is_refused():
    with pytest.raises(ValueError):
        loop.two_phase_pressure_drop(**DP_KW, **IN_BASIS, gravity_m_s2=float("nan"))
    with pytest.raises(ValueError):
        loop.two_phase_pressure_drop(**DP_KW, **OTB_LOOP, height_m=float("nan"))


def test_f04_control_a_valid_case_still_evaluates():
    """The control: the validation must not refuse the physical cases."""
    r = loop.two_phase_pressure_drop(**DP_KW, **IN_BASIS)
    assert math.isfinite(r.total_Pa) and r.total_Pa > 0.0
    assert r.is_applicable


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
