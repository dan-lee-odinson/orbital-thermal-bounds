# Acceptance criteria — `OTB-G003` (S4, coupled two-phase steady-state solver)

**Written before the S4 code, against the rule established when the `OTB-G002` criteria were
rewritten:** *an acceptance criterion must name a state of the world that the artifact could
**fail** to reach.* "A label appears in the output" is a property of the code. "The reported
quantity changes when the independent variable changes" is a property of the model. Prefer the
second; where a criterion can only be administrative, say so and pair it with one that is not.

The `OTB-G002` criteria 1–10 remain in force for everything they already cover. What follows is
what S4 adds, and criteria **7** (a negative result is earned) and **8** (every new check has been
witnessed failing) from that set are load-bearing here rather than merely inherited.

**The central hazard this set exists to catch.** S4 delivers two runs of the same machinery: one
inside every adopted correlation's declared basis, and one on this project's own reference case
where three of four legs refuse. A demonstration mistaken for a result about the orbital loop is
the worst outcome available at this milestone. Criteria **S4-1** and **S4-2** exist to make that
mistake impossible rather than merely discouraged, and if they cannot distinguish the two runs
then they are the wrong criteria.

---

## The criteria

**S4-1. The two run kinds are distinguishable by type, not by convention.**
A reader holding only a result object — no filename, no comment, no surrounding prose — can
determine whether it describes this project's device or a machinery demonstration. The
distinction is carried by the type of the returned object and by a field on the object itself.
**Falsifiable by:** a single result type used for both runs; a distinction carried only in a
docstring, a variable name, a module name, or a printed comment; or any code path where the
demonstration's fluid and conditions can reach a reference-case result.

**S4-2. A demonstration's own output says it is not a statement about the device.**
The disclosure travels **in** the rendered output, not in a footnote or a caller's prose, and it
cannot be omitted, blanked, or overridden by a caller. **Falsifiable by:** a demonstration output
rendered without the disclosure; a constructor argument that suppresses it; or an empty
disclosure that still validates.

**S4-3. The solver couples — the legs are not independent calculations reported together.**
Changing a quantity that belongs to one leg moves the operating point reached by the others.
**Falsifiable by:** a converged operating point that is unchanged when the bore, the duty, or the
sink temperature moves; or an energy balance that closes without the pump term participating.

**S4-4. The operating point is a root of a characteristic, not an assertion.**
The coupled solution is the intersection of the loop's internal pressure-drop/flow-rate
characteristic with the external (pump) characteristic, and it satisfies both to a stated
tolerance. **Falsifiable by:** a reported operating point at which the two characteristics differ
by more than the stated tolerance, or a solver that reports success without evaluating the
residual.

**S4-5. Non-uniqueness is detected and reported, never silently selected.**
Where more than one steady solution satisfies the system, every root is reported and none is
chosen. **Falsifiable by:** a system with three intersections returning one operating point, or
returning a "preferred" root by any rule whatever.

**S4-6. The static Ledinegg guard fires on the sign of the internal-characteristic slope.**
At each operating point the guard evaluates `∂p/∂Ṁ` — the source's printed form — on the
**internal** characteristic and reports an excursion where it is negative. The guard is **static
only**; nothing in the artifact claims that the time-domain instability is modelled.
**Falsifiable by:** a negative-slope operating point reported as stable; a positive-slope one
reported unstable; or any claim, in code or output, that dynamic instability is modelled.

**S4-6a. A guard that cannot trigger says so, in the output.**
Where a guard is structurally unable to fire against the model it is attached to, every artifact
carrying the guard states that, in the rendered output rather than a footnote, and the statement
cannot be suppressed by a caller. **Falsifiable by:** an artifact describing the milestone as
carrying a static Ledinegg guard without the qualification.
*(Not hypothetical here: the pressure-drop boundary evaluates the frictional multiplier once per
call and scales it by length, so the moving boiling boundary is not represented and the internal
characteristic is monotone at every duty tried.)*

**S4-7. A refusal names its axis, its source, and what would lift it.**
Each blocked leg reports which declared axis refuses, the entry that refuses, and the state that
would unblock it. A leg that is *in* basis is not reported as blocked. **Falsifiable by:** a
blocked leg with no named axis; a refusal that cites no entry; or a leg reported blocked while its
correlation evaluates.

**S4-8. A policy refusal is distinguished from an absence of knowledge.**
Where a correlation exists whose declared basis admits some part of this project's operating
space, and it is not adopted, the refusal states that it is a **policy** refusal and names the
settled decision standing in the way. **Falsifiable by:** a refusal reported as "no correlation
exists" when the assessment found one whose declared basis admits part of the space.
*(This criterion is what makes the difference between "nothing covers this corner" and "something
covers part of this corner and was not adopted" a machine-checkable property rather than a matter
of wording. The two are materially different claims and only one of them is true.)*

**S4-9. An assessment applies every declared axis, and reports the overlap it computed.**
Where a correlation's declared validity box is a union over several fluids, the assessment reports
the sub-region supported by data for **this project's fluid**, separately from the declared box.
**Every** declared range is applied — a declared axis with no evaluator is an error, not an
omission — and what the assessment reports having applied is a record of what it did, not a copy
of what the entry declares. **Falsifiable by:** an assessment that reports a fluid as covered on
the strength of its appearance in a fluid list; a declared range that is silently skipped; or an
`applied_axes` that survives an axis being dropped.
*(A fluid list is not a coverage map. This is the failure shape recorded against a single
secondary tabulation of a validity box, applied to a source that is in hand.)*

**S4-9a. An input that decides the answer has no default.**
Where an assessment's verdict changes with a parameter — as it does with vapour quality, on which
two of the assessed candidate's declared axes depend — that parameter is required, and the value
used is reported alongside the result. **Falsifiable by:** a default that makes the reported
window an artifact of the default, or a reported window with no stated operating point.
*(Added after the first cut of S4-9 applied three of seven declared axes and assessed at an
assumed quality. The reported window was 2.2 mm too wide at the low end and the refusal was
classified as policy where the whole basis makes it knowledge.)*

**S4-10. A non-SI source is converted at the boundary and the conversion is tested.**
A source declared in non-SI units carries its conversion in the registry, the converted bounds are
what get enforced, and the conversion has its own test against an independently computed value.
Where the unit itself is ambiguous, both readings are recorded and the adopted one is named.
**Falsifiable by:** an enforced bound in the source's own units; a conversion with no test; or a
silently chosen definition where two exist.

**S4-11. An unresolved provenance travels with every result that depends on it.**
Any output carrying pump heat in the rejected load carries the unresolved-provenance disclosure
for the pump efficiency, and the value is unchanged from its pre-S4 setting. **Falsifiable by:** an
energy balance reporting pump heat without the disclosure; a changed efficiency value; or the
artifact resolving the question in either direction.

**S4-12. The energy balance closes on the boundary it names.**
Rejected load equals applied duty plus the pump heat that enters the fluid, on the stated control
boundary, to a stated tolerance. **Falsifiable by:** a balance that closes only when the pump term
is dropped, or a residual larger than the stated tolerance.

**S4-13. No ranked output.**
S4 emits no ranked value and no ordering of cases. The ranking-scope mechanism is left in place
for its later users, and is not exercised here. **Falsifiable by:** any S4 entry point returning a
rank, a score, or an ordering.

**S4-14. Every enforced bound is traceable to a page that was read.**
Each new registry bound cites its source and locator, and no bound is asserted from an automated
text extraction where a rendered page was available. **Falsifiable by:** an enforced number with no
locator, or a claim about a source that the rendered page contradicts.
*(Administrative in form. Paired with S4-9 and S4-10, which are not: those two fail on the numbers
rather than on the citation.)*

---

## What these criteria deliberately do **not** require

- **They do not require the reference case to produce a number.** Three of the four legs decline,
  and a criterion demanding convergence on the reference case would be a criterion demanding that
  a refusal be weakened. S4-7 requires the refusal to be *informative*; nothing requires it to go
  away.
- **They do not require the assessed pressure-drop correlation to be adopted or implemented.**
  S4-8 and S4-9 constrain what the assessment must *report*. Rank-eligibility is a settled
  decision's to grant.
- **They do not treat dynamic instability as in scope.** S4-6 constrains the static guard and
  explicitly makes a claim of dynamic modelling a falsification.
