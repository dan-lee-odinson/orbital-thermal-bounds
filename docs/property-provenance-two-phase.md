# Two-phase property / correlation registry — provenance (Phase B Stage 2, S1)

> **Status: registry only (milestone S1).** Every row below is registered with a cited source, a
> resolution status, a validity range, a pinned backend version, and (for HTC/Δp/CHF) machine-visible
> microgravity fields. **No correlation math is implemented in S1** — the executable forms land at the
> milestone that first uses each (S2: HTC / ONB / CHF; S3: Δp + condenser/pump-inlet; S4: coupled
> use). No-invention: an unsourced or out-of-regime input is a machine-visible blocker
> (`SOURCE_REQUIRED` / `SENSITIVITY`), never a guess. Machine-readable source of truth:
> `src/orbital_thermal/registry/two_phase.py`.

## Backend pin (reproducibility)

Saturation properties are evaluated by **CoolProp HEOS, pinned to `7.2.0`** (matches Stage-1 B1).
`8.0.0` is known but **not adopted**: advancing the pin requires a **property-drift check** —
re-verify `T_sat, h_fg, ρ_v, σ` against the pinned reference first (8.0.0 adds mass-basis vapor
quality `Qmass` and a new tabular backend). Recorded as `COOLPROP_PIN`.

- **Ammonia (R717) EOS:** Gao, Wu, Bell & Lemmon (2020), via CoolProp HEOS.
- **Water EOS:** IAPWS-95 (Wagner & Pruß, 2002), via CoolProp HEOS.

## Correlation registry

| id | source | status | rank-eligible | validity range (S1 metadata) |
|---|---|---|---|---|
| `two_phase.htc.gungor_winterton` | Gungor & Winterton (1986), *Int. J. Heat Mass Transfer* | RESOLVED | **yes (reference)** | G 10–600 kg/m²s; q″ 2–240 kW/m²; x 0.002–0.997; P 0.19–1.6 MPa; D 1.2–32 mm |
| `two_phase.htc.chen` | Chen (1966), *IEC Proc. Des. Dev.* | SENSITIVITY | no | — |
| `two_phase.htc.shah_2022` | Shah (2022), updated saturated-boiling HTC | SENSITIVITY | no | — |
| `two_phase.onb.bergles_rohsenow` | Bergles & Rohsenow (1964), *J. Heat Transfer* | SOURCE_REQUIRED | no | applicability/range guards required; ammonia/regime applicability source-gated |
| `two_phase.dp.lockhart_martinelli_chisholm` | Lockhart & Martinelli (1949) + Chisholm (1967) | RESOLVED | **yes (reference)** | low/moderate P (0.1–2.0 MPa); pinned Chisholm C rule |
| `two_phase.dp.friedel` | Friedel (1979) | SENSITIVITY | no | — |
| `two_phase.dp.muller_steinhagen_heck` | Müller-Steinhagen & Heck (1986) | SENSITIVITY | no | — |
| `two_phase.chf.shah_2015` | Shah (2015), general saturated-flow-boiling CHF | RESOLVED | **yes (reference)** | reduced pressure ~0.0014–0.96; **local** wall-flux basis; feeds q″/CHF ≤ 0.5 |
| `two_phase.chf.shah_1987` | Shah (1987), *Int. J. Heat Fluid Flow* | SENSITIVITY | no | — |
| `two_phase.chf.katto_ohno` | Katto & Ohno (1984), *Int. J. Heat Mass Transfer* | SENSITIVITY | no | — |
| `two_phase.pump.npsh` | Hydraulic Institute / NPSH practice | SOURCE_REQUIRED | no | pump-class NPSH_req source-gated; else idealized pump-inlet boundary |

## Saturation property backends

| id | kind | backend / version | source | domain (triple → critical) |
|---|---|---|---|---|
| `coolant.ammonia.saturation_backend` | BACKEND_EVALUATION | CoolProp HEOS 7.2.0 | Gao et al. (2020) | T 195.5–405.4 K |
| `coolant.water.saturation_backend` | BACKEND_EVALUATION | CoolProp HEOS 7.2.0 | IAPWS-95 (2002) | T 273.16–647.1 K |

Both are rank-eligible per-state evaluators; the actual `T_sat, h_fg, ρ_v, σ` calls happen in S2/S3
via `orbital_thermal.fluids`.

## Pinned two-phase pressure-drop regime rule (F7)

`CHISHOLM_C`, keyed by `(liquid_regime, gas_regime)`: turbulent–turbulent = **20**, laminar–turbulent
= **12**, turbulent–laminar = **10**, laminar–laminar = **5**. Per-phase laminar/turbulent split:
`Re < 1000` laminar, `Re > 2000` turbulent (`CHISHOLM_RE_LAMINAR_MAX` / `CHISHOLM_RE_TURBULENT_MIN`).
Data only in S1; the multiplier itself is evaluated at S3.

## Microgravity fields (F7 / S0 §9.2)

Every HTC / Δp / CHF row carries: `microgravity_validated = False`, `gravity_basis = "1g"`,
`rank_scope = "reference_correlation_only"`, and a `limitation` string ("ISS/microgravity literature
shows gravity-dependent HTC/CHF behavior; rankings are not microgravity-validated"). So a caller
cannot silently treat a 1-g-correlation ranking as microgravity-valid.

## Open items (recorded, not blocking S1)

- **Citation locators (DOI / volume / pages) are intentionally left blank** and to be confirmed at
  review — no identifiers were fabricated (no-invention). Author + year + journal are given.
- **`shah_2015` reduced-pressure domain** (~0.0014–0.96) is a provisional metadata band recorded so
  the rank-eligible reference declares a validity range; confirm/adjust against the source at review.
- **ONB (`bergles_rohsenow`) and NPSH** are `SOURCE_REQUIRED` (not rank-eligible) pending
  ammonia/regime and pump-class sourcing — as intended (S0 §9.5 / §3).
