# B5 completion report: Stage-1 common-envelope architecture cases

> **Working verification record.** B5 is an *intermediate* Phase B milestone (a full cross-model
> review is required only at B0/B4/B6/B8). This report + an optional spot-check are the record.
> No physical result is validated; nothing here is a published-architecture comparison.

- **Milestone:** B5 (Phase B, Stage 1 architecture cases)
- **Date:** 2026-07-04
- **Built on:** `main` after B4 (`1d334cd`)
- **Governing plan:** `docs/development/chip_to_radiator_phase_b_plan.md` Sections 4.8 (ranking
  gates), 4.8a (mass-accounting boundary), and the B5 summary (Section 8); roadmap B5.

## Scope (as directed)

- **Full 16-case matrix, classified not force-ranked.** Every coolant x material combination
  carries a verdict; only the 4 that pass the B1/B2/B3/B4 gates **and** are feasible enter
  ranked outputs.
- **Self-contained Stage-1 common envelope** -- all design variables; **no** AI1 / Starcloud /
  Suncatcher anchoring or labels.
- **Modeled component mass only** (incomplete Stage-1 accounting, 4.8a) -- no total-system,
  launch, or flight-qualified mass claim.

## What was built

`orbital_thermal.architecture_cases` -- gate-driven classification (`rank-eligible` /
`sensitivity-only` / `source-required` / `unsupported` / `rejected`) with reason codes; the
`Stage1Envelope`; the 16-case matrix builder; ranked solve via the B4 coupled model; a
sensitivity path that runs only with explicit parametric inputs and is never rank-eligible; and
the 4.6/4.8a `modeled_component_mass`. Plus a generator that emits the matrix doc.

Files (5 new + 1 index):
- `src/orbital_thermal/architecture_cases.py` (new)
- `tests/test_architecture_cases.py` (new)
- `scripts/generate_architecture_matrix.py` (new)
- `docs/architecture-cases.md` (new, design-intent)
- `docs/architecture-case-matrix.md` (new, generated: classification / counts / ranked /
  sensitivity / mass)
- `verification/mastery-ledger/entries/architecture-cases.md` (new)
- `verification/mastery-ledger/index.md` (Phase B entries: add the B5 row)

## Result (Stage-1 common envelope)

- **16 total -> 4 rank-eligible, 12 non-ranked** (4 sensitivity-only CO2; 8 source-required =
  4 PGW + 4 anisotropic APG/diamond); 0 unsupported, 0 rejected in the standard matrix.
- Ranked cases (ammonia/water x Al/Cu) are all feasible and **differentiated**: copper gives
  ~6 K more junction margin than aluminium (T_j 337 vs 343 K); ammonia vs water trade pump power
  (15.7 vs 7.8 W) against Reynolds regime.
- Modeled component mass ~16.2-16.6 kg per reference case (radiator-panel dominated; copper
  heavier by its solid density), **labelled incomplete**.

## Verification performed

- **ruff** (E,F,W,I,B,UP, line 100): clean.
- **B5 tests** (`tests/test_architecture_cases.py`): **18 passed** -- 16-combo classification +
  counts (16/4/12), rank-eligible feasibility + ranked-only, sensitivity-only-with-parametric-
  inputs, CO2/PGW non-evaluable, REJECTED-by-junction, and the modeled-mass components / labels
  / exclusions / thin+thick-wall containment.
- **Full suite** (sandbox clone, CoolProp pinned): **524 passed, 3 xfailed, 0 failed** -- no
  regressions (+18 over B4's 506).
- **Coverage:** `architecture_cases.py` 92%; total 95.4% (CI gate is 90%).
- **Phase A guards:** `verify_suite.py`, `verify_paper3.py`, `companion/verify_ai1.py` all pass.
- **Evidence level:** a (registry statuses / 4.8 gates) + c (executable).

## Limitations and readiness

- CO2/PGW property backends, anisotropic (cited directional) material paths, and total
  thermal-system mass closure remain deferred; the parametric sensitivity conductivities are
  uncited bounds (never ranked).
- **Next: B6 (trade-study engine, MAJOR)** assembles these rank-eligible cases into Pareto
  fronts; its physical conclusions inherit B1-B5 evidence and it carries a mandatory review.
