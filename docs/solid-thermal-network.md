# Solid thermal network (Phase B, Stage 1 - milestone B2)

> **Status: design-intent implementation (B2), not a validated result.** This is the
> chip-side solid conduction path of the coupled model; it is verified against analytic
> limits and consumes the B1 registry, but it is not calibrated to hardware.

## What this is

`orbital_thermal.solid_network` computes the **junction-to-cold-plate** solid path of the
B0 plan's coupled model (Section 4.1a, residual R1): a series of solid resistances carrying
the **chip heat only** (`Q_chip`; pump heat enters the fluid downstream, per the B0
heat-injection rule). The junction temperature above the cold-plate base is

```
T_j = T_base + Q_chip * R_total,   R_total = R_conduction + R_spreading + R_contact
```

## Resistances

| Term | Model | Units |
|---|---|---|
| Conduction | `R = L / (k A)` (1-D) | K/W |
| Spreading | Yovanovich / Lee-Song-Au-Moran (1995) circular source on a coaxial disk | K/W |
| Contact | `R = 1 / (h_c A)` from a contact conductance `h_c` | K/W |

The **spreading** model uses an **isothermal base** by default (`base_htc=None`, i.e.
Biot -> infinity) and accepts a finite base heat-transfer coefficient for a convective base:

```
eps = a/b,  tau = t/b,  lam = pi + 1/(sqrt(pi) eps)
phi = (tanh(lam tau) + lam/Bi) / (1 + (lam/Bi) tanh(lam tau))    # phi = tanh(lam tau) if isothermal
psi = 0.5 (1 - eps)^{3/2} phi
R   = psi / (sqrt(pi) k a)
```

In the point-source, thick-plate, isothermal-base limit this returns `R ~ 0.282/(k a)`,
consistent with the isoflux half-space constriction value `8/(3 pi^2 k a) ~ 0.270/(k a)`
(a reduced-order fit; ~4%).

## Registry-governed rank-eligibility (B1)

Conductivity is pulled from `orbital_thermal.registry`. A **ranked** case (`build_ranked_path`):

- must use a **rank-eligible isotropic** material -- `solid.aluminum` (237 W/m/K) or
  `solid.copper` (401 W/m/K). A blocked material (APG / diamond, `source_required`) or an
  anisotropic material with no isotropic entry raises `NotRankEligibleError`;
- must supply a **cited** contact resistance (the registry marks contact resistance
  `source_required`); an uncited contact raises `NotRankEligibleError`;
- must include a **spreading** resistance unless 1-D conduction is explicitly justified
  (`one_d_justified`).

Parametric exploration (an anisotropic bound, an uncited contact) uses
`build_sensitivity_path`, which is **never** rank-eligible.

## Scope (B2)

- **Isotropic only.** Anisotropic / direction-aware conductivity (APG, diamond) is
  **deferred**; those materials are registry-blocked and cannot enter a ranked path here.
- **Chip side only.** The convective film and the fluid loop are B3; the radiator boundary
  is Phase A. B2 stops at the cold-plate base temperature `T_base`.

## Verification

Analytic conduction/contact exactness; spreading-model limits (isoflux half-space, source
filling the plate, monotonicity in source radius, convective >= isothermal, higher-`k`
lowers spreading); series assembly; and registry rank-eligibility enforcement. See
`tests/test_solid_network.py`.
