# Verification, Validation, and Model Credibility

This document consolidates, in one place, what the `orbital_thermal` package and the
accompanying preprints establish — and, equally important, what they do **not**.

## Definitions

- **Mathematical verification** — the equations follow from the stated assumptions.
- **Software verification** — the code computes those equations correctly.
- **Cross-model verification** — independent implementations of the *same* model agree
  (e.g. our replication of McCalip's model against his frozen oracle).
- **Validation** — predictions match physical hardware or flight data.
- **Reproducibility** — an independent party can regenerate the published results from
  pinned inputs.
- **Applicability** — the range of uses for which the model's assumptions are appropriate.

This project supports mathematical, software, and cross-model verification, and is built
for reproducibility. **It does not claim validation against flown hardware**, and it has
not undergone formal human scholarly peer review (the audit was a human-directed,
AI-assisted adversarial technical review with independent computer-algebra checks).

## Credibility matrix

| Capability / claim | Evidence | Verification method | Validation status | Limitation |
|---|---|---|---|---|
| Gray-body equilibrium ↔ capacity inverse | Unit tests, analytic identity | Direct mathematical inversion | Mathematically + software verified | Reduced-order radiation model |
| Analytic thermodynamic bounds (Thms 1–5) | `verify_suite.py`, `verify_suite.wl` | Symbolic + numeric checks | Mathematically verified | Idealized reversible limits |
| Exact tilted-plate-to-sphere view factor | Independent derivation + closed form | Numerical vs symbolic (`~1e-9`) | Cross-checked | Differential-element idealization |
| McCalip baseline replication | Frozen, SHA-256-pinned Node oracle | Floating-point reproduction (`~4e-14`) | Software replicated | Retains his original model assumptions |
| Exact-view-factor correction (+6.35 K) | Substitution into his own balance | Self-consistency + decomposition | Cross-model verified | Correction to his coded model, not a flown radiator |
| Transient RK4 solver | Energy balance + grid refinement | N/2N/4N certificate + forcing check | Numerically verified | One-node model; residual is an estimate |
| Averaging-load bias (Jensen) | Periodic identity ⟨T⁴⟩ = T_steady⁴ | Analytic + numerical | Mathematically verified | Subpoint-albedo forcing |
| Ammonia coolant screen | CoolProp 7.2.0 (pinned) | Property regression vs pinned backend | Property-source verified | Not a loop/pressure design model |
| AI1 design-point analysis | Public reported parameters | Reproducible reduced-order analysis | **Not hardware validated** | Private design data unavailable |

Each row's evidence is reproducible from the repository at release `v1.0.1`; see the
verification scripts and the test suite.

## Applicability

**Appropriate uses**
- Early concept screening and order-of-magnitude radiator sizing.
- Sensitivity and trade studies within the stated model.
- Educational and illustrative analysis.
- Cross-model comparison and reproducible reduced-order research.

**Inappropriate uses**
- Flight certification or hardware qualification.
- Detailed coolant-loop, pressure, or fin-level thermal design.
- Final thermal-control design.
- Safety-critical or operational spacecraft decisions.

## How to reproduce the evidence

From a clone of the tagged release:

```bash
pip install -e ".[fluids]"
pytest                      # 259 passed, 3 xfailed
python verify_suite.py      # analytic bounds (paper one)
python verify_paper3.py     # view-factor decomposition + transient bias (paper three)
python companion/verify_ai1.py
```

The frozen McCalip oracle is checked by the package suite and the CI `oracle-freeze`
job (which fails closed when `ORACLE_REQUIRE_EXTERNAL=1` and the upstream source
cannot be attested).
