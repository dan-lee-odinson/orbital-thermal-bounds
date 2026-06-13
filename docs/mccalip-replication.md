# Replicating the McCalip orbital thermal/cost model

## Purpose

Andrew McCalip's "Space Datacenters" model (github.com/andrewmccalip/thoughts,
MIT) is the most visible public first-principles model of orbital-datacenter
thermal and cost economics. Before the third paper builds on or argues against
that body of work, we establish exactly what his model says by reproducing it
independently. This document records that exercise and -- more importantly --
draws the line between three claims that are easy to conflate.

## Replication vs. verification vs. validation

**Replication** -- *does our independent implementation reproduce his?*
`src/orbital_thermal/mccalip_replication.py` is a from-scratch Python port of his
`static/js/math.js`, using his exact constants, including the truncated
sigma = 5.67e-8 and the rounded deep-space temperature T_space = 3 K. Run over
the same parameter grid, it matches the frozen Node oracle
(`external_models/mccalip_thoughts/expected_outputs.json`) to a maximum relative
error of ~4e-14 across all 297 compared values in 11 cases -- floating-point
roundoff. **The model is faithfully replicated.** This says nothing about whether
the model is right; it says only that we understand it precisely enough to
recompute it in another language.

**Verification** -- *is the physics internally correct?* This is the job of the
core package (`orbital_thermal.radiation`, `.equilibrium`, `.bounds`,
`.environment`) and its published-results suite, which use the exact CODATA
sigma = 5.670374419e-8 and the exact tilted-plate-to-sphere view factor rather
than McCalip's approximations. Where the two diverge, the gap is bounded and
explained, not reconciled away:

| Element | McCalip model | Core package | Consequence |
|---|---|---|---|
| Stefan-Boltzmann sigma | 5.67e-8 (truncated) | 5.670374419e-8 (exact) | ~0.002 K at 340 K |
| Deep-space sink | 3 K (rounded) | 2.7255 K (CMB) | negligible above 300 K |
| Tilted view factor | cos-tilt heuristic + 5% edge-on floor | exact integral (machine precision) | >0.10 in VF near the horizon |
| Orbit-averaged VF | 72-point Riemann sum | exact / analytic | small, but uncontrolled |

The view-factor heuristic is the substantive modelling difference, and at the
default geometry it is not a small one. At beta = 90 deg the sun-tracking panel is
EDGE-ON to Earth: its normal tracks the Sun, which at beta = 90 deg is normal to
the orbit plane, while nadir lies in the plane 90 deg away. Around the orbit
McCalip's per-face floor averages ~0.021 there; the exact tilted-plate-to-sphere
view factor is ~0.258 -- a ~12x underestimate
(`test_floor_underestimates_exact_by_about_12x`). This is not a region where his
heuristic is reasonable; it is the region where it is worst, and it is his
default. The core package therefore carries its own exact geometry rather than
inheriting his -- and, as the next subsection quantifies, that correction moves his
headline temperature.

## The edge-on correction (headline result)

Substituting the exact per-face view factor into McCalip's own heat balance --
changing nothing else, not his truncated sigma, rounded deep-space temperature, or
constants -- raises his default equilibrium temperature

    335.75 K  (McCalip, replicated)  ->  342.10 K  (exact edge-on VF)   +6.35 K

The replication in `mccalip_replication.py` stays faithful; this is a quantified
new result, not a defect papered over. It is implemented in
`orbital_thermal.mccalip_exact_vf` and locked by
`tests/test_mccalip_exact_vf.py::TestEdgeOnDefault::test_exact_vf_raises_default_eqtemp_by_about_6_3K`.
The self-consistency test in that file confirms that feeding McCalip's own view
factors back through the same heat balance reproduces his number exactly, so the
+6.35 K is attributable to geometry alone. The correction across the full range of
beta angles is tabulated in the next section.

## Correction across beta

McCalip's default is beta = 90 deg -- the worst case -- but the correction is
present at every beta, because the sun-tracking panel's faces are never near
nadir. Recomputing his own heat balance with the exact per-face view factor
(`mccalip_exact_vf.correction_table_vs_beta`) across the oracle's beta grid gives:

| beta (deg) | McCalip eqTemp (K) | exact-VF eqTemp (K) | correction (K) |
|---:|---:|---:|---:|
| 0  | 349.58 | 351.53 | +1.94 |
| 15 | 348.94 | 350.98 | +2.04 |
| 30 | 347.12 | 349.53 | +2.41 |
| 45 | 344.42 | 347.63 | +3.22 |
| 60 | 341.28 | 345.66 | +4.38 |
| 75 | 338.24 | 343.79 | +5.55 |
| 90 | 335.75 | 342.10 | +6.35 |

The correction is positive and grows monotonically toward the edge-on default,
since his cos-tilt floor underestimates the exact view factor more severely as the
panel tilts away from nadir. The figure
`results/figures/mccalip_beta_correction.png`
(`scripts/plot_mccalip_correction.py`) plots this; it is the section paper three
leads with.

**Validation** -- *does the model match reality?* Neither the replication nor the
core package claims this. Validation would require flight or test data for an
orbital datacenter radiator, which does not exist publicly. The third paper's
contribution is to frame that open question precisely (orientation-dependent
effective sink, transient peak excess) rather than to assert a validated answer.

## What was replicated

The port covers `calculateOrbital`, `calculateThermal`, `calculateBreakeven`, and
the view-factor functions (`earthAngularRadius`, `nadirViewFactor`,
`sunTrackingPanelViewFactors`). The oracle grid is: defaults; beta in
{0, 30, 60, 90} deg; altitude in {400, 550, 800} km; radiator emissivity in
{0.85, 0.90, 0.95}. The replicated default equilibrium temperature is 335.75 K
(342.10 K once the edge-on view factor is corrected; see "The edge-on
correction" above).

## Reproducing this result

Regenerate the oracle from the pinned JavaScript (requires Node), then check the
Python port against it:

    cd external_models/mccalip_thoughts
    node generate_oracle.js > expected_outputs.json
    cd ../..
    pytest tests/test_mccalip_replication.py -v

The oracle is frozen under the oracle-freeze rule: it is never hand-edited to make
a test pass. If McCalip updates his model, regenerate the whole file at a new
pinned commit and update `provenance.md`.
