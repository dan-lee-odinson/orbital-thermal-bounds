# Two-phase acquisition / evaporator (Stage 2, S2)

!!! warning "Screening-level, unreleased, and not microgravity-validated"
    This page documents **work in progress on a Stage-2 build branch.** It is a
    reduced-order, screening-level model of a single acquisition operating point:
    there is **no coupled solve, no pressure drop, and no condenser**. Every
    correlation reached from here is a **1-g reference correlation**; nothing here is
    microgravity-validated and no such claim is made. Released project results are
    Stage 1 (`v1.1.0`) and are unaffected by this page.

## What this module does

`orbital_thermal.two_phase` evaluates one evaporator operating point and **classifies**
it. It answers: given a loop state, a channel, and a wall heat flux, what is the
flow-boiling heat-transfer coefficient, and may this case be **ranked**, reported only as
a **sensitivity**, **rejected**, or is it **blocked** for want of a sourced input?

It does not size a loop, solve a radiator boundary, or compare architectures.

## Loop state and vapour quality

The loop state generalises from subcooled `(T, P)` to specific enthalpy and pressure:

```
x = (h - h_f(P)) / h_fg(P),    0 <= x <= 1
```

Saturation properties come from **CoolProp HEOS pinned at 7.2.0**
(`registry.two_phase.COOLPROP_PIN`). Pressure is bounded by
`P_triple < P < P_crit` — outside that band there is no saturation state and the call
raises. There is **no blanket supercritical treatment**.

Quality is **enforced, not clamped**. A clamped quality would silently turn a subcooled
or superheated state into a saturated one, so `loop_state` classifies into
`SUBCOOLED_LIQUID`, `SATURATED_TWO_PHASE` or `SUPERHEATED_VAPOUR` and keeps the raw
equilibrium quality alongside the physical one.

Only **ammonia** (reference) and **water** (secondary) have registered saturation
domains. Any other coolant raises `SourceGatedFluidError` rather than being evaluated.

## Flow-boiling heat-transfer coefficient

The one implemented correlation is **Gungor & Winterton (1986)**, in its vertical /
non-stratified form:

```
alpha_tp = E alpha_L + S alpha_nb
E        = 1 + 24000 Bo^1.16 + 1.37 (1/X_tt)^0.86
S        = [1 + 1.15e-6 E^2 Re_L^1.17]^-1
```

with `alpha_L` the liquid-fraction Dittus-Boelter coefficient and `alpha_nb` the
Cooper (1984) nucleate pool-boiling term. Symbols and units are defined in the
[mastery-ledger entry](https://github.com/dan-lee-odinson/orbital-thermal-bounds/blob/main/verification/mastery-ledger/entries/two-phase-flow-boiling-heat-acquisition.md).

**Every call is range-checked** against the entry's declared validity domain. An
out-of-range call raises; it is **never silently extrapolated**.

### Two limitations that travel with every result

- **The horizontal-channel Froude/stratification de-rating is deliberately not applied.**
  It models gravitational phase stratification — a 1-g effect with no microgravity
  meaning. This is a **recorded modelling decision**, not an omission.
- **The reference coolant is outside the correlation's fluid database.** Gungor &
  Winterton (1986) was developed on water, R-11, R-12, R-22, R-113, R-114 and ethylene
  glycol. **Ammonia is not among them.** This is reported machine-visibly by
  `fluid_in_gw86_database` and on every assessment, and is recorded as an open item for
  director disposition.

The declared numeric domain of this entry **could not be confirmed** against an obtained
source and is **declared provisional** (`PROVISIONAL_DOMAINS`). It is still enforced as
the guard.

## Regime / ONB policy

Rank-eligible cases are restricted to a defined **saturated flow-boiling** regime.

**No sourced onset-of-nucleate-boiling criterion is implemented.** Bergles & Rohsenow
(1964) is a graphical construction in the original, and its usual algebraic surrogate is
a dimensional **water-only** fit — out of fluid domain for ammonia. So the gate applies
the conservative fallback: a case that is **not unambiguously in saturated flow boiling**
cannot be shown to sit above ONB and is **sensitivity-only, never rank-eligible**. The
unknown de-ranks the case rather than admitting it.

A superheated / post-dryout state is **rejected**: the implemented coefficient is a
wetted-wall correlation and is not valid once the wall dries out.

## CHF / dryout bands

Banded on the **local modeled wall heat flux**:

| Band | Outcome |
|---|---|
| `q''/CHF <= 0.5` | **rank-eligible** |
| `0.5 < q''/CHF < 1` | **parametric / sensitivity** — reported, **not ranked** |
| `q''/CHF >= 1` | **dryout — rejected** |

This is a **modelling margin, not flight certification.**

!!! danger "No CHF correlation is implemented in this build"
    The banding *policy* above ships and is fully tested, but the correlation behind it
    does not exist here. The registry's reference CHF entry could not be implemented
    because its source attribution could not be established: the "Shah (2015)" citation
    is ambiguous (two distinct 2015 Shah CHF papers, for different geometries), and its
    declared reduced-pressure domain traces to **Shah (1987)** instead. Rather than
    attach maths whose attribution is unknown, the entry is left unimplemented and
    `critical_heat_flux()` **raises**. A case that needs a computed CHF is **blocked** —
    never silently ranked, and never given a plausible number.

## Local-flux discipline

`q''` must be the **local modeled** wall heat flux derived from **sourced** channel
geometry. Because channel geometry is source-required, a flux carries its own basis
(`LOCAL_SOURCED`, `SECTION_AVERAGE`, `CHIP_AVERAGE`) and that basis travels with the
number to every gate that consumes it.

A section- or chip-average is permitted **only when explicitly named and categorised**,
and can never produce a rank-eligible result however small the CHF ratio. A local flux
built on **unsourced** geometry is likewise not rankable. An average is **never silently
substituted** for a local flux.

## Combining the gates

`assess_acquisition` runs every gate and takes the **worst** outcome, so a permissive
gate can never outvote a strict one. Outcomes are `RANK_ELIGIBLE`, `SENSITIVITY_ONLY`,
`REJECTED`, or `BLOCKED`, and each carries the reasons that produced it.

With no CHF value supplied and no sourced CHF correlation available, a case is
**`BLOCKED`** — not assumed to be below CHF.

## Scope limits

Not modelled here, and not claimed: two-phase pressure drop, the condenser, pump-inlet
NPSH/cavitation feasibility, the coupled steady-state solution, flow instabilities
(Ledinegg, density-wave, pressure-drop oscillation), architecture cases, and any trade
study or Pareto content. Stage 2 addresses **mechanically pumped flow-boiling loops
only** and does not retire the two-phase prerequisite in general.

## Reproducing

```bash
pip install -e ".[dev]"
pytest tests/test_two_phase_evaporator.py tests/test_two_phase_registry.py -q
python scripts/witness_s2_checks.py
```
