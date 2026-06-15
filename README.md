# Thermodynamic Bounds and Mass-Trade Criteria for Heat Rejection in Orbital Data Centers
[![tests](https://github.com/dan-lee-odinson/orbital-thermal-bounds/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/dan-lee-odinson/orbital-thermal-bounds/actions/workflows/tests.yml)
![version](https://img.shields.io/badge/version-1.0.0-blue)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![license](https://img.shields.io/badge/code-MIT-green)

*Machine-verified thermodynamic bounds for orbital data-center thermal architecture, plus an audited Python simulation package that extends the analytic results to time-dependent, environment-coupled radiator behavior.* This repository contains three things: the **bounds preprint** and its proofs, the **AI1 design-point companion paper**, and the **`orbital_thermal` package** — a reduced-order radiator model whose headline result is a quantified correction to a published peer model.

**Bounds preprint:** DOI [10.5281/zenodo.20650893](https://doi.org/10.5281/zenodo.20650893)  
**AI1 companion paper:** DOI [10.5281/zenodo.20670772](https://doi.org/10.5281/zenodo.20670772)  
**Author:** Dan Lee-Odinson ([ORCID 0009-0009-9504-0796](https://orcid.org/0009-0009-9504-0796)) | dan.lee.odinson@gmail.com

---

## What this is

Orbital data centers must reject waste heat by far-field thermal radiation, and the resulting radiator-area requirement is widely regarded as the binding engineering constraint on the concept. This work derives, within a gray-body effective-sink radiator model, a set of exact results governing that constraint:

1. The Carnot efficiency evaluated at the environmental sink temperature (the "2.7 K cold reservoir" argument) is unattainable by any heat engine with a material cold reservoir at finite radiator area and positive throughput. Near-limit efficiencies command extreme area (a worked 99% example requires roughly 6.4 billion square meters per megawatt).
2. Radiator area per unit work output is minimized, along the reversible lower envelope, at a cold-side temperature of exactly three quarters of the hot-side temperature, with a 25% efficiency ceiling. The nonzero-sink optimum satisfies a quintic with the exact implicit form T_c\*/T_h = (3 + q⁴)/4, q = T_s/T_c\*.
3. Converting waste heat to work before rejecting it multiplies the required radiator area by at least (T_h/T_c)³. Equality requires reversible conversion and a zero-temperature sink.
4. No cyclic system can sustain its compute load solely by reconverting its own waste heat.
5. Radiator selection, heat-pump inclusion, and topping-cycle inclusion reduce to explicit mass-trade inequalities whose verdicts depend on empirical parameters but whose algebraic form does not.

The design implication: within the model, orbital thermal management is a temperature-architecture problem. The temperature at which heat finally leaves the system enters the area requirement quartically and dominates fixed-temperature efficiency optimization.

The **`orbital_thermal` package** (below) turns these static bounds into an executable, time-dependent model — and in doing so produces a new, independently verified result.

---

## The `orbital_thermal` package

A dependency-light Python package (`src/orbital_thermal/`) that implements the bounds as executable functions and extends them to the regime the analytic results do not cover: a panel with thermal mass whose effective radiative sink swings around the orbit. It is the simulation/modeling layer behind the papers, and it has been through nine rounds of adversarial review (eight remediation rounds plus a final pass; see **Audit status**).

### Headline result: McCalip's edge-on geometry is ~6.35 K low at its own default

The package vendors and re-executes Andrew McCalip's open `thoughts` orbital-radiator model (frozen and SHA-256-pinned under `external_models/`) and substitutes the **exact** tilted-plate-to-sphere Earth view factor for his cos-tilt heuristic with a 5% edge-on floor. At his own default geometry (β = 90°, sun-tracking bifacial panel, 550 km), the panel is **edge-on to Earth**, where the heuristic underestimates the per-face view factor by ~12×. Correcting it moves his equilibrium temperature:

```text
McCalip replicated equilibrium       335.749538028260 K
Exact-view-factor equilibrium        342.099222283610 K
Correction                            +6.349684255349 K
Exact edge-on per-face view factor     0.257772825310
```

This is a headline contribution, not a caveat: his replicated result is reproduced to floating-point roundoff, and the shift comes entirely from the view factor. The +6.35 K is the correction to the public code *as executed*; it decomposes into **+5.77 K** of model-form geometry (relative to the model's intended 5%-of-nadir floor) and **+0.58 K** of a floating-point `cos(90°)` branch artifact in the orbit average. The correction is positive at every sampled β and largest at the edge-on default.

This result, its decomposition, and an orbit-coupled transient extension are written up as a standalone preprint (paper three) in this repository: **[`orbital-thermal-edge-on-correction.pdf`](orbital-thermal-edge-on-correction.pdf)**, DOI [10.5281/zenodo.20695720](https://doi.org/10.5281/zenodo.20695720). Its numbers are reproduced by [`verify_paper3.py`](verify_paper3.py) against `orbital-thermal==1.0.0`.

### Install

```bash
pip install -e .              # core (numpy only)
pip install -e ".[fluids]"    # adds CoolProp==7.2.0 for the ammonia coolant screen
```

Requires Python 3.10+.

### Quickstart

```python
from orbital_thermal import equilibrium, mccalip_exact_vf as mx, transient
from orbital_thermal.constants import SIGMA_SB

# 1. Static radiator sizing (AI1 primary operating point: 120 kW / 220 m^2)
T = equilibrium.equilibrium_temperature(Q=120e3, area=220.0, emissivity=0.91, T_sink=220.0)
#   -> 337.1 K

# 2. The McCalip exact-view-factor correction table vs orbit beta angle
for row in mx.correction_table_vs_beta():
    print(row["beta_deg"], round(row["delta_K"], 3))   # +6.35 K at beta = 90

# 3. Transient averaging-load bias with a certified periodic steady state
Q = 0.91 * SIGMA_SB * (337.1**4 - 220.0**4)
bias = transient.averaging_bias(
    altitude_km=550, beta_deg=30, q_load=Q, areal_heat_capacity=8000.0,
    tilt_deg=0, assume_sun_shielded=True)        # raises unless fully certified
print(bias["transient_mean_K"], bias["peak_excess_over_steady_K"])
```

### Module map

| Module | Purpose |
|---|---|
| `constants` | SI constants (full binary64 Stefan–Boltzmann σ) |
| `radiation` | Gray-body net flux, required area, area ratios |
| `equilibrium` | Equilibrium temperature and fixed-temperature capacity (inverses) |
| `bounds` | Theorems 1–5 / Corollary 2.1: Carnot non-attainability, the 3/4 rule, quintic optimum, conversion-area penalty, heat-pump identities |
| `environment` | Orbital period/radius and the exact tilted-plate-to-sphere view factor |
| `sink` | Orbit-varying effective sink, subpoint-albedo approximation, exact orbit-mean closed form |
| `transient` | One-node RK4 radiator solver, periodic-steady-state convergence + temporal-resolution certificate, averaging-load bias, areal heat-capacity provenance |
| `mccalip_replication` | Faithful replication of McCalip's heat balance |
| `mccalip_exact_vf` | The exact per-face view-factor correction and β-sweep table |
| `fluids` | CoolProp-backed ammonia coolant screen (pinned EOS, optional) |

### Transient solver and convergence certificate

The one-node model `C dT/dt = q_load − εσ(T⁴ − T_sink_eff(t)⁴)` is marched with fixed-step RK4 and a positivity guard at every stage. `simulate(..., check_time_resolution=True)` returns a result only when it is certified along three independent axes:

- **periodic closure** — start-to-end orbit change below tolerance;
- **scale-aware energy balance** — orbit-mean net flux, as an equivalent temperature error, below tolerance (catches the high-thermal-inertia false-convergence trap that periodic closure alone misses);
- **temporal resolution** — the N-, 2N-, and 4N-step periodic solutions are independently converged and compared by a grid-free analytic forcing-quadrature certificate, direct N→4N summaries, and a pointwise waveform comparison on a common phase grid, with a conservative default safety factor. Peak-time/phase drift is reported separately (an amplitude bound does not bound peak timing).

`time_residual_K` is documented as a refinement-based error **estimate**, not a guaranteed continuum bound; the gate is made conservative by a default factor-of-two margin.

### Verification and reproducibility

- **Test suite:** 259 passing, 3 intentional xfails (placeholders for the not-yet-implemented disk-integrated albedo model, pinned to `NotImplementedError`). Run `pytest`.
- **Oracle freeze:** the vendored McCalip model is SHA-256-pinned (`external_models/mccalip_thoughts/PINS.json`), semantically regenerated via Node, and attested against the upstream GitHub blob; CI fails closed (`ORACLE_REQUIRE_EXTERNAL=1`). Published/oracle expected values are never edited to pass tests.
- **Thermophysics:** ammonia properties are computed from a pinned CoolProp backend (HEOS, EOS key `Gao-JPCRD-2020`), not transcribed; the generated table is hash-checked.
- **CI:** tests on Python 3.10/3.11/3.12, an oracle-freeze job, and a wheel-license job (PEP 639, MIT-only wheel).

### Audit status

The package passed an adversarial review cycle conducted by GPT-5.5 with independent Wolfram verification: **eight remediation rounds and a final pass**, ending in **FULL PASS — AUDIT CLOSED** at v1.0.0. The reviewer independently reproduced the +6.35 K headline correction every round, confirmed the analytic bounds symbolically, and verified the transient certificate against 8×–16×-resolution reference solutions across structured and randomized parameter sweeps (largest certified pointwise error 0.0046 K against a 0.01 K tolerance; zero exceedances). No P1/P2/blocking defect remains.

---

## Repository layout

| Path | Description |
|---|---|
| `src/orbital_thermal/` | The audited reduced-order radiator package (see module map above) |
| `tests/` | Test suite (259 passing, 3 intentional xfails) |
| `external_models/` | Vendored, SHA-256-pinned McCalip oracle + attestation |
| `scripts/` | Plotting and helper scripts (figures, ammonia table, wheel-license check) |
| `results/` | Generated figures and the ammonia property table |
| `docs/` | McCalip replication and ammonia-model notes |
| `orbital-thermal-preprint.pdf` / `.tex` | The bounds preprint (paper one) and LaTeX source |
| `orbital-thermal-edge-on-correction.pdf` / `.tex` | The edge-on view-factor correction preprint (paper three) and source |
| `orbital-thermal-resolution-proof-v3.md` | Audited proof document with full revision history |
| `verify_suite.py` / `verify_suite.wl` | Independent Python and Wolfram verification suites (paper one) |
| `verify_paper3.py` | Paper-three verification script (view-factor decomposition, balances, transient bias) |
| `companion/` | The AI1 design-point paper (paper two), source, and verification suite |
| `LICENSING.md` | Per-component license map |

## Running the verification suites

**Python** (Python 3.10+, numpy):

```bash
python3 verify_suite.py        # -> All assertions pass.
```

asserts every central numerical claim in the manuscript: the exact sink-corrected area ratios, the 3/4-rule optimum with second-order condition, the q⁴/3 shift identity at eight sink temperatures, the COP identities, and the conversion-area penalty bounds.

**Wolfram Language** (Mathematica or Wolfram Engine): open `verify_suite.wl` and evaluate blocks W1–W9 in order; each states its expected output. They verify the proofs symbolically (stationarity, the fixed-point contraction factor, the Theorem-1 divergence limits, the nonzero-sink penalty inequality, and the quintic root to 50 digits). The two suites are independent implementations.

## Provenance

This work was produced through an iterative, adversarial workflow across multiple AI systems, orchestrated and directed by the author: derivations and drafting by Claude (Anthropic), literature-armed review by Perplexity deep research, and formal proof and software audits with independent computer-algebra verification by GPT-5.5 with the Wolfram plugin. The source and response documents record every correction from every audit round. The author takes responsibility for the result.

## How to cite

> Lee-Odinson, D. (2026). Thermodynamic Bounds and Mass-Trade Criteria for Heat Rejection in Orbital Data Centers. Zenodo. [Version 3] https://doi.org/10.5281/zenodo.20650893

```bibtex
@misc{leeodinson2026orbitalthermal,
  author       = {Lee-Odinson, Dan},
  title        = {Thermodynamic Bounds and Mass-Trade Criteria for
                  Heat Rejection in Orbital Data Centers},
  year         = {2026},
  month        = jun,
  publisher    = {Zenodo},
  version      = {v3},
  doi          = {10.5281/zenodo.20650893},
  url          = {https://doi.org/10.5281/zenodo.20650893},
  note         = {Preprint}
}
```

## Paper three: The edge-on view-factor correction

A standalone preprint that builds on the package's headline result. It reproduces Andrew McCalip's public "Space Datacenters" radiator model to floating-point roundoff, then replaces only its approximate Earth view factor with the exact tilted-plate-to-sphere value at the model's own default (β = 90°, 550 km) edge-on geometry. The exact per-face view factor there is 0.25777; the public code produces an orbit-averaged 0.02118 (its intended 5% floor is 0.04237, halved by a `cos(90°)` floating-point branch), so the corrected equilibrium rises **335.75 K → 342.10 K (+6.35 K)** — decomposed as **+5.77 K** geometry and **+0.58 K** implementation artifact. The paper also extends the static balance to an orbit-coupled one-node transient model and quantifies the averaging-load bias (mean ≤ steady by Jensen; peak excess up to several kelvin). It is offered as cross-model verification, not validation against a flown radiator.

**Archived version:** Zenodo DOI [10.5281/zenodo.20695720](https://doi.org/10.5281/zenodo.20695720)

Reproduce its numbers (requires the installed package):

```bash
python verify_paper3.py     # decomposition, Tables 1-4, the periodic identity
```

### How to cite paper three

> Lee-Odinson, D. (2026). *Edge-On Geometry Raises a Public Orbital Data-Center Radiator Model's Coded Equilibrium Temperature by 6.35 K: An Exact Earth View-Factor Correction, Its Decomposition, and a Verified Orbit-Coupled Transient Extension.* Zenodo. https://doi.org/10.5281/zenodo.20695720

```bibtex
@misc{leeodinson2026edgeon,
  author       = {Lee-Odinson, Dan},
  title        = {Edge-On Geometry Raises a Public Orbital Data-Center
                  Radiator Model's Coded Equilibrium Temperature by 6.35 K},
  year         = {2026},
  month        = jun,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.20695720},
  url          = {https://doi.org/10.5281/zenodo.20695720},
  note         = {Preprint}
}
```

## Companion paper: The AI1 Design Point

On June 9–10, 2026, SpaceX announced AI1, its first orbital data-center satellite. The companion paper in `companion/` applies this repository's thermodynamic bounds to the announced design and establishes its coherence within the gray-body radiator model, under one specific reading of the reported figures.

**Archived version:** Zenodo DOI [10.5281/zenodo.20670772](https://doi.org/10.5281/zenodo.20670772)

What it shows, briefly: treating the reported 110 m² of radiators as double-sided panel planform (the reading SpaceX itself states — "radiating both sides, orientated knife-edge to the sun"), the implied radiator surface temperature is about 337 K at the 120 kW sustained load and about 353 K if the 150 kW peak runs continuously. The alternative total-emitting-area reading requires 391–412 K, which strongly disfavors the subcritical ammonia loop secondary coverage describes as likely. An illustrative combined stress case (emissivity 0.91 → 0.80, effective sink 220 → 260 K) removes about 40 kW of fixed-temperature capacity. The reduced-order model does not rule the design out; margin, the engineering interior, and the economics remain open.

Every reported figure traces to a quoted source, and every radiator-model calculation and displayed value is asserted by `companion/verify_ai1.py`. The paper passed four rounds of adversarial peer review by GPT-5.5 with independent Wolfram verification; the revision history is in the response letters.

### How to cite the companion paper

> Lee-Odinson, D. (2026). *The AI1 design point: A bounds-based analysis of SpaceX's orbital data-center satellite* (Revision 4) [Preprint]. Zenodo. https://doi.org/10.5281/zenodo.20670772

```bibtex
@misc{leeodinson2026ai1,
  author       = {Lee-Odinson, Dan},
  title        = {The AI1 design point: A bounds-based analysis of SpaceX's orbital data-center satellite},
  year         = {2026},
  month        = jun,
  publisher    = {Zenodo},
  version      = {v1},
  doi          = {10.5281/zenodo.20670772},
  url          = {https://doi.org/10.5281/zenodo.20670772},
  note         = {Preprint}
}
```

## License

This repository is licensed by component (see [`LICENSING.md`](LICENSING.md)):

- **Software** — `src/`, `tests/`, `scripts/`, the root `verify_suite.py` / `verify_suite.wl`, `companion/verify_ai1.py`, and packaging — is MIT-licensed (see [`LICENSE-MIT`](LICENSE-MIT)). The packaged distribution declares MIT.
- **Papers, documentation, and figures** — the manuscripts, `docs/`, and `results/figures/` — are licensed under Creative Commons Attribution 4.0 International (CC BY 4.0; see [`LICENSE-DOCS-CC-BY-4.0`](LICENSE-DOCS-CC-BY-4.0)).
- **Vendored McCalip model** — `external_models/` — retains its upstream MIT license (see [`external_models/mccalip_thoughts/UPSTREAM-LICENSE.md`](external_models/mccalip_thoughts/UPSTREAM-LICENSE.md)).
