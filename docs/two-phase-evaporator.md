# Two-phase acquisition / evaporator (Stage 2, S2)

!!! warning "Screening-level, unreleased, and not microgravity-validated"
    This page documents **work in progress on a Stage-2 build branch.** It is a
    reduced-order, screening-level model of a single acquisition operating point:
    there is **no coupled solve, no pressure drop, and no condenser**. Every
    correlation reached from here is a **1-g reference correlation**, and one of them
    has no microgravity limit at all. Nothing here is microgravity-validated and no
    such claim is made. Released project results are Stage 1 (`v1.1.0`) and are
    unaffected by this page.

## What this module does

`orbital_thermal.two_phase` evaluates one evaporator operating point and **classifies**
it: given a loop state, a channel, and a wall heat flux, what is the flow-boiling
heat-transfer coefficient, and may this case be **ranked**, reported only as a
**sensitivity**, **rejected**, or is it **blocked** for want of a sourced input?

It does not size a loop, solve a radiator boundary, or compare architectures.

## Declared applicability is enforced, not annotated

Every correlation here declares what it is applicable to — fluid, geometry,
orientation, flow regime, provenance — and those declarations are **binding**, through
a single mechanism in `orbital_thermal.registry.applicability`.

Two rules give it teeth:

- **Silence is not consent.** An axis a correlation *declares* but which the case does
  not *state* is a violation in its own right. An unstated geometry is not a licence to
  assume a tube.
- **Violations change the verdict.** They are typed values with a consequence
  (de-rank, reject, block), and the worst one wins. Recording an applicability failure
  without acting on it is not enforcement.

A case therefore carries a status **and** the reasons for it, and cannot rank on a
correlation outside its documented basis.

## Loop state and vapour quality

```
x = (h - h_f(P)) / h_fg(P),    0 <= x <= 1
```

Saturation properties come from **CoolProp HEOS pinned at 7.2.0**, and the pin is
**enforced at every evaluation** — a different installed version fails rather than
quietly producing values presented as pinned. Pressure is bounded by
`P_triple < P < P_crit`; there is **no blanket supercritical treatment**.

Quality is **enforced, not clamped**: `loop_state` classifies into `SUBCOOLED_LIQUID`,
`SATURATED_TWO_PHASE` or `SUPERHEATED_VAPOUR` and keeps the raw equilibrium quality, so
a subcooled or superheated state stays distinguishable.

Properties travel as a **`SaturationState`** carrying their own fluid, pressure and
backend version, validated against the loop state before evaluation — so the domain
that was guarded is provably the domain that was evaluated.

Only **ammonia** (reference) and **water** (secondary) have registered saturation
domains; any other coolant is source-gated.

## Flow-boiling heat-transfer coefficient

**Gungor & Winterton (1986)**, vertical / non-stratified form:

```
alpha_tp = E alpha_L + S alpha_nb
E        = 1 + 24000 Bo^1.16 + 1.37 (1/X_tt)^0.86
S        = [1 + 1.15e-6 E^2 Re_L^1.17]^-1
```

with `alpha_L` the liquid-fraction Dittus-Boelter coefficient and `alpha_nb` the Cooper
(1984) nucleate term. The executable form is confirmed by **three independent
printings** (Thome *Engineering Data Book III* §10.3.3; *CFD Letters* 10(2) 2018 Eq. 3;
Collier & Thome 3rd ed. §7.4.3 Eq. 7.36), which agree with each other and with the code.

**Every call is range-checked. There is no bypass** on the guarded wrapper; explicitly
labelled non-ranking analysis uses the low-level pure evaluator instead.

### What is enforced, and what is only labelled

| Axis | Status |
|---|---|
| Fluid | **Enforced**: water, R-11, R-12, R-22, R-113, R-114, ethylene glycol — the database agreed by five independent sources |
| Geometry | **Enforced**: round tube or annulus |
| Orientation | **Enforced**: vertical up/down flow only (see below) |
| Flow regime | **Enforced**: liquid Reynolds number above the turbulent threshold its Dittus-Boelter base requires |
| Numeric limits | **Enforced as guards, but labelled provenance-unestablished** |

The five numeric limits appear in **none of the twenty-one consulted sources**,
including Collier & Thome §7.4.3 — the canonical text by the same author as the
handbook the code came from, which describes the database by point count, fluid list
and flow orientation and prints no numeric range. They are retained and enforced, but
they are **not the authors' declared range** and are never presented as such.

The horizontal-channel Froude/stratification de-rating is deliberately **not
implemented**: it models gravitational phase stratification, which has no microgravity
meaning. That is why horizontal orientation is outside what is implemented.

!!! danger "The reference coolant is outside the reference correlation"
    **Ammonia is not in the Gungor & Winterton database**, and ammonia is the project's
    reference coolant. Zürcher, Thome & Favrat (1999) measured GW86 at **47.6 %**
    standard deviation against ammonia data, rising past **84 %** above `x = 0.85`.
    Ammonia is therefore **de-ranked** through this correlation — the exclusion alters
    the case status, it is not a footnote. A fluid-corrected alternative is scoped for
    evaluation at S5.

## CHF / dryout bands

The CHF reference is **Shah (1987)**, *Int. J. Heat and Fluid Flow* 8(4):326–335, for
CHF during upflow in uniformly heated vertical tubes. It replaced an entry cited as
"Shah (2015)", which resolved to no single paper — two distinct 2015 Shah CHF papers
exist, for different geometries — and whose declared reduced-pressure band turned out
to be Shah (1987)'s all along.

Banding on the **local modeled wall heat flux**:

| Band | Outcome |
|---|---|
| `q''/CHF <= 0.5` | **rank-eligible** |
| `0.5 < q''/CHF < 1` | **parametric / sensitivity** — reported, **not ranked** |
| `q''/CHF >= 1` | **dryout — rejected** |

A **modelling margin, not flight certification.**

A CHF value is not a number: it is a **`ChfResult`** binding the value to its
correlation, citation, locator, fluid, geometry, evaluated domain and gravity basis. A
bare float is rejected by type, and a result carrying applicability violations cannot
produce a rank-eligible band however small the ratio.

!!! danger "Shah (1987) is gravity-explicit and has no microgravity limit"
    Its correlating parameter contains `g`:

    ```
    Y = (G D cp_f / k_f) * (G^2 / (rho_f^2 g D))^0.4 * (mu_f / mu_g)^0.6
    ```

    As `g -> 0` the Froude group diverges, taking `Y` and the correlation's branch
    selection with it. This is stronger than the standing "1-g derived" caveat — there
    is no zero-gravity limit to take. Evaluating it at `g <= 0` is refused, and
    gravity is a declared applicability axis rather than a remark.

    Ammonia is absent from Shah (1987)'s 23-fluid database too, so the same exclusion
    applies here.

## Onset of nucleate boiling

**No sourced ONB criterion is implemented.** Three independent sources confirm the
published Bergles & Rohsenow criterion has no closed form — it is a four-equation
system solved graphically in the original — and the usual algebraic surrogate is
water-only and needs a contact angle not in hand for ammonia.

The policy gate ships regardless: a state that is not unambiguously in saturated flow
boiling **cannot be shown to sit above ONB** and is sensitivity-only. A criterion is
honoured only if it is a typed `OnbCriterion`, is declared valid for the case's fluid,
and is actually **evaluated** — presence of an object is not evidence.

The `x = 0` boundary is reported for what it is: the **bulk-equilibrium saturation
crossing**, not an established onset-of-nucleate-boiling transition. Subcooled boiling
can occur while equilibrium quality is negative.

## Local-flux discipline

`q''` must be the **local modeled** wall heat flux from **sourced** channel geometry.
A flux carries its own basis (`LOCAL_SOURCED`, `SECTION_AVERAGE`, `CHIP_AVERAGE`), and
that basis travels with the number to every gate that consumes it.

An average is permitted **only when explicitly named and categorised**, and can never
produce a rank-eligible result. A local flux built on unsourced geometry is likewise
not rankable. An average is **never silently substituted** for a local flux.

## Scope limits

Not modelled, and not claimed: two-phase pressure drop, the condenser, pump-inlet
NPSH/cavitation feasibility, the coupled steady-state solution, flow instabilities,
architecture cases, and any trade study or Pareto content. Stage 2 addresses
**mechanically pumped flow-boiling loops only** and does not retire the two-phase
prerequisite in general.

## Reproducing

```bash
pip install -e ".[dev]"
pytest tests/test_two_phase_evaporator.py tests/test_two_phase_registry.py tests/test_applicability_enforcement.py -q
python scripts/witness_s2_checks.py
```
