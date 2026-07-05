<!-- Major-milestone review + release record (B8). OPEN until the staged PR is reviewed and the
reviewed commit SHA + final disposition are recorded below; then CLOSED and v1.1.0 is tagged. -->
> **Working verification record:** This document may contain incomplete, provisional, or
> unresolved material. Its inclusion in the repository does not indicate validation or
> acceptance of the associated technical claims.

# Review Record: B8 - Review and release decision (v1.1.0)

## Record Metadata
- **Record status:** **CLOSED - B8 approved; Phase B v1.1.0 release authorized.** Staged PR
  director-reviewed at the final green commit; the initial `7a854ab` failed the clean-room
  smoke on the per-release version pin, fixed in `542ad0f` (`scripts/smoke_test.py`).
- **Date:** 2026-07-04
- **Reviewed commit:** `542ad0f` (`chore/b8-release-decision` head; green including the clean-room smoke). Supersedes `7a854ab`, which failed the smoke on the version pin.
- **Reviewer(s):** **project director (Dan Lee-Odinson) only** for this gate. Cross-model
  (GPT-5.5) review may be added and is recorded separately; it is **not** qualified external
  human engineering review.
- **Trigger:** major milestone (B8; release decision).
- **Disposition:** **Proceed to v1.1.0 with narrowed claims and explicit limitations** (staged-PR checks green; director review complete).

## Automated release check (regression baseline = `v1.0.1`)
- **Full test suite:** 548 passed, 3 xfailed, 0 failed.
- **Phase A / published verification suites:** `verify_suite.py`, `verify_paper3.py`,
  `companion/verify_ai1.py` all pass -> **no Phase A result changed**.
- **Oracle-freeze** (`external_models/mccalip_thoughts/verify_oracle_reproducible.py`, external
  attestation required): passes.
- **Examples:** all four `examples/*.py` pass (example 04 exits cleanly with and without CoolProp).
- **Wheel clean-room smoke:** `scripts/smoke_test.py`'s per-release version pin updated
  `1.0.1 -> 1.1.0`; the smoke reconfirms the **published AI1 point 337.1 K** and the
  **edge-on correction +6.349684 K** are **unchanged** -> a direct no-regression check.
- **No published `v1.0.1` number changed** (the Phase A suites and the oracle-freeze are the
  regression guard). Version bumped `1.0.1 -> 1.1.0` (metadata only; no computed result changed).

## External review statement (per the director's B8 direction)
- **Qualified external human review of the central transport/pressure claims is not currently
  available for this B8 gate.** The absence is **not** treated as a silent pass.
- **Cross-model review does not count as qualified external human review.**
- The reviewer for this gate is performing **project-director review only**: scope, claim
  discipline, evidence labeling, reproducibility, documentation consistency, and release judgment.
- The release proceeds **only with explicit limitations**, not as physically validated or
  flight-qualified.

### Required wording (recorded verbatim; also placed in the public docs)
- "No qualified external human engineering review has yet validated the central
  transport/pressure claims."
- "The Phase B Stage-1 model remains a reduced-order research and comparison framework."
- "It is not flight-grade, not hardware-validated, and not suitable for certification or
  safety-critical design."
- "External qualified review remains a future target before stronger engineering claims are
  made."

## Release decision: **Proceed to v1.1.0 with narrowed claims and explicit limitations**

**Allowed claim (v1.1.0):** Phase B Stage 1 adds a **verification-supported, reduced-order,
single-phase chip-to-radiator modeling and trade-study framework**, with documented assumptions,
executable tests, review records, and explicit limitations.

**Disallowed claims (must not appear):** externally validated; flight-grade; hardware-validated;
qualified for spacecraft design; total thermal-system mass closure; best architecture; complete
Starcloud / Suncatcher architecture judgment; validated transport/pressure physics by qualified
human review. *(Docs scanned; none present.)*

**Required limitation (recorded):** No qualified external human engineering review has yet
validated the central transport/pressure claims; the model remains a reduced-order
research/comparison framework.

## Public-claims hygiene
- **README wording ("certified"):** README wording was updated to avoid public-facing
  ambiguity around the word "certified," while the underlying Phase A technical meaning was not
  changed. The transient-solver adjective/verb uses of "certified" were replaced with
  convergence-checked language, and the "convergence certificate" section now carries an explicit
  definition that the term denotes an internal numerical convergence certificate, not external
  validation, engineering sign-off, qualification, or flight certification.
- **Historical CHANGELOG v1.0.0 entry (not rewritten):** The historical CHANGELOG v1.0.0 phrase
  "transient convergence certificate" is retained as release-history language. In this project,
  "certificate" in that context means an internal numerical convergence certificate produced by
  solver checks; it does not mean external validation, engineering sign-off, qualification, or
  flight certification.

## Verification level
- **d (qualified external human review):** **not obtained** -> recorded inability + explicit
  decision (this record). Level d remains `pending` for every ledger entry.
- Cross-model adversarial review: completed and CLOSED at the majors (B4, B6); recorded
  separately in their review records. Not a substitute for level d.

## Future action item (standing)
Seek targeted external review from a **qualified spacecraft thermal / pumped-loop reviewer** of
the central transport/pressure claims. This B8 documentation/release gate is **not** blocked on
review that is not currently available; level d advances if/when such review is obtained.

## Release gating (director's condition)
Tag `v1.1.0` **only** after the staged B8 PR passes: full tests; docs build; reproduction/
regression checks; review-record updates; project-director review; cross-model review if
requested. **Do not merge/tag until this record contains the exact reviewed commit SHA and the
final disposition.**

## Findings / director review
Project-director review of commit `7a854ab`:
1. **Release check verified green:** full suite 548 passed / 3 xfailed / 0 failed; Phase A /
   published `v1.0.1` suites + oracle-freeze pass (no regression); all four examples pass;
   wheel builds at 1.1.0, the MIT-only license check passes, and the **clean-room smoke
   passes** (per-release version pin updated to 1.1.0; AI1 337.1 K + edge-on 6.349684 K
   unchanged); `ruff` (library/tests/scripts/examples) clean.
2. **Claim discipline verified:** only the allowed claim is asserted; the disallowed-claim
   scan of the docs/README/CHANGELOG is empty; the required limitation wording is present in
   `README.md`, `docs/chip-to-radiator-model.md`, `CHANGELOG.md`, and this record.
3. **External review status confirmed:** qualified external human review of the central
   transport/pressure claims is not currently available; recorded as such; cross-model review
   is noted as **not** a substitute (level d remains `pending` for all entries).
4. **Decision stands:** proceed to v1.1.0 with narrowed claims and explicit limitations.

## Disposition
**CLOSED. Proceed to v1.1.0 with narrowed claims and explicit limitations.** Reviewed commit
`542ad0f + docs-hygiene follow-up`; the squash-merge commit on `main` is tagged `v1.1.0`. Standing future action: seek
targeted qualified-human review of the transport/pressure claims (level d).
