# The chip-to-radiator model (Phase B, Stage 1)

> **Status: reduced-order, verification-supported model -- not an externally validated result.**
> Every conclusion below is reproducible from the package and its tests; none has yet had
> qualified external human review. Read each claim with its ledger status (see the
> [mastery ledger](https://github.com/dan-lee-odinson/orbital-thermal-bounds/tree/main/verification/mastery-ledger)).

## What this model is

Phase B Stage 1 is a **single-phase, reduced-order chip-to-radiator trade study**: from a
compute heat load at a chip junction, through a solid conduction path and a pumped single-phase
liquid loop, to an orbital radiator that rejects the heat to space -- solved as a coupled
steady state and swept into Pareto trade fronts. It is deliberately reduced-order: it exposes
the main thermal / hydraulic / mass trade space, not a flight design.

## The chain (each stage links to its own doc and record)

| Stage | What it adds | Doc | Ledger / review |
|---|---|---|---|
| **B1** property registry | typed, provenance-tagged properties + rank-eligibility gates | [property provenance](property-provenance.md) | ledger: property entries |
| **B2** solid network | junction->cold-plate conduction + Yovanovich spreading + contact | [solid thermal network](solid-thermal-network.md) | ledger: `solid-thermal-network` |
| **B3** pumped loop | single-phase hydraulics, film coefficient, pump energy, phase margins | [pumped loop](pumped-loop.md) | ledger: `single-phase-pumped-loop` |
| **B4** coupled model | the simultaneous R1-R5 solve (temperatures/area are **outputs**) | [coupled model](coupled-model.md) | ledger: `coupled-steady-state-solution`; **review CLOSED** |
| **B5** architecture cases | gate-driven classification of the coolant x material case space | [architecture cases](architecture-cases.md) + [matrix](architecture-case-matrix.md) | ledger: `architecture-cases` |
| **B6** trade-study engine | grid sweep -> six Pareto fronts (plot-ready data) | [trade study](trade-study.md) + [data](trade-study-data.md) | ledger: `trade-study`; **review CLOSED** |
| **B7** docs & figures | public synthesis + the six Pareto figures | *(this page)* | -- |

The full machine-readable trade data is
[`trade-study-points.csv`](trade-study-points.csv); the six figures are in
[the trade-study guide](trade-study.md#pareto-figures-b7).

## What is (and is not) established

- **Verification level.** B1-B5 carry source (a), analytic (b), and executable (c) evidence
  for their claims; **B6 verifies the engine's assembly and plots (c)** -- it does **not**
  independently validate the underlying physics, which it inherits from B1-B5.
- **Mass.** All mass figures are **modeled component mass (incomplete Stage-1 accounting)** --
  **not** total thermal-system, launch, or flight mass (accumulator, pump, motor, manifolds,
  minimum gauge, and more are named exclusions; 4.8a).
- **Nonconvergence.** A handful of extreme grid corners do not converge in the solver; those
  points are reported with a reason and excluded from every ranking -- nonconvergence is **not**
  evidence of physical infeasibility.
- **The trade result.** Under the Stage-1 common envelope, **no single coolant/material case is
  Pareto-optimal on every named front**; membership is distributed across cases. This is a
  multi-front trade-off-diversity statement, **not** a global aggregate ranking of architectures.
- **Scope.** Single-phase liquid only; C1/C2 (shielded) radiator contracts; C3 direct-solar and
  CO2/PGW/anisotropic paths are deferred or sensitivity-only; no published-architecture
  (AI1 / Starcloud / Suncatcher) comparison is claimed by this Stage-1 chain.

## Reproducing it

```bash
python -m pytest -q                          # the full test suite (physics + engine)
python scripts/generate_trade_study.py       # regenerate the trade data
python scripts/plot_trade_study.py           # regenerate the six Pareto figures
python examples/04_chip_to_radiator.py       # a single end-to-end walkthrough
```

## Verification status and limitations (v1.1.0)

- **No qualified external human engineering review has yet validated the central transport/pressure claims.** Cross-model review is not qualified external human review.
- The Phase B Stage-1 model remains a **reduced-order research and comparison framework**.
- It is **not flight-grade, not hardware-validated, and not suitable for certification or safety-critical design**.
- **External qualified review remains a future target** before stronger engineering claims are made.
