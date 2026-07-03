> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Mastery ledger: Radiator attitude and sun-shielding contract

- **Entry id:** `radiator-attitude-and-sun-shielding`
- **Current status:** `reproduced` (code; enforced by a hard guard) -- director explanation
  `TODO`
- **Last updated:** 2026-06-21 (rev 1)
- **Reviewed at commit:** `abef98e` (branch `main`)
- **Opened by:** B0 rev 1 (Phase B core-boundary set; review F3/F9)

## Physical question
Under what attitude assumption is the inherited effective-sink model valid, and what direct-
solar load does it omit?

## Why it matters
The Phase A effective-sink model **omits direct solar flux on the radiator face** and is valid
only when that face is sun-shielded (an anti-solar attitude or an external shade). This is a
load-bearing assumption: if a Phase B reported case lets a face see the Sun, the inherited
sink under-predicts the absorbed load and the rejection result is wrong. The model does **not**
verify attitude; the caller must assert it. Phase B must carry this contract explicitly rather
than inherit it silently.

## Governing relation and variable definitions
The effective sink (per `sink.py`) is

```
sigma * T_sink_eff^4 = q_IR + (alpha_s / eps) * q_albedo + sigma * T_space^4
```

with **no direct-solar term**. The code enforces the assumption with a hard guard:
`assume_sun_shielded` must be boolean `True` (truthy non-booleans are rejected); `False`
raises `NotImplementedError` because direct-solar loading from the surface-normal . Sun-vector
is not modelled.

- `alpha_s` solar absorptivity; `eps` IR emissivity (IR absorptivity = eps by Kirchhoff)
- `q_IR`, `q_albedo` absorbed Earth-IR and reflected-solar fluxes [W/m^2]
- the omitted term is direct solar on the radiator face

## Assumptions
Cold-side-only environment; radiator face receives no direct sunlight (anti-solar attitude or
shade); attitude is asserted, not computed.

## Explanation in the director's own words
`TODO (director)` -- to be written without model drafting before status advances to
`explained`. Do not infer or fabricate.

## Reproduction method
```bash
python -m pytest tests/test_sink.py -q   # includes the shielding-guard behavior
```
Code: `orbital_thermal.sink` (`_require_shielding`, `sink_temperature_series`,
`orbital_effective_sink_temperature`); the guard is the single point where the direct-solar
omission is asserted for scalar, profile, and transient paths.

## Supporting evidence (by category)
- **a. source / reference:** standard spacecraft-thermal practice (radiators oriented away
  from the Sun; direct solar falls on the back face); `sink.py` module documentation.
- **b. independent derivation:** n/a -- this is an applicability **contract**, not a derived
  relation.
- **c. executable reproduction:** the `assume_sun_shielded` guard and its tests in
  `tests/test_sink.py`. Status: present and passing (the guard is enforced).
- **d. qualified external human review:** `pending`.
- **cross-model review (separate; not category d):** the B0 re-review (F3/F9) identified that
  this load-bearing assumption was missing from the core-boundary set; this entry adds it.

## Sensitivity / limiting cases
- A sun-facing or tilted face that sees direct solar **violates** the contract; such a case is
  out of the inherited model's applicability and must not be reported without a direct-solar
  term.
- The contract pairs with `emitting-face-convention`: the two-sided area assumes both faces see
  comparable (shielded) environments.

## Known uncertainties
Real attitudes wander; shades have finite size and edge leakage. The binary shielded/not
contract is a screening idealization; it narrows applicability rather than quantifying partial
illumination.

## What evidence would invalidate this result
- A reported configuration where the radiator face provably sees direct solar yet uses the
  shielded sink.
- Addition of a direct-solar term that materially changes a ranking.

## Open questions / TODO
- `TODO (director)`: plain-language statement of the attitude/shielding assumption and why
  direct-solar omission is acceptable for the intended cold-side screening.
- Phase B: every reported (orbital-boundary) case must assert `assume_sun_shielded=True` and
  record the attitude justification, or carry a direct-solar extension.
