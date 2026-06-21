# Working verification records

This directory holds the project's **working verification artifacts**: the
technical-mastery ledger and the milestone/review records. It is the lightweight,
risk-proportional backbone described in
[`docs/VERIFICATION_AND_VALIDATION.md`](../docs/VERIFICATION_AND_VALIDATION.md).

## What this is, and is not

- These records are **public through the repository** (the repo is public); they are
  version-controlled like any other tracked file.
- They are **not part of the published documentation site**. The MkDocs build only
  includes `docs/`; this directory is intentionally excluded from the site navigation,
  and its pending content is not copied into the public docs.
- **`TODO` and `pending` statuses are expected here.** This is a working record of
  verification *in progress*, not a record of completed validation.
- **No confidential reviewer information** belongs here (no private identities, contracts,
  or material a reviewer asked to keep confidential). Keep entries to technical content
  and publicly shareable review notes.
- A conclusion is **summarized in the public documentation only after its evidence and
  recorded status justify it** — not merely because it appears in a ledger entry.

Every ledger entry and review record carries this notice at the top:

> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

## Contents

```
verification/
  README.md                         <- this file
  mastery-ledger/
    index.md                        <- index of entries + current statuses
    template.md                     <- reusable entry template
    entries/                        <- one file per central result
  review-records/
    template.md                     <- reusable review-record template
                                       (records added per major milestone / review / release)
```

## Evidence categories (shared with the public policy)

Each claim's evidence is one or more of:

- **a.** source / authoritative reference
- **b.** independent derivation
- **c.** executable reproduction / numerical comparison
- **d.** qualified external **human** review

**Cross-model review** (one model auditing another) is recorded *separately*: it supports
category **c** and strengthens error detection, but it is **not** category **d**.
Verification effort scales with the **consequence and uncertainty** of the claim; not
every claim needs every category. Two AI systems agreeing count as **one** category,
never as external human review.

## Mastery-ledger statuses (demonstrated, not subjective)

Statuses describe *demonstrated* progress, in roughly increasing order. They are not a
self-rated "mastered":

| Status | Means |
|---|---|
| `identified` | the result and its role are named |
| `explained` | the director has explained it in their own words (recorded in the entry) |
| `derived` | the governing relation has an independent derivation (b) |
| `reproduced` | the result is reproduced by executable evidence (c) |
| `stress-tested` | limiting/sensitivity cases checked (c) |
| `externally-reviewed` | a qualified external **human** review exists (d), with scope recorded (cross-model review is noted separately and does not satisfy this status) |

An entry may legitimately sit at a low status with higher-status items marked `TODO`.

## When a record is required

A **review record** is required for **major milestones, formal cross-model reviews, and
releases** — not for every development interaction. The major-milestone workflow that
produces these records is defined in
[`docs/development/phase-b-roadmap.md`](../docs/development/phase-b-roadmap.md).
