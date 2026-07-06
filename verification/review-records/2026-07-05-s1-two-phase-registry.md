<!-- Stage-2 review record (S1, two-phase registry). Intermediate milestone. CLOSED on director
review + green CI. No cross-model review at S1 (deferred to the S4/S6 majors). -->
> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Review Record: S1 — two-phase property/correlation registry

## Record Metadata
- **Record status:** **CLOSED** on director review + green CI (intermediate milestone).
- **Date:** 2026-07-05
- **Reviewed commit:** S1 apply commit on `feat/s1-two-phase-registry` (squash-merge on `main` is
  the applied state).
- **Reviewer(s):** **project director (Dan Lee-Odinson).** No cross-model review at S1 (intermediate;
  deferred to the S4/S6 majors). Cross-model, if run, is category **c**, never level **d**.
- **Trigger:** Stage-2 milestone S1 (registry; r1 source-cleanup applied).
- **Disposition:** **Registry built and verified; proceed to S2.**

## Scope (registry only — no physics)
- Registered the two-phase property/correlation set with cited sources, validity ranges, pinned
  backend version, rank-eligibility status, and machine-visible microgravity fields.
- **No correlation math is implemented.** Every `evaluate` is `None`; formulas land at S2 (HTC/ONB/
  CHF), S3 (Δp + condenser/pump-inlet), S4 (coupled). Reuses the B1 guard framework
  (`assert_rank_eligible`, `assert_in_domain`).
- **No `orbital_thermal` published number changed**; regression baseline `v1.1.0`.

## What S1 added
- `src/orbital_thermal/registry/two_phase.py` — 11 correlation entries + 2 saturation-backend
  property entries; `COOLPROP_PIN` (7.2.0 → 8.0.0 migration gate); `CHISHOLM_C` regime rule;
  `_MICROGRAVITY_1G` fields; `missing_metadata()` structural checker.
- `src/orbital_thermal/registry/provenance.py` — **four optional, backward-compatible** microgravity
  fields on `CorrelationEntry` (`microgravity_validated`, `gravity_basis`, `rank_scope`,
  `limitation`); guard logic unchanged; all existing B1 entries unaffected.
- `src/orbital_thermal/registry/__init__.py` — aggregates the two-phase entries into `ALL_ENTRIES` /
  `_BY_ID` / `__all__`.
- `tests/test_two_phase_registry.py` — 28 tests (metadata / flags / guards only; **not** physical
  correctness).
- `docs/property-provenance-two-phase.md` — the human-readable registry provenance.

## Director source decisions applied (r1)
Ammonia EOS Gao et al. (2020) [not Tillner-Roth 1993]; CoolProp 7.2.0 reproducibility pin + 8.0.0
drift-check gate; Gungor–Winterton (1986) reference HTC + Chen (1966)/Shah (2022) sensitivities;
Shah (2015) reference CHF + Shah (1987)/Katto–Ohno (1984) sensitivities; Bergles–Rohsenow (1964) ONB
applicability-guarded (SOURCE_REQUIRED); Lockhart–Martinelli/Chisholm + Friedel + Müller-Steinhagen–
Heck with the **pinned Chisholm C rule**; the four machine-visible microgravity fields.

## Verification
- **Tests:** 28 passed (sandbox, reconstructed package; stdlib-only, no CoolProp/numpy needed). Adds
  to the suite: **548 → 576**.
- **Lint:** `ruff` (repo config, line-length 100) clean on the new `src/` files and test.
- **Rank-eligibility (verified):** only the three references are rank-eligible
  (`gungor_winterton`, `lockhart_martinelli_chisholm`, `shah_2015`); all sensitivities + ONB + NPSH
  are correctly blocked. Registry summary after S1: 52 total entries, 24 rank-eligible.
- **Guards (verified):** `assert_in_domain` raises out-of-range; `assert_rank_eligible` raises on a
  sensitivity; `missing_metadata` is empty for the registry and non-empty for a deliberately-broken
  entry.

## Claim discipline / no-invention
- Registry only; no physics, no ranking, no comparison to the Track-R Suncatcher reference (R3).
- Every row is sourced or a machine-visible blocker; no constants invented. 1-g correlations carry
  the explicit microgravity limitation; rankings are reference-only, not microgravity-validated.

## Open items (recorded, not blocking)
- Citation **locators (DOI/volume/pages) left blank**, to confirm at review (no fabricated
  identifiers).
- `shah_2015` reduced-pressure domain (~0.0014–0.96) is a **provisional** metadata band so the
  rank-eligible reference declares a validity range; confirm/adjust against the source.
- ONB + NPSH remain `SOURCE_REQUIRED` pending ammonia/regime and pump-class sourcing.

## Disposition
**CLOSED. Two-phase registry built, sourced, and verified (28 tests + ruff clean); no physics, no
ranking.** Next: **S2** (two-phase acquisition/evaporator — flow-boiling HTC / ONB / CHF formulas +
dryout bands), which will implement and test the executable forms this registry names.
