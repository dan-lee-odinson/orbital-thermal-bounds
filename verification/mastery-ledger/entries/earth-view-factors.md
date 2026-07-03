> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Mastery ledger: Exact tilted-plate-to-sphere Earth view factor

- **Entry id:** `earth-view-factors`
- **Current status:** `reproduced` (code), cross-checked -- director explanation and
  director-authored independent derivation `TODO`
- **Last updated:** 2026-06-21 (rev 1)
- **Reviewed at commit:** `abef98e` (branch `main`)
- **Opened by:** B0 (Phase B core-boundary set)
- **Correction note (rev 1, review F9):** an earlier draft of this entry stated the exact
  factor `~0.258` was compared against an approximate `0.25`. That comparator was **wrong**.
  The repository's `mccalip_exact_vf.py` documents the actual comparison: McCalip's cos-tilt
  heuristic with a 5%-of-nadir edge-on floor orbit-averages to **~0.021 per face**, versus
  the exact **~0.258** -- a **~12x underestimate**. Corrected below.

## Physical question
What fraction of a tilted flat plate's hemisphere is subtended by the Earth (the view factor
`F`) at a given altitude and plate tilt, used to scale Earth-IR and albedo loads into the
effective sink?

## Why it matters
The Earth view factor sets how much planetary IR and albedo the radiator absorbs, hence the
effective sink the Phase B coupled solve rejects against. At McCalip's default geometry
(beta = 90 deg, 550 km) a sun-tracking bifacial panel is edge-on to Earth, where his heuristic
floor badly underestimates the true view factor; Phase B therefore reuses the **exact** closed
form, not the heuristic.

## Governing relation and variable definitions
The exact tilted-plate-to-sphere view factor is `env.sphere_view_factor(altitude, tilt)`.
Per-face orbit averages for a sun-tracking bifacial panel are
`mccalip_exact_vf.exact_per_face_view_factors`. At beta = 90 deg, 550 km:

```
McCalip cos-tilt heuristic, 5%-of-nadir edge-on floor:  ~0.021 per face (orbit-averaged)
exact tilted-plate-to-sphere view factor:               ~0.258
ratio:                                                   ~12x underestimate
```

Substituting the exact per-face view factor into McCalip's own heat balance:

```
335.75 K (McCalip, replicated)  ->  342.10 K (exact edge-on VF)   = +6.35 K
```

- `F` plate-to-Earth view factor [-]; altitude [km]; tilt angle from nadir [deg]
- only the view factor changes; truncated sigma, rounded deep-space temperature, constants,
  and orbit sampling are retained, so the +6.35 K shift is attributable to geometry alone

## Assumptions
Differential-element (small-plate) idealization; spherical Earth; diffuse exchange; far-field
geometry; McCalip's 72-point orbit sampling and per-face tilt cosines are retained for the
comparison.

## Explanation in the director's own words
`TODO (director)` -- to be written without model drafting before status advances to
`explained`. Do not infer or fabricate.

## Reproduction method
```bash
python -m pytest tests/test_mccalip_exact_vf.py -q   # exact VF + per-face + correction tests
python verify_paper3.py                              # view-factor decomposition (paper three)
python examples/02_edge_on_correction.py             # +6.35 K edge-on correction demo
```
Code: `orbital_thermal.mccalip_exact_vf` (`exact_per_face_view_factors`,
`equilibrium_temperature_with_view_factors`, `eqtemp_exact_vf`, `correction_table_vs_beta`),
built on `environment.sphere_view_factor`. The module reproduces McCalip's number exactly when
fed his own view factors, isolating the geometry effect.

## Supporting evidence (by category)
- **a. source / reference:** edge-on view-factor correction preprint (paper three; see
  `CITATION.cff` for the DOI); standard view-factor literature for the closed form.
- **b. independent derivation:** the closed form is derived in the preprint; a
  **director-authored** independent re-derivation is `TODO`.
- **c. executable reproduction:** `tests/test_mccalip_exact_vf.py`, `verify_paper3.py`,
  `examples/02_edge_on_correction.py`; numerical vs symbolic ~1e-9 (V&V matrix). Status:
  present and passing.
- **d. qualified external human review:** `pending`.
- **cross-model review (separate; not category d):** the GPT audit reviewed the edge-on
  correction during Phase A; the **B0 re-review (F9)** caught the mis-stated comparator now
  corrected here.

## Sensitivity / limiting cases
- Tilt 0 deg (Earth-facing) vs 90 deg (edge-on) bound the view-factor range; the edge-on case
  drives the +6.35 K correction and the ~12x heuristic underestimate.
- Altitude sets the Earth's angular radius; higher orbits reduce `F`.

## Known uncertainties
The differential-element idealization neglects finite-panel self-view and across-panel
gradients; adequate for screening, not detailed panel design.

## What evidence would invalidate this result
- A finite-panel computation diverging from the element view factor beyond model-form error.
- An error in the closed-form derivation or its numerical evaluation.

## Open questions / TODO
- `TODO (director)`: plain-language explanation of the tilted-plate-to-sphere geometry and why
  the edge-on heuristic floor (~0.021) is a ~12x underestimate of the exact ~0.258.
- `TODO`: record a director-authored or external independent derivation (b).
- Phase B: confirm the exact per-face view factor (not the heuristic floor) feeds the orbital
  boundary in reported cases.
