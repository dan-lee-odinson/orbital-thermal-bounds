# B7 completion report: documentation and examples

> **Working verification record.** B7 is an *intermediate* Phase B milestone (a full cross-model
> review is required only at B0/B4/B6/B8). This report + an optional spot-check are the record.
> B7 adds **no new physical claim**: it documents and visualizes existing B1-B6 artifacts, so it
> opens **no new mastery-ledger entry**. Public docs state only conclusions whose ledger status
> justifies them.

- **Milestone:** B7 (Phase B, Stage 1 documentation and examples)
- **Date:** 2026-07-04
- **Built on:** `main` after B6 (`c025d07`)
- **Governing plan:** roadmap B7 ("public docs summarize only conclusions whose ledger status
  justifies it"); plan Section 8.

## Scope (as directed)

- **Six Pareto figures from the B6 CSV only** -- no new physics, smoothing, interpolation, or
  ranking; figures render the already-computed points.
- **Concise `chip-to-radiator-model.md`** synthesis that links the per-milestone docs + records
  and preserves every limitation -- no new claims/numbers.
- **One CoolProp-guarded end-to-end example** at a single rank-eligible point.

## What was built

- `scripts/plot_trade_study.py` -- reads the committed `docs/trade-study-points.csv` **and**
  imports `trade_study.TRADES`, so the figures **cannot drift** from the tested engine output.
  One figure per front, points coloured by case, **Pareto-front members highlighted** (from the
  exported `pareto_front_membership`), each front's **dominating assumption** in the caption,
  the mass axis labelled **"modeled component mass (incomplete)"**. Gate-rejected / nonconverged
  points have no feasible metric coordinates, so their counts are stated (not plotted).
- `docs/trade-study-figures/*.png` (6) -- the generated figures.
- `docs/chip-to-radiator-model.md` -- public synthesis of the B1-B6 chain; links each stage's
  doc + ledger/review; preserves the limitations (reduced-order; single-phase; physics inherits
  B1-B5; B6 verifies assembly not physics; modeled component mass is incomplete; nonconvergence
  is not physical infeasibility; no single case is optimal on every front is not a global
  ranking; no published-architecture comparison).
- `docs/trade-study.md` -- the six figures embedded under a new "Pareto figures (B7)" section.
- `examples/04_chip_to_radiator.py` -- the full Stage-1 path at one representative rank-eligible
  point (case setup -> coupled solve -> modeled component mass -> classification + traceability),
  **guarded** so it exits 0 with a skip message when CoolProp is absent (the numpy-only CI
  examples job stays green).
- `tests/test_examples.py` -- asserts the example runs cleanly (full path with CoolProp; guarded
  skip without).

## Verification performed

- **ruff** (src / tests / scripts / examples): clean.
- **Full suite** (clone, CoolProp pinned): **548 passed, 3 xfailed, 0 failed** (+1 example test).
- **Coverage:** total 96.0% (gate 90%) -- unchanged; the figure script and example are report/
  demo code, exercised via `tests/test_examples.py` (which walks the coupled path).
- **Examples job (numpy-only) simulation:** all four `examples/*.py` exit 0; example 04 reaches
  its guarded CoolProp skip.
- **Phase A guards:** `verify_suite.py`, `verify_paper3.py`, `companion/verify_ai1.py` pass.
- **mkdocs --strict:** builds the new page, copies all six figures, and resolves the internal
  links.

## Limitations and readiness

- Figures are static PNGs of the Stage-1 modest grid; they inherit every B1-B6 limitation and
  add none. The synthesis doc makes no claim beyond the B1-B6 artifacts.
- **Next: B8 (review and release decision, MAJOR)** -- full suite + verification suites +
  examples; confirm no Phase A / `v1.0.1` result changed; seek targeted qualified-human review
  of the central transport/pressure claims; B8 review + release record required.
