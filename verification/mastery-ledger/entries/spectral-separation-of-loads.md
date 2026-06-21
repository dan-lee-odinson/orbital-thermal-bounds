> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Mastery ledger: Spectral separation of absorbed loads (short-wave vs long-wave)

- **Entry id:** `spectral-separation-of-loads`
- **Current status:** `reproduced` (code) -- director explanation and independent derivation
  `TODO`
- **Last updated:** 2026-06-21
- **Reviewed at commit:** `abef98e` (branch `main`)
- **Opened by:** B0 (Phase B core-boundary set)

## Physical question
How are the absorbed environmental loads separated by wavelength band -- short-wave (direct
solar + reflected albedo) governed by solar absorptivity, versus long-wave (Earth IR)
governed by the IR emissivity (Kirchhoff) -- when forming the effective sink?

## Why it matters
A surface's short-wave absorptivity and its long-wave emissivity are generally different
(selective coatings exploit exactly this). Collapsing them into one number mis-states the
absorbed load and therefore the effective sink the Phase B coupled solve must reject against.
Phase B inherits the separated treatment.

## Governing relation and variable definitions
Absorbed flux is summed per band, then balanced against long-wave emission:

```
q_absorbed = alpha_sw * (q_solar + q_albedo) + epsilon_lw * q_earth_IR
emission   = epsilon_lw * sigma * T^4
```

- `alpha_sw` short-wave (solar) absorptivity [-]; `epsilon_lw` long-wave emissivity [-]
- `q_solar`, `q_albedo`, `q_earth_IR` incident band fluxes [W/m^2]
- by Kirchhoff, long-wave absorptivity = `epsilon_lw`

## Assumptions
Two-band (gray-within-band) treatment; diffuse surfaces; properties constant over each band;
incidence handled via the inherited view factors and albedo model.

## Explanation in the director's own words
`TODO (director)` -- to be written without model drafting before status advances to
`explained`. Do not infer or fabricate.

## Reproduction method
```bash
python -m pytest tests/test_environment.py tests/test_sink.py -q   # environment + sink loads
python -m pytest tests/test_starcloud_spectral_balance.py -q       # spectral balance anchor
python scripts/reproduce_all.py                                    # full reproduction harness
```
Code: `orbital_thermal.spectral_radiation`, with environment/sink assembly in
`orbital_thermal.environment` and `orbital_thermal.sink`.

## Supporting evidence (by category)
- **a. source / reference:** standard spacecraft thermal control (separate solar absorptivity
  and IR emissivity; Kirchhoff's law); Bounds/Starcloud preprint treatment.
- **b. independent derivation:** the two-band balance is elementary; a director-authored or
  external re-derivation is `TODO`.
- **c. executable reproduction:** `tests/test_environment.py`, `tests/test_sink.py`,
  `tests/test_starcloud_spectral_balance.py`. Status: present and passing.
- **d. qualified external human review:** `pending`.
- **cross-model review (separate; not category d):** the Starcloud reference-architecture
  review (Phase A) exercised the spectral balance.

## Sensitivity / limiting cases
- Setting `alpha_sw = epsilon_lw` collapses to the single-property (gray) model -- a useful
  degenerate check.
- Selective coatings (`alpha_sw << epsilon_lw`) sharply reduce the absorbed solar load; the
  separation is what makes that representable.

## Known uncertainties
Real coatings are wavelength-dependent within each band and degrade on orbit (UV, atomic
oxygen); the two-band constants are a screening idealization.

## What evidence would invalidate this result
- Measured absorbed loads inconsistent with the two-band split beyond model-form error.
- A case where intra-band spectral variation dominates the result.

## Open questions / TODO
- `TODO (director)`: plain-language explanation of why two bands (and Kirchhoff) are needed.
- `TODO`: record an independent derivation (b).
- Phase B: confirm `alpha_sw` and `epsilon_lw` are carried as distinct, sourced inputs per case.
