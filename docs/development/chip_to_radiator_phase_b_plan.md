# Phase B, Stage 1 - Chip-to-Radiator Implementation Plan (B0)

> **Status: proposed, forward-looking, provisional, and subject to revision.** This is the
> B0 planning deliverable - a *design-intent specification*, not implemented code and not a
> record of validated results. No milestone past B0 is approved for implementation. **B1 is
> blocked** until a cross-model re-review of this plan finds no unresolved blocker.

> **Revision 1 (2026-06-21).** Responded to the first B0 adversarial review (3 blockers,
> 6 majors, 1 verified factual error).
>
> **Revision 2 (2026-06-21).** Responds to the B0 **re-review**, which cleared the Revision 1
> changes but raised **two remaining blockers** (a node-and-equation determinacy proof, 4.1a;
> an all-face direct-solar contract, 4.4a) and **one required limitation** (the mass objective
> must stay "modeled component mass" until accumulator mass is closed, 4.8a). All three are
> closed below. Dispositions and the exact changed sections are recorded in the B0 review
> record
> ([`verification/review-records/2026-06-21-b0-phase-b-plan.md`](https://github.com/dan-lee-odinson/orbital-thermal-bounds/tree/main/verification/review-records)).
> Findings requiring a changed physical or mathematical contract were not closed by
> documentation alone.

**Repository:** orbital-thermal-bounds
**Milestone:** B0 (first milestone governed by the verification workflow)
**Governs:** the Phase B milestone roadmap
([`phase-b-roadmap.md`](phase-b-roadmap.md))
**Verification policy:** [`../VERIFICATION_AND_VALIDATION.md`](../VERIFICATION_AND_VALIDATION.md)

---

## 0. Purpose and scope of this document

B0 produces a written plan only. It (a) fixes the design intent for Phase B, Stage 1 so a
cross-model reviewer can critique the physics and architecture before any code exists;
(b) resolves the open design questions; and (c) opens the retrospective mastery-ledger
entries Phase B depends on.

This is a **design-intent specification**: decisions, governing relations, the coupled-solver
*contract* (variables, equations, convergence, failure), and acceptance criteria. It does not
fix implementation internals (data structures, code). Per agreed scope, **B1-B4 carry full
integration blocks; B5-B8 are summarized.**

---

## 1. What Phase B is, and is not

**Goal.** Extend the model back from the radiator to the chip: a complete *single-phase*
chip-to-radiator path (solid spreading + interfaces, a pumped coolant loop, radiator
coupling) as a reduced-order, **coupled steady-state** model, used to produce **trade
spaces** under explicit assumptions - not a single "best" architecture.

**Terminal condition.** The radiator boundary is inherited from Phase A and reused unchanged.

**Stage 1 is single-phase only.** No two-phase, capillary, PCM, liquid metals, ionic liquids,
or nanofluids. Because Starcloud describes two-phase transport "where practical," Stage 1
**cannot** determine the best complete Starcloud-like architecture; a two-phase Stage 2
benchmark is a documented prerequisite (Section 12).

**Non-goal.** No preprint, release, or DOI-affecting change to any Phase A / published-release
(`v1.0.1`) result without separate approval.

---

## 2. No-invention policy and provenance classes

Phase B inherits the no-invention / oracle-freeze discipline. Every numerical quantity carries
a provenance class:

- **published** - stated by a primary source.
- **derived** - computed from published quantities by a stated relation.
- **assumed** - a stated modelling assumption, never presented as published.
- **corrected** - a published value re-derived/corrected with the correction documented.
- **design variable** *(new; review F6)* - a quantity the study **sweeps or optimizes**
  (e.g., tube diameter, mass flow, radiator area). It is neither published data nor an
  invented property; it is an independent variable of the trade study and is labelled as such.

No Phase A or `v1.0.1` value is edited to make a Phase B result work. Where a needed value is
unavailable, the case is a **labelled sensitivity**, not a ranked result.

---

## 3. Inherited Phase A boundary (core set)

B0 opens **only** the Phase A boundary assumptions/results this plan uses. The core-boundary
mastery-ledger entries (revised count: **six**, after review F3/F9):

| Ledger entry | What Phase B uses it for | Source module(s) |
|---|---|---|
| `radiative-equilibrium-and-net-rejection` | terminal rejection law: `q_net`, equilibrium `T`, required area `A` | `radiation.py`, `equilibrium.py` |
| `emitting-face-convention` | two-sided emitting area (= 2 x planform) **valid only when both faces see equal sinks** | `radiation.py` |
| `earth-view-factors` | exact tilted-plate-to-sphere Earth view factor feeding the orbital sink | `mccalip_exact_vf.py` |
| `spectral-separation-of-loads` | short-wave (solar/albedo) vs long-wave (Earth-IR) absorbed flux; IR absorptivity = emissivity (Kirchhoff) | `spectral_radiation.py`, `sink.py` |
| `beta-angle-albedo-model` | sub-point albedo factor and its documented `beta = 90` null (a model limitation, not zero albedo) | `sink.py` |
| `radiator-attitude-and-sun-shielding` *(new; F3/F9)* | the effective-sink model **omits direct solar** and is valid only for a sun-shielded cold face (`assume_sun_shielded=True`) | `sink.py` |

Not opened in B0: `ai1-starcloud-comparison-assumptions` (opens at B5/B6) and
`three-quarter-temperature-result` (only if Phase B uses the cold-fraction optimum).

Inherited governing relations (gray, diffuse, isothermal one-node radiator):

```
q_net = epsilon * sigma * (T_rad^4 - T_sink^4)              [W/m^2]
T_rad = ( Q / (epsilon * sigma * A) + T_sink^4 )^(1/4)      [K]
A     = Q / (epsilon * sigma * (T_rad^4 - T_sink^4))        [m^2]   (A = emitting area)
```
`sigma = 5.670374419184429e-8 W m^-2 K^-4` (`constants.SIGMA_SB`).

---

## 4. Resolved open design questions

### 4.1 Variable taxonomy and square solve modes (review F1, F8)

The coupled path is **not** solved as `T_radiator = T_chip - sum(dT)`. It is a coupled
steady-state residual. To make it *well-posed*, every quantity is assigned one role, and each
solve mode is shown to be **square** (independent equations = state unknowns) once design
variables are fixed.

**Variable roles**

| Role | Examples |
|---|---|
| Case/design inputs (fixed) | `Q_compute`, coolant, solid material(s), tube geometry (`d`, `L`, `N_ch`), cold-plate geometry, emissivity, area convention, boundary mode, low-side fill pressure `P_lo`, safety factor, pump/motor efficiencies |
| **Design variables** (swept or optimized) | one of {`A_rad`, `T_rad`}, one of {`m_dot`, loop `dT`}, optionally `d`, `N_ch` |
| **Solved states** (one residual each) | loop temperatures `T_in`,`T_out`; `T_rad` (when not a design var); pump-heat feedback fixed point; absolute station pressures |
| Derived outputs (algebraic) | `P_pump`, `Q_pump`, Reynolds, friction factor, masses |
| Constraints (inequalities; may go active) | `T_j <= T_j_max`; single-phase margins; `r/t >= 10`; correlation domains; `T_rad > T_sink_eff`; `P_abs > P_sat + margin` |
| Optimization variables / objective (outer loop) | the design variables, minimizing system mass (or area/power) subject to constraints - this is the B6 Pareto loop |

**Closing the count.** For fixed `Q` the radiator law alone gives a one-parameter family of
`(A_rad, T_rad)`; the loop energy balance gives a one-parameter family of `(m_dot, dT)`. Each
family is closed by **declaring one member a design variable**, never by letting the solver
pick arbitrarily. `T_j_max` is an **inequality**; it closes the system only in a sizing mode
where it is explicitly made the active equality `T_j = T_j_max`.

**Solve modes (each square after design variables are fixed)**

| Mode | Fixed design variables | Solved states | Closing equation(s) |
|---|---|---|---|
| **T (temperature-solve / baseline-1)** | `A_rad`, `m_dot` | `T_rad`, `T_in/T_out`, `Q_pump`, `P_abs` | radiator law gives `T_rad`; loop balance gives `dT`; pump-heat fixed point |
| **A (area-solve / baseline-2)** | `T_rad`, `m_dot` | `A_rad`, `T_in/T_out`, `Q_pump`, `P_abs` | radiator law gives `A_rad`; loop balance; pump-heat fixed point |
| **S (sizing to junction limit)** | `m_dot`; sweep one of {`A_rad`,`T_rad`} | the other of {`A_rad`,`T_rad`}, temps, `Q_pump`, `P_abs` | active constraint `T_j = T_j_max` closes the swept variable |
| **O (optimization / Pareto, B6)** | none free | design vars become optimization vars | minimize objective s.t. all constraints; wraps Mode S |

The single circular dependency (pump heat -> properties -> pressure drop -> pump heat, all
through loop temperature) is solved as a **fixed point in loop mean temperature and pressure**
(Section 5), not by a one-directional subtraction.

### 4.1a Node-and-equation determinacy contract (re-review blocker 2.1)

The square-system claim is demonstrated here on the canonical Stage-1 reduced-order topology,
not merely asserted. The model is a single series loop:

```
chip(T_j) --R_cond+R_spread+R_contact--> wall(T_w) --R_film,cp--> coolant cold-plate
cold leg T1  --[cold plate: +Q_chip then +Q_pump]-->  hot leg T2
hot leg T2   --[radiator: -Q_rad]-->  cold leg T1
radiator coolant --R_film,rad--> panel(T_rad) --eps*sigma*A*(T_rad^4 - T_sink^4)--> space
```

**Heat-injection rule (re-review point).** `Q_chip` flows through the junction chain (R1, R2);
**pump heat `Q_pump` does not** - it is added directly to the fluid (R3), downstream of the
junction resistances. The radiator rejects `Q_rad = Q_chip + Q_pump_deposited` (deposition per
the 4.7 control volume). Heat injected at different nodes therefore enters different equations.

**State variables and roles by mode** (`Q_pump`, `dP`, `Re`, `f`, `h/Nu`, `R_film,*`, station
pressures, and masses are **derived algebraically**, not state unknowns; `P_lo` is a fixed
input per 4.3):

| State | Meaning | Mode T | Mode A | Mode S |
|---|---|---|---|---|
| `T_j` | junction temperature | solved | solved | **fixed** = `T_j_max` |
| `T_w` | cold-plate wall temperature | solved | solved | solved |
| `T1` | cold-leg fluid temperature | solved | solved | solved |
| `T2` | hot-leg fluid temperature | solved | solved | solved |
| `T_rad` | radiator panel temperature | solved | **fixed** (design) | solved |
| `A_rad` | emitting area | **fixed** (design) | solved | the **sized** variable |
| `m_dot` | mass flow | **fixed** (design) | **fixed** (design) | **fixed** (design) |

**Residual equations** (`cp` evaluated at the solved loop state; `T_f,cp = T_f,rad = (T1+T2)/2`):

```
R1: T_j - T_w - Q_chip*(R_cond + R_spread + R_contact) = 0      (junction chain; Q_chip only)
R2: T_w - (T1+T2)/2 - Q_chip*R_film,cp                = 0      (wall -> cold-plate film)
R3: Q_chip + Q_pump - m_dot*cp*(T2 - T1)              = 0      (loop energy; pump heat added here)
R4: (T1+T2)/2 - T_rad - Q_rad*R_film,rad             = 0      (radiator film; Q_rad = m_dot*cp*(T2-T1))
R5: Q_rad - sum_faces[eps*sigma*A_face*(T_rad^4 - T_sink_eff,face^4)] = 0   (radiator law)
```

**Count and independence.** In Mode T the unknown vector is
`{T_j, T_w, T1, T2, T_rad}` (5) against `{R1..R5}` (5) - **square**. The Jacobian is
lower-triangular in solve order: R5 fixes `T_rad` (given `A_rad`, `Q_rad`); R4 fixes the
absolute fluid level `(T1+T2)/2`; R3 fixes the split `T2 - T1`; R2 then fixes `T_w`; R1 fixes
`T_j`. Each residual introduces exactly one new temperature, so the system is full-rank away
from the **declared degeneracies** (`T_rad -> T_sink_eff`, `m_dot -> 0`), which are failure
states (Section 5). Mode A swaps `T_rad <-> A_rad` (R5 then solves `A_rad`); Mode S fixes
`T_j = T_j_max` (R1 becomes the closing equation for the swept design variable). All three
modes keep 5 unknowns against 5 residuals.

**Pump-heat feedback is a coefficient, not an extra unknown.** `Q_pump = g(T1, T2, P)` through
the hydraulics (4.7), so R3 is nonlinear but adds no state; the fixed-point iteration of
Section 5 resolves it. The contract above is what B2-B4 must implement; numerical methods are
selected later.

### 4.2 Coolant definitions (single-phase, Stage 1)
- **Ammonia** - liquid, kept subcooled (single-phase margin in 4.3); two-phase deferred.
- **Water** - reference coolant.
- **Propylene-glycol / water (PGW)** - concentration standardized in B1 with the basis
  (**mass- or volume-fraction**) stated explicitly (review F7), modelled with an
  incompressible-mixture backend within its documented composition/temperature range.
- **CO2** - **sensitivity-only in Stage 1** (review F2/F7). The 278-308 K band straddles the
  critical point (NIST: ~304.18 K, ~7.38 MPa). CO2 admission to a ranked case requires a
  dedicated compressible/near-critical treatment that does not yet exist; until then CO2 runs
  as a labelled sensitivity with an explicit saturation/near-critical exclusion band, checked
  **per segment** against absolute pressure (4.3), not per endpoint.

### 4.3 Absolute pressure and fill/accumulator contract (review F2 - blocker)
Hydraulic closure yields pressure **drop**, not absolute pressure; phase, density, inventory,
and containment all need **absolute** pressure. Stage 1 adds an explicit pressure contract:

- **Screening default:** prescribe the **low-side absolute pressure** `P_lo` (a design input)
  at the pump inlet, chosen so the coldest/most-volatile station holds its required
  single-phase margin. Absolute station pressure is `P(s) = P_lo + sum of rises/drops` around
  the loop from that reference; the pump raises pressure by `dP_loop` at steady state.
- **Charge/accumulator closure (higher fidelity, deferred-with-consequence):** an
  accumulator/compliance volume sets system pressure from charge mass, loop volume, and
  temperature via the coolant equation of state. Stage 1 default is prescribed `P_lo`; the
  accumulator model is documented as deferred and its omission is noted as a limitation on
  inventory/expansion accuracy.
- **Phase evaluation** uses absolute `(T, P)` at **every segment** (4.2, 5).

### 4.4 Radiator boundary: canonical orbital balance, per-face, attitude (review F3 - blocker)
Two boundary modes:

- **Fixed effective sink** (`T_sink` constant) - baseline/debugging only; the configuration
  for baseline recovery (5).
- **Orbital boundary** - for reported trade spaces. This revision makes it canonical:
  - **Attitude / shielding (inherited contract, F3/F9):** the radiator cold face is
    **sun-shielded** (anti-solar attitude or shade); **direct solar is omitted** on that face,
    exactly matching `sink.py` (`assume_sun_shielded=True`, hard-guarded). This load-bearing
    assumption is carried explicitly and recorded in `radiator-attitude-and-sun-shielding`.
  - **Per-face energy balance:** a bifacial panel uses **per-face** Earth-IR and albedo with
    per-face view factors (`vf_a`, `vf_b`, as in `mccalip_exact_vf.exact_per_face_view_factors`)
    and per-face absorbed loads. A single `T_sink_eff` is used **only** when both faces see the
    same environment; otherwise rejection is summed per face. This removes the two-area-basis
    ambiguity: the canonical balance is **per-face absorbed-load summation on planform area**,
    converted to the two-sided emitting-area convention by the documented `A_emit = 2 A_plan`
    relation, with **no double counting**.
  - **Averaging statistic (steady solve):** the steady trade study consumes the
    **radiatively-weighted orbit-mean sink** `(<T_sink_eff^4>)^(1/4)` (the grid-free
    `sink.analytic_orbit_averaged_sink`), because rejection scales with `T^4`. A **hot/worst-
    case** sink is available as a sensitivity. Instantaneous sinks are out of Stage-1 steady
    scope (transient is Phase A's domain).
  - The sub-point albedo `beta = 90` null is treated as an **applicability limitation/
    sensitivity**, not a silent zero (`beta-angle-albedo-model`).

### 4.4a Per-face direct-solar contract (re-review blocker 2.2)

The inherited sink omits direct solar and assumes the cold face is shielded. For a **bifacial**
radiator that is insufficient on its own: the plan must state, **per case**, what happens to
the *other* face. Every reported case must declare exactly one of three contracts:

- **C1 - fully-shielded bifacial.** Both emitting faces receive no direct solar (e.g.,
  edge-on-to-Sun or externally shaded). Both faces use the shielded effective sink; the
  two-sided `A_emit = 2 A_plan` convention is valid **only if** both faces also see equal
  Earth/albedo (cross-checked against `emitting-face-convention`).
- **C2 - single cold-face.** Only the shielded face is in the effective-sink boundary; the
  other (potentially sunlit) face is **excluded** from the emitting-area claim, so
  `A_emit = A_plan` (one-sided), not `2 A_plan`.
- **C3 - explicit sunlit-face.** Direct solar is included per face via a **sourced** solar
  absorptivity `alpha_s` and incidence geometry (`max(0, n . s)`). This requires the
  direct-solar term `sink.py` currently omits, so C3 is a **model extension**
  (deferred-with-consequence) and runs **sensitivity/parametric** until that term exists.

**Defaults and no-invention.** Stage-1 reported cases default to **C1** where attitude
supports it, else **C2**. Missing `alpha_s` (needed for C3) makes the case **parametric/
unresolved - never an assumed ranked value**. The chosen contract is recorded per case and is
part of the "common mission/operating envelope" ranking gate (4.8).

### 4.5 Anisotropic solids (sensitivity-only)
Aluminium and copper are isotropic **reference** materials. APG and diamond composites are
anisotropic; without a cited product/process and directional data they are **sensitivity
bounds only**, never ranked (ranking criterion, 4.8).

### 4.6 Containment mass - corrected (review F5)
Corrections to the prior draft:

- **Pressure is gauge:** `P_g = P_abs - P_ambient`; in vacuum `P_ambient ~ 0`, so `P_g ~ P_abs`
  (stated, not assumed silently).
- **Safety factor applied once:** either use a sourced temperature-dependent allowable
  `sigma_allow` that already includes margin, **or** apply `SF` to `sigma_yield`/
  `sigma_ultimate` - never both. The convention is recorded per material in B1.
- **Thin-wall validity:** hoop `t = P_g r / sigma_allow` is used only when `r/t >= 10`;
  otherwise the **Lame thick-wall** relation is used.
- **Completeness:** include closed-end **axial** stress (`sigma_axial = P_g r / 2t`),
  endcaps/joints/fittings, a **minimum manufacturable gauge** `t_min`, and a documented
  launch/pressure-transient allowance - or the result is declared an **ideal shell lower
  bound** and labelled as such.
- **Scaling correction (F5):** my prior text wrongly called "pressure x volume" dimensionally
  invalid. The **normalized** form `m ~ P_g * V * rho_w / sigma_allow` *is* a correct ideal
  mass scaling for geometrically similar thin-wall vessels and is equivalent to the hoop
  `t * rho_w * A_surface` estimate. Both are acceptable; bare `P*V` (energy) is not a mass.

### 4.7 Pump energy control volume (review F4)
A node-level energy contract replaces the ambiguous `P_pump` vs `Q_pump` usage:

```
P_elec  -> motor (eta_motor) -> shaft -> pump (eta_hyd) -> P_hyd = m_dot * dP / rho
losses:  motor loss = P_elec (1 - eta_motor);  hydraulic dissipation -> fluid heat
```
- **Boundary choice (stated per study):**
  - *Whole-spacecraft boundary:* total rejected thermal load = `Q_compute + P_elec` **exactly
    once**; `Q_rad = Q_compute + P_elec + Q_other` and no pump term is double counted.
  - *Fluid-loop boundary:* only the fraction `f` of `P_elec` deposited in the coolant
    (`Q_pump_fluid = f * P_elec`) enters the loop energy balance; the remaining `(1 - f)`
    is rejected elsewhere and tracked in `Q_other`. `f` and its basis are recorded.
- The radiator energy balance (5, residual R2) uses the boundary-consistent total, not a bare
  `P_pump`.

### 4.8 Ranking threshold and mass-accounting boundary (review F6)
A case is **rank-eligible** only if it passes **all** gates; otherwise it is a **flagged
sensitivity**. The gates (expanded from six):

*Provenance & properties*
1. all inputs are published/derived/**design-variable** (no invented values);
2. every property has source + valid range + pinned backend version.

*Physics validity*
3. single-phase margin holds across the case envelope (per-segment, 4.2/4.3);
4. coupled solve converged **and** passes the feasibility gates (5);
5. solid conductivity isotropic, or anisotropic **with cited directional data**;
6. containment computed per 4.6 with `r/t` (or thick-wall) and gauge pressure.

*Comparability & completeness (new, F6)*
7. **common system boundary** - the case uses the same control volume as the cases it is
   ranked against;
8. **mass-accounting completeness** - all components in the declared mass boundary (4.8a)
   have a closure; otherwise the objective is renamed (4.8a);
9. **correlation-domain validity** - all heat-transfer/friction correlations are within their
   stated Reynolds/geometry/temperature ranges (6);
10. **common mission/operating envelope** - same load, sink statistic, and duty assumptions.

**(4.8a) Mass-accounting boundary.** "Total thermal-system mass" **must** close: radiator
panel (areal density x area), coolant inventory, tubing/containment walls, cold plate(s),
manifolds/fittings allowance, accumulator (if modelled), pump + motor mass, structural-support
allowance, and a redundancy factor. If any closure is unavailable, the Pareto objective is
renamed **"modeled component mass"** and is **not** called total thermal-system mass (F6).

**Consequence of the Stage-1 pressure default (re-review 2.3).** Because the Stage-1 default
uses prescribed low-side pressure (4.3) and **defers accumulator/compliance and
thermal-expansion mass**, those closures are missing by construction. Therefore the Stage-1
objective **remains "modeled component mass" and must not be reported as total thermal-system
mass** until the accumulator/compliance and thermal-expansion mass closures exist. This is a
standing limitation, not a per-case choice.

---

## 5. Coupled-solver contract (design intent) (review F1, F8)

Interface the B2-B4 implementation must satisfy; internals deferred.

**Inputs / unknowns / outputs:** per the Section 4.1 taxonomy and the selected solve mode.

**Residual equations (consistency conditions).**
1. **Transport chain:** `T_j - T_rad = Q_path * R_total`, where `R_total` sums conduction,
   spreading (mandatory for ranked cases unless 1-D proven, F7), contact, and convective film
   resistances - imposed as a residual so intermediate temperatures are consistent outputs.
2. **Radiator energy balance:** `Q_rad = Q_compute + Q_pump_boundary + Q_other` (4.7).
3. **Radiator rejection law:** `Q_rad = sum_faces epsilon * sigma * A_face *
   (T_rad^4 - T_sink_eff,face^4)` (per-face, 4.4).
4. **Loop energy balance:** `Q_into_loop = m_dot * cp(T,P) * (T_out - T_in)`.
5. **Hydraulic closure:** `dP`, `P_hyd`, `Q_pump_fluid` consistent with `m_dot` and properties
   at the solved loop state; absolute pressures from `P_lo` (4.3).
6. **Property closure:** all properties evaluated at the solved `(T, P)` with a pinned backend.

**Convergence (F8).** Declared only when the **nondimensionalized** residual vector (each
component scaled by its characteristic magnitude) is below tolerance **and** global energy
closure holds within tolerance. A raw mixed-unit norm is not used.

**Feasibility gates (checked post-convergence; a converged-but-infeasible solution is
rejected, F8).** `m_dot > 0`; correct temperature ordering; `0 < eta <= 1`; Reynolds within
correlation range; `P_abs > P_sat + margin` (and outside the CO2 near-critical band);
`T_j <= T_j_max`; `T_rad > T_sink_eff`; `r/t` valid for the wall model.

**Branch / multiplicity (F8).** Multi-start initial guesses and/or continuation; if multiple
physical roots exist they are reported, not silently chosen.

**Failure states (must fail loudly).** non-convergence; property out of range; phase-envelope
violation; any feasibility gate failed; impossible absolute pressure; containment infeasible.

**Baseline recovery - two separate tests (F8).** With all transport losses and pump heat
zeroed:
- **Mode T:** fixed `(Q, A, sink, epsilon)` recovers Phase A `T_rad` within tolerance;
- **Mode A:** fixed `(Q, T, sink, epsilon)` recovers Phase A `A` within tolerance.
(Phase A fixes one of `T`/`A` and returns the other; the baseline test must do the same, not
solve both freely.)

**Independent checks (F8).** manufactured/hand solutions for both thermal and hydraulic
closures; monotonicity and perturbation tests; multi-start agreement - all before treating
convergence as evidence.

---

## 6. Thermal and hydraulic correlation registry (review F7)

B1/B3 must record, with validity ranges, **both** thermal and hydraulic correlations (the
prior draft specified only pressure drop):

- **Convection / Nusselt** for film resistance: laminar with entry-length (developing-flow)
  correction; turbulent via a named correlation (e.g., Gnielinski or Dittus-Boelter) with its
  Reynolds/Prandtl range.
- **Friction factor:** laminar `f = 64/Re`; turbulent via a named correlation (e.g.,
  Haaland/Colebrook or Blasius) with its range.
- **Minor losses:** K-factors for bends, fittings, and manifolds.
- **Maldistribution:** a parallel-channel flow-maldistribution allowance.
- **Segmented energy balance:** location-dependent heat rate and **per-segment** phase-margin
  evaluation (not endpoint-only).
- **Spreading resistance:** **mandatory** for ranked chip-to-cold-plate cases unless a
  geometry criterion proves 1-D conduction adequate; contact resistance always included.
- **PGW basis:** mass- vs volume-fraction fixed; backend composition/temperature range enforced.

Each correlation carries its domain; correlation-domain validity is ranking gate 9 (4.8).

---

## 7. Milestone integration blocks B1-B4 (full)

Evidence categories a-d are from the policy; **d is qualified external human review**;
cross-model review is recorded separately and is not d.

### B1 - Property, source, and correlation registry
- **Inherited:** B0 plan; Phase A `sigma`/emissivity; the six core-boundary entries.
- **New central claims:** Stage-1 coolant + solid properties (source + range + pinned version);
  the **correlation registry** (6); containment material allowables + density + SF convention
  (4.6); the `P_lo`/accumulator pressure basis (4.3). Property *values* are registry rows;
  ledger entries only for central modeling decisions (PGW mixture basis; CO2 near-critical
  treatment; anisotropic-conductivity convention; pump-deposition fraction `f`).
- **Automated checks:** property-range guards; provenance/version recording (pinned CoolProp
  via `fluids.py`); independent spot-checks; correlation-domain guards.
- **Verification level:** a + c; d for any contested, load-bearing value.
- **Completion:** every rank-eligible property and correlation has source + range + version;
  CO2 phase-envelope guard exists and is unit-tested; pressure basis recorded.

### B2 - Solid thermal network
- **Inherited:** B1 properties.
- **New claims:** junction-to-cold-plate resistance network (series conduction + **spreading**
  + contact), with directional-conductivity handling.
- **Automated checks:** analytic series-resistance comparison; spreading-resistance check;
  contact-resistance sensitivity; anisotropy direction test (APG/diamond flagged
  sensitivity-only absent cited data).
- **Verification level:** b + c. **Completion:** matches analytic cases; spreading mandatory
  for ranked cases unless 1-D proven.

### B3 - Single-phase pumped loop
- **Inherited:** B1 properties + correlation registry.
- **New claims:** loop hydraulics + thermics - `m_dot`, Reynolds, friction, minor losses,
  `dP`, **convective film (Nusselt)**, pump power, and the pump-energy control volume (4.7);
  per-segment phase margins.
- **Automated checks:** laminar Poiseuille `dP` analytic; turbulent vs the named correlation;
  independent `dP` cross-check; **Nusselt** limiting cases; energy-deposition accounting (`f`).
- **Verification level:** b + c. **Completion:** thermal *and* hydraulic limiting-case +
  cross-check pass; per-segment phase margins enforced as failure states.

### B4 - Radiator coupling (MAJOR)
- **Inherited:** Phase A radiator law (`radiative-equilibrium-and-net-rejection`); the orbital
  boundary + attitude/shielding contract (4.4); B1-B3.
- **New claims:** the **coupled steady-state solution** of Section 5 in a declared solve mode,
  with radiator/transport temperatures as **outputs**, pump heat per the 4.7 control volume,
  and per-face orbital rejection.
- **Automated checks:** **two-direction baseline recovery** (Mode T and Mode A); energy
  closure; nondimensional convergence; the full feasibility-gate suite; multi-start/branch
  check.
- **Verification level:** c (baseline + closure + feasibility are the key gates) + b
  (residual formulation). **Completion:** all of the above pass; **B4 review record produced.**

---

## 8. Milestone summaries B5-B8 (to be expanded when reached)

- **B5 - Architecture cases.** Coolant x solid paths (ammonia / water / PGW ranked; **CO2
  sensitivity-only**; Al/Cu reference, APG/diamond sensitivity-only). Each case carries its
  rank-eligibility verdict (4.8). Verification a + c per case.
- **B6 - Trade-study engine (MAJOR).** Assemble cases into Pareto fronts. The **engine**
  requires executable verification (c); its **physical conclusions inherit a/b/sensitivity
  from B1-B5** and are not newly validated by the engine. Objective is **"total thermal-system
  mass"** only if 4.8a closes; otherwise **"modeled component mass."** Plots distinguish
  **verification-supported / reference / rank-eligible / parametric / rejected** and expose the
  dominating assumption. B6 review record required.
- **B7 - Documentation and examples.** Public docs summarize only conclusions whose ledger
  status justifies it.
- **B8 - Review and release decision (MAJOR).** Full suite + verification suites + examples;
  confirm no Phase A and no `v1.0.1` result changed (regression baseline = `v1.0.1`). Require
  **targeted external (qualified human) review** of central transport/pressure claims where
  feasible; if unobtainable, document the attempt and decide **narrow claims / defer release /
  proceed with recorded limitation.** Verification d where obtainable + cross-model recorded
  separately. B8 review + release record required.

---

## 9. Verification approach for Phase B

- Cadence at major milestones (B0, B4, B6, B8), cross-model reviews, and releases; intermediate
  milestones grouped/documented only when risk warrants.
- Risk-proportional evidence; automated execution = software verification + reproducibility,
  not physical validation.
- New central claims get a ledger entry at the introducing milestone; status advances only on
  demonstrated evidence; director-explanation and independent derivation are never inferred
  from passing tests.

---

## 10. Deferred to Stage 2 (documented prerequisite)

Two-phase / capillary transport, PCM, liquid metals, ionic liquids, nanofluids, He-Xe, and
experimental materials. A two-phase Stage 2 benchmark is a documented prerequisite before any
claim about the best *complete* Starcloud-like architecture. **CO2 ranked use** also depends
on a dedicated compressible/near-critical treatment (4.2).

---

## 11. Changes in this revision (summary; full matrix in the review record)

**Revision 2 (re-review closures):**
- Re-review 2.1 (blocker) **fixed**: node-and-equation determinacy contract with a per-mode
  5x5 state/residual table and a rank/independence argument (4.1a).
- Re-review 2.2 (blocker) **fixed**: explicit per-case all-face direct-solar contract C1/C2/C3
  (4.4a); missing `alpha_s` forces a parametric case, never an assumed ranked value.
- Re-review 2.3 (limitation) **stated**: Stage-1 objective stays "modeled component mass" until
  accumulator/thermal-expansion mass is closed (4.8a).

**Revision 1 (original review closures):**
- F1 (blocker) **fixed**: variable taxonomy + square solve modes (4.1, 5).
- F2 (blocker) **fixed**: absolute-pressure + fill/accumulator contract; CO2 demoted to
  sensitivity-only (4.2, 4.3).
- F3 (blocker) **fixed**: canonical orbital boundary, per-face balance, averaging statistic,
  attitude/shielding contract (4.4) + new ledger entry.
- F4 (major) **fixed**: pump-energy control volume (4.7).
- F5 (major) **fixed**: containment corrections + `P*V*rho/sigma` acknowledgement (4.6).
- F6 (major) **fixed**: expanded ranking gates + mass-accounting boundary + design-variable
  provenance class (2, 4.8).
- F7 (major) **fixed**: thermal + hydraulic correlation registry; spreading mandatory (6).
- F8 (major) **fixed**: nondimensional residual, feasibility gates, branch checks, two-
  direction baseline (5).
- F9 (major, documentation) **fixed**: earth-view-factor comparator corrected; attitude/
  shielding ledger entry added.

---

## 12. B0 completion and return for re-review

B0 (revised) is complete when this plan and the updated ledger are committed, the review record
carries the finding-response matrix and the revision commit hash, and the plan is **returned
for a new cross-model review.** **B1 remains blocked until the re-review finds no unresolved
blocker.** Director-authored explanations and independent derivations in the ledger remain
`TODO` until actually completed and approved; they are not inferred from existing tests.
