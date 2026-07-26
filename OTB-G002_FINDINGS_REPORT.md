# OTB-G002 — Reviewer-Findings Report

**Gate:** `OTB-G002` · Phase B Stage 2, S3 · METHOD v1.0 · Tier 2
**Branch:** `stage-2/s2-evaporator` · `6a97ad9` → **`7312a0c`** · **Date:** 2026-07-26

> **`main` untouched at `155b10c`. No merge, no tag, no release. Nothing in the shared folder.**

---

## 1. Headline

| Metric | `6a97ad9` | `7312a0c` |
|---|---|---|
| F-01 bore does not reach the physics | present | **fixed** |
| F-02 labels decide applicability | present | **fixed** |
| F-03 settled `x → 0` limit untested | present | **fixed** |
| F-04 NaN / impossible quality cross as applicable | present | **fixed** |
| Full suite | 784 passed, 3 xfailed | **815 passed, 3 xfailed, 0 failed** |
| Witnessed mutations | 61/61 | **70/70** |
| `ruff check src tests scripts` | clean | **clean** |
| `reproduce_g002_findings.py` | 3/4 present | **unusable — see §7** |

**The negative result survived, and it is now earned.** §6.

**The probe cannot score this round.** Three of its four checks pass the exact arguments
the mandated fix removes, and the fourth reports `RESOLVED` for a reason that is not
evidence. §7. I did not edit it.

---

## 2. F-01 — the swept variable never reached the physics

`sweep_bore` took `mass_flux_kg_m2s`, `dp_dz_liquid_Pa_m`, `dp_dz_gas_Pa_m`,
`liquid_regime` and `gas_regime` as caller-supplied scalars and handed each bore the same
five values. Bore moved the required length, and nothing else. Across the adopted
1.224–32 mm band the mass flux should span a factor of **685**; it was one number.

**The finding is correct, and its consequence is the one the handoff states.** A sweep
that holds the hydraulics fixed has not explored the space it reports on, so the
milestone's headline claim — no bore in the band is applicable — was a claim about a
space that was never entered.

### 2.1 The fix

`hydraulic_state_from_bore` derives, from the bore itself:

```
A = πD²/4            G = ṁ/A            G_f = G(1−x),  G_g = Gx
Re_f = G_f D / μ_f   Re_g = G_g D / μ_g
f from Stage-1's own friction machinery
dp/dz|_k = f_k ρ_k v_k² / (2D)
```

The five scalars are **gone from both signatures**. That is the class-level part:
accepting them is what made holding them constant possible, and a test pins their
absence. `BorePoint` now carries `mass_flux_kg_m2s`, populated for evaluated *and*
blocked points, so a sweep can show that its hydraulics moved — nothing in the previous
output could have revealed that they did not.

### 2.2 R1

Four siblings of *"a swept variable that does not reach the physics it is supposed to
move"*: mass flux, both phase Reynolds numbers, both phase-alone gradients, and the
acceleration term (which takes the mass flux and therefore did not vary with bore at
all). **Control:** the derivation is checked against the closed form, not merely checked
for varying — a wrong formula that happens to be monotone would otherwise pass.

---

## 3. F-02 — labels decided what the state should have decided

Three things were asserted rather than derived, and they were not the same kind of thing.
The fix separates them, which is why it is not one patch.

**Flow regime is derivable, so it is now derived.** `_regime()` classifies from Reynolds
number against Stage-1's own laminar threshold (2300), so the Chisholm `C` follows from
the state. This matters inside the adopted band and not only in principle: at 32 mm the
liquid Reynolds number is **2372**, a little over the threshold, so the band straddles it.

**Composition and orientation are not derivable, so they stay declarations — but they
are no longer freely assertable.** `case_contradictions()` refuses a case whose own
declarations contradict each other:

- a **registered single-component coolant declared `two_component`**. Ammonia and some
  mixture can present identical densities, so composition cannot be recovered from the
  numbers; but a case naming a pure registered coolant *and* claiming two components has
  contradicted itself, whatever the numbers say.
- **`horizontal` with a non-zero static height.** The static head is identically zero in
  horizontal flow, so a non-zero height says the flow is not horizontal.

It lives in `registry/applicability.py`, not in `sweep_bore` or in the pressure-drop
boundary, so every entry point gets it from **one** place (C9). A test asserts that
placement directly and then shows the sweep inheriting it.

### 3.1 One thing a reader could mistake for an unfixed F-02

Relabelling composition **still** flips applicability on an unchanged set of numbers, and
the probe treated that as the defect. It is not, and the fix deliberately keeps it:
Lockhart–Martinelli's declared basis *is* two-component, so whether it applies genuinely
depends on a fact that the densities do not carry. §6.1 shows the flip explicitly. What
changed is that the label can no longer be set to a value the case contradicts — which is
the Director's direction as written, *derive what is derivable and make the rest mutually
consistency-checked rather than independently assertable*, and not a stronger one.

### 3.2 R1

Regime computed rather than declared, both contradictions, and placement at the shared
boundary rather than the sweep. **Control:** a genuine two-component mixture
(`air-water`) with a zero height is not obstructed — the check must refuse
contradictions, not composition labels.

---

## 4. F-03 — the settled `x → 0` limit, tested against Stage-1

The finding is right and its characterisation is right: **the limit holds**, so this was
a missing test of correct behaviour, not a wrong number. I did not touch the maths.

The oracle is **Stage-1's own single-phase `Δp`**, recomputed inside the test from the
same bore, mass flow and liquid properties, so the test cannot drift away from the thing
it claims to recover. (The handoff's own probe used the literal `50.0000 Pa`; that literal
was only meaningful because the gradient was caller-supplied, and F-01 removes it.)

### 4.1 What the measurement actually shows, and why it changes the test

Convergence is **O(√x)**, and slow:

| `x` | `Δp_2φ / Δp_1φ` | `(ratio − 1)/√x` |
|---|---|---|
| 1e-3 | 1.303622 | 9.601 |
| 1e-4 | 1.096263 | 9.626 |
| 1e-5 | 1.030461 | 9.633 |
| 1e-6 | 1.009634 | 9.634 |
| 1e-7 | 1.003047 | 9.635 |
| 1e-8 | 1.000964 | 9.635 |

The rate is a **prediction, not a curve fit**: laminar gas friction gives `f_g = 64/Re_g ∼
1/x` while `v_g ∼ x`, so the gas-alone gradient vanishes as `x`, `X ∼ x^(−1/2)`, and
`φ_f² ≈ 1 + C/X` leaves an excess of order `√x`. The constant is stable to three figures
across five decades.

So the test asserts **both** the limit (recovery to 0.1 % at `x = 1e-8`) and the rate. The
rate assertion is the load-bearing one: a test that checked recovery at `x = 1e-5` and
demanded 1 % would read a **correct** model as broken, because the true residual there is
3 %. Testing the limit without knowing the rate is how a correct model gets "fixed".

---

## 5. F-04 — a sign test is not a finiteness check

`> 0` guards passed NaN straight through, because every comparison against NaN is false.
A NaN gradient or density crossed the boundary and returned `total_Pa = nan` **marked
applicable** — a value nobody downstream can distinguish from a real one. Qualities of
1.7 and −0.5 produced confident finite numbers for a mass fraction.

Finiteness is now checked explicitly and quality is bounded to `[0, 1]`.

**R1** uses the four input families the handoff names — gradient-driving inputs, mass
flow, density, quality — across NaN, `inf` and out-of-range, plus the control that the
physical cases still evaluate. The Director's spelling in F-04 is untouched.

### 5.1 The harness found a defect in my own fix

The first cut left **three** boundaries validating the same inputs independently:
`hydraulic_state_from_bore`, `_validate_hydraulic_inputs`, and an inline pair for
`height_m`/`gravity_m_s2`. Every test passed. The mutation harness would not:
reintroducing the sign test at any one site left the other two standing, so **no mutation
could show any single guard was load-bearing.**

That is the per-instance duplication C9 forbids, and an unwitnessable check is its
symptom rather than a separate problem. All hydraulic entry points now validate through
one function. **The mutation was not weakened to fit the code; the code was fixed.**

---

## 6. Did the negative result survive? Yes — and it is now earned

Corrected sweep, OTB loop conditions, ṁ = 0.01 kg/s, `x` 0.05 → 0.40, across the full
adopted band:

```
bore mm   L m      G kg/m2s   Re_liq     dP total Pa     applicable
 1.224    5.201     8498.6     62014     152235928.7     False
 2.600    2.449     1883.5     29194       2057345.0     False
 8.000    0.796      198.9      9488          4633.2     False
20.000    0.318       31.8      3795            58.7     False
32.000    0.199       12.4      2372             7.5     False

any_applicable = False
```

The hydraulics now move: mass flux over **685×**, total `Δp` over **2×10⁷×**, and the
liquid Reynolds number from fully turbulent down to 2372, just above the laminar
threshold. **The claim is the same and its basis is not.** Before, it was a statement
about one hydraulic state reported as though it were a band. It is now a statement about
the band.

D7 holds: this is a result. It is a statement about **basis**, not about arithmetic — and
that is exactly what the next section shows.

### 6.1 The control that proves what the negative result is about

Identical numbers, identical bores, declared as an unnamed two-component mixture instead
of ammonia:

```
any_applicable = True     (every bore, same dP to the last digit)
```

Nothing numerical changed. The negative result is driven entirely by the **composition
axis** — Lockhart–Martinelli's declared basis is two-component flow, and the OTB loop is
single-component ammonia. That is a real limit on what the correlation can be used to
claim, and it is now visible as such rather than buried under a frozen mass flux.

**DEBTS:** the single-component route is **Martinelli–Nelson (1948)**, not Chisholm
(1967) — recorded last round and unchanged. Closing this negative result requires that
entry, which is S4 scope.

---

## 7. What this handoff got wrong

The handoff asked me to assume it contained at least one thing of this kind. It does, and
it is in the machinery used to score the round.

### 7.1 Three probes are structurally incompatible with the fix they mandate

`reproduce_g002_findings.py` cannot reach `RESOLVED` against the fix the findings require.
F-01's remedy is that the caller-supplied hydraulic scalars **stop existing**; the probes
pass them:

```
[PRESENT ] F-01  PROBE ERRORED (TypeError: sweep_bore() got an unexpected
                 keyword argument 'dp_dz_liquid_Pa_m')
[PRESENT ] F-02  PROBE ERRORED (TypeError: two_phase_pressure_drop() got an
                 unexpected keyword argument 'dp_dz_liquid_Pa_m')
[PRESENT ] F-03  PROBE ERRORED (TypeError: two_phase_pressure_drop() got an
                 unexpected keyword argument 'dp_dz_liquid_Pa_m')
```

Under the probe's own scoring rule — *a probe that raises is scored PRESENT, never
RESOLVED* — the correct fix scores as three unfixed defects. The rule is right; it is the
calls that are stale. F-01's flux read (`getattr(p, "mass_flux_kg_m2s", None)` on
`BorePoint`) is the one part that would work, and it is satisfied.

**I did not edit the probe.** It is Cowork's instrument, and a builder who repairs the
thing that scores him has removed the check.

### 7.2 F-04's `RESOLVED` is not evidence — and this is the one that could have slipped through

F-04 reports `RESOLVED — crossed as APPLICABLE: none`. That reading is **vacuous**. Its
inner loop is:

```python
try:
    r = loop.two_phase_pressure_drop(**kw, liquid_regime=..., **IN_BASIS)
except Exception:
    continue
```

Those calls carry the same removed keywords, so **every one of the five raises TypeError
and is swallowed by `continue`.** Nothing was evaluated, so nothing leaked, so the probe
reports success. Executed directly:

```
F-04 probe inner call raises: TypeError: two_phase_pressure_drop() got an
unexpected keyword argument 'dp_dz_liquid_Pa_m'
```

All four probes are equally unusable; the difference is that three announce it and one
hides it behind a green result. The `except Exception: continue` inside the probe
contradicts the scoring rule stated in the probe's own docstring.

F-04 **is** genuinely fixed — but that is established by §5 and by two witnessed
mutations, not by this probe. Had F-04 not been fixed, this probe would have said the
same thing.

### 7.3 F-03's oracle was a literal that the F-01 fix removes

The probe records the limit as holding *"(`X` Pa vs single-phase 50.0000)"*. The 50.0000
came from `dp_dz_liquid_Pa_m=50.0 × length_m=1.0` — a caller-supplied gradient, which is
the object F-01 abolishes. The instruction the handoff gives in prose is the right one
(*test the limit against the Stage-1 single-phase `Δp` as the oracle rather than against a
literal*), and that is what §4 does; only the probe's embedded oracle is stale.

### 7.4 Everything else in the handoff is correct

All four findings reproduce on the pre-fix tree, all four are real, and the
characterisation of F-03 as *a missing test of correct behaviour, not a wrong number* is
right — I confirmed it by measurement before touching anything, and did not "fix" the
maths.

---

## 8. Witnessed-failure record (R2)

61 → **70**. **70/70 witnessed.** Reproduce with `python scripts/witness_s2_checks.py`.

New: pin the mass flux to one bore · pin both phase Reynolds numbers · stop recording the
flux on each sweep point · let a pure coolant be declared two-component · let horizontal
flow carry a static head · classify every flow as turbulent · put a floor under the
frictional multiplier · guard non-finite inputs with a sign test again · let quality leave
the unit interval.

**Three did not witness on the first run.** In each case the mutation was corrected, not
the test weakened:

- Two F-01 mutations pinned the hydraulics to **8 mm** — which is the bore the control
  test itself uses, so the control passed against a deliberately broken tree. Repinned.
- Pinning only the *length scale* in the Reynolds numbers does not break the monotone
  test, because the mass flux still varies with bore. Pinned outright.
- The F-04 sign-test mutation could not be witnessed at all. That one was **not** a bad
  mutation — it was a real defect in my fix, and it is fixed in the source (§5.1).

---

## 9. Suite delta from 784

```
6a97ad9:  784 passed,  3 xfailed,  0 failed,  0 skipped
7312a0c:  815 passed,  3 xfailed,  0 failed,  0 skipped
delta:    +31 passed
```

Oracle-freeze and the `v1.1.0` suites untouched. `ruff check .` still reports the same 8
pre-existing findings in `notebooks/`, left alone as instructed.

---

## 10. Definition of done

- [x] F-01: hydraulic state **derived** from bore; scalars removed from both signatures; `BorePoint` records the flux it used
- [x] F-02: regime computed; composition and orientation mutually consistency-checked at the shared boundary (C9)
- [x] F-03: `x → 0` limit tested against the **Stage-1 single-phase `Δp`** as oracle; the maths untouched; the O(√x) rate asserted
- [x] F-04: finiteness checked explicitly; quality bounded to `[0, 1]`; Director's spelling untouched
- [x] R1 per finding — ≥3 siblings plus a control in every case
- [x] R2 — harness grown 61 → **70**, all witnessed, three mutations corrected rather than tests weakened
- [x] Negative result re-run on the corrected sweep and **survives** (§6), with the control that identifies what drives it (§6.1)
- [x] Handoff defects reported (§7); the probe **not** edited
- [x] Suite green from **784** and grown; `ruff check src tests scripts` clean
- [x] No fabricated identifier anywhere in the diff
- [x] Branch pushed. `main` untouched, no tag, no release, nothing in the shared folder
- [ ] Sol review and Director disposition — not the builder's

---

## 11. Handback

New head **`7312a0c`**.

**The probe needs rebuilding before it can score this round** (§7). The three erroring
checks need their calls updated to the post-fix signatures; F-04 additionally needs its
`except Exception: continue` removed or narrowed, since as written it converts a signature
error into a passing result.

Carry-overs unchanged from last round: the round-2 ledger's `classification` is `null` on
all eight findings; `PACKET_LAYOUT.tsv` has no rows for files added since it was written;
**DEBTS D-11** (no condensation entry, S4) lives in the project home rather than the repo.
Newly relevant: closing the negative result of §6 needs the **Martinelli–Nelson (1948)**
single-component entry, which is S4 scope.
