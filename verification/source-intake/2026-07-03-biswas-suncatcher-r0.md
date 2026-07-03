> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Source intake: Biswas / Suncatcher reference model (Track R, milestone R0)

- **Date:** 2026-07-03
- **Milestone:** R0 (source intake and provenance) - **pin only; no reproduction**
- **Scope boundary:** R1 reproduction not started; not integrated into `orbital_thermal`; not
  plotted or ranked; B0.5 notebook untouched.
- **Pinned artifacts:**
  [`external_models/biswas_suncatcher/`](https://github.com/dan-lee-odinson/orbital-thermal-bounds/tree/main/external_models/biswas_suncatcher)
  (`PINS.json`, `provenance.md`, `author_clarifications.md`, `UPSTREAM-LICENSE.md`).

## Source facts recorded

| Fact | Value |
|---|---|
| Repository | `Samarjithbiswas/space-based-ai-datacenter` |
| Release tag | `v1.2` |
| Full commit SHA | `23053beeff5375485af2834e4f77327e48b5475b` |
| Short SHA (author-provided) | `23053beeff53` -> confirmed prefix of the full SHA |
| Commit date / subject | 2026-06-30; "Reconcile satellite mass to the integrated model" |
| License | MIT (software) + CC BY 4.0 (report text / math / figures) |
| Standalone thermal script | `report-1/report_one_thermal.py` **present** at `v1.2` (128 lines, dependency-free); SHA-256 `52b2f7af...02d8c` |
| Author | Samarjith Biswas, PhD |
| Reference architecture | Google Project Suncatcher (arXiv:2511.19468) |

Verified by cloning the upstream repo at tag `v1.2` in an isolated sandbox (inspection only;
no code run, nothing reproduced).

## Author-provided baseline (recorded as clarification, NOT reproduced)

`T_rad = 21.3 C`; `T_j = 111.3 C`; `T_j` single-heat-pipe-failure `= 114.8 C`;
`R_th` before/after optimization `= 0.350 / 0.300 K/W`. Recorded in
`external_models/biswas_suncatcher/author_clarifications.md` with the `author-provided
clarification` label. **No `orbital-thermal-bounds` reproduction claim is made.**

## Source classification

`published repository` | `tagged release` | `author-provided clarification` |
`future reproduction target`.

## Acceptance criteria

- [x] `v1.2` source pinned by **full commit SHA** (`23053beeff5375485af2834e4f77327e48b5475b`).
- [x] License recorded (MIT + CC BY 4.0; `LICENSE` reproduced verbatim with SHA-256).
- [x] Standalone thermal-script path **confirmed** present at `v1.2` (with SHA-256).
- [x] No reproduction claims made.
- [x] No numerical Biswas result added as locally reproduced.
- [x] Changed files are records only (JSON/Markdown); no package/tests touched, so existing
      tests/CI are unaffected and the docs build is unchanged (these files live outside
      `docs/` and do not publish to the site).

## Unresolved items

- None blocking R0. The upstream `CITATION.cff` `version` field (`1.0.0`) does not match the
  release tag (`v1.2`) - recorded as an upstream metadata note; the pin uses the tag + full SHA.

## Status and next steps

- **Biswas / Suncatcher: pinned, unreproduced, unranked, future.**
- **R1** (run the standalone `report-1/report_one_thermal.py` unchanged and confirm its
  self-check) is the next Track-R step and is **not** started.
- **Does B2 (Phase B solid thermal network) proceed?** **Yes - independently.** B2 does not
  depend on the Biswas track; R0 introduces only reference records under `external_models/`
  and `verification/` and changes no `orbital_thermal` code, tests, or B0.5 assets.
