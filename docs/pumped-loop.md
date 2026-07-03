# Single-phase pumped loop (Phase B, Stage 1 - milestone B3)

> **Status: design-intent implementation (B3), not a validated result.** Verified against
> analytic limits and consuming the B1 registry; not calibrated to hardware.

## What this is

`orbital_thermal.pumped_loop` models the **single-phase liquid coolant loop**: hydraulics
(Reynolds, friction, pressure drop), thermics (Nusselt film coefficient closing the B2
wall-to-fluid leg), pump energy, and per-segment single-phase margins. It consumes the B1
correlation registry and the coolant **property backend** (per-state CoolProp evaluation via
`orbital_thermal.fluids`; the B1 reference literals are cross-check anchors only).

## Correlations (auto by Reynolds)

| Regime | Friction | Nusselt |
|---|---|---|
| Laminar (`Re <= 2300`) | `f = 64/Re` | `4.36` (uniform flux) / `3.66` (uniform Ts) |
| Turbulent (`Re >= 3000-4000`) | Haaland (Colebrook approx.) | Gnielinski |
| Transition | laminar/turbulent blend (**warned**) | laminar/Gnielinski blend (**warned**) |

`f = 64/Re` reproduces Hagen-Poiseuille `dP = 32 mu L v / D^2` exactly. Pressure drop is
`dP = (f L/D + sum K) rho v^2 / 2`.

## Pump energy (hydraulic-into-fluid; B0 plan 4.7)

```
P_hyd = m_dot dP / rho                 # hydraulic power -> heats the coolant
P_elec = P_hyd / (eta_pump eta_motor)  # electrical input
fluid_heat = P_hyd,  other = P_elec - P_hyd,  f = fluid_heat / P_elec
```

`f` and the control-volume boundary (`fluid_loop` vs `whole_spacecraft`) are explicit. The
`fluid_heat` is reported for the coupled solve (B4) to add to the rejected load; it is not
re-injected into the per-segment march here.

## N-segment march and phase margins

`march_single_phase_loop(...)` marches the loop in `segments` steps (default 10), evaluating
properties per-state and checking **freeze**, **saturation (subcooling)**, and **critical**
margins at each segment. A violation raises `LoopPhaseError` (fail loudly) -- the model never
silently extrapolates a boiling or frozen coolant.

## Registry-governed rank-eligibility (B1)

A ranked loop must use a coolant with a **rank-eligible property backend** -- ammonia or
water. CO2 (sensitivity-only) and PGW (`source_required`) are blocked, as is any unknown
coolant; `assert_loop_coolant_rankable` raises `NotRankEligibleError`.

## Scope (B3)

Single-phase liquid only; the loop leg (cold-plate side) hydraulics + film. The **radiator
coupling and the coupled energy closure are B4** (the loop's `fluid_heat` and outlet state are
the hand-off). No two-phase, no ranking. See `tests/test_pumped_loop.py`.
