# OTB-G001 — Fixes Report

**Gate:** OTB-G001 · Stage 2, S2 (two-phase acquisition / evaporator)
**Branch:** `stage-2/s2-evaporator` · reviewed artifact `6522da7` · base `main` @ `155b10c`
**Method:** METHOD v1.0 · **Tier 2** · **Date:** 2026-07-25 · **Builder:** Claude (Claude Code)

**Review verdict:** FAIL — **8 blockers, 2 major**, 87 files read, freeze verified.
**Disposition:** six `accept`, four `accept_with_modification`, all `product`. Zero appeals.

> **`main` untouched. No tag. No release. Nothing in the shared folder.**

---

## 1. Headline

| Metric | Reviewed (`6522da7`) | After fixes |
|---|---|---|
| Full suite (CoolProp 7.2.0) | 630 passed, 3 xfailed | **697 passed, 3 xfailed** |
| Failures / skips | 0 / 0 | **0 / 0** |
| Coverage (CI gate 90 %) | 96 % | **95.78 %** |
| `ruff check src tests scripts` | clean | **clean** |
| Checks witnessed failing | 16 / 16 | **32 / 32** |
| Correlations with `evaluate` | 1 (GW86) | **2** (GW86 + Shah 1987) |

All ten findings are fixed. **Five were closed by one mechanism, not five patches.**
Two things were found that were *not* in the ten, and both are flagged for the Director
in §5.

---

## 2. The class-level fix

Five findings were the same defect wearing different clothes — **a declared constraint
that is recorded but never enforced**:

| Sibling | The constraint that existed and did nothing |
|---|---|
| F-02 | CHF value had no required provenance — any bare float accepted |
| F-03 | an entry with no evaluator still passed the rank-eligibility guard |
| F-04 | the fluid-applicability failure was written to a note, then ignored |
| F-06 | the correlation's turbulent basis was documented, never checked |
| **D-9** | **"tubes and annuli" was in the docstring, enforced nowhere** |

`src/orbital_thermal/registry/applicability.py` makes declared applicability binding on
**fluid, geometry, orientation, regime and provenance**. Two rules carry the weight:

- **Silence is not consent.** An axis a correlation *declares* but which the case does
  not *state* is itself a violation, consequence `BLOCK`. Without this the class returns
  as "declared, enforced when someone remembers to pass it" — which is what D-9 was.
- **Consequences, not annotations.** `check()` returns typed `Violation`s carrying a
  `Consequence`; the consumer folds the worst into the case status. Recording a violation
  without acting on it **is** the defect (that was F-04).

**R1 regression** — `tests/test_applicability_enforcement.py`: five sibling instances
**plus two controls**, including the case that must still rank, so over-enforcement fails
as loudly as under-enforcement. **DEBTS D-9 closes as a consequence**, not by a patch.

One deliberate act of restraint, recorded because it cuts the other way: the
provenance-unestablished label does **not** de-rank a case. Director direction on F-08 is
that the relabelling is "labelling only" and the limits "remain enforced as guards".
Making provenance de-rank would over-enforce past the ruling and de-rank every case
through Gungor & Winterton regardless of merit. It is carried as a caveat that travels
with the result instead. My first implementation got this wrong and de-ranked everything;
it was corrected before commit.

---

## 3. Per-finding

### The four accept-with-modification

**F-08 — labelling only; maths untouched.** The five numeric limits are relabelled
**provenance-unestablished** in the registry entry, the applicability spec,
`PROVISIONAL_DOMAINS` and the public docs, stated there as *not* the authors' declared
range while remaining enforced as guards. Three confirming locators added: Thome *EDB III*
§10.3.3 Eqs. [10.3.20]–[10.3.23]; *CFD Letters* 10(2) 2018 Eq. (3); Collier & Thome 3rd
ed. §7.4.3 Eq. (7.36). The citation now carries the volume/issue/pages confirmed by four
independent reference lists, and **no DOI is asserted** because none was obtained. The
Táboas `1.23` outlier is recorded as a transcription error, not a variant form.

**F-06 — enforce what is sourced, demote what is not.** Liquid-Reynolds turbulence guard
added; a laminar `Re_L` now **rejects** the case. The threshold reuses Stage-1's own
turbulent boundary so both stages classify regime identically, and its provenance is
stated honestly as an **internal project convention** — no consulted source prints a
Reynolds band for GW86, and the classical Dittus-Boelter range is *stricter*, so this
guard is the permissive end and tightening it is a recorded option rather than a silent
default. The seven-fluid database is enforced. Liquid Prandtl is recorded as a
deliberately **unenforced** axis with its reason: no sourced band was obtained, and the
Director direction names only the Reynolds guard.

**F-03 — Shah (1987) promoted.** `shah_2015` → `SOURCE_REQUIRED` / `UNSUPPORTED`, its
`pr_reduced` band **detached** (it now declares no domain at all), kept as a registered
blocked entry rather than deleted so the misattribution stays visible. Shah (1987)
promoted with an executable form, the band re-attributed, and its diameter database
recorded. Eligibility additionally requires an executable form where the entry declares
it needs one — **opt-in**, so B1/S1 entries registered on source and domain ahead of
their formula are unaffected (`lockhart_martinelli_chisholm` is the control).

**F-04 — the exclusion alters status.** Ammonia is de-ranked to `SENSITIVITY_ONLY`
through Gungor & Winterton, and the same mechanism applies to Shah (1987), from whose
23-fluid database ammonia is also absent. **Steiner–Taborek was not implemented** — S5
scope, per the direction.

### The six plain accepts

| # | Fix |
|---|---|
| **F-01** | `OnbCriterion` must be an instance, declare the fluids it is sourced for, and be **evaluated**. `"banana"`, `object()`, `0.0`, `1`, `[]` are all treated as *no* criterion. The `x = 0` boundary is reported as the **bulk-equilibrium saturation crossing**, and the reason string states explicitly that this is not an evaluated ONB transition. Entry stays `SOURCE_REQUIRED`. |
| **F-02** | `ChfResult` binds value, correlation id, citation, locator, fluid, geometry, evaluated domain, gravity and violations. A bare float raises `TypeError`. A result with violations cannot rank however small the ratio. Producing one requires **sourced** geometry and a heated length, so a case lacking either is blocked before a number exists. |
| **F-05** | `SaturationState` carries fluid, pressure, backend and version; `assert_state_consistent` validates it against the `LoopState`, and `loop_state_from()` builds the loop state *from* the saturation state. The untagged dict path was **removed**, not deprecated. Both demonstrated bypasses are now unconstructible. |
| **F-07** | Rebuilt on a **domain-valid** path through the guarded wrapper — see §4. |
| **F-09** | `check_domain` removed from the public wrapper; the unguarded seam is the low-level pure evaluator, whose docstring says so. A **signature** test asserts the parameter is absent, because the defect was an API affordance. |
| **F-10** | `assert_backend_pin()` runs on every saturation evaluation. The migration path is `override_backend_pin(version, review_record=...)`, which **refuses a blank review record** — not an environment variable that silently disables the guard. |

---

## 4. F-07: what the limiting case actually shows

The old test reached the single-phase base only by *also* sending `q'' → 0`, at `x = 0`
and `q'' = 0` — both outside the declared domain — through the unguarded evaluator.

Rebuilt through the **guarded** wrapper at the domain's own lower edge, the honest result
is that **the correlation does not recover its single-phase base anywhere inside the
declared domain**. At the lower corner (`x = 0.002`, `q'' = 2000 W/m²`, `G = 600`) it
still sits about **1.2×** above it, and the excess grows with quality and heat flux.

What the limiting case *can* honestly claim on a domain-valid path is the **direction**,
so a second test asserts the excess falls monotonically toward the corner without
reaching unity. The exact `x = 0`, `q'' = 0` collapse is retained but demoted to a
clearly labelled **out-of-domain analytic property**, with an assertion that the guarded
path refuses those inputs — so it can never again be read as ranked-path evidence.

**No agreement was manufactured, and no Director disposition changing the acceptance
criterion was sought or assumed.**

---

## 5. Two things found that were not in the ten

### 5.1 Three unflagged transcription errors in the supplied Shah (1987) extract

The extract carried two flagged hazards. Reconciling it against **Shah's own printing**
(*Fluids* 2023, 8, 90, Appendix A, Eqs. A1–A17 — obtained from the author's publication
archive) resolved both **and surfaced three more that were not flagged**:

| Term | Springer extract | Shah (2023) | Impact |
|---|---|---|---|
| **`Y`** | `Pe · Fe^0.4 · (μ_l/μ_v)^0.6` with `Fe = 1.54 − 0.032(L/d_h)` | `(G D cp_f/k_f)(G²/(ρ_f² g D))^0.4 (μ_f/μ_g)^0.6` | **Severe.** Conflates the *entrance-effect factor* with a **Froude group**. Both carry exponent 0.4, which is how it passed unnoticed. |
| **`Bo0(3)`** | `0.0024 Y^−0.105` | `0.00024 Y^−0.105` | Factor of **ten**; `Bo0` is the highest of three candidates, so this changes which branch wins at large `Y`. |
| **`Fx` (`x>0`)** | malformed, contains `0.24157` | `F3[1 + (F3^−0.29 − 1)(p_r−0.6)/0.35]^c` | `0.24157` is a mangling of `F3^−0.29`. |

Both flagged hazards resolved: Eq. (6.65)'s LHS **is** `F2`, and the mass-velocity range
is **4–2905 kg/m²s** (recorded provenance-conflicted, Shah preferred as instructed).

The **F2 exponent sign** also differed (`+0.42` vs `−0.42`), which the inputs did not
anticipate. It is settled **independently of authority** by continuity at `F1 = 4`:
`4^−0.42 = 0.5588` against the branch value `0.55`, versus a **3.25× jump** for the
positive exponent. Shah's high-Y rule is separately confirmed *numerically* against the
extract's printed `4.452` (`0.0052 × 1.4e7^0.41 = 4.428`, 0.5 %). Both are asserted as
tests — which is why **the subcooled branch is implemented rather than blocked**, as the
inputs permitted once confirmed.

### 5.2 Shah (1987) is gravity-explicit — no microgravity limit

Its correlating parameter contains `g`. As `g → 0` the Froude group diverges, taking `Y`
and the branch selection (`Y ≤ 10⁶` vs `Y > 10⁶`) with it. **This correlation has no
zero-gravity limit at all** — a stronger statement than the standing 1-g caveat, which
says the correlations are *derived* at 1 g.

It is enforced as the `gravity_explicit` applicability axis and refused at `g ≤ 0`.
**Raised for the Director**, because it bears directly on whether a two-phase CHF ranking
can mean anything in orbit, and on what a future microgravity-specific CHF source would
have to supply. It is recorded in the mastery-ledger entry as the sharpest open question
on that claim.

---

## 6. Witnessed-failure record (R2)

`scripts/witness_s2_checks.py` grows from 16 to **32** mutations, each tagged with the
finding it guards. It also now **refuses to run** when the imported `orbital_thermal` is
not the tree being mutated — the hazard named in the handoff, where a stray editable
install turns every mutation into a silent no-op.

**Result: 32/32 witnessed.** Reproduce with `python scripts/witness_s2_checks.py`.

**Eight were not witnessed on the first run, and the split matters.**

**Four were bad mutations of mine**, which the harness correctly refused to credit: a
body-level change where the defect was an API affordance (F-09); an anchor that matched
`declared_axes` instead of `check` (D-9); a single fold site mutated where the mapping
was the real seam (F-04); and two `expect_failing` lists naming tests that structurally
could not see the change.

**Four were genuinely weak tests** — which is what the witness exists to find:

- The **F-03 executable-form rule was not load-bearing on `shah_2015` at all**, because
  that entry's *status* already blocks it. Disabling the rule left every `shah_2015` test
  green. It now has a direct test on a synthetic `RESOLVED`/`PUBLISHED` entry that would
  otherwise rank, plus a control that ranks with its evaluator restored.
- The **F-04 mapping could be broken with every ammonia test still green**, because a
  full ammonia case is de-ranked by two independent paths. The consequence→status mapping
  now has its own test.
- The **Shah F2 continuity test asserted arithmetic, not the implementation**, and sampled
  two points on the same side of the branch boundary. It now locates `F1 = 4` exactly
  (`x_crit = −2.1988` at `Y = 10⁶`) and steps across it; the measured residual is 0.3 %
  against ~40 % for the wrong sign.
- The **`Bo0` constant could shift by a factor of ten unnoticed**, because `Bo0` is the
  highest of three candidates and the third only wins at large `Y`. There is now a direct
  assertion at `Y = 10⁹`, where the wrong constant takes over and raises CHF by ~66 %.

---

## 7. Suite delta from 630

```
reviewed (6522da7):  630 passed,  3 xfailed,  0 failed,  0 skipped
after fixes:         697 passed,  3 xfailed,  0 failed,  0 skipped
delta:               +67 passed
```

Coverage 95.78 % against the 90 % gate — `applicability.py` 100 %, `two_phase.py` 96 %,
`fluids.py` 98 %, `registry/two_phase.py` 89 %. Phase A and Stage-1 (`v1.1.0`) suites and
the frozen oracle points are untouched; the only Stage-1 file changed is
`registry/provenance.py`, whose eligibility change is opt-in and leaves every B1 entry's
behaviour identical.

---

## 8. Ledger

`dispositions/OTB-G001.yaml` — `action`, `commit` and `verified: true` filled on **all
ten**. `classification`, `disposition`, `rationale` and `status` **untouched**.

This was verified mechanically rather than by eye: after writing, the file is re-parsed
and every non-builder field on every finding is compared against the original parse, with
the run aborting on any drift. The four Director **DIRECTION** texts are preserved
verbatim and the builder's account appended below a labelled
`BUILT (Claude Code, 2026-07-25):` marker, never mixed with them. A **folded** block
scalar was used precisely so the round trip cannot alter his wording. All five rationale
seams survive, including the `degredation` spelling, which is his and is untouched.

`status` stays `open` on all ten: closure is the Director's.

---

## 9. Definition of done

- [x] One enforcement mechanism covering fluid, geometry, orientation, regime and provenance — not five patches
- [x] R1 regression with 5 siblings + 2 controls; **D-9 closed as a consequence**
- [x] F-08: bounds relabelled provenance-unestablished; **maths untouched**; three locators added
- [x] F-06: Reynolds guard added; seven-fluid database enforced
- [x] F-03: `shah_2015` de-eligible; band detached; **Shah 1987 promoted** with the band re-attributed
- [x] F-04: ammonia exclusion **alters status**; Steiner–Taborek **not** implemented
- [x] F-01, F-02, F-05, F-07, F-09, F-10 fixed as specified
- [x] Every new check **witnessed failing**; witness record shipped (§6)
- [x] Suite green from 630, grown; oracle-freeze and `v1.1.0` untouched
- [x] Ledger: `action` + `verified: true` on all ten; **no Director field touched**
- [x] No fabricated identifier anywhere in the diff (no DOI asserted for either paper)
- [x] Branch pushed. **`main` untouched, no tag, no release, nothing in the shared folder**
- [ ] Sol re-review — **not run by the builder**
- [ ] Director closure of the ten, and disposition of the gravity-explicit finding (§5.2)

---

## 10. Handback

Back to **Cowork** for machine verification and the re-freeze. The pickup was not run or
simulated, no adversarial subagent was launched, and nothing was deposited to
`Claude_GPT_Shared_Workflow`.

The S2 review record stays **OPEN**, now carrying a fix-cycle section; it is not
builder-closable.
