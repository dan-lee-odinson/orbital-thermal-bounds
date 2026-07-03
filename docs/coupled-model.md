# Coupled steady-state model (Phase B, Stage 1 - milestone B4)

> **Status: design-intent implementation (B4), not a validated result.** Verified by
> two-direction baseline recovery against Phase A, energy closure, and residual/feasibility
> gates; not calibrated to hardware. A cross-model review record is required (major milestone).

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
introduces exactly one new temperature). The single circular dependency -- pump heat and fluid
properties depend on loop temperature, which depends on them -- is resolved as a **fixed point
in loop mean temperature and pressure**. The radiator law is linear in `T_rad^4`, so R5
(Mode T) and its inverse (Mode A) are **closed form**.

The fixed point is **guarded to the single-phase-liquid domain**: an iterate that climbs past
the coolant critical temperature is a phase-envelope excursion (a failure state, 5), not a
physical root. Multi-start seeds bracket the converged root within the liquid range and must
agree, or a branch is reported.

## Solve modes (B4 scope: T and A)

| Mode | Fixed design variables | Solved |
|---|---|---|
| **T** | `A_rad`, `m_dot` | `T_rad`, `T_w`, `T1`, `T2`, `T_j`, `Q_pump` |
| **A** | `T_rad`, `m_dot` | `A_rad`, `T_w`, `T1`, `T2`, `T_j`, `Q_pump` |

Mode S (size to `T_j = T_j_max`) and Mode O (optimization) wrap into **B6** and are not built
here. Component/containment **mass is deferred to B5**.

## Convergence, closure, feasibility (B0 plan 5)

- **Convergence** is declared only when the **nondimensionalized** residual vector (each
  component scaled by its characteristic magnitude) is below tolerance **and** global energy
  closure holds. A raw mixed-unit norm is not used.
- **Energy closure:** `Q_rad = Q_chip + Q_pump_boundary` (fluid-loop, 4.7).
- **Feasibility gates** (post-convergence; a converged-but-infeasible **ranked** case is
  **rejected**, a sensitivity case is **flagged**): mass-flow positive; temperature ordering
  `T_j >= T_w >= T_mean >= T_rad`, `T2 > T1`; efficiencies in `(0,1]`; `T_rad > T_sink`;
  Reynolds in correlation range; `P_lo - P_sat >= subcooling margin`; `T_j <= T_j_max` (if
  given); residual + closure below tolerance.
- **Failure states (fail loudly):** non-convergence, property/phase-envelope excursion,
  feasibility-gate failure for a ranked case, impossible pressure, multi-start branch.

## Baseline recovery (two separate tests, B0 plan 5)

With transport losses and pump heat zeroed: **Mode T** recovers Phase A `T_rad` for fixed
`(Q, A, sink, eps)`; **Mode A** recovers Phase A `A` for fixed `(Q, T, sink, eps)`. Both are
exact to machine precision in the test suite.

## Direct-solar contract (4.4a; B4 keeps C3 deferred)

Per face, the case declares C1 (fully-shielded bifacial), C2 (single cold-face), or C3
(explicit sunlit). **C1 and C2 are rank-eligible** using the inherited (shielded) Phase A
sink. **C3 is parametric-only** -- the inherited sink omits direct solar, so a C3 face
requires a sourced/parametric `alpha_s` flux and is **never rank-eligible** here; a C3 face
without that flux raises (missing `alpha_s` blocks ranking). No solar term is added to
`sink.py` in B4.

## Rank-eligibility inheritance

A ranked coupled case requires a rank-eligible coolant backend (B3: ammonia/water), a
rank-eligible solid path (B2: isotropic + spreading + cited contact), and a rank-eligible
radiator contract (C1/C2). Any failure raises `NotRankEligibleError`. See
`tests/test_coupled_model.py`.
