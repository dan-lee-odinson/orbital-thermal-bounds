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

The view-factor heuristic is the substantive modelling difference: at a radiator
tilted 90 deg from nadir, McCalip's floor gives ~0.04 while the exact view factor
is ~0.26 (`test_tilted_vf_approximation_departs_from_exact`). This does not make
his headline number wrong -- his bifacial panel is near nadir/anti-nadir where the
heuristic is reasonable -- but it is why the core package carries its own exact
geometry rather than inheriting his.

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
{0.85, 0.90, 0.95}. The replicated default equilibrium temperature is 335.75 K.

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
