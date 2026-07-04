# Trade-study engine (Phase B, Stage 1 - milestone B6)

> **Status: design-intent implementation (B6), not a validated result.** The engine carries
> executable verification (c); the physics **inherits** B1-B5 and is not re-validated here. A
> cross-model review record is required (major milestone). Figures are deferred to B7 -- B6
> emits plot-ready data only.

## What this is

`orbital_thermal.trade_study` sweeps a **declared modest grid** of design variables across the
**rank-eligible B5 reference cases only**, evaluates every point through the verified B4 coupled
model (via B5's `evaluate_case`, so the **physics inherits B1-B5**), and assembles the **minimum
Pareto set** of six named trade fronts. Every point carries a category, reason codes, active
constraint, and per-front dominance flags; the outputs are machine-readable data, not figures.

## What B6 newly verifies (level c)

The **engine**, not the physics: grid enumeration; feasible/infeasible classification with
reason codes; **Pareto-dominance construction**; degenerate/empty-front handling (recorded, never
silently omitted); reproducible, fully-labelled output. The underlying physics is inherited from
B1-B5 (source a, analytic b, sensitivity) and is not independently validated here.

## Swept variables and the grid (first pass)

Four variables are swept (the ones the six fronts require): heat load `Q`, mass flow `m_dot`,
radiator area `A_plan`, and low-side pressure `P_lo`. **Held fixed** (declared Stage-1
assumptions, not swept): tube diameter, loop length, cold-plate and radiator wetted geometry,
contact resistance, material geometry, and the junction-limit threshold. `T_j <= T_j_max` is a
**filter**: violating points are reported as infeasible with a reason, never dropped. The exact
grid values are recorded in the output metadata (see `DesignGrid`).

## The six Pareto fronts (minimum set)

| Front | axes (sense) |
|---|---|
| `modeled_mass_vs_load` | heat load (max) vs modeled mass (min) |
| `pump_power_vs_delta_T` | fluid delta_T (min) vs pump power (min) |
| `radiator_area_vs_temp` | radiator temperature (min) vs radiator area (min) |
| `junction_margin_vs_load` | heat load (max) vs junction margin (max) |
| `inventory_containment_mass_vs_pressure` | operating pressure (max) vs inventory+containment mass (min) |
| `modeled_mass_vs_parasitic_power` | parasitic power (min) vs modeled mass (min) |

Each front carries its **dominating assumption** (the physical/accounting driver, e.g., mass is
radiator-panel-dominated; containment is an ideal-shell lower bound). A front that is
mathematically degenerate or empty for the population is emitted as an **explicit record with a
reason**, never silently omitted.

## Honesty rules (enforced)

- Only **rank-eligible feasible** points enter a front; only the B5 rank-eligible cases are
  swept.
- Every point carries a **category** (`feasible_ranked` / `infeasible_ranked` / ...) and
  **reason codes** (`junction_limit_failure`, `phase_margin_failure`, `reynolds_domain_failure`,
  `residual_nonconvergence`, `mass_accounting_incomplete`, dominance reasons).
- Mass is **modeled component mass (incomplete Stage-1 accounting, 4.8a)** -- never total-system,
  launch, or flight mass. The objective is *not* renamed "total thermal-system mass".
- **No universal winner:** different cases are Pareto-optimal on different fronts; the engine
  makes no single-architecture ranking claim.

## Outputs

`scripts/generate_trade_study.py` emits the machine-readable
[`trade-study-points.csv`](trade-study-points.csv) (every point x every objective, feasibility,
category, reasons, per-front membership) and the human-readable
[`trade-study-data.md`](trade-study-data.md) (grid metadata, counts, the six fronts with
members and dominating assumptions). **Figures are produced in B7**, consuming this data. See
`tests/test_trade_study.py` for the engine's executable verification.

## Note on the B4 solver (exposed by this sweep)

The B6 sweep exercised the B4 coupled solver across many design points and surfaced a
multi-start false-positive near the coolant critical temperature: a high bracketing seed could
converge to an **infeasible near-critical** second fixed point and raise a spurious `BranchError`
even though the physical **subcooled-liquid** root was correct. B4's multi-start was tightened
(reduced-temperature domain cap `Tr <= 0.97`, and a subcooled-liquid filter so an alt root is a
branch only if it is itself a subcooled single-phase liquid). See the B6 review record.
