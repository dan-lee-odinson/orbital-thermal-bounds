> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Mastery ledger: Solid thermal network (junction-to-cold-plate)

- **Entry id:** `solid-thermal-network`
- **Current status:** `reproduced` (code) -- director explanation and independent derivation
  `TODO`
- **Last updated:** 2026-07-03
- **Opened by:** B2 (Phase B solid thermal network)

## Physical question
What is the steady conduction temperature rise from a chip junction to the cold-plate base,
through a solid spreader with a finite contact interface, in the reduced-order model?

## Why it matters
This is the chip-side leg of the B0 coupled model (Section 4.1a, R1). It sets the junction
temperature for a given cold-plate base temperature and chip heat, and therefore the junction
margin that every ranked architecture must satisfy. A spreading-resistance error propagates
directly into junction-temperature and area/mass conclusions.

## Governing relation and variable definitions
```
R_total = R_conduction + R_spreading + R_contact          [K/W]
T_j     = T_base + Q_chip * R_total                        [K]
R_conduction = L / (k A)
R_spreading  = psi / (sqrt(pi) k a),  psi = 0.5 (1-eps)^{3/2} phi   (Yovanovich / Lee 1995)
R_contact    = 1 / (h_c A)
```
- `L` conduction length, `A` area, `k` conductivity, `a` source radius, `b` plate radius,
  `t` thickness; `eps=a/b`, `tau=t/b`; `phi` the isothermal/Biot factor; `h_c` contact
  conductance. Chip heat `Q_chip` only (pump heat is added to the fluid downstream).

## Assumptions
Steady, 1-D series conduction with a Yovanovich spreading term; **isotropic** conductivity;
isothermal cold-plate base by default (finite-Biot optional); circular source on a coaxial
disk with `a < b`. Anisotropic/direction-aware conduction is deferred.

## Explanation in the director's own words
`TODO (director)` -- to be written without model drafting before status advances to
`explained`. Do not infer or fabricate.

## Reproduction method
```bash
python -m pytest tests/test_solid_network.py -q
python -c "from orbital_thermal import solid_network as s; import math; \
p=s.build_ranked_path(material='copper', length_m=0.003, area_m2=math.pi*0.01**2, \
source_radius_m=0.01, plate_radius_m=0.03, thickness_m=0.003, \
contact_conductance_W_m2K=1e4, contact_source='example'); \
print('R_total', round(p.total_K_per_W,4), 'K/W')"
```
Code: `orbital_thermal.solid_network`. Conductivity provenance: `orbital_thermal.registry`.

## Supporting evidence (by category)
- **a. source / reference:** Lee, Song, Au, Moran (1995), constriction/spreading-resistance
  model (registry entry `thermal.spreading_resistance`); Incropera Table A.1 conductivities.
- **b. independent derivation:** `TODO` -- the series-resistance algebra is elementary; a
  director-authored or external re-derivation of the spreading form is not yet recorded.
- **c. executable reproduction:** `tests/test_solid_network.py` (analytic exactness +
  spreading-limit checks + rank-eligibility enforcement). Status: present and passing.
- **d. qualified external human review:** `pending`.
- **cross-model review (separate; not category d):** optional B2 spot-check not yet run.

## Sensitivity / limiting cases
- Point source / thick plate / isothermal base -> `R_spread ~ 0.282/(k a)` (cf isoflux
  `0.270/(k a)`; ~4% reduced-order fit).
- Source filling the plate (`eps -> 1`) -> spreading resistance -> 0.
- Convective base (finite Biot) -> spreading resistance >= isothermal-base value.

## Known uncertainties
The Yovanovich closed form is a reduced-order fit (few-percent vs the exact series);
contact resistance is interface-specific and `source_required`; the isothermal-base default
idealizes the cold-plate boundary.

## What evidence would invalidate this result
- A finite-element spreading computation diverging from the closed form beyond the stated
  fit error.
- Evidence the isothermal-base idealization is inadequate for the intended cold-plate.

## Open questions / TODO
- `TODO (director)`: plain-language explanation of spreading resistance and the isothermal
  vs convective base.
- `TODO`: record an independent derivation (b).
- Deferred: anisotropic/direction-aware conductivity; convective-film coupling (B3).
