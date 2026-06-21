 > **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Mastery ledger: Radiative equilibrium temperature and net rejection (area law)

- **Entry id:** `radiative-equilibrium-and-net-rejection`
- **Current status:** `reproduced` (code) -- director explanation and independent derivation `TODO`
- **Last updated:** 2026-06-20
- **Reviewed at commit:** `825b904` (branch `main`)

## Physical question
What steady radiator temperature `T` is required to reject a heat load `Q` through an
emitting area `A` to an effective radiative sink, and what is the net rejected flux per
unit area?

## Why it matters
This is the radiator-boundary relation that the entire project rests on, and the one
Phase B reuses as its terminal condition: chip-to-radiator transport delivers heat at an
*achievable* radiator temperature, after which area and net rejection follow from this
law. An error here propagates to every sizing result.

## Governing relation and variable definitions
Net flux:  `q_net = emissivity * sigma * (T^4 - T_sink^4)`  [W/m^2]
Equilibrium temperature:  `T = ( Q / (emissivity * sigma * A) + T_sink^4 )^(1/4)`  [K]
Required area:  `A = Q / (emissivity * sigma * (T^4 - T_sink^4))`  [m^2]

- `T` radiator temperature [K]; `T_sink` effective sink temperature [K]
- `emissivity` in (0, 1]; `sigma` Stefan-Boltzmann constant [W m^-2 K^-4]
- `Q` heat load [W]; `A` *emitting* area [m^2] (two-sided panel: emitting = 2 x planform)

## Assumptions
Gray, diffuse, isothermal, one-node radiator; far-field radiation only; lumped effective
sink `T_sink` standing in for the orbital environment; `T > T_sink` for net rejection.

## Explanation in the director's own words
`TODO (director)` -- to be written without model drafting before status advances to
`explained`. Do not infer or fabricate.

## Reproduction method
```bash
python -m pytest tests/test_published_results.py -q       # area-law and inverse anchors
python examples/01_equilibrium_and_area.py                # worked equilibrium + area
python scripts/reproduce_all.py                           # full reproduction harness
```
Code: `orbital_thermal.radiation.net_flux` / `required_area`;
`orbital_thermal.equilibrium.equilibrium_temperature` / `radiative_capacity`.
Anchor (Corollary 1.2): 1 MW at 293 K, emissivity 0.91, zero sink -> ~2630 m^2 emitting.

## Supporting evidence (by category)
- **a. source / reference:** Bounds preprint, Lemma 1 / Corollaries 1.1-1.2
  (DOI 10.5281/zenodo.20650893).
- **b. independent derivation:** `TODO` (algebraic inversion is elementary; a director-
  authored or external re-derivation is not yet recorded).
- **c. executable reproduction:** `tests/test_published_results.py`,
  `tests/test_smoke.py`, `examples/01_equilibrium_and_area.py`; `equilibrium <-> capacity`
  round-trip asserted. Status: present and passing.
- **d. qualified external human review:** `pending` -- no qualified external human
  subject-matter review of this result has been obtained.
- **cross-model review (recorded separately; not category d):** partial -- the GPT audit
  reviewed the surrounding radiative model; this specific identity was not a flagged item.

## Sensitivity / limiting cases
- `T_sink = 0` reduces to `q = emissivity*sigma*T^4` (checked).
- `T -> T_sink` degenerates (no net rejection); inputs with `T <= T_sink` are rejected.
- Emissivity bounds enforced in (0, 1]; non-finite / non-positive inputs rejected.

## Known uncertainties
The reduced-order, one-node, gray-body model-form error dominates the numerical error by
orders of magnitude. The lumped `T_sink` abstraction is an idealization of a
time-varying orbital environment.

## What evidence would invalidate this result
- A measured flown-radiator net rejection diverging from the law beyond model-form error.
- A derivation error in the area law or its inverse.
- Evidence that the gray-body / isothermal assumptions are inadequate for the intended
  screening use (which would narrow applicability, not the algebra).

## Open questions / TODO
- `TODO (director)`: plain-language explanation.
- `TODO`: record an independent derivation (b).
- `pending`: targeted external **human** review (d) of the radiator-boundary assumptions
  (the GPT cross-model audit does not satisfy this).
