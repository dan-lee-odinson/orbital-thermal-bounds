<!-- Major-milestone review record (S0, Stage-2 scoping). CLOSED: cross-model adversarial review
complete, findings dispositioned, S0 text revised (r1) to close F2-F9; S1 may begin. -->
> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Review Record: S0 — Stage-2 scoping decision (two-phase / boiling transport)

## Record Metadata
- **Record status:** **CLOSED** — Stage-2 scope approved (two-phase flow-boiling extension);
  proceed to S1.
- **Date:** 2026-07-05
- **Reviewed commit:** `6a7194444d3cf8716010c4255b466e88ba05886e` (cross-model + director-reviewed
  baseline) **+ r1 S0 text-revision follow-up in the same PR** (`docs/s0-stage-2-scoping`) closing
  findings F2–F9.
- **Reviewer(s):** **project director (Dan Lee-Odinson)** for this gate. Cross-model (GPT-5.5)
  adversarial review is recorded below and is **not** qualified external human engineering review.
- **Trigger:** major milestone (S0; Stage-2 scoping / B0-equivalent).
- **Disposition:** **Approve Stage-2 scope; proceed to S1.** No S1 code until this record is
  committed CLOSED alongside the revised note.

## Scope of this gate
- **Planning only. No code.** S0 selects the Stage-2 primary target (two-phase transport), fixes
  the model boundary, defines verification gates *before* code, and records director decisions.
- Deliverable under review: `docs/development/phase-b-stage-2-scoping-note.md` (r1).

## Director decisions recorded (2026-07-05)
1. Reference coolant: **ammonia primary; water secondary; all others source-gated.**
2. Microgravity: **cited 1-g correlations as reference + explicit microgravity limitation**; not
   hard blockers; **no microgravity validation claimed.**
3. Condenser/radiator boundary: **Stage-1/B0 dual boundary** — fixed effective sink for
   baseline/debug; Phase A orbital boundary for reported trade spaces.
4. Two-phase pressure drop: **Lockhart–Martinelli/Chisholm reference; Friedel sensitivity.**
5. CHF/dryout: **rank-eligible iff `q''/CHF ≤ 0.5`** on local wall flux; above → reject or
   sensitivity, do not rank. Modeling margin, **not** flight certification.
6. Version target: **`v1.2.0` additive default; `v2.0.0` only** on a framing shift / breaking change.
7. Suncatcher: **out of Stage-2 S0 scope**; Biswas/Suncatcher stays **pinned, unreproduced,
   unranked** unless separately approved.

## Cross-model (GPT-5.5) adversarial review — **not level d**
- **Verdict:** *proceed with required changes.* Chosen boundary (reduced-order, single-component,
  mechanically pumped flow-boiling extension) accepted as a defensible first two-phase increment.
- **Process note (recorded honestly):** the cross-model pass ran against the **pre-decision draft**,
  not the committed baseline `6a71944`. Reconciled against `6a71944`, findings **F1, F4, F10 were
  already resolved**; **F2, F3, F5, F6, F7** were closed by the **r1 text revision**; **F8, F9**
  closed as named-boundary/wording cleanup. Because the revision only implements the reviewer's own
  requested text gates and **changes no technical scope**, a full re-review was **not** required
  (director direction).
- **Category:** supports **c** (error detection). Two AI systems agreeing counts as a single
  category and **does not** advance level d. Level d remains **`pending` for every ledger entry.**

### Finding dispositions

| # | Sev | Disposition |
|---|---|---|
| F1 — decisions still shown as open questions | major | **Already resolved in `6a71944`** — §9 is "Director decisions (resolved)"; §10 says "recorded." (draft-only) |
| F2 — `x→0` gate can pass a wrong ONB transition | major | **Closed by r1** — §3 ONB/saturated-regime policy (source-gated ONB; sub-ONB = sensitivity-only); §6 gate 1 adds separate subcooled/ONB/saturated tests. |
| F3 — pump-inlet cavitation/NPSH not gated | major | **Closed by r1** — §3 pump-inlet feasibility: source-gated NPSH margin → reject on fail, else explicit "not modeled (idealized boundary)"; §6 gate 5 rejects NPSH failures; §5 registry row. |
| F4 — stability/uniqueness not in note | major | **Already resolved in `6a71944`** — §3 flow-stability/uniqueness paragraph + §6 gates 3/5 (Ledinegg slope, non-unique fail-loudly, dynamic instabilities out-of-scope). (draft-only) |
| F5 — `q''` in CHF ratio undefined | major | **Closed by r1** — §3 defines `q''` as **local modeled wall flux**; unobtainable → block/sensitivity; no silent average. §9.5 aligned. |
| F6 — 1-g ranking readable as microgravity-valid | major | **Closed by r1** — §7 exact ranking-scope limitation wording; tagged on every S6 output (§8). |
| F7 — LM/Chisholm sub-choices not source-gated | major | **Closed by r1** — §3/§5/§8 require the S1 registry to record the exact variant + regime + range + source; rank-changing sub-choice = recorded sensitivity. |
| F8 — adiabatic transport lines not a named boundary | minor | **Closed by r1** — §3 promotes adiabatic lines to a named boundary/limitation; §6 gate 2 reads as closure **under that boundary**. |
| F9 — overstates what flow-boiling retires | minor | **Closed by r1** — §1/§2 reworded to "partially addresses the two-phase prerequisite for mechanically pumped flow-boiling loops"; capillary/Suncatcher stay deferred (§7). |
| F10 — "real spacecraft coolant" unsourced | minor | **Already resolved in `6a71944`** — phrase absent; ammonia is stated as Stage-1/Stage-2 reference with spacecraft-use basis source-gated in S1. (draft-only) |

- **Endorsed with no action:** flow-boiling as the first Stage-2 target; the fixed-sink /
  Phase-A-orbital reported-boundary split; the Suncatcher exclusion; the S4/S6/S8 major stops.

## Claim-discipline check (S0)
- S0 asserts **no new physical claim** — only a **scope claim** (planned reduced-order two-phase
  extension). Disallowed-claim scan (r1): none present (externally validated / flight-grade /
  hardware-validated / microgravity-validated / best architecture / total mass closure / complete
  Starcloud judgment — all absent). r1 additionally forbids implying Stage 2 retires the two-phase
  prerequisite beyond mechanically pumped flow-boiling loops.
- Required limitation wording (microgravity applicability + ranking-scope; reduced-order framework;
  cross-model ≠ level d) present.

## No-regression status
- **Docs-only change; no code.** No `src/` behavior changes; no Phase A or Stage-1 (`v1.1.0`)
  published number is touched. Regression baseline = `v1.1.0`. CI: tests / quality unaffected; docs
  build renders the revised note (auto-nav); oracle-freeze untouched.

## Verification level
- **n/a (plan).** The plan is reviewed (director + cross-model), recorded here. No ledger entry
  advances at S0; the three anticipated Stage-2 entries are only **named** in the note (§4), created
  at the milestone that introduces each.

## Release governance
- AI-assistance checkbox in the PR **left unchecked** (director attestation).
- Major milestone: **stopped for the director.** S1 may begin only after this record and the r1 note
  are committed.

## Findings / director review
Director review of `6a71944` + the r1 revision:
1. Cross-model adversarial review obtained (GPT-5.5, verdict "proceed with required changes"); ran
   against the pre-decision draft, reconciled against the committed baseline above.
2. F1/F4/F10 confirmed already resolved in `6a71944`; F2/F3/F5/F6/F7 confirmed closed in the r1
   text; F8/F9 confirmed closed as named-boundary/wording cleanup.
3. No technical-scope change introduced by r1 → full re-review not required.
4. Claim discipline and no-regression verified; decisions §9 stand, unreopened.

## Disposition
**CLOSED. Approve Stage-2 scope (two-phase flow-boiling extension); proceed to S1.** Reviewed commit
`6a71944` + r1 S0 text-revision follow-up in `docs/s0-stage-2-scoping`. Standing future action:
seek qualified-human (level d) review of the central transport/pressure claims as Stage 2 matures.
