"""Witness that every S2 check can actually fail (Stage 2, milestone S2).

A checker is a callable that *can* fail; a check that has never failed is not a
check. This script proves each new S2 gate is load-bearing by deliberately breaking
the thing it guards -- one mutation at a time -- and requiring the mapped tests to
fail. A mutation that leaves the suite green is itself a failure: it means the gate
does not actually constrain the behaviour it claims to.

Each mutation is a literal source substitution, applied to a working copy, verified
to have changed the file, exercised, and then reverted. Files are restored in a
``finally`` block, so an interrupted run does not leave the tree dirty.

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
TESTS = REPO / "tests"

REGISTRY = SRC / "registry" / "two_phase.py"
TWO_PHASE = SRC / "two_phase.py"
FLUIDS = SRC / "fluids.py"

EVAP_TESTS = "tests/test_two_phase_evaporator.py"
REG_TESTS = "tests/test_two_phase_registry.py"


@dataclass(frozen=True)
class Mutation:
    """One deliberate break, and the tests that must notice it."""

    name: str
    guards: str
    path: Path
    old: str
    new: str
    expect_failing: tuple[str, ...]
    notes: str = ""


@dataclass
class Result:
    mutation: str
    guards: str
    applied: bool
    witnessed: bool
    failed_tests: list[str] = field(default_factory=list)
    detail: str = ""


MUTATIONS: list[Mutation] = [
    Mutation(
        name="implement-an-unsourced-CHF-entry",
        guards="the exact-set evaluate guard and the locator<->evaluate invariant",
        path=REGISTRY,
        old='        source=_SHAH_2015,\n        evaluate=None,',
        new='        source=_SHAH_2015,\n        evaluate=gungor_winterton_1986_htc,',
        expect_failing=(
            "test_exactly_the_s2_implemented_ids_carry_an_evaluate_callable",
            "test_s2_unimplemented_entries_are_still_none",
            "test_implemented_correlations_have_a_nonempty_locator",
        ),
        notes="Simulates attaching maths to an entry whose source was never established.",
    ),
    Mutation(
        name="implement-an-S3-pressure-drop-entry-early",
        guards="the S3 scope guard",
        path=REGISTRY,
        old='        source=_LOCKHART_MARTINELLI,\n        evaluate=None,',
        new='        source=_LOCKHART_MARTINELLI,\n        evaluate=gungor_winterton_1986_htc,',
        expect_failing=(
            "test_s3_pressure_drop_entries_are_not_implemented_early",
            "test_exactly_the_s2_implemented_ids_carry_an_evaluate_callable",
        ),
        notes="S3 / OTB-G002 work must not leak into this build.",
    ),
    Mutation(
        name="blank-the-locator-of-an-implemented-correlation",
        guards="the locator<->evaluate invariant (Sec. 3.2b)",
        path=REGISTRY,
        old='    locator=(\n        "executable form transcribed from Thome',
        new='    locator="" and (\n        "executable form transcribed from Thome',
        expect_failing=("test_implemented_correlations_have_a_nonempty_locator",),
        notes="An implemented correlation must record the source actually consulted.",
    ),
    Mutation(
        name="drop-the-provisional-domain-declaration",
        guards="the provisional-domain declaration",
        path=REGISTRY,
        old='    "two_phase.htc.gungor_winterton": (\n        "S2: the declared',
        new='    "_disabled.htc.gungor_winterton": (\n        "S2: the declared',
        expect_failing=("test_provisional_domains_are_declared_not_promoted",),
        notes="An unconfirmed domain must stay declared provisional, not quietly promoted.",
    ),
    Mutation(
        name="pretend-ammonia-is-in-the-GW86-database",
        guards="the fluid-database applicability flag",
        path=REGISTRY,
        old='{"water", "r-11", "r-12", "r-22", "r-113", "r-114", "ethylene glycol"}',
        new='{"water", "ammonia", "r-11", "r-12", "r-22", "r-113", "r-114", "ethylene glycol"}',
        expect_failing=("test_ammonia_is_not_in_the_gw86_fluid_database",),
        notes="The reference coolant really is outside the reference HTC's fluid basis.",
    ),
    Mutation(
        name="clamp-vapour-quality-instead-of-enforcing-it",
        guards="the 0 <= x <= 1 enforcement (gate 3)",
        path=TWO_PHASE,
        old="    if not (0.0 <= x <= 1.0):\n        raise ValueError(",
        new="    if False:\n        raise ValueError(",
        expect_failing=("test_gate3_quality_outside_zero_one_is_rejected",),
        notes="Clamping would silently turn a subcooled state into a saturated one.",
    ),
    Mutation(
        name="collapse-subcooled-into-saturated",
        guards="regime classification and the ONB gate (gate 1a/1b, gate 3)",
        path=TWO_PHASE,
        old="    if x_eq < 0.0:\n        regime, x = Regime.SUBCOOLED_LIQUID, None",
        new="    if False:\n        regime, x = Regime.SUBCOOLED_LIQUID, None",
        expect_failing=(
            "test_gate1a_subcooled_forced_convection_is_not_rank_eligible",
            "test_gate1b_onb_transition_is_resolved_and_de_ranks_the_subcooled_side",
            "test_gate3_loop_state_classifies_instead_of_clamping",
        ),
        notes="The ONB gate depends on the subcooled side staying distinguishable.",
    ),
    Mutation(
        name="widen-the-HTC-validity-domain-to-nothing",
        guards="the correlation range checks (gate 4)",
        path=REGISTRY,
        old='                "G_kg_m2s": (10.0, 600.0),',
        new='                "G_kg_m2s": (0.0, 1.0e12),',
        expect_failing=(
            "test_gate4_assert_in_domain_fires_on_every_axis",
            "test_gate4_out_of_domain_htc_call_is_rejected_not_extrapolated",
        ),
        notes="Proves the declared domain is what makes out-of-range calls raise.",
    ),
    Mutation(
        name="move-the-CHF-rank-band-from-0.5-to-0.9",
        guards="director ruling 9.5 CHF bands (gate 5)",
        path=TWO_PHASE,
        old="CHF_RANK_MAX = 0.5",
        new="CHF_RANK_MAX = 0.9",
        expect_failing=(
            "test_gate5_chf_band_between_half_and_one_is_sensitivity_not_ranked",
            "test_gate5_band_boundaries_are_closed_on_the_conservative_side",
        ),
        notes="The 0.5 margin is a director ruling, not a tunable.",
    ),
    Mutation(
        name="let-an-averaged-flux-rank",
        guards="the local-flux discipline (gate 5, T6)",
        path=TWO_PHASE,
        old="    if not wall_flux.is_rankable_basis:\n        return ChfAssessment(",
        new="    if False:\n        return ChfAssessment(",
        expect_failing=(
            "test_gate5_underivable_local_flux_is_never_silently_averaged",
            "test_gate5_unsourced_geometry_de_ranks_a_local_flux",
        ),
        notes="A section- or chip-average must never be substituted for a local flux.",
    ),
    Mutation(
        name="assume-a-missing-CHF-is-safe",
        guards="the blocked-on-missing-CHF rule (gate 5)",
        path=TWO_PHASE,
        old="        status = _worst(status, RankStatus.BLOCKED)",
        new="        status = _worst(status, RankStatus.RANK_ELIGIBLE)",
        expect_failing=(
            "test_gate5_missing_chf_blocks_the_case_rather_than_assuming_it_is_safe",
        ),
        notes="Absent CHF evidence must block, not pass.",
    ),
    Mutation(
        name="return-an-invented-CHF-value",
        guards="the no-invention blocker at the point of use",
        path=TWO_PHASE,
        old="    entry = get(CHF_ID)\n    raise NotRankEligibleError(",
        new="    return 1.0e6\n    entry = get(CHF_ID)\n    raise NotRankEligibleError(",
        expect_failing=("test_gate4_no_sourced_chf_evaluator_exists",),
        notes="The single most dangerous failure mode: a plausible number from nowhere.",
    ),
    Mutation(
        name="silently-correct-the-published-Cooper-constant",
        guards="fidelity to the printed source constant",
        path=REGISTRY,
        old="* (-0.4343 * math.log(p_reduced)) ** -0.55",
        new="* (-math.log10(p_reduced)) ** -0.55",
        expect_failing=(
            "test_cooper_term_matches_the_independently_cross_checked_source",
        ),
        notes="0.4343 is what both sources print; 1/ln(10) would be a silent edit.",
    ),
    Mutation(
        name="drop-the-critical-point-guard",
        guards="no blanket supercritical treatment (gate 3)",
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
        notes="Closes the ~4 mK window the declared water domain admits above T_crit.",
    ),
    Mutation(
        name="disable-the-convective-enhancement-factor",
        guards="the flow-boiling physics and the x->0 recovery (gate 1c/1d)",
        path=REGISTRY,
        old="    e_factor = 1.0 + 24000.0 * bo**1.16 + conv_term",
        new="    e_factor = 1.0",
        expect_failing=(
            "test_gw86_htc_increases_with_quality_and_with_mass_flux",
            "test_gate1c_saturated_flow_boiling_is_evaluated_and_rank_eligible",
        ),
        notes="E carries the convective enhancement; without it boiling stops enhancing.",
    ),
    Mutation(
        name="take-the-best-gate-outcome-instead-of-the-worst",
        guards="gate combination (a permissive gate must not outvote a strict one)",
        path=TWO_PHASE,
        old="    return max(statuses, key=lambda s: _STATUS_SEVERITY[s])",
        new="    return min(statuses, key=lambda s: _STATUS_SEVERITY[s])",
        expect_failing=(
            "test_gate5_combined_assessment_takes_the_worst_gate_outcome",
            "test_gate5_missing_chf_blocks_the_case_rather_than_assuming_it_is_safe",
        ),
        notes="Rejection must survive combination with a passing gate.",
    ),
]


def _run_tests() -> tuple[int, set[str]]:
    """Run the two S2 test modules; return (exit code, set of failing test names)."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", EVAP_TESTS, REG_TESTS, "-q", "--no-header",
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
            print(f"{m.name}\n    guards: {m.guards}\n    {m.notes}")
        return 0

    print(f"Witnessing {len(MUTATIONS)} S2 checks by deliberate mutation.\n")
    results: list[Result] = []
    for i, m in enumerate(MUTATIONS, 1):
        res = witness(m)
        results.append(res)
        mark = "WITNESSED" if res.witnessed else "NOT WITNESSED"
        print(f"[{i:2d}/{len(MUTATIONS)}] {mark:14s} {m.name}")
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
