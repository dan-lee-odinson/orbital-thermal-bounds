<!-- Stage-2 review record (S2, two-phase acquisition / evaporator). Intermediate milestone.
     OPEN pending director disposition + Sol cross-model review. No cross-model review is
     mandatory at S2 (deferred to the S4/S6 majors), but two findings below need a director
     ruling before S3 proceeds. -->
> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Review Record: S2 — two-phase acquisition / evaporator

## Record Metadata
- **Record status:** **OPEN** — awaiting director disposition of findings F1/F2 and Sol's
  cross-model review. Not closable by the builder.
- **Date:** 2026-07-25
- **Reviewed commit:** S2 build commits on branch `stage-2/s2-evaporator` (base `155b10c`).
- **Reviewer(s):** pending — **project director (Dan Lee-Odinson)** + cross-model (Sol).
  Cross-model review is category **c**, never level **d**.
- **Trigger:** Stage-2 milestone S2 (OTB-G001); METHOD v1.0, Tier 2.
- **Disposition:** **pending director review.** `main` untouched; no tag, no release.

## Scope

Screening-level two-phase acquisition, per S0 §8's S2 row. Vapour quality and loop state,
the flow-boiling HTC, the ONB/saturated-regime policy, the CHF/dryout bands on **local**
wall flux, and the local-flux basis discipline. **No coupled solve, no pressure drop, no
condenser, no NPSH, no architecture cases, no trade study, no Suncatcher comparison.**

**No Phase A or Stage-1 published number changed.** Regression baseline `v1.1.0`;
oracle-freeze intact.

## What S2 added

- `src/orbital_thermal/fluids.py` — the S2 saturation backend: `saturation_temperature`,
  `saturation_enthalpies`, `surface_tension`, `saturation_properties`, `triple_pressure`,
  `two_phase_domain_K`, `assert_two_phase_domain`, `SourceGatedFluidError`.
- `src/orbital_thermal/registry/two_phase.py` — the executable Gungor & Winterton (1986)
  HTC and its parts (`martinelli_xtt`, `boiling_number`, `dittus_boelter_liquid_htc`,
  `cooper_pool_boiling_htc`); `PROVISIONAL_DOMAINS`; `GW86_DATABASE_FLUIDS` /
  `fluid_in_gw86_database`.
- `src/orbital_thermal/two_phase.py` — the S2 evaporator module (stdlib-only).
- `tests/test_two_phase_evaporator.py`, `tests/test_two_phase_registry.py` (successor
  guards), `scripts/witness_s2_checks.py`.
- `docs/two-phase-evaporator.md`; this record; the mastery-ledger entry.

## Verification

- **Tests:** **630 passed, 3 xfailed, 0 failed, 0 skipped** with CoolProp 7.2.0.
  Baseline before S2 (measured on `155b10c`, not assumed): **587 passed, 3 xfailed**.
  Delta **+43**, all new legs; nothing removed.
- **Coverage:** 95.88% total (CI gate 90%). New modules: `two_phase.py` 94%,
  `registry/two_phase.py` 98%, `fluids.py` 98%.
- **Lint:** `ruff check src tests scripts` clean. (`ruff format` is deliberately not used
  by this repo and was not run.)
- **Witnessed failures:** **16/16** — see below.

### S0 §6 gate coverage

| Gate | Covered | How |
|---|---|---|
| **1 — limiting case AND transition** | yes | **Four separate tests**: subcooled forced convection; the ONB transition (checked from both sides at ±1e-6); saturated flow boiling; `x → 0` recovery. Plus a fifth asserting the recovery band **fails** below the turbulent threshold. |
| **2 — energy closure** | **not S2** | Needs the condenser and coupled solve (S3/S4). |
| **3 — pressure / quality / domain** | yes | `0 ≤ x ≤ 1` enforced (not clamped); `P_triple < P < P_crit`; `T_sat(P)` monotonic and inverting `saturation_pressure`; no blanket supercritical. |
| **4 — correlation validity ranges** | yes | Every declared axis driven out of range (9 parametrised cases); the guard is required to fire. In-domain calls still evaluate, so the guard is not vacuous. |
| **5 — rejection / de-ranking** | yes | All three CHF bands including both boundaries; underivable local flux; unsourced geometry; missing CHF → blocked; worst-gate-wins combination. |
| **6 — no regression** | yes | Full suite green from the 587 baseline, grown by the new legs. |

### Witnessed-failure record (S0 §3.1: "a check that has never failed is not a check")

Every S2 check was proven load-bearing by deliberate mutation via
`scripts/witness_s2_checks.py` (`16/16 checks witnessed failing on purpose`). Reproduce
with `python scripts/witness_s2_checks.py`.

| # | Mutation | Guard witnessed |
|---|---|---|
| 1 | implement an unsourced CHF entry | exact-set evaluate guard; locator↔evaluate invariant |
| 2 | implement an S3 pressure-drop entry early | S3 scope guard |
| 3 | blank an implemented correlation's locator | locator↔evaluate invariant (§3.2b) |
| 4 | drop a provisional-domain declaration | provisional-domain declaration |
| 5 | pretend ammonia is in the GW86 database | fluid-database applicability flag |
| 6 | clamp vapour quality instead of enforcing | `0 ≤ x ≤ 1` enforcement (gate 3) |
| 7 | collapse subcooled into saturated | regime classification + ONB gate (gates 1a/1b, 3) |
| 8 | widen the validity domain to nothing | correlation range checks (gate 4) |
| 9 | move the CHF rank band 0.5 → 0.9 | director ruling 9.5 bands (gate 5) |
| 10 | let an averaged flux rank | local-flux discipline (gate 5, T6) |
| 11 | assume a missing CHF is safe | blocked-on-missing-CHF rule (gate 5) |
| 12 | return an invented CHF value | no-invention blocker at the point of use |
| 13 | "correct" the published Cooper constant to 1/ln(10) | fidelity to the printed source constant |
| 14 | drop the critical-point guard | no blanket supercritical treatment (gate 3) |
| 15 | disable the convective enhancement factor | flow-boiling physics (gates 1c/1d) |
| 16 | combine gates by best instead of worst | gate combination |

**Two mutations were NOT witnessed on the first run, and both were real:**

- **#3** was a no-op (`"" or X` returns `X`), so it proved nothing about the guard. Fixed.
- **#15** left the saturated-flow-boiling test **passing**. That exposed the *test* as too
  weak: with `E = 1` the correlation still satisfies `htc > alpha_L`, because the nucleate
  term is additive. The assertion is now a strict excess over `alpha_L + alpha_nb`, which
  with `S ≤ 1` is reachable only if `E > 1`. **The witness found a genuine gap in the test
  suite, which is exactly its purpose.**

## Sourcing outcome (T1–T8) — what was and was not implemented

**Implemented: `two_phase.htc.gungor_winterton`.** Vertical / non-stratified form,
transcribed from Thome, *Engineering Data Book III*, Ch. 10 §10.3.3, Eqs.
[10.3.20]–[10.3.23] with supporting [10.3.4]–[10.3.6], [10.3.8], [10.3.15]. The primary
1986 IJHMT paper was **not obtained**, so no volume/page/DOI is asserted for it; the
locator names the reference work actually consulted. The Cooper (1984) nucleate term was
independently cross-checked against Shah (2022), *Int. J. Refrigeration* 137:103–116
Eq. (25) and agrees term by term.

> **Judgment call for the director.** §2 of the handoff bars implementing "from a
> secondary description." Thome's data book is a secondary *source* but a **verbatim
> reproduction** with equation numbers, and one full term was corroborated against a
> second independent source. The builder judged that this clears the bar and the primary
> paper's absence is recorded rather than papered over. **If the director disagrees,
> reverting is a one-line change** (`evaluate=None`), and
> `test_exactly_the_s2_implemented_ids_carry_an_evaluate_callable` makes the reversion
> trivially verifiable.

**Named modelling decision.** GW86's horizontal-channel Froude/stratification de-rating
is deliberately **not applied** — confirmed to exist by Shah (2006), *HVAC&R Research*
12(4). It models gravitational phase stratification, a 1-g effect with no microgravity
meaning; applying a gravity-driven de-rating in a microgravity screening model would be a
silent physical assumption. Mirrors S0 §3's treatment of `dP_static ≈ 0`.

**Not implemented: `two_phase.chf.shah_2015` — attribution blocker (closes the S1 open
item on this domain).** See finding **F1**.

**Not implemented: `two_phase.onb.bergles_rohsenow` — promotion attempted, declined.**
The 1964 criterion is a **graphical** construction (Liu, Lee & Garimella 2005, *IJHMT*
48:5134–5149), and its usual algebraic surrogate is a dimensional **water-only** fit —
out of fluid domain for the ammonia reference coolant. Stays `SOURCE_REQUIRED`, locator
blank. The ONB **policy gate ships unconditionally** and, absent a sourced criterion,
de-ranks anything not unambiguously in saturated flow boiling (S0 §3, F2).

**Locators (T8).** Exactly one filled — GW86, the only entry whose source was consulted
for a formula that was implemented. The other twelve stay blank. Both directions are
enforced by tests: an implemented correlation **must** have a locator, and an
unimplemented one **must not**.

## Findings requiring director disposition

### F1 — `two_phase.chf.shah_2015` is misattributed (blocking for the CHF leg)

Two independent problems, both established from Shah's own publications:

1. **The citation is ambiguous.** There is no single "Shah (2015)" general CHF
   correlation. Shah published **two** distinct 2015 CHF papers — *Improved general
   correlation for CHF in vertical annuli with upflow*, **Heat Transfer Engineering**
   37(6):557–570, and *A general correlation for CHF in horizontal channels*, **Int. J.
   Refrigeration** 59:37–52. The registry citation identifies neither, and they apply to
   different geometries. The S2 evaporator geometry is **channels**, so the choice is not
   immaterial.
2. **The declared domain belongs to a different paper.** `pr_reduced` 0.0014–0.96 is
   verifiably the database range of **Shah (1987)**, *Int. J. Heat and Fluid Flow*
   8(4):326–335. Shah's own *Fluids* 2023, 8, 90 §3.1 states: "Shah (1987) analyzed data
   for 23 fluids …, tube diameters 0.315 to 37.5 mm, mass flux 4 to 2905 kg m⁻² s⁻¹,
   **reduced pressure 0.0014 to 0.96**, and critical quality −0.26 to 0.96." That same
   2023 paper still treats **Shah (1987)** — not a 2015 paper — as the most-verified
   general CHF correlation for tubes.

**Consequence.** Implementing the id would require choosing a paper and attaching maths
whose attribution cannot be established. Under no-invention the entry stays unimplemented
and **the blocker is the deliverable**. The domain is declared provisional.

**Knock-on for director attention:** this also puts the registry's classification of
`two_phase.chf.shah_1987` as a mere "historical ancestor" **sensitivity** in question —
on this evidence it is the live, most-verified general tube CHF correlation. Director
ruling 3 currently pins it to `SENSITIVITY` with `evaluate=None`, and this build did not
touch it. **Registry-level correction is a director decision, not a builder one.**

### F2 — the reference coolant is outside the reference HTC's fluid database

The GW86 development database is water, R-11, R-12, R-22, R-113, R-114 and ethylene
glycol (Thome §10.3.3). **Ammonia is not in it** — and ammonia is the S0 §9.1 **reference
coolant**. Independent assessments also report poor GW86 accuracy for ammonia
specifically.

This is a collision between two director-level facts (ruling 9.1 makes ammonia the
reference coolant; the S1 registry makes GW86 the rank-eligible reference HTC), so the
build **surfaced it machine-visibly** (`fluid_in_gw86_database`, reported in every
`AcquisitionAssessment`) rather than resolving it by silently de-ranking ammonia or
silently ranking it. **Disposition needed before any two-phase ranking (S5/S6).**

### F3 — declared water saturation domain marginally exceeds the critical point (minor)

`TWO_PHASE_PROPERTIES` declares water `T_K` up to 647.1 K; the pinned backend's critical
temperature is 647.096 K. ~4 mK of declared domain is genuinely supercritical. Handled in
code by guarding against the **actual** triple/critical bounds as well as the declared
domain, and a test drives that exact window. Recorded rather than edited: the declared
domain is S1 reviewed content.

## Claim discipline / no-invention

- No fabricated DOI, identifier, volume, page, or physical value anywhere in the diff.
- Two entries left `SOURCE_REQUIRED`/unimplemented with the reason recorded machine-visibly;
  twelve of thirteen locators still blank.
- Both unconfirmed domains **declared provisional** and still **enforced** as guards.
- 1-g basis preserved on every entry (`microgravity_validated=False`, `gravity_basis="1g"`,
  `rank_scope="reference_correlation_only"`). **No microgravity claim.**
- **No level-d claim.** Sol's review is category **c**.
- Nothing in S0 §7's disallowed list is asserted in any doc or docstring added here.

## Disposition

**OPEN.** Builder work complete and verified: 630 passed / 3 xfailed from a measured 587
baseline, 16/16 checks witnessed failing, lint clean, coverage 95.88%.

**Not closable by the builder.** Requires: (i) director disposition of **F1** and **F2**;
(ii) director judgment on the GW86 secondary-source call recorded above; (iii) Sol's
cross-model review. `main` is untouched, no tag, no release.
