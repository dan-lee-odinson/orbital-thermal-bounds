# Thermodynamic Bounds and Mass-Trade Criteria for Heat Rejection in Orbital Data Centers

Machine-verified thermodynamic bounds for orbital data center thermal architecture: the preprint, its LaTeX source, the audited proof document, and two independent verification suites (Python and Wolfram Language).

**Author:** Dan Lee-Odinson ([ORCID 0009-0009-9504-0796](https://orcid.org/0009-0009-9504-0796)) | dan.lee.odinson@gmail.com

**Archived version:** Zenodo DOI: *[pending — will be added on publication]*

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

Until the Zenodo DOI is minted:

> Lee-Odinson, D. (2026). *Thermodynamic bounds and mass-trade criteria for heat rejection in orbital data centers* [Preprint].

A BibTeX entry with the DOI will be added here on publication.

## License

[Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). You may share and adapt this material for any purpose, including commercially, provided you give appropriate credit.
