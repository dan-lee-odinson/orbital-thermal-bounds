# B8 completion report: review and release decision (v1.1.0)

> **Working verification record.** B8 is the **major** release-decision milestone (an explicit
> stop for human review). The review + release record is
> `verification/review-records/2026-07-04-b8-release-decision.md` (**OPEN** until the staged PR
> is director-reviewed and the reviewed commit SHA is recorded). No Phase A / `v1.0.1` result
> changed.

- **Milestone:** B8 (Phase B review and release decision)
- **Date:** 2026-07-04
- **Built on:** `main` after B7 (`a2cc1b0`)
- **Governing plan:** roadmap B8; plan Section 8 (B8).

## Release check (all pass; regression baseline `v1.0.1`)
- Full suite **548 passed, 3 xfailed, 0 failed**; Phase A / published suites + oracle-freeze
  pass (**no regression**); all four examples pass; `ruff` library/tests/scripts/examples clean
  (the only findings are pre-existing report-only items in a Phase A notebook).

## Decision (director)
- **External qualified-human review: recorded as currently unobtainable** (cross-model review is
  not a substitute; project-director review only). Level d remains `pending` for all entries.
- **Release: Proceed to v1.1.0 with narrowed claims and explicit limitations.** Contingent on
  the staged PR passing all checks + director review; **no merge/tag until the review record
  carries the reviewed commit SHA + final disposition.**

## What changed for the release
- `pyproject.toml`: version `1.0.1 -> 1.1.0`.
- `CHANGELOG.md`: `[1.1.0]` entry (allowed claim + the required limitation wording; no disallowed
  claim).
- `README.md`, `docs/chip-to-radiator-model.md`: the exact required limitation wording added.
- `verification/mastery-ledger/index.md`: a level-d-pending / release note.
- `verification/review-records/2026-07-04-b8-release-decision.md`: the B8 review + release record.

## After director review (release steps, recorded for reproducibility)
1. Record the reviewed commit SHA + final disposition in the B8 review record; flip to CLOSED.
2. Squash-merge the B8 PR to `main`.
3. Tag `v1.1.0` on the merge commit (triggers the publish workflow).

## Limitations and readiness
- Phase B ships as a **reduced-order research/comparison framework**, verification-supported
  (a/b/c + cross-model), **not** externally validated (level d pending). All narrowed-claim and
  limitation wording is recorded in the review record and the public docs.
