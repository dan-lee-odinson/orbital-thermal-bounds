<!--
Major-milestone review record (B4). OPEN until the cross-model review is conducted and its
findings are dispositioned.
-->
> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Review Record: B4 - Coupled steady-state radiator model

## Record Metadata
- **Record status:** **CLOSED - B4 approved.** The initial adversarial review returned 1
  blocker + 7 findings (F1-F8); all were fixed, and the **confirmation re-review closed all
  eight**. One new minor item (N1) was raised in the re-review and also fixed. No open items.
- **Date opened:** 2026-07-03
- **Reviewed commit (original):** `ca08e69` (`chore/b4-coupled-model`)
- **Revision commit (F1-F8):** `6f22fbf` (`chore/b4-coupled-model`)
- **Final revision (N1 closure):** follow-up commit on the same branch (PR #36 head; the
  squash-merge commit is the closing record on `main`)
- **Reviewer(s):** human director (Dan Lee-Odinson); cross-model reviewer (GPT-5.5 High)
- **Trigger:** major milestone (B4)
- **Disposition (original):** **changes required** - 1 blocker (F1) + 6 major (F2-F7) + 1
  minor (F8).
- **Disposition (revision):** all 8 findings **fixed**.
- **Disposition (confirmation re-review):** **F1-F8 all CLOSED**; one new minor item (N1)
  raised and **fixed**. **B4 APPROVED - B5 may proceed.**

## Review Basis
B4 is reviewed against the B0 plan (`docs/development/chip_to_radiator_phase_b_plan.md`,
Sections 4.1/4.1a, 4.4a, 4.7, 5, and the B4 block), the Phase B roadmap, and the verification
policy (`docs/VERIFICATION_AND_VALIDATION.md`). The cross-model review is to be conducted with
an explicit adversarial, anti-agreeableness prompt.

## Review Scope
**In scope:** `src/orbital_thermal/coupled_model.py`; `tests/test_coupled_model.py`;
`docs/coupled-model.md`; the `coupled-steady-state-solution` ledger entry.
**Directed scope decisions (for the reviewer's awareness):** Modes **T and A only** (Mode S ->
B6); **mass/containment deferred to B5**; **C3 kept deferred** (C1/C2 rank-eligible with the
inherited shielded sink; C3 parametric-only; `sink.py` untouched).
**Out of scope:** B5+ implementation; physical validation of any assumption; the deferred
Mode S / mass / C3 items.

## Implementation summary (what the reviewer is auditing)
- R1-R5 residual system (4.1a); `Q_chip` through R1/R2 only, pump heat into R3,
  `Q_rad = Q_chip + Q_pump_fluid` (4.7).
- Lower-triangular solve R5->R4->R3->R2->R1; pump-heat/property fixed point in loop mean
  temperature and pressure, **guarded to the single-phase-liquid domain** (supercritical
  excursion rejected).
- Radiator law closed form (linear in `T_rad^4`), per-face (C1/C2); Mode T solves `T_rad`,
  Mode A solves `A_rad`.
- Nondimensional convergence + energy closure; feasibility-gate suite (ranked-infeasible
  rejected, sensitivity flagged); failure states raise; multi-start branch check.

## Commands and Tests Run (self-verification, pre-review)
```
ruff check src/ tests/                      # clean
pytest -q                                   # 496 passed, 3 xfailed
pytest tests/test_coupled_model.py -q       # 32 passed
pytest --cov=orbital_thermal --cov-fail-under=90   # total 95.4%; coupled_model.py 97%
python verify_suite.py / verify_paper3.py / companion/verify_ai1.py   # all pass (Phase A intact)
```
- **Two-direction baseline recovery** (Mode T -> Phase A `T_rad`; Mode A -> Phase A area):
  exact to ~1e-9.
- **Energy closure** and **nondimensional residual**: ~1e-15 at the solution.

## Suggested adversarial focus for the cross-model reviewer
1. Is the R1-R5 mapping to code faithful (heat-injection rule; `Q_chip` never through the
   fluid; pump heat never through the chip-side resistances)?
2. Is the lower-triangular solve + fixed point a correct realization of the 4.1a determinacy
   claim, and is the convergence criterion genuinely nondimensional (5, F8)?
3. Are the feasibility gates complete and correctly gating (ranked-reject vs sensitivity-flag)?
4. Is the single-phase-liquid domain guard the right treatment of the supercritical branch,
   and does multi-start actually establish uniqueness of the physical root?
5. Is the C1/C2/C3 handling faithful to 4.4a (C3 parametric-only; missing `alpha_s` blocks
   ranking), given `sink.py` is untouched?
6. Does the fluid-loop pump-energy boundary (4.7) close consistently, and is the
   whole-spacecraft accounting correctly left to B5/B6?

## Findings (initial cross-model review, retained) and disposition

All eight findings are **fixed** in the revision. Location lines refer to the revised
`coupled_model.py`.

1. **[blocker][defect] F1 - C2 rank-eligibility did not require excluded-face evidence.** §4.4a
   makes C2 rank-eligible only if the excluded face is outside the thermal control volume; the
   code only checked "one face", reopening the B0 Rev-3 loophole. **FIXED:** `RadiatorSpec`
   gains `excluded_face_outside_thermal_cv` + `excluded_face_basis`; `rank_eligible` is False
   for C2 without both; `assert_case_rank_eligible` raises a C2-specific `NotRankEligibleError`.
   Tests: `test_c2_without_evidence_raises`, `test_rank_eligibility_by_contract`.
2. **[major][defect] F2 - C3 accepted a solar flux but ignored it in the radiator balance.**
   **FIXED (deferred per scope):** `solve_coupled` now **rejects** any C3 case (`CoupledError`)
   -- C3 is not solved with the direct-solar term silently omitted. Test: `test_c3_solve_is_rejected`.
3. **[major][defect] F3 - `whole_spacecraft` boundary accepted but not applied to `Q_rad`.**
   **FIXED:** `solve_coupled` accepts only `boundary="fluid_loop"`; the whole-spacecraft
   roll-up is deferred to B5 accounting. Test: `test_whole_spacecraft_boundary_rejected`.
4. **[major][risk] F4 - `converged=True` meant "fixed point stopped", not residual converged.**
   **FIXED:** added `residual_tol`; `converged = residual_converged AND energy_closed`; exposed
   `fixed_point_converged` separately. Test: `test_converged_reflects_residual_not_just_fixed_point`.
5. **[major][risk] F5 - multi-start did not establish uniqueness; skipped failed seeds.**
   **FIXED:** alt-seed outcomes are classified -- same root / classified domain-exit / else a
   `BranchError`; the docs claim is downgraded to a *local branch smoke check* with the
   lower-triangular structure as the uniqueness basis.
6. **[major][risk] F6 - single-phase guard was lumped, not per-station/segment.** **FIXED
   (labelled):** worst-case station margins (hottest `T2`, minimum `P_lo`) are computed via
   `fluids.single_phase_liquid_margins` and exposed (`min_subcooling_Pa`, `min_freeze_margin_K`,
   `min_critical_margin_K`); docs label it a lumped conservative screen with the per-segment
   march (B3) noted. Test: `test_min_margin_fields_exposed`.
7. **[major][defect] F7 - ranked cases could use transitional friction (3000<=Re<4000).**
   **FIXED:** the ranked Reynolds gate now requires `Re <= 2300 or Re >= 4000` (the friction
   turbulent cutoff), not the Nusselt cutoff 3000. Test: `test_transitional_reynolds_rejected_when_ranked`.
8. **[minor][robustness] F8 - `RadiatorSpec` did not coerce the contract enum.** **FIXED:**
   `object.__setattr__(self, "contract", Contract(self.contract))` in `__post_init__`. Test:
   `test_string_contract_is_coerced_and_checked`.

## Post-revision self-verification
```
ruff check src/ tests/                       # clean
pytest -q                                    # 505 passed, 3 xfailed
pytest tests/test_coupled_model.py -q        # 39 passed
pytest --cov=orbital_thermal --cov-fail-under=90   # total 95.7%; coupled_model.py 97%
verify_suite.py / verify_paper3.py / companion/verify_ai1.py   # all pass
```

### Confirmation re-review (retained) and new item

The confirmation re-review **closed F1-F8** against the requested closure criteria and raised
one new minor item:

9. **[minor][API hardening] N1 - the standalone radiator-law helpers accepted a C3 spec and
   ignored its solar flux.** `solve_coupled` already rejects C3, so no coupled result omitted
   direct solar; but `radiator_temperature` / `radiator_area` / `_radiator_rejection` could
   silently compute a C3 spec if called directly. **FIXED:** added `_reject_c3_radiator_law`
   (per the reviewer's suggested guard), called at the top of all three helpers. Test:
   `test_c3_spec_rejected_by_radiator_law_helpers`. Test count 39 -> 40; suite 506 passed.

## Disposition
**B4 APPROVED.** Original review: 1 blocker + 7 findings; confirmation re-review: **F1-F8
CLOSED**; new minor N1 **fixed**. No open items. Reviewed commit `ca08e69`; F1-F8 revision
`6f22fbf`; N1 closed in the follow-up branch head (squash-merge lands the closing commit on
`main`). **B5 may proceed.**
