"""Witness that every S2 check can actually fail (Stage 2, milestone S2).

A checker is a callable that *can* fail; a check that has never failed is not a
check. This script proves each S2 gate is load-bearing by deliberately breaking the
thing it guards -- one mutation at a time -- and requiring the mapped tests to fail.
A mutation that leaves the suite green is itself a failure: it means the gate does not
actually constrain the behaviour it claims to.

Each mutation is a literal source substitution, applied to a working copy, verified to
have changed the file, exercised, and then reverted. Files are restored in a
``finally`` block, so an interrupted run does not leave the tree dirty. An anchor that
no longer matches is reported as NOT WITNESSED rather than skipped, so the harness
cannot rot into a no-op as the source moves.

**Verification hazard.** ``pip install -e .`` in a second checkout repoints the global
editable install, which silently turns every mutation into a no-op -- the harness then
reports 0/N. This script therefore checks at start-up that the imported
``orbital_thermal`` is the one it is about to mutate, and refuses to run otherwise.

Usage::

    python scripts/witness_s2_checks.py            # run every mutation
    python scripts/witness_s2_checks.py --list     # show them without running
    python scripts/witness_s2_checks.py --json OUT # also write a machine record

Exit status is 0 only if **every** mutation was witnessed failing.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "orbital_thermal"

REGISTRY = SRC / "registry" / "two_phase.py"
APPLIC = SRC / "registry" / "applicability.py"
PROVENANCE = SRC / "registry" / "provenance.py"
TWO_PHASE = SRC / "two_phase.py"
TWO_PHASE_LOOP = SRC / "two_phase_loop.py"
FLUIDS = SRC / "fluids.py"

TEST_MODULES = (
    "tests/test_two_phase_evaporator.py",
    "tests/test_two_phase_registry.py",
    "tests/test_applicability_enforcement.py",
    "tests/test_boundary_enforcement.py",
    "tests/test_two_phase_loop.py",
    "tests/test_coupled_loop.py",
    "tests/test_c11_collapse.py",
)

COUPLED = SRC / "coupled_loop.py"
ASSESSMENT = SRC / "dp_basis_assessment.py"
COLLAPSE = SRC / "registry" / "collapse.py"


@dataclass(frozen=True)
class Mutation:
    """One deliberate break, and the tests that must notice it."""

    name: str
    guards: str
    path: Path
    old: str
    new: str
    expect_failing: tuple[str, ...]
    finding: str = ""
    notes: str = ""


@dataclass
class Result:
    mutation: str
    guards: str
    finding: str
    applied: bool
    witnessed: bool
    failed_tests: list[str] = field(default_factory=list)
    detail: str = ""


MUTATIONS: list[Mutation] = [
    # ---------------------------------------------------------------- registry scope
    Mutation(
        name="implement-an-unsourced-CHF-entry",
        guards="the exact-set evaluate guard and the locator<->evaluate invariant",
        finding="pre-existing",
        path=REGISTRY,
        old="        source=_SHAH_2015,\n        evaluate=None,",
        new="        source=_SHAH_2015,\n        evaluate=gungor_winterton_1986_htc,",
        expect_failing=(
            "test_exactly_the_s2_implemented_ids_carry_an_evaluate_callable",
            "test_s2_unimplemented_entries_are_still_none",
            "test_implemented_correlations_have_a_nonempty_locator",
        ),
        notes="Attaching maths to an entry whose source was never established.",
    ),
    Mutation(
        name="implement-a-named-dP-sensitivity",
        guards="ruling A4: only the REFERENCE pressure drop is implemented",
        finding="pre-existing",
        path=REGISTRY,
        old="        source=_FRIEDEL,\n        evaluate=None,",
        new="        source=_FRIEDEL,\n        evaluate=gungor_winterton_1986_htc,",
        expect_failing=(
            "test_only_the_reference_pressure_drop_is_implemented",
            "test_the_named_dp_sensitivities_stay_unimplemented",
            "test_exactly_the_s2_implemented_ids_carry_an_evaluate_callable",
        ),
        notes=(
            "Successor to the S2-era 'no dP entry may be implemented' mutation, which "
            "went obsolete the moment S3 legitimately implemented the reference. "
            "Friedel and Mueller-Steinhagen-Heck are sensitivities and stay unbuilt."
        ),
    ),
    Mutation(
        name="blank-the-locator-of-an-implemented-correlation",
        guards="the locator<->evaluate invariant",
        finding="pre-existing",
        path=REGISTRY,
        old='    locator=(\n        "Executable form confirmed by THREE',
        new='    locator="" and (\n        "Executable form confirmed by THREE',
        expect_failing=("test_implemented_correlations_have_a_nonempty_locator",),
        notes="An implemented correlation must record the source actually consulted.",
    ),
    # ------------------------------------------------------- F-03 provenance / eligibility
    # ------------------------------------------------------------- F-04 fluid axis
    Mutation(
        name="F04-record-applicability-violations-without-acting-on-them",
        guards="F-04: a violation must ALTER STATUS, not merely annotate",
        finding="F-04",
        path=TWO_PHASE,
        # Mutating the MAPPING, not one fold site: violations are folded into the
        # status in two places (HTC and CHF), and mutating only the first left the
        # ammonia case still de-ranked by the second. The first witness run caught it.
        old="_CONSEQUENCE_TO_STATUS = {\n    Consequence.DE_RANK: RankStatus.SENSITIVITY_ONLY,",
        new="_CONSEQUENCE_TO_STATUS = {\n    Consequence.DE_RANK: RankStatus.RANK_ELIGIBLE,",
        expect_failing=(
            "test_every_consequence_maps_to_a_status_that_actually_de_ranks",
        ),
        notes=(
            "This is the exact defect: appending a warning and not worsening status. "
            "A full ammonia case is de-ranked by two independent paths, so only a "
            "direct test of the mapping can witness it -- the first run showed that."
        ),
    ),
    Mutation(
        name="F04-widen-the-fluid-database-to-include-ammonia",
        guards="F-04: the sourced seven-fluid database",
        finding="F-04",
        path=REGISTRY,
        old='{"water", "r-11", "r-12", "r-22", "r-113", "r-114", "ethylene glycol"}',
        new='{"water", "ammonia", "r-11", "r-12", "r-22", "r-113", "r-114", "ethylene glycol"}',
        expect_failing=(
            "test_ammonia_is_not_in_the_gw86_fluid_database",
            "test_gw86_spec_matches_the_sourced_seven_fluid_database",
            "test_gate5_ammonia_is_de_ranked_through_gungor_winterton",
        ),
    ),
    # ------------------------------------------------------------ F-06 regime axis
    Mutation(
        name="F06-remove-the-liquid-Reynolds-turbulence-guard",
        guards="F-06: the Dittus-Boelter turbulent basis is checked, not documented",
        finding="F-06",
        path=REGISTRY,
        old="    min_liquid_reynolds=GW86_MIN_LIQUID_REYNOLDS,",
        new="    min_liquid_reynolds=None,",
        expect_failing=(
            "test_gate5_laminar_liquid_reynolds_rejects_the_case",
            "test_gw86_spec_matches_the_sourced_seven_fluid_database",
        ),
        notes="47 combinations inside the declared box are laminar; worst Re_L = 0.3.",
    ),
    Mutation(
        name="F06-stop-rejecting-laminar-flow-in-the-mechanism",
        guards="F-06: the regime axis actually rejects",
        finding="F-06",
        path=APPLIC,
        old="            elif liquid_reynolds < self.min_liquid_reynolds:",
        new="            elif False:",
        expect_failing=(
            "test_sibling_laminar_liquid_reynolds_is_rejected",
            "test_gate5_laminar_liquid_reynolds_rejects_the_case",
        ),
    ),
    # ------------------------------------------------------- D-9 geometry axis
    Mutation(
        name="D9-stop-enforcing-the-geometry-axis",
        guards="DEBTS D-9: 'tubes and annuli' enforced, not just in the title",
        finding="D-9",
        path=APPLIC,
        # Anchored inside check(), not declared_axes -- 'if self.geometries:' appears in
        # both, and a bare anchor hit the wrong one on the first witness run.
        old="        # --- geometry (DEBTS D-9) ---\n        if self.geometries:",
        new="        # --- geometry (DEBTS D-9) ---\n        if False:",
        expect_failing=(
            "test_sibling_geometry_outside_the_basis_is_de_ranked",
            "test_multiple_axis_failures_are_all_reported",
        ),
        notes="The hole that becomes live the moment a chevron geometry is supplied.",
    ),
    Mutation(
        name="D9-let-an-unstated-axis-pass-silently",
        guards="the rule that closes the class: silence is not consent",
        finding="D-9",
        path=APPLIC,
        old="            if fluid is None:",
        new="            if False:",
        expect_failing=("test_a_declared_axis_with_no_stated_value_blocks",),
        notes="Without this rule the class returns as 'enforced when someone remembers'.",
    ),
    # ------------------------------------------------------------ F-01 ONB criterion
    Mutation(
        name="F01-accept-any-object-as-a-sourced-ONB-criterion",
        guards="F-01: an ONB criterion must be typed and EVALUATED",
        finding="F-01",
        path=TWO_PHASE,
        old="        isinstance(onb_criterion, OnbCriterion)",
        new="        onb_criterion is not None",
        expect_failing=(
            "test_f01_a_non_criterion_object_is_not_treated_as_a_sourced_criterion",
        ),
        notes="The original defect: 'banana' returned sourced=True and was never called.",
    ),
    # ------------------------------------------------------------- F-02 CHF provenance
    Mutation(
        name="F02-accept-a-naked-CHF-float-again",
        guards="F-02: CHF must be a validated result binding its evidence",
        finding="F-02",
        path=TWO_PHASE,
        old="    if not isinstance(chf, ChfResult):",
        new="    if False:",
        expect_failing=("test_f02_a_naked_float_is_rejected_by_type",),
        notes="Any positive number could previously carry a case to RANK_ELIGIBLE.",
    ),
    Mutation(
        name="F02-let-a-violated-CHF-result-rank",
        guards="F-02: a CHF result carrying violations cannot rank",
        finding="F-02",
        path=TWO_PHASE,
        old="    if not chf.is_sourced:",
        new="    if False:",
        expect_failing=("test_f02_a_chf_result_with_violations_cannot_rank",),
    ),
    # ------------------------------------------------------ F-05 bound saturation state
    Mutation(
        name="F05-skip-the-state-consistency-check",
        guards="F-05: the guarded domain must be the evaluated domain",
        finding="F-05",
        path=TWO_PHASE,
        old='    if not state.matches(fluid=state.fluid, pressure_Pa=loop.pressure_Pa):',
        new="    if False:",
        expect_failing=("test_f05_a_loop_state_from_another_pressure_is_rejected",),
        notes="Properties at 0.3 MPa evaluating under a 1.0 MPa guard (18 % shift).",
    ),
    # ---------------------------------------------------------------- F-09 guard bypass
    Mutation(
        name="F09-reintroduce-a-domain-bypass-on-the-public-wrapper",
        guards="F-09: the ranked-facing wrapper always range-checks",
        finding="F-09",
        path=TWO_PHASE,
        # The defect was an API AFFORDANCE, so the mutation must restore it in the
        # SIGNATURE. Adding a flag to the body proved nothing on the first run.
        old="    gravity_m_s2: float = STANDARD_GRAVITY_M_S2,\n) -> HtcResult:",
        new=(
            "    gravity_m_s2: float = STANDARD_GRAVITY_M_S2,\n"
            "    check_domain: bool = True,\n) -> HtcResult:"
        ),
        expect_failing=("test_f09_the_public_wrapper_exposes_no_domain_bypass",),
        notes=(
            "Restores the removed keyword on the ranked-facing wrapper. Nothing in the "
            "old API distinguished a sensitivity call from a ranking call."
        ),
    ),
    # ------------------------------------------------------------------ F-10 backend pin
    Mutation(
        name="F10-stop-enforcing-the-backend-pin",
        guards="F-10: pinned properties require the pinned backend",
        finding="F-10",
        path=FLUIDS,
        old="    if installed == _COOLPROP_PIN.pinned_version:\n        return",
        new="    if True:\n        return",
        expect_failing=("test_f10_a_mismatched_backend_version_fails_evaluation",),
        notes="The pin was metadata only: any installed version silently applied.",
    ),
    Mutation(
        name="F10-allow-an-override-with-no-review-record",
        guards="F-10: the migration path is explicit and separately reviewed",
        finding="F-10",
        path=FLUIDS,
        old="    if not review_record.strip():",
        new="    if False:",
        expect_failing=(
            "test_f10_the_migration_path_is_explicit_and_requires_a_review_record",
        ),
    ),
    # ------------------------------------------- Shah (1987) transcription fidelity
    Mutation(
        name="SHAH-flip-the-F2-exponent-sign",
        guards="the reconciled F2 exponent (the minus sign the extract lost)",
        finding="F-03",
        path=REGISTRY,
        old="    f2 = f1**-0.42 if f1 <= 4.0 else 0.55",
        new="    f2 = f1**0.42 if f1 <= 4.0 else 0.55",
        expect_failing=("test_shah_1987_f2_exponent_is_negative_by_continuity",),
        notes=(
            "The supplied extract prints +0.42; continuity at F1 = 4 shows it must be "
            "negative (0.5588 vs 0.55, against a 3.25x jump)."
        ),
    ),
    Mutation(
        name="SHAH-use-the-extracts-Bo0-constant",
        guards="the reconciled Bo0 third constant (0.00024, not 0.0024)",
        finding="F-03",
        path=REGISTRY,
        old="        0.00024 * y**-0.105 * (1.0 + 1.15 * p_reduced**3.39),",
        new="        0.0024 * y**-0.105 * (1.0 + 1.15 * p_reduced**3.39),",
        expect_failing=(
            "test_shah_1987_bo_zero_third_candidate_uses_the_reconciled_constant",
        ),
        notes=(
            "A factor of ten. Bo0 is the HIGHEST of three candidates, so the wrong "
            "constant only shows up where candidate 3 could win -- at large Y. The "
            "order-of-magnitude plausibility test cannot see it; the direct one can."
        ),
    ),
    Mutation(
        name="SHAH-drop-the-gravity-explicit-guard",
        guards="the gravity axis: Shah (1987) has no microgravity limit",
        finding="new",
        path=REGISTRY,
        old="    gravity_explicit=True,",
        new="    gravity_explicit=False,",
        expect_failing=(
            "test_shah_1987_spec_carries_the_gravity_axis_and_the_ammonia_exclusion",
        ),
        notes="Y divides by g; as g -> 0 the correlation diverges.",
    ),
    Mutation(
        name="SHAH-allow-zero-gravity-evaluation",
        guards="the gravity guard in the correlating parameter itself",
        finding="new",
        path=REGISTRY,
        old="    if gravity_m_s2 <= 0.0:\n        raise ValueError(",
        new="    if False:\n        raise ValueError(",
        expect_failing=("test_shah_1987_y_is_gravity_explicit",),
    ),
    # ------------------------------------------------------------- carried-over gates
    Mutation(
        name="clamp-vapour-quality-instead-of-enforcing-it",
        guards="the 0 <= x <= 1 enforcement (gate 3)",
        finding="pre-existing",
        path=TWO_PHASE,
        old="    if not (0.0 <= x <= 1.0):\n        raise ValueError(",
        new="    if False:\n        raise ValueError(",
        expect_failing=("test_gate3_quality_outside_zero_one_is_rejected",),
    ),
    Mutation(
        name="collapse-subcooled-into-saturated",
        guards="regime classification and the ONB gate (gates 1a/1b, 3)",
        finding="pre-existing",
        path=TWO_PHASE,
        old="    if x_eq < 0.0:\n        regime, x = Regime.SUBCOOLED_LIQUID, None",
        new="    if False:\n        regime, x = Regime.SUBCOOLED_LIQUID, None",
        expect_failing=(
            "test_gate1a_subcooled_forced_convection_is_not_rank_eligible",
            "test_gate3_loop_state_classifies_instead_of_clamping",
        ),
    ),
    Mutation(
        name="widen-the-HTC-validity-domain-to-nothing",
        guards="the correlation range checks (gate 4)",
        finding="pre-existing",
        path=REGISTRY,
        old='                "G_kg_m2s": (10.0, 600.0),',
        new='                "G_kg_m2s": (0.0, 1.0e12),',
        expect_failing=(
            "test_gate4_htc_guard_fires_on_every_axis",
            "test_f09_out_of_domain_always_raises_through_the_wrapper",
        ),
    ),
    Mutation(
        name="move-the-CHF-rank-band-from-0.5-to-0.9",
        guards="director ruling A5 CHF bands (gate 5)",
        finding="pre-existing",
        path=TWO_PHASE,
        old="CHF_RANK_MAX = 0.5",
        new="CHF_RANK_MAX = 0.9",
        expect_failing=(
            "test_gate5_chf_band_between_half_and_one_is_sensitivity_not_ranked",
            "test_gate5_band_boundaries_are_closed_on_the_conservative_side",
        ),
    ),
    Mutation(
        name="let-an-averaged-flux-rank",
        guards="the local-flux discipline (gate 5)",
        finding="pre-existing",
        path=TWO_PHASE,
        old="    if not wall_flux.is_rankable_basis:\n        return ChfAssessment(",
        new="    if False:\n        return ChfAssessment(",
        expect_failing=(
            "test_gate5_underivable_local_flux_is_never_silently_averaged",
            "test_gate5_unsourced_geometry_de_ranks_a_local_flux",
        ),
    ),
    Mutation(
        name="assume-a-missing-CHF-is-safe",
        guards="the blocked-on-missing-CHF rule (gate 5)",
        finding="pre-existing",
        path=TWO_PHASE,
        old="        status = _worst(status, RankStatus.BLOCKED)",
        new="        status = _worst(status, RankStatus.RANK_ELIGIBLE)",
        expect_failing=(
            "test_gate5_missing_chf_blocks_the_case_rather_than_assuming_it_is_safe",
        ),
    ),
    Mutation(
        name="silently-correct-the-published-Cooper-constant",
        guards="fidelity to the printed source constant",
        finding="pre-existing",
        path=REGISTRY,
        old="* (-0.4343 * math.log(p_reduced)) ** -0.55",
        new="* (-math.log10(p_reduced)) ** -0.55",
        expect_failing=(
            "test_cooper_term_matches_the_independently_cross_checked_source",
        ),
    ),
    Mutation(
        name="drop-the-critical-point-guard",
        guards="no blanket supercritical treatment (gate 3)",
        finding="pre-existing",
        path=FLUIDS,
        old=(
            "    if T >= t_crit:\n        raise ValueError(\n"
            '            f"T = {T} K is at or above the critical temperature of {fluid} "'
        ),
        new=(
            "    if False:\n        raise ValueError(\n"
            '            f"T = {T} K is at or above the critical temperature of {fluid} "'
        ),
        expect_failing=("test_gate3_no_blanket_supercritical_treatment",),
    ),
    Mutation(
        name="disable-the-convective-enhancement-factor",
        guards="the flow-boiling physics (gates 1c/1d)",
        finding="pre-existing",
        path=REGISTRY,
        old="    e_factor = 1.0 + 24000.0 * bo**1.16 + conv_term",
        new="    e_factor = 1.0",
        expect_failing=(
            "test_gw86_htc_increases_with_quality_and_with_mass_flux",
            "test_gate1c_saturated_flow_boiling_is_evaluated_and_rank_eligible",
        ),
    ),
    # ============================================================ OTB-G001-FIXES
    # Round-2 guards. Four of these six defects were round-1 fixes built at one call
    # site instead of at the boundary, so each mutation below reopens the specific
    # door that was left open.
    Mutation(
        name="R2-F01-enforce-gravity-only-at-exactly-zero",
        guards="F-01: reduced gravity is an applicability violation, not just g <= 0",
        finding="R2 F-01",
        path=APPLIC,
        old="        if self.reference_gravity_m_s2 is not None:",
        new="        if False:",
        expect_failing=(
            "test_sibling_f01_reduced_gravity_is_an_applicability_violation",
        ),
        notes="Before the fix 1e-12 m/s^2 produced no violation at all.",
    ),
    Mutation(
        name="R2-F01-drop-the-database-gravity-declaration",
        guards="F-01: the boundary is the database's gravity, and is sourced",
        finding="R2 F-01",
        path=REGISTRY,
        old="    reference_gravity_m_s2=STANDARD_GRAVITY_M_S2,",
        new="    reference_gravity_m_s2=None,",
        expect_failing=(
            "test_sibling_f01_reduced_gravity_is_an_applicability_violation",
            "test_sibling_f01_the_threshold_is_sourced_not_invented",
        ),
    ),
    Mutation(
        name="R2-F01-disable-the-branch-straddle-test",
        guards="F-01: gravity moving a case across Shah's own branch threshold",
        finding="R2 F-01",
        path=APPLIC,
        old="                if here != there:",
        new="                if False:",
        expect_failing=(
            "test_sibling_f01_gravity_moving_a_case_across_shahs_branch_is_rejected",
        ),
    ),
    Mutation(
        name="R2-F02-let-a-ChfResult-be-hand-built",
        guards="F-02: a CHF result is unconstructible outside the evaluator",
        finding="R2 F-02",
        path=TWO_PHASE,
        old="        if _mint is not _CHF_MINT:",
        new="        if False:",
        expect_failing=(
            "test_sibling_f02_a_fabricated_chf_result_cannot_be_constructed",
            "test_sibling_f02_a_mutated_chf_result_cannot_be_rebuilt",
        ),
        notes="Round 1 wrapped a bare float in labels; a label nothing reads is not a fix.",
    ),
    Mutation(
        name="R2-F02-stop-verifying-the-case-binding",
        guards="F-02: the consumer verifies the result was produced for THIS case",
        finding="R2 F-02",
        path=TWO_PHASE,
        old="    diffs = chf.binding.agrees_with(binding)",
        new="    diffs = []",
        expect_failing=(
            "test_sibling_f02_a_replayed_chf_result_is_refused_by_the_consumer",
            "test_sibling_f02_the_binding_covers_every_identifying_field",
        ),
        notes="Being unforgeable is not enough if nobody checks who it was made for.",
    ),
    Mutation(
        name="R2-F03-compare-the-fluid-field-to-itself-again",
        guards="F-03: fluid identity is verified against re-derived properties",
        finding="R2 F-03",
        path=TWO_PHASE,
        old="        state.verify_is(state.fluid if fluid is None else fluid)",
        new="        state.matches(fluid=state.fluid, pressure_Pa=loop.pressure_Pa)",
        expect_failing=(
            "test_sibling_f03_a_relabelled_state_is_refused",
            "test_sibling_f03_verification_is_not_optional",
        ),
        notes="The original guard asked whether the state's fluid equals itself.",
    ),
    Mutation(
        name="R2-F03-make-verification-optional-again",
        guards="F-03: verification must not be skippable by omitting an argument",
        finding="R2 F-03",
        path=TWO_PHASE,
        old="    try:\n        state.verify_is(state.fluid if fluid is None else fluid)",
        new="    try:\n        state.verify_is(fluid) if fluid is not None else None",
        expect_failing=("test_sibling_f03_verification_is_not_optional",),
        notes=(
            "This is the shape my own first attempt took, and the probe walked straight "
            "through it by simply not passing the argument."
        ),
    ),
    Mutation(
        name="R2-F03-compare-only-the-headline-properties",
        guards="F-03: the full property set is compared, not a couple of fields",
        finding="R2 F-03",
        path=FLUIDS,
        old='    _VERIFIED_PROPERTIES = (\n        "T_sat_K",',
        new='    _VERIFIED_PROPERTIES = (\n        "T_sat_K",  # truncated\n    )\n    _UNUSED = (',
        expect_failing=("test_sibling_f03_the_full_property_set_is_compared",),
    ),
    Mutation(
        name="R2-F04-skip-the-mechanism-in-the-public-wrapper",
        guards="F-04: enforcement at the boundary, not only in assess_acquisition",
        finding="R2 F-04",
        path=TWO_PHASE,
        # Computes the violations and then DISCARDS them on the way out. This is
        # precisely the failure mode the handoff excludes -- "checking applicability
        # and discarding the answer would close this finding and change nothing".
        old="    return HtcResult(\n        value_W_m2=value,\n        violations=violations,",
        new="    return HtcResult(\n        value_W_m2=value,\n        violations=(),",
        expect_failing=(
            "test_every_public_value_producing_entry_point_enforces_applicability",
            "test_sibling_f04_a_blocking_axis_raises_rather_than_returning",
        ),
        notes="The exact round-1 shape: the check existed, one door did not use it.",
    ),
    Mutation(
        name="R2-F05-accept-any-non-blank-review-record",
        guards="F-05: the review record must resolve to a real file",
        finding="R2 F-05",
        path=FLUIDS,
        old="    resolved = _resolve_review_record(review_record)",
        new="    resolved = review_record",
        expect_failing=("test_sibling_f05_an_unresolvable_review_record_is_refused",),
        notes="Round 1 made the pin real, then added a door whose lock opens to any key.",
    ),
    Mutation(
        name="R2-F06-unbound-the-inlet-quality-axis",
        guards="F-06: inlet quality is enforced, so CHF cannot be inflated",
        finding="R2 F-06",
        path=REGISTRY,
        old='                "inlet_quality": (-2.6, 0.85),',
        new='                "inlet_quality": (-1.0e9, 1.0e9),',
        expect_failing=(
            "test_sibling_f06_out_of_range_inlet_quality_is_refused",
            "test_sibling_f06_the_provenance_is_recorded_as_it_actually_is",
        ),
        notes="x_in = -1000 inflated CHF ~1000x and still reported sourced.",
    ),
    Mutation(
        name="R2-F06-stop-passing-inlet-quality-to-the-domain-guard",
        guards="F-06: the enforced bound is actually reached by the evaluator",
        finding="R2 F-06",
        path=TWO_PHASE,
        old=(
            "        critical_quality=critical_quality,\n"
            "        inlet_quality=inlet_quality,\n    )"
        ),
        new="        critical_quality=critical_quality,\n    )",
        expect_failing=("test_sibling_f06_out_of_range_inlet_quality_is_refused",),
        notes="A declared bound nothing passes a value to is a declared bound, not a guard.",
    ),
    # ================================================================ S3 / OTB-G002
    Mutation(
        name="S3-DIR02-let-an-entry-with-no-executable-form-rank",
        guards="DIR-02: eligibility requires an executable form, generically",
        finding="S3 DIR-02",
        path=PROVENANCE,
        old="        return self.has_executable_form",
        new="        return True",
        expect_failing=(
            "test_dir02_eligibility_requires_an_executable_form_generically",
        ),
        notes=(
            "Round 1 demoted one entry's status; the permissive rule survived. NOTE: "
            "the class-level sweep cannot witness this while no shipped entry is "
            "status-eligible but formless -- the desired end state -- so the "
            "synthetic-entry test is what holds the rule."
        ),
    ),
    Mutation(
        name="S3-DIR02-forget-where-the-B1-forms-live",
        guards="DIR-02: 'implemented elsewhere' is distinguishable from 'unimplemented'",
        finding="S3 DIR-02",
        path=REPO / "src" / "orbital_thermal" / "registry" / "correlations.py",
        old='        executable_form="orbital_thermal.solid_network.spreading_resistance",',
        new="",
        expect_failing=("test_dir02_eligibility_requires_an_executable_form_generically",),
        notes="Without the location the generic rule would wrongly demote a B1 entry.",
    ),
    Mutation(
        name="S3-drop-the-composition-axis",
        guards="LM's two-component basis, which this loop violates",
        finding="S3 DP-APPL",
        path=REGISTRY,
        old='    compositions=frozenset({"two_component"}),',
        new="    compositions=frozenset(),",
        expect_failing=(
            "test_sibling_composition_single_component_is_outside_the_basis",
            "test_this_loop_violates_the_correlation_on_two_axes_at_once",
        ),
    ),
    Mutation(
        name="S3-drop-the-horizontal-orientation-basis",
        guards="LM's horizontal basis, which this loop violates",
        finding="S3 DP-APPL",
        path=REGISTRY,
        old=(
            '    orientations=frozenset({"horizontal"}),\n    orientations_basis=(\n       '
            ' "Collier & Thome p. 54'
        ),
        new=(
            '    orientations=frozenset(),\n    orientations_basis=(\n        "Collier & Th'
            'ome p. 54'
        ),
        expect_failing=(
            "test_sibling_orientation_vertical_is_outside_the_basis",
            "test_this_loop_violates_the_correlation_on_two_axes_at_once",
        ),
    ),
    Mutation(
        name="S3-drop-the-database-gravity-on-the-dP-leg",
        guards="D12: gravity is an enforced axis on the pressure-drop leg too",
        finding="S3 D12",
        path=REGISTRY,
        old=(
            "    reference_gravity_m_s2=STANDARD_GRAVITY_M_S2,\n    numeric_domain_provenan"
            "ce=DomainProvenance.UNESTABLISHED,\n    numeric_domain_note=(\n        \"The d"
            "eclared P_Pa ceiling"
        ),
        new=(
            "    reference_gravity_m_s2=None,\n    numeric_domain_provenance=DomainProvenan"
            "ce.UNESTABLISHED,\n    numeric_domain_note=(\n        \"The declared P_Pa ceil"
            "ing"
        ),
        expect_failing=(
            "test_sibling_gravity_is_a_declared_axis_consistent_with_shah_1987",
        ),
        notes="The two legs must be consistent; this is what the D12 test pins.",
    ),
    Mutation(
        name="S3-let-the-static-term-quietly-vanish-in-microgravity",
        guards="D12: omission makes it silently microgravity",
        finding="S3 D12",
        path=REGISTRY,
        old=(
            "    if gravity_m_s2 <= 0.0:\n        raise ValueError(\n            f\"static "
            "head is evaluated at g ="
        ),
        new=(
            "    if False:\n        raise ValueError(\n            f\"static head is evalua"
            "ted at g ="
        ),
        expect_failing=(
            "test_sibling_gravity_zero_g_refuses_rather_than_contributing_zero",
        ),
        notes="The rejected option, which is exact and still wrong (D12).",
    ),
    Mutation(
        name="S3-hard-code-the-bore-band",
        guards="D11: the band is read from the registry, not chosen",
        finding="S3 D11",
        path=TWO_PHASE_LOOP,
        old="        rng = entry.domain.ranges.get(\"D_m\")",
        new="        rng = (0.5e-3, 50e-3)",
        expect_failing=("test_the_bore_band_is_read_from_the_registry_not_hard_coded",),
    ),
    Mutation(
        name="S3-drop-the-provenance-label-from-the-sweep-output",
        guards="D11: the label appears in the OUTPUT, not a comment",
        finding="S3 D11",
        path=TWO_PHASE_LOOP,
        old='        lines = [head, self.provenance_label]',
        new="        lines = [head]",
        expect_failing=("test_the_negative_result_is_the_result",),
    ),
    Mutation(
        name="S3-let-the-condenser-size-itself",
        guards="D10: no condensation coefficient is computed or estimated at S3",
        finding="S3 D10",
        path=TWO_PHASE_LOOP,
        old=(
            "        raise NotRankEligibleError(\n            \"condenser area cannot be co"
            "mputed at S3"
        ),
        new=(
            "        return 1.0\n        raise NotRankEligibleError(\n            \"condens"
            "er area cannot be computed at S3"
        ),
        expect_failing=("test_the_condenser_refuses_to_size_itself",),
        notes="A plausible area is worse than a blocker: it would look like a result.",
    ),
    Mutation(
        name="S3-accept-a-pump-inlet-at-saturation",
        guards="D8: the subcooling margin must be strictly positive",
        finding="S3 D8",
        path=TWO_PHASE_LOOP,
        old="    if margin <= required_margin_K:",
        new="    if margin < -1.0e9:",
        expect_failing=("test_pump_inlet_at_saturation_is_the_cavitation_condition",),
    ),
    Mutation(
        name="S3-let-a-sweep-silently-drop-its-failures",
        guards="D7: a negative result is a result, so failures are recorded",
        finding="S3 D7",
        path=TWO_PHASE_LOOP,
        old="        if not band.contains(d):\n            points.append(",
        new="        if not band.contains(d):\n            continue\n            points.append(",
        expect_failing=("test_a_bore_outside_the_band_is_recorded_not_dropped",),
    ),
    Mutation(
        name="S3-DIR01-blur-the-geometry-vocabulary",
        guards="DIR-01: round_tube and channel are defined and disjoint",
        finding="S3 DIR-01",
        path=REGISTRY,
        old='    "channel": (\n        "A NON-circular passage',
        new='    "channel": (\n        "A circular passage',
        expect_failing=("test_dir01_round_tube_and_channel_are_defined_and_disjoint",),
    ),
    # ========================================== OTB-G002 machine-verification fixes
    Mutation(
        name="V01-admit-a-declaration-instead-of-a-fact",
        guards="V-01: rank-eligibility needs a form that can be REACHED",
        finding="V-01",
        path=PROVENANCE,
        old="        return resolve_executable_form(self.executable_form) is not None",
        new="        return bool(self.executable_form.strip())",
        expect_failing=(
            "test_v01_a_declaration_that_cannot_be_honoured_is_not_eligible",
        ),
        notes=(
            "The exact pre-fix expression. 'x' made an entry rank-eligible. Nothing "
            "shipped broken, which is precisely why it needed saying: the same "
            "standard let round-1 F-03 return as DIR-02."
        ),
    ),
    Mutation(
        name="V01-let-a-declaration-reach-outside-the-package",
        guards="V-01: a declared form must live inside orbital_thermal",
        finding="V-01",
        path=PROVENANCE,
        old='    if path.startswith(_EXECUTABLE_FORM_ROOT) and "." in path:',
        new='    if "." in path:',
        expect_failing=(
            "test_v01_a_declaration_that_cannot_be_honoured_is_not_eligible",
        ),
    ),
    Mutation(
        name="V01-accept-a-non-callable-attribute",
        guards="V-01: the resolved target must actually be callable",
        finding="V-01",
        path=PROVENANCE,
        old="        if callable(candidate):\n            resolved = candidate",
        new="        if candidate is not None:\n            resolved = candidate",
        expect_failing=(
            "test_v01_a_declaration_that_cannot_be_honoured_is_not_eligible",
        ),
    ),
    Mutation(
        name="V01-stop-reporting-unresolved-declarations",
        guards="V-01: the loud half -- a broken declaration is named, not just silent",
        finding="V-01",
        path=PROVENANCE,
        old="        elif resolve_executable_form(declared) is None:",
        new="        elif False:",
        expect_failing=("test_v01_the_reporter_actually_names_a_broken_declaration",),
        notes=(
            "The shipped-declarations sweep cannot witness this while nothing is "
            "broken -- the harness caught that -- so a synthetic broken declaration "
            "holds it. Fails closed at the boundary AND loud in the test, because "
            "they do "
            "different jobs: the boundary refuses, the test says which declaration "
            "broke. Neither alone was judged sufficient."
        ),
    ),
    Mutation(
        name="V02-reassert-that-the-printed-equation-was-illegible",
        guards="V-02: the artifact must not say something false about the source",
        finding="V-02",
        path=REGISTRY,
        old=(
            "        \"S3 PROVENANCE. Eqs. (2.67), (2.68), (2.69) and the Chisholm C "
            "table were READ \""
        ),
        new="        \"S3 PROVENANCE. Eq. (2.68) is NOT legible -- its operators are lost. READ \"",
        expect_failing=(
            "test_v02_no_provenance_field_claims_the_equation_was_illegible",
        ),
        notes="Eq. (2.68) is sharply printed on p. 53; the PDF's text layer is what was degraded.",
    ),
    Mutation(
        name="V02-delete-the-true-limitation-along-with-the-false-claim",
        guards="V-02 control: the real caveat survives the correction",
        finding="V-02",
        path=REGISTRY,
        old='        "LIMITATION OF THE FILE, NOT THE SOURCE: this PDF\'s embedded text layer is "',
        new=(
            '        "" or "LIMITATION OF THE FILE, NOT THE SOURCE: this PDF\'s embed'
            'ded text layer is "'
        ),
        expect_failing=("test_v02_control_the_true_limitation_is_still_recorded",),
        notes="Removing a false claim must not also remove the true caveat next to it.",
    ),
    Mutation(
        name="V02-relabel-the-cross-check-as-the-equations-source",
        guards="V-02: the identity confirms the printed equation, it is not its source",
        finding="V-02",
        path=REGISTRY,
        old='        "INDEPENDENT CONFIRMATION of the printed equation, not its source. "',
        new='        "the source of the equation. "',
        expect_failing=(
            "test_v02_control_the_derivation_survives_relabelled_as_confirmation",
        ),
    ),
    # ------------------------------------------------- OTB-G002 reviewer findings
    Mutation(
        name="F01-hold-the-mass-flux-constant-across-bore",
        guards="F-01: the swept variable must reach the physics it is supposed to move",
        finding="F-01",
        path=TWO_PHASE_LOOP,
        old="    mass_flux = mass_flow_kg_s / area_m2",
        new="    mass_flux = mass_flow_kg_s / (math.pi * 2.0e-3**2 / 4.0)",
        expect_failing=(
            "test_f01_mass_flux_moves_with_bore",
            "test_f01_control_the_derivation_is_arithmetically_right",
            "test_f01_the_sweep_records_the_flux_it_used_at_every_point",
        ),
        notes="The exact defect: hydraulics pinned to one bore while the sweep varied bore.",
    ),
    Mutation(
        name="F01-decouple-the-phase-reynolds-numbers-from-bore",
        guards="F-01: both phase Reynolds numbers are derived from the bore",
        finding="F-01",
        path=TWO_PHASE_LOOP,
        old="    re_f, re_g = g_f * diameter_m / mu_f, g_g * diameter_m / mu_g",
        new="    re_f, re_g = 5.0e3, 5.0e3",
        expect_failing=(
            "test_f01_both_phase_reynolds_numbers_move_with_bore",
            "test_f01_control_the_derivation_is_arithmetically_right",
        ),
        notes=(
            "Pinning only the length scale is NOT enough to break the monotone test -- "
            "the mass flux still varies, so Re still moves. Pinned outright instead."
        ),
    ),
    Mutation(
        name="F01-stop-recording-the-flux-on-each-sweep-point",
        guards="F-01: a sweep must be able to show that its hydraulics moved",
        finding="F-01",
        path=TWO_PHASE_LOOP,
        old=(
            "                    mass_flux_kg_m2s=dp.hydraulics.mass_flux_kg_m2s\n"
            "                    if dp.hydraulics is not None\n"
            "                    else None,"
        ),
        new="                    mass_flux_kg_m2s=None,",
        expect_failing=("test_f01_the_sweep_records_the_flux_it_used_at_every_point",),
        notes=(
            "Nothing in the pre-fix sweep output could have revealed the constant flux. "
            "This is the reporting half, witnessed separately from the derivation."
        ),
    ),
    Mutation(
        name="F02-let-a-single-component-fluid-be-declared-two-component",
        guards="F-02: declarations that are not derivable must still be consistency-checked",
        finding="F-02",
        path=APPLIC,
        old=(
            "        if fluid.strip().lower() in pure and "
            'composition.strip().lower() == "two_component":'
        ),
        new='        if False and fluid.strip().lower() in pure:',
        expect_failing=(
            "test_f02_a_single_component_fluid_declared_two_component_is_a_contradiction",
            "test_f02_the_contradiction_check_is_at_the_boundary_not_the_sweep",
        ),
    ),
    Mutation(
        name="F02-let-horizontal-flow-carry-a-static-head",
        guards="F-02: the static head is identically zero in horizontal flow",
        finding="F-02",
        path=APPLIC,
        old='        if orientation.strip().lower() == "horizontal" and abs(height_m) > 0.0:',
        new='        if False and orientation.strip().lower() == "horizontal":',
        expect_failing=("test_f02_horizontal_with_a_static_height_is_a_contradiction",),
    ),
    Mutation(
        name="F02-classify-every-flow-as-turbulent-regardless-of-reynolds",
        guards="F-02: regime is computed from the state, never declared",
        finding="F-02",
        path=TWO_PHASE_LOOP,
        old='    return "laminar" if reynolds <= _LAMINAR_RE_MAX else "turbulent"',
        new='    return "" or "turbulent"',
        expect_failing=("test_f02_flow_regime_is_computed_never_declared",),
        notes="A regime that cannot come out laminar is a label wearing a computation's clothes.",
    ),
    Mutation(
        name="F03-break-the-single-phase-limit-with-a-floor-on-the-multiplier",
        guards="F-03: as x -> 0 the two-phase dP must recover the Stage-1 single-phase dP",
        finding="F-03",
        path=REGISTRY,
        old="    return 1.0 + C / X + 1.0 / X**2",
        new="    return 1.0 + C / X + 1.0 / X**2 + 0.05",
        expect_failing=(
            "test_f03_x_to_zero_recovers_the_stage1_single_phase_pressure_drop",
            "test_f03_the_approach_to_the_single_phase_limit_is_order_sqrt_x",
            "test_f03_the_multiplier_itself_tends_to_one",
        ),
        notes=(
            "A 5% offset is invisible at the working quality and fatal at the limit -- "
            "which is exactly why the limit needed a test rather than a spot check."
        ),
    ),
    Mutation(
        name="F04-guard-non-finite-inputs-with-a-sign-test-again",
        guards="F-04: NaN passes every comparison, so > 0 is not a finiteness check",
        finding="F-04",
        path=TWO_PHASE_LOOP,
        old="            _v.positive(name, value)",
        new="            if value <= 0.0:\n                raise ValueError(f'{name} must be > 0')",
        expect_failing=(
            "test_f04_a_non_finite_input_is_refused_not_returned_as_nan",
            "test_f04_a_non_finite_gravity_or_height_is_refused",
        ),
        notes="The exact pre-fix expression: a sign test that NaN walks straight through.",
    ),
    Mutation(
        name="F04-let-quality-leave-the-unit-interval",
        guards="F-04: quality is a mass fraction, so 1.7 and -0.5 are not answers",
        finding="F-04",
        path=TWO_PHASE_LOOP,
        old="            _v.in_range(name, value, 0.0, 1.0)",
        new="            _v.in_range(name, value, -1.0e9, 1.0e9)",
        expect_failing=("test_f04_an_impossible_quality_is_refused",),
    ),
    # -------------------------------------------------------- OTB-G003 (S4) checks
    Mutation(
        name="S4-let-a-de-ranked-pressure-drop-onto-the-characteristic",
        guards="S4-7: a coupled solve may not be built on a number the correlation "
        "disclaims",
        finding="S4",
        path=COUPLED,
        old="            if not result.is_applicable:",
        new="            if False and not result.is_applicable:",
        expect_failing=(
            "test_s4_7_the_refusal_is_behavioural_not_read_off_the_registry",
            "test_s4_7_every_blocked_leg_names_an_axis_an_entry_and_an_unblocker",
            "test_s4_7_no_operating_point_is_invented_when_a_leg_refuses",
        ),
        notes=(
            "The defect found during this build. Lockhart-Martinelli refuses this "
            "project by DE_RANK, which RETURNS a finite number with violations "
            "attached; a leg check that only caught exceptions reported the reference "
            "case's pressure-drop leg as AVAILABLE and solved it."
        ),
    ),
    Mutation(
        name="S4-let-a-label-alone-make-something-a-demonstration",
        guards="S4-1: a demonstration must be in basis, not merely declared one",
        finding="S4",
        path=COUPLED,
        old="        if not leg.available:\n            raise NotRankEligibleError(\n"
        '                "this case is NOT inside the declared basis',
        new="        if False:\n            raise NotRankEligibleError(\n"
        '                "this case is NOT inside the declared basis',
        expect_failing=(
            "test_s4_1_a_demonstration_must_actually_be_in_basis_not_merely_labelled",
        ),
        notes="Relabelling the reference case would otherwise buy it a demonstration "
        "banner.",
    ),
    Mutation(
        name="S4-blank-the-demonstration-disclosure",
        guards="S4-2: a demonstration's own output says what it is not",
        finding="S4",
        path=COUPLED,
        old='    "MACHINERY DEMONSTRATION -- NOT A RESULT ABOUT THIS PROJECT\'S DEVICE. "',
        new='    "" or "" "" "" ',
        expect_failing=(
            "test_s4_2_the_disclosure_is_in_the_rendered_output_and_cannot_be_blanked",
            "test_s4_2_str_renders_the_disclosure_so_printing_cannot_lose_it",
        ),
    ),
    Mutation(
        name="S4-return-only-the-first-operating-point",
        guards="S4-5: non-uniqueness is reported, never resolved",
        finding="S4",
        path=COUPLED,
        old="    return tuple(roots)\n\n\ndef loop_characteristic",
        new="    return tuple(roots[:1])\n\n\ndef loop_characteristic",
        expect_failing=(
            "test_s4_5_every_root_is_reported_and_none_is_selected",
            "test_s4_5_the_result_reports_non_uniqueness_rather_than_resolving_it",
            "test_s4_6_the_guard_fires_on_the_middle_root_and_not_the_outer_two",
        ),
        notes="Silently selecting one of three steady states is the exact thing S0 "
        "forbids.",
    ),
    Mutation(
        name="S4-make-the-Ledinegg-criterion-non-strict",
        guards="S4-6: the adopted criterion is a STRICT sign test",
        finding="S4",
        path=REGISTRY,
        old="    return slope_dP_dmdot_Pa_s_kg < 0.0",
        new="    return slope_dP_dmdot_Pa_s_kg <= 0.0",
        expect_failing=("test_s4_6_the_criterion_is_a_strict_sign_test",),
        notes="A stationary point is the boundary case, not the unstable one; "
        "widening it is a builder's margin applied to a sourced criterion.",
    ),
    Mutation(
        name="S4-flip-the-Ledinegg-criterion",
        guards="S4-6: negative slope is the excursion, not positive",
        finding="S4",
        path=REGISTRY,
        old="    return slope_dP_dmdot_Pa_s_kg < 0.0",
        new="    return slope_dP_dmdot_Pa_s_kg > 0.0",
        expect_failing=(
            "test_s4_6_the_criterion_is_a_strict_sign_test",
            "test_s4_6_the_guard_fires_on_the_middle_root_and_not_the_outer_two",
        ),
    ),
    Mutation(
        name="S4-always-report-the-refusal-as-an-absence-of-knowledge",
        guards="S4-8: a policy refusal must not be reported as an empty literature",
        finding="S4",
        path=ASSESSMENT,
        old="    if not assessment.admits_part_of_the_band:",
        new="    if True:",
        expect_failing=(
            "test_s4_8_the_classifier_still_returns_policy_when_the_candidate_does_reach",
        ),
        notes="'No correlation exists for this corner' and 'one does and was not "
        "adopted' are different claims and only one is true. The blocked-leg test "
        "does NOT catch this -- it accepts either kind, by design. Nor does the "
        "reference case, whose refusal IS a knowledge refusal once the whole declared "
        "basis is applied; the guard is the classifier's other branch.",
    ),
    Mutation(
        name="S4-judge-fluid-coverage-on-mass-flux-alone",
        guards="S4-9: the fluid's bore and mass-flux ranges must hold at the SAME bore",
        finding="S4",
        path=ASSESSMENT,
        old="        fluid_supported=flux_matched.intersect(bore_hull),",
        new="        fluid_supported=flux_matched,",
        expect_failing=(
            "test_s4_9_two_different_overlaps_are_reported_and_not_conflated",
        ),
        notes="Dropping the bore constraint turns 'no bore satisfies both' into a "
        "spurious 0.3 mm overlap -- a fluid list read as a coverage map.",
    ),
    Mutation(
        name="S4-invert-the-mass-flux-to-bore-mapping",
        guards="S4-9: G falls as D rises, so the flux ceiling sets the LOWER bore bound",
        finding="S4",
        path=ASSESSMENT,
        old="    d_lo = math.sqrt(4.0 * mass_flow_kg_s / (math.pi * g_hi))\n"
        "    d_hi = math.sqrt(4.0 * mass_flow_kg_s / (math.pi * g_lo))",
        new="    d_lo = math.sqrt(4.0 * mass_flow_kg_s / (math.pi * g_lo))\n"
        "    d_hi = math.sqrt(4.0 * mass_flow_kg_s / (math.pi * g_hi))",
        expect_failing=(
            "test_s4_9_the_mass_flux_to_bore_inversion_is_the_right_way_round",
            "test_s4_9_two_different_overlaps_are_reported_and_not_conflated",
        ),
    ),
    Mutation(
        name="S4-drop-the-hours-to-seconds-factor-in-the-kcal-conversion",
        guards="S4-10: a non-SI source is converted at the boundary and tested",
        finding="S4",
        path=REGISTRY,
        old="    return q_kcal_m2_hr * kcal_J / 3600.0",
        new="    return q_kcal_m2_hr * kcal_J",
        expect_failing=(
            "test_s4_10_the_kcal_conversion_matches_an_independently_computed_value",
        ),
        notes="The Ayub (2003) hazard class: an SI implementation that omits the "
        "conversion is silently wrong by a factor of 3600.",
    ),
    Mutation(
        name="S4-swap-the-two-kilocalorie-definitions",
        guards="S4-10: where the unit is ambiguous, both readings are recorded",
        finding="S4",
        path=REGISTRY,
        old="KCAL_IT_J = 4186.8",
        new="KCAL_IT_J = 4184.0",
        expect_failing=(
            "test_s4_10_both_kilocalorie_definitions_are_recorded_and_differ_as_expected",
            "test_s4_10_the_kcal_conversion_matches_an_independently_computed_value",
        ),
    ),
    Mutation(
        name="S4-widen-the-Shah-1974-pressure-domain-to-cover-this-loop",
        guards="S4-10/D-6: the registered gap must stay machine-visible",
        finding="S4",
        path=REGISTRY,
        old="SHAH_1974_P_MAX_PA = 4.29248e5  # T_sat =   0 C",
        new="SHAH_1974_P_MAX_PA = 25.0e5  # T_sat =   0 C",
        expect_failing=(
            "test_s4_10_shah_1974_refuses_this_loop_on_every_declared_numeric_axis",
        ),
        notes="Registering the entry makes D-6 measurable; widening its domain to "
        "admit this loop would delete the measurement.",
    ),
    Mutation(
        name="S4-drop-the-D-13-disclosure-from-the-energy-balance",
        guards="S4-11: an unresolved provenance travels with every result using it",
        finding="S4",
        path=COUPLED,
        old=(
            "            (_PUMP_EFFICIENCY_DISCLOSURE,) "
            "if self.pump_heat_into_fluid_W > 0.0 else ()"
        ),
        new="            ()",
        expect_failing=(
            "test_s4_11_any_balance_carrying_pump_heat_carries_the_d13_disclosure",
        ),
    ),
    Mutation(
        name="S4-drop-the-pump-heat-from-the-rejected-load",
        guards="S4-12: energy closure carries pump heat in the rejected load (S0)",
        finding="S4",
        path=COUPLED,
        old="    rejected = duty_W + pump.fluid_heat_W",
        new="    rejected = duty_W",
        expect_failing=(
            "test_s4_12_the_rejected_load_is_duty_plus_pump_heat_and_closes",
            "test_s4_12_the_pump_term_is_load_bearing_in_the_balance",
        ),
        notes=(
            "The D-13 disclosure test does NOT catch this, and that is correct: the "
            "disclosure keys off pump heat being computed, not off it reaching the "
            "rejected load. Two different guards for two different failures."
        ),
    ),
    Mutation(
        name="S4-broadcast-the-transitional-flow-warnings-instead-of-recording-them",
        guards="a real caveat must reach the result, not a warnings log",
        finding="S4",
        path=COUPLED,
        old="    transitional = transitional_count[0]",
        new="    transitional = 0",
        expect_failing=("test_the_transitional_flow_caveat_travels_on_the_result",),
    ),
    # ------------------------------------------- OTB-G003-FIXES corrections
    Mutation(
        name="S4F-apply-only-the-convenient-declared-axes",
        guards="S4-9: every declared range binds, not a chosen subset",
        finding="S4-FIX",
        path=ASSESSMENT,
        old="    for name, (lo, hi) in ranges.items():",
        new="    for name, (lo, hi) in "
        "{k: v for k, v in ranges.items() if k in ('D_h_m','G_kg_m2s','P_R')}.items():",
        expect_failing=(
            "test_s4_9_every_declared_axis_is_applied_not_a_chosen_subset",
            "test_s4_9_the_reynolds_ceiling_binds_at_small_bore_and_narrows_the_window",
            "test_s4_9_the_admitted_window_is_empty_away_from_the_middle_qualities",
            "test_s4_8_the_refusal_is_knowledge_once_the_whole_declared_basis_is_applied",
        ),
        notes=(
            "The defect this round corrected. Applying three of seven declared axes "
            "reported an admitted window 2.2 mm too wide at the low end and "
            "classified the refusal as POLICY when the whole basis makes it KNOWLEDGE."
        ),
    ),
    Mutation(
        name="S4F-silently-skip-an-axis-with-no-evaluator",
        guards="S4-9: an unimplemented declared axis must be loud, not skipped",
        finding="S4-FIX",
        path=ASSESSMENT,
        old="        if evaluator is None:\n            raise ValueError(",
        new="        if evaluator is None:\n            continue\n        if False:\n"
        "            raise ValueError(",
        expect_failing=(
            "test_s4_9_a_declared_axis_with_no_evaluator_raises_rather_than_being_skipped",
        ),
    ),
    Mutation(
        name="S4F-assess-at-a-convenient-quality-instead-of-the-loops-own",
        guards="S4-9: two declared axes depend on quality, so the value decides the answer",
        finding="S4-FIX",
        path=COUPLED,
        old="        quality=x_mean,",
        new="        quality=0.5,",
        expect_failing=(
            "test_s4_8_the_refusal_is_knowledge_once_the_whole_declared_basis_is_applied",
        ),
        notes="At x = 0.5 the candidate admits part of the band; at the loop's own "
        "x = 0.048 it admits nothing. Picking the quality picks the verdict.",
    ),
    # SUPERSEDED BY C11. This mutation blanked the hand-written disclosure constant
    # `_LEDINEGG_UNREACHABLE_DISCLOSURE`, which no longer exists: C11 replaced it with a
    # statement DERIVED from the collapse/detect cross-check. Removed rather than
    # repointed, because the two C11 mutations below break the derivation itself, which
    # is a strictly stronger test than blanking a constant -- and the harness reported
    # the rotted anchor as a failure rather than skipping it, which is why it was found.
    Mutation(
        name="S4F-drop-the-Shah-property-backend-caveat",
        guards="C8: a correlation and the properties it was fitted against are a package",
        finding="S4-FIX",
        path=REGISTRY,
        old=(
            '        "THE PROPERTY BACKEND IS PART OF THE METHOD, and this one is '
            'not the project\'s. "'
        ),
        new='        "" or "" "" "" ',
        expect_failing=("test_s4_10_the_property_backend_caveat_is_recorded",),
    ),
    Mutation(
        name="S4F-register-the-Shah-pressure-drop-half",
        guards="the pressure-drop half is deliberately NOT registered at all",
        finding="S4-FIX",
        path=REGISTRY,
        old='        id="two_phase.htc.shah_1974_ammonia",\n'
        '        name="Shah ammonia-evaporator flow-boiling HTC (psi-Y)",\n'
        '        kind="htc",',
        new='        id="two_phase.htc.shah_1974_ammonia",\n'
        '        name="Shah ammonia-evaporator flow-boiling HTC (psi-Y)",\n'
        '        kind="dp",',
        expect_failing=(
            "test_s4_10_only_the_heat_transfer_half_of_shah_1974_is_registered",
        ),
        notes="Registering the pressure-drop half would assert that the literature "
        "covers a domain it does not, and D-6 is a heat-transfer debt.",
    ),
    # ---------------------------------------------------- C11 (OTB-MAINT-02 MAINT-02-01)
    # The three mutations the finding's own check specification mandates. Each must turn
    # the check RED; a check that survives any of them is trivially true and METHOD
    # 5.4.5 rejects it.
    Mutation(
        name="C11-mutation-1-delete-the-boundary-crosscheck",
        guards="C11(ii): the shared boundary intersects detects with collapses (C9)",
        finding="C11",
        path=COLLAPSE,
        old="    collapsed = model.collapsed_phenomena()\n    return tuple(",
        new="    collapsed = {}\n    return tuple(",
        expect_failing=(
            "test_c11_the_boundary_reports_the_conflict_naming_guard_term_and_phenomenon",
            "test_c11_assert_detectable_raises_for_a_caller_that_depends_on_the_verdict",
            "test_c11_the_disclosure_is_derived_and_disappears_when_the_collapse_does",
            "test_c11_the_disclosure_names_the_phenomenon_and_the_term_that_took_it",
            "test_c11_it_does_not_claim_the_gap_is_closed",
            "test_c11_both_run_kinds_carry_the_derived_disclosure_in_the_output",
            "test_s4_6_every_result_states_that_the_guard_cannot_fire_on_this_model",
        ),
        notes="Mandated mutation 1. With the intersection emptied, every derived "
        "statement disappears and the guard reports itself healthy.",
    ),
    Mutation(
        name="C11-mutation-2-empty-the-collapses-on-the-frictional-term",
        guards="C11(i): a collapsing term declares what it costs",
        finding="C11",
        path=TWO_PHASE_LOOP,
        old="        ModelTerm(\n            term=\"frictional\",\n            entry_id=DP_ID,\n"
        "            collapses=(",
        new="        ModelTerm(\n            term=\"frictional\",\n            entry_id=DP_ID,\n"
        "            collapses=() and (",
        expect_failing=(
            "test_c11_the_named_terms_declare_a_non_empty_collapse",
            "test_c11_the_frictional_collapse_names_the_quality_profile_and_what_it_costs",
            "test_c11_control_a_term_that_collapses_nothing_says_so",
            "test_c11_the_boundary_reports_the_conflict_naming_guard_term_and_phenomenon",
            "test_c11_the_disclosure_is_derived_and_disappears_when_the_collapse_does",
            "test_s4_6_every_result_states_that_the_guard_cannot_fire_on_this_model",
        ),
        notes="Mandated mutation 2. This is the one that proves the disclosure is "
        "DERIVED: removing the collapse removes the sentence, with no prose edited.",
    ),
    Mutation(
        name="C11-mutation-3-remove-detects-from-the-Ledinegg-guard",
        guards="C11(ii): a guard declares the phenomenon it targets",
        finding="C11",
        path=REGISTRY,
        old='        detects=("negative_slope_segment",),',
        new="        detects=(),",
        expect_failing=(
            "test_c11_the_ledinegg_guard_declares_what_it_detects",
            "test_c11_the_boundary_reports_the_conflict_naming_guard_term_and_phenomenon",
            "test_c11_assert_detectable_raises_for_a_caller_that_depends_on_the_verdict",
            "test_c11_the_disclosure_is_derived_and_disappears_when_the_collapse_does",
            "test_s4_6_every_result_states_that_the_guard_cannot_fire_on_this_model",
        ),
        notes="Mandated mutation 3. The boundary refuses an undeclared target rather "
        "than passing it, so this raises rather than quietly reporting no conflict.",
    ),
    Mutation(
        name="take-the-best-gate-outcome-instead-of-the-worst",
        guards="gate combination (a permissive gate must not outvote a strict one)",
        finding="pre-existing",
        path=TWO_PHASE,
        old="    return max(statuses, key=lambda s: _STATUS_SEVERITY[s])",
        new="    return min(statuses, key=lambda s: _STATUS_SEVERITY[s])",
        expect_failing=(
            "test_gate5_combined_assessment_takes_the_worst_gate_outcome",
            "test_gate5_missing_chf_blocks_the_case_rather_than_assuming_it_is_safe",
        ),
    ),
]


def _assert_mutating_the_imported_package() -> None:
    """Refuse to run if the installed package is not the tree being mutated.

    ``pip install -e .`` in another checkout repoints the global editable install, and
    every mutation then silently becomes a no-op (observed: 0/16 witnessed). This is
    cheap insurance against trusting such a run.
    """
    proc = subprocess.run(
        [sys.executable, "-c", "import orbital_thermal;print(orbital_thermal.__file__)"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    imported = Path(proc.stdout.strip()).resolve().parent
    if imported != SRC.resolve():
        raise SystemExit(
            f"REFUSING TO RUN: mutations target {SRC}, but 'import orbital_thermal' "
            f"resolves to {imported}. Every mutation would be a silent no-op. Fix the "
            "editable install (pip install -e . from this repo) and retry."
        )


def _run_tests() -> tuple[int, set[str]]:
    """Run the S2 test modules; return (exit code, set of failing test names)."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *TEST_MODULES, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    failing: set[str] = set()
    for line in (proc.stdout + proc.stderr).splitlines():
        line = line.strip()
        if line.startswith("FAILED ") or line.startswith("ERROR "):
            body = line.split(" ", 1)[1]
            name = body.split("::")[-1].split(" ")[0].split("[")[0]
            failing.add(name)
    return proc.returncode, failing


def witness(mutation: Mutation) -> Result:
    original = mutation.path.read_text(encoding="utf-8")
    if mutation.old not in original:
        return Result(
            mutation=mutation.name,
            guards=mutation.guards,
            finding=mutation.finding,
            applied=False,
            witnessed=False,
            detail=(
                "anchor text not found -- the source moved and this mutation needs "
                "updating; treated as a failure so the witness cannot silently rot"
            ),
        )
    try:
        mutation.path.write_text(
            original.replace(mutation.old, mutation.new, 1), encoding="utf-8"
        )
        _, failing = _run_tests()
        missing = [t for t in mutation.expect_failing if t not in failing]
        return Result(
            mutation=mutation.name,
            guards=mutation.guards,
            finding=mutation.finding,
            applied=True,
            witnessed=not missing,
            failed_tests=sorted(failing),
            detail=(
                "" if not missing else f"expected these to fail but they passed: {missing}"
            ),
        )
    finally:
        mutation.path.write_text(original, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list mutations and exit")
    parser.add_argument("--json", type=Path, help="write a machine-readable record")
    args = parser.parse_args()

    if args.list:
        for m in MUTATIONS:
            print(f"{m.name}  [{m.finding}]\n    guards: {m.guards}\n    {m.notes}")
        return 0

    _assert_mutating_the_imported_package()

    print(f"Witnessing {len(MUTATIONS)} S2 checks by deliberate mutation.\n")
    results: list[Result] = []
    for i, m in enumerate(MUTATIONS, 1):
        res = witness(m)
        results.append(res)
        mark = "WITNESSED" if res.witnessed else "NOT WITNESSED"
        tag = f"[{m.finding}]" if m.finding else ""
        print(f"[{i:2d}/{len(MUTATIONS)}] {mark:14s} {m.name} {tag}")
        print(f"                        guards: {m.guards}")
        if res.witnessed:
            print(f"                        caught by: {', '.join(res.failed_tests)}")
        else:
            print(f"                        PROBLEM: {res.detail}")
        print()

    ok = sum(r.witnessed for r in results)
    print(f"{ok}/{len(results)} checks witnessed failing on purpose.")

    if args.json:
        args.json.write_text(
            json.dumps([r.__dict__ for r in results], indent=2), encoding="utf-8"
        )
        print(f"record written to {args.json}")

    if ok != len(results):
        print("\nFAIL: a check that cannot fail is not a check.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
