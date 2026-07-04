<!-- Major-milestone review record (B6). OPEN until the cross-model review is dispositioned. -->
> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Review Record: B6 - Trade-study engine

## Record Metadata
- **Record status:** **OPEN - revision delivered; re-review pending.** The adversarial review
  returned 0 blockers + 4 major + 4 minor findings (F1-F8); **all eight were fixed** and the
  code + data revised. Awaiting the confirmation re-review.
- **Date opened:** 2026-07-04
- **Reviewed commit (original):** `385d2b1` (`chore/b6-trade-study`)
- **Revision commit:** *(to be recorded when the F1-F8 revision is pushed)*
- **Reviewer(s):** human director (Dan Lee-Odinson); cross-model reviewer (GPT-5.5 High)
- **Trigger:** major milestone (B6)
- **Disposition (original):** **changes required** - 4 major (F1-F4/F5) + 4 minor; no blocker.
- **Disposition (revision):** all 8 findings **fixed**; **re-review requested** before B6 is
  treated as complete and before B7.

## Review Basis
B6 is reviewed against the roadmap B6 entry, the plan Section 8 (B6) and 4.8/4.8a, and the
verification policy. The engine is verified at level c (executable); its physical conclusions
inherit a/b/sensitivity from B1-B5 and are **not** newly validated. Figures are deferred to B7.

## Review Scope
**In scope:** `src/orbital_thermal/trade_study.py`; `tests/test_trade_study.py`;
`scripts/generate_trade_study.py`; `docs/trade-study.md` + generated `trade-study-data.md` /
`trade-study-points.csv`; and the **B4 fix** (`coupled_model.py` multi-start:
reduced-temperature cap + subcooled-liquid filter) with its regression test.
**Directed scope decisions:** sweep Q/m_dot/area/P_lo only; junction limit is a filter; all six
fronts as data; figures -> B7; modeled component mass only (no total-system claim).
**Out of scope:** B7 figures; denser sweeps; independent re-validation of B1-B5 physics.

## Implementation summary (what the reviewer is auditing)
- Grid enumeration + per-point evaluation via B5 `evaluate_case` (physics inherits B1-B5).
- Feasible/infeasible classification with reason codes; `T_j <= T_j_max` as a filter.
- Pareto-dominance construction per trade (declared axis senses); degenerate/empty fronts
  emitted explicitly; per-point category, reason codes, active constraint, dominance flags.
- Modeled component mass only (4.8a); no total-system mass; only rank-eligible cases swept.
- **B4 multi-start fix** (reduced-temperature cap `Tr<=0.97`; subcooled-liquid alt-root filter).

## Commands and Tests Run (self-verification, pre-review)
```
ruff check src/ tests/                        # clean
pytest -q                                     # 541 passed, 3 xfailed
pytest tests/test_trade_study.py -q           # 16 passed
pytest tests/test_coupled_model.py -q         # 41 passed (+ near-critical branch regression)
pytest --cov=orbital_thermal --cov-fail-under=90   # total 95.8%; trade_study.py 98%
verify_suite.py / verify_paper3.py / companion/verify_ai1.py   # all pass
python scripts/generate_trade_study.py        # 144 points; 6 fronts, 0 degenerate
```

## Suggested adversarial focus for the cross-model reviewer
1. Is the Pareto-dominance relation correct for every trade's declared axis sense, and are
   non-dominated members computed correctly (no dominated point on a front, none omitted)?
2. Are feasible/infeasible classification and reason codes faithful, and is `T_j <= T_j_max`
   genuinely a filter (infeasible points reported, never dropped)?
3. Is the mass strictly "modeled component mass (incomplete)"? Any hidden total-system claim?
4. Are only rank-eligible cases swept, and are sensitivity/rejected points kept out of fronts?
5. Is the **B4 fix** correct and safe -- does the subcooled-liquid filter ever suppress a *real*
   feasible second root, and is `Tr<=0.97` defensible? Does it weaken B4's F5 branch check?
6. Are degenerate/empty fronts handled honestly, and is "no universal winner" actually supported
   by the data (not asserted)?
7. Is the 22/144 nonconvergence rate acceptable, and are those points correctly excluded from
   ranking?

## Findings (adversarial review, retained) and disposition

No blocker. Core Pareto logic and the mass boundary **passed**. All eight findings are **fixed**.

1. **[major][defect] F1 - feasibility reason codes lossy (message-parsed, one reason).**
   **FIXED:** `FeasibilityError` now carries structured `failed_gates`; `architecture_cases`
   maps **every** failed gate to a reason (deduped) via `_GATE_REASON` (no message parsing);
   B6 emits all mapped reason codes. Test: a junction+subcooling failure reports both reasons.
2. **[major][risk] F2 - `Tr <= 0.97` cap not justified as a safe branch filter.**
   **FIXED:** removed the arbitrary cap; the domain guard is now the clean supercritical check
   (`mean >= Tcrit`, a phase-envelope violation), and near-critical alternate roots are handled
   by the **subcooled-liquid filter** (an alt root is a branch only if it is itself a subcooled
   single-phase liquid at the operating pressure). Documented in `coupled-model.md` /
   `trade-study.md`. B4 tests pass (41, incl. the near-critical regression).
3. **[major][defect] F3 - dominance flags/reasons computed but not exported.**
   **FIXED:** the CSV now exports `pareto_front_membership` and `dominated_reasons`
   (front=dominated_on_axis) per point. Test asserts the fields and a known dominated reason.
4. **[major][risk] F4 - "no universal winner" overclaimed.**
   **FIXED:** narrowed to the supported claim -- *no single case is Pareto-optimal on every
   named front* (max 4 of 6; membership across all 4 cases); the generated page states it is
   not a global aggregate-ranking claim. Test asserts `max fronts-per-case < len(TRADES)`.
5. **[major][limitation] F5 - 22/144 nonconvergence under-diagnosed.**
   **FIXED:** a distinct `NONCONVERGED` category (separate from gate-rejection); a
   nonconvergence diagnostic table (case + grid coordinates) in the generated data; and an
   explicit statement that nonconvergence is **not** evidence of physical infeasibility. Test
   asserts the category invariant.
6. **[minor][documentation] F6 - front members not uniquely identified.**
   **FIXED:** stable `point_id` (`case|Q|mdot|A|Plo`); exported in the CSV and shown in the
   generated front tables; `ParetoFront` carries `member_point_ids`. Test: point_ids unique.
7. **[minor][sensitivity] F7 - pressure front maximizes pressure without proving benefit.**
   **FIXED:** `min_subcooling_Pa` is now an exposed objective; the front's dominating-assumption
   and docs state pressure is a **design-capability proxy** for phase margin, not an intrinsic
   benefit. (Axis kept as pressure to match the roadmap's named front.)
8. **[minor][test gap] F8 - fronts not checked against an independent oracle.**
   **FIXED:** an oracle test recomputes each of the six fronts with a naive local dominance and
   asserts engine membership == oracle (no dominated member; none omitted).

## Post-revision self-verification
```
ruff check src/ tests/ scripts/                    # clean
pytest -q                                          # 546 passed, 3 xfailed
pytest tests/test_trade_study.py -q                # 20 passed (incl. oracle)
pytest tests/test_coupled_model.py -q              # 41 passed
pytest --cov=orbital_thermal --cov-fail-under=90   # total 96.0%; trade_study.py 98%
verify_suite.py / verify_paper3.py / companion/verify_ai1.py   # all pass
python scripts/generate_trade_study.py             # 144 points; 6 fronts, 0 degenerate
```

## Disposition
**Revision delivered; all 8 findings fixed. Re-review requested.** Reviewed commit `385d2b1`;
the revision commit will be recorded when pushed. B6 is not treated as closed until the
confirmation re-review clears the revision.
