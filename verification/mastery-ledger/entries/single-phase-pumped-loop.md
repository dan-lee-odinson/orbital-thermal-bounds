> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Mastery ledger: Single-phase pumped loop (hydraulics, film, pump energy, phase margins)

- **Entry id:** `single-phase-pumped-loop`
- **Current status:** `reproduced` (code) -- director explanation and independent derivation
  `TODO`
- **Last updated:** 2026-07-03
- **Opened by:** B3 (Phase B single-phase pumped loop)

## Physical question
For a single-phase liquid coolant loop, what are the pressure drop, pump power/heat, convective
film coefficient, and single-phase margins, given geometry, mass flow, and heat load?

## Why it matters
This is the fluid-transport leg of the B0 coupled model. The film resistance closes the
junction-to-fluid path from B2; the pressure drop sets pump power and the hydraulic heat added
to the rejected load; the per-segment margins keep the coolant single-phase. All three feed the
B4 coupled solve and the ranking gates.

## Governing relation and variable definitions
```
Re = m_dot D / (A mu);   f = 64/Re (laminar) or Haaland (turbulent)
dP = (f L/D + sum K) rho v^2 / 2                          [Pa]
Nu = 4.36 / 3.66 (laminar) or Gnielinski (turbulent);  h = Nu k / D_h
R_film = 1 / (h A_wetted)                                  [K/W]
P_hyd = m_dot dP / rho;  P_elec = P_hyd/(eta_pump eta_motor);  fluid_heat = P_hyd
single-phase margins: P - P_sat(T) > 0, T - T_triple > 0, T_crit - T > 0
```
Properties `rho, cp, k, mu, Pr` are evaluated per-state at `(T,P)` via `orbital_thermal.fluids`.

## Assumptions
Steady, single-phase incompressible-liquid loop; circular tube; auto regime selection with a
warned transition blend; hydraulic dissipation heats the fluid (B0 4.7); uniform heat over the
marched segments; properties from the pinned CoolProp backend.

## Explanation in the director's own words
`TODO (director)` -- to be written without model drafting before status advances to
`explained`. Do not infer or fabricate.

## Reproduction method
```bash
python -m pytest tests/test_pumped_loop.py -q
```
Code: `orbital_thermal.pumped_loop` (+ per-state properties in `orbital_thermal.fluids`).

## Supporting evidence (by category)
- **a. source / reference:** Incropera (Gnielinski, laminar Nu), White (friction), the B1
  correlation registry entries; CoolProp 7.2.0 properties.
- **b. independent derivation:** laminar friction reproduces Hagen-Poiseuille `32 mu L v/D^2`
  exactly (checked); a director-authored derivation is `TODO`.
- **c. executable reproduction:** `tests/test_pumped_loop.py` (23 tests: Poiseuille, regime
  selection, pump accounting, Nusselt/film, phase-margin failure, energy balance,
  rank-eligibility, CoolProp per-state). Status: present and passing.
- **d. qualified external human review:** `pending`.
- **cross-model review (separate; not category d):** optional B3 spot-check not yet run.

## Sensitivity / limiting cases
- Laminar friction -> exact Hagen-Poiseuille.
- Under-pressured loop (`P < P_sat`) -> `LoopPhaseError` (subcooling violated).
- Segment count converges (N=5 vs N=40 outlet temperature within 1e-3).

## Known uncertainties
Turbulent correlations carry their own (few-to-ten-percent) uncertainty; the transition band is
an approximate blend; uniform-heat-per-segment is a reduced-order idealization; contact/minor-
loss inventories are case inputs.

## What evidence would invalidate this result
- A CFD/loop measurement diverging from the correlations beyond their stated ranges.
- Evidence the single-phase idealization is inadequate for the intended operating envelope.

## Open questions / TODO
- `TODO (director)`: plain-language explanation of the loop hydraulics/thermics and the
  hydraulic-into-fluid pump-heat convention.
- `TODO`: record an independent derivation (b) beyond the Poiseuille check.
- Deferred: two-phase transport; developing-flow/minor-loss inventories; maldistribution model.
