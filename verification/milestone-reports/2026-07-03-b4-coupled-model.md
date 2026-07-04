# B4 completion report: coupled steady-state radiator model (MAJOR)

> **Working verification record.** B4 is a **major** milestone: a cross-model review record is
> **required** and is **OPEN** (`verification/review-records/2026-07-03-b4-coupled-model.md`).
> B4 is not complete until that review is dispositioned. No physical result is validated.

- **Milestone:** B4 (Phase B, Stage 1 radiator coupling)
- **Date:** 2026-07-03
- **Built on:** `main` after B3 (`c1f53aa`)
- **Governing plan:** `docs/development/chip_to_radiator_phase_b_plan.md` Sections 4.1/4.1a,
  4.4a, 4.7, 5, and the B4 block (Section 7).

## Scope (as directed)

- **Solve modes T and A only.** Mode S (size to `T_j = T_j_max`) and Mode O (optimization)
  wrap into B6.
- **Mass/containment deferred to B5.** B4 delivers the coupled thermal/hydraulic solve, pump
  heat, and per-face rejection.
- **C3 kept deferred.** C1/C2 rank-eligible with the inherited shielded sink; C3 is
  parametric-only (missing `alpha_s` blocks ranking); `sink.py` is untouched.

## What was built

`orbital_thermal.coupled_model` -- the R1-R5 residual system (4.1a) solved lower-triangular
(R5->R1) with an outer fixed point for the pump-heat/property feedback, guarded to the
single-phase-liquid domain. Radiator law closed form (linear in `T_rad^4`). Modes T and A.
Per-face `RadiatorSpec` with the C1/C2/C3 contract (4.4a). Nondimensional convergence, energy
closure, the full feasibility-gate suite, failure states, and multi-start branch check.
Rank-eligibility inherits B2 (solid path), B3 (coolant backend), and the 4.4a contract.

Files (4 new + 1 index):
- `src/orbital_thermal/coupled_model.py` (new)
- `tests/test_coupled_model.py` (new)
- `docs/coupled-model.md` (new)
- `verification/mastery-ledger/entries/coupled-steady-state-solution.md` (new)
- `verification/mastery-ledger/index.md` (Phase B entries: add the B4 row)
- `verification/review-records/2026-07-03-b4-coupled-model.md` (new; **OPEN**)

## Verification performed

- **ruff** (E,F,W,I,B,UP, line 100): clean.
- **B4 tests** (`tests/test_coupled_model.py`): **39 passed** -- including the **two-direction
  baseline recovery** (Mode T recovers Phase A `T_rad`; Mode A recovers Phase A area, both to
  ~1e-9), energy closure, vanishing nondimensional residual (~1e-15), Mode T/A
  cross-consistency, feasibility gates, failure states, multi-start robustness, and the
  C1/C2/C3 contract.
- **Full suite** (sandbox clone, CoolProp pinned): **505 passed, 3 xfailed, 0 failed** -- no
  regressions (+39 over B3's 466).
- **Coverage:** `coupled_model.py` 97%; total 95.7% (CI gate is 90%).
- **Phase A guards:** `verify_suite.py`, `verify_paper3.py`, `companion/verify_ai1.py` all
  pass -- no published result perturbed.
- **Evidence level:** c (baseline + closure + feasibility) + b (residual formulation).

## Automated checks vs the B4 contract

- **Two-direction baseline recovery** (Mode T and Mode A): pass (exact).
- **Energy closure** `Q_rad = Q_compute + Q_pump_boundary`: pass (~1e-15).
- **Nondimensional convergence** + feasibility-gate suite: pass; ranked-infeasible rejected.
- **Multi-start / branch** check: pass (supercritical excursion rejected as a domain exit,
  not a root).

## Cross-model re-review (F1-F8) applied

The initial adversarial cross-model review returned one blocker and seven major/minor
findings; **all eight were fixed** (see the review record). Summary: C2 now requires
excluded-face-outside-thermal-CV evidence (F1, blocker); `solve_coupled` rejects C3 (F2)
and the whole-spacecraft boundary (F3); `converged` now means the residual + energy gates
pass, not merely that the fixed point stopped (F4); multi-start classifies seed outcomes
and the docs claim is a local smoke check (F5); worst-case station min margins are exposed
and the guard is labelled a lumped conservative screen (F6); the ranked Reynolds gate
requires validity for every active correlation, including the friction blend to 4000 (F7);
and the contract enum is coerced (F8). Test count 32 -> 39.

## Limitations and readiness

- Reduced-order (uniform-property, single series loop, steady); C3 direct-solar deferred;
  Mode S / mass to later milestones.
- **B4 is a major milestone:** the OPEN cross-model review must be conducted and its findings
  dispositioned before B4 is treated as complete and before B5 begins.
