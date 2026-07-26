# OTB-G002 — S3 Build Report

**Gate:** `OTB-G002` · Phase B Stage 2, **S3** · METHOD v1.0 · **Tier 2** (ruling B7) · target `v1.2.0`
**Branch:** `stage-2/s2-evaporator` · `e22498c` → **`d45d4b3`** · **Date:** 2026-07-26

> **`main` untouched at `155b10c`. No merge, no tag, no release. Nothing in the shared folder.**

---

## 1. Headline

| Metric | `e22498c` | `d45d4b3` |
|---|---|---|
| `reproduce_s3_baseline.py` | **3/3 defects present** | **0/3** |
| Full suite | 732 passed, 3 xfailed | **765 passed, 3 xfailed, 0 failed** |
| Witnessed mutations | 44/44 | **54/54** |
| Coverage (gate 90 %) | 96 % | **95.79 %** |
| `ruff check src tests scripts` | clean | **clean** |

I ran the baseline before touching anything and confirmed 3/3.

**The milestone's headline result is negative, and that is the result.** The reference
pressure-drop correlation does not apply to this loop at all — and the source says so
in one sentence.

---

## 2. §0's question, answered from the source

> Collier & Thome §2.4 p. 54, **verbatim**: *"The correlation was developed for
> horizontal two-phase flow of **two-component** systems at low pressures (close to
> atmospheric) and its application to situations outside this range of conditions is
> not recommended."*

Three axes, all explicit. This loop is **single-component** ammonia, **not horizontal**,
and runs to **20 bar** — it meets none of them.

### 2.1 The handoff's premise about Chisholm (1967) is wrong

§0 supposed: *"Chisholm (1967) is presumably what extends the correlation beyond those
conditions — that is why A4 names the pair."* **The source does not support that.** Read
directly, Collier & Thome attribute:

| Source | What §2.4 says it does |
|---|---|
| **Chisholm (1967)**, p. 52 | corrects the treatment *"by allowing for the **interfacial shear force (S)** between the phases"* — it fixes the annular-flow void-fraction inconsistency, **not** the validity range |
| **Chisholm (1963)**, p. 54 | supplies **C = 1.36** at the *critical* pressure, inside Martinelli–Nelson's construction |
| **Martinelli–Nelson (1948)**, p. 54 | **is** the single-component / pressure extension — *"enable the application of the model to single component systems"* — with tabulated φ_lo from 1.01 to 221.2 bar (Table 2.2) |

So the route from the declared basis to this loop is **Martinelli–Nelson (1948)**, which
is not in the registry, not in the bundle, and not what ruling A4 names. Under C1 it is
**not reconstructed**.

**Therefore §0 option 2**: the entry ships implemented as far as the sourced form allows,
refusing outside it, with the gap named.

### 2.2 What was implemented, and how each part was established

> **CORRECTED after machine verification (V-02).** The paragraph that stood here
> asserted that **Eq. (2.68) was not legible in the source**. That was **false**, and it
> is the finding V-02 raised. Eq. (2.68) is sharply printed on p. 53:
> `φ_f² = 1 + C/X + 1/X²`. What was degraded is the **PDF's embedded text layer** — an
> automated extraction returns `"1 + _ + _2"` — not the source. Describing an extraction
> as the source is exactly the failure the "read the page" rule exists to prevent. The
> original text is replaced rather than annotated, because a provenance claim that is
> false should not survive in the record even with a correction beside it.

Everything below was **read from the rendered pages**:

- **Eq. (2.68)**, p. 53 — `φ_f² = 1 + C/X + 1/X²`
- **Eq. (2.69)**, p. 53 — `φ_g² = 1 + CX + X²`
- **Eq. (2.67)**, p. 52 — `X² = (dp/dz F)_f / (dp/dz F)_g`
- the p. 53 Chisholm **C** table — 20 / 12 / 10 / 5, which **match the repo's pinned
  `CHISHOLM_C` exactly**, an independent confirmation of an S1 value

**The real limitation, which is worth recording:** this PDF's text layer is degraded, so
anything taken from it must be read from the rendered page.

**The derivation is retained, re-labelled.** `φ_g² = φ_f² X²` follows from the
definitions plus (2.67), and reproduces the printed (2.68) from the printed (2.69). It is
an **independent confirmation** of the printed equation — a genuine cross-check that
would catch a transcription slip in either — **not the equation's source**. The test
asserting it is kept.

Also implemented: the **acceleration** term and the **static** term. The acceleration
term is stated in the homogeneous limit deliberately — the separated-flow version needs
a void fraction, and the void-fraction relation in this source is the one Collier &
Thome themselves show to be *inconsistent* for annular flow (p. 52). Using a relation
the source disowns would be worse than a named modelling choice.

### 2.3 The pressure ceiling

The declared `P_Pa` ceiling of 2 MPa is **not traceable** to "close to atmospheric",
which is qualitative and gives no number. It is retained as an enforced guard under
ruling D1 and labelled **provenance-unestablished**. **No number is invented to replace
it** — the composition and orientation axes are what actually bite, and those are
verbatim.

---

## 3. Rulings implemented

**D12 — gravity is an enforced applicability axis.** The static term is computed, and
refuses at `g ≤ 0` rather than contributing zero. Omission would be *exact* and still
wrong: it builds a microgravity model out of a 1-g-derived frictional correlation,
leaving a model exact in one term and terrestrial in the next with nothing marking the
seam.

> **Building this exposed a real defect in the S2 mechanism.** The database-gravity
> check was nested under `gravity_explicit`, so a correlation whose *formula* carries no
> `g` — like this one — was never checked against the gravity its *database* was taken
> at. A 1e-6 m/s² case passed unflagged until the D12 consistency test caught it. The
> two declarations are now independent. That is a latent hole in the round-2 F-01 fix,
> found by building the second leg.

**D10 — condenser is an energy boundary.** Heat out, state change, bookkeeping against
the A3 sink. **No condensation coefficient is computed, and no condensation entry is
added.** `required_area_m2()` **raises**, naming DEBTS D-11, rather than returning a
plausible number.

**D8 — pump inlet is a subcooling margin** on the AMS-02 precedent. **No non-zero
default margin is invented** — AMS-02 establishes the *criterion*, not a number. The
HI 9.6.1 definitions and the NPSH3 warning (*`NPSHA = NPSHR` is the onset of damage, not
a safe operating point*) are recorded in the entry note and deliberately not implemented.

**D11 / D7 — bore is swept, length is derived.** The band is **read from the registry**
(GW86 binds both ends at 1.224–32 mm), and the provenance-unestablished label travels
into the sweep's **output**. Length is computed from the duty and **cross-checked against
the enthalpy rise it claims** — a duty that disagrees is refused, not averaged. A bore
outside the band is **recorded as a blocked point, not dropped**, because a sweep that
silently omitted its failures could not report a negative result.

**A4 — Friedel and Müller–Steinhagen–Heck untouched**, and a test pins that.

---

## 4. DIR-01 and DIR-02 — fixed inside S3 against closed gates (ruling D13)

This is disclosed plainly, as D13 requires: **the S3 packet contains fixes to defects
raised against closed gates alongside new work.**

**DIR-01.** The unsourced *"the S2 evaporator geometry is channels"* claim is corrected,
and `round_tube` / `annulus` / `channel` are now **defined and disjoint**, so a 2.6 mm
bore cannot be simultaneously inside and outside a declared basis. "Small-bore" is
recorded as a description of *where in the range a case sits*, not a separate geometry.

**DIR-02 — closed generically, which is the point.** Round 1 named this class and fixed
it by demoting one entry's status; the permissive rule survived, and this is its **third
occurrence**. So the rule itself changed: eligibility now requires that an entry can
actually supply a value, and it is **no longer opt-in**.

The vocabulary was the other half. `RESOLVED` was carrying two meanings — "the sourcing
question is settled" and "this can be evaluated" — so `Status.IMPLEMENTATION_REQUIRED`
splits them.

**Why the generic rule does not break Stage 1.** Two B1 entries
(`thermal.spreading_resistance`, `hydraulic.minor_losses`) have always had
`evaluate=None` while being evaluated by a *module* — `solid_network.spreading_resistance`
and the `minor_loss_K` term of `pumped_loop.pressure_drop`. They were never
unimplemented, only **undocumented**, and `evaluate=None` could not express the
difference. The new `executable_form` field records where they live, so the rule spans
"a callable on the entry **or** a named module implementation". Nothing about their
behaviour changed; the control test pins that.

---

## 5. Witnessed-failure record (R2)

`scripts/witness_s2_checks.py` grows 44 → **54**. **54/54 witnessed.** Reproduce with
`python scripts/witness_s2_checks.py`.

**Six were not witnessed on the first run**, and the split is the useful part:

- **Three rotted anchors** — the harness working. The S2-era *"no dP entry may be
  implemented"* mutation went obsolete the moment S3 legitimately implemented the
  reference; it is **replaced by its successor** (implementing a named *sensitivity*
  must still fail). The R2-F01 gravity anchor moved when the database-gravity check was
  separated out.
- **Two superseded mutations, removed rather than repaired.** Both F-03 opt-in mutations
  guarded `requires_executable_form`, which the generic DIR-02 rule supersedes — the
  flag no longer decides anything, and mutations guarding a dead branch would inflate
  the count without adding coverage.
- **One genuinely weak test.** `test_the_negative_result_is_the_result` checked only for
  the "NEGATIVE RESULT" line, so the **provenance-unestablished label could have been
  dropped from the sweep output with the test still green** — exactly what D11 asks to
  appear in the output. It now asserts the label.

Also recorded rather than left puzzling: the class-level DIR-02 sweep **cannot** witness
its own rule while no shipped entry is status-eligible-but-formless, which is the
desired end state. The synthetic-entry test is what holds that rule.

---

## 6. R1 class-level regression

`tests/test_two_phase_loop.py`. The class is *"a constraint the source states but the
artifact does not carry"* — four siblings (composition, orientation, pressure, gravity)
plus two controls: a case inside the declared basis must still evaluate cleanly, and the
two module-implemented B1 entries must not be demoted.

---

## 7. Suite delta from 732

```
e22498c:  732 passed,  3 xfailed,  0 failed,  0 skipped
d45d4b3:  765 passed,  3 xfailed,  0 failed,  0 skipped
delta:    +33 passed
```

Coverage 95.79 %; `two_phase_loop.py` 93 %, `applicability.py` 98 %. Oracle-freeze and
the `v1.1.0` suites untouched.

---

## 8. What this handoff got wrong, and one thing it did not anticipate

1. **§0's Chisholm (1967) premise** — §2.1 above. The extension is Martinelli–Nelson
   (1948), and Chisholm (1967) does something else entirely.
2. **Not anticipated: the D12 work exposed a latent hole in the round-2 F-01 fix** —
   §3. Gravity was enforced only for correlations whose *formula* contains `g`, so the
   pressure-drop leg would have gone unchecked. Building the second leg is what surfaced
   it, which is an argument for D12's "the two legs must be consistent" beyond the one
   the ruling gives.

Nothing else in the handoff was found to be wrong. The baseline numbers, the bore band,
the ruling summaries and the scope boundaries all matched.

### 8.1 And one thing **this build** got wrong — added after machine verification

**The illegibility claim about Eq. (2.68) (V-02).** It was false: the equation is
sharply printed and the *PDF's text layer* is what was degraded. See §2.2, which has
been corrected.

It matters more than its consequence suggests. The number was right, the `formula` and
`locator` fields were accurate, and nothing wrong shipped — but the **method** for that
one equation was derivation under a false premise, carrying a justification (*"the
source is illegible here"*) that would have travelled with a wrong answer just as
readily as a right one, and nothing in the artifact would have prompted anyone to go and
look at the page.

**Scope of the lapse, verified independently rather than assumed.** Every other
assertion this build makes about that source was re-checked against the **rendered
pages**, not the extraction: Eq. (2.67) and the Chisholm (1967) interfacial-shear
attribution on p. 52; the p. 53 C table; the p. 54 validity sentence, the
Martinelli–Nelson (1948) attribution and Chisholm (1963)'s `C = 1.36`; and Table 2.2's
1.01–221.2 bar range on p. 55. **All correct, and Eq. (2.68) was the only place the text
layer was treated as the source.** That confirms Cowork's own check independently.

---

## 9. Definition of done

- [x] `reproduce_s3_baseline.py` reports **0/3**, each backed by real tests
- [x] LM/Chisholm **implemented as far as the sourced form allows and blocking outside it** — never reconstructed
- [x] Acceleration term implemented; **Friedel and Müller–Steinhagen–Heck untouched**
- [x] Gravity an enforced axis on the pressure-drop leg, consistent with `shah_1987`
- [x] Condenser is an **energy boundary**; no condensation coefficient computed, no entry added
- [x] `two_phase.pump.npsh` is a **subcooling margin**; HI 9.6.1 and the NPSH3 warning recorded
- [x] Bore band **read from the registry**, length **derived**, provenance label in the **output**
- [x] DIR-01 note corrected and vocabulary defined; **DIR-02 closed generically**
- [x] R1 regression (4 siblings + 2 controls); every new check **witnessed failing** (54/54)
- [x] Suite green from **732** and grown; oracle-freeze and `v1.1.0` untouched
- [x] No fabricated identifier anywhere in the diff
- [x] Branch pushed. `main` untouched, no tag, no release, nothing in the shared folder
- [ ] Sol review and Director disposition — not the builder's

---

## 10. Handback

New head **`d45d4b3`** for Cowork to package against.

Two carry-overs from the last round that remain open on Cowork's side: the round-2
ledger's `classification` is `null` on all eight findings, and `PACKET_LAYOUT.tsv` has no
rows for the files added since it was written (`tests/test_boundary_enforcement.py`, the
two round-2 reports, and now `src/orbital_thermal/two_phase_loop.py`,
`tests/test_two_phase_loop.py` and this report).

**DEBTS D-11** (no condensation entry of any kind, scoped to S4) is created by this
milestone and is not yet in the repository's own debts record — `DEBTS.md` lives in the
project home, not the repo, so it is flagged here rather than edited.
