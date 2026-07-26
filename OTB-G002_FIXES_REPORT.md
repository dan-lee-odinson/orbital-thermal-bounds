# OTB-G002 — Machine-Verification Fixes Report

**Gate:** `OTB-G002` · Phase B Stage 2, S3 · METHOD v1.0 · Tier 2
**Branch:** `stage-2/s2-evaporator` · `b16ca62` → **`cf812b7`** · **Date:** 2026-07-26

> **`main` untouched at `155b10c`. No merge, no tag, no release. Nothing in the shared folder.**

---

## 1. Headline

| Metric | `b16ca62` | `cf812b7` |
|---|---|---|
| `reproduce_g002_fixes.py` | **2/2 present** | **0/2** |
| `reproduce_s3_baseline.py` | 0/3 | **0/3** (unchanged) |
| Full suite | 765 passed, 3 xfailed | **784 passed, 3 xfailed, 0 failed** |
| Witnessed mutations | 54/54 | **61/61** |
| `ruff check src tests scripts` | clean | **clean** |

Both probes were run before touching anything: 2/2 present.

---

## 2. V-01 — a declaration where the rule needed a fact

`has_executable_form` was `bool(self.executable_form.strip())`. `"x"` made an entry
rank-eligible; so did a well-formed but non-existent path. **Nothing shipped broken** —
both real declarations resolved — and that is exactly why it needed raising. *"The
current entries happen to be correct"* is the standard that let round-1 F-03 return as
DIR-02.

A declared path is now **resolved**.

### 2.1 The design choice, and why

The handoff set out three options and asked for reasoning rather than compliance. **I
took the third — both — and the reasoning is that they do different jobs.**

**Lazy, cached resolution at the boundary.** Resolving at registry-construction time is
circular (`solid_network` and `pumped_loop` both import the registry); I confirmed
Cowork's finding rather than taking it. Resolution happens on first call and is cached,
so it is one import per path.

**The boundary fails *closed*, and quietly.** Resolution failure returns `False` rather
than raising, so `rank_eligible` stays a total predicate — a read-only property that
does an import is already a smell, and one that can *raise* would be worse. An entry
whose declaration does not resolve simply cannot rank.

**The test fails *loud*.** `unresolved_executable_forms` names the offender. This is the
half the boundary cannot do: failing closed means a typo would silently de-rank an
entry, which is safe but undiagnosable.

**Why not one or the other.** A test *alone* moves the guard back into a test — the
precise pattern DIR-02 was raised against. A boundary *alone* is a silent diagnostic.
Neither is sufficient, and the two are not redundant: one decides eligibility, the other
reports breakage.

**One addition the handoff did not ask for:** resolution is restricted to
`orbital_thermal.*`. A registry entry has no business naming an arbitrary importable
target, and `os.path.join` — resolvable *and* callable — would otherwise have been
admitted. It is a witnessed guard in its own right.

### 2.2 R1 and R3

**Five siblings** of *"the boundary admits a declaration where the rule needs a fact"*:
bare `"x"`; absent module; absent attribute; attribute that exists but is not callable;
resolvable and callable but outside the package.

**Two controls**, and the first is the one that matters: `thermal.spreading_resistance`
and `hydraulic.minor_losses` **still rank-eligible**; and a genuine module path is
honoured.

**R3** — the handoff correctly flagged that this fix touches import machinery, where
host semantics vary. Resolution is asserted **stable and cached** (same object on repeat
calls) and **case-significant** (`ORBITAL_THERMAL...` must not resolve on a
case-insensitive filesystem).

---

## 3. V-02 — the artifact said something false about the source

**The finding is correct and I was wrong.** I opened the page. Eq. (2.68) is sharply
printed on p. 53:

```
φ_f² = 1 + C/X + 1/X²                                        (2.68)
```

What is degraded is the **PDF's embedded text layer**, which returns `"1 + _ + _2"` from
a perfectly clear printed equation. I described an automated extraction as the source —
in the provenance fields whose entire job is to be true about the source. An extraction
is a transcription; it is just one nobody typed.

**Why this matters more than its consequence.** The number was right and the `formula`
and `locator` fields were accurate, so nothing wrong shipped. But the *method* for that
one equation was derivation under a false premise, and it carried a justification —
*"the source is illegible here"* — that would have travelled with a wrong answer exactly
as readily as a right one, with nothing in the artifact prompting anyone to go and look.
This project's rule after its last extract failure was **read the page**. This is that
rule lapsing for one equation.

### 3.1 What changed

Fixed at **all five sites**: the entry `note`, the `applicability` text, the
`# --- S3 executable form ---` comment block, the `phi_f_squared` docstring, and the
`test_two_phase_loop.py` docstring.

- Eq. (2.68) is recorded as **read from the page**.
- **The true limitation is kept**, because there is one: the text layer is degraded, so
  anything from this source must be read from the rendered page. Removing a false claim
  must not remove the real caveat sitting next to it — a control test pins that.
- **The derivation survives, re-labelled.** `φ_g² = φ_f² X²` is a genuine cross-check —
  it would catch a transcription slip in either (2.68) or (2.69) — so it is kept as an
  **independent confirmation of the printed equation**, not as its source. Another
  control test pins that distinction.
- Build report **§2.2 replaced** (not annotated: a false provenance claim should not
  survive in the record with a correction beside it) and **§8 extended with §8.1**.

### 3.2 The scope question, answered independently

The handoff asked me to confirm — not assume — that Eq. (2.68) was the only place the
extracted text was treated as the source. **Answering that from the text layer would
have repeated the error**, so I installed a renderer, rendered all seven pages, and
re-read every assertion from the images:

| Assertion | Page | Verdict |
|---|---|---|
| Eq. (2.68) `φ_f² = 1 + C/X + 1/X²` | 53 | **legible — my claim was false** |
| Eq. (2.69) `φ_g² = 1 + CX + X²` | 53 | correct |
| Chisholm C table 20 / 12 / 10 / 5 (tt/vt/tv/vv) | 53 | correct |
| Eq. (2.67) `X² = (dp/dz F)_f / (dp/dz F)_g` | 52 | correct |
| Chisholm (1967) = interfacial-shear correction | 52 | correct, verbatim |
| Validity sentence (horizontal, two-component, close to atmospheric) | 54 | correct, verbatim |
| Martinelli–Nelson (1948) = single-component extension | 54 | correct |
| Chisholm (1963) `C = 1.36` at critical pressure | 54 | correct |
| Table 2.2 range 1.01 – 221.2 bar | 55 | correct |

**Eq. (2.68) was the only place.** That confirms Cowork's own check independently.

One detail worth noting since it survived the audit: the source names the flow regimes
**viscous**/turbulent where the pinned `CHISHOLM_C` uses **laminar**/turbulent. That
difference was already documented in the registry, and the rendered table confirms the
four values map as recorded.

---

## 4. Witnessed-failure record (R2)

54 → **61**. **61/61 witnessed.** Reproduce with `python scripts/witness_s2_checks.py`.

New: admit a declaration instead of a fact (the exact pre-fix expression) · let a
declaration reach outside the package · accept a non-callable attribute · stop reporting
unresolved declarations · reassert that the printed equation was illegible · delete the
true limitation along with the false claim · relabel the cross-check as the equation's
source.

**Two were not witnessed on the first run:**

- The **unresolved-declaration reporter could not be witnessed by the sweep over shipped
  entries**, because every shipped declaration resolves — there is nothing for it to
  find, so breaking it changed nothing. Structurally the same as the DIR-02 class sweep
  last round. A **synthetic broken declaration** now holds it.
- **My V-02 mutation was imprecise**: it kept the word `READ` at the end of the line it
  replaced, so the string concatenation still produced `"READ FROM THE RENDERED PAGES"`
  and one of the two expected tests could not see it. The other did. **The expectation
  was corrected rather than the test weakened.**

---

## 5. Suite delta from 765

```
b16ca62:  765 passed,  3 xfailed,  0 failed,  0 skipped
cf812b7:  784 passed,  3 xfailed,  0 failed,  0 skipped
delta:    +19 passed
```

Oracle-freeze and the `v1.1.0` suites untouched. `ruff check .` still reports the same
8 pre-existing findings in `notebooks/`, left alone as instructed.

---

## 6. What this handoff got wrong

**Nothing.** Both findings reproduce, both are real, and the one piece of advice that
could have cost a cycle — that resolving at registry-construction time is circular while
resolving lazily is not — was checked before being given and is correct; I verified it
rather than taking it.

The V-01 write-up explicitly declined to dictate a design and invited a reasoned
refusal. I did not refuse: the boundary check is the right place, and §2.1 records why
the test alone would have reproduced the very pattern DIR-02 was raised against.

---

## 7. Definition of done

- [x] `reproduce_g002_fixes.py` reports **0/2**, each backed by real tests
- [x] V-01: eligibility requires a form that **can be reached**; design choice and reasoning in §2.1
- [x] V-01 control: `thermal.spreading_resistance` and `hydraulic.minor_losses` still rank-eligible
- [x] V-02: illegibility claim removed from **all five** sites; Eq. (2.68) recorded as read from the page; derivation retained and re-labelled
- [x] V-02: the **true** limitation — degraded text layer, read the rendered page — recorded in the note
- [x] V-02: build report §2.2 and §8 corrected; the independent re-check answered in §3.2
- [x] R1 per fix (5 siblings + 2 controls for V-01; 5 sites + 2 controls for V-02); harness grown 54 → **61**
- [x] Suite green from **765** and grown; oracle-freeze and `v1.1.0` untouched
- [x] No fabricated identifier anywhere in the diff
- [x] Branch pushed. `main` untouched, no tag, no release, nothing in the shared folder
- [ ] Sol review and Director disposition — not the builder's

---

## 8. Handback

New head **`cf812b7`** for Cowork to re-freeze against.

Carry-overs still open on Cowork's side, unchanged by this round: the round-2 ledger's
`classification` is `null` on all eight findings; `PACKET_LAYOUT.tsv` has no rows for the
files added since it was written; and **DEBTS D-11** (no condensation entry, scoped to
S4) is created by S3 but `DEBTS.md` lives in the project home rather than the repo.
