# Phase B, Stage 1 - Chip-to-Radiator Implementation Plan (B0)

> **Status: proposed, forward-looking, provisional, and subject to revision.** This is the
> B0 planning deliverable. It is a *design-intent specification*, not implemented code and
> not a record of validated results. No milestone past B0 is approved for implementation.
> This plan returns for human + cross-model review before any B1 code is written.

**Repository:** orbital-thermal-bounds
**Milestone:** B0 (first milestone governed by the verification workflow)
**Governs:** the Phase B milestone roadmap
([`phase-b-roadmap.md`](phase-b-roadmap.md))
**Verification policy:** [`../VERIFICATION_AND_VALIDATION.md`](../VERIFICATION_AND_VALIDATION.md)
**Working records:**
[`verification/`](https://github.com/dan-lee-odinson/orbital-thermal-bounds/tree/main/verification)

---

## 0. Purpose and scope of this document

B0 produces a written plan only. Its job is to (a) fix the design intent for Phase B,
Stage 1 so that a cross-model reviewer can critique the physics and architecture before any
code exists; (b) resolve the open design questions carried out of Phase A external review;
and (c) open the retrospective mastery-ledger entries that Phase B actually depends on.

This document is a **design-intent specification**. It states decisions, governing
relations, the coupled-solver *contract* (inputs, outputs, convergence, failure), and
acceptance criteria. It deliberately does **not** fix implementation details (data
structures, numerical-method internals, code); those are decided inside each milestone.

Per the agreed scope, milestones **B1-B4 carry full integration blocks** here and
**B5-B8 are summarized**, to be expanded when reached.

---

## 1. What Phase B is, and is not

**Goal.** Extend the model *back from the radiator to the chip*: represent a complete
single-phase chip-to-radiator thermal path (solid spreading + interfaces, a pumped coolant
loop, and radiator coupling) as a reduced-order, coupled steady-state model, and use it to
produce **trade spaces** under explicit assumptions - not a single "best" architecture.

**Terminal condition.** The radiator boundary is **inherited from Phase A** and reused
unchanged as the terminal condition of the chip-to-radiator path (Section 3).

**Stage 1 is single-phase only.** No two-phase physics, capillary/loop heat pipes, PCM,
liquid metals, ionic liquids, or nanofluids. Because Starcloud explicitly describes
two-phase transport "where practical," Stage 1 **cannot** determine the best complete
Starcloud-like transport architecture; a two-phase Stage 2 benchmark is a documented
prerequisite for that question (Section 9).

**Non-goal.** No preprint, no release, and no DOI-affecting change to any Phase A result
without separate approval. Phase B is additive.

---

## 2. No-invention policy (carried from Phase A)

Phase B inherits the project's no-invention / oracle-freeze discipline without exception:

- Every numerical input is tagged **published**, **derived**, **assumed**, or **corrected**,
  with a source. Assumed values are explicitly labelled and never presented as published.
- No Phase A or published-release (`v1.0.1`) value is edited to make a Phase B result work.
- Where a needed value is unavailable (e.g., a proprietary directional conductivity), the
  case is run as a **sensitivity bound**, not a ranked result, and is labelled as such.

---

## 3. Inherited Phase A boundary (core set only)

Per the agreed B0 scope, this plan opens **only** the Phase A boundary assumptions and
results the Phase B plan actually uses - the radiator boundary the transport path
terminates on. It does **not** inherit all of Phase A. The opened retrospective
mastery-ledger entries (the "core boundary set") are:

| Ledger entry | What Phase B uses it for | Source module(s) |
|---|---|---|
| `radiative-equilibrium-and-net-rejection` | terminal rejection law: `q_net`, equilibrium `T`, required area `A` | `radiation.py`, `equilibrium.py` |
| `emitting-face-convention` | two-sided emitting area (emitting = 2 x planform) used in area sizing | `radiation.py` |
| `earth-view-factors` | exact tilted-plate-to-sphere Earth view factor feeding the orbital sink | `mccalip_exact_vf.py` |
| `spectral-separation-of-loads` | short-wave (solar/albedo) vs long-wave (Earth-IR) absorbed flux into the effective sink | `spectral_radiation.py`, `environment.py`, `sink.py` |
| `beta-angle-albedo-model` | sub-point albedo factor and its documented `beta = 90` limitation | `sink.py`, `environment.py` |

Explicitly **not** opened in B0 (not depended on by this plan):
`ai1-starcloud-comparison-assumptions` (opens when B5/B6 compare against the Starcloud
reference) and `three-quarter-temperature-result` (opens only if Phase B uses the
cold-fraction optimum).

The governing relations Phase B reuses (gray, diffuse, isothermal one-node radiator):

```
q_net = epsilon * sigma * (T_rad^4 - T_sink^4)              [W/m^2]
T_rad = ( Q / (epsilon * sigma * A) + T_sink^4 )^(1/4)      [K]
A     = Q / (epsilon * sigma * (T_rad^4 - T_sink^4))        [m^2]   (A = emitting area)
```

`sigma = 5.670374419184429e-8 W m^-2 K^-4` (package `constants.SIGMA_SB`).

---

## 4. Resolved open design questions

These resolve the questions carried from Phase A external review. Each is a **decision for
implementation**, still subject to review.

### 4.1 Coupled solver (not sequential)
The chip-to-radiator path is solved as a **coupled steady-state residual**, not as a
sequential `T_radiator = T_chip - sum(dT)` subtraction. Radiator temperature, loop
temperatures, mass flow, pressure drop, pump power, pump heat, radiator area, and component
masses are the **simultaneous solution** of one residual system (the solver contract is in
Section 5). This is required because pump heat depends on pressure drop, which depends on
fluid properties, which depend on loop temperatures, which depend on the total load - which
includes pump heat. The dependency is circular and must be solved as a fixed point, with
explicit convergence and failure states.

### 4.2 Coolant definitions (single-phase, Stage 1)
The Stage-1 coolant set, each kept single-phase within margin:

- **Ammonia** - liquid, kept subcooled; two-phase ammonia is deferred to Stage 2.
- **Water** - reference well-characterized coolant.
- **Propylene-glycol / water (PGW)** mixture - concentration standardized in B1 (candidate:
  a single freeze-protected concentration with a stated operating range), modelled with an
  incompressible-mixture property backend.
- **CO2** - subject to a mandatory **per-station phase-envelope check**: the 278-308 K band
  straddles the critical temperature (~304.13 K) and pressure (~7.38 MPa), so each station's
  (T, P) must be verified to sit in a single, named phase (liquid or supercritical). There
  is **no blanket "supercritical" assumption**; a station that crosses the envelope is a
  failure state, not a silent extrapolation.

### 4.3 Dual radiator boundary
Two boundary modes, used for different purposes:

- **Fixed effective sink** (constant `T_sink`) - for baseline recovery and debugging. It
  isolates transport behavior from environment variability and is the configuration in which
  the coupled model must reduce to the Phase A result (Section 6, B4).
- **Phase A orbital boundary** (environment-dependent sink: view factors + spectral loads +
  sub-point albedo) - for **reported** trade spaces. Early cases are **not** multiplied by
  the full beta sweep; the beta sweep is applied only where it materially changes a ranking,
  to keep case counts tractable.

### 4.4 Ranking threshold (6 criteria)
A case is **rank-eligible** (admitted to Pareto ranking) only if it meets all six; otherwise
it is shown as a **flagged sensitivity** and never ranked:

1. **Provenance** - all inputs are published/derived (no invented values; Section 2).
2. **Property pedigree** - every property has an authoritative source, a stated valid range,
   and a pinned backend version (B1).
3. **Single-phase margin** - the coolant stays single-phase within margin across the case's
   operating envelope (no freeze / saturation / critical-envelope violation).
4. **Solver health** - the coupled solve converged and satisfies energy closure within
   tolerance (Section 5).
5. **Conductivity basis** - solid conductivity is isotropic, or anisotropic *with cited
   directional data*; otherwise the case is sensitivity-only (Section 4.5).
6. **Containment basis** - containment mass is computed from geometry / hoop-stress with a
   stated allowable stress and safety factor (Section 4.6), not from pressure x volume.

### 4.5 Anisotropic solids (sensitivity-only)
**Aluminium and copper** are the isotropic **reference** materials. **Annealed pyrolytic
graphite (APG)** and **diamond composites** are strongly anisotropic (high in-plane, low
through-plane conductivity); without a specific product/process and its directional data they
are run as **sensitivity bounds only**, never as ranked cases (criterion 5).

### 4.6 Containment mass (hoop-stress, not pressure x volume)
Pressure-containment mass is estimated from thin-wall hoop stress, not the dimensionally
incorrect "pressure x volume." For tubing/vessel of internal radius `r`, operating pressure
`P`, allowable stress `sigma_allow`, wall density `rho_w`, and safety factor `SF`:

```
t      = SF * P * r / sigma_allow                 (thin-wall hoop thickness)
m_wall = rho_w * A_surface * t                     (A_surface = wetted/containment area)
```

`sigma_allow` (with `SF`) and `rho_w` are recorded per material in B1. This yields
mass ~ `P * r` scaling, which is the physically correct dependence.

---

## 5. Coupled-solver contract (design intent)

This is the interface the B2-B4 implementation must satisfy. Internals (the specific
root-finding method, damping, data structures) are deferred to implementation.

**Inputs (case definition).**
- Compute heat load `Q_compute` [W] and junction temperature limit `T_j_max` [K].
- Solid path: geometry + material(s) (Section 4.5), contact resistances.
- Loop: coolant (Section 4.2), geometry (tube diameter, length, count), pump efficiency.
- Boundary: fixed `T_sink` (baseline) or the orbital boundary (reported); emissivity, area
  convention (Section 3).

**Unknowns solved simultaneously.**
`T_rad`, loop inlet/outlet temperatures, mass flow `m_dot`, pressure drop `dP`, pump power
`P_pump`, pump heat `Q_pump`, radiator area `A_rad`, and component masses.

**Residual equations (consistency conditions).**
1. **Radiator energy balance:** `Q_rad = Q_compute + P_pump + Q_other` (the radiator rejects
   the total load, pump heat included).
2. **Radiator rejection law (inherited):** `Q_rad = epsilon * sigma * A_rad *
   (T_rad^4 - T_sink_eff^4)`.
3. **Transport temperature chain:** junction-to-radiator temperature differences equal the
   sum of conduction, contact, film, and fluid-side resistances times the heat they carry -
   imposed as residuals so `T_rad` and intermediate temperatures are *consistent outputs*,
   not a one-directional subtraction.
4. **Hydraulic closure:** `dP`, `P_pump`, and `Q_pump` are consistent with `m_dot` and the
   fluid properties evaluated at the loop temperatures.
5. **Property closure:** all fluid properties are evaluated (pinned backend) at the solved
   loop state.

**Outputs.** The full consistent state above, plus the rank-eligibility verdict (Section 4.4).

**Convergence.** Declared only when the residual norm is below tolerance (tolerance fixed in
B4) and energy closure holds within tolerance.

**Failure states (must fail loudly, never silently extrapolate).**
- non-convergence within the iteration budget;
- any property evaluated outside its recorded valid range;
- `T_rad <= T_sink_eff` (no net rejection possible);
- a coolant phase-envelope violation (freeze / saturation / CO2 critical crossing).

---

## 6. Milestone integration blocks B1-B4 (full)

Each block lists: inherited assumptions, new central claims (ledger-worthy), required
automated checks, required documentation updates, expected verification level (evidence
categories a-d from the policy), open questions/dependencies, and completion criteria.
Recall: category **d** is qualified external *human* review; cross-model review is recorded
separately and is not category d.

### B1 - Property and source registry
- **Inherited:** B0 plan; Phase A `sigma`/emissivity conventions.
- **New central claims:** Stage-1 coolant and solid properties recorded in a property/source
  **registry** with source + valid range + pinned backend version. Individual property values
  are **registry rows, not separate ledger entries.** A mastery-ledger entry is opened only
  for a central *modeling decision* or property family Phase B conclusions materially depend
  on (candidates: the PGW mixture property model; the CO2 phase-envelope treatment; the
  anisotropic-conductivity convention).
- **Required automated checks:** property-range guards; provenance/version recording (pinned
  CoolProp via the existing `fluids.py` extra); independent spot-check of a few values
  against a second source.
- **Required doc updates:** `docs/property-provenance.md` (registry); ledger entries only for
  the material modeling decisions above.
- **Expected verification level:** **a** (authoritative property source) + **c**; **d** only
  for a contested, load-bearing value.
- **Open questions / dependencies:** PGW concentration to standardize; CoolProp coverage for
  PGW (incompressible-mixture backend) and CO2 near-critical region; allowable-stress and
  density sources for containment materials (Section 4.6).
- **Completion criteria:** every rank-eligible property has source + range + pinned version;
  the CO2 phase-envelope guard exists and is unit-tested.

### B2 - Solid thermal network
- **Inherited:** B1 properties (conductivity, contact data).
- **New central claims:** a junction-to-cold-plate resistance network (series conduction +
  contact resistance, optional spreading resistance) with explicit handling of directional
  (anisotropic) conductivity.
- **Required automated checks:** analytic series-resistance comparison; contact-resistance
  sensitivity; an anisotropy direction test (in-plane vs through-plane) confirming
  APG/diamond are flagged sensitivity-only without cited directional data.
- **Required doc updates:** solid-network section of the chip-to-radiator model doc; ledger
  entry for the anisotropic-conductivity convention if not opened in B1.
- **Expected verification level:** **b** (analytic) + **c**.
- **Open questions / dependencies:** contact-resistance values and their source; whether
  spreading resistance is in Stage-1 scope.
- **Completion criteria:** network matches analytic series cases within tolerance;
  anisotropic materials correctly flagged.

### B3 - Single-phase pumped loop
- **Inherited:** B1 properties.
- **New central claims:** loop hydraulics and thermics - mass flow, Reynolds number, friction
  factor (laminar/turbulent), pressure drop, pump power, pump heat into the fluid; and
  freeze / saturation / critical margins per coolant.
- **Required automated checks:** limiting cases (laminar Poiseuille `dP` analytic; turbulent
  vs a named correlation); an independent pressure-drop cross-check; energy-term accounting
  (how much pump power becomes fluid heat).
- **Required doc updates:** loop section of the model doc; ledger entry for the pump-heat /
  hydraulic-closure modeling decision.
- **Expected verification level:** **b** + **c**.
- **Open questions / dependencies:** pump-efficiency model; fraction of pump power deposited
  as fluid heat; friction correlation choice (e.g., Colebrook vs Blasius) and its range.
- **Completion criteria:** limiting-case and independent cross-check pass; phase margins
  enforced as failure states.

### B4 - Radiator coupling (MAJOR milestone)
- **Inherited:** the Phase A radiator law (ledger
  `radiative-equilibrium-and-net-rejection`) and the B1-B3 models.
- **New central claims:** the **coupled steady-state solution** of Section 5 - `T_rad`, loop
  temperatures, `m_dot`, `dP`, `P_pump`, `Q_pump`, `A_rad`, and masses solved together.
  **Radiator and transport temperatures are outputs of the coupled solve**, with pump heat
  added to the rejected load.
- **Required automated checks:** **baseline recovery** (transport losses -> 0 reduces the
  coupled solve to the Phase A equilibrium `T` and area within tolerance, using the fixed
  sink); **energy closure** (`Q_compute + P_pump + Q_other = Q_rad`); **convergence/failure
  behavior** (consistent fixed point or loud failure).
- **Required doc updates:** coupling section of the model doc; B4 review record; update the
  `radiative-equilibrium-and-net-rejection` entry to note Phase B reuse.
- **Expected verification level:** **c** (baseline recovery and energy closure are the key
  gates) + **b** (residual formulation).
- **Open questions / dependencies:** root-finding method and damping; initial-guess strategy;
  convergence tolerance; how the dual boundary (fixed vs orbital) plugs into residual 2.
- **Completion criteria:** baseline recovery, energy closure, and convergence behavior all
  pass; **B4 review record produced** (major milestone).

---

## 7. Milestone summaries B5-B8 (to be expanded when reached)

- **B5 - Architecture cases.** Enumerate coolant x solid paths (ammonia / water / PGW / CO2;
  Al / Cu reference + APG / diamond sensitivity-only). Each case carries its rank-eligibility
  verdict (Section 4.4). Verification: **a + c** per case. Al/Cu are the **reference** cases;
  APG/diamond remain sensitivity-only absent cited directional data.

- **B6 - Trade-study engine (MAJOR).** Assemble cases into trade spaces / Pareto fronts (no
  universal winner). The **software engine requires executable verification (c)** - regression
  tests, reproducible outputs, Pareto-construction checks. Its **physical conclusions inherit
  the source (a), analytic (b), and sensitivity evidence established in B1-B5** and are not
  newly validated by the engine. Every plot distinguishes **verification-supported /
  reference / rank-eligible / parametric / rejected** cases and exposes the dominating
  assumption. B6 review record required.

- **B7 - Documentation and examples.** `docs/chip-to-radiator-model.md`, property and
  trade-study guides, runnable examples. Public docs summarize only conclusions whose ledger
  status justifies it.

- **B8 - Review and release decision (MAJOR).** Full suite + verification suites + examples;
  confirm **no Phase A result and no published-release `v1.0.1` result changed** (regression
  baseline = `v1.0.1`). Require **targeted external (qualified human) review** of the central
  transport/pressure claims **where feasible**; if it cannot be obtained, document the attempt
  and explicitly decide to **narrow the claims**, **defer the release**, or **proceed with a
  recorded limitation**. Verification: **d** where obtainable, plus cross-model review
  recorded separately. B8 review + release record required.

---

## 8. Verification approach for Phase B

- **Cadence applies at major milestones (B0, B4, B6, B8), cross-model reviews, and
  releases.** Intermediate milestones (B1, B2, B3, B5, B7) are grouped or documented only
  when their risk warrants a separate record.
- **Evidence is risk-proportional.** A load-bearing or novel claim warrants at least one of
  {a, b} plus c, with d where stakes justify it; a routine intermediate calculation may rest
  on c alone. Automated execution establishes software verification and reproducibility, not
  physical validation.
- **Ledger discipline.** New central claims get a `verification/mastery-ledger/entries/`
  entry at the milestone that introduces them; status advances only on demonstrated evidence.
  Director-authored explanation and independent derivation are never inferred from passing
  tests.

---

## 9. Deferred to Stage 2 (documented prerequisite)

Two-phase / capillary transport, PCM storage, liquid metals, ionic liquids, nanofluids,
He-Xe working fluids, and experimental materials. A two-phase Stage 2 benchmark is a
**documented prerequisite** before any claim about the best *complete* Starcloud-like
transport architecture.

---

## 10. B0 completion and return for review

B0 is complete when:

1. this plan is written and committed under `docs/development/`;
2. the core-boundary retrospective ledger entries are opened
   (`emitting-face-convention`, `earth-view-factors`, `spectral-separation-of-loads`,
   `beta-angle-albedo-model`; `radiative-equilibrium-and-net-rejection` already populated);
3. a **B0 review record** is opened (draft) and the plan is returned for **human +
   cross-model review.**

**No B1 work begins until this plan is reviewed and approved.** Director-authored
explanations and independent derivations in the opened ledger entries remain `TODO` until
actually completed and approved; they are not inferred from existing tests.
