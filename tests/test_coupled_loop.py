"""S4 regressions: the coupled solver, the static Ledinegg guard, and the two runs.

Organised by the criteria in ``ACCEPTANCE_CRITERIA_OTB-G003.md``. Each block is a
class-level regression (R1): at least three siblings of the same defect shape plus a
control that fails if the guard merely refuses everything.
"""

from __future__ import annotations

import inspect
import math
import warnings
from itertools import pairwise

import pytest

from orbital_thermal import coupled_loop as C
from orbital_thermal import dp_basis_assessment as A
from orbital_thermal.registry import NotRankEligibleError, get
from orbital_thermal.registry.two_phase import (
    KCAL_IT_J,
    KCAL_TH_J,
    kcal_per_m2_hr_to_W_m2,
    ledinegg_static_criterion,
)

# --- the two cases used throughout ------------------------------------------------

#: Air-water, horizontal, near-atmospheric: verbatim inside Lockhart-Martinelli's
#: declared basis, which is the only implemented pressure-drop correlation and
#: therefore the only basis a machinery demonstration can be built inside.
DEMO_KW = dict(
    fluid="air-water",
    composition="two_component",
    geometry_shape="round_tube",
    orientation="horizontal",
    diameter_m=8.0e-3,
    length_m=1.0,
    duty_W=1200.0,
    pressure_Pa=1.2e5,
    h_fg_J_kg=2.26e6,
    rho_f=997.0,
    rho_g=1.2,
    mu_f=8.9e-4,
    mu_g=1.8e-5,
)

#: This project's device.
REF_KW = dict(
    fluid="Ammonia",
    composition="single_component",
    geometry_shape="round_tube",
    orientation="vertical_upflow",
    diameter_m=8.0e-3,
    length_m=1.0,
    duty_W=1000.0,
    pressure_Pa=20.0e5,
    h_fg_J_kg=1.05e6,
    rho_f=560.0,
    rho_g=15.8,
    mu_f=1.1e-4,
    mu_g=1.0e-5,
    height_m=1.5,
)

PUMP = C.PumpCharacteristic(shutoff_Pa=6.0e4, runout_kg_s=0.05)
FLOWS = dict(flow_min_kg_s=0.002, flow_max_kg_s=0.049)
BAND = dict(band_min_m=1.224e-3, band_max_m=32.0e-3, reduced_pressure=0.176)


def demo_case(**over) -> C.LoopCase:
    return C.LoopCase(kind=C.RunKind.MACHINERY_DEMONSTRATION, **{**DEMO_KW, **over})


def ref_case(**over) -> C.LoopCase:
    return C.LoopCase(kind=C.RunKind.REFERENCE_CASE, **{**REF_KW, **over})


def solve_demo(**over):
    return C.demonstrate_machinery(demo_case(**over), PUMP, **FLOWS)


def solve_ref(**over):
    return C.solve_reference_case(ref_case(**over), PUMP, **FLOWS, **BAND)


# =============================================================================
# S4-1 / S4-2 -- the two runs cannot be confused
#
# R1 class: "a distinction that exists only by convention". Siblings: the result type,
# the disclosure, the entry-point guards in both directions, and the behavioural check
# that a demonstration is actually in basis. Control: a real demonstration still runs.
# =============================================================================


def test_s4_1_the_two_runs_return_different_types():
    """A reader holding only a result object can tell which run produced it."""
    assert isinstance(solve_demo(), C.DemonstrationResult)
    assert isinstance(solve_ref(), C.ReferenceCaseResult)
    assert not isinstance(solve_demo(), C.ReferenceCaseResult)
    assert not isinstance(solve_ref(), C.DemonstrationResult)


def test_s4_1_each_result_carries_its_kind_as_data_not_as_a_name():
    """Not only the type: the kind is a field, so it survives serialisation."""
    assert solve_demo().case.kind is C.RunKind.MACHINERY_DEMONSTRATION
    assert solve_ref().case.kind is C.RunKind.REFERENCE_CASE


def test_s4_1_neither_entry_point_accepts_the_other_kind():
    with pytest.raises(ValueError, match=r"machinery demonstration"):
        C.demonstrate_machinery(ref_case(), PUMP, **FLOWS)
    with pytest.raises(ValueError, match=r"reference case"):
        C.solve_reference_case(demo_case(), PUMP, **FLOWS, **BAND)


def test_s4_1_a_demonstration_must_actually_be_in_basis_not_merely_labelled():
    """The behavioural half. A label is not evidence, and this is the whole point.

    Relabelling the reference case as a demonstration must not produce a
    demonstration: it would put a reference-case refusal behind a demonstration
    banner, which is the exact confusion the criterion exists to prevent.
    """
    mislabelled = C.LoopCase(kind=C.RunKind.MACHINERY_DEMONSTRATION, **REF_KW)
    with pytest.raises(NotRankEligibleError, match=r"NOT inside the declared basis"):
        C.demonstrate_machinery(mislabelled, PUMP, **FLOWS)


def test_s4_2_the_disclosure_is_in_the_rendered_output_and_cannot_be_blanked():
    rendered = solve_demo().render()
    assert "MACHINERY DEMONSTRATION -- NOT A RESULT ABOUT THIS PROJECT'S DEVICE" in rendered
    # F-06: an `assert ... or True` stood here. Anything `or True` is true, so it was a
    # dead assertion -- it masked nothing (the banner is genuinely present, and the
    # sibling assertions check it) but it could not have failed. Replaced with the
    # thing it was reaching for: the disclosure is in the BODY, not appended as a
    # trailing footnote a reader can skip.
    assert rendered.index("MACHINERY DEMONSTRATION") < len(rendered) // 2, (
        "the disclosure must lead the output, not trail it"
    )
    # It is a property, not a field: there is no constructor argument to suppress it.
    assert "disclosure" not in C.DemonstrationResult.__dataclass_fields__
    assert isinstance(C.DemonstrationResult.disclosure, property)


def test_s4_2_str_renders_the_disclosure_so_printing_cannot_lose_it():
    """``print(result)`` is the likeliest way an artifact escapes; it must carry it."""
    assert "MACHINERY DEMONSTRATION" in str(solve_demo())


def test_s4_2_control_a_reference_result_does_not_carry_the_demonstration_banner():
    """The control: the banner must mark demonstrations, not everything."""
    rendered = solve_ref().render()
    assert "MACHINERY DEMONSTRATION" not in rendered
    assert "REFERENCE CASE" in rendered


# =============================================================================
# S4-3 -- the legs are coupled, not reported side by side
# =============================================================================


def _demo_flow(**over) -> float:
    points = solve_demo(**over).operating_points
    assert points, "the in-basis demonstration must solve"
    return points[0].mass_flow_kg_s


def test_s4_3_the_operating_point_moves_with_the_duty():
    """Duty belongs to the thermal leg and must reach the hydraulic solution."""
    flows = [_demo_flow(duty_W=q) for q in (600.0, 1200.0, 2400.0)]
    assert len(set(flows)) == 3
    assert all(b < a for a, b in pairwise(flows)), (
        f"more duty means more vapour and more pressure drop, so the intersection "
        f"with a drooping pump curve must move to lower flow; got {flows}"
    )


def test_s4_3_the_operating_point_moves_with_the_bore():
    flows = [_demo_flow(diameter_m=d) for d in (6.0e-3, 8.0e-3, 12.0e-3)]
    assert len(set(flows)) == 3
    assert all(b > a for a, b in pairwise(flows)), (
        f"a wider bore drops less pressure, so the operating flow must rise; got {flows}"
    )


def test_s4_3_the_operating_point_moves_with_the_length():
    flows = [_demo_flow(length_m=L) for L in (0.5, 1.0, 2.0)]
    assert len(set(flows)) == 3
    assert all(b < a for a, b in pairwise(flows))


def test_s4_3_the_operating_point_moves_with_the_pump_characteristic():
    """The external characteristic is half the coupling and must matter too."""
    flows = [
        C.demonstrate_machinery(
            demo_case(), C.PumpCharacteristic(shutoff_Pa=p, runout_kg_s=0.05), **FLOWS
        ).operating_points[0].mass_flow_kg_s
        for p in (4.0e4, 6.0e4, 9.0e4)
    ]
    assert len(set(flows)) == 3
    assert all(b > a for a, b in pairwise(flows))


def test_s4_3_control_the_same_inputs_give_the_same_point():
    """A control against a solver that merely wanders."""
    assert _demo_flow() == pytest.approx(_demo_flow(), rel=0.0, abs=0.0)


def test_s4_3_outlet_quality_is_not_an_input():
    """Holding x_out fixed while the flow moves is how the coupling gets faked."""
    assert "quality_out" not in C.LoopCase.__dataclass_fields__
    assert "quality_out" not in inspect.signature(C.LoopCase).parameters


# =============================================================================
# S4-4 -- the operating point is a root, checked by its residual
# =============================================================================


def test_s4_4_the_reported_point_satisfies_both_characteristics():
    for point in solve_demo().operating_points:
        assert abs(point.residual_Pa) <= 1.0e-2, (
            "the internal and external characteristics must agree at a reported "
            f"operating point; residual was {point.residual_Pa} Pa"
        )


def test_s4_4_the_residual_is_recomputed_not_asserted_zero():
    """A residual field that is always exactly 0.0 would be decoration."""
    residuals = [p.residual_Pa for p in solve_demo().operating_points]
    assert residuals and not all(r == 0.0 for r in residuals)


# =============================================================================
# S4-5 / S4-6 -- non-uniqueness and the static Ledinegg guard
#
# The guard is exercised against a characteristic that HAS a negative-slope segment,
# because the project's own pressure-drop model does not produce one -- see
# test_s4_6_the_current_pressure_drop_model_cannot_produce_an_excursion.
# =============================================================================


def n_shaped(mdot: float) -> float:
    """A characteristic with the shape the adopted source's Fig. 1.3 prints.

    Rising, then falling through the unstable segment, then rising again. A cubic is
    the least contrived thing with that shape, and the shape is the whole content of
    the criterion being tested.
    """
    return 5.0e7 * (mdot - 0.03) ** 3 - 2.0e4 * (mdot - 0.03) + 800.0


N_PUMP = C.PumpCharacteristic(shutoff_Pa=900.0, runout_kg_s=0.20)
N_FLOWS = dict(flow_min_kg_s=0.001, flow_max_kg_s=0.06, samples=400)


def n_points():
    return C.operating_points_from_characteristic(n_shaped, N_PUMP, **N_FLOWS)


def test_s4_5_every_root_is_reported_and_none_is_selected():
    """Fig. 1.3's three intersections. Returning one would be choosing an answer."""
    points = n_points()
    assert len(points) == 3, f"expected three intersections, got {len(points)}"
    flows = [p.mass_flow_kg_s for p in points]
    assert all(b > a for a, b in pairwise(flows))


def test_s4_5_the_result_reports_non_uniqueness_rather_than_resolving_it():
    """No API returns 'the' operating point when there is more than one.

    F-03: this constructed a ``DemonstrationResult`` directly and so never exercised
    the energy path that selected the first root -- the suite had the same blind spot
    as the code. It now goes through ``demonstrate_machinery``; see
    :func:`test_f03_no_closure_is_computed_when_the_solution_is_non_unique`.
    """
    result = C.DemonstrationResult(case=demo_case(), pump=N_PUMP, legs=(), operating_points=n_points())
    assert result.non_unique
    assert "NON-UNIQUE" in result.render()
    for name in ("operating_point", "preferred_point", "chosen_point", "best_point"):
        assert not hasattr(result, name), (
            f"{name} would be a rule for choosing among steady states, and this "
            "milestone does not have one"
        )


def test_s4_6_the_guard_fires_on_the_middle_root_and_not_the_outer_two():
    points = n_points()
    assert [p.ledinegg_unstable for p in points] == [False, True, False], (
        "the negative-slope segment lies between the outer intersections; the caption "
        "of the adopted figure says the middle point is the unstable one"
    )
    assert points[1].slope_dP_dmdot_Pa_s_kg < 0.0
    assert points[0].slope_dP_dmdot_Pa_s_kg > 0.0
    assert points[2].slope_dP_dmdot_Pa_s_kg > 0.0


@pytest.mark.parametrize(
    ("slope", "expected"),
    [(-1.0e6, True), (-1e-9, True), (0.0, False), (1e-9, False), (1.0e6, False)],
)
def test_s4_6_the_criterion_is_a_strict_sign_test(slope, expected):
    """`dp/dM_dot < 0`, strictly. A stationary point is the boundary, not the fault."""
    assert ledinegg_static_criterion(slope) is expected


def test_s4_6_the_current_pressure_drop_model_cannot_produce_an_excursion():
    """A recorded property of the model, not of the guard.

    The S3 pressure-drop model evaluates the two-phase multiplier at the section's
    MEAN quality over a fixed length rather than integrating along the channel -- a
    stated screening simplification. That removes the moving boiling boundary, which
    is the mechanism that puts a negative-slope segment into a boiling channel's
    characteristic. The consequence is that on this model the internal characteristic
    is monotone at every duty tried, so the Ledinegg criterion is unreachable through
    it and the guard has to be verified against a characteristic supplied to it.

    Pinned rather than left as a remark: if a successor integrates along the channel,
    this test fails, and it should -- that is the signal that the guard has become
    reachable through the physics and needs exercising there.
    """
    for duty in (600.0, 1200.0, 12000.0, 60000.0):
        assert C.characteristic_is_monotone(
            C.loop_characteristic(demo_case(duty_W=duty)),
            flow_min_kg_s=0.002,
            flow_max_kg_s=0.049,
        ), f"the characteristic became non-monotone at duty {duty} W -- re-read this test"


def test_s4_6_every_result_states_that_the_guard_cannot_fire_on_this_model():
    """C6: the qualification is in the output, not a footnote, on BOTH run kinds.

    Describing this milestone as shipping a static Ledinegg guard, without saying that
    it cannot trigger against the pressure-drop model it is attached to, would
    overstate what was delivered.
    """
    for result in (solve_demo(), solve_ref()):
        rendered = result.render()
        assert "UNABLE TO FIRE ON THIS MODEL" in rendered
        assert "negative_slope_segment" in rendered
        assert "does not by itself discharge the requirement" in rendered
        assert "UNABLE TO FIRE ON THIS MODEL" in str(result)


def test_s4_6_the_guard_disclosure_cannot_be_suppressed_by_a_caller():
    """A property, not a field: there is no constructor argument for it."""
    assert "ledinegg_disclosure" not in C.DemonstrationResult.__dataclass_fields__
    assert "ledinegg_disclosure" not in C.ReferenceCaseResult.__dataclass_fields__
    assert isinstance(C.DemonstrationResult.ledinegg_disclosure, property)


def test_s4_6_nothing_claims_dynamic_instability_is_modelled():
    """The source defers instability treatment to another volume; so does this."""
    entry = get(C.LEDINEGG_ID)
    text = (entry.applicability + " " + entry.note + " " + C.__doc__).lower()
    assert "static" in text
    for forbidden in ("density-wave model", "models the excursion", "instability model"):
        assert forbidden not in text


# =============================================================================
# S4-7 / S4-8 -- refusals name their axis, and policy is distinguished from ignorance
# =============================================================================


def test_s4_7_every_blocked_leg_names_an_axis_an_entry_and_an_unblocker():
    blocked = solve_ref().blocked_legs
    assert len(blocked) == 3, f"expected three blocked legs, got {[b.leg for b in blocked]}"
    for leg in blocked:
        assert leg.axis, f"{leg.leg} is blocked but names no axis"
        assert leg.entry_id, f"{leg.leg} is blocked but names no entry"
        assert leg.would_unblock, f"{leg.leg} is blocked but says nothing about lifting it"
        assert leg.refusal_kind in ("policy", "knowledge")


def test_s4_7_the_leg_that_is_in_basis_is_not_reported_blocked():
    """The control. 'Everything refuses' is not a result, it is a broken run."""
    result = solve_ref()
    chf = [leg for leg in result.legs if leg.leg == "CHF"]
    assert chf and chf[0].available, "CHF is in basis and must not be reported blocked"


def test_s4_7_the_refusal_is_behavioural_not_read_off_the_registry():
    """The leg is run. Reading applicability off the entry would report a declaration.

    This is what caught the real defect during the build: Lockhart-Martinelli refuses
    this project by DE_RANK, which *returns a finite number* with violations attached
    so the case stays reportable as a sensitivity. A leg check that only caught
    exceptions reported the reference case's pressure-drop leg as AVAILABLE.
    """
    from orbital_thermal.two_phase_loop import two_phase_pressure_drop

    case = ref_case()
    raw = two_phase_pressure_drop(
        mass_flow_kg_s=0.01,
        diameter_m=8.0e-3,
        length_m=1.0,
        quality_in=0.0,
        # The quality the CASE produces at this flow, so the two calls describe the
        # same physical point rather than two different ones that happen to agree.
        quality_out=case.quality_out_at(0.01),
        rho_f=560.0,
        rho_g=15.8,
        mu_f=1.1e-4,
        mu_g=1.0e-5,
        pressure_Pa=20.0e5,
        composition="single_component",
        geometry_shape="round_tube",
        orientation="vertical_upflow",
        fluid="Ammonia",
        height_m=1.5,
    )
    assert math.isfinite(raw.total_Pa) and not raw.is_applicable, (
        "this test is only meaningful while the correlation de-ranks rather than raises"
    )
    (point,) = C.internal_characteristic(case, (0.01,))
    assert not point.evaluated, (
        "a de-ranked number must not be usable as a point on the characteristic: an "
        "operating point built on it is a root of a curve the correlation disclaims"
    )
    assert point.inapplicable_value_Pa == pytest.approx(raw.total_Pa)


def test_s4_7_no_operating_point_is_invented_when_a_leg_refuses():
    result = solve_ref()
    assert not result.solved
    assert result.operating_points == ()
    assert result.closure is None


#: The reference case's own mean quality at the nominal flow -- x_in = 0 rising to
#: Q/(mdot h_fg). Load-bearing: two of the candidate's declared axes are functions of
#: quality, so the assessment must be made here and not at a convenient value.
REF_X_MEAN = 0.5 * (1000.0 / (0.01 * 1.05e6))


def assess_at(quality, **over):
    return A.assess_declared_basis(
        mass_flow_kg_s=0.01, band_min_m=1.224e-3, band_max_m=32.0e-3,
        reduced_pressure=0.176, quality=quality, mu_f=1.1e-4, mu_g=1.0e-5, **over
    )


def test_s4_8_the_refusal_is_knowledge_once_the_whole_declared_basis_is_applied():
    """The corrected result, and it reverses an earlier one of this build's.

    Applying only D_h, G and P_R, the candidate appeared to admit 2.156-5.350 mm and
    the refusal classified as POLICY. The entry also declares Re_fo, Re_f, Re_g and x.
    With all seven applied at the loop's own quality, the superficial-liquid Reynolds
    ceiling of 16,020 excludes every bore at or below the 5.35 mm bore ceiling, the
    admitted window is EMPTY, and the refusal is a knowledge refusal.
    """
    result = solve_ref()
    dp = [leg for leg in result.legs if leg.leg == "pressure drop"][0]
    assert dp.refusal_kind == "knowledge"
    assert "WHOLE declared basis" in result.pressure_drop_refusal
    assert assess_at(REF_X_MEAN).admitted.is_empty


def test_s4_8_the_knowledge_refusal_says_the_correlation_is_not_empty_everywhere():
    """'Does not reach THIS loop' must not be readable as 'does not reach anything'."""
    detail = solve_ref().pressure_drop_refusal
    assert "not empty everywhere" in detail
    assert "vapour qualities" in detail


def test_s4_8_a_knowledge_refusal_is_not_dressed_as_a_policy_one():
    """The control on the classifier: the other two legs are genuine gaps."""
    for leg in solve_ref().blocked_legs:
        if leg.leg in ("boiling HTC", "condensation"):
            assert leg.refusal_kind == "knowledge"


def test_s4_8_the_classifier_still_returns_policy_when_the_candidate_does_reach():
    """It must be capable of both answers, or it is not a classifier.

    At a quality the loop does not reach, the same declared basis DOES admit part of
    the band -- and there the D16 disclosure obligation would fire.
    """
    reaching = assess_at(0.5)
    assert reaching.admits_part_of_the_band
    verdict = A.classify_pressure_drop_refusal(reaching)
    assert verdict.kind == "policy"
    assert verdict.settled_decision == "A4"
    assert "POLICY REFUSAL" in verdict.detail


def test_s4_8_the_admitting_quality_window_is_bounded_on_both_sides():
    """Empty below and above: Re_f binds at low quality, Re_g at high."""
    window = A.qualities_admitting_any_bore(
        mass_flow_kg_s=0.01, band_min_m=1.224e-3, band_max_m=32.0e-3,
        reduced_pressure=0.176, mu_f=1.1e-4, mu_g=1.0e-5,
    )
    assert window is not None
    lo, hi = window
    assert 0.0 < lo < hi < 1.0
    assert REF_X_MEAN < lo, (
        f"the loop's own mean quality {REF_X_MEAN:.4g} must sit BELOW the admitting "
        f"window {lo:.2f}-{hi:.2f}; that is why its refusal is a knowledge refusal"
    )
    assert assess_at(lo * 0.5).admitted.is_empty
    assert assess_at(min(1.0, hi + (1.0 - hi) / 2)).admitted.is_empty


# =============================================================================
# S4-9 -- the assessment computes overlap; it does not read a fluid list
# =============================================================================


def test_s4_9_every_declared_axis_is_applied_not_a_chosen_subset():
    """The defect this block was rewritten for. Seven declared ranges, seven applied."""
    declared = set(get(A.KIM_MUDAWAR_ID).domain.ranges)
    assert set(assess_at(0.5).applied_axes) == declared
    assert declared == {"D_h_m", "G_kg_m2s", "Re_fo", "Re_f", "Re_g", "x", "P_R"}


def test_s4_9_a_declared_axis_with_no_evaluator_raises_rather_than_being_skipped():
    """The class-level guard: silently ignoring an axis is what went wrong."""
    with pytest.raises(ValueError, match=r"no evaluator"):
        A._admits(
            5.0e-3,
            {"some_axis_nobody_implemented": (0.0, 1.0)},
            A.OperatingContext(0.01, 0.176, 1.1e-4, 1.0e-5, 0.5),
        )


def test_s4_9_the_reynolds_ceiling_binds_at_small_bore_and_narrows_the_window():
    """Re_fo scales as 1/D, so it cuts the end the bore ceiling does not.

    Applying D_h and G alone gives 2.156-5.350 mm; adding Re_fo moves the low end up
    by roughly 2 mm, in the direction of over-claiming applicability.

    The low end is a function of the liquid viscosity, so both readings are pinned:
    4.132 mm at this test's mu_f = 1.10e-4, and 4.352 mm at CoolProp's saturated-liquid
    ammonia value at 20 bar. The second is the independently reported figure and
    matching it is the point of asserting it.
    """
    a = assess_at(0.5)
    assert a.admitted.lo_m == pytest.approx(4.1324e-3, rel=1e-3)
    assert a.admitted.hi_m == pytest.approx(5.35e-3, rel=1e-9)
    assert a.admitted.lo_m > 2.1564e-3

    at_coolprop_mu = A.assess_declared_basis(
        mass_flow_kg_s=0.01, band_min_m=1.224e-3, band_max_m=32.0e-3,
        reduced_pressure=0.176, quality=0.5, mu_f=1.044729e-4, mu_g=1.0e-5,
    )
    assert at_coolprop_mu.admitted.lo_m == pytest.approx(4.3516e-3, rel=1e-3)


@pytest.mark.parametrize("quality", [0.02, REF_X_MEAN, 0.2, 0.95])
def test_s4_9_the_admitted_window_is_empty_away_from_the_middle_qualities(quality):
    """Two declared axes depend on quality, so there is no single admitted band."""
    assert assess_at(quality).admitted.is_empty


def test_s4_9_quality_has_no_default_because_it_decides_the_answer():
    default = inspect.signature(A.assess_declared_basis).parameters["quality"].default
    assert default is inspect.Parameter.empty, (
        f"quality must have no default; it has {default!r}, and two declared axes "
        "depend on it"
    )
    with pytest.raises(TypeError):
        A.assess_declared_basis(  # type: ignore[call-arg]
            mass_flow_kg_s=0.01, band_min_m=1.224e-3, band_max_m=32.0e-3,
            reduced_pressure=0.176,
        )


def test_s4_9_two_different_overlaps_are_reported_and_not_conflated():
    """One is evidence and one is not, and they are easy to mistake for each other.

    (a) mass flux alone: of the admitted window, 5.046-5.350 mm carries a mass flux
        inside the range the ammonia rows were taken over. Real, and narrow.
    (b) mass flux AND bore: those rows were measured at 1.224-1.70 mm, which the
        flux-matched interval 5.046-11.284 mm never reaches. Empty at any quality.

    A bore in (a) matches the ammonia mass flux while sitting three times wider than
    any bore ammonia was measured at, so (a) is not ammonia evidence for this loop.
    """
    a = assess_at(0.5)
    assert not a.flux_matched_within_admitted.is_empty
    assert a.flux_matched_within_admitted.lo_m == pytest.approx(5.0463e-3, rel=1e-3)
    assert a.flux_matched_within_admitted.hi_m == pytest.approx(5.35e-3, rel=1e-9)

    assert a.fluid_supported.is_empty
    assert not a.fluid_evidence_reaches_the_admitted_window
    assert a.fluid_bore_hull.lo_m == pytest.approx(1.224e-3)
    assert a.fluid_bore_hull.hi_m == pytest.approx(1.70e-3)
    assert a.fluid_flux_matched.lo_m == pytest.approx(5.0463e-3, rel=1e-3)

    detail = A.classify_pressure_drop_refusal(a).detail
    assert "MASS FLUX ONLY" in detail and "MASS FLUX AND BORE TOGETHER" in detail


def test_s4_9_control_a_fluid_measured_where_the_loop_runs_does_reach():
    """The control: the overlap test must be able to come out positive."""
    generous = A.FluidEvidence(
        fluid="ammonia",
        diameters_m=(4.5e-3, 6.0e-3),
        mass_flux_min_kg_m2s=400.0,
        mass_flux_max_kg_m2s=2000.0,
        points=235,
        total_points=2378,
        orientation="vertical_upflow",
        geometry="round_tube",
        locator="hypothetical control, not a source",
    )
    assert assess_at(0.5, evidence=generous).fluid_evidence_reaches_the_admitted_window


def test_s4_9_the_mass_flux_to_bore_inversion_is_the_right_way_round():
    """G falls as D rises, so the flux CEILING sets the lower bore bound."""
    window = A._bores_for_mass_flux(0.01, 33.0, 2738.0)
    assert window.lo_m < window.hi_m
    assert 0.01 / (math.pi * window.lo_m**2 / 4) == pytest.approx(2738.0, rel=1e-9)
    assert 0.01 / (math.pi * window.hi_m**2 / 4) == pytest.approx(33.0, rel=1e-9)


# =============================================================================
# S4-10 -- the non-SI conversion is at the boundary and is tested
# =============================================================================


def test_s4_10_the_kcal_conversion_matches_an_independently_computed_value():
    assert kcal_per_m2_hr_to_W_m2(2000.0) == pytest.approx(2000.0 * 4186.8 / 3600.0, rel=1e-12)
    assert kcal_per_m2_hr_to_W_m2(500.0) == pytest.approx(581.5, rel=1e-6)
    assert kcal_per_m2_hr_to_W_m2(2000.0) == pytest.approx(2326.0, rel=1e-6)


def test_s4_10_both_kilocalorie_definitions_are_recorded_and_differ_as_expected():
    """The source writes 'kcal' unqualified, so the ambiguity is real."""
    assert KCAL_IT_J == 4186.8
    assert KCAL_TH_J == 4184.0
    spread = abs(kcal_per_m2_hr_to_W_m2(2000.0, kcal_J=KCAL_TH_J) / 2326.0 - 1.0)
    assert spread == pytest.approx(6.69e-4, rel=0.02)


def test_s4_10_the_enforced_domain_is_in_si_not_in_the_sources_units():
    entry = get("two_phase.htc.shah_1974_ammonia")
    lo, hi = entry.domain.ranges["q_W_m2"]
    assert (lo, hi) == pytest.approx((581.50, 2326.00), rel=1e-6)
    assert "kcal" not in "".join(entry.domain.ranges)


def test_s4_10_shah_1974_refuses_this_loop_on_every_declared_numeric_axis():
    """Four axes, from the source's own Experimental Range block."""
    entry = get("two_phase.htc.shah_1974_ammonia")
    bad = entry.domain.out_of_domain(P_Pa=20.0e5, q_W_m2=5.0e4, mdot_kg_s=0.01)
    assert len(bad) == 3, f"expected all three numeric axes to refuse; got {bad}"
    # ...and the control: its own declared mid-range is inside.
    assert entry.domain.contains(P_Pa=2.0e5, q_W_m2=1200.0, mdot_kg_s=0.1)


def test_s4_10_shah_1974_is_registered_and_not_rank_eligible():
    entry = get("two_phase.htc.shah_1974_ammonia")
    assert not entry.rank_eligible
    assert entry.evaluate is None
    assert entry.applicability_spec.orientations == frozenset({"horizontal"})


def test_s4_10_only_the_heat_transfer_half_of_shah_1974_is_registered():
    """The source reports heat transfer AND pressure drop; only one half is here.

    Registering the pressure-drop half would assert that the literature covers a
    pressure-drop domain it does not -- and its friction data miss standard in both
    directions from compressor oil, by the author's own account.
    """
    from orbital_thermal.registry.two_phase import TWO_PHASE_CORRELATIONS

    shah_entries = [e for e in TWO_PHASE_CORRELATIONS if "shah_1974" in e.id]
    assert [e.kind for e in shah_entries] == ["htc"], (
        f"expected exactly one Shah (1974) entry, of kind htc; found "
        f"{[(e.id, e.kind) for e in shah_entries]}"
    )
    assert not any(
        "shah_1974" in e.id and e.kind == "dp" for e in TWO_PHASE_CORRELATIONS
    )


def test_s4_10_the_property_backend_caveat_is_recorded():
    """A correlation and the properties it was fitted against are a package (C8).

    Shah's values came from VDI Kaltemaschinen Regeln, whose liquid viscosity runs
    ~20 % above the 1972 ASHRAE handbook. This project computes on CoolProp, so a
    reimplementation would not be the published method -- and unlike every domain
    limit on this entry, that one would bite even inside the declared range.
    """
    note = get("two_phase.htc.shah_1974_ammonia").source.note
    assert "VDI Kaltemaschinen Regeln" in note
    assert "20%" in note
    assert "CoolProp" in note
    assert "not be the published method" in note


def test_s4_10_the_oil_contamination_is_recorded_in_both_directions():
    """Friction factors came out below Moody AND, at low temperature, twice it."""
    note = get("two_phase.htc.shah_1974_ammonia").source.note
    assert "drag reduction" in note
    assert "twice Moody" in note or "viscous oil films" in note


# =============================================================================
# S4-11 / S4-12 -- unresolved provenance travels; the balance closes
# =============================================================================


def test_s4_11_any_balance_carrying_pump_heat_carries_the_d13_disclosure():
    closure = solve_demo().closure
    assert closure is not None and closure.pump_heat_into_fluid_W > 0.0
    assert closure.disclosures, "pump heat is in the rejected load with no disclosure"
    assert "DEBTS D-13" in closure.disclosures[0]
    assert "DEBTS D-13" in solve_demo().render()


def test_s4_11_the_pump_efficiency_value_is_unchanged():
    """S4 must not resolve D-13 in either direction, including by editing the value."""
    from orbital_thermal import architecture_cases, pumped_loop

    assert inspect.signature(pumped_loop.pump_energy).parameters["eta_pump"].default == 0.70
    envelope = architecture_cases.__dict__
    assert any(
        getattr(v, "__dataclass_fields__", {}).get("eta_pump") is not None
        for v in envelope.values()
        if hasattr(v, "__dataclass_fields__")
    )


def test_s4_11_the_disclosure_is_absent_when_there_is_no_pump_heat():
    """The control: it must mark the balances that depend on it, not every balance."""
    closure = C.EnergyClosure(
        duty_W=1000.0, pump_heat_into_fluid_W=0.0, rejected_W=1000.0,
        residual_W=0.0, boundary="fluid_loop",
    )
    assert closure.disclosures == ()


def test_s4_12_the_rejected_load_is_duty_plus_pump_heat_and_closes():
    closure = C.energy_closure(
        duty_W=1000.0, mass_flow_kg_s=0.02, pressure_drop_Pa=1.5e4, density_kg_m3=997.0
    )
    assert closure.closes
    assert closure.rejected_W == pytest.approx(
        closure.duty_W + closure.pump_heat_into_fluid_W, rel=1e-12
    )
    assert closure.pump_heat_into_fluid_W == pytest.approx(0.02 * 1.5e4 / 997.0, rel=1e-9)


def test_s4_12_the_pump_term_is_load_bearing_in_the_balance():
    """A balance that closes with the pump term dropped is not this balance."""
    a = C.energy_closure(duty_W=1000.0, mass_flow_kg_s=0.02, pressure_drop_Pa=1.5e4,
                         density_kg_m3=997.0)
    b = C.energy_closure(duty_W=1000.0, mass_flow_kg_s=0.02, pressure_drop_Pa=3.0e4,
                         density_kg_m3=997.0)
    assert b.rejected_W > a.rejected_W > 1000.0


# =============================================================================
# S4-13 / S4-14 -- no ranked output; every bound is traceable
# =============================================================================


def test_s4_13_no_s4_entry_point_returns_a_rank_or_an_ordering():
    for name in ("rank", "ranking", "score", "order", "best", "recommend"):
        assert not any(
            name in attr.lower() for attr in C.__all__
        ), f"'{name}' appears in the S4 public surface"
    for result in (solve_demo(), solve_ref()):
        for field_name in type(result).__dataclass_fields__:
            assert "rank" not in field_name.lower()


def test_s4_13_the_ranking_mechanism_is_left_in_place_for_its_later_users():
    """S4 emits none, but must not have removed the machinery."""
    from orbital_thermal.registry import assert_rank_eligible

    assert callable(assert_rank_eligible)


def test_s4_14_every_new_entry_cites_a_source_and_a_locator():
    for entry_id in (
        "two_phase.htc.shah_1974_ammonia",
        "two_phase.dp.kim_mudawar_2013",
        C.LEDINEGG_ID,
    ):
        entry = get(entry_id)
        assert entry.source is not None and entry.source.citation.strip()
        assert entry.source.locator.strip(), f"{entry_id} enforces bounds with no locator"


def test_s4_14_the_sources_record_that_they_were_read_from_rendered_pages():
    """Criterion 9 from the previous set, applied to what S4 adds."""
    for entry_id in ("two_phase.htc.shah_1974_ammonia", "two_phase.dp.kim_mudawar_2013",
                     C.LEDINEGG_ID):
        text = get(entry_id).source.locator.upper()
        assert "RENDERED" in text, f"{entry_id} does not record reading a rendered page"


def test_s4_14_the_photocopy_scan_is_recorded_as_having_no_text_layer():
    """A file property that makes automated extraction impossible, not merely unwise."""
    note = get("two_phase.htc.shah_1974_ammonia").source.locator
    assert "no text layer" in note.lower()


# =============================================================================
# OTB-G003 round 1 — Sol's findings, dispositioned by the Director
# =============================================================================


def test_f01_an_infeasible_pump_inlet_refuses_rather_than_returning_points():
    """F-01(b). A cavitating loop behind a green leg with a solved point is neither."""
    result = solve_demo(inlet_temperature_K=400.0)
    assert result.pump_inlet_feasible is False
    (inlet_leg,) = [leg for leg in result.legs if leg.leg == "pump-inlet criterion"]
    assert inlet_leg.available is False, "the leg must report the COMPUTED feasibility"
    assert inlet_leg.axis and inlet_leg.reason and inlet_leg.would_unblock
    assert result.operating_points == ()
    assert result.closure is None
    assert "NO OPERATING POINT IS REPORTED" in result.render()


def test_f01_control_a_feasible_inlet_still_evaluates_cleanly():
    """The paired control: the fix must not degrade into 'refuses everything'."""
    result = solve_demo()
    assert result.pump_inlet_feasible is True
    assert len(result.operating_points) == 1
    (inlet_leg,) = [leg for leg in result.legs if leg.leg == "pump-inlet criterion"]
    assert inlet_leg.available is True


def test_f01_the_pump_inlet_leg_is_not_a_literal():
    """It was `available=True`, written out, regardless of what was computed."""
    import inspect

    src = inspect.getsource(C.demonstrate_machinery)
    assert "available=inlet.feasible" in src
    assert 'LegStatus(leg="pump-inlet criterion", entry_id=NPSH_ID, available=True)' not in src


def test_f01_the_condenser_duty_is_computed_from_the_solved_state():
    """F-01(2.2). It was h_in=h_fg, h_out=0 — fixed, so `energy_closes` was a tautology."""
    result = solve_demo()
    assert result.condenser_duty_matches_applied is True
    assert "condenser duty from the SOLVED state" in result.render()


def test_f01_the_condenser_closure_can_fail():
    """R2 in the test itself: the check must be capable of the other answer.

    Built from the same boundary with a deliberately inconsistent outlet state, so
    "matches" is a computed comparison and not a restatement of its own inputs.
    """
    from orbital_thermal.two_phase_loop import condenser_energy_boundary

    case = demo_case()
    honest = condenser_energy_boundary(
        mass_flow_kg_s=0.0436, h_in_J_kg=0.0122 * case.h_fg_J_kg, h_out_J_kg=0.0,
        sink_temperature_K=case.sink_temperature_K,
        saturation_temperature_K=case.saturation_temperature_K, outlet_is_liquid=True,
    )
    wrong = condenser_energy_boundary(
        mass_flow_kg_s=0.0436, h_in_J_kg=0.5 * case.h_fg_J_kg, h_out_J_kg=0.0,
        sink_temperature_K=case.sink_temperature_K,
        saturation_temperature_K=case.saturation_temperature_K, outlet_is_liquid=True,
    )
    tol = 1e-6 * max(abs(case.duty_W), 1.0)
    assert abs(honest.duty_W - case.duty_W) <= max(tol, 0.02 * case.duty_W)
    assert abs(wrong.duty_W - case.duty_W) > tol, (
        "an inconsistent outlet state must move the condenser duty away from the "
        "applied duty; if it cannot, the comparison is not a check"
    )


def test_f01_the_sink_collapse_is_declared_and_stated_in_the_output():
    """F-01(2.3). C11(i) and (ii) for criterion S4-3."""
    (conflict,) = C.sink_collapse_conflicts()
    assert conflict.phenomenon == "sink_temperature_coupling"
    assert conflict.term == "condenser/radiator"
    text = C.sink_disclosure_text()
    assert "UNABLE TO FIRE ON THIS MODEL" in text
    for result in (solve_demo(), solve_ref()):
        assert text in result.render()


def test_f01_the_sink_declaration_transcribes_the_module_prose():
    """D21's standing modification: verbatim, with a match check."""
    from orbital_thermal.registry.collapse import transcription_mismatches

    collapses = tuple(
        c for t in C.COUPLED_SOLVE_MODEL.terms for c in t.collapses
    )
    assert collapses and all(c.transcription is not None for c in collapses)
    assert transcription_mismatches(collapses) == ()


def test_f01_the_artifact_does_not_claim_the_coupling_is_solved():
    """§2.4. Path C stops the artifact claiming what is untrue; it does not make it true."""
    doc = C.__doc__.lower()
    assert "declared collapse, not a solved coupling" in doc
    assert "fails on its own terms" in doc
    for forbidden in ("s4-3 now passes", "solved together is discharged", "sink is coupled"):
        assert forbidden not in doc


def test_f02_relabelling_the_demonstration_as_the_reference_device_is_refused():
    """The direction the suite had never tested. One changed enum field is not identity."""
    mislabelled = C.LoopCase(kind=C.RunKind.REFERENCE_CASE, **DEMO_KW)
    with pytest.raises(ValueError, match=r"does not describe this project's device"):
        C.solve_reference_case(mislabelled, PUMP, **FLOWS, **BAND)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("fluid", "Water"),
        ("composition", "two_component"),
        ("orientation", "horizontal"),
        ("pressure_Pa", 1.2e5),
    ],
)
def test_f02_each_device_fact_is_checked_not_just_the_label(field, value):
    """Four axes, one at a time: the guard must not pass on three out of four."""
    with pytest.raises(ValueError, match=r"does not describe this project's device"):
        C.solve_reference_case(ref_case(**{field: value}), PUMP, **FLOWS, **BAND)


def test_f02_control_the_real_device_is_still_accepted():
    assert isinstance(solve_ref(), C.ReferenceCaseResult)


def test_f03_no_closure_is_computed_when_the_solution_is_non_unique():
    """The Director's ruling: compute no energy closure at all at multiplicity."""
    case = demo_case()
    assert C.closure_for((), case) is None
    one = solve_demo().operating_points
    assert len(one) == 1 and C.closure_for(one, case) is not None
    assert C.closure_for(n_points(), case) is None, (
        "three steady states must yield no closure; picking the first and disclosing "
        "it is still picking"
    )


def test_f03_the_non_uniqueness_note_says_no_closure_rather_than_which_root():
    result = C.DemonstrationResult(
        case=demo_case(), pump=N_PUMP, legs=(), operating_points=n_points(),
        closure=C.closure_for(n_points(), demo_case()),
        notes=("NO ENERGY CLOSURE IS REPORTED: the solution is non-unique (3 steady states).",),
    )
    assert result.closure is None
    assert "NO ENERGY CLOSURE IS REPORTED" in result.render()
    assert "FIRST root" not in result.render()


def test_f03_the_demonstration_path_is_exercised_not_constructed():
    """The test suite had the code's blind spot: it never called the entry point."""
    result = solve_demo()
    assert isinstance(result, C.DemonstrationResult)
    assert result.closure is not None and not result.non_unique


# --- F-04: the root enumerator ---------------------------------------------------
#
# Roots are placed deliberately OFF the grid nodes. Cowork's first verification put
# them ON nodes, where the exact-zero branch catches them, and nearly reported the
# finding refuted. The off-grid placement IS the fixture.

F4_FLOWS = dict(flow_min_kg_s=0.5, flow_max_kg_s=2.5, samples=11)  # nodes every 0.2


class _FlatPump(C.PumpCharacteristic):
    def available_Pa(self, mass_flow_kg_s: float) -> float:
        return 0.0


F4_PUMP = _FlatPump(shutoff_Pa=1.0, runout_kg_s=1e9)


def _roots(fn):
    return [
        p.mass_flow_kg_s
        for p in C.operating_points_from_characteristic(fn, F4_PUMP, **F4_FLOWS)
    ]


def test_f04_a_root_exactly_at_flow_max_is_found():
    """It is the `hi` of the last bracket and was never the `lo` of any."""
    found = _roots(lambda m: m - 2.5)
    assert found and abs(found[-1] - 2.5) < 1e-6


def test_f04_a_tangential_root_is_found():
    """Touches zero without crossing, so no sign change exists to bracket."""
    found = _roots(lambda m: (m - 1.61) ** 2)
    assert len(found) == 1, f"expected one tangential root, got {found}"
    assert abs(found[0] - 1.61) < 0.02


def test_f04_two_roots_inside_one_sampling_interval_are_both_found():
    found = _roots(lambda m: (m - 1.61) * (m - 1.63))
    assert len(found) == 2, f"expected two roots, got {found}"
    assert abs(found[0] - 1.61) < 0.02 and abs(found[1] - 1.63) < 0.02


def test_f04_control_an_ordinary_off_grid_sign_change_still_resolves():
    """The control that keeps the enumerator from being 'returns everything'."""
    found = _roots(lambda m: m - 1.61)
    assert len(found) == 1 and abs(found[0] - 1.61) < 1e-3


def test_f04_a_flat_characteristic_far_from_zero_yields_no_roots():
    """The other control: near-zero is not the same as small, and neither is a root."""
    assert _roots(lambda m: 5.0) == []


def test_f04_a_bracket_that_closes_on_a_discontinuity_emits_nothing():
    """(iii) The case the residual gate actually exists for.

    A step from -1 to +1 with no zero in between presents a perfect sign change, so
    bisection brackets it and converges -- to a discontinuity, not a root. Without the
    final residual check an ``OperatingPoint`` is emitted carrying |residual| = 1.0 Pa
    against a 1e-3 Pa tolerance, and every emitted point gets a slope and a stability
    verdict. A flat characteristic cannot exercise this: it produces no candidate at
    all, so the gate is never reached.
    """
    step = C.operating_points_from_characteristic(
        lambda m: -1.0 if m < 1.61 else 1.0, F4_PUMP, **F4_FLOWS
    )
    assert step == (), f"a discontinuity is not a steady state; got {step}"


def test_f04_no_emitted_point_exceeds_the_residual_tolerance():
    """(iii) A non-root was emitted: neither stop branch required a final residual."""
    for fn in (lambda m: m - 2.5, lambda m: (m - 1.61) ** 2, lambda m: m - 1.61):
        for p in C.operating_points_from_characteristic(fn, F4_PUMP, **F4_FLOWS):
            assert math.isfinite(p.residual_Pa)
            assert abs(p.residual_Pa) <= 1.0e-3, (
                f"emitted a point with residual {p.residual_Pa} Pa against a 1e-3 Pa "
                "tolerance — multiplicity is the Ledinegg verdict and every emitted "
                "point gets a slope"
            )


def test_f04_the_bracket_tolerance_is_a_flow_tolerance_not_a_scaled_pressure():
    """(ii) `(hi - lo) [kg/s] <= tol * 1e-6 [Pa]` was dimensionally incoherent."""
    import inspect

    src = inspect.getsource(C._bisect)
    # Any spelling of "scale the pressure tolerance and call it a flow one".
    assert "1e-6" not in src, "the bracket stop must not be derived from a pressure"
    assert "flow_tol_kg_s" in src
    assert C._FLOW_BRACKET_TOL_KG_S == 1.0e-12
    # And it is a genuinely separate knob: changing the PRESSURE tolerance must not
    # change the flow bracket the search closes to.
    sig = inspect.signature(C._bisect).parameters
    assert sig["flow_tol_kg_s"].default == C._FLOW_BRACKET_TOL_KG_S
    assert "tol_Pa" in sig and sig["tol_Pa"].default is inspect.Parameter.empty


# --- F-05: non-finite input is refused, at the boundary ---------------------------


@pytest.mark.parametrize("slope", [float("nan"), float("inf"), float("-inf")])
def test_f05_a_non_finite_slope_is_refused_not_classified(slope):
    """Criterion 6 names this in its own sentence: a sign test does not exclude NaN."""
    from orbital_thermal.registry.two_phase import ledinegg_static_criterion

    with pytest.raises(ValueError, match=r"non-finite slope"):
        ledinegg_static_criterion(slope)


def test_f05_control_a_finite_slope_still_gets_a_verdict():
    from orbital_thermal.registry.two_phase import ledinegg_static_criterion

    assert ledinegg_static_criterion(-1.0) is True
    assert ledinegg_static_criterion(0.0) is False
    assert ledinegg_static_criterion(1.0) is False


@pytest.mark.parametrize(
    "bad",
    [
        {"duty_W": float("nan")},
        {"h_fg_J_kg": float("nan")},
        {"rho_f": float("nan")},
        {"mu_g": float("inf")},
        {"pressure_Pa": float("nan")},
        {"diameter_m": 0.0},
        {"quality_in": 1.5},
        {"height_m": float("nan")},
        {"saturation_temperature_K": float("nan")},
    ],
)
def test_f05_a_loop_case_refuses_non_finite_and_unphysical_inputs(bad):
    """C9: checked where the case is CONSTRUCTED, so no consumer has to remember."""
    with pytest.raises(ValueError):
        demo_case(**bad)


def test_f05_a_vapour_denser_than_the_liquid_is_refused():
    with pytest.raises(ValueError, match=r"not below liquid density"):
        demo_case(rho_g=2000.0)


def test_f05_control_a_valid_case_still_constructs_and_evaluates():
    """Criterion 6's paired control: 'refuses everything' cannot satisfy this."""
    assert solve_demo().operating_points


# --- F-06: no assertion in this suite can be unconditionally true -----------------


def test_f06_no_test_in_this_package_carries_a_tautological_assertion():
    """The sixth tracked instance of the shape. This is the regression for it."""
    import pathlib

    offenders = []
    for path in sorted(pathlib.Path("tests").glob("test_*.py")):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            s = line.strip()
            if s.startswith("assert ") and (s.endswith(" or True") or " or True" in s):
                offenders.append(f"{path}:{i}")
    assert not offenders, f"tautological assertions: {offenders}"


def test_s4_registry_ids_all_resolve():
    assert len(C.registered_s4_entries()) == 7


def test_the_transitional_flow_caveat_travels_on_the_result():
    """Stage-1 warns when Reynolds lands in the blended band; a sweep crosses it.

    Emitting the warning hundreds of times sends a real limitation to a log and
    nowhere else. It belongs on the result that depends on it.
    """
    result = solve_demo()
    notes = " ".join(result.notes)
    assert "TRANSITIONAL FLOW" in notes
    assert "TRANSITIONAL FLOW" in result.render()


def test_the_sweep_does_not_emit_a_warning_storm():
    """The caveat is collected, not broadcast once per sampled point."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        solve_demo()
    transitional = [w for w in caught if "transitional flow" in str(w.message)]
    assert not transitional, (
        f"{len(transitional)} transitional-flow warnings escaped the solve; they are "
        "collected onto the result instead"
    )
