# Biswas / Suncatcher reference model - provenance record (R0)

**R0 is a source-intake pin only.** No reproduction, harmonization, ranking, or integration
into `orbital_thermal` has been performed. The Biswas/Suncatcher model is recorded here as
**pinned, unreproduced, unranked, and future** (a Stage-2 / reference-comparison target per
the integrated program roadmap, Track R).

## Repository

- **URL**: https://github.com/Samarjithbiswas/space-based-ai-datacenter
- **Title**: "Space-Based Data Center Infrastructure: A Multi-Physics Approach"
  (CITATION.cff)
- **Description**: a sourced, reproducible systems-engineering study of AI data centers in
  low Earth orbit, with open Python subsystem models, a mathematical guide, a monograph, and
  a 3D visualization. Reference architecture: **Google Project Suncatcher** (arXiv:2511.19468).
- **Author**: Samarjith Biswas, PhD
- **License**: **MIT** for software; **CC BY 4.0** for report text, the mathematical guide,
  and figures (see `UPSTREAM-LICENSE.md`, reproduced verbatim from the pinned commit).

## Pinned version

| Field | Value |
|---|---|
| Release tag | `v1.2` |
| Release page | https://github.com/Samarjithbiswas/space-based-ai-datacenter/releases/tag/v1.2 |
| Commit SHA (full) | `23053beeff5375485af2834e4f77327e48b5475b` |
| Commit SHA (author-provided short) | `23053beeff53` (confirmed to be a prefix of the full SHA) |
| Commit date | 2026-06-30T18:11:04-05:00 |
| Commit subject | "Reconcile satellite mass to the integrated model (220 kg dry / 233 kg launch)" |
| Date accessed | 2026-07-03 |

The short SHA supplied by the author resolves unambiguously to the full 40-character SHA above
(the `v1.2` tag points to this commit; verified by cloning at the tag).

## Standalone thermal script (confirmed present)

| Field | Value |
|---|---|
| Path | `report-1/report_one_thermal.py` |
| Exists at `v1.2` | **yes** (128 lines) |
| Dependencies | standard library only (dependency-free) |
| SHA-256 | `52b2f7af90e99e9aa2bb4c4de479c03ef742622c9a153d7867f1bfbeece02d8c` |

The SHA-256 is recorded to pin the exact bytes so R1 can confirm byte-identity before any
future reproduction. **The script was not executed and no output was reproduced in R0.**

## Source classification

| Class | What it covers |
|---|---|
| `published repository` | the public GitHub repository and its code |
| `tagged release` | release `v1.2` at the pinned commit |
| `author-provided clarification` | the thermal-baseline values and context Dr. Biswas provided (see `author_clarifications.md`), recorded as author-provided, **not** independently reproduced |
| `future reproduction target` | R1 (standalone script) and R2 (package-level) reproduction, deferred |

## Status (R0)

- **pinned**: yes (full SHA + release tag + script SHA-256)
- **reproduced**: no
- **ranked**: no
- **integrated into `orbital_thermal`**: no
- **phase**: future (Track R; Stage-2 heat-pipe benchmark and reference comparisons)

## Upstream metadata note

The upstream `CITATION.cff` `version` field reads `1.0.0`, while the GitHub release is tagged
`v1.2`. This is an upstream metadata mismatch, recorded for transparency; the pin here uses the
**release tag and full commit SHA**, which are unambiguous.

## Convention differences (to account for at reproduction time, not now)

Deferred to R1/R2. The Biswas model uses its own environment constants and conventions (e.g.,
single-sided `4.0 m^2` radiator, `eps = 0.85` EOL, 650 km dawn-dusk SSO, junction limit
`125 C`); the harmonization to `orbital-thermal-bounds` conventions is Track R work (R4/R5) and
is **not** performed in R0.
