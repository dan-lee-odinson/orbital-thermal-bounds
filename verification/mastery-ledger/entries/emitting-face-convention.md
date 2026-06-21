> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Mastery ledger: Two-sided emitting-area convention

- **Entry id:** `emitting-face-convention`
- **Current status:** `reproduced` (code) -- director explanation `TODO`
- **Last updated:** 2026-06-21
- **Reviewed at commit:** `abef98e` (branch `main`)
- **Opened by:** B0 (Phase B core-boundary set)

## Physical question
When a flat-panel radiator rejects heat from both faces, what area enters the rejection law:
the planform (one-sided) area, or the total emitting area?

## Why it matters
Phase B sizes radiator area from the inherited rejection law. A factor-of-two error in the
area convention propagates directly into every area, mass, and trade-space result. The
convention must be fixed and consistent between Phase A and Phase B.

## Governing relation and variable definitions
The rejection law uses the **emitting** area `A`:

```
A_emitting = 2 * A_planform     (two-sided flat panel)
A = Q / (epsilon * sigma * (T^4 - T_sink^4))     [m^2, emitting]
```

- `A_planform` one-sided projected area [m^2]; `A_emitting` total radiating area [m^2]
- the factor 2 applies to a flat two-sided panel radiating from both faces

## Assumptions
Both faces radiate to the same effective sink with the same emissivity; edge area is
neglected; the panel is thin and isothermal across its thickness.

## Explanation in the director's own words
`TODO (director)` -- to be written without model drafting before status advances to
`explained`. Do not infer or fabricate.

## Reproduction method
```bash
python -m pytest tests/test_published_results.py -q   # area anchors use the emitting convention
python examples/01_equilibrium_and_area.py            # worked equilibrium + area
```
Code: `orbital_thermal.radiation.required_area` (and the area handling in
`orbital_thermal.equilibrium`). Convention is exercised by the published-result area anchors.

## Supporting evidence (by category)
- **a. source / reference:** Bounds preprint area-sizing corollaries
  (DOI 10.5281/zenodo.20650893); the two-sided convention is stated with the area law.
- **b. independent derivation:** n/a -- this is a modelling **convention**, not a derived
  relation. (What can be checked is *consistency of use*, under c.)
- **c. executable reproduction:** `tests/test_published_results.py` area anchors;
  `examples/01_equilibrium_and_area.py`. Status: present and passing.
- **d. qualified external human review:** `pending`.
- **cross-model review (separate; not category d):** the Phase A audit exercised area
  results; the convention itself was not a flagged item.

## Sensitivity / limiting cases
- A single-sided radiator (one face insulated) uses `A_emitting = A_planform`; the model must
  expose which convention a case uses.
- Mis-applying the factor 2 doubles or halves area and mass -- a guard/labelling check is the
  intended Phase B protection.

## Known uncertainties
Real radiators have non-radiating mounting/edge area and face-to-face view obstruction in
packed arrays; the clean "2 x planform" is an idealization for screening.

## What evidence would invalidate this result
- A case where the two faces see materially different sinks (so the factor 2 is wrong).
- Packed-array geometry where one face is substantially obstructed.

## Open questions / TODO
- `TODO (director)`: plain-language explanation of why emitting area, not planform, is correct.
- Phase B: ensure every case records which area convention it uses (one- vs two-sided).
