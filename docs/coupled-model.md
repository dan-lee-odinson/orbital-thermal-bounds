# Coupled steady-state model (Phase B, Stage 1 - milestone B4)

> **Status: design-intent implementation (B4), not a validated result.** Verified by
> two-direction baseline recovery against Phase A, energy closure, and residual/feasibility
> gates; not calibrated to hardware. A cross-model review record is required (major milestone);
> the initial adversarial review (F1-F8) has been dispositioned and the code revised.

## What this is

`orbital_thermal.coupled_model` solves the junction-to-radiator path as the **simultaneous**
solution of the five per-node residuals R1-R5 (B0 plan 4.1a), **not** a one-directional
`T_rad = T_chip - sum(dT)` subtraction. Radiator and transport temperatures (Mode T) or the
radiator area (Mode A) are **outputs** of the coupled solve.

## Residual system (B0 plan 4.1a)

```
R1: T_j - T_w  - Q_chip*(R_cond+R_spread+R_contact)          = 0   (junction chain; Q_chip)
R2: T_w - T_mean - Q_chip*R_film,cp                          = 0   (wall -> cold-plate film)
R3: Q_chip + Q_pump - m_dot*cp*(T2 - T1)                     = 0   (loop energy; pump heat)
R4: T_mean - T_rad - Q_rad*R_film,rad                        = 0   (radiator film)
R5: Q_rad - sum_faces eps*sigma*A_face*(T_rad^4 - T_sink^4)  = 0   (radiator law, per face)
```

**Heat-injection rule.** `Q_chip` flows through the junction chain (R1, R2) **only**; pump
heat is added directly to the fluid (R3). The radiator rejects `Q_rad = Q_chip + Q_pump_fluid`
(fluid-loop boundary, 4.7). Pump heat is never routed through the chip-side resistances.

## How it is solved

The Jacobian is **lower-triangular** in solve order R5 -> R4 -> R3 -> R2 -> R1 (each residual
introduces exactly one new temperature) -- this is the actual uniqueness basis for the physical
root. The circular dependency (pump heat and fluid properties depend on loop temperature) is a
**fixed point in loop mean temperature and pressure**, guarded to the single-phase-liquid
domain (a supercritical excursion is a failure state, not a root). The radiator law is linear
in `T_rad^4`, so R5 (Mode T) and its inverse (Mode A) are **closed form**.

`converged` means the **nondimensional residual vector** and **global energy closure** are both
below `residual_tol` (B0 plan 5, F8) -- distinct from `fixed_point_converged`, which only
reports that the iteration stopped stepping (below `tol`). Multi-start bracketing seeds are a
**local branch smoke check**: each must return to the same root or fail for a *classified*
single-phase-domain reason; an unexplained non-convergence is reported as a branch.

## Solve modes (B4 scope: T and A)

| Mode | Fixed design variables | Solved |
|---|---|---|
| **T** | `A_rad`, `m_dot` | `T_rad`, `T_w`, `T1`, `T2`, `T_j`, `Q_pump` |
| **A** | `T_rad`, `m_dot` | `A_rad`, `T_w`, `T1`, `T2`, `T_j`, `Q_pump` |

Mode S (size to `T_j = T_j_max`) and Mode O (optimization) wrap into **B6**. Component/
containment **mass is deferred to B5**. **Boundary: fluid-loop only** -- `solve_coupled` rejects
`whole_spacecraft` (the system roll-up is B5 accounting, 4.7).

## Convergence, closure, feasibility (B0 plan 5)

- **Energy closure:** `Q_rad = Q_chip + Q_pump_fluid` (fluid-loop, 4.7).
- **Feasibility gates** (post-convergence; a converged-but-infeasible **ranked** case is
  **rejected**, a sensitivity case is **flagged**): mass-flow positive; temperature ordering
  `T_j >= T_w >= T_mean >= T_rad`, `T2 > T1`; efficiencies in `(0,1]`; `T_rad > T_sink`;
  **Reynolds valid for every active correlation** (`Re <= 2300` or `Re >= 4000` -- the friction
  factor blends up to 4000, F7); subcooling/freeze/critical margins at the worst-case station;
  residual + energy closure below `residual_tol`; `T_j <= T_j_max` (if given).
- **Failure states (fail loudly):** non-convergence, property/phase-envelope excursion,
  feasibility-gate failure for a ranked case, impossible pressure, multi-start branch, a C3
  solve, or a non-fluid-loop boundary.

**Single-phase feasibility is a lumped conservative screen.** Properties and margins are
evaluated at the loop **mean** state, and the phase margins are checked at the **worst-case
station** -- the hottest loop temperature `T2` at the minimum station pressure `P_lo` (the
prescribed low side, 4.3). The reported `min_subcooling_Pa` / `min_freeze_margin_K` /
`min_critical_margin_K` are that worst-case screen. A full **per-segment** march lives in B3
(`march_single_phase_loop`) and is not re-run here.

## Baseline recovery (two separate tests, B0 plan 5)

With transport losses and pump heat zeroed: **Mode T** recovers Phase A `T_rad` for fixed
`(Q, A, sink, eps)`; **Mode A** recovers Phase A `A` for fixed `(Q, T, sink, eps)`. Both are
exact to machine precision in the test suite.

## Direct-solar contract (4.4a)

Per face, the case declares C1 (fully-shielded bifacial), C2 (single cold-face), or C3
(explicit sunlit).

- **C1** is rank-eligible using the inherited (shielded) Phase A sink.
- **C2** is rank-eligible **only** with evidence that the excluded face is **outside the
  thermal control volume** (`excluded_face_outside_thermal_cv=True` + a cited
  `excluded_face_basis`); without it the case is not rank-eligible and must be treated as
  C3/parametric (closes the B0 Rev-3 loophole, F1).
- **C3** is **deferred**: the inherited sink omits direct solar, so `solve_coupled` **rejects**
  a C3 case (it is not solved with the solar term silently ignored). C3 is never rank-eligible.
  No solar term is added to `sink.py` in B4.

## Rank-eligibility inheritance

A ranked coupled case requires a rank-eligible coolant backend (B3: ammonia/water), a
rank-eligible solid path (B2: isotropic + spreading + cited contact), and a rank-eligible
radiator contract (C1, or C2 with excluded-face evidence). Any failure raises
`NotRankEligibleError`. See `tests/test_coupled_model.py`.
