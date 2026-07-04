# B6 completion report: Stage-1 trade-study engine (MAJOR)

> **Working verification record.** B6 is a **major** milestone: a cross-model review record is
> **required** and is **OPEN** (`verification/review-records/2026-07-04-b6-trade-study.md`). B6
> is not complete until that review is dispositioned. The engine carries executable verification
> (c); the physics is inherited from B1-B5 and is not re-validated.

- **Milestone:** B6 (Phase B, Stage 1 trade-study engine)
- **Date:** 2026-07-04
- **Built on:** `main` after B5 (`ddf89c3`)
- **Governing plan:** roadmap B6; plan Section 8 (B6 summary); 4.8/4.8a (ranking + mass).

## Scope (as directed)

- **Sweep Q / m_dot / radiator area / P_lo** at a modest declared grid; hold tube diameter,
  loop length, cold-plate/radiator geometry, contact, material geometry, and junction limit
  fixed. `T_j <= T_j_max` is a **filter**, not a swept axis.
- **All six named Pareto fronts**, as **plot-ready data** (machine-readable CSV + summary);
  **figures deferred to B7**.
- **Modeled component mass only** (4.8a); no total-system mass claim.

## What was built

`orbital_thermal.trade_study` -- `DesignGrid` (declared modest grid + metadata); `evaluate_grid`
reusing B5 `evaluate_case` (physics inherits B1-B5); `EvaluatedPoint` with full metadata
(coords, objectives, feasibility, category, reason codes, active constraint, per-front dominance
flags); six `TradeDef`s with explicit axes/senses + dominating assumption; Pareto-dominance
construction with degenerate/empty-front records; machine-readable CSV export. Plus a generator
emitting the data doc + CSV.

Files (6 new + 1 index) and 2 B4-fix files:
- `src/orbital_thermal/trade_study.py` (new)
- `tests/test_trade_study.py` (new)
- `scripts/generate_trade_study.py` (new)
- `docs/trade-study.md` (new, design-intent)
- `docs/trade-study-data.md` (new, generated)
- `docs/trade-study-points.csv` (new, generated machine-readable)
- `verification/mastery-ledger/entries/trade-study.md` (new)
- `verification/mastery-ledger/index.md` (Phase B entries: add the B6 row)
- `verification/milestone-reports/2026-07-04-b6-trade-study.md` (this file)
- `verification/review-records/2026-07-04-b6-trade-study.md` (new; **OPEN**)
- **B4 fix (exposed by the sweep):** `src/orbital_thermal/coupled_model.py` +
  `tests/test_coupled_model.py` (see below).

## B4 robustness fix (exposed by B6)

The sweep surfaced a B4 multi-start false-positive near the critical temperature: a high
bracketing seed could converge to an **infeasible near-critical** second fixed point and raise a
spurious `BranchError` while the physical **subcooled-liquid** root was correct. Fixes: (1)
reduced-temperature domain cap `Tr <= 0.97` (was `Tcrit - 1`); (2) a subcooled-liquid filter --
an alt root is a branch only if it is itself a subcooled single-phase liquid at `P_lo`. B4 tests
still pass (41, +1 regression). This touches approved B4 code and is called out for the review.

## Result (default 144-point grid)

- **144 points -> 110 feasible, 34 infeasible** (junction x2, phase-margin x10,
  nonconvergence x22 at low-m_dot/high-load corners -- all reported with reasons, never ranked).
- All **6 fronts built, 0 degenerate**. Membership spans multiple cases across fronts:
  **no universal winner**.

## Verification performed

- **ruff**: clean. **B6 tests** (`tests/test_trade_study.py`): **16 passed** (dominance,
  Pareto membership, degenerate/empty records, grid/trade defs, real sweep + reason metadata,
  reproducibility, CSV export, trade-offs). **B4 tests:** 41 passed (+ regression).
- **Full suite** (clone, CoolProp pinned): **541 passed, 3 xfailed, 0 failed** (+17 over B5).
- **Coverage:** `trade_study.py` 98%; total 95.8% (gate 90%).
- **Phase A guards:** all three scripts pass. **mkdocs --strict**: builds the new pages + CSV.
- **Evidence level:** c (engine) + inherited a/b/sensitivity (physics).

## Limitations and readiness

- First-pass engine: modest grid, four swept variables; 22/144 corner points do not converge
  (reported, not ranked); mass incomplete (4.8a).
- **B6 is major:** the OPEN cross-model review must be conducted and dispositioned (including
  the B4 fix) before B6 is complete and before B7.
