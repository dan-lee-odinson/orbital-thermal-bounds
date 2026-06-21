# Phase B Roadmap - Chip-to-Radiator Thermal Transport Trade Study

> **Status: proposed, forward-looking, provisional, and subject to revision.** This roadmap
> describes planned work; it is not a record of completed or validated results, and planned
> verification work here is not a claim of completed capability. Milestones B1-B8 are not
> approved for implementation; B0 (a written plan) is the next step and returns for human +
> cross-model review before any B1 code.

**Repository:** orbital-thermal-bounds
**Relation to Phase A:** Phase A modelled the radiator boundary (heat reaches a radiator
and is rejected). Phase B extends the model *back to the chip* and reuses the Phase A
radiator law as its terminal condition.

---

## 1. Goal and non-goal

**Goal.** Compare complete chip-to-radiator thermal architectures (coolant loops, solid
spreaders, interfaces, radiator coupling) under explicit assumptions, as a reduced-order
trade study that produces trade spaces, not a universal winner.

**Non-goal.** No preprint, release, or DOI-affecting change without separate approval. No
two-phase physics, PCM, liquid metals, ionic liquids, or nanofluids in Phase B, Stage 1.

---

## 2. Lightweight, risk-proportional milestone workflow

This roadmap is governed by the verification policy in
[`VERIFICATION_AND_VALIDATION.md`](../VERIFICATION_AND_VALIDATION.md) and the working
records under
[`verification/`](https://github.com/dan-lee-odinson/orbital-thermal-bounds/tree/main/verification)
(version-controlled, excluded from this site).

**Major milestones are B0, B4, B6, and B8.** Full review records are required only at those
major milestones, at formal cross-model reviews, and at releases - never per development
step. The intermediate milestones (B1, B2, B3, B5, B7) may be grouped, or documented with a
separate record only when their risk warrants it.

### 2.1 Major-milestone cadence

For each **major milestone** (B0, B4, B6, B8), a cross-model review, or a release:

1. **implement** the scoped change;
2. **run focused tests** for the change;
3. **commit and push**;
4. **confirm automated checks** (CI) pass on the pushed commit;
5. **record the reviewed commit** (hash + branch) in a review record;
6. **conduct cross-model review** where warranted by consequence/uncertainty;
7. **resolve or document findings**;
8. **update affected ledger entries** (`verification/mastery-ledger/`);
9. **declare the milestone stable.**

Automated checks establish software behavior and reproducibility only; they do not
validate physical assumptions (see the policy's evidence categories a-d).

### 2.2 Per-milestone integration blocks live in the B0 plan

The **full per-milestone integration block** for each milestone - inherited assumptions,
new central physical claims, required automated checks, required documentation updates,
expected verification level, open questions/dependencies, and completion criteria - is
produced in the **B0 implementation plan**
(`docs/development/chip_to_radiator_phase_b_plan.md`). This roadmap retains only the
**concise milestone summaries** in section 3.

### 2.3 Expected verification level by claim type

- Routine intermediate calculation: **c** (executable) only.
- Reused Phase A boundary: inherit existing evidence; re-run **c**; no new derivation.
- New central physical claim driving a trade-space conclusion: at least one of **{a, b}**
  plus **c**, with **d** (qualified external *human* review) where the stakes justify it.

**Cross-model review** (for example, a second model auditing the work) is recorded
*separately*. It strengthens error detection and supports category **c**, but it does
**not** count as category **d**, and two AI systems agreeing counts as a single category.

---

## 3. Milestones (concise summaries)

The full integration block for each milestone is written in the B0 plan (section 2.2). B0
is the **first milestone governed by this workflow**. Major milestones are marked.

### B0 - Inspect and plan (MAJOR; FIRST GOVERNED MILESTONE; stop for approval)
- **Inherited scope:** **only the Phase A boundary assumptions and results actually used by
  the Phase B plan** (the radiator-boundary law and the specific environment/sink
  assumptions the transport model reuses) - **not** all of Phase A. The retrospective ledger
  baseline opens only the entries this plan depends on.
- **New central claims:** none (planning only).
- **Required automated checks:** none (no code).
- **Required doc updates:** produce `docs/development/chip_to_radiator_phase_b_plan.md`
  (carrying the full per-milestone integration blocks); open the retrospective ledger
  entries this plan depends on.
- **Expected verification level:** n/a (plan); the plan itself is reviewed (human director +
  cross-model), recorded in a review record.
- **Open questions to resolve in B0 (carried from external review):**
  - coupled solver (residual/iteration with convergence + failure states), NOT a sequential
    `T_radiator = T_chip - sum(dT)`;
  - coolant definitions: propylene-glycol/water mixture (concentration + range); CO2 per-
    station phase-envelope check (278-308 K straddles the critical temperature - no blanket
    "supercritical");
  - dual radiator boundary: fixed effective sink for baseline/debugging; Phase A orbital
    boundary for reported trade spaces; do not multiply early cases by the beta sweep;
  - ranking threshold (6 criteria) separating rank-eligible/Pareto cases from flagged
    sensitivities;
  - containment mass via geometry/hoop-stress relations, not pressure x volume;
  - anisotropic solids (APG, diamond composite) sensitivity-only; Al/Cu anchor the
    reference cases.
- **Completion criteria:** plan written; ledger baseline opened; returned for human +
  cross-model review; **review record produced. No B1 work until approved.**

### B1 - Property and source registry
- **Inherited:** B0 plan.
- **New claims:** individual coolant/solid property values are recorded in the
  property/source **registry** (`docs/property-provenance.md`) with source, range, and
  pinned-version provenance - they are **registry rows, not separate ledger entries.** A
  mastery-ledger entry is created **only for a central modeling decision or a property family
  that Phase B conclusions materially depend on** (e.g., the chosen coolant property model,
  or a property whose uncertainty drives a ranking).
- **Automated checks:** property-range guards; provenance/version recording (pinned CoolProp).
- **Verification level:** a (authoritative property source) + c; d for any contested,
  load-bearing value. **Completion:** every rank-eligible property has source + range +
  recorded version in the registry.

### B2 - Solid thermal network
- **New claims:** series + contact resistance; directional (anisotropic) conductivity.
- **Automated checks:** analytic series-resistance comparison; anisotropy direction tests.
- **Verification level:** b (analytic) + c. **Completion:** matches analytic cases in tolerance.

### B3 - Single-phase pumped loop
- **New claims:** mass flow, Reynolds, friction factor, pressure drop, pump power, freeze/
  saturation/critical margins.
- **Automated checks:** limiting cases; independent pressure-drop cross-check; energy terms.
- **Verification level:** b + c. **Completion:** limiting-case + cross-check pass.

### B4 - Radiator coupling (MAJOR)
- **Inherited:** the Phase A radiator law (ledger:
  `radiative-equilibrium-and-net-rejection`) and the B1-B3 property/network/loop models.
- **New claims:** a **coupled steady-state solution** in which loop temperatures, fluid
  properties, mass flow, pressure drop, pump heat, radiator temperature, radiator area, and
  component masses are solved **together as the simultaneous solution of the system
  residual**. **Radiator and transport temperatures are outputs of this coupled solution,
  not a sequential `T_radiator = T_chip - sum(dT)` subtraction.** Pump heat is added to the
  load the radiator must reject.
- **Automated checks:** **baseline recovery** (transport losses off -> Phase A radiator
  model within tolerance); **energy closure** (`Q_compute + P_pump + Q_other = Q_radiator`);
  **convergence/failure behavior** (the solver reaches a consistent fixed point or fails
  loudly).
- **Verification level:** c (baseline recovery + energy closure are the key gates) + b for
  the residual formulation. **Completion:** baseline recovery, energy closure, and
  convergence behavior all pass; **review record produced.**

### B5 - Architecture cases
- **New claims:** ammonia / water / propylene-glycol-water / CO2 (per-station phase margin) +
  Al / Cu / APG / diamond-composite paths.
- **Verification level:** a + c per case; APG/diamond remain **sensitivity-only** unless a
  specific product/process with directional data is cited. **Completion:** each rank-eligible
  case meets the B1 ranking threshold (Al/Cu are the **reference** cases); others are flagged
  sensitivities.

### B6 - Trade-study engine (MAJOR)
- **New claims:** trade spaces (no universal winner). Minimum Pareto set: total thermal-
  system mass vs heat load; pump power vs fluid temperature rise; radiator area vs achievable
  radiator temperature; chip-temperature margin vs heat load; fluid inventory + containment
  mass vs operating pressure; Pareto mass vs parasitic power with rejected cases identified.
- **Software vs physical evidence:** the trade-study **engine** (the software that assembles
  cases, solves them, and builds Pareto fronts) requires **executable verification (c)** -
  regression tests, reproducible outputs, and Pareto-construction checks. Its **physical
  conclusions are not newly validated here**; they **inherit the source (a), analytic (b),
  and sensitivity evidence established in B1-B5**. The engine verifies that conclusions are
  *assembled* correctly, not that the underlying physics is independently validated.
- **Verification level:** c for the engine; inherited a/b/sensitivity for the physics. Every
  plot distinguishes **verification-supported / reference / rank-eligible / parametric /
  rejected** cases and exposes the dominating assumption.
- **Completion:** Pareto outputs produced; assumptions surfaced; no unjustified ranking;
  **review record produced.**

### B7 - Documentation and examples
- **Doc updates:** `docs/chip-to-radiator-model.md`, property/trade-study guides, examples.
  Public docs summarize only conclusions whose ledger status justifies it.

### B8 - Review and release decision (MAJOR; stop for human review)
- **Automated checks:** full suite + verification suites + examples; confirm **no Phase A
  result and no published release `v1.0.1` result changed** (regression baseline = `v1.0.1`).
- **Doc updates:** change report; review record; ledger statuses updated.
- **External review:** require **targeted external (qualified human) review** of the central
  transport/pressure claims **where feasible**. If such review **cannot be obtained**,
  document the attempt and **explicitly decide** whether to (i) **narrow the claims**, (ii)
  **defer the release**, or (iii) **proceed with an explicit, recorded limitation.**
- **Verification level:** d (qualified external human review) where obtainable; cross-model
  review in addition, recorded separately. **Completion:** human review (or a recorded
  inability + decision); explicit release decision; **review record produced.**

---

## 4. Deferred to later stages

Two-phase / capillary systems, PCM storage, liquid metals, ionic liquids, nanofluids,
He-Xe, and experimental materials. **Note:** because Starcloud explicitly describes
two-phase systems "where practical", **Phase B, Stage 1 (single-phase only) cannot
determine the best complete Starcloud-like transport architecture**; a future two-phase
benchmark is a documented prerequisite for that question.

---

## 5. How this roadmap relates to the working records

- New central claims get a `verification/mastery-ledger/entries/` entry at the milestone
  that introduces them; the index status advances only on demonstrated evidence.
- Each **major milestone (B0, B4, B6, B8)**, each formal cross-model review, and the release
  produce a `verification/review-records/` record.
- This roadmap stays provisional; results migrate into public docs only after their
  evidence and ledger status justify it.
