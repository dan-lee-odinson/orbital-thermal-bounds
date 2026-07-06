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
**Revision:** **r2 (2026-07-05)** — added the comparable-tools landscape (§7), **Track C** (correlation
backend/comparator, §8), **Track X** (external planning comparable, §9), and terminology /
claim-discipline notes (§10).
**Related records:** approved scope — `docs/development/phase-b-stage-2-scoping-note.md` (S0, r1);
S0 review — `verification/review-records/2026-07-05-s0-stage-2-scoping.md` (CLOSED); source pin —
the **R0 Biswas/Suncatcher intake** (`biswas-r0`, pinned, reproduced at R1/R2).

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

Two further **optional / future** tracks — **Track C** (correlation backend / comparator, §8) and
**Track X** (external planning comparable, §9) — are recorded for positioning; **neither gates any
release** and each is gated on a separate director approval.

---

## 2. Ordering (director-directed)

```
S0  approve Stage-2 scope .......................... DONE (merged; review record CLOSED)
R1  reproduce Biswas/Suncatcher v1.2 Part I ........ DONE (reproduced; byte-identical script)
R2  wrap reproduction as an external reference case  DONE (test + ledger + provenance)
S1  two-phase property/correlation registry ........ DONE (registry; no physics)
S2  two-phase acquisition / evaporator
S3  two-phase pressure drop + condenser
S4  coupled two-phase steady-state solver (MAJOR)
S5  two-phase architecture cases
S6  two-phase trade-study extension (MAJOR)
R3  harmonized comparison (MAJOR) .................. requires R2 AND S4–S6
S7  docs + figures
S8  review + release decision (MAJOR) → v1.2.0
```

**Placement.** R1 and R2 sat **after S0 and before S1** (director direction) as a **separable,
dependency-independent** track. **R3 is the dependency join:** it requires **R2** (the reference
case) and **S4–S6** (the two-phase framework), so R3 cannot start until both exist.

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
- **State:** `biswas-r0` — Biswas/Suncatcher source intake, **pinned.**
- **Note:** the exact release/commit identifiers and the as-published inputs live in the R0 intake
  record; R1 reads them from there (no-invention for anything unspecified).

### R1 — reproduce the v1.2 Part I thermal baseline  *(DONE)*
- **Result:** the pinned standalone script (`report_one_thermal.py`, byte-identical, SHA-256 pinned)
  was run unchanged; its self-check passed and it reproduced the author baseline within tolerance
  (`T_rad` 21.34 °C, `T_j` 111.3 / 114.8 °C, `R_th` 0.350 → 0.300 K/W).
- **Claim discipline:** "faithful reproduction of the pinned baseline." **Not** validation, **not**
  ranking, **not** a comparison to our model.

### R2 — wrap as an external reference case  *(DONE)*
- **Result:** vendored byte-identical script + CI-enforced test + `suncatcher-v1.2-part-i-reference`
  ledger entry (external reference; **unranked, unharmonized, unvalidated**) + explicit `PINS.json`
  status fields.
- **Verification:** **c** (tests) + **a** (provenance). Not level d.

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
- **Records are separate:** R1 produced a reproduction review record; R3 (major) produces a
  cross-model + director review record. S-milestones keep their own records per the S0 plan.
- **Mastery-ledger:** R1/R2 opened an **external-reference** entry at `reproduced` (external
  reference — *not* validation, *not* ranking), in a **separate Track-R section**. **No ledger
  entry ranks Suncatcher.** Level d `pending` for every entry.
- **No-regression:** every R and S milestone keeps the Phase A / `v1.1.0` published suites and
  oracle-freeze green (regression baseline `v1.1.0`).

---

## 6. Verification-level summary

| Milestone | New evidence | Review | Ranking? |
|---|---|---|---|
| R0 (done) | pinned intake (a: source pin) | intake note | no |
| R1 (done) | c (reproduction) + a (pinned published values) | review record | **no** |
| R2 (done) | c (tests) + a (provenance) | ledger entry + limitations | **no** |
| S1 (done) | a (sources) + c (registry guards) | intermediate | n/a (registry only) |
| S2–S3 | a/b + c per S0 plan | intermediate | n/a |
| S4 (major) | c baseline recovery + b residual | cross-model + director | n/a |
| S5 | a + c | spot-check | n/a |
| S6 (major) | c engine + inherited physics | cross-model + director | within-model only |
| **R3 (major)** | c comparison + inherited a/b/sensitivity | **cross-model + director** | **harmonized comparison only — no "best"** |
| S7 | docs | intermediate | n/a |
| S8 (major) | full regression vs v1.1.0 | director stop → v1.2.0 | n/a |

---

## 7. Comparable tools & adjacent landscape

Recorded for positioning and possible future reuse. **None is a dependency or a competitor
benchmark** unless a track below (§8–§9) is explicitly approved.

### 7.1 Closest technical overlap — ChEDL `ht` / `fluids`
The open-source **ChEDL** libraries **`ht`** (heat transfer) and **`fluids`** (fluid dynamics)
already implement **many of the correlations this Stage-2 build names** — flow-boiling
heat-transfer coefficients and two-phase pressure-drop multipliers among them. They are the
**closest technical overlap** to the S1 registry.

**What differentiates `orbital-thermal-bounds`** (the raw formulas are shared literature — the
difference is the discipline layer):

- **source-pinned validity ranges** with **no silent extrapolation** (out-of-range → flagged/
  rejected, per the S1 range guards);
- **rank-eligibility** + **provenance labels** (reference / sensitivity / source-required) so no
  value silently enters a ranked case;
- the **orbital-compute context** (radiator-boundary coupling; machine-visible microgravity fields);
- **external reference-case comparison** (Track R).

**Positioning:** treat `ht` / `fluids` as **optional comparator / backend candidates, not direct
competitors.** Whether to use them at all is the subject of **Track C** (§8).

### 7.2 Commercial-adjacent — RotaStellar
**RotaStellar** ([rotastellar.com](https://rotastellar.com/) — "software infrastructure for computing
beyond Earth") appears to model **orbital-compute feasibility**, including **thermal, power, latency,
and cost** constraints. It is a **commercial-adjacent orbital-data-center planning comparable.**

**Positioning:** track as **adjacent, not equivalent** — a different scope (systems / feasibility
planning) from this project's reduced-order, source-pinned thermal bounds + trade study. A
**potential future Track X** API / handoff candidate **if accessible**; **not** benchmarked or
endorsed here.

---

## 8. Track C — Correlation Backend / Comparator  *(future; optional; not gating any release)*

A future, **optional** track to position `orbital-thermal-bounds` against `ht` / `fluids` **without
ceding audit control.**

- **C0 — Survey existing open-source implementations.** Document which S1/S2/S3 correlations are
  already implemented in ChEDL `ht` / `fluids`; identify **licenses, versions, formulas, and whether
  validity ranges are enforced.**
- **C1 — Independent implementation vs wrapped-backend decision.** Decide **per correlation** whether
  `orbital-thermal-bounds` implements locally or wraps/compares against `ht` / `fluids`. **Default:
  local implementation for audit control; optional `ht` / `fluids` comparator for regression checks.**
- **C2 — Comparator tests.** For any overlapping correlation, run **selected in-domain points**
  through both implementations. **Differences are recorded as implementation / comparison evidence,
  not as validation.**
- **C3 — Range-guard layer.** Demonstrate the project's distinct value: the **same / similar formula,
  but source-pinned, range-guarded, rank-aware, and with no silent extrapolation** — the
  authoritative layer stays `orbital-thermal-bounds`.
- **C4 — Dependency policy.** Keep `ht` / `fluids` **optional** unless there is a strong reason to
  make them **core dependencies** (an explicit, separately-approved dependency decision).

---

## 9. Track X — external planning comparable  *(future; speculative; not gating any release)*

A future, **speculative** track: an **API / handoff exploration** with an external orbital-compute
planning tool — candidate **RotaStellar** — **if accessible.** Adjacent, not equivalent; not
benchmarked or endorsed. Gated on a separate approval; nothing here commits to it.

---

## 10. Terminology & claim-discipline notes (authoritative)

Recorded to keep Stage-2 wording precise; these correct earlier framing.

- **"Machine-verified" = executable verification** (evidence levels a/b/c), **not formal proof**
  unless separately proven. *(For accuracy: the Phase A thermodynamic bounds additionally carry an
  independent Wolfram symbolic-proof suite — that is genuine proof. The Stage-2 reduced-order
  two-phase models are **executable-verified only**; do not describe them as proven.)*
- **Suncatcher is an external reference / harmonized-comparison target (Track R), not a final
  baseline.** The reproduced values anchor a *comparison* (R3); they are **not** the project's
  baseline of record and never a "best / worst" verdict.
- **Biswas has a physics model behind the thermal figure.** With Track R's **pinned standalone
  script and reproduction path** (R1 reproduced; R2 wrapped as a tested reference case), it is
  **inaccurate to say the Biswas thermal figure has "no physics model"** — it has a reproducible,
  source-pinned computation. It remains an **external reference** (reproduced, unranked,
  unharmonized), **not validated**.

---

*Living Stage-2 roadmap. Standing rules carried in unchanged: no-invention, oracle-freeze, claim
discipline, cross-model ≠ level d, "certificate" = internal numerical convergence. R1/R2 anchor an
external reference by faithful reproduction only; ranking, if it ever happens, is a harmonized,
assumption-explicit R3 comparison — never a declaration of a best architecture. Tracks C and X are
optional/future and gate nothing.*
