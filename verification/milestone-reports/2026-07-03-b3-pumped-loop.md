# B3 completion report: single-phase pumped loop

> **Working verification record.** B3 is an *intermediate* Phase B milestone (a full
> cross-model review record is required only at B0/B4/B6/B8 and releases). No physical result
> is validated.

- **Milestone:** B3 (Phase B, Stage 1 single-phase pumped loop)
- **Date:** 2026-07-03
- **Built on:** `main` after B2
- **Governing plan:** `docs/development/chip_to_radiator_phase_b_plan.md` Section 7 "B3"
  (and 4.2, 4.7, 6).

## What was built

`orbital_thermal.pumped_loop` -- loop hydraulics (Reynolds, auto friction, pressure drop with
minor losses), pump energy (hydraulic-into-fluid; `f` + boundary explicit), thermics (auto
Nusselt, film coefficient/resistance closing the B2 wall-to-fluid leg), and a configurable
N-segment march with per-segment freeze/saturation/critical margins. Plus per-state transport
properties added to `orbital_thermal.fluids` (the B1 `property_backend`).

Files (5 new/updated + 1 index):
- `src/orbital_thermal/pumped_loop.py` (new)
- `src/orbital_thermal/fluids.py` (extended: per-state density/cp/k/mu/Pr, margins)
- `tests/test_pumped_loop.py` (new)
- `docs/pumped-loop.md` (new)
- `verification/mastery-ledger/entries/single-phase-pumped-loop.md` (new)
- `verification/mastery-ledger/index.md` (Phase B entries: add the B3 row; also backfills
  the B2 `solid-thermal-network` row, whose entry file merged with B2 but was not yet
  listed in the index table)

## Design decisions (B3 scoping)

- **Pump heat:** hydraulic-into-fluid; `f` and the control-volume boundary explicit (B0 4.7).
- **Correlations:** auto by Reynolds -- laminar (64/Re, Nu 4.36/3.66), turbulent (Gnielinski
  Nu + Haaland friction), transition blended and warned; all domain-aware.
- **Discretization:** configurable N-segment march (default 10) with per-segment phase margins.

## Verification performed

- **ruff** (E,F,W,I,B,UP, line 100): clean.
- **B3 tests** (`tests/test_pumped_loop.py`): **23 passed** -- laminar friction reproduces
  Hagen-Poiseuille exactly; regime selection + transition warnings; pump-energy accounting
  (`f = eta_pump eta_motor`); Nusselt/film; registry rank-eligibility (ammonia/water pass;
  CO2/PGW/unknown raise); the N-segment march (energy balance, segment convergence,
  under-pressured loop raises `LoopPhaseError`); and CoolProp per-state property agreement.
- **Full suite** (sandbox clone, CoolProp pinned): **466 passed, 3 xfailed, 0 failed** -- no
  regressions.
- **Evidence level:** a (sources) + b (Poiseuille) + c (executable).

## Scope boundaries

Single-phase liquid only; loop hydraulics + film. The radiator coupling and the coupled energy
closure are **B4** (the loop's `fluid_heat` and outlet state are the hand-off). No two-phase; no
ranking; no Biswas. No published / v1.0.1 result changed.

## Limitations and readiness

- Turbulent correlations and the transition blend carry their own uncertainty; uniform-heat
  per segment is reduced-order.
- Minor-loss / maldistribution inventories remain case inputs / deferred.
- **B4 (radiator coupling, MAJOR)** is the next step and the next *required* cross-model review:
  it assembles B2 + B3 + the Phase A radiator law into the coupled residual solve with
  baseline recovery and energy closure.
