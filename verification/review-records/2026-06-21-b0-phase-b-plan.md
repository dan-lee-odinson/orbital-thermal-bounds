<!--
Copy to review-records/YYYY-MM-DD-<scope>.md for each major milestone,
formal cross-model review, or release. Not required for routine development.
-->
> **Working verification record:** This document may contain incomplete,
> provisional, or unresolved material. Its inclusion in the repository does
> not indicate validation or acceptance of the associated technical claims.
# Review Record: B0 - Phase B, Stage 1 implementation plan
## Record Metadata
- **Record status:** original review + two re-reviews completed; **revision 3 submitted; third
  (confirmation) re-review pending**
- **Date:** 2026-06-21 (updated 2026-07-02)
- **Reviewed commit (original):** `c462840` (`main`)
- **Revision 1:** delivered as a draft and re-reviewed; **not merged** to `main`
  (superseded by Revision 2).
- **Revision 2 commit:** `5740909` (`main`) - reviewed by the second re-review.
- **Revision 3 commit:** `<fill with the chore/b0-revision-3 merge commit hash after push>`
- **Branch:** `chore/b0-revision-3`
- **Reviewer(s):** human director (Dan Lee-Odinson); cross-model reviewer (GPT-5.5 High)
- **Trigger:** major milestone (B0)
- **Disposition (original, retained):** **not ready / changes required**
- **Disposition (re-review 1, retained):** **changes required** - Revision 1 changes cleared,
  two remaining blockers + one required limitation.
- **Disposition (re-review 2, retained):** **changes required** - 2.1 and 2.3 closed, both
  source checks passed; one remaining blocker (C2 loophole) + one major + one minor.
- **Disposition (current):** revision 3 submitted; **B1 remains blocked** until a confirmation
  re-review finds no unresolved blocker.

## Review Basis
The B0 deliverable was reviewed against the Phase B roadmap
(`docs/development/phase-b-roadmap.md`), the verification policy
(`docs/VERIFICATION_AND_VALIDATION.md`), and the agreed B0 scope (design-intent depth,
B1-B4 deep / B5-B8 summarized coverage, core-boundary retrospective ledger set). The cross-
model review was conducted with an explicit adversarial, anti-agreeableness prompt.

## Review Scope
**In scope:** `docs/development/chip_to_radiator_phase_b_plan.md`; the core-boundary ledger
entries and index. **Out of scope:** B1+ implementation; the two not-yet-opened entries;
physical validation of any assumption.

## Commands and Tests Run
Static review only; B0 is a planning document and no Phase B code exists. Two of the cross-
model findings were independently verified by the director's tooling against repository source
(`src/orbital_thermal/mccalip_exact_vf.py` for F9; `src/orbital_thermal/sink.py` for the
shielding contract in F3/F9); both were confirmed correct.

## Findings (original cross-model review, retained verbatim in substance)
1. **[blocker][defect]** The residual system is not mathematically closed (no per-mode
   unknown-equation table; design vs solved vs derived vs optimization variables not
   separated; underdetermined `(A_rad,T_rad)` and `(m_dot,dT)` families; `T_j_max` is an
   inequality). *Location:* plan 4.1, 5.
2. **[blocker][defect]** Absolute loop pressure is missing, so CO2 phase and containment
   cannot be evaluated (only pressure drop is computed; no low-side/fill/accumulator closure).
   *Location:* plan 4.2, 4.6, 5.
3. **[blocker][defect]** The reported orbital boundary is undefined for a steady bifacial
   solve (no averaging statistic; direct-solar omission/shielding not carried; two area bases;
   a single `T_sink_eff` is not valid for two faces). *Location:* plan 3, 4.3, 5, B4; core set.
4. **[major][defect]** Pump power and pump heat lack a consistent control-volume boundary.
   *Location:* plan 4.1, 5, B3, B4.
5. **[major][defect]** The containment model is not a valid general ranking basis (SF
   placement, gauge pressure, `r/t` check, missing axial/endcaps/min-gauge; `P*V*rho/sigma`
   wrongly called dimensionally invalid). *Location:* plan 4.4 criterion 6, 4.6.
6. **[major][limitation]** The six ranking criteria admit incomplete/non-comparable
   architectures (no mass-account completeness/common boundary; no `design variable`
   provenance class). *Location:* plan 4.4, B6.
7. **[major][defect]** The thermal-hydraulic model omits load-bearing heat-transfer and path
   checks (no Nusselt/convection; minor losses; maldistribution; between-station phase; optional
   spreading resistance). *Location:* plan 4.2, 5, B2, B3.
8. **[major][limitation]** Convergence and baseline recovery are necessary but insufficient
   gates (unit-mixing residual norm; missing feasibility/branch checks; ambiguous baseline).
   *Location:* plan 5, B4.
9. **[major][documentation]** The `earth-view-factors` entry has a false comparator (`0.25`
   vs the actual ~0.021 heuristic floor vs ~0.258 exact); the core set omits the attitude/
   shielding contract. *Location:* `earth-view-factors.md`; plan 3; `emitting-face-convention.md`.

**Original disposition: not ready.** B1 should not begin from the original design intent.

## Finding-Response Matrix (revision 1)
Disposition key: **fixed** (contract changed) | **accepted limitation** (scoped, documented) |
**deferred with consequence** (postponed, impact stated). Documentation-only closure was not
used where a changed physical/mathematical contract was required.

| # | Sev | Disposition | Specific revision | Changed location |
|---|---|---|---|---|
| 1 | blocker | **fixed** | Added variable-role taxonomy and four **square** solve modes (T/A/S/O) with a per-mode fixed/solved/closing-equation table; design variables close the underdetermined families; `T_j_max` closes the system only as an active equality in sizing mode. | plan 4.1, 5 |
| 2 | blocker | **fixed** (pressure contract) + **deferred with consequence** (CO2 ranked use) | Added absolute-pressure states + `P_lo` low-side contract and an accumulator/fill closure (accumulator deferred-with-consequence); per-segment phase checks on absolute `(T,P)`; **CO2 demoted to sensitivity-only** until a compressible/near-critical treatment exists. | plan 4.2, 4.3, 5 |
| 3 | blocker | **fixed** | Canonical orbital balance: per-face Earth-IR/albedo on per-face view factors; radiatively-weighted orbit-mean sink as the steady statistic (worst-case as sensitivity); explicit attitude/sun-shielding contract; per-face summation replaces a single `T_sink_eff`; area-basis conversion fixed. New ledger entry added. | plan 4.4; `radiator-attitude-and-sun-shielding.md` |
| 4 | major | **fixed** | Pump-energy control-volume contract (`P_elec`->motor->shaft->hydraulic; deposition fraction `f`); whole-spacecraft vs fluid-loop boundary stated; radiator balance uses the boundary-consistent total. | plan 4.7, 5 |
| 5 | major | **fixed** | Gauge pressure; SF applied once; `r/t>=10` thin-wall gate with Lame thick-wall fallback; axial/endcaps/min-gauge/transient allowance or ideal-lower-bound label; acknowledged `P*V*rho/sigma` as a valid equivalent scaling. | plan 4.6 |
| 6 | major | **fixed** | Expanded ranking gates (common boundary, mass-account completeness, correlation-domain, common envelope); mass-accounting boundary list; objective renamed "modeled component mass" if closures missing; added **design-variable** provenance class. | plan 2, 4.8, 4.8a |
| 7 | major | **fixed** (requirement set; implemented in B1-B3) | Thermal + hydraulic correlation registry (Nusselt + friction + minor losses + maldistribution + segmented energy balance + per-segment phase); spreading resistance **mandatory** for ranked cases; PGW mass/volume basis fixed. | plan 6, B1-B3 |
| 8 | major | **fixed** | Nondimensional residual scaling; post-convergence feasibility-inequality suite; branch/multi-start checks; **two-direction** baseline recovery (Mode T and Mode A). | plan 5, B4 |
| 9 | major | **fixed** | Corrected `earth-view-factors` comparator (~0.021 heuristic floor vs ~0.258 exact, ~12x, +6.35 K) with a transparency note; added `radiator-attitude-and-sun-shielding`; added equal-sink condition to `emitting-face-convention`. | `earth-view-factors.md`, `radiator-attitude-and-sun-shielding.md`, `emitting-face-convention.md`, plan 3 |

## Re-review 1 findings (retained) and Revision 2 response
The cross-model re-review of Revision 1 confirmed the Revision 1 changes materially improved
the plan and cleared the original nine findings, but raised **two remaining blockers** and
**one required limitation** before B1 authorization:

- **RR-2.1 [blocker]** square-system closure was *asserted, not demonstrated* (no node
  topology, no per-unknown equation map, no rank/independence count, no heat-injection-node
  treatment).
- **RR-2.2 [blocker]** the bifacial direct-solar treatment was incomplete (cold face shielded,
  but the other face and the missing-`alpha_s` case were unspecified).
- **RR-2.3 [limitation]** until accumulator/thermal-expansion mass is closed, the objective
  must remain "modeled component mass," and Section 4.8a should state that consequence.

**Re-review 1 disposition: changes required** (retained above).

| RR # | Sev | Disposition | Specific revision | Changed location |
|---|---|---|---|---|
| 2.1 | blocker | **fixed** | Added the node-and-equation determinacy contract: canonical node topology, a per-mode (T/A/S) 5x5 state/residual table, a lower-triangular rank/independence argument, declared degeneracies as failure states, and the explicit heat-injection-node rule (`Q_chip` through the junction chain; `Q_pump` into the fluid). | plan 4.1a |
| 2.2 | blocker | **fixed** | Added a per-case all-face direct-solar contract with three options (C1 fully-shielded bifacial / C2 single cold-face / C3 explicit sunlit-face); C3 needs the deferred direct-solar term; missing `alpha_s` forces a parametric case, never an assumed ranked value; the chosen contract is a ranking-gate input. | plan 4.4a |
| 2.3 | limitation | **stated (accepted)** | Section 4.8a now states the consequence explicitly: the Stage-1 prescribed-pressure default defers accumulator/thermal-expansion mass, so the objective stays "modeled component mass" and must not be reported as total thermal-system mass until those closures exist. | plan 4.8a |

## Re-review 2 findings (retained) and Revision 3 response
The second cross-model re-review (of Revision 2, commit `5740909`) confirmed **2.1 closed**
(solve modes T/A/S are square; pump heat correctly routed to the fluid) and **2.3 closed**, and
independently **verified both source checks**: the corrected `earth-view-factors` comparator
matches `mccalip_exact_vf.py` (~0.021 vs ~0.258, +6.35 K), and the attitude entry matches
`sink.py`. It left one blocker + one major + one minor:

- **RR2-1 [blocker]** C2 could let a **sunlit, thermally coupled backside** be excluded from
  *both* the emitting-area credit and the absorbed-solar load, underpredicting radiator
  temperature/area and bypassing the missing-`alpha_s` rule.
- **RR2-2 [major]** Section 5 residual 1 kept a collapsed `T_j - T_rad = Q_path * R_total` that
  conflicts with the per-node routing in 4.1a.
- **RR2-3 [minor]** C1 wording conflated the `2 A_plan` area-bookkeeping convention with the
  equal-sink simplification.

**Re-review 2 disposition: changes required** (retained above).

| RR2 # | Sev | Disposition | Specific revision | Changed location |
|---|---|---|---|---|
| 1 | blocker | **fixed** | C2 is rank-eligible only if the excluded face is outside the thermal control volume (insulated / isolated / shielded / demonstrated no direct-solar deposition). A sunlit, thermally coupled face forces C3 (sourced or parametric `alpha_s`) or a rejected/parametric case; missing `alpha_s` blocks ranking even when the face is not credited as emitting area. | plan 4.4a (C2) |
| 2 | major | **fixed** | Section 5 residual 1 now defers to the 4.1a per-node R1-R5 and states per-segment heat rates: chip-side resistances carry `Q_chip`; radiator-side rejection carries `Q_rad = Q_compute + Q_pump_boundary + Q_other`; pump heat is never routed through chip-side resistances. | plan 5 (residual 1) |
| 3 | minor | **fixed** | C1 clarifies `A_emit = 2 A_plan` as a total-emitting-area bookkeeping convention; equal per-face sinks are required only to collapse both faces into one shared effective-sink law, else per-face summation. Mirrored in the `emitting-face-convention` entry. | plan 4.4a (C1); `emitting-face-convention.md` |

## Unresolved Questions
Carried to the **third (confirmation) re-review**: whether the tightened C2 (4.4a) fully closes
the sunlit-coupled-backside loophole without creating a new inconsistency, and whether the
Section 5 -> 4.1a reference is now unambiguous. CO2 ranked use and the accumulator/total-mass
closure remain deferred with consequence.

## Resulting Changes
Revision 2 (commit `5740909`) landed all Revision 1 changes plus the first-re-review closures
(4.1a, 4.4a, 4.8a). Revision 3 (on `chore/b0-revision-3`) closes the second-re-review blocker
and its two lower-severity findings: C2 tightened (4.4a), Section 5 residual 1 deferred to 4.1a,
C1 wording clarified (4.4a and `emitting-face-convention.md`).

## Follow-Up
- **Owner:** human director
- **Required action:** submit Revision 3 for a **short confirmation re-review** (scoped to the
  C2 closure and the two lower-severity fixes); on a clean re-review, set the Revision 3 commit
  hash and mark the final disposition **B0 approved**.
- **Re-review required:** yes (third, confirmation)
- **Target milestone:** B0 approval (gates the start of B1)

## Verification Limitations
- This is a planning document; no Phase B physical assumption has been validated.
- Static review only; no Phase B code was executed (none exists). Dispositions marked "fixed"
  change the **design-intent contract**; the corresponding implementations are verified in
  B1-B4, not here.
- Ledger entries at `reproduced` reflect executable evidence only; director-authored
  explanations and independent derivations remain `TODO`.
- Two cross-model findings (F9; the F3/F9 shielding contract) were verified against source;
  the remaining findings were accepted on their reasoning and addressed by contract change.
