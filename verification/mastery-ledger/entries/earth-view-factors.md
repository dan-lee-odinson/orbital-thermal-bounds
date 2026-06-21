> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Mastery ledger: Exact tilted-plate-to-sphere Earth view factor

- **Entry id:** `earth-view-factors`
- **Current status:** `reproduced` (code), cross-checked -- director explanation and
  director-authored independent derivation `TODO`
- **Last updated:** 2026-06-21
- **Reviewed at commit:** `abef98e` (branch `main`)
- **Opened by:** B0 (Phase B core-boundary set)

## Physical question
What fraction of a tilted flat plate's hemisphere is subtended by the Earth (the view factor
`F`) at a given altitude and plate tilt, used to scale Earth-IR and albedo loads into the
effective sink?

## Why it matters
The Earth view factor sets how much planetary IR and albedo the radiator absorbs, which sets
the effective sink temperature that the Phase B coupled solve rejects against. The edge-on
("paper three") correction showed that an approximate view factor materially shifts results,
so Phase B reuses the **exact** closed form, not an approximation.

## Governing relation and variable definitions
Exact tilted-plate-to-sphere view factor (closed form) as implemented in
`orbital_thermal.mccalip_exact_vf`. Reference operating point: at 550 km altitude and 90 deg
tilt (edge-on), `F ~= 0.258`, versus the approximate `0.25` used in the original external
model.

- `F` plate-to-Earth view factor [-]; altitude [km]; tilt angle [deg]
- closed-form expression of the differential plate element viewing a sphere

## Assumptions
Differential-element (small-plate) idealization; spherical Earth; diffuse exchange; far-field
geometry. The element view factor stands in for a finite panel.

## Explanation in the director's own words
`TODO (director)` -- to be written without model drafting before status advances to
`explained`. Do not infer or fabricate.

## Reproduction method
```bash
python -m pytest tests/test_mccalip_exact_vf.py -q   # exact VF unit tests
python verify_paper3.py                              # view-factor decomposition (paper three)
python examples/02_edge_on_correction.py             # +6.35 K edge-on correction demo
```
Code: `orbital_thermal.mccalip_exact_vf`. Numerical-vs-symbolic agreement at ~1e-9 is
recorded in the V&V credibility matrix.

## Supporting evidence (by category)
- **a. source / reference:** Edge-on view-factor correction preprint (paper three,
  DOI 10.5281/zenodo... see CITATION.cff); standard view-factor literature for the closed form.
- **b. independent derivation:** the closed form is derived in the preprint; a
  **director-authored** independent re-derivation is `TODO`.
- **c. executable reproduction:** `tests/test_mccalip_exact_vf.py`, `verify_paper3.py`,
  `examples/02_edge_on_correction.py`; numerical vs symbolic ~1e-9. Status: present and passing.
- **d. qualified external human review:** `pending`.
- **cross-model review (separate; not category d):** the GPT audit reviewed the edge-on
  correction and view-factor decomposition during Phase A.

## Sensitivity / limiting cases
- Tilt 0 deg (facing Earth) vs 90 deg (edge-on) bound the view-factor range; the edge-on case
  is the one that produced the +6.35 K correction.
- Altitude sets the angular radius of the Earth; higher orbits reduce `F`.

## Known uncertainties
The differential-element idealization neglects finite-panel self-view and gradient across a
large panel; adequate for screening, not for detailed panel design.

## What evidence would invalidate this result
- A finite-panel computation diverging from the element view factor beyond model-form error.
- An error found in the closed-form derivation or its numerical evaluation.

## Open questions / TODO
- `TODO (director)`: plain-language explanation of the tilted-plate-to-sphere geometry.
- `TODO`: record a director-authored or external independent derivation (b).
- Phase B: confirm the exact VF (not 0.25) feeds the orbital-boundary sink in reported cases.
