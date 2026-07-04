> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Mastery ledger: Stage-1 common-envelope architecture cases

- **Entry id:** `architecture-cases`
- **Current status:** `reproduced` (code) -- director explanation and independent derivation
  `TODO`
- **Last updated:** 2026-07-04
- **Opened by:** B5 (Phase B architecture cases)

## Physical question
Across the coolant x solid-path case space, which combinations are rank-eligible under a common
Stage-1 operating envelope, which are sensitivity/source-required/unsupported/rejected, and what
are the rank-eligible cases' coupled temperatures, pump power, and modeled component mass?

## Why it matters
B5 is where the B1-B4 machinery is exercised as a **case space with verdicts**: it proves the
no-invention gates actually classify, solve, reject, and separate ranked vs sensitivity cases,
and it produces the reference cases the B6 trade engine will assemble into Pareto fronts.

## Governing relation and variable definitions
Classification is decided by the real gates: coolant backend rank-eligibility (B3), ranked solid
path (B2: isotropic + spreading + cited contact), radiator contract (B4: C1, or C2 with
excluded-face evidence; C3 deferred), and, for provenance-eligible cases, the B4 coupled
feasibility gates under the common `Stage1Envelope`. Modeled component mass follows 4.6
(containment ideal shell) and 4.8a (modeled component mass, not total-system).

## Assumptions
One declared Stage-1 common operating point (all design variables); C1 shielded contract;
single-phase liquid coolant; reduced-order B4 coupled solve; ideal-shell containment lower bound;
mass accounting incomplete by construction (accumulator/pump/motor/manifolds/etc. excluded).

## Explanation in the director's own words
`TODO (director)` -- to be written without model drafting before status advances to
`explained`. Do not infer or fabricate.

## Reproduction method
```bash
python -m pytest tests/test_architecture_cases.py -q
python scripts/generate_architecture_matrix.py   # regenerates docs/architecture-case-matrix.md
```
Code: `orbital_thermal.architecture_cases` (consumes B1 registry, B2 solid_network, B3
pumped_loop/fluids, B4 coupled_model).

## Supporting evidence (by category)
- **a. source / reference:** the 4.8 ranking gates and 4.8a mass-accounting limitation; the B1
  registry statuses that drive the classification (CO2 sensitivity; PGW/APG/diamond
  source-required).
- **b. independent derivation:** the classification precedence and the 4.6 containment relations
  are documented in `docs/architecture-cases.md`; a director-authored derivation is `TODO`.
- **c. executable reproduction:** `tests/test_architecture_cases.py` (18 tests): 16-combo
  classification (4 rank-eligible / 4 sensitivity / 8 source-required) with reason codes; count
  summary 16/4/12; rank-eligible cases feasible + ranked-only; sensitivity runs only with
  parametric inputs and never rank-eligible; CO2/PGW not evaluable; REJECTED-by-physics
  (junction limit); modeled-component-mass components/labels/exclusions and the thin/thick-wall
  containment branches. Status: present and passing.
- **d. qualified external human review:** `pending`.
- **cross-model review (separate; not category d):** optional B5 spot-check available;
  intermediate milestone, so no mandatory review.

## Sensitivity / limiting cases
- CO2/PGW have no rank-eligible backend -> classification-only (not evaluable in Stage-1).
- Anisotropic APG/diamond -> source-required; evaluable only as a labelled parametric sensitivity.
- A tight spreader (high junction) -> a provenance-eligible case is REJECTED by the junction gate.

## Known uncertainties
Modeled component mass is an incomplete lower bound (many components excluded by construction,
4.8a); the common envelope is a Stage-1 design choice, not an optimized or published point; the
parametric sensitivity conductivities are uncited bounds, never ranked.

## What evidence would invalidate this result
- A gate misclassifying a combination (e.g., ranking a sensitivity-only coolant).
- A ranked case that fails a feasibility gate but is still reported as ranked.
- A mass total presented as total-system/launch mass despite the incomplete accounting.

## Open questions / TODO
- `TODO (director)`: plain-language explanation of the case-space classification and the
  modeled-component-mass limitation.
- `TODO`: independent derivation record (b) beyond the docs argument.
- Deferred: CO2/PGW property backends; anisotropic (cited directional) material paths; the B6
  Pareto trade engine; total thermal-system mass closure (accumulator/expansion).
