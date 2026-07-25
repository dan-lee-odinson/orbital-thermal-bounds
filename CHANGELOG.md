# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project uses
[semantic versioning](https://semver.org/).

Scope note: entries describe the **software package** (`orbital_thermal`) and the
repository. The three preprints have their own Zenodo DOIs (see the README).

## [Unreleased] — Stage 2

Work in progress on Stage-2 build branches. **Not released, not tagged**, and not part
of any published version. No Phase A or Stage-1 published number is changed.

### Added — S2, two-phase acquisition / evaporator (screening level)
- Two-phase saturation backend in `fluids`: `saturation_temperature`,
  `saturation_enthalpies`, `surface_tension`, `saturation_properties`, guarded against
  both the declared registry domain and the real triple/critical bounds. Coolants with
  no registry entry are source-gated.
- `orbital_thermal.two_phase`: vapour quality / loop state, the ONB-saturated-regime
  rank policy, the CHF/dryout bands (`q''/CHF ≤ 0.5` rank-eligible; `0.5–1` sensitivity,
  not ranked; `≥ 1` rejected), and the local-wall-flux basis discipline.
- Executable Gungor & Winterton (1986) flow-boiling HTC wired into
  `two_phase.htc.gungor_winterton` — the **only** correlation carrying an `evaluate`.
  Vertical / non-stratified form; the horizontal Froude/stratification de-rating is
  deliberately not applied (1-g effect, recorded modelling decision).
- `scripts/witness_s2_checks.py`: 16 deliberate mutations proving every S2 check can
  actually fail.
- `docs/two-phase-evaporator.md`, the S2 review record, and the mastery-ledger entry for
  S0 §4 claim 1 (status `derived`).

### Not implemented (recorded as blockers, not guessed)
- `two_phase.onb.bergles_rohsenow` — the 1964 criterion has no closed form (three
  independent sources: a four-equation system solved graphically), and its usual
  algebraic surrogate is a dimensional water-only fit, out of fluid domain for the
  ammonia reference coolant. The ONB **policy gate** ships regardless.

### Changed
- The S1 `test_no_evaluate_callable_in_s1` guard is replaced by a strictly stronger
  successor pinning the **exact** set of implemented ids, plus a new invariant requiring
  every implemented correlation to carry a non-empty `source.locator` (and its converse).

### Added — OTB-G001 fix cycle (Sol review FAIL: 8 blockers, 2 major; all dispositioned)
- **One applicability enforcement mechanism** (`registry/applicability.py`) making a
  correlation's declared applicability binding on fluid, geometry, orientation, regime
  and provenance. Five of the ten findings were the same defect — a declared constraint
  recorded but never enforced — and are closed by this one mechanism rather than five
  patches. A declared axis with **no stated value** is itself a violation, which is what
  closes DEBTS **D-9** (geometry enforced, not merely titled).
- **`two_phase.chf.shah_1987` promoted to the CHF reference** with an executable form
  (Director ruling D3), the `pr_reduced` 0.0014–0.96 band re-attributed to it from
  `shah_2015`, and its 23-fluid / 0.315–37.5 mm database recorded. `shah_2015` moves to
  `SOURCE_REQUIRED` with **no domain at all** and can no longer pass the eligibility
  guard. **Shah (1987) is gravity-explicit** — its correlating parameter divides by `g`,
  so it has no microgravity limit; carried as an enforced applicability axis.
- **`SaturationState`**: an immutable value binding fluid, pressure and backend version
  to its properties, validated against the loop state before evaluation. The untagged
  dict path was removed, not deprecated.
- **`ChfResult`** and a typed, **evaluated** `OnbCriterion` — a bare CHF float and a
  merely-present ONB object are both refused.
- **Enforced backend pin**: a CoolProp version differing from `COOLPROP_PIN` now fails
  saturation evaluation, with a migration path requiring a review-record reference.
- Liquid-Reynolds turbulence guard; seven-fluid database enforced; ammonia **de-ranked**
  through Gungor & Winterton (ruling D4). The `check_domain` bypass was removed from the
  public HTC wrapper.
- The GW86 numeric limits are relabelled **provenance-unestablished** (ruling D1) with
  three confirming locators added; the maths is unchanged.
- Witness harness extended to **32 mutations**, and it now refuses to run when the
  installed package is not the tree being mutated.

## [1.1.0] — 2026-07-04

Phase B (Stage 1): a **verification-supported, reduced-order, single-phase
chip-to-radiator** modeling and trade-study framework, with documented
assumptions, executable tests, cross-model review records, and explicit
limitations. Backward-compatible feature addition — **no Phase A result and no
published `v1.0.1` result changed** (the Phase A verification suites and every
published number are unchanged; the full test suite is 548 passed / 3 xfailed).

### Added
- Property/correlation registry with provenance and rank-eligibility gates (B1).
- Solid conduction network: conduction + Yovanovich spreading + contact (B2).
- Single-phase pumped loop: hydraulics, film coefficient, pump energy, per-segment
  phase margins (B3).
- Coupled steady-state chip-to-radiator solve (per-node residuals R1–R5), Modes T/A —
  temperatures/area are solved outputs (B4; adversarial cross-model review CLOSED).
- Stage-1 architecture-case classification + modeled component mass (B5).
- Trade-study engine: grid sweep → six Pareto fronts, plot-ready data (B6; adversarial
  cross-model review CLOSED).
- Public docs (`docs/chip-to-radiator-model.md`, guides), six Pareto figures, and an
  end-to-end example (B7).

### Verification and limitations
- Evidence levels a (source) + b (analytic) + c (executable), plus adversarial
  cross-model review at the major milestones (B4, B6).
- **No qualified external human engineering review has yet validated the central
  transport/pressure claims.** Cross-model review is **not** qualified external human
  review.
- The Phase B Stage-1 model remains a **reduced-order research and comparison
  framework**. It is **not flight-grade, not hardware-validated, and not suitable for
  certification or safety-critical design**.
- Mass figures are **modeled component mass (incomplete Stage-1 accounting)** — not
  total thermal-system mass. No single case is Pareto-optimal on every named front
  (not a global architecture ranking). No published-architecture (AI1 / Starcloud /
  Suncatcher) judgment is claimed.
- **External qualified review remains a future target** before stronger engineering
  claims are made.


## [1.0.1] — 2026-06-16

Maintenance release. No functional, numerical, or API changes; every published
number and all 259 tests are identical to 1.0.0.

### Changed
- Resolved all Ruff lint findings in the library, tests, and verification
  scripts (import ordering, explicit `zip(..., strict=False)`, `warnings.warn`
  `stacklevel`, one wrapped long line, one unused test variable). Behavior is
  unchanged; the cleanup is style-only.
- Enriched package metadata: added the Zenodo software-archive DOI and the full
  set of project URLs (documentation, changelog, issues, all three preprints),
  plus PyPI keywords and trove classifiers.
- First release published to PyPI (`pip install orbital-thermal`) via GitHub
  Actions Trusted Publishing.

[1.0.1]: https://github.com/dan-lee-odinson/orbital-thermal-bounds/releases/tag/v1.0.1

## [1.0.0] — 2026-06-14

First stable, audit-closed release of the `orbital_thermal` reduced-order radiator
package, alongside the third preprint.

### Added
- `orbital_thermal` Python package: gray-body radiation, equilibrium/capacity
  inverses, the analytic thermodynamic bounds (Theorems 1–5), orbital geometry
  and the **exact** tilted-plate-to-sphere Earth view factor, an orbit-varying
  effective-sink model, and a one-node RK4 transient solver.
- Orbit-coupled transient convergence certificate: periodic closure, a scale-aware
  energy-balance criterion, and a temporal-resolution check (independently
  converged N / 2N / 4N grids, a grid-free analytic forcing-quadrature certificate,
  pointwise waveform comparison, and a conservative safety factor).
- Faithful replication of Andrew McCalip's public "Space Datacenters" model and the
  exact-view-factor correction module (`mccalip_exact_vf`).
- Optional CoolProp-backed ammonia coolant screen (`fluids`, the `[fluids]` extra),
  pinned to CoolProp 7.2.0.
- Paper-three preprint and `verify_paper3.py` (pinned to `orbital-thermal==1.0.0`).
- GitHub Wiki (installation, running the simulation, API reference, reproducing,
  troubleshooting).

### Verified
- 259 passing tests, 3 intentional `xfail`s (the not-yet-implemented disk-integrated
  albedo model, pinned to `NotImplementedError`).
- Independent Python (`verify_suite.py`, `verify_paper3.py`, `companion/verify_ai1.py`)
  and Wolfram Language (`verify_suite.wl`) checks.
- SHA-256-pinned, Node-regenerated, externally attested McCalip oracle; the
  oracle-freeze CI job fails closed.
- CI on Python 3.10, 3.11, 3.12; PEP 639 MIT-only wheel check.
- Headline result reproduced: McCalip default 335.749538 K → exact-VF 342.099222 K
  (+6.349684 K), decomposed as +5.766313 K model-form geometry and +0.583371 K
  floating-point branch artifact.

### Known limitations
- Reduced-order **one-node** thermal model; no spatial gradients, conduction, fin
  efficiency, or loop design.
- The reflected-solar term uses a **subpoint-albedo approximation**; the
  disk-integrated albedo model is not yet implemented.
- The transient temporal residual is a refinement-based **estimate**, not a
  guaranteed continuum bound (a conservative safety factor is applied).
- **No validation against flown hardware**; no public flight data exists for this
  configuration. The project supports mathematical, software, and cross-model
  verification only.

### Development history
- `v0.8.0`–`v0.8.6` were the iterative audit-remediation pre-releases: eight rounds
  of adversarial software review with independent computer-algebra verification,
  each shipped as its own tag (see the repository tags). `v1.0.0` is the
  audit-closed state of that process plus the paper-three documentation.

[1.0.0]: https://github.com/dan-lee-odinson/orbital-thermal-bounds/releases/tag/v1.0.0
