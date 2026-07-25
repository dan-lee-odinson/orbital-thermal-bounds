> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Mastery ledger: two-phase flow-boiling heat acquisition

- **Entry id:** `two-phase-flow-boiling-heat-acquisition`
- **Current status:** `derived`
- **Last updated:** 2026-07-25
- **Reviewed at commit:** S2 build commits on branch `stage-2/s2-evaporator`

This is S0 §4 central claim **1** — vapour quality, the boiling heat-transfer
coefficient, the ONB/saturated-regime policy, and the CHF/dryout rejection bands on
**local** wall flux — introduced at milestone S2 as S0 §4 requires.

**Why `derived` and not `reproduced`.** The status is deliberately one step below the
Stage-1 entries. The *policy* layer (regime gate, CHF bands, local-flux discipline,
domain guards) is fully executable and mutation-witnessed, and the *one* implemented
correlation reproduces its own analytic limiting case exactly. But the claim as S0
words it also covers the CHF band's underlying correlation, and **no CHF correlation
is implemented** — its source attribution could not be established (see below).
A claim whose CHF leg rests on a blocked entry has not been reproduced end to end, and
recording it as `reproduced` would overstate the evidence.

## Physical question

When a coolant is allowed to boil in the chip-acquisition (evaporator) section, how
much heat can be moved per unit wall area, at what wall superheat, and at what point
does the wall dry out and the mechanism fail?

## Why it matters

Stage 1 is single-phase by design and therefore cannot determine a Starcloud-like
transport architecture (S0 §1). Two-phase acquisition is the physics extension whose
absence most limits what the trade study may conclude. Everything downstream —
condenser sizing (S3), the coupled solve (S4), and any two-phase Pareto content (S6) —
rests on this acquisition model. If the boiling coefficient or the dryout limit is
wrong, every two-phase area, pump-power and inventory number built on it is wrong, and
a case that would dry out in flight could be ranked as feasible.

## Governing relation and variable definitions

**Loop state / vapour quality** (S0 §3):

    x = (h - h_f(P)) / h_fg(P),    0 <= x <= 1

`h` specific enthalpy [J/kg]; `h_f`, `h_g` saturated liquid/vapour enthalpy [J/kg];
`h_fg = h_g - h_f` latent heat [J/kg]; `P` pressure [Pa], bounded by
`P_triple < P < P_crit`.

**Flow-boiling HTC** — Gungor & Winterton (1986), vertical / non-stratified form:

    alpha_tp = E alpha_L + S alpha_nb
    E        = 1 + 24000 Bo^1.16 + 1.37 (1/X_tt)^0.86
    S        = [1 + 1.15e-6 E^2 Re_L^1.17]^-1
    alpha_L  = 0.023 Re_L^0.8 Pr_L^0.4 k_f / D          (Dittus-Boelter, liquid fraction)
    alpha_nb = 55 p_r^0.12 (-0.4343 ln p_r)^-0.55 M^-0.5 q''^0.67    (Cooper 1984)
    Re_L     = G (1-x) D / mu_f
    Pr_L     = cp_f mu_f / k_f
    X_tt     = ((1-x)/x)^0.9 (rho_g/rho_f)^0.5 (mu_f/mu_g)^0.1
    Bo       = q'' / (G h_fg)

`alpha` heat-transfer coefficient [W/m²/K]; `G` mass flux [kg/m²/s]; `q''` **local
modeled** wall heat flux [W/m²]; `D` hydraulic diameter [m]; `p_r` reduced pressure
[-]; `M` molar mass [g/mol — the Cooper term is dimensional]; `rho`, `mu`, `k`, `cp`
density [kg/m³], dynamic viscosity [Pa·s], conductivity [W/m/K], isobaric specific
heat [J/kg/K], subscripts `f` liquid and `g` vapour.

**CHF / dryout bands** (S0 §3, director ruling 9.5), on the **local** wall flux:

    q''/CHF <= 0.5      rank-eligible
    0.5 < q''/CHF < 1   parametric / sensitivity — reported, NOT ranked
    q''/CHF >= 1        dryout — rejected

A **modelling margin, not flight certification.**

## Assumptions

- **Saturated flow boiling, wetted wall.** The HTC is valid only while the wall is
  wetted; a superheated / post-dryout state is rejected rather than evaluated.
- **Vertical / non-stratified form.** The GW86 horizontal-channel Froude/stratification
  de-rating is deliberately **not** applied: it models gravitational phase
  stratification, a 1-g effect with no microgravity meaning. A **recorded modelling
  decision**, mirroring S0 §3's treatment of `dP_static ≈ 0`.
- **1-g correlation basis.** Not microgravity-validated, and no such claim is made.
- **Screening level.** A single operating point is evaluated and classified; there is
  no coupled solve, no pressure drop, and no condenser.
- **Pinned properties.** CoolProp HEOS 7.2.0; ammonia (reference) and water
  (secondary) only — every other coolant is source-gated.

## Explanation in the director's own words

TODO (director)

## Reproduction method

```bash
pytest tests/test_two_phase_evaporator.py tests/test_two_phase_registry.py -q
```

Expected: 71 passed. The full suite is `630 passed, 3 xfailed` with CoolProp 7.2.0
installed (baseline before S2: `587 passed, 3 xfailed`).

Witness that each check can fail:

```bash
python scripts/witness_s2_checks.py
```

Expected: `16/16 checks witnessed failing on purpose.`

Reference point (ammonia, `P = 1.0 MPa`, `G = 300 kg/m²/s`, `x = 0.30`,
`q'' = 5.0e4 W/m²`, `D = 3.0 mm`): `alpha_tp ≈ 2.80e4 W/m²/K`. Saturation anchors at
300 K: `h_fg = 1 158 051 J/kg`, `sigma = 0.02006 N/m`.

## Supporting evidence (by category)

- **a. source / reference:** Gungor & Winterton (1986), *Int. J. Heat Mass Transfer* —
  **primary paper not obtained.** The executable form was transcribed from Thome,
  *Engineering Data Book III*, Ch. 10 §10.3.3, Eqs. [10.3.20]–[10.3.23] with supporting
  [10.3.4]–[10.3.6], [10.3.8], [10.3.15]. The Cooper (1984) nucleate term was
  independently cross-checked against Shah (2022), *Int. J. Refrigeration*
  137:103–116 Eq. (25) and agrees term by term. **CHF: no source established — see
  "Known uncertainties". ONB: no usable source — promotion attempted and declined.**
- **b. independent derivation:** partial. The `x → 0`, `q'' → 0` limit is derived
  analytically (`E → 1`, `X_tt → ∞`, `alpha_nb → 0`) and asserted to reproduce the
  Dittus-Boelter base to floating-point tolerance. The Cooper term is rebuilt factor by
  factor in a closed-form hand check. The full correlation is **not** independently
  re-derived.
- **c. executable reproduction:** `tests/test_two_phase_evaporator.py` (S0 §6 gates 1,
  3, 4, 5), `tests/test_two_phase_registry.py` (exact-set and locator↔evaluate
  invariants), `scripts/witness_s2_checks.py` (16/16 mutations witnessed).
- **d. qualified external review:** `pending`. Sol's cross-model review is category
  **c** and is **not** level d.

## Sensitivity / limiting cases

Gate 1 is covered by **four separate** tests, as S0 §6 requires — the endpoint check is
necessary but not sufficient:

1. **Subcooled forced convection** — classified subcooled, sensitivity-only.
2. **The ONB transition** — the gate flips verdict across `x = 0`, checked from both
   sides at `±1e-6`; the transition itself is the object under test.
3. **Saturated flow boiling** — HTC evaluates; the two-phase coefficient must strictly
   exceed `alpha_L + alpha_nb`, which is reachable only if `E > 1`.
4. **`x → 0` recovery** — two distinct claims, kept separate because only one is exact:
   - **Exact:** collapses to GW86's own Dittus-Boelter base (rel. 1e-12).
   - **Banded, not exact:** Stage-1 `pumped_loop` uses **Gnielinski**, so exact
     recovery is *not* expected and is not manufactured. Agreement is ~1% at
     `Re ≈ 1.1e4`, widening to ~10% near `Re ≈ 4.5e3`. A companion test asserts the two
     **diverge** below the turbulent threshold (ratio > 2 at `Re ≈ 2.3e3`), so the
     banded claim cannot be misread as holding everywhere.

Also checked: monotonicity in quality and mass flux; `X_tt` falling with quality;
`T_sat(P)` monotonic and inverting `saturation_pressure`; all three CHF bands including
both boundaries (`0.5` ranks, `1.0` rejects); every declared domain axis driven out of
range with the guard required to fire.

## Known uncertainties

1. **No CHF correlation is implemented — the claim's dryout leg is blocked.**
   `two_phase.chf.shah_2015` was not implemented because its attribution could not be
   established. There is no single "Shah (2015)" general CHF correlation: Shah published
   two distinct 2015 CHF papers (vertical annuli, *Heat Transfer Engineering*
   37(6):557–570; horizontal channels, *Int. J. Refrigeration* 59:37–52), and the
   registry citation identifies neither, though they apply to different geometries. The
   declared `pr_reduced` range 0.0014–0.96 is verifiably the database range of **Shah
   (1987)**, *IJHFF* 8(4):326–335, per Shah's own *Fluids* 2023, 8, 90 §3.1 — which
   still treats the 1987 correlation as the most-verified general one for tubes. The
   band *policy* ships and is fully tested; the correlation behind it does not exist in
   this build, so a case needing a computed CHF is **blocked**, never silently ranked.
2. **The reference coolant is outside the reference correlation's fluid database.** The
   GW86 database is water, R-11, R-12, R-22, R-113, R-114 and ethylene glycol. **Ammonia
   is not in it**, and ammonia is the S0 §9.1 reference coolant. Machine-visible via
   `fluid_in_gw86_database`; surfaced for director disposition, not resolved here.
3. **Both declared numeric domains are provisional.** The GW86 ranges could not be
   matched to any obtained source; the CHF range traces to a different paper. Declared
   provisional in `PROVISIONAL_DOMAINS` and still enforced as the guard.
4. **No sourced ONB criterion.** Bergles & Rohsenow (1964) is a graphical construction,
   and its usual algebraic surrogate is a dimensional water-only fit — out of fluid
   domain for ammonia. The regime gate therefore de-ranks anything not unambiguously in
   saturated flow boiling.
5. **Microgravity.** Every correlation reached is 1-g. Not microgravity-validated.
6. **Model-form.** GW86 has a reported mean deviation of ±21.4% against its own
   database; screening-level accuracy at best, and worse outside that database.

## What evidence would invalidate this result

- The original Gungor & Winterton (1986) paper showing a form that differs from the
  transcription (the primary paper was not obtained — this is the most direct falsifier).
- A microgravity flow-boiling dataset showing HTC or CHF behaviour that the 1-g
  correlation cannot bracket.
- Ammonia flow-boiling data showing GW86 deviating far beyond its ±21.4% band, which
  would confirm uncertainty 2 as disqualifying rather than merely recorded.
- A sourced CHF correlation giving dryout limits that reorder the `q''/CHF` bands for
  cases this build would currently rank.
- Evidence that the omitted horizontal Froude de-rating is *not* purely a
  stratification effect and has a microgravity analogue.

## Open questions / TODO

- **Director disposition needed:** which paper `two_phase.chf.shah_2015` denotes, or
  whether the entry should be re-pointed at Shah (1987) — which the registry currently
  classifies as a mere "historical ancestor" sensitivity, a classification this
  evidence also puts in question.
- **Director disposition needed:** ammonia vs the GW86 fluid database (uncertainty 2).
- Confirm the GW86 numeric domain against the primary paper, or re-derive it.
- Obtain a CHF correlation whose attribution can be established, then implement it and
  connect it to the (already tested) banding policy.
- Obtain an ONB criterion valid for ammonia, or record ONB as permanently not modelled.
- Director-authored explanation (status `explained` and above).
- Level **d** qualified external human review — `pending`.
