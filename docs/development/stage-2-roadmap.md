# Phase B Stage 2 — Roadmap (two-phase build + external reference-case track)

> **Status: proposed, forward-looking, provisional, and subject to revision.** Living planning
> document. It **extends** the milestone plan in the approved S0 scoping note (§8 of
> `phase-b-stage-2-scoping-note.md`) by inserting an **external reference-case reproduction track
> (R1–R3)** around the two-phase build. It **does not edit** the CLOSED S0 record. No
> implementation code is authorized by this document; each milestone is picked up and reviewed on
> its own terms.

**Repository:** `orbital-thermal-bounds` — https://github.com/dan-lee-odinson/orbital-thermal-bounds
**Director:** Dan Lee-Odinson (project director, sole release gate)
**Baseline:** Phase B **Stage 1 = v1.1.0**; **regression baseline for Stage 2 = `v1.1.0`**
**Target version:** `v1.2.0` (additive) — `v2.0.0` only on a framing shift / breaking change
**Date:** 2026-07-05
**Related records:** approved scope — `docs/development/phase-b-stage-2-scoping-note.md` (S0, r1);
S0 review — `verification/review-records/2026-07-05-s0-stage-2-scoping.md` (CLOSED); source pin —
the **R0 Biswas/Suncatcher intake** (`biswas-r0`, pinned, unreproduced).

---

## 1. Two distinct workstreams

Stage 2 runs two separate tracks that meet only at the end:

- **S-track (S1–S8) — the two-phase build.** The reduced-order, single-component, mechanically
  pumped **flow-boiling** model + trade study, scope fixed by the approved S0 note. This is the
  Stage-2 physics implementation.
- **R-track (R0–R3) — external reference-case reproduction.** Reproduce and source-anchor the
  **Biswas/Suncatcher v1.2 Part I thermal baseline**, wrap it as a cited external reference case,
  and — only after the two-phase framework exists — run a **harmonized comparison**.

**The R-track is not part of the two-phase model implementation.** It is an external
reference/reproduction track that stands beside the build. Keeping them separate protects claim
discipline: the two-phase model is developed on its own evidence, and the external reference is
reproduced on its own provenance, before the two are ever compared.

---

## 2. Ordering (director-directed)

```
S0  approve Stage-2 scope .......................... DONE (merged; review record CLOSED)
R1  reproduce Biswas/Suncatcher v1.2 Part I ........ from the pinned R0 release/commit
R2  wrap reproduction as an external reference case  tests + provenance + limitations
S1  two-phase property/correlation registry ........ Stage-2 build begins
S2  two-phase acquisition / evaporator
S3  two-phase pressure drop + condenser
S4  coupled two-phase steady-state solver (MAJOR)
S5  two-phase architecture cases
S6  two-phase trade-study extension (MAJOR)
R3  harmonized comparison (MAJOR) .................. requires R2 AND S4–S6
S7  docs + figures
S8  review + release decision (MAJOR) → v1.2.0
```

**Placement.** R1 and R2 sit **after S0 and before S1** in intended order (director direction).
They are a **separable, dependency-independent** track — they touch external-reference intake code,
**not** the two-phase model — so if the R1 reproduction proves lengthy, R1/R2 **may run alongside
S1** without blocking it. **R3 is the dependency join:** it requires **R2** (the reference case) and
**S4–S6** (the two-phase framework), so R3 cannot start until both exist.

**Recommendation:** sequential-first (R1 → R2 → S1…), with the parallel fallback above reserved for
if R1 runs long. Confirm or redirect at review.

---

## 3. Hard constraints for the R-track (claim discipline + no-invention)

These are load-bearing. They apply to every R-milestone.

1. **No ranking yet.** R1 and R2 establish **faithful reproduction and source anchoring only.** They
   do **not** rank Biswas/Suncatcher against `orbital-thermal-bounds`, and assert **no** "better/
   worse/best" judgment.
2. **Reproduction ≠ validation.** Faithfully reproducing their published baseline **from their
   pinned source** means we reproduced *their calculation*. It does **not** validate their physics,
   nor ours.
3. **External reference oracle ≠ our oracle-freeze set.** The reproduced Suncatcher values are an
   **external reference** (their numbers, cited from the pin), kept **separate** from our Phase A /
   Stage-1 oracle-freeze numbers. Oracle-freeze on our published numbers is untouched.
4. **Pinned source.** R1 works from the **pinned R0 release/commit** for reproducibility. Do **not**
   substitute a newer public version; a version change is a new, separately-approved pin.
5. **No-invention.** Any Biswas/Suncatcher input **not specified** in the pinned release becomes a
   **machine-visible blocker / source-gate**, never a guessed value.
6. **Disallowed even at R3.** No "best architecture," no "complete Starcloud/Suncatcher judgment,"
   no externally-validated / flight-grade / hardware-validated claims. **R3 is a harmonized
   comparison that surfaces the dominating assumptions — not a winner.**
7. **Cross-model ≠ level d.** As everywhere in this project, cross-model (GPT-5.5) review supports
   category **c** and never counts as level **d** (qualified external human review), which remains
   `pending`.

---

## 4. R-track milestone blocks

### R0 — pinned source intake  *(DONE)*
- **State:** `biswas-r0` — Biswas/Suncatcher source intake, **pinned, unreproduced, unranked.**
- **Note:** the exact release/commit identifiers and the as-published inputs live in the R0 intake
  record; R1 reads them from there (no-invention for anything unspecified).

### R1 — reproduce the v1.2 Part I thermal baseline
- **Inherited:** the R0 pin.
- **Scope:** recompute Biswas/Suncatcher's **published Part I thermal baseline** from the pinned
  release/commit. Every input is taken from the pin; anything unspecified is a **blocker/source-
  gate**, not a guess.
- **Deliverable:** a reproduction module/script that recomputes their baseline, plus a **fidelity
  comparison** to their published values within a **stated tolerance**; a review record.
- **Verification:** **c** (executable reproduction) + **a** (their published values as the external
  reference target, cited from the pin). Reproduction fidelity is claim-sensitive → **review record
  produced.** Not level d.
- **Claim discipline:** "faithful reproduction of the pinned baseline." Explicitly **not**
  validation, **not** ranking, **not** a comparison to our model.
- **Completion:** reproduction matches the pinned published baseline within tolerance (or documented,
  source-gated gaps); review record produced.

### R2 — wrap as an external reference case
- **Inherited:** the R1 reproduction.
- **Scope:** package the reproduction as a **first-class external reference case** in the repo, with
  **tests**, **provenance** (source + pin + version), and an **explicit limitations** statement.
- **Deliverable:** reference-case module + tests + provenance/limitations doc; a mastery-ledger entry
  (e.g. `suncatcher-v1.2-part-i-reference`) at status **`reproduced` (external reference)** —
  **clearly labeled as external-reference reproduction, not validation and not a ranking.**
- **Verification:** **c** (tests) + **a** (provenance). Not level d.
- **Claim discipline:** external reference only; **unranked**; limitations explicit.
- **Completion:** tests green; provenance + limitations recorded; ledger entry opened and labeled.

### R3 — harmonized comparison  *(MAJOR; after S4–S6)*
- **Inherited:** the **R2** reference case **and** the Stage-2 two-phase framework (**S4–S6**).
- **Scope:** compare the Suncatcher reference baseline against `orbital-thermal-bounds` two-phase
  results **under explicitly harmonized assumptions**, surfacing the **dominating assumptions** and
  where results diverge and why.
- **Deliverable:** comparison outputs that distinguish **verification-supported / reference /
  rank-eligible / parametric / rejected** cases; **every output tagged** with the harmonization
  assumptions **and** the S0 §7 ranking-scope limitation (rank-eligible only within the adopted 1-g
  reference-correlation model; not microgravity-validated).
- **Verification:** **c** (comparison engine) + inherited **a/b/**sensitivity physics from S1–S6.
  **MAJOR → mandatory cross-model adversarial review + director stop.** Level d `pending`.
- **Claim discipline:** **harmonized comparison, not "best architecture," not a complete
  Starcloud/Suncatcher judgment.** No validation claims. Differences are attributed to explicit
  assumptions, not declared as a winner.
- **Completion:** comparison produced; assumptions surfaced; no unjustified ranking; cross-model
  review + review record; **stops for the director.**

---

## 5. Relationship to the S-track, records, and the ledger

- The **S0 §8 milestone table remains the S-track plan**; this roadmap inserts the R-track around it
  and is the **living Stage-2 sequence of record.** The CLOSED S0 note is not edited.
- **Records are separate:** R1 produces a reproduction review record; R3 (major) produces a
  cross-model + director review record. S-milestones keep their own records per the S0 plan.
- **Mastery-ledger:** R1/R2 open an **external-reference** entry at `reproduced` (external reference
  — *not* validation, *not* ranking). **No ledger entry ranks Suncatcher.** Level d `pending` for
  every entry.
- **No-regression:** every R and S milestone keeps the Phase A / `v1.1.0` published suites and
  oracle-freeze green (regression baseline `v1.1.0`).

---

## 6. Verification-level summary

| Milestone | New evidence | Review | Ranking? |
|---|---|---|---|
| R0 (done) | pinned intake (a: source pin) | intake note | no |
| R1 | c (reproduction) + a (pinned published values) | review record | **no** |
| R2 | c (tests) + a (provenance) | ledger entry + limitations | **no** |
| S1–S3 | a/b + c per S0 plan | intermediate | n/a |
| S4 (major) | c baseline recovery + b residual | cross-model + director | n/a |
| S5 | a + c | spot-check | n/a |
| S6 (major) | c engine + inherited physics | cross-model + director | within-model only |
| **R3 (major)** | c comparison + inherited a/b/sensitivity | **cross-model + director** | **harmonized comparison only — no "best"** |
| S7 | docs | intermediate | n/a |
| S8 (major) | full regression vs v1.1.0 | director stop → v1.2.0 | n/a |

---

*Living Stage-2 roadmap. Standing rules carried in unchanged: no-invention, oracle-freeze, claim
discipline, cross-model ≠ level d, "certificate" = internal numerical convergence. R1/R2 anchor an
external reference by faithful reproduction only; ranking, if it ever happens, is a harmonized,
assumption-explicit R3 comparison — never a declaration of a best architecture.*
