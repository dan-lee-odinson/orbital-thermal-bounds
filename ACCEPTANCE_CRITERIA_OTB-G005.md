# Acceptance criteria — `OTB-G005` (S5, two-phase architecture cases)

**Written before the S5 code, against the rule the `OTB-G002` rewrite established and the S4
criteria carried:** *an acceptance criterion must name a state of the world that the artifact could
**fail** to reach.* "A label appears in the output" is a property of the code. "The reported
quantity changes when the independent variable changes" is a property of the model. Prefer the
second; where a criterion can only be administrative, say so and pair it with one that is not.

The `OTB-G002` criteria 1–10 and the S4 criteria **S4-1 … S4-14** remain in force for everything
they already cover. `OTB-G002` **7** (a negative result is earned) and **8** (every new check has
been witnessed failing) are load-bearing here rather than merely inherited, and **S4-3** is
load-bearing in a way no earlier milestone made it: see S5-12.

S5's deliverable, from the S0 scoping note §8: *"Two-phase architecture cases — which coolants are
rank-eligible (ammonia reference; water; others source-gated)."* Review level: spot-check (a + c).

**Three inherited obligations are discharged or carried here, and their identifiers are stated
once, precisely, because two of them were transposed in the drafting brief and the correction is
the Director's:**

| what | identifier | where |
|---|---|---|
| a 1-g-derived CHF correlation may not ground a microgravity-valid ranking | **Director ruling D6** (the mechanism) with **debt D-7** (the unvalidated claim) | S5-4 … S5-7 |
| the Steiner–Taborek (1992) evaluation, which **retires at S5** | **debt D-6** — *"No ammonia-valid heat-transfer correlation is adopted"* | S5-8 … S5-11 |
| the unbuilt S4 coupling, whose gate is **S8** | **debt D-14** | S5-12, S5-13 |

`D6` without the hyphen is a **settled decision**, not a debt: it is the gravity axis in
`registry/applicability.py` — *"the default is standard gravity because the database is
terrestrial."* `D-6` and `D-7` are **debt-register** entries and are easy to swap, so the
subject, not the number, is what each criterion below is written against.

**The central hazard this set exists to catch.** S5 decides **eligibility**; S6 emits the
**rankings**. Everything S5 records is consumed later by a milestone that publishes ordered
results, and the project's standing position is that no ranking is microgravity-validated. The
worst outcome available at this milestone is an eligibility record that is *true when written and
lossy when read* — one that lets S6 emit a CHF-dependent ordering with the gravity basis dropped
somewhere between the two. Criteria **S5-4** through **S5-6** exist to make that loss impossible
rather than merely discouraged. If they cannot stop a rank from being emitted without its basis,
they are the wrong criteria.

---

## The criteria

### Rank-eligibility is a computed property

**S5-1. Eligibility is derived from the adopted correlation set, not declared.**
Whether a fluid is rank-eligible is computed from the applicability of the correlations actually
adopted for each leg it needs. **Falsifiable by:** a hard-coded eligible-fluids list; an
eligibility that does not change when a correlation's declared basis, adoption status, or
applicability axis changes; or an eligibility that can be set by a caller.
*(This is S4-9's shape one level out — a fluid list is not a coverage map, and an eligibility list
is not an eligibility rule.)*

**S5-2. Eligibility is reported per leg, and partial eligibility is never summarised into a
verdict.** A fluid eligible on the pressure-drop leg and refused on the heat-transfer leg is
reported as exactly that. **Falsifiable by:** a single boolean covering several legs; an
eligibility that averages, scores, or otherwise collapses per-leg outcomes; or a fluid reported
eligible while a leg the ranking consumes refuses it.

**S5-3. S5 emits no ordering.**
S5 emits eligibility and the evidence for it. It does not rank, score, or order coolants — that is
S6, and it is a MAJOR gate with its own review. **Falsifiable by:** any S5 entry point returning a
rank, a score, an ordering, or a "preferred" or "best" coolant by any rule whatever.
*(S4-13 said the same of S4. It is repeated rather than inherited because S5 is the first
milestone whose subject matter makes ranking the obvious next line of code.)*

### D6 / D-7 — a CHF-dependent ranking cannot claim microgravity validity

**S5-4. An eligibility record that depends on CHF carries the gravity basis of the CHF correlation
that produced it, and cannot be constructed without one.** The basis travels as a field on the
record, populated from the adopted correlation's `reference_gravity_m_s2` and `gravity_basis`, not
from a caller's argument. **Falsifiable by:** a CHF-dependent eligibility record constructible with
an absent, empty, or defaulted gravity basis; a basis suppliable or overridable by a caller; or a
basis carried only in a docstring, a comment, a variable name, or rendered prose.

**S5-5. The basis survives the hand-off to the consumer that ranks.**
Whatever S5 hands forward is such that a downstream ranking cannot emit a CHF-dependent ordering
having lost the gravity basis — the record cannot be reduced to a bare eligibility flag without the
reduction failing. **Falsifiable by:** any projection, serialisation, export, or convenience
accessor that yields CHF-dependent eligibility without its basis and still validates.
*(This is the criterion that actually discharges D6's obligation at S5. S5-4 makes the basis
present; only S5-5 makes it non-droppable, and the obligation is about what a **later** milestone
can claim.)*

**S5-6. Evaluating CHF-dependent eligibility away from the correlation's reference gravity
de-ranks; it does not return a number with a caveat.** The existing `Axis.ORIENTATION` /
`Consequence.DE_RANK` mechanism is the enforcement, extended to the eligibility path rather than
re-implemented beside it. **Falsifiable by:** a CHF-dependent eligibility returned as `True` at a
gravity outside `reference_gravity_m_s2 ± gravity_rel_tol`; a caveat string substituted for the
de-rank; or a second, parallel gravity check that can disagree with the registry's.

**S5-7. No S5 output asserts a *direction* for CHF error in microgravity.**
D-7's own refinement is explicit: the "known direction" is Hammer (2021) and is about the
**heat-transfer coefficient**; for **CHF**, Kharangate, Konishi & Mudawar (2015) place microgravity
predictions *between* the Earth-gravity orientation extremes, so the sign depends on which
orientation the 1-g correlation was taken at. **Falsifiable by:** any S5 output, docstring, ledger
entry or doc claiming that 1-g CHF correlations over-predict, under-predict, are conservative, or
are non-conservative in microgravity; or any text that carries the HTC direction across to CHF.
*(This criterion can only be falsified by text, which normally makes it administrative. It is not:
the conflation it forbids is already written into D-7's own title, and the debt says so. A wrong
claim here is the most likely single error at this milestone.)*

### D-6 — the Steiner–Taborek (1992) evaluation

**S5-8. The evaluation reaches a disposition, and the disposition names the number it acted on.**
Adopt, adopt-with-scope, or decline. The three recorded ammonia measurements disagree — VDI/Steiner
**41.9 %**, Gungor–Winterton **37.2 %**, Kattan–Thome–Favrat **19.5 %** (Zürcher; Táboas 2006
separately calls Steiner–Taborek the only correlation that predicts ammonia). **Falsifiable by:** an
evaluation that returns "assessed" with no disposition; a disposition citing no measurement; or a
disposition that cites the 19.5 % figure as support for adopting Steiner–Taborek.

**S5-9. A better score does not by itself make a correlation adoptable, and Kattan–Thome–Favrat is
the named case.** KTF scores best *because* it resolves gravitational flow-pattern regimes — the
mechanism that does not exist in orbit (D-6's closing line, and D-7). Any preference expressed on
accuracy alone, without that being confronted in the record, is a falsification. **Falsifiable by:**
an adoption or preference for KTF resting on the 19.5 % figure with no recorded treatment of its
gravity dependence; or a comparison table that ranks the three by deviation and stops there.

**S5-10. Whichever way the evaluation goes, ammonia's eligibility changes measurably or is
measurably unchanged, and the outcome is attributable.** If Steiner–Taborek is adopted, ammonia's
per-leg eligibility differs from its pre-S5 state and the difference is traceable to the adoption.
If it is declined, ammonia remains de-ranked through GW86 and the decline is reported as a
**policy** refusal or an **absence of knowledge** per S4-8 — never as "no correlation exists" when
Steiner–Taborek does. **Falsifiable by:** an adoption that leaves eligibility bit-identical; a
decline reported as absence; or an eligibility change that cannot be attributed to a named
adoption decision.

**S5-11. D-6 retires on a recorded disposition, not on the evaluation having been performed.**
The debt says *"Retires at S5"*; performing an evaluation and leaving the debt open is a
different state from retiring it, and the artifact must be able to show which one obtains.
**Falsifiable by:** a retirement claimed with no disposition recorded, or a disposition recorded
with the debt left open and nothing saying so.
*(Administrative in form. Paired with S5-8 and S5-10, which are not: those two fail on the
disposition's content and on the eligibility numbers rather than on the bookkeeping.)*

### D-14 — the unbuilt S4 coupling

**S5-12. S5 does not weaken S4-3, and does not imply the coupling exists.**
S4-3 fails measurably: sink temperatures 150 K, 250 K and 320 K all return the identical
`0.043654969267 kg/s` root, and the artifact says so by D28. **Falsifiable by:** any S5 output that
presents a coupled result while that remains true; any S5 text asserting the S0 coupled-solver
milestone is discharged; or **any edit to S4-3's wording, its falsifier, or its sink-temperature
witness that makes it pass without the coupling being built.**
*(The third clause is the one that matters. The cheapest way to discharge D-14 is to reword the
criterion it fails, and that would be a criterion weakened to fit an artifact — the inverse of what
this file is for.)*

**S5-13. If S5 builds the coupling, the discharge is measured on S4-3's own falsifier.**
D-14 permits S5, S6 or S7 to build it early and requires none of them to. If S5 does, the
retirement condition is met by re-running S4-3's stated falsifier — three sink temperatures
producing three roots differing by more than the solver's own convergence tolerance — not by
assertion. **Falsifiable by:** a claimed discharge with no re-run; roots differing by less than the
solver tolerance reported as a discharge; or a discharge claimed on a criterion other than S4-3.
*(Conditional by construction. If S5 does not build the coupling this criterion is vacuous, and
S5-12 is the one that binds — which is the correct division, because D-14's gate is S8, not this
milestone.)*

### Traceability

**S5-14. Every new enforced bound and every adopted source is traceable to a page that was read.**
Each new registry bound cites its source and locator; no bound is asserted from automated text
extraction where a rendered page was available; a non-SI source is converted at the boundary and
the conversion has its own test against an independently computed value. **Falsifiable by:** an
enforced number with no locator; a claim a rendered page contradicts; an enforced bound in the
source's own units; or a conversion with no test.
*(Administrative in form, and inherited from S4-10 and S4-14 rather than new. Paired with S5-8 and
S5-10, which fail on numbers.)*

---

## What these criteria deliberately do **not** require

- **They do not require any coolant to be rank-eligible.** If the adopted correlation set admits
  none of the candidate fluids on every leg a ranking consumes, that is a result — `OTB-G002`
  criterion 7, a negative result is earned — and a criterion demanding eligibility would be a
  criterion demanding that a refusal be weakened. S5-1 and S5-2 require the eligibility rule to be
  *informative*; nothing requires it to say yes.
- **They do not require Steiner–Taborek to be adopted.** D-6 scopes an **evaluation** at S5, and
  the recorded evidence is genuinely mixed — 41.9 % against GW87's 37.2 %, alongside Táboas calling
  it the only correlation that predicts ammonia. S5-8 constrains what the evaluation must
  *conclude and cite*; declining is an available conclusion and S5-10 covers that branch.
- **They do not require the S4 coupling to be built.** D-14's gate is **S8**, expressed as a
  pass-condition rather than an owner assignment. S5-13 binds only if S5 chooses to build it.
- **They do not treat microgravity validation as in scope.** No S5 output may claim it, and S5-7
  additionally forbids claiming a *direction* for CHF error — including a claim that would flatter
  the artifact by calling it conservative.
- **They do not extend to ranked output.** S6 owns rankings and the §7 ranking-scope limitation on
  every one of them. S5-5 exists precisely so that S6 cannot lose what S5 established.
