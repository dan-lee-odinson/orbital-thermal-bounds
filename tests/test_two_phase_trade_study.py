"""S6 (``OTB-G006``) -- the six acceptance criteria, each with its falsifier exercised.

Each test names the criterion it checks and, where the criterion has one, drives the
falsifier rather than only the passing case. **A witness that has not been seen to fail
is not a witness (S-3)**, which is why
:func:`test_s6_the_candidate_filter_has_a_witness` deliberately weakens the filter and
requires the framework to go red.

The instruments here are deliberately plain -- assertions over the engine's own output.
**D137**: the burden is on an instrument to justify its existence and the default is the
simpler mechanism. Nothing in this file inspects source text, walks an AST, or builds a
classifier; S6's claims are all statements about values the engine produces, so values
are what these tests read.
"""

from __future__ import annotations

import dataclasses
import hashlib
import pathlib
import warnings

import pytest

from orbital_thermal import trade_study as ts
from orbital_thermal import two_phase_architecture_cases as _ac
from orbital_thermal import two_phase_trade_study as s6
from orbital_thermal.registry.applicability import Cause, Consequence
from orbital_thermal.two_phase import RankStatus

#: The S6-5 criterion: sha256 of the export ROWS joined by "\n", with NO trailing
#: newline. Not the file on disk -- see the docstring of the S6-5 test.
STAGE1_EXPORT_ROWS_SHA = (
    "16d396823e1ca2c7da6ac51487ab78170d2d642ab2acd899d7830ae207c30ef5"
)
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def stage1():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ts.build_trade_study()


@pytest.fixture(scope="module")
def study(stage1):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return s6.build_two_phase_study(single_phase_points=stage1.points)


# ======================================================================================
# S6-1 -- no point the applicability layer de-ranks appears as feasible-ranked
# ======================================================================================


def test_s6_1_no_de_ranked_point_is_feasible_ranked(study):
    """Falsifier: a FEASIBLE_RANKED point whose leg carries a disqualifying violation."""
    offenders = [
        p.point_id for p in study.points
        if p.category is ts.PointCategory.FEASIBLE_RANKED
        and any(s is not RankStatus.RANK_ELIGIBLE for s in p.leg_status.values())
    ]
    assert not offenders, (
        "these points are categorised feasible_ranked while a production applicability "
        f"result de-ranked one of their legs: {offenders}")


def test_s6_1_a_de_ranked_leg_keeps_the_point_out_of_that_leg_s_front(study):
    """The de-rank has to *do* something: it must cost front membership.

    Measured at ``8e094d9``: the pressure-drop correlation is declared for horizontal
    two-component flow and this loop is neither, so every two-phase point is de-ranked on
    that leg and no two-phase point may enter a pressure-drop-dependent front.
    """
    for name in ("pressure_drop_vs_mass_flux", "quality_vs_pump_power",
                 "subcooling_margin_vs_pressure_drop", "heat_load_vs_pump_power"):
        front = study.front(name)
        two_phase_members = [m for m in front.member_point_ids if "two_phase" in m]
        assert not two_phase_members, (
            f"front {name!r} ranks on the pressure-drop leg, which de-ranks every "
            f"two-phase point, yet these are members: {two_phase_members}")


def test_s6_1_the_seam_reads_the_production_result_not_the_s5_boundary():
    """The eligibility source is the production result (D139).

    At the S5 boundary every leg blocks on axes that boundary cannot derive, so a study
    built on it would report an empty front for a reason that is about the boundary
    rather than about the case. Both halves are measured here so the distinction is not
    merely asserted.
    """
    for fluid in ("Ammonia", "Water"):
        leg = _ac.assess_leg(fluid=fluid, leg="chf", gravity_m_s2=9.80665)
        assert leg.eligible is False, "the S5 boundary is expected to block, by design"
        assert any(v.cause is Cause.NOT_EVALUATED for v in leg.violations)

    # The production path evaluates the axis and reaches a real verdict.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        water = s6.evaluate_two_phase_point("Water", 1200.0, 500.0, 0.6, 10.0)
    assert water.leg_status["chf"] is RankStatus.RANK_ELIGIBLE, (
        "water is in the Shah database; the production path must reach a verdict rather "
        "than block the way the S5 boundary does")


# ======================================================================================
# S6-2 -- an axis that could not be evaluated is reported, never silently passed
# ======================================================================================


def test_s6_2_unevaluable_is_distinguishable_from_checked_and_passed(study):
    """Falsifier: a point with a non-empty unevaluable set and no reason code for it."""
    offenders = [
        p.point_id for p in study.points
        if p.unevaluable_axes and ts.ReasonCode.AXIS_NOT_EVALUATED not in p.reason_codes
    ]
    assert not offenders, (
        "these points report an unevaluable axis with no reason code saying so, so "
        f"'could not be checked' reads as 'checked and passed': {offenders}")


def test_s6_2_the_unevaluable_set_comes_from_cause_not_from_block():
    """``BLOCK`` carries both meanings; ``Cause`` is the field that separates them.

    D119/D120. Deriving "never checked" from the consequence would be right about eight
    times in nine, which is how the defect this guards against arose.
    """
    de_rank_evaluated = _violation(Consequence.DE_RANK, Cause.EVALUATED_AND_FAILED)
    assert s6._unevaluable((de_rank_evaluated,)) == ()

    blocked_absent = _violation(Consequence.BLOCK, Cause.NOT_EVALUATED)
    assert s6._unevaluable((blocked_absent,)) == ("orientation",)

    # The discriminating case: BLOCK whose axis WAS evaluated is not "unevaluable".
    blocked_evaluated = _violation(Consequence.BLOCK, Cause.EVALUATED_AND_FAILED)
    assert s6._unevaluable((blocked_evaluated,)) == (), (
        "a BLOCK whose axis was evaluated must not be reported as never checked")


def _violation(consequence: Consequence, cause: Cause):
    from orbital_thermal.registry.applicability import Axis, Violation
    return Violation(axis=Axis.ORIENTATION, consequence=consequence,
                     detail="probe", cause=cause)


# ======================================================================================
# S6-3 -- every ranked output CONTAINING TWO-PHASE CASES carries the F6 tag verbatim
# ======================================================================================


def test_s6_3_the_two_phase_export_carries_the_f6_text_verbatim(study):
    rows = s6.to_two_phase_csv_rows(study)
    assert s6.F6_RANKING_SCOPE_LIMITATION in rows[0]
    assert rows[0].startswith("# "), "the tag goes on the export as a whole, line one"


def test_s6_3_every_front_table_containing_two_phase_cases_is_tagged(study):
    for front in study.fronts:
        rows = s6.front_table_rows(study, front.name)
        has_two_phase = any(",two_phase," in r for r in rows[3:])
        if has_two_phase:
            assert s6.F6_RANKING_SCOPE_LIMITATION in rows[0], (
                f"front table {front.name!r} contains two-phase cases and must carry the "
                "F6 ranking-scope limitation verbatim")


def test_s6_3_the_mixed_front_table_is_in_scope_and_tagged(study):
    """A mixed front is IN SCOPE (D140): it contains two-phase cases."""
    rows = s6.front_table_rows(study, "heat_load_vs_pump_power")
    assert any(",two_phase," in r for r in rows), "the mixed table must show both sides"
    assert any(",single_phase," in r for r in rows)
    assert s6.F6_RANKING_SCOPE_LIMITATION in rows[0]


def test_s6_3_the_frozen_stage1_csv_is_out_of_scope_and_untagged():
    """The second falsifier, pointing the other way (D140).

    ``docs/trade-study-points.csv`` holds only single-phase Stage-1 cases. Tagging it
    would move the export hash S6-5 pins, so the two criteria could not both hold.
    """
    raw = (REPO_ROOT / "docs" / "trade-study-points.csv").read_bytes().decode("utf-8")
    assert "microgravity" not in raw, (
        "the Stage-1 single-phase CSV is out of S6-3's scope and frozen under S6-5; "
        "adding the F6 tag to it is an explicit falsifier")


# ======================================================================================
# S6-4 -- single- and two-phase points are comparable, or explicitly not compared
# ======================================================================================


def test_s6_4_exactly_one_mixed_front_exists(study):
    """D144 Q1=1c: exactly one, on heat_load_W x pump_power_W."""
    assert len(s6.MIXED_TRADES) == 1
    t = s6.MIXED_TRADES[0]
    assert (t.x_key, t.y_key) == ("heat_load_W", "pump_power_W")


def test_s6_4_both_architectures_reach_pump_power_by_the_same_convention(study):
    """The mixed axis is comparable because the route to it is identical.

    Stage-1 reads ``pump.electrical_power_W`` from the coupled solve; S6 calls
    :func:`~orbital_thermal.pumped_loop.pump_energy` with ``boundary='fluid_loop'``
    directly. Same function, same boundary, same section 4.7 convention.
    """
    from orbital_thermal import pumped_loop as pl
    expected = pl.pump_energy(0.04, 37000.0, 400.0,
                              boundary="fluid_loop").electrical_power_W
    got = s6.two_phase_pump_power_W(
        mass_flow_kg_s=0.04, pressure_drop_Pa=37000.0, rho_mix_kg_m3=400.0)
    assert got == expected


def test_s6_4_the_density_collapse_is_declared_for_pump_work_not_inherited():
    """**C11.** The collapse's scope extends, so it gets its own recorded entry.

    Falsifier (D144): inheriting the static term's declaration silently. The entry must
    exist, name the quantity it collapses, and say what is new about carrying it here.
    """
    collapses = [c for term in s6.PUMP_WORK_MODEL.terms for c in term.collapses]
    assert collapses, "pump work must declare its own density collapse"
    basis = " ".join(c.basis for c in collapses)
    assert "rho_mix" in " ".join(c.representative_value for c in collapses)
    assert "SCOPE" in basis or "scope" in basis, (
        "the entry must say what is new: the same representative value now stands "
        "behind a work term rather than the static head it was declared for")
    assert "axial_profile" in {p for c in collapses for p in c.phenomena}


def test_s6_4_no_front_ranks_across_a_definitional_difference(study):
    """Every non-mixed front is two-phase-native; the one mixed front is the exception."""
    mixed = {t.name for t in s6.MIXED_TRADES}
    for front in study.fronts:
        if front.name in mixed:
            continue
        rows = s6.front_table_rows(study, front.name)
        assert not any(",single_phase," in r for r in rows), (
            f"front {front.name!r} is two-phase-native and must not carry single-phase "
            "points; only the one mixed front compares architectures")


# ======================================================================================
# S6-5 -- the Stage-1 engine's behaviour is unchanged
# ======================================================================================


def test_s6_5_building_the_two_phase_study_does_not_move_the_stage1_export(stage1):
    """**Computed AFTER the two-phase study has run, and that ordering is the point.**

    ``pareto_front`` records membership by mutating ``pareto_fronts`` and
    ``dominated_reasons`` on the point, and both are in ``_CSV_FIELDS``. An early version
    of :func:`~orbital_thermal.two_phase_trade_study.build_two_phase_study` ranked the
    caller's own Stage-1 points in the mixed front and wrote a seventh front name into
    their rows. ``total_points``, the three category counts and all six front sizes were
    still exactly right; only the sha moved. Checking the hash before building would have
    seen nothing.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        s6.build_two_phase_study(single_phase_points=stage1.points)

    rows = ts.to_csv_rows(stage1)
    got = hashlib.sha256("\n".join(rows).encode()).hexdigest()
    assert got == STAGE1_EXPORT_ROWS_SHA, (
        "the Stage-1 export-rows sha moved after building the two-phase study; the "
        "counts can all still be right while the rows have changed (D140)")


def test_s6_5_the_stage1_counts_and_front_sizes_are_unchanged(stage1):
    assert stage1.summary() == {
        "total_points": 144, "feasible_ranked": 110, "gate_rejected": 14,
        "nonconverged": 20, "fronts": 6, "degenerate_fronts": 0,
    }
    assert [len(f.member_point_ids) for f in stage1.fronts] == [2, 48, 4, 3, 4, 4]
    assert not any(f.degenerate for f in stage1.fronts)


def test_s6_5_trades_still_holds_exactly_six(study):
    """S6's fronts live in this module. Appending to ``TRADES`` would move
    ``summary()['fronts']`` and break the criterion."""
    assert len(ts.TRADES) == 6
    names = {t.name for t in ts.TRADES}
    for t in s6.TWO_PHASE_TRADES + s6.MIXED_TRADES:
        assert t.name not in names


def test_s6_5_the_stage1_trades_keep_the_stage1_candidate_rule():
    """S6 adds a per-trade filter; it does not repoint the existing six."""
    for t in ts.TRADES:
        assert t.candidate is None, (
            f"{t.name!r} must keep the default rule -- only rank-eligible feasible "
            "points enter a front")


# ======================================================================================
# S6-6 -- no ordering is emitted that D-20 or D-22 forbids, absent the re-acceptance
# ======================================================================================


def test_s6_6_ammonia_appears_in_the_chf_front_export_de_ranked_with_its_reason(study):
    """Both falsifiers, in opposite directions (D144 Q2=2b).

    "Appears in the front" binds as: appears in the front's EXPORTED OUTPUT, in a
    de-ranked category. Not membership of the non-dominated set.
    """
    rows = s6.front_table_rows(study, "chf_margin_vs_load")
    ammonia = [r for r in rows if r.startswith("Ammonia")]

    # Falsifier 1: ammonia absent from the CHF front. The re-acceptance licenses the row.
    assert ammonia, (
        "ammonia is absent from the CHF front's exported table; D-20/D-22 are "
        "RE-ACCEPTED at D139, which licenses the row -- suppressing it is a failure")

    # Falsifier 2: an ammonia ordering emitted without the de-rank surfaced.
    for row in ammonia:
        assert ",sensitivity_only," in row, (
            "an ammonia CHF row must carry its de-ranked category")
        assert "outside the correlation's fluid basis" in row, (
            "the exclusion must fire BY NAME with its source note, on the row")


def test_s6_6_ammonia_is_not_in_the_chf_front_member_list(study):
    """The honesty rule is not widened: a de-ranked point in ``member_point_ids`` is a
    falsifier. The rule may be widened by a ruling, never by a build."""
    front = study.front("chf_margin_vs_load")
    assert front.member_point_ids, "water is rank-eligible; the front must not be empty"
    assert not [m for m in front.member_point_ids if m.startswith("Ammonia")]
    assert all(m.startswith("Water") for m in front.member_point_ids)


def test_s6_6_water_is_rank_eligible_on_the_chf_leg(study):
    """The negative control for the de-rank: it must not fire on everything."""
    water = [p for p in study.points if p.fluid == "Water"]
    assert water and all(p.leg_status["chf"] is RankStatus.RANK_ELIGIBLE for p in water)


def test_s6_6_summary_feasible_ranked_keeps_its_stage1_meaning(stage1):
    """``feasible <=> FEASIBLE_RANKED`` still holds on the Stage-1 result, all 144."""
    assert all(p.feasible == (p.category is ts.PointCategory.FEASIBLE_RANKED)
               for p in stage1.points)


# ======================================================================================
# The candidate filter's witness, and the D144 hard line
# ======================================================================================


def test_s6_the_candidate_filter_has_a_witness(study):
    """**Exercise the witness, do not assume it (D144, S-3).**

    ``_metric`` is ``point.metrics[key]``, so the framework fails closed: a two-phase
    point reaching a mass front raises ``KeyError`` rather than ranking as a silent zero
    on a minimise axis -- which would put it top of the front. Weaken the filter and
    watch it go red.
    """
    mass_trade = next(t for t in ts.TRADES if t.y_key == "modeled_mass_kg")
    two_phase = [p for p in study.points if p.metrics]
    assert two_phase, "need at least one two-phase point carrying metrics"

    weakened = dataclasses.replace(mass_trade, candidate=lambda p: True)
    with pytest.raises(KeyError, match="modeled_mass_kg"):
        ts.pareto_front(two_phase, weakened)


def test_s6_the_witness_is_not_vacuous_the_same_call_succeeds_when_admission_is_right(
    study, stage1
):
    """The other half: the KeyError above is about admission, not about the trade."""
    mass_trade = next(t for t in ts.TRADES if t.y_key == "modeled_mass_kg")
    front = ts.pareto_front([s6._detached(p) for p in stage1.points], mass_trade)
    assert front.member_point_ids, (
        "the same trade over correctly-admitted points must build a front, or the "
        "KeyError proves nothing about the filter")


def test_s6_two_phase_points_never_acquire_the_harmonization_axes(study):
    """**D144 hard line.** ``radiator_temperature_K`` and ``radiator_area_m2`` are the
    Biswas/Suncatcher harmonization's axes; acquiring them puts S6 inside R3's scope."""
    for p in study.points:
        assert not (s6.FORBIDDEN_METRICS & set(p.metrics)), (
            f"{p.point_id} carries a forbidden metric: "
            f"{sorted(s6.FORBIDDEN_METRICS & set(p.metrics))}")


def test_s6_the_forbidden_metric_guard_can_fire():
    """The guard is mechanical, so it is exercised rather than trusted (S-3)."""
    with pytest.raises(ValueError, match="radiator_area_m2"):
        s6.TwoPhasePoint(
            "Water", 800.0, 300.0, 0.3, 5.0, True,
            ts.PointCategory.FEASIBLE_RANKED, (), {"radiator_area_m2": 2.5})


def test_s6_source_gated_fluid_is_reported_not_silently_dropped(study):
    """R134a has no registry entry declaring a validity domain. That is a statement
    about the evidence, and it must appear on the output rather than vanish."""
    r134a = [p for p in study.points if p.fluid == "R134a"]
    assert r134a, "the source-gated fluid must still produce rows"
    for p in r134a:
        assert p.category is ts.PointCategory.SOURCE_REQUIRED
        assert ts.ReasonCode.SOURCE_GATED_FLUID in p.reason_codes
        assert p.exclusion_notes and "source-gated" in p.exclusion_notes[0]
