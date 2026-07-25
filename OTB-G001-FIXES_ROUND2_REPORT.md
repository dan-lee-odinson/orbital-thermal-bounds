# OTB-G001-FIXES — Round-2 Report

**Gate:** `OTB-G001-FIXES` · Phase B Stage 2, S2 · METHOD v1.0 · Tier 2
**Branch:** `stage-2/s2-evaporator` · `d487901` → **`dc06d66`** · **Date:** 2026-07-25
**Review:** Sol round 2 — 8 findings (5 blockers, 2 major, 1 minor). Zero appeals.
**Scope:** the **six `product`** findings. F-07/F-08 are `apparatus` and untouched.

> **`main` untouched at `155b10c`. No merge, no tag, no release. Nothing in the shared folder.**

---

## 1. Headline

| Metric | `d487901` | `dc06d66` |
|---|---|---|
| `reproduce_findings.py` | **6/6 defects reproduce** | **0/6** |
| Full suite | 697 passed, 3 xfailed | **732 passed, 3 xfailed, 0 failed** |
| Witnessed mutations | 32/32 | **44/44** |
| Coverage (gate 90 %) | 96 % | **96.11 %** |
| `ruff check src tests scripts` | clean | **clean** |

I ran `reproduce_findings.py` **before** touching anything and confirmed 6/6, then again
after. Every number above is from execution.

---

## 2. The class: boundary, not call site

Four of six were round-1 fixes returning. Each round-1 fix was real and was built — at
**one call site** instead of at the boundary, so the same wrong answer stayed reachable
through another door.

The R1 regression is `tests/test_boundary_enforcement.py`: **five sibling instances plus
two controls**, and it opens with a class-level test that **enumerates every public
value-producing entry point** and asserts each enforces — rather than re-testing the one
that was reported. That test is the actual deliverable of this round; the six individual
fixes are its instances.

**The near-miss worth recording:** my first attempt at F-03 made verification conditional
on a `fluid` argument. The probe walked straight through it by not passing one — the exact
call-site-not-boundary shape this round is about, reproduced by me while fixing it. It is
now unconditional, and that shape is itself a witnessed mutation
(`R2-F03-make-verification-optional-again`).

---

## 3. Per finding

**F-01 — gravity.** The boundary is now the gravity the database was taken at
(`reference_gravity_m_s2 = standard gravity`), which is **sourced**: 16 terrestrial
studies, and D6's "the default is standard gravity because the database is terrestrial".
Departure is a `DE_RANK` violation; `g ≤ 0` stays `REJECT`. Only the ±1 % tolerance is a
convention, labelled as one — it admits Earth's ~0.3 % surface variation so terrestrial
labs anywhere still pass. **See §4 for the threshold, which is reported, not substituted.**

**F-02 — CHF binding.** Both halves, since neither alone closes it. `ChfResult` is
**unconstructible outside the evaluator** (module-private mint token; direct construction
*and* `dataclasses.replace` raise), and the **consumer verifies**: `classify_chf_band`
requires the case's own `CaseBinding` and refuses a result whose fluid, pressure,
geometry, diameter, orientation, mass flux or gravity differ.

**F-03 — fluid identity.** Established by **re-deriving** the state from the pinned
backend and comparing all 13 properties plus backend and version. That is the only test a
relabelling cannot pass, because it never reads the label. Verification is
**unconditional** (see §2).

**F-04 — the public wrapper.** `flow_boiling_htc` runs the mechanism itself and returns
`HtcResult(value, violations, caveats)`; every caller moved. `BLOCK`/`REJECT` raise;
`DE_RANK` returns **with the violations attached** — deliberately, because ammonia must
remain evaluable as a *sensitivity* under ruling D4 and raising would wrongly escalate
every de-ranked coolant to rejected. The split is a consequence of D4, not convenience.
The false docstring sentence is gone, and a test asserts it stays gone.

**F-05 — the pin override.** `review_record` must resolve to a real file under
`verification/review-records/` matching the naming in use there.

**F-06 — inlet quality.** Enforced at `[-2.6, 0.85]`. The two valid probe points are
unchanged **to the digit** (`x_in = 0.0 → 880628.1560252411`;
`x_in = -2.6 → 3170261.361690868`), confirming the correlation itself was not perturbed.
**See §4 for the provenance, which is not what the handoff described.**

---

## 4. Two places where this handoff was wrong — checked, not assumed

The handoff asked to be checked. Both items below were verified by execution or against
the sources before being acted on, and both are recorded in the registry.

### 4.1 F-01: `Y ≥ 10⁶` does not work as an *absolute* gravity cutoff

The direction was to use Shah's own branch threshold rather than invent a number, and to
**stop and report** if it did not work. It does not work as literally described, so:

- **At standard gravity, `Y` already exceeds 10⁶ at `G ≈ 1400 kg/m²s`** — well inside
  Shah's declared 4–2905 range. An absolute "`Y ≥ 10⁶` ⇒ gravity violation" test would
  reject ordinary terrestrial high-mass-flux cases.
- **The crossing gravity is case-dependent**, not a constant: 0.33 g at `G = 1000`,
  0.0014 g at `G = 300`. That is *why* it was measured to fall "between Mars and milli-g"
  — the range is the spread across mass flux, not a single boundary.

**Applied as a straddle instead.** If gravity moves a case across the threshold *relative
to its value at 1 g*, the calculation procedure has flipped and the case is `REJECT`ed.
This uses the sourced number correctly and cannot misfire at 1 g, where the two values are
equal by construction. **No round number was invented.** A test pins the misfire case so
the reasoning cannot quietly regress.

### 4.2 F-06: the inlet-quality provenance is reversed in the handoff

The handoff stated the printings conflict — *"the Springer microscale text gives −2.6,
Shah's own 2023 paper gives −4.00"*. Both attributions are reversed and the two quality
axes are conflated. What the sources actually print:

| | inlet quality | critical quality |
|---|---|---|
| **Springer microscale text** | **−4.00 to 0.85** | −2.6 to 1 |
| **Shah (2023) §3.1** | *not stated* | −0.26 to 0.96 |

So inlet quality is **single-source, not conflicted**, and −2.6 is Springer's *critical*
quality bound — a different axis, already enforced separately at Shah's tighter −0.26.

**The ruling is applied exactly as given anyway**, because it is implementable and
conservative: −2.6 is *tighter* than the only sourced inlet bound (−4.00), and CHF is the
**denominator** of `q″/CHF`, so a tighter bound can only exclude cases, never admit one.
The discrepancy is recorded in `SHAH_1987_INLET_QUALITY_NOTE` rather than silently
reconciled (C8) — a registry asserting "−2.6 is Springer's inlet bound" would state
something Springer does not say.

---

## 5. Witnessed-failure record (R2)

`scripts/witness_s2_checks.py` grows 32 → **44**, twelve new mutations each reopening the
specific door a round-1 fix left open. **44/44 witnessed.** Reproduce with
`python scripts/witness_s2_checks.py`.

New: enforce gravity only at zero · drop the database-gravity declaration · disable the
branch straddle · let a `ChfResult` be hand-built · stop verifying the case binding ·
compare the fluid field to itself again · make verification optional again · compare only
the headline properties · **discard the violations on the way out of the public wrapper** ·
accept any non-blank review record · unbound the inlet-quality axis · stop passing inlet
quality to the guard.

**Three were not witnessed on the first run:**

- The **F-09 anchor had rotted** — `flow_boiling_htc`'s signature changed with the F-04
  API change. Reported as NOT WITNESSED rather than skipped, which is the harness working:
  an anchor that no longer matches proves nothing.
- My **R2-F04 mutation was malformed** and produced a `SyntaxError`, so the suite failed
  to *collect* and no named test failed. Replaced with one that computes the violations and
  **discards them on return** — semantically the precise failure mode the handoff excludes,
  and valid Python.
- The **blank-review-record branch turned out to be genuinely redundant**: the resolver
  rejects a blank string too, so deleting the branch changed nothing. It earns its place
  only through its distinct message, which names the property-drift re-verification the pin
  requires — so the test now asserts that specific message and the branch is no longer
  deletable unnoticed.

---

## 6. Suite delta from 697

```
d487901:  697 passed,  3 xfailed,  0 failed,  0 skipped
dc06d66:  732 passed,  3 xfailed,  0 failed,  0 skipped
delta:    +35 passed
```

Coverage 96.11 %; `applicability.py` 100 %, `two_phase.py` 97 %, `fluids.py` 96 %.
Oracle-freeze and the `v1.1.0` suites untouched.

**One cost worth naming:** suite wall-clock roughly doubled (≈34 s → ≈66 s). F-03's fix
re-derives the saturation state from CoolProp on every consistency check, which is the only
test a relabelling cannot pass. It is a deliberate trade — verification cost for an
unfakeable guard — and it is stated here rather than left to be discovered.

---

## 7. One thing for the Director / Cowork, not fixed here

**`classification` is `null` on all eight ledger findings.** The handoff states them
(six `product`, two `apparatus`) and I worked to that, but the shipped
`dispositions/OTB-G001-FIXES.yaml` carries `classification: null` throughout.
`classification` is a Director field I must never write, so this is **reported, not
fixed**. Given round 1's ledger-lint defect was of exactly this shape — a field the
paperwork claimed was set and was not — it is worth checking before the re-freeze.

---

## 8. Definition of done

- [x] `reproduce_findings.py` reports **0/6**, and each of the six is also covered by real tests
- [x] F-01 threshold **sourced**, not invented — and the reading that does not work is reported (§4.1)
- [x] F-02: consumer verifies the binding **and** the result is unconstructible outside the evaluator
- [x] F-03: compared against the case's declared fluid, full property set, **unconditionally**
- [x] F-04: enforcement at the boundary, API changed as authorised, **docstring corrected**
- [x] F-05: review record must resolve to a real file
- [x] F-06: **−2.6** enforced, provenance recorded as it actually is, stale caveat removed
- [x] R1 regression: 5 siblings + 2 controls; every new check **witnessed failing** (44/44)
- [x] Suite green from 697 and grown; oracle-freeze and `v1.1.0` untouched
- [x] Ledger: `action` + `commit` + `verified: true` on the six; F-07/F-08 and every Director field untouched
- [x] No fabricated identifier anywhere in the diff
- [x] Branch pushed. `main` untouched, no tag, no release, nothing in the shared folder
- [ ] Sol re-review and Director closure — not the builder's

---

## 9. Handback

New head **`dc06d66`** for Cowork to re-freeze against. The ledger's six `commit` fields
point at it.

The packet scope in `PACKET_LAYOUT.tsv` will need rows for the two files added this round
(`tests/test_boundary_enforcement.py`, this report) plus the previous round's packaging
report, which was also absent from the 82-row scope.
