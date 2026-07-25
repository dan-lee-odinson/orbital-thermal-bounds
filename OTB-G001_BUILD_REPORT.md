# OTB-G001 — Build Report

**Gate:** OTB-G001 · Stage 2, milestone **S2** (two-phase acquisition / evaporator)
**Branch:** `stage-2/s2-evaporator` · **Base:** `main` at `155b10c`
**Method:** METHOD v1.0 · **Tier:** 2 (substantive) · **Target version:** `v1.2.0` (additive)
**Date:** 2026-07-25 · **Builder:** Claude (Claude Code)

> **`main` untouched. No tag. No release. Nothing deposited to the shared folder.**
> The branch is pushed and stops there. Merge is the terminal action of a gate that Sol
> has reviewed and Dan has dispositioned and signed.

---

## 1. Headline

All nine tasks (T1–T9) are addressed. **Seven were implemented; two correlations were
deliberately *not* implemented because their sources could not be established, and those
blockers are the deliverable.**

| Metric | Baseline (`155b10c`) | After S2 |
|---|---|---|
| Full suite (CoolProp 7.2.0) | **587 passed, 3 xfailed** | **630 passed, 3 xfailed** |
| Failures / skips | 0 / 0 | **0 / 0** |
| Coverage (CI gate 90%) | — | **95.88%** |
| `ruff check src tests scripts` | clean | **clean** |
| Correlations carrying `evaluate` | 0 of 11 | **1 of 11** |
| `source.locator` filled | 0 of 13 | **1 of 13** |
| Checks witnessed failing on purpose | — | **16 / 16** |

The baseline was **measured on `155b10c` in this environment**, not taken on trust; it
reproduced the handoff's numbers exactly, including the stated ammonia anchors
(`h_fg = 1 158 051 J/kg`, `σ = 0.02006 N/m` at 300 K).

---

## 2. What was implemented

| # | Task | Outcome |
|---|---|---|
| **T1** | Saturation properties | **Done.** `saturation_temperature`, `saturation_enthalpies` (`h_f`/`h_g`/`h_fg`), `surface_tension`, plus `saturation_properties`, `triple_pressure`, `two_phase_domain_K`, `assert_two_phase_domain`, `SourceGatedFluidError`. CoolProp HEOS pinned 7.2.0. Guarded against **both** the declared registry domain and the real triple/critical bounds. |
| **T2** | Quality / loop state | **Done.** `x = (h − h_f)/h_fg` **enforced** to `[0,1]`, not clamped; `P_triple < P < P_crit`; no blanket supercritical. `loop_state` classifies into subcooled / saturated / superheated and keeps the raw equilibrium quality so the regime gate can see it. |
| **T3** | Flow-boiling HTC | **Done.** Gungor & Winterton (1986) wired as the entry's `evaluate`. Every call range-checked via `assert_in_domain`; out of range raises, never extrapolates. |
| **T4** | ONB / regime policy | **Policy gate done and shipping unconditionally.** Source **not** obtained → promotion declined (see §3). Gate applies the S0 §3 (F2) fallback: anything not unambiguously in saturated flow boiling is sensitivity-only. |
| **T5** | CHF / dryout bands | **Bands done** (`≤0.5` rank-eligible; `0.5–1` sensitivity, not ranked; `≥1` rejected). **Correlation not implemented** (see §3). `critical_heat_flux()` raises a blocker rather than returning a number. |
| **T6** | Local-flux discipline | **Done.** Flux carries its basis (`LOCAL_SOURCED` / `SECTION_AVERAGE` / `CHIP_AVERAGE`) and its `geometry_sourced` flag, so an average can never be silently substituted. Averages are permitted only when explicitly named, and are never rankable. |
| **T7** | `shah_2015` domain | **Checked against the source and refuted.** Declared provisional; **not** promoted (see §3, F1). |
| **T8** | Locators, bounded | **Done.** Exactly **one** filled — the only entry whose source was consulted for a formula that was implemented. Twelve stay blank. Both directions test-enforced. |
| **T9** | Records | **Done.** S2 review record (`OPEN`, not builder-closable) + mastery-ledger entry for S0 §4 claim 1 at status **`derived`** with level **d** `pending`. |

---

## 3. What was NOT implemented, and why

This is the substantive half of the report. Two of the three correlations S2 was scoped
to touch were left unimplemented. Neither gap was filled by reconstruction.

### 3.1 `two_phase.chf.shah_2015` — attribution blocker

**Not implemented. Locator left blank. Domain declared provisional.**

Two independent problems, both established from **Shah's own publications**:

1. **The citation is ambiguous.** There is no single "Shah (2015)" general CHF
   correlation. Shah published **two** distinct 2015 CHF papers:
   - *Improved general correlation for CHF in vertical annuli with upflow*, **Heat
     Transfer Engineering** 37(6):557–570
   - *A general correlation for CHF in horizontal channels*, **Int. J. Refrigeration**
     59:37–52

   The registry citation identifies neither, and they apply to different geometries. The
   S2 evaporator geometry is **channels**, so the choice is not immaterial.

2. **The declared domain belongs to a different paper.** The declared `pr_reduced`
   0.0014–0.96 is verifiably the database range of **Shah (1987)**, *Int. J. Heat and
   Fluid Flow* 8(4):326–335. Shah's own *Fluids* 2023, 8, 90 §3.1 states: "Shah (1987)
   analyzed data for 23 fluids …, tube diameters 0.315 to 37.5 mm, mass flux 4 to 2905
   kg m⁻² s⁻¹, **reduced pressure 0.0014 to 0.96**, and critical quality −0.26 to 0.96."
   That same 2023 paper still treats **Shah (1987)** — not a 2015 paper — as the
   most-verified general CHF correlation for tubes.

Implementing this id would have required picking one of the two papers and attaching
maths whose attribution cannot be established. A reconstructed correlation that happens
to be right is indistinguishable, in the artifact, from one that is wrong — so the entry
stays unimplemented.

> **Knock-on finding for Dan.** This also puts the registry's classification of
> `two_phase.chf.shah_1987` as a mere *"historical ancestor"* **sensitivity** in question:
> on this evidence it is the live, most-verified general tube CHF correlation. **Ruling 3
> pins it to `SENSITIVITY` with `evaluate=None`, and this build did not touch it.** The
> registry-level correction is a director decision, not a builder one.

The CHF **banding policy** — the part Dan actually ruled on in §9.5 — ships in full and
is exercised across all three bands and both boundaries. It is a policy gate over a CHF
*value*; it simply has no sourced correlation feeding it, so a case needing a computed
CHF is **blocked**, never silently ranked.

### 3.2 `two_phase.onb.bergles_rohsenow` — promotion attempted, declined

**Not implemented. Locator left blank.** Two reasons, either sufficient alone:

1. **The criterion is graphical.** Liu, Lee & Garimella (2005), *Int. J. Heat and Mass
   Transfer* 48:5134–5149, records that Bergles and Rohsenow "extended Hsu's model and
   proposed a **graphical** solution to predict the incipient heat flux in flow boiling."
   There is no closed form in the original to transcribe.
2. **The algebraic surrogate is water-only and dimensional.** The form usually attributed
   to that construction is a dimensional fit for **water**. The S0 §9.1 reference coolant
   is **ammonia**, which is outside its fluid domain; applying it would be an
   extrapolation across fluids, not a citation.

Per T4, the policy gate ships regardless and works with or without a sourced criterion —
`classify_regime` accepts one if it is ever obtained.

### 3.3 Locators left blank

**Twelve of thirteen.** Only `two_phase.htc.gungor_winterton` has a locator, because it
is the only entry whose source was consulted for a formula that was implemented. No DOI,
volume, page or identifier was fabricated anywhere in the diff. Both directions are
test-enforced: an implemented correlation **must** carry a locator; an unimplemented one
**must not**.

---

## 4. Judgment call the director should rule on

**The GW86 executable form came from a secondary source.** §2 of the handoff bars
implementing "from a secondary description." What was actually done:

- The primary Gungor & Winterton (1986) *IJHMT* paper was **not obtained** (paywalled).
- The equations were transcribed from **Thome, *Engineering Data Book III*, Ch. 10
  §10.3.3, Eqs. [10.3.20]–[10.3.23]** with supporting [10.3.4]–[10.3.6], [10.3.8],
  [10.3.15] — a professional reference work that reproduces them **verbatim, with
  equation numbers**, not a paraphrase.
- The Cooper (1984) nucleate term was **independently cross-checked** against Shah
  (2022), *Int. J. Refrigeration* 137:103–116 Eq. (25) and agrees **term by term**.
- **No** volume/page/DOI is asserted for the 1986 paper, and the locator says plainly
  which work was consulted.

The builder judged that a verbatim reproduction with an independent cross-check clears
the bar, and that the primary paper's absence belongs in the record rather than hidden.
**This is flagged rather than buried precisely because it is a judgment call.** If Dan
rules otherwise, reverting is a one-line change (`evaluate=None`) and
`test_exactly_the_s2_implemented_ids_carry_an_evaluate_callable` makes the reversion
trivially verifiable.

---

## 5. Findings requiring director disposition

**F1 — `shah_2015` is misattributed.** §3.1 above. Blocks the CHF leg of S0 §4 claim 1,
and puts the `shah_1987` sensitivity classification in question.

**F2 — the reference coolant is outside the reference HTC's fluid database.** The GW86
development database is water, R-11, R-12, R-22, R-113, R-114 and ethylene glycol
(Thome §10.3.3). **Ammonia is not in it** — and ruling 9.1 makes ammonia the reference
coolant. Independent assessments also report poor GW86 accuracy for ammonia specifically.

This is a collision between two director-level facts, so the build **surfaced it
machine-visibly** (`fluid_in_gw86_database`, reported on every `AcquisitionAssessment`)
rather than resolving it by silently de-ranking ammonia or silently ranking it.
**Disposition is needed before any two-phase ranking (S5/S6).**

**F3 — declared water domain marginally exceeds the critical point (minor).**
`TWO_PHASE_PROPERTIES` declares water `T_K` to 647.1 K; the pinned backend's critical
temperature is 647.096 K, so ~4 mK of declared domain is genuinely supercritical. Handled
in code by also guarding the **actual** triple/critical bounds, with a test driving that
exact window. Recorded rather than edited, since the declared domain is S1 reviewed
content.

**F4 — both declared numeric domains are provisional.** The GW86 ranges could not be
matched to any obtained source; the CHF range traces to a different paper. Both are
listed in `PROVISIONAL_DOMAINS`, declared provisional, and **still enforced** as guards.

---

## 6. Witnessed-failure record

`scripts/witness_s2_checks.py` breaks the thing each S2 gate guards — one literal source
mutation at a time — and requires the mapped tests to fail. A mutation that leaves the
suite green is reported as a **failure**, because it means the gate does not constrain
what it claims to. An anchor that no longer matches is also reported as not witnessed, so
the harness cannot rot into a no-op. Files are restored in a `finally` block.

**Result: `16/16 checks witnessed failing on purpose.`** Reproduce with
`python scripts/witness_s2_checks.py`.

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
| 13 | "correct" the published Cooper constant to 1/ln(10) | fidelity to the printed constant |
| 14 | drop the critical-point guard | no blanket supercritical treatment (gate 3) |
| 15 | disable the convective enhancement factor | flow-boiling physics (gates 1c/1d) |
| 16 | combine gates by best instead of worst | gate combination |

### Two mutations were NOT witnessed on the first run, and both were real

- **#3** was a no-op: `"" or X` returns `X`, so the locator was never actually blanked.
  The mutation proved nothing and was fixed.
- **#15** left the saturated-flow-boiling test **passing**. That exposed the *test* as too
  weak: with `E = 1` the correlation still satisfies `htc > alpha_L`, because the nucleate
  term is additive. The assertion is now a strict excess over `alpha_L + alpha_nb`, which
  with `S ≤ 1` is reachable only if `E > 1`. **The witness found a genuine gap in the test
  suite — which is exactly what it is for, and is the reason the requirement exists.**

Two further checks were witnessed failing *unintentionally* during development, and both
were also real: a hand-checked Cooper value that had idealised `0.4343` to `1/ln(10)`
(the test was wrong, and the printed constant now has its own guard), and a
supercritical-guard test whose assertion had assumed the wrong guard fired first — which
is what surfaced finding **F3**.

---

## 7. Suite delta from 587

```
baseline (155b10c):  587 passed,  3 xfailed,  0 failed,  0 skipped
after S2:            630 passed,  3 xfailed,  0 failed,  0 skipped
delta:               +43 passed
```

All 43 are new S2 legs. **Nothing was removed**: the one S1 test that S2 necessarily
invalidated (`test_no_evaluate_callable_in_s1`, which asserted that *no* correlation
carries an `evaluate`) was **replaced by a strictly stronger successor**, not deleted —
it now pins the **exact** set of implemented ids, so it still catches an accidental early
S3 implementation, in both directions.

Coverage 95.88% against the CI gate of 90%; new modules 94–98%. `ruff check` clean.
Phase A and Stage-1 (`v1.1.0`) suites and the frozen oracle points are untouched.

---

## 8. Definition-of-done checklist

- [x] T1–T9 addressed; every unimplemented item recorded as a machine-visible blocker, never a guess
- [x] Only `two_phase.htc.gungor_winterton` carries an `evaluate`; every other entry `None`
- [x] `test_no_evaluate_callable_in_s1` **replaced** by the exact-set successor, not deleted
- [x] Locator↔evaluate invariant exists and passes (plus its converse)
- [x] All five applicable S0 §6 gates covered; gate 1 satisfied by **four separate** tests
- [x] Every new check **witnessed failing** on purpose; witness record shipped (§6)
- [x] Suite green from 587, grown by the new legs; oracle-freeze and `v1.1.0` untouched
- [x] No fabricated DOI, identifier, or physical value anywhere in the diff
- [x] Microgravity fields preserved on every entry; **no microgravity claim**
- [x] **No level-d claim** — Sol's review is category **c**
- [x] Branch pushed; **`main` untouched, no tag, no release, nothing in the shared folder**
- [ ] Director disposition of **F1**, **F2**, and the §4 judgment call — **for Dan**
- [ ] Sol cross-model review — **not run by the builder** (adversarial review is Sol's job)

---

## 9. Handback

Back to **Cowork** for machine verification and the freeze. The pickup was not run or
simulated, no LLM adversarial subagent was launched, and nothing was deposited to
`Claude_GPT_Shared_Workflow`.

The S2 review record is deliberately left **`OPEN`**: it is not builder-closable, and it
names the disposition items above as its closure conditions.
