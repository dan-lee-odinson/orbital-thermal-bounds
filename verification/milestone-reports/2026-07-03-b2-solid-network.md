# B2 completion report: solid thermal network

> **Working verification record.** B2 is an *intermediate* Phase B milestone (a full
> cross-model review record is required only at B0/B4/B6/B8 and releases). This documents
> what was built, how it was verified, and what is deferred. No physical result is validated.

- **Milestone:** B2 (Phase B, Stage 1 solid thermal network)
- **Date:** 2026-07-03
- **Built on:** `main` after B1.1 and Biswas R0
- **Governing plan:** `docs/development/chip_to_radiator_phase_b_plan.md` Section 7 "B2"
  (and 4.1a).

## What was built

`orbital_thermal.solid_network` -- the junction-to-cold-plate solid path (chip heat only):
1-D conduction, Yovanovich isothermal-base (Biot-optional) spreading, and contact resistance,
assembled as a series `SolidPath` with `R_total` and `junction_temperature`. Registry-aware
builders pull isotropic conductivity from B1 and enforce rank-eligibility.

Files (4 new + 1 updated):
- `src/orbital_thermal/solid_network.py`
- `tests/test_solid_network.py`
- `docs/solid-thermal-network.md`
- `verification/mastery-ledger/entries/solid-thermal-network.md`
- `verification/mastery-ledger/index.md` (Phase B entries: add the B2 entry)

## Design decisions (from B2 scoping)

- **Spreading:** Yovanovich / Lee-Song-Au-Moran (1995), isothermal base by default,
  finite-Biot optional.
- **Contact resistance:** cited-or-blocked -- a ranked case must pass a non-empty
  `contact_source` (the registry marks contact `source_required`), else `NotRankEligibleError`.
- **Anisotropy:** isotropic-only in B2; APG/diamond are registry-blocked and cannot enter a
  ranked path. Direction-aware handling is deferred.

## Verification performed

- **ruff** (E,F,W,I,B,UP, line 100): clean.
- **B2 tests** (`tests/test_solid_network.py`): **22 passed** -- analytic conduction/contact
  exactness; spreading limits (isoflux half-space `~0.28/(k a)`, source-fills-plate -> 0,
  monotonic in source radius, convective >= isothermal, higher `k` lowers spreading);
  series assembly + junction temperature; and registry rank-eligibility (Al/Cu rank-eligible;
  APG/diamond and uncited contact raise; sensitivity path never rank-eligible; Cu beats Al).
- **Full suite** (sandbox clone, CoolProp pinned): **443 passed, 3 xfailed, 0 failed** -- no
  regressions.
- **Evidence level:** a (Lee 1995 source) + b (analytic limits) + c (executable).

## Scope boundaries

Chip side only (no convective film / fluid loop -- that is B3; no radiator -- Phase A). No
architecture ranking; no Biswas; isotropic only. No published / v1.0.1 result changed.

## Limitations and readiness

- The spreading closed form is a reduced-order fit (~4% vs the isoflux half-space limit).
- Contact resistance stays `source_required`; a ranked case must cite an interface.
- Anisotropic/direction-aware conductivity is deferred; the B0-plan anisotropy direction
  test moves with it.
- **B3 (single-phase pumped loop)** is the next Phase B step and can build on this
  (`T_base` is the hand-off; the film resistance closes the junction-to-fluid path in B3).
