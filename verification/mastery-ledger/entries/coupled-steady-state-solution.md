> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Mastery ledger: Coupled steady-state chip-to-radiator solution (R1-R5)

- **Entry id:** `coupled-steady-state-solution`
- **Current status:** `reproduced` (code) -- director explanation and independent derivation
  `TODO`; **cross-model review required (major milestone B4)**
- **Last updated:** 2026-07-03
- **Opened by:** B4 (Phase B radiator coupling)

## Physical question
Given a compute load, coolant, solid path, tube/cold-plate/radiator geometry, mass flow, and
orbital sink, what are the coupled steady-state junction, wall, loop, and radiator temperatures
(Mode T) or the required radiator area (Mode A), with pump heat added to the rejected load?

## Why it matters
This is the milestone that makes the chip-to-radiator model *coupled*: radiator and transport
temperatures are the **simultaneous** solution of the system residual, not a one-directional
subtraction. It is the solve that B5 architecture cases and the B6 trade engine call.

## Governing relation and variable definitions
The five per-node residuals R1-R5 of B0 plan 4.1a (junction chain, cold-plate film, loop
energy with pump heat, radiator film, per-face radiator law). `Q_chip` flows through R1/R2
only; pump heat enters R3; `Q_rad = Q_chip + Q_pump_fluid` (4.7). Jacobian lower-triangular in
solve order R5->R4->R3->R2->R1; the pump-heat/property circular dependency is a fixed point in
loop mean temperature and pressure. Radiator law linear in `T_rad^4` (R5 closed form).

## Assumptions
Steady state; single series loop; single-phase liquid coolant (fixed point guarded to the
liquid domain); `T_f,cp = T_f,rad = (T1+T2)/2`; uniform properties at the solved loop mean
state; fluid-loop pump-energy boundary (4.7); per-face C1/C2 shielded sinks (C3 deferred).

## Explanation in the director's own words
`TODO (director)` -- to be written without model drafting before status advances to
`explained`. Do not infer or fabricate.

## Reproduction method
```bash
python -m pytest tests/test_coupled_model.py -q
```
Code: `orbital_thermal.coupled_model` (consumes B1 registry, B2 `solid_network`, B3
`pumped_loop`/`fluids`, and Phase A `radiation`).

## Supporting evidence (by category)
- **a. source / reference:** the B0 plan 4.1a/5 contract; Phase A radiator law
  (`radiative-equilibrium-and-net-rejection`); the B1-B3 correlations/properties.
- **b. independent derivation:** the lower-triangular solve order and the closed-form radiator
  law (linear in `T_rad^4`) are derived in `docs/coupled-model.md`; a director-authored
  derivation is `TODO`.
- **c. executable reproduction:** `tests/test_coupled_model.py` (32 tests): two-direction
  baseline recovery (Mode T -> Phase A `T_rad`; Mode A -> Phase A area), energy closure,
  vanishing nondimensional residual, Mode T/A cross-consistency, feasibility gates (junction
  limit, subcooling, radiator-above-sink), failure states (non-convergence, unknown coolant),
  multi-start robustness, per-face C1/C2, and C3 parametric-only. Status: present and passing.
- **d. qualified external human review:** `pending`.
- **cross-model review (separate; not category d):** initial adversarial review returned 1
  blocker + 7 findings (F1-F8); **all fixed**; the B4 review record is OPEN pending the
  confirmation re-review.

## Sensitivity / limiting cases
- Transport losses + pump heat zeroed -> exact Phase A recovery (both modes).
- Pump heat on -> `Q_rad > Q_chip` (rejected load rises).
- Supercritical seed -> rejected as a phase-envelope excursion, not a competing root.

## Known uncertainties
Reduced-order (uniform-property, single-loop, steady) idealization; turbulent-correlation and
transition-band uncertainty inherited from B3; the C3 direct-solar term is deferred, so sunlit
coupled faces are parametric-only.

## What evidence would invalidate this result
- A converged solution that fails energy closure or the residual gate.
- A physical (feasible, single-phase-liquid) second root that multi-start does not report.
- A coupled measurement / higher-fidelity model diverging beyond the reduced-order tolerance.

## Open questions / TODO
- `TODO (director)`: plain-language explanation of the coupled solve and the heat-injection
  rule (chip heat through R1/R2; pump heat into R3).
- `TODO`: independent derivation record (b) beyond the docs argument.
- **Required:** confirmation re-review of the F1-F8 revision; finalize the B4 review record
  before B4 is treated as complete.
- Deferred: Mode S / Mode O (B6); mass/containment (B5); C3 direct-solar term.
