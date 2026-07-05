# Phase B Stage 2 — S0 Scoping Note (Two-Phase / Boiling Transport)

> **Status: proposed, forward-looking, provisional, and subject to revision.** This is a
> planning document (the Stage-2 "B0-equivalent"). It describes *planned* work; it is **not** a
> record of completed or validated results, and the verification work named here is not a claim
> of completed capability. **No Stage-2 implementation code is authorized by this note.** S0 stops
> for director review; no S1 code proceeds until this note is approved (human director +
> cross-model review, recorded in a review record).

**Repository:** `orbital-thermal-bounds` — https://github.com/dan-lee-odinson/orbital-thermal-bounds
**Director:** Dan Lee-Odinson (project director, sole release gate)
**Baseline:** Phase B **Stage 1 = v1.1.0** (single-phase chip-to-radiator model + trade study; B0–B8 closed)
**Regression baseline for Stage 2:** `v1.1.0` (Stage 2 must not change any Phase A *or* Stage-1 published number)
**Target version:** `v1.2.0` (additive) — `v2.0.0` only if the scope becomes a framing shift or breaking change
**Date:** 2026-07-05 — **director decisions recorded at §9**

---

## 0. Purpose and how to read this note

This note picks **one** primary Stage-2 target from the deferred menu — **two-phase / boiling
transport** — and scopes it to the point where the director can approve or redirect *before any
code is written*. It states the model boundary and the decision behind it, the new central
physical claims, the property/source needs, the verification gates that must exist **before**
code, the allowed/disallowed claims, a milestone plan that mirrors the Stage-1 cadence, and the
director's rulings (§9) now locked in.

It follows the standing project rules without exception: **no-invention** (an unresolved input
becomes a machine-visible blocker/gate, never a guess), **oracle-freeze** (never edit a
published/oracle expected value to pass a test), **claim discipline** (only assert
verification-supported claims), **cross-model review ≠ level d**, and **"certificate" = internal
numerical convergence certificate only**. Verification levels are: **a** (source), **b**
(analytic), **c** (executable), **d** (qualified external human — `pending` for every entry).

---

## 1. Context — why two-phase, and why now

Stage 1 was **single-phase by design**. The Phase B roadmap records the consequence explicitly:
because Starcloud/Suncatcher-class concepts describe two-phase systems "where practical," the
single-phase Stage-1 model **cannot** determine a complete Starcloud-like transport architecture,
and a **future two-phase benchmark is named as a documented prerequisite** for that question.
Two-phase transport is therefore the primary physics extension on the Stage-1 deferral menu, and
it is the one whose absence most limits what the trade study is allowed to conclude.

Stage 1 already leaves the right seams: the single-phase pumped loop (`pumped_loop.py`) already
tracks **saturation margin** (it deliberately stays subcooled), the coupled solver
(`coupled_model.py`, Modes T/A) already solves the loop and the radiator boundary **together** as a
system residual, and the fluid backend (`fluids.py`) is already per-`(T,P)` on a pinned CoolProp.
Stage 2 generalizes the loop state from "subcooled liquid" to "liquid → two-phase mixture →
condensed liquid," a direct extension of existing machinery rather than a new architecture.

---

## 2. The decision — model boundary (ADR-style)

**Decision.** Scope Stage 2 as a **reduced-order, single-component, mechanically-pumped
*flow-boiling* loop extension** of the Stage-1 pumped loop (menu option 2 — the
boiling / quality / pressure-drop extension). The coolant is allowed a finite vapor quality in the
chip-acquisition (evaporator) section, is transported as a two-phase mixture, and is fully
condensed back to liquid before the pump. Capillary / heat-pipe / loop-heat-pipe architectures
(option 3) and any broader multi-fluid screening as a stand-alone deliverable (option 1) are
**explicitly deferred** and named below.

### Options considered

**Option 1 — Limited two-phase *screening* model.** A coarse "does two-phase help at all" pass
(latent vs sensible capacity), no coupled solve. *Pros:* fastest, low risk. *Cons:* almost no new
trade-space content; cannot be ranked; would not retire the roadmap's named prerequisite.
**Rejected as the primary target** — but its value is preserved by making the **first build
milestone (S2) deliberately screening-level** before full coupling.

**Option 2 — Flow-boiling / quality / pressure-drop extension (CHOSEN).** Generalize the pumped
loop to carry vapor quality `x ∈ [0,1]`; add flow-boiling heat transfer, a critical-heat-flux
(dryout) limit, two-phase pressure drop, and a condenser that rejects latent heat to the Phase A
radiator boundary. *Pros:* directly reuses the coupled-solver architecture; produces genuinely new
Pareto content (pump power, fluid inventory, radiator area vs heat load all change materially with
two-phase operation); clean limiting-case recovery to Stage 1 (`x → 0`). *Cons:* the two new
physics areas (boiling heat-transfer coefficient and two-phase pressure drop) are correlation-heavy
and carry real **microgravity** applicability uncertainty — treated as sensitivity-flagged, not
asserted (§9.2).

**Option 3 — Capillary / heat-pipe-like comparison model.** Passive, capillary-driven; a genuinely
different architecture with wick/evaporator/condenser and capillary-limit physics. *Pros:* closest
to some flight two-phase hardware. *Cons:* a larger departure from the Stage-1 pumped-loop
architecture, gated on wick/geometry parameters not currently in hand. **Deferred** to a later
Stage-2 milestone or Stage 3; recorded here as a named future branch, not scoped now.

### Trade-off summary

| Dimension | Option 1 (screening) | **Option 2 (flow-boiling)** | Option 3 (capillary/heat-pipe) |
|---|---|---|---|
| New trade-space content | minimal | **substantial** | substantial |
| Reuse of Stage-1 solver | partial | **high** | low |
| Limiting-case recovery to Stage 1 | weak | **clean (`x→0`)** | none (different architecture) |
| New source/geometry dependence | low | medium (correlations) | **high (wick/geometry)** |
| Microgravity uncertainty exposure | low | medium–high (flagged) | high |
| Risk of over-claiming | low | medium (controlled by gates) | high |

### Consequences

- **Easier:** answering "how does allowing boiling change the pump-power / radiator-area /
  fluid-inventory trades?" within the existing coupled-solver and trade-study framework.
- **Harder:** every new correlation must carry a cited validity range and a microgravity caveat;
  cases exceeding the CHF margin, failing to fully condense before the pump, or sitting on an
  unstable branch of the internal characteristic must be **rejected or de-ranked**, not ranked.
- **To revisit:** capillary/heat-pipe architectures (option 3); multi-fluid two-phase breadth; and
  whether a later stage attempts the two-phase benchmark against Biswas/Suncatcher (§7).

---

## 3. Math model (reduced-order, stated for review — not yet implemented)

**State.** The transported loop state generalizes from subcooled `(T, P)` to specific enthalpy `h`
and pressure `P`, with vapor quality `x = (h − h_f(P)) / h_fg(P)` clamped to the physical domain
`x ∈ [0, 1]`. Saturation properties `T_sat(P)`, `h_f`, `h_g`, `h_fg`, `ρ_f`, `ρ_g`, `μ_f`, `μ_g`,
and surface tension `σ` come from the **pinned CoolProp** backend; triple-point and critical bounds
are enforced (no blanket "supercritical" — the discipline applied to the CO₂ 278–308 K straddle in
B0). **Reference coolant: ammonia (primary); water (secondary); all others source-gated** (§9.1).

**Heat acquisition (evaporator / cold plate).** Energy balance `Q_chip = ṁ (h_out − h_in)`. If exit
enthalpy crosses `h_f`, the section is two-phase with exit quality `x_out`; the boiling
heat-transfer coefficient comes from a **cited flow-boiling correlation** (e.g. Chen-type
superposition of nucleate-boiling and forced-convective contributions) used **only inside its
stated validity range**. Wall superheat follows from `ΔT_wall = q'' / h_boil`.

**Dryout / critical-heat-flux gate (director margin, §9.5).** A cited CHF correlation sets the
maximum local heat flux. Cases are banded by `q'' / CHF`:
- **`q'' / CHF ≤ 0.5` → rank-eligible.**
- **`0.5 < q'' / CHF < 1` → parametric / sensitivity only — reported, *not ranked*.**
- **`q'' / CHF ≥ 1` → dryout → rejected.**

This is a **modeling margin, not flight certification**.

**Two-phase pressure drop (director choice, §9.4).** Separated-flow model:
`ΔP_2φ = φ² · ΔP_f,liq + ΔP_accel + ΔP_static`, with the two-phase multiplier `φ²` from the
**Lockhart–Martinelli / Chisholm** family as the **reference**, and **Friedel retained as a named
sensitivity**. `ΔP_accel` is the momentum change across the density ratio `ρ_f/ρ_g`; `ΔP_static ≈ 0`
in microgravity (a recorded modeling decision, not a silent assumption). **Limiting case:** as
`x → 0`, `φ² → 1` and `ΔP_2φ` recovers the Stage-1 single-phase `ΔP`.

**Condenser.** Rejects `Q_cond = ṁ (h_in − h_out)` (including latent heat) to the Phase A radiator
law at `T_sat(P_cond)`. **Constraint (operational gate):** the pump inlet must be liquid with a
subcooling margin — incomplete condensation (`x > 0` at pump inlet) rejects the case.

**Coupled solution.** Loop enthalpy/quality field, pressure field, `T_sat`, radiator temperature
and area, and pump power are solved **together as the system residual** (the Stage-2 analog of the
B4 coupled solve), **not** by sequential `T_radiator = T_chip − Σ dT`. Pump heat is added to the
load the radiator must reject. **Energy closure:** `Q_chip + P_pump = Q_cond` at steady state
(adiabatic transport lines), with the loop enthalpy balance closing to tolerance.

**Flow stability and solution uniqueness (recorded limitation + validity guard).** Two-phase
pumped loops admit dynamic instabilities — **Ledinegg (flow-excursion), density-wave, and
pressure-drop oscillations** — and the internal `ΔP`-vs-`ṁ` characteristic can be non-monotonic, so
a steady operating point may be **non-unique**. This reduced-order **steady-state** model does not
resolve dynamic instabilities; they are **recorded limitations, out of scope for the S-milestones,
and not claimed as modeled**. As a tractable guard, a **static Ledinegg criterion** (sign of the
internal-characteristic slope at the operating point) is included as a **domain-validity check**,
and any **non-unique** steady solution must be **detected and reported (fail loudly), never
silently selected**.

**Microgravity caveat (load-bearing, §9.2).** Nearly all flow-boiling heat-transfer and two-phase
pressure-drop correlations are derived from 1-g terrestrial data. Per the director ruling, these
**cited 1-g correlations are used as the reference** with an **explicit microgravity-applicability
limitation carried in every reported result**; microgravity-specific sources are **not required as
hard blockers up front**, and **no microgravity validation is claimed**.

---

## 4. New central claims (named here; ledger entries opened at the milestone that introduces each)

Per roadmap §5, a `verification/mastery-ledger/entries/` entry is created **at the milestone that
introduces the claim**, and the index status advances only on demonstrated evidence. S0 **names**
the anticipated entries; it does **not** create any at `reproduced`.

1. **Two-phase flow-boiling heat acquisition** — vapor quality, boiling heat-transfer coefficient,
   and the CHF/dryout rejection bands (§3). *(introduced at S2)*
2. **Two-phase pressure drop** — Lockhart–Martinelli/Chisholm reference multiplier + acceleration
   term; Friedel sensitivity; microgravity static-term decision. *(introduced at S3)*
3. **Coupled two-phase steady-state solution** — loop + condenser + radiator solved together;
   liquid-at-pump constraint; static Ledinegg / non-uniqueness guard; energy closure with pump
   heat in the rejected load. *(introduced at S4 — MAJOR)*

---

## 5. New property / source needs (no-invention: registry rows or blockers, never guesses)

Each item is either a **registry row** (source + range + pinned version, per B1's model) or, if
unavailable, a **machine-visible blocker/sensitivity** — never a guessed value.

- **Saturation property backend** for the two-phase coolant(s) — **ammonia (reference)**; **water
  (secondary)**; **all others source-gated** (§9.1). Pin the CoolProp version.
- **Flow-boiling heat-transfer correlation** — cited, with mass-flux / quality / pressure validity
  range recorded.
- **Two-phase pressure-drop correlation** — **Lockhart–Martinelli/Chisholm (reference)** and
  **Friedel (sensitivity)**, each cited with validity range.
- **Critical-heat-flux correlation** — cited, with validity range; feeds the `q''/CHF ≤ 0.5`
  rank-eligibility band (§3, §9.5).
- **Flow-regime / onset-of-boiling checks and a static Ledinegg criterion** — at minimum
  validity-domain checks even where regime-specific modeling is deferred.
- **Channel geometry** (hydraulic diameter, length, count) and **surface tension `σ`** — geometry
  parameters are **source-required**, not invented.

---

## 6. Verification gates — defined **before** any code (the S2–S4 test plan)

Acceptance conditions, written now so implementation is measured against them. They map to the
director's constraints.

1. **Limiting-case recovery.** As `x → 0` (subcooled), the two-phase loop reproduces the Stage-1
   single-phase pumped-loop outputs within tolerance (`φ² → 1`, boiling HTC → single-phase forced
   convection) — the Stage-2 analog of B4 baseline recovery. *(unit + integration)*
2. **Energy conservation.** `Q_chip + P_pump = Q_cond`; the loop enthalpy balance closes across
   latent + sensible terms. *(integration)*
3. **Pressure / quality / domain validity.** `0 ≤ x ≤ 1` enforced; `P_triple < P < P_crit`;
   `T_sat(P)` monotonic; no blanket supercritical treatment; static **Ledinegg** slope checked;
   **non-unique** steady solutions detected and reported. *(unit)*
4. **Correlation validity ranges.** Every correlation call is range-checked against its cited
   window; out-of-range → flagged or rejected, **never** silently extrapolated. *(unit)*
5. **Explicit rejection / de-ranking of out-of-domain cases.** `q''/CHF ≥ 1` (dryout), incomplete
   condensation at the pump inlet, unstable (negative-slope) operating point, or regime/pressure/
   quality outside the correlation domain → **rejected**; `0.5 < q''/CHF < 1` → **sensitivity only,
   not ranked**. Reported in all cases, never silently ranked. *(integration + trade-study)*
6. **No regression.** The full suite plus the Phase A / `v1.1.0` published suites and the
   oracle-freeze remain green; the frozen oracle points (AI1 `337.1 K`, edge-on `+6.349684 K`) are
   unchanged. *(release gate; regression baseline = `v1.1.0`)*

**Verification level by claim type.** Engine/solver code: **c** (executable). Each new central
two-phase physical claim: at least one of {**a** source, **b** analytic-limiting} **+ c**, with
**d** (qualified external human) as the standing target — **`pending`**. **Cross-model (GPT-5.5)
adversarial review is mandatory at the majors (S4, S6, S8)**, recorded separately, and **does not
count as level d**.

---

## 7. What will and will not be claimed

**Allowed (Stage-2 target claim).** A **verification-supported, reduced-order, single-component,
exploratory flow-boiling extension** of the Stage-1 chip-to-radiator model, with documented
assumptions, executable tests, review records, and explicit limitations; trade outputs that
distinguish **verification-supported / reference / rank-eligible / parametric / rejected** cases and
surface the dominating assumption.

**Disallowed (must not appear).** externally validated; flight-grade; hardware-validated; qualified
for spacecraft design; **flight-grade heat-pipe / loop-heat-pipe design**; validated two-phase
transport/pressure physics by qualified human review; **microgravity-validated boiling**; total
thermal-system mass closure; "best" architecture; **complete Starcloud / Suncatcher architecture
judgment**.

**Biswas / Suncatcher (future connection only, §9.7).** A later two-phase benchmark *could* connect
to the pinned-but-unreproduced `biswas-r0` intake once two-phase machinery exists. Per the director
ruling, **Suncatcher reproduction is NOT part of S0 or Stage-2** unless separately approved;
`biswas-r0` stays pinned/unreproduced/unranked. This note records only the connection point.

---

## 8. Milestone plan (mirrors the Stage-1 B0–B8 cadence; majors marked)

| Milestone | Scope | Type / review |
|---|---|---|
| **S0** (this note) | Scoping: model boundary, gates, claims, director decisions | **MAJOR** — director + cross-model; **stop** |
| S1 | Two-phase property/correlation **registry** (saturation backend, boiling HTC, LM/Chisholm + Friedel ΔP, CHF) with provenance + validity ranges | intermediate (a + c; d for contested) |
| S2 | Two-phase **acquisition/evaporator** module — quality, boiling HTC, **CHF/dryout bands** (screening-level first) | intermediate (b + c) |
| S3 | Two-phase **pressure drop** + **condenser** + liquid-at-pump constraint | intermediate (b + c) |
| **S4** | **Coupled two-phase steady-state solver** — baseline recovery, energy closure, Ledinegg/uniqueness guard, convergence/failure | **MAJOR** — cross-model; **stop** |
| S5 | Two-phase **architecture cases** — which coolants are rank-eligible (ammonia reference; water; others source-gated) | spot-check (a + c) |
| **S6** | **Two-phase trade-study extension** — updated/new Pareto fronts (single- vs two-phase) | **MAJOR** — cross-model; **stop** |
| S7 | **Docs + figures** — synthesis update, Pareto PNGs, end-to-end example | intermediate |
| **S8** | **Review + release decision** — full regression vs `v1.1.0`; change report; version bump to `v1.2.0` | **MAJOR (director)** — **stop** |

Each milestone: small reviewable commits, one PR per milestone, adversarial (cross-model) review at
each major, a ledger entry + docs per new central claim, and the by-hand Codespaces application
protocol every time. The AI-assistance checkbox stays **unchecked** (director attestation).

---

## 9. Director decisions (resolved at the S0 review — 2026-07-05)

Recorded rulings; these supersede the draft's open questions and govern S1+.

1. **Reference coolant.** **Ammonia primary; water secondary; all others source-gated.**
2. **Microgravity policy.** Use **cited 1-g correlations as the reference** with **explicit
   microgravity-applicability limitations**. Microgravity-specific sources are **not** required as
   hard blockers up front; **no microgravity validation is claimed**.
3. **Condenser/radiator boundary.** Confirm the **Stage-1/B0 dual-boundary rule**: **fixed
   effective sink** for baseline/debug; **Phase A orbital boundary** for reported trade spaces.
4. **Two-phase pressure-drop family.** **Lockhart–Martinelli/Chisholm = reference**; **Friedel =
   named sensitivity**.
5. **CHF/dryout margin.** Ranked cases require **`q'' / CHF ≤ 0.5`**. Above that: **reject or mark
   sensitivity — do not rank**. This is a **modeling margin, not flight certification**.
6. **Version target.** **`v1.2.0` additive by default**; **`v2.0.0` only** if scope becomes a
   framing shift or breaking change.
7. **Suncatcher scope.** **Out of scope for Stage-2 S0.** Record only the future connection point;
   Biswas/Suncatcher remains **pinned, unreproduced, and unranked** unless separately approved.

---

## 10. S0 acceptance / completion criteria

- **No code written** (planning only).
- Model boundary decided and justified (§2); math model stated (§3); new central claims named
  (§4); property/source needs listed as registry rows or blockers (§5); verification gates defined
  **before** code (§6); allowed/disallowed claims fixed (§7); director decisions recorded (§9).
- **Returned for human director + cross-model review**; the review record at
  `verification/review-records/2026-07-05-s0-stage-2-scoping.md` records the reviewed commit SHA +
  disposition **before any S1 code**.
- **No S1 work until this note is approved and the review record is CLOSED.**

---

*Prepared as the first Stage-2 action per the Stage-2 handoff §9. Structure informed by the
`engineering:architecture` (ADR decision spine) and `engineering:testing-strategy` (gate/test-plan
framing) skills; recorded here for the handoff's skills log. All standing rules (no-invention,
oracle-freeze, claim discipline, cross-model ≠ level d, "certificate" = internal numerical
convergence) carried in unchanged.*
