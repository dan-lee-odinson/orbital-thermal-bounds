<!-- Index of mastery-ledger entries. Update the status column as entries advance. -->

> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Mastery ledger - index

Statuses are *demonstrated* levels (see [`../README.md`](../README.md)):
`identified` -> `explained` -> `derived` -> `reproduced` -> `stress-tested` ->
`externally-reviewed`. A low status with higher items marked `TODO` is normal and honest.

## Retrospective baseline (results Phase B directly inherits)

Category-**d** qualified external *human* review is `pending` for every entry below; the
"cross-model review" column records GPT audit coverage, which is **not** category d (see
[`../README.md`](../README.md)).

| Entry | Result | Status | Director explanation | Independent derivation (b) | Cross-model review (not d) |
|---|---|---|---|---|---|
| [radiative-equilibrium-and-net-rejection](entries/radiative-equilibrium-and-net-rejection.md) | Gray-body equilibrium temperature and net rejection (area law) | `reproduced` | TODO (director) | TODO | partial (audit) |
| [emitting-face-convention](entries/emitting-face-convention.md) | Two-sided emitting area; valid only with equal sinks on both faces | `reproduced` | TODO (director) | n/a (convention) | B0 re-review (equal-sink) |
| [earth-view-factors](entries/earth-view-factors.md) | Exact tilted-plate-to-sphere Earth view factor (~0.258 vs ~0.021 heuristic floor) | `reproduced` | TODO (director) | TODO | audit + B0 re-review (comparator fix) |
| [spectral-separation-of-loads](entries/spectral-separation-of-loads.md) | Separation of solar / albedo / Earth-IR absorbed flux | `reproduced` | TODO (director) | TODO | Starcloud review |
| [beta-angle-albedo-model](entries/beta-angle-albedo-model.md) | Sub-point albedo factor and its documented beta=90 limitation | `reproduced` | TODO (director) | TODO | GPT (beta=90) |
| [radiator-attitude-and-sun-shielding](entries/radiator-attitude-and-sun-shielding.md) | Direct-solar omission; sun-shielded-face contract | `reproduced` | TODO (director) | n/a (contract) | B0 re-review (F3/F9) |
| ai1-starcloud-comparison-assumptions | As-published and harmonized comparison assumptions | `identified` | TODO (director) | TODO | GPT (Phase A) |
| three-quarter-temperature-result | Conditional 3/4 cold-fraction optimum (only if Phase B uses it) | `identified` | TODO (director) | TODO | partial (audit) |

> The **core boundary set** (first six entries) is opened and populated by B0 -- the Phase A
> radiator-boundary results the Phase B plan directly reuses. The `radiator-attitude-and-sun-
> shielding` entry and the equal-sink condition on `emitting-face-convention` were added in the
> B0 revision (review F3/F9), and the `earth-view-factors` comparator was corrected then. The
> remaining two entries are `identified` placeholders, opened later:
> `ai1-starcloud-comparison-assumptions` at B5/B6, and `three-quarter-temperature-result` only
> if Phase B uses the cold-fraction optimum. Status `reproduced` reflects executable evidence
> only; director-authored explanation and independent derivation remain `TODO` and must not be
> inferred or fabricated.

## Phase B entries

Added per Phase B milestone as new central claims are introduced
(see [`../../docs/development/phase-b-roadmap.md`](../../docs/development/phase-b-roadmap.md)).

Category-**d** qualified external *human* review is `pending` for every entry below; the
"cross-model review" column records optional GPT spot-check coverage, which is **not**
category d. A mandatory cross-model review is required at the major milestones (B4/B6/B8);
intermediate milestones (B1/B2/B3) carry a completion report with an optional spot-check.

| Entry | Result | Status | Director explanation | Independent derivation (b) | Cross-model review (not d) |
|---|---|---|---|---|---|
| [solid-thermal-network](entries/solid-thermal-network.md) | Junction-to-cold-plate solid resistance network (conduction + Yovanovich spreading + contact) | `reproduced` | TODO (director) | TODO | not yet run |
| [single-phase-pumped-loop](entries/single-phase-pumped-loop.md) | Single-phase loop hydraulics, film coefficient, pump energy, per-segment phase margins | `reproduced` | TODO (director) | TODO | not yet run |
| [coupled-steady-state-solution](entries/coupled-steady-state-solution.md) | Coupled R1-R5 chip-to-radiator steady state (Modes T/A); temperatures/area are solved outputs | `reproduced` | TODO (director) | TODO | **approved (F1-F8 + N1 closed)** |
| [architecture-cases](entries/architecture-cases.md) | Stage-1 common-envelope coolant x solid-path case matrix; gate-driven classification + ranked references + modeled component mass | `reproduced` | TODO (director) | TODO | optional spot-check (intermediate) |
| [trade-study](entries/trade-study.md) | Stage-1 trade-study engine: grid sweep over the rank-eligible cases + six Pareto fronts (engine verified c; physics inherits B1-B5) | `reproduced` | TODO (director) | TODO | **approved (F1-F8 + N1/N2 closed)** |

