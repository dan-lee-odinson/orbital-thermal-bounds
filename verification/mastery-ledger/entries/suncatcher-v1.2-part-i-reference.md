> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Mastery ledger: Biswas/Suncatcher v1.2 Part I passive thermal baseline (EXTERNAL REFERENCE)

- **Entry id:** `suncatcher-v1.2-part-i-reference`
- **Current status:** `reproduced` (external reference) — reproduced from the pinned upstream
  standalone script; **not** an `orbital-thermal-bounds` claim
- **Category:** **external reference — unranked, unharmonized, not validated**
- **Last updated:** 2026-07-05
- **Reviewed at commit:** R2 apply commit on `track-r/r2-biswas-reference-case` (the squash-merge
  commit on `main` is the applied state)

> **EXTERNAL REFERENCE — READ FIRST.** This entry records a faithful *reproduction* of a pinned
> third-party model **in the source author's own conventions**. It is **NOT** validation of the
> Biswas/Suncatcher physics, **NOT** a comparison to or ranking against `orbital-thermal-bounds`,
> and **NOT** harmonized to this project's conventions. Any comparison is the harmonized,
> assumption-explicit Track-R **R3**. It lives in the separate *Track R* section of the ledger index
> so it can never be read as a project result.

## Reference question
Does the pinned Biswas/Suncatcher v1.2 standalone thermal script (`report_one_thermal.py`) reproduce
its stated Part I passive thermal baseline when run unchanged, and are those outputs pinned so drift
is caught?

## Why it matters (to Track R, not to our claims)
R2 establishes a stable, CI-enforced **external anchor** for a *future* harmonized comparison (R3)
against the `orbital-thermal-bounds` two-phase framework (S4–S6). It does **not** feed any
`orbital-thermal-bounds` sizing result or claim.

## Reproduced baseline (external reference; author's conventions)
Design point: a **1.45 kW total modeled thermal load** = **1.2 kW compute** (4 × 300 W TPUs) +
150 W avionics + 100 W parasitic; single-sided **4.0 m²** radiator; ε = 0.85 EOL; 650 km dawn–dusk
SSO; 125 °C junction limit. The **1.45 kW is the script's total modeled thermal load**; the
**1.2 kW is the compute input** — both are asserted in the test so the distinction is explicit and
the compute baseline is not silently changed.

| Quantity | Reproduced value (author convention) |
|---|---|
| Radiator temperature `T_rad` | 21.34 °C |
| Junction temperature `T_j` | 111.3 °C |
| `T_j`, one heat-pipe out | 114.8 °C |
| Resistance chain `R_th` before / after | 0.350 / 0.300 K/W |

Matches the author-provided baseline within ±0.05 °C / ±0.001 K/W (see
`external_models/biswas_suncatcher/R1-reproduction.md`).

## Supporting evidence (by category)
- **a. source / reference:** pinned upstream repo `Samarjithbiswas/space-based-ai-datacenter`,
  release `v1.2`, commit `23053beeff53`; script SHA-256 `52b2f7af…02d8c`; license MIT + CC BY 4.0.
- **b. independent derivation:** n/a — external model, not an `orbital-thermal-bounds` derivation.
- **c. executable reproduction:** `tests/test_biswas_suncatcher_reference.py` — byte-identity pin,
  script self-check (subprocess, timed), and reproduced-value assertions within tolerance. Present
  and passing.
- **d. qualified external human review:** `pending`.
- **cross-model review (recorded separately; not category d):** deferred to the Track-R **R3** major
  (harmonized comparison).

## Conventions and limitations
- **Author's own conventions, unharmonized:** single-sided 4.0 m² radiator, ε = 0.85 EOL — **not**
  mapped to `orbital-thermal-bounds` conventions (that is R3).
- **Single design point** (1.45 kW node), not a swept model.
- **Reduced-order passive / heat-pipe sizing** — distinct from the `orbital-thermal-bounds`
  two-phase pumped-loop S-track.
- **Reproduction ≠ validation** — reproducing the script's outputs does not validate its physics.
- The author cross-check is an optional **source-author review**, not independent external
  validation.

## What would invalidate this reproduction
- The vendored script's bytes drifting from the pin (SHA-256 mismatch) — caught by the test.
- The script's outputs drifting from the recorded baseline beyond tolerance (e.g., environment or
  Python change) — caught by the test.

## Explicit non-claims
Not validated · not ranked · not harmonized · not integrated into `orbital_thermal`.

## Open questions / TODO
- `pending`: Track-R **R3** harmonized, assumption-explicit comparison (requires S4–S6) + its
  mandatory cross-model review.
- `pending`: qualified external **human** review (d).
