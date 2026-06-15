# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project uses
[semantic versioning](https://semver.org/).

Scope note: entries describe the **software package** (`orbital_thermal`) and the
repository. The three preprints have their own Zenodo DOIs (see the README).

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
