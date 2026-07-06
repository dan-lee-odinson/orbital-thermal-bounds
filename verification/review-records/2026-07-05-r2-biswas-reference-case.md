<!-- Track-R review record (R2). CLOSED: external reference case wrapped and CI-enforced; remains
unranked / unharmonized / unvalidated. Next Track-R step R3 is gated on S4-S6. -->
> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Review Record: R2 — wrap R1 reproduction as a tested external reference case

## Record Metadata
- **Record status:** **CLOSED** — external reference case wrapped; test green; proceed (R3 gated on
  S4–S6).
- **Date:** 2026-07-05
- **Reviewed commit:** R2 apply commit on `track-r/r2-biswas-reference-case` (the squash-merge commit
  on `main` is the applied state).
- **Reviewer(s):** **project director (Dan Lee-Odinson).** Intermediate milestone — **no cross-model
  review at R2** (deferred to the R3 major). Cross-model, if run, is category **c**, never level **d**.
- **Trigger:** Track-R milestone R2 (reference-case wrap).
- **Disposition:** **Reference case complete; external reference remains unranked / unharmonized /
  unvalidated; proceed.**

## Scope
- Wrapped the R1 reproduction as a **CI-enforced external reference case**: a pytest + a mastery-
  ledger entry (in the separate Track-R section) + limitations + explicit `PINS.json` status fields.
- **No `orbital_thermal` source or published number changed;** regression baseline `v1.1.0`. **No
  comparison to `orbital-thermal-bounds`.**

## What R2 added
- `tests/test_biswas_suncatcher_reference.py` — three tests: **SHA-256 byte pin**; **script
  self-check** (subprocess, `timeout=30`); **reproduced-value asserts** within ±0.05 °C / ±0.001 K/W.
  Verified locally (**3 passed**) and by CI.
- `verification/mastery-ledger/entries/suncatcher-v1.2-part-i-reference.md` — external-reference entry
  (status `reproduced`; evidence a + c; **d `pending`**; cross-model deferred to R3).
- `verification/mastery-ledger/index.md` — new **Track R — external reference reproductions** section,
  separate from the project's own claim tables.
- `external_models/biswas_suncatcher/PINS.json` — explicit machine-readable status: `reference_case`
  true; `reproduced` true; `ranked` false; `harmonized` false; `validated` false; `source_conventions`
  recorded.

## Claim discipline
- External reference, reproduced, **unranked, unharmonized, unvalidated.** The test pins the
  reference values; it **never** compares to `orbital-thermal-bounds`.
- The **1.45 kW total modeled thermal load** is labeled as the Biswas-script convention (1.2 kW
  compute + 150 W avionics + 100 W parasitic); the 1.2 kW compute input is asserted separately, so
  the baseline input is not silently changed.

## Verification / CI
- Test count **548 → 551** (3 new); **no new dependencies**; the new test lives in `tests/`, is
  stdlib-only, and is ruff-clean; `external_models/` stays lint/test-excluded; docs/coverage
  unaffected. Checks: `tests / quality / docs` green.

## Disposition
**CLOSED. External reference case wrapped and CI-enforced; remains unranked / unharmonized /
unvalidated.** The next Track-R step, **R3** (harmonized, assumption-explicit comparison), stays
gated on S4–S6 and carries the mandatory cross-model review.
