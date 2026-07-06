<!-- R1 reproduction record. External reference; not validation, not ranking. -->
> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# R1 — reproduction of the pinned Suncatcher v1.2 Part I thermal baseline

**Milestone:** R1 (Track R). **External reference; not validation, not ranking.** The pinned
standalone script was run **unchanged**, its self-check confirmed, and its outputs compared to the
author-provided baseline **in the author's own conventions** (no harmonization to
`orbital-thermal-bounds` — that is R3).

## Vendored script & provenance
The pinned script is vendored **byte-identical** at
`external_models/biswas_suncatcher/report_one_thermal.py` — **no provenance header is embedded in
the script**, so its SHA-256 stays identical to the pin
(`52b2f7af90e99e9aa2bb4c4de479c03ef742622c9a153d7867f1bfbeece02d8c`). The full pin (upstream repo,
release tag `v1.2`, commit `23053beeff53`, script SHA-256) and license (MIT + CC BY 4.0) are already
recorded in `provenance.md` (R0) and `UPSTREAM-LICENSE.md`; the machine-readable pin + reproduction
status is in `PINS.json`. There is **no separate `PROVENANCE.md`** — the existing `provenance.md`
already covers script provenance.

## Method
- **Target:** `report_one_thermal.py` at upstream commit `23053beeff53` (tag `v1.2`); 128 lines,
  dependency-free (stdlib `math` only).
- **Byte-identity:** the reproduced file's `sha256sum` equals the pinned
  `52b2f7af90e99e9aa2bb4c4de479c03ef742622c9a153d7867f1bfbeece02d8c`. The **director's Codespaces
  `git` + `sha256sum` check is the authoritative pin confirmation** (recorded in the R1 review record).
- **Run:** executed unchanged under Python 3.10; no edits (no-invention — nothing in the script was
  supplied or altered).
- **Self-check:** the script's built-in `assert` suite passed; it printed `checks ok`; exit code 0.

## Reproduced vs author-provided baseline (tolerance ±0.05 °C / ±0.001 K/W)

| Quantity | Author-provided | Reproduced (script output) | Δ | Pass |
|---|---|---|---|---|
| Radiator temperature `T_rad` | 21.3 °C | **21.34 °C** | 0.04 | ✅ |
| Junction temperature `T_j` | 111.3 °C | **111.3 °C** | 0.00 | ✅ |
| `T_j`, single heat-pipe failure | 114.8 °C | **114.8 °C** | 0.00 | ✅ |
| `R_th` before optimization | 0.350 K/W | **0.350 K/W** | 0.000 | ✅ |
| `R_th` after optimization | 0.300 K/W | **0.300 K/W** | 0.000 | ✅ |

All five within tolerance; the `T_rad` 0.04 °C difference is display rounding (author reported to
0.1 °C; the script computes 21.339 °C). **The author-provided Part I baseline is reproduced from the
pinned script.**

## Additional script outputs (recorded for completeness; NOT part of the author baseline)
- Heat load: 4×300 W compute + 150 W avionics + 100 W parasitic = **1450 W** (radiator 4.0 m²,
  ε = 0.85, 650 km dawn–dusk SSO, junction limit 125 °C).
- Passive wall `P_max = 125 / 0.300 = 417 W`; junction margin 13.7 °C (10.2 °C on one-heat-pipe
  failure).
- External loads (α_s = 0.15): view factor F = 0.290; solar 820 W; albedo 71 W; Earth-IR 234 W.
- Eclipse transient (t = 300 s): h_rad 4.92 W/m²K; τ 2468 s; ΔT_ss −5.08 K; T_rad(300 s) 20.76 °C.

## Captured stdout (verbatim)
```
Heat load
  4x300 W compute + 150 W avionics + 100 W parasitic = 1450 W

Radiator temperature
      iter 1: T =  21.489 C   (step 5.3608 K)
      iter 2: T =  21.339 C   (step 0.1499 K)
      iter 3: T =  21.339 C   (step 0.0001 K)
  T_rad = 21.34 C

Resistance chain [K/W]
  junction-to-case   0.150
  interface (TIM)    0.040
  cold-plate base    0.060
  heat pipe          0.080
  radiator           0.020
  total 0.350, optimized 0.300

Junction temperature
  T_j = 21.34 + 300*0.300 = 111.3 C, margin 13.7 C

One heat pipe out (8 -> 7)
  dR = +0.0114, T_j = 114.8 C, margin 10.2 C

Passive wall (interface rise alone hits the budget)
  P_max = 125 / 0.300 = 417 W  (no radiator size relaxes it)

External loads (alpha_s = 0.15)
  F = 0.290, solar 820 W, albedo 71 W, Earth-IR 234 W
  Earth-facing worst case ~305 W; edge-on baseline 100 W

Eclipse transient (t = 300 s)
  h_rad 4.92 W/m^2K, tau 2468 s, dT_ss -5.08 K, T_rad(300s) 20.76 C

======================================================================
checks ok
======================================================================
```

## Claim discipline & limitations
- **What this is:** a faithful reproduction of the pinned v1.2 standalone script's Part I thermal
  baseline, in the author's own conventions.
- **What this is NOT:** validation of the Biswas/Suncatcher physics; a comparison to or ranking
  against `orbital-thermal-bounds`; integration into `orbital_thermal`. Those are R2 (reference-case
  wrap) and R3 (harmonized comparison).
- The reproduced values are an **external reference**, kept **separate** from our Phase A / Stage-1
  oracle-freeze set. Level **d** (qualified external human review) remains `pending`.
