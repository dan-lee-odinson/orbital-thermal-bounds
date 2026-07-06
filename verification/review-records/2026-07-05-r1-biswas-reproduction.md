<!-- Track-R review record (R1). CLOSED: byte-identity confirmed by the director; reproduction
faithful within tolerance; R2 may begin. -->
> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Review Record: R1 — reproduce pinned Suncatcher v1.2 Part I thermal baseline

## Record Metadata
- **Record status:** **CLOSED** — reproduction faithful within tolerance; byte-identity confirmed;
  proceed to R2.
- **Date:** 2026-07-05
- **Reviewed commit:** R1 apply commit on branch `track-r/r1-biswas-reproduction` (the squash-merge
  commit on `main` is the applied state).
- **Reviewer(s):** **project director (Dan Lee-Odinson).** No cross-model review at R1 (not a major;
  deferred to the R3 major). Cross-model, if run, is category **c**, never level **d**.
- **Trigger:** Track-R milestone R1 (external-reference reproduction).
- **Disposition:** **Reproduction faithful within tolerance; proceed to R2.**

## Scope
- **External-reference reproduction only.** Ran the pinned standalone script unchanged; confirmed its
  self-check; compared outputs to the author-provided baseline in the author's own conventions.
- **No `orbital_thermal` code/tests touched** — changes live under `external_models/` and
  `verification/` only; regression baseline `v1.1.0` intact. `external_models/` is ruff-excluded and
  `pytest testpaths = tests`, so CI is unaffected.

## Result summary (see `external_models/biswas_suncatcher/R1-reproduction.md`)
- Script self-check passed (`checks ok`, exit 0).
- Reproduced within tolerance (±0.05 °C / ±0.001 K/W): `T_rad` 21.34 °C, `T_j` 111.3 °C, `T_j`
  (1 heat-pipe failure) 114.8 °C, `R_th` 0.350 → 0.300 K/W. The author-provided Part I baseline is
  reproduced from the pinned script.

## Byte-identity — director's authoritative check
```
# throwaway clone of the pinned upstream (public MIT); not added to the repo
cd /tmp && rm -rf scv && git clone https://github.com/Samarjithbiswas/space-based-ai-datacenter scv
cd scv && git checkout 23053beeff5375485af2834e4f77327e48b5475b
sha256sum report-1/report_one_thermal.py
cp report-1/report_one_thermal.py /workspaces/orbital-thermal-bounds/external_models/biswas_suncatcher/report_one_thermal.py
sha256sum /workspaces/orbital-thermal-bounds/external_models/biswas_suncatcher/report_one_thermal.py
```
- **Result: CONFIRMED.** Both the upstream file and the vendored copy hash to
  `52b2f7af90e99e9aa2bb4c4de479c03ef742622c9a153d7867f1bfbeece02d8c` — byte-identity holds.

## Claim discipline
- Faithful reproduction of the pinned script's Part I baseline; **not** validation, **not** ranking,
  **not** integration. External reference kept **separate** from the oracle-freeze set.
- Values remain in the author's own conventions (no harmonization; that is R3).

## Verification level
- **c** (executable reproduction) + **a** (pinned published source). **Level d `pending`.**
  Cross-model review deferred to the R3 major.

## Milestone numbering
- Governed by the merged Stage-2 roadmap: **R1** (reproduce) → **R2** (reference-case wrap: tests +
  ledger + limitations) → **R3** (harmonized comparison, major). The older `biswas-r0` numbering
  (R1/R2/R4/R5/R7) is retained as **historical notes only**; the author cross-check is an **optional
  source-author review**, not independent external validation.

## Findings / director review
1. **Byte-identity confirmed** via Codespaces `git` + `sha256sum`; both the upstream file and the
   vendored copy match the pinned `52b2f7af…02d8c`.
2. **Reproduction faithful:** the pinned script ran unchanged, its self-check passed, and all five
   baseline quantities reproduced within the ±0.05 °C / ±0.001 K/W tolerance.
3. **Claim discipline verified:** external reference only; unranked; author's own conventions;
   separate from the oracle-freeze set.
4. **No regression:** no `orbital_thermal` code/tests touched; `external_models/` is lint/test
   excluded; baseline `v1.1.0` intact.

## Disposition
**CLOSED. R1 reproduction faithful within tolerance and byte-identical to the pin; proceed to R2.**
Standing: the reproduced values stay an external reference (unranked); any comparison to
`orbital-thermal-bounds` is deferred to the harmonized, assumption-explicit R3.
