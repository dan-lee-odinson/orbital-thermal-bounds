# Thermodynamic Bounds and Mass-Trade Criteria for Heat Rejection in Orbital Data Centers
*Machine-verified thermodynamic bounds for orbital data center thermal architecture: the preprint, its LaTeX source, the audited proof document, and two independent verification suites (Python and Wolfram Language).*

**Archived version:** DOI: [https://doi.org/10.5281/zenodo.20650893](https://doi.org/10.5281/zenodo.20650893)

and

# The AI1 Design Point: A Bounds-Based Analysis of SpaceX's Orbital Data-Center Satellite
*Companion paper to "Thermodynamic Bounds" applying its radiator-area bounds to the industrial design point: SpaceX's AI1 Satellite announcement. Included are the preprint, its LaTeX source, and Python verification suite. (See /Companion )*

**Archived version:** DOI: [https://doi.org/10.5281/zenodo.20670772](https://doi.org/10.5281/zenodo.20670772)

**Author:** Dan Lee-Odinson ([ORCID 0009-0009-9504-0796](https://orcid.org/0009-0009-9504-0796)) | dan.lee.odinson@gmail.com
---

## What this is

Orbital data centers must reject waste heat by far-field thermal radiation, and the resulting radiator area requirement is widely regarded as the binding engineering constraint on the concept. This work derives, within a gray-body effective-sink radiator model, a set of exact results governing that constraint:

1. The Carnot efficiency evaluated at the environmental sink temperature (the "2.7 K cold reservoir" argument) is unattainable by any heat engine with a material cold reservoir at finite radiator area and positive heat or work throughput. Near-limit efficiencies are possible in principle but command extreme area (a worked 99% example requires roughly 6.4 billion square meters per megawatt).
2. Radiator area per unit work output is minimized, along the reversible lower envelope, at a cold-side temperature of exactly three quarters of the hot-side temperature, with a 25% efficiency ceiling. The nonzero-sink optimum satisfies a quintic with the exact implicit form T_c\*/T_h = (3 + q⁴)/4, q = T_s/T_c\*, and fractional shift q⁴/3.
3. Converting waste heat to work before rejecting it multiplies the required radiator area by at least (T_h/T_c)³. Equality requires reversible conversion and a zero-temperature sink; every real system pays more.
4. No cyclic system can sustain its compute load solely by reconverting its own waste heat.
5. Radiator selection, heat-pump inclusion, and topping-cycle inclusion reduce to explicit mass-trade inequalities whose verdicts depend on empirical parameters but whose algebraic form does not.

The design implication: within the model, orbital thermal management is a temperature-architecture problem. The temperature at which heat finally leaves the system enters the area requirement quartically and dominates fixed-temperature efficiency optimization.

## Files

| File | Description |
|---|---|
| `orbital-thermal-preprint.pdf` | The preprint (9 pages, compiled) |
| `orbital-thermal-preprint.tex` | LaTeX source (self-contained, no external figures) |
| `orbital-thermal-resolution-proof-v3.md` | Audited source document with full revision history across three audit rounds |
| `verify_suite.py` | Python assertion suite covering every central numerical claim |
| `verify_suite.wl` | Wolfram Language symbolic verification suite (stationarity, second-order conditions, limits, exact rationals, high-precision roots) |
| `LICENSE` | CC BY 4.0 |

## Running the verification suites

**Python** (requires Python 3.8+ and numpy):

```bash
python3 verify_suite.py
```

Expected output: `All assertions pass.` Runtime is under a minute; the suite asserts every central numerical claim in the manuscript, including the exact sink-corrected area ratios, the 3/4-rule optimum with second-order condition, the q⁴/3 shift identity at eight sink temperatures, the COP identities, and the conversion area penalty bounds.

**Wolfram Language** (requires Mathematica or Wolfram Engine):

Open `verify_suite.wl` and evaluate the blocks (W1 through W9) in order. Each block states its expected output in comments. The blocks verify the proofs symbolically: stationarity conditions via `Solve` and `FullSimplify`, the fixed-point contraction factor 4q⁴/(3+q⁴) < 1, the divergence limits in Theorem 1, the nonzero-sink penalty inequality via `Reduce`, and the quintic root as an exact algebraic `Root` object evaluated to 50 digits.

The two suites are independent implementations. A reviewer who trusts neither can check the proofs by hand; the verification protocol is stated at the end of the source document.

## Provenance

This work was produced through an iterative, adversarial workflow across multiple AI systems, orchestrated and directed by the author: derivations and drafting by Claude Fable 5 (Anthropic), literature-armed review by Perplexity deep research, and two formal proof audits with independent computer-algebra verification by GPT 5.5 with the Wolfram plugin. The source document records every correction from every audit round, including the errors each system made and retracted along the way. The author takes responsibility for the result.

## How to cite

> Lee-Odinson, D. (2026). Thermodynamic Bounds and Mass-Trade Criteria for Heat Rejection in Orbital Data Centers. Zenodo. [Version 3] [https://doi.org/10.5281/zenodo.20650893](https://doi.org/10.5281/zenodo.20650893)

BibTeX:

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
## Companion paper: The AI1 Design Point

On June 9–10, 2026, SpaceX announced AI1, its first orbital data-center satellite. The companion paper in `companion/` applies this repository's thermodynamic bounds to the announced design and establishes its coherence within the gray-body radiator model, under one specific reading of the reported figures.

**Archived version:** Zenodo DOI: [https://doi.org/10.5281/zenodo.20670772](https://doi.org/10.5281/zenodo.20670772)

What it shows, briefly: treating the reported 110 m² of radiators as double-sided panel planform (the reading SpaceX itself states — "radiating both sides, orientated knife-edge to the sun"), the implied radiator surface temperature is about 337 K at the 120 kW sustained load and about 353 K if the 150 kW peak runs continuously. The alternative total-emitting-area reading requires 391–412 K, which strongly disfavors the subcritical ammonia loop secondary coverage describes as likely. An illustrative combined stress case (emissivity 0.91 → 0.80, effective sink 220 → 260 K) removes about 40 kW of fixed-temperature capacity — the entire reported peak-to-sustained headroom plus 10 kW — or raises the sustained equilibrium by about 22 K into unreported temperature and pressure limits. The reduced-order model does not rule the design out; margin, the engineering interior, and the economics remain open.

Every reported figure in the paper traces to a quoted source (the key statements are direct Musk and Dahl quotations from announcement coverage), and every radiator-model calculation and displayed value is asserted by the verification suite. The paper passed four rounds of adversarial peer review by GPT 5.5 with independent Wolfram verification; the revision history is recorded in the response letters.

### Companion files

| File | Description |
|---|---|
| `companion/ai1-design-point.pdf` | The companion paper (8 pages, Revision 4, review-approved) |
| `companion/ai1-design-point.tex` | LaTeX source |
| `companion/verify_ai1.py` | Assertion suite: both area interpretations, both power bases, both sensitivity branches, overhead cases, display-rounding policy. Run: `python3 verify_ai1.py` |

The suite's expected output states its scope precisely: "All radiator-model calculations and manuscript display-rounding assertions pass. External thermophysical property values are not computed by this suite." Ammonia properties are reference values from the NIST Chemistry WebBook (SRD 69), cited in the paper.

### How to cite the companion paper

> Lee-Odinson, D. (2026). *The AI1 design point: A bounds-based analysis of SpaceX's orbital data-center satellite* (Revision 4) [Preprint]. Zenodo. [(https://doi.org/10.5281/zenodo.20670772)](https://doi.org/10.5281/zenodo.20670772)]

BibTeX:

```bibtex
@misc{leeodinson2026orbitalthermal,
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

[Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). You may share and adapt this material for any purpose, including commercially, provided you give appropriate credit.
