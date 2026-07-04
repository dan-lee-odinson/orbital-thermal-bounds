# Architecture cases (Phase B, Stage 1 - milestone B5)

> **Status: design-intent implementation (B5), not a validated result.** The rank-eligible
> cases are solved by the verified B4 coupled model under one declared common envelope; all
> inputs are Stage-1 design variables. This is **not** an AI1 / Starcloud / Suncatcher
> comparison. Intermediate milestone: completion report + optional spot-check.

## What this is

`orbital_thermal.architecture_cases` assembles the coolant x solid-path case space,
**classifies every combination using the actual B1-B4 gates** (not a hardcoded lookup), solves
the rank-eligible cases through the B4 coupled model under **one Stage-1 common operating
envelope**, and computes a **modeled component mass** (incomplete Stage-1 accounting). The point
is to show the whole case space and prove the gates work -- not to pretend all combinations are
equally valid.

## Classification (gate-driven, per §4.8)

Every coolant x material combination is classified by running the real gates:

| Class | Meaning | How it is decided |
|---|---|---|
| `rank-eligible` | enters ranked outputs | coolant backend (B3) + solid path (B2) + contract (B4) all pass **and** the case is feasible under the common envelope |
| `sensitivity-only` | never ranked | a property is sensitivity-status (CO2 near-critical loop use) |
| `source-required` | never ranked | a property needs a cited source (PGW composition; anisotropic APG/diamond directional conductivity) |
| `unsupported/deferred` | never ranked | a deferred model path (C3 direct solar) |
| `rejected` | never ranked | provenance-eligible but **physics-infeasible** under the envelope (junction limit, single-phase margin, correlation domain, non-convergence) |

For the standard 16-combination matrix (4 coolants x 4 materials, contract C1): **4 rank-eligible**
(ammonia/water x Al/Cu), **4 sensitivity-only** (CO2), **8 source-required** (PGW x 4;
anisotropic APG/diamond x 4). Multi-block cells carry **all** applicable reason codes; the
primary class follows the precedence unsupported > sensitivity-only > source-required.

## No-invention rules (enforced)

- Sensitivity / source-required / unsupported cases are **never** ranked, **never** averaged
  into ranked conclusions, and **never** reported as published performance.
- A non-ranked case is *evaluated* **only** if the required parametric inputs are explicitly
  supplied and labelled (e.g., an uncited parametric conductivity for APG/diamond). CO2 and PGW
  have no rank-eligible property backend, so they remain **classification-only**.
- Only the rank-eligible, feasible cases appear in the ranked-results table.

## Stage-1 common envelope

A single declared operating point (all design variables): heat load, inherited Phase A shielded
sink, C1 contract, tube/cold-plate/radiator geometry, mass flow, low-side pressure, and a
junction limit. The same envelope is used for every case, so ranked cases are comparable
(ranking gate 10). No published-architecture inputs are used. See `Stage1Envelope`.

## Modeled component mass (§4.6 / §4.8a)

Mass is **modeled component mass (incomplete Stage-1 accounting)** -- **never** total-system,
launch, or flight-qualified mass. Included only for components with a declared basis: coolant
inventory (tube), tube containment ideal shell (§4.6: gauge pressure, safety factor applied
once, thin-wall only when `r/t >= 10` else Lame thick-wall, **ideal-shell lower bound** with
endcaps/joints/minimum gauge/launch-transient absent), solid conduction+spreader element, and
the radiator panel (only when an areal density is declared). Accumulator, pump, motor, valves,
manifolds, fittings, supports, MLI, redundancy, minimum gauge, and integration hardware are
**named exclusions**, so the incompleteness is visible.

## Outputs

The generated matrix (`scripts/generate_architecture_matrix.py` ->
[`architecture-case-matrix.md`](architecture-case-matrix.md)) contains the full 16-case
classification table, the count summary, the ranked-results table (rank-eligible only), a
sensitivity appendix (non-ranked cases evaluated with explicit parametric inputs), and a
modeled-component-mass breakdown. See `tests/test_architecture_cases.py`.
