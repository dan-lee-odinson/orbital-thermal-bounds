# Phase B property, source, and correlation registry (B1)

> **Generated from `orbital_thermal.registry`** by `scripts/generate_property_registry.py`.
> Do not edit by hand; edit the registry and regenerate. This is a design-intent /
> data-provenance record, not a validation of any physical result.

Every load-bearing Phase B property and correlation is registered with an explicit
**provenance class** and a **resolution status**. The registry enforces one invariant:
a non-rank-eligible entry **cannot silently enter a ranked Phase B case**
(`registry.assert_rank_eligible`). Unresolved items are recorded with a machine-visible
blocker status and no value -- they are never invented (no-invention policy; B0 plan
Sections 2, 4.2, 4.5, 4.6).

**Summary:** 39 entries, 19 rank-eligible, 20 blocked (future=2, resolved=27, sensitivity=1, source_required=9).

Resolved coolant transport values are **derived** from CoolProp 7.2.0 at the saturated-liquid
300 K reference state and re-checked in `tests/test_registry.py`.

## Provenance classes
`published` | `derived` | `assumed` | `corrected` | `design_variable` | `sensitivity` | `unsupported`

## Blocker statuses (keep an entry out of ranked cases)
`resolved` (rankable) | `sensitivity` | `future` | `source_required` | `backend_required` |
`unsupported` | `not_rank_eligible`

## Properties (coolants, solids, containment)

| ID | Name | Kind | Provenance | Status | Value (SI) | Units | Source | Rank-eligible |
|---|---|---|---|---|---|---|---|---|
| `coolant.ammonia.density` | Ammonia density | reference_anchor | derived | resolved | 600.17 | kg/m^3 | NIST Chemistry WebBook, SRD 69 (via CoolProp HEOS, Gao et al. JPCRD 2020) | **no** |
| `coolant.ammonia.specific_heat` | Ammonia specific heat | reference_anchor | derived | resolved | 4796.38 | J/kg/K | NIST Chemistry WebBook, SRD 69 (via CoolProp HEOS, Gao et al. JPCRD 2020) | **no** |
| `coolant.ammonia.thermal_conductivity` | Ammonia thermal conductivity | reference_anchor | derived | resolved | 0.48064 | W/m/K | NIST Chemistry WebBook, SRD 69 (via CoolProp HEOS, Gao et al. JPCRD 2020) | **no** |
| `coolant.ammonia.viscosity` | Ammonia dynamic viscosity | reference_anchor | derived | resolved | 0.000129489 | Pa*s | NIST Chemistry WebBook, SRD 69 (via CoolProp HEOS, Gao et al. JPCRD 2020) | **no** |
| `coolant.ammonia.critical_temperature` | Ammonia critical temperature | operational | published | resolved | 405.4 | K | NIST Chemistry WebBook, SRD 69 (via CoolProp HEOS, Gao et al. JPCRD 2020) | yes |
| `coolant.ammonia.property_backend` | Ammonia per-state property evaluation | backend_evaluation | derived | resolved | - | SI | NIST Chemistry WebBook, SRD 69 (via CoolProp HEOS, Gao et al. JPCRD 2020) | yes |
| `coolant.water.density` | Water density | reference_anchor | derived | resolved | 996.513 | kg/m^3 | NIST Chemistry WebBook, SRD 69 (via CoolProp HEOS, Gao et al. JPCRD 2020) | **no** |
| `coolant.water.specific_heat` | Water specific heat | reference_anchor | derived | resolved | 4180.91 | J/kg/K | NIST Chemistry WebBook, SRD 69 (via CoolProp HEOS, Gao et al. JPCRD 2020) | **no** |
| `coolant.water.thermal_conductivity` | Water thermal conductivity | reference_anchor | derived | resolved | 0.60944 | W/m/K | NIST Chemistry WebBook, SRD 69 (via CoolProp HEOS, Gao et al. JPCRD 2020) | **no** |
| `coolant.water.viscosity` | Water dynamic viscosity | reference_anchor | derived | resolved | 0.000853751 | Pa*s | NIST Chemistry WebBook, SRD 69 (via CoolProp HEOS, Gao et al. JPCRD 2020) | **no** |
| `coolant.water.property_backend` | Water per-state property evaluation | backend_evaluation | derived | resolved | - | SI | NIST Chemistry WebBook, SRD 69 (via CoolProp HEOS, Gao et al. JPCRD 2020) | yes |
| `coolant.pgw.concentration` | PGW mass-fraction concentration | operational | assumed | source_required | - | - |  | **no** |
| `coolant.pgw.transport_properties` | PGW transport properties | operational | assumed | source_required | - | SI |  | **no** |
| `coolant.co2.critical_temperature` | CO2 critical temperature | operational | published | resolved | 304.128 | K | NIST Chemistry WebBook, SRD 69 (via CoolProp HEOS, Gao et al. JPCRD 2020) | yes |
| `coolant.co2.critical_pressure` | CO2 critical pressure | operational | published | resolved | 7.3773e+06 | Pa | NIST Chemistry WebBook, SRD 69 (via CoolProp HEOS, Gao et al. JPCRD 2020) | yes |
| `coolant.co2.loop_use` | CO2 as a Stage-1 loop coolant | operational | sensitivity | sensitivity | - | SI |  | **no** |
| `solid.aluminum.thermal_conductivity` | Aluminum (pure) thermal conductivity | operational | published | resolved | 237 | W/m/K | Incropera & DeWitt, Fundamentals of Heat and Mass Transfer, Table A.1 (300 K) | yes |
| `solid.copper.thermal_conductivity` | Copper thermal conductivity | operational | published | resolved | 401 | W/m/K | Incropera & DeWitt, Fundamentals of Heat and Mass Transfer, Table A.1 (300 K) | yes |
| `solid.apg.in_plane_conductivity` | APG in-plane thermal conductivity | operational | sensitivity | source_required | - | W/m/K |  | **no** |
| `solid.apg.through_plane_conductivity` | APG through-plane thermal conductivity | operational | sensitivity | source_required | - | W/m/K |  | **no** |
| `solid.diamond_composite.thermal_conductivity` | Diamond-composite thermal conductivity | operational | sensitivity | source_required | - | W/m/K |  | **no** |
| `containment.al6061t6.density` | Al 6061-T6 density | operational | published | resolved | 2700 | kg/m^3 | ASM / MMPDS handbook room-temperature properties | yes |
| `containment.al6061t6.yield_strength` | Al 6061-T6 yield strength | operational | published | resolved | 2.76e+08 | Pa | ASM / MMPDS handbook room-temperature properties | yes |
| `containment.al6061t6.allowable_stress` | Al 6061-T6 allowable stress | operational | assumed | source_required | - | Pa |  | **no** |
| `containment.ti6al4v.density` | Ti-6Al-4V density | operational | published | resolved | 4430 | kg/m^3 | ASM / MMPDS handbook room-temperature properties | yes |
| `containment.ti6al4v.allowable_stress` | Ti-6Al-4V allowable stress | operational | assumed | source_required | - | Pa |  | **no** |
| `containment.safety_factor_convention` | Containment safety-factor convention | operational | assumed | source_required | - | - |  | **no** |

## Correlations (thermal, hydraulic)

| ID | Name | Provenance | Status | Value (SI) | Units | Source | Rank-eligible |
|---|---|---|---|---|---|---|---|
| `friction.laminar` | Laminar Darcy friction factor | published | resolved | - |  | White, Fluid Mechanics (friction-factor correlations) | yes |
| `friction.blasius` | Blasius turbulent friction factor | published | resolved | - |  | White, Fluid Mechanics (friction-factor correlations) | yes |
| `friction.haaland` | Haaland friction factor (Colebrook approx.) | published | resolved | - |  | White, Fluid Mechanics (friction-factor correlations) | yes |
| `nusselt.laminar_const_q` | Laminar Nusselt, constant heat flux | published | resolved | - |  | Incropera & DeWitt, Fundamentals of Heat and Mass Transfer (7th ed.) | yes |
| `nusselt.laminar_const_Ts` | Laminar Nusselt, constant wall temperature | published | resolved | - |  | Incropera & DeWitt, Fundamentals of Heat and Mass Transfer (7th ed.) | yes |
| `nusselt.dittus_boelter` | Dittus-Boelter turbulent Nusselt | published | resolved | - |  | Incropera & DeWitt, Fundamentals of Heat and Mass Transfer (7th ed.) | yes |
| `nusselt.gnielinski` | Gnielinski turbulent Nusselt | published | resolved | - |  | Incropera & DeWitt, Fundamentals of Heat and Mass Transfer (7th ed.) | yes |
| `nusselt.developing_entry_length` | Developing (entry-length) Nusselt correction | assumed | future | - |  | Incropera & DeWitt, Fundamentals of Heat and Mass Transfer (7th ed.) | **no** |
| `thermal.spreading_resistance` | Spreading (constriction) resistance model | published | resolved | - |  | Lee, Song, Au, Moran; Yovanovich constriction/spreading-resistance model | yes |
| `thermal.contact_resistance` | Thermal contact resistance | sensitivity | source_required | - |  |  | **no** |
| `hydraulic.minor_losses` | Minor-loss K-factor method | published | resolved | - |  | Crane Technical Paper TP-410 (minor-loss K-factors) | yes |
| `hydraulic.maldistribution_allowance` | Parallel-channel maldistribution allowance | assumed | future | - |  |  | **no** |
