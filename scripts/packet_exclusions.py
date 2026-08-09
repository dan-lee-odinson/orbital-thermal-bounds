"""C10 at PACKAGING time: a member addressed to the Director does not go in a packet.

**OTB-G003 F-08.** C10 forbids Director-addressed and process-addressed text in
committed files. It is a **writing-time** rule, and at `OTB-G001-FIXES` F-05 the
Director kept that half and declined the packaging-time half. This module is the half
he has now accepted, on a new fact: `OTB-G003_S4_SCOPE_PROPOSAL.md` shipped inside the
`OTB-G003` packet. Its first line is *"S4 - scope proposal for Director approval"*, it
says *"Nothing is built until this is approved"*, its section 8 asks the Director eleven
decisions -- **and it cites C10's own prohibition.** The document invoking the rule
breaks it, which is a different animal from a report committed before the rule existed.

**The historical files stay committed and this module does not touch them.** Rewriting
committed history to satisfy a rule written afterwards would be C2's reasoning violated
one level out: the record is the record, and a packet is a separate act of selection.

**D30 widened the rule.** C10 said of itself that *"no rule governs the existing text"* and
that F-05's situation should be expected to recur at the next freeze. It recurred, and the
Director ruled the half he had declined: a committed file addressed to him does not enter a
packet **whenever it was written.** The repository is still not edited. Four historical
reports joined the list under that ruling; the record they are part of is untouched.

The list is **enumerated, not pattern-matched**. A regex over "Director" or "approval"
would sweep in registry notes that legitimately cite a ruling -- ``two_phase.py`` says
"Director ruling D9" dozens of times as provenance -- and an exclusion that fires on
provenance would delete the artifact to protect the packet. Every entry below was read
and is named, with the reason it qualifies.

**And enumeration alone is not sufficient, which D30 proved.** The sentence above certifies
the ENTRIES. It cannot certify the COVERAGE -- and when the rule widened, four members that
qualified were not on the list. C9 forbids repairing named instances while leaving the rule
permissive. So :func:`discover_director_addressed` stands **beside** the enumeration rather
than replacing it: it re-derives candidates from the member text, and a member carrying a
marker that is neither enumerated nor on the small reasoned :data:`QUOTATION_ALLOWLIST`
fails the build. The list stays the authority on *what is dropped and why*; discovery is the
authority on *whether the list is complete*. Neither can silently cover for the other -- the
regression that proves that removes an entry from the list and requires discovery to catch it
anyway.

**This module reads nothing.** Every function is pure over inputs the packager already holds.
``os``, ``subprocess`` and ``shutil`` are absent by regression: a review packet is a
reconstruction with no ``.git`` and no ``git``, and tests that read a repository died inside
one at the round-2 freeze.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from typing import NamedTuple

#: Names that must not enter a review packet, each with the reason it qualifies.
#:
#: **These come from two different places and the filter has to run after they meet.**
#: The three reports are tracked repository files; ``OTB-G003_S4_SCOPE_PROPOSAL.md`` is
#: **not tracked at all** -- it is a gate-record document added at packaging time. A
#: filter over ``git ls-files`` would therefore never see the sharpest case on the
#: list. The filter runs over the ASSEMBLED member set, and
#: :func:`unknown_exclusions` is given that same set so a stale entry is caught rather
#: than silently protecting nothing.
DIRECTOR_ADDRESSED_MEMBERS: dict[str, str] = {
    "OTB-G001_BUILD_REPORT.md": (
        "a build report addressed to the Director: it reports completion of work he "
        "commissioned and asks him to disposition it."
    ),
    "OTB-G001_FIXES_REPORT.md": (
        "same shape -- a fixes report written to the Director, discharging findings he "
        "dispositioned."
    ),
    "OTB-G001-FIXES_ROUND2_REPORT.md": (
        "same shape again -- a round-2 fixes report written to the Director, reporting "
        "what was built against findings he had dispositioned and inviting the next "
        "disposition."
    ),
    "OTB-G003_S4_SCOPE_PROPOSAL.md": (
        "the sharpest case, and NOT a tracked repository file -- it enters at packaging "
        "time: 'scope proposal for Director approval', 'Nothing is built until this is "
        "approved', an eleven-decision table addressed to him -- and it cites C10 while "
        "breaking it."
    ),
    # --- added under D30: committed before the rule, excluded by it now -------------
    "OTB-G001-FIXES_PACKAGING_REPORT.md": (
        "line 144 puts a builder judgment to him for decision: 'Whether METHOD's packet "
        "checker should accept an honest `xfail` is a Director question about the tool, "
        "not something a build can resolve.' That is F-05's second cited shape -- a "
        "passage asking the Director to rule."
    ),
    "OTB-G002_BUILD_REPORT.md": (
        "line 266 is an unchecked checklist item naming his action -- '- [ ] Sol review "
        "and Director disposition' -- which is F-05's third cited shape: a report that "
        "tracks the Director's next step as an open box of its own."
    ),
    "OTB-G002_FIXES_REPORT.md": (
        "line 208 carries the same unchecked checklist item naming his action, in a "
        "report whose subject is work he dispositioned."
    ),
    "OTB-G002_FINDINGS_REPORT.md": (
        "line 343 carries the same unchecked checklist item naming his action, closing a "
        "findings report addressed to the review cycle he owns."
    ),
    # --- added under D38: surfaced by the D37 vocabulary, ruled member by member -----
    # Each reason is the LINE that makes the member qualify, not a summary of it.
    #
    # **Three of the five D38 named are here. Two are not, and that is reported rather
    # than quietly done**: excluding `verification/review-records/2026-07-25-s2-two-phase-
    # evaporator.md` or `src/orbital_thermal/visual_api.py` breaks the packet's own suite,
    # measured by reconstructing a tree without each. That is the defect `verify_packet.py`
    # exists to catch and the one this test module already carries a scar from.
    "docs/development/phase-b-stage-2-scoping-note.md": (
        "line 7 routes the note to him before work may start: 'for director review; no S1 "
        "code proceeds until this note is approved'. A scoping note that gates the build "
        "on his approval is addressed to him, not to the reviewer."
    ),
    "verification/mastery-ledger/index.md": (
        "line 76 holds a ledger entry open on his action: 'Two items need **director "
        "disposition** before this entry'. The ledger is a record for the reviewer; a line "
        "inside it waiting on the Director is not."
    ),
    "external_models/biswas_suncatcher/author_clarifications.md": (
        "line 43 conditions publication on him: 'Any public-documentation summary of these "
        "values requires the project director's approval'. A standing request for his "
        "approval, sitting in a vendored-source clarification file."
    ),
    # --- added under D44: mastery-ledger entries carrying a TASK assigned to him -----
    #
    # The D43 marker surfaced twelve members. The Director walked all twenty-two lines
    # and split them on the distinction the text actually carries, not on the file they
    # sit in. Three shapes:
    #
    #   A  the empty-field marker, in eleven entries, under the heading
    #      "## Explanation in the director's own words" -- naming a field, not asking
    #      for anything. That is the D41 `STATE.md` case.
    #   B  a task assigned to him WITH CONTENT: a specific explanation he owes, naming
    #      the physics it must cover.
    #   C  `template.md`'s guidance to whoever fills a new entry, assigning nobody
    #      anything.
    #
    # The ten below carry A **and** B in the same file. An exclusion is per-member, so
    # for these ten it was binary, and B decides it. The reason for each is its own
    # B-line verbatim: a name with no evidence is what the enumeration exists not to be.
    "verification/mastery-ledger/entries/architecture-cases.md": (
        "line 79 assigns him a specific write-up: '`TODO (director)`: plain-language "
        "explanation of the case-space classification and the modeled-component-mass "
        "limitation.' That is a task he owes, not a field naming him."
    ),
    "verification/mastery-ledger/entries/beta-angle-albedo-model.md": (
        "line 81 assigns him a specific write-up: '`TODO (director)`: plain-language "
        "explanation of the sub-point albedo factor and its beta = 90 limitation.'"
    ),
    "verification/mastery-ledger/entries/coupled-steady-state-solution.md": (
        "line 79 assigns him a specific write-up: '`TODO (director)`: plain-language "
        "explanation of the coupled solve and the heat-injection rule (chip heat through "
        "R1/R2; pump heat into R3).'"
    ),
    "verification/mastery-ledger/entries/earth-view-factors.md": (
        "line 99 assigns him a specific write-up: '`TODO (director)`: plain-language "
        "explanation of the tilted-plate-to-sphere geometry and why the edge-on heuristic "
        "floor (~0.021) is a ~12x underestimate of the exact ~0.258.'"
    ),
    "verification/mastery-ledger/entries/emitting-face-convention.md": (
        "line 84 assigns him a specific write-up: '`TODO (director)`: plain-language "
        "explanation of why emitting area, not planform, is correct, and when the "
        "equal-sink condition holds.'"
    ),
    "verification/mastery-ledger/entries/radiative-equilibrium-and-net-rejection.md": (
        "line 80 assigns him a write-up in his own words: '`TODO (director)`: "
        "plain-language explanation.' Terser than its nine siblings and the same kind of "
        "thing -- an open task with his name on it, not a field naming him."
    ),
    "verification/mastery-ledger/entries/radiator-attitude-and-sun-shielding.md": (
        "line 87 assigns him a specific write-up: '`TODO (director)`: plain-language "
        "statement of the attitude/shielding assumption and why direct-solar omission is "
        "acceptable for the intended cold-side screening.'"
    ),
    "verification/mastery-ledger/entries/single-phase-pumped-loop.md": (
        "line 75 assigns him a specific write-up: '`TODO (director)`: plain-language "
        "explanation of the loop hydraulics/thermics and the hydraulic-into-fluid "
        "pump-heat convention.'"
    ),
    "verification/mastery-ledger/entries/solid-thermal-network.md": (
        "line 82 assigns him a specific write-up: '`TODO (director)`: plain-language "
        "explanation of spreading resistance and the isothermal vs convective base.'"
    ),
    "verification/mastery-ledger/entries/spectral-separation-of-loads.md": (
        "line 80 assigns him a specific write-up: '`TODO (director)`: plain-language "
        "explanation of why two bands (and Kirchhoff) are needed.'"
    ),
}

#: The marker shapes, each traceable to what `OTB-G002` F-05 was actually raised on.
#:
#: **Deliberately narrow.** The rejected alternative is a sweep for ``Director``, which
#: this module's own docstring explains would fire on provenance and delete the artifact
#: to protect the packet. These fire on a member *addressing* him -- asking him to rule,
#: naming him in an open checklist item, or waiting on him -- not on one *citing* him.
#: Measured on the assembled member set: ten members carry a marker, seven are enumerated
#: exclusions and three are quotation (see :data:`QUOTATION_ALLOWLIST`).
#: **D37/F-04: matched case-INSENSITIVELY, and every pattern carries word boundaries.**
#:
#: The vocabulary was case-sensitive, so ``for Dan`` matched and ``for dan`` did not. That
#: alone was not the whole defect and it is worth stating precisely, because the fix was
#: nearly scoped to it: the review record that escaped uses *none* of the shapes below in
#: any case. ``need a director ruling``, ``pending director disposition``,
#: ``Findings requiring director disposition``, ``for director attention`` and
#: ``is a director decision`` were measured to miss as-is, capitalised AND
#: case-insensitively. Case-blindness was necessary; it was not sufficient.
#:
#: **Word boundaries went on BEFORE the case flag, and that ordering matters.** Under
#: ``re.I`` the bare ``for Dan`` matches "waiting **for dan**ger to pass" and ``awaiting
#: (?:Dan|...)`` matches "**awaiting dan**gerous weather" -- both measured. Trading a
#: false negative for a false positive would have been a worse rule, not a fixed one.
#:
#: The five shapes added below all require a REQUESTING verb or a pending-state word beside
#: the noun. That is what keeps the standing control intact: ``registry/two_phase.py`` cites
#: "Director ruling D9" **28 times** as provenance and none of them fires.
DIRECTOR_ADDRESSED_MARKERS: dict[str, str] = {
    "for-dan": r"\bfor Dan\b",
    "director-question": r"\bis a Director question\b",
    # D31: widened. The old form was ``asks (?:him|the Director) to`` and it missed
    # ``asks Dan to rule`` -- the name is recognised by ``for-dan`` and was not
    # recognised here, so which noun the sentence used decided whether it fired.
    "asks-him-to": r"\basks (?:him|Dan|the Director) to\b",
    # D31: NEW, and it exists because the marker written FROM a case did not match
    # that case's own words. The docstring above cites the scope proposal's
    # "section 8 asks the Director eleven decisions" as the most flagrant example on
    # the list -- and no marker fired on it, because the verb is not followed by "to".
    # That is `_COUPLING_SUBJECT` wanting "solved together" while the module said
    # "solves them together", one level out.
    # ``s?`` before the boundary, not a bare ``\b``: the boundary added for D37 broke
    # BOTH cases this marker was written from -- "eleven decision**s**" and "asks Dan for
    # ruling**s**" -- because ``\b`` fails between "decision" and its plural. The two D31
    # regressions caught it immediately, which is the only reason it is not shipping.
    "asks-him-for-a-decision": (
        r"\basks (?:him|Dan|the Director) [^.\n]{0,40}?(?:decision|ruling|approval)s?\b"
    ),
    "unchecked-checklist": r"^[ \t]*-[ \t]*\[ \].*\bDirector\b",
    "director-must-rule": (
        r"\bDirector (?:must|needs to|should) (?:rule|decide|choose|disposition)\b"
    ),
    "awaiting": r"\bawaiting (?:Dan|the Director)\b",
    # --- D37/F-04: the shapes the escaped review record actually uses ---------------
    # Each requires a requesting verb or a pending-state word next to the noun, which is
    # the line between a member ASKING him for something and one CITING what he decided.
    # Every trailing noun takes ``s?``: `\b` alone fails between a noun and its plural,
    # which is how the D37 boundary pass briefly broke two markers that had worked.
    "pending-his-action": (
        r"\bpending (?:the )?director(?:'s)? "
        r"(?:disposition|review|ruling|decision|judg[e]?ment|approval)s?\b"
    ),
    "needs-his-action": (
        r"\b(?:need|needs|needed|requir\w+|await\w+)\b[^.\n]{0,20}?\b(?:a |the )?"
        r"director(?:'s)? "
        r"(?:disposition|ruling|decision|judg[e]?ment|attention|review|approval)s?\b"
    ),
    "for-his-attention": (
        r"\bfor (?:the )?director(?:'s)? "
        r"(?:attention|approval|disposition|review|judg[e]?ment|decision)s?\b"
    ),
    # ``question`` is deliberately NOT in this alternation: ``director-question`` already
    # covers "is a Director question", and now that both are case-blind the two would be
    # redundant. A marker that only ever fires where another already has is not a check.
    "is-his-call": r"\bis a director (?:decision|call|judg[e]?ment)s?\b",
    "his-call-to-make": (
        r"\b(?:judg[e]?ment|decision|call|question|choice)\b[^.\n]{0,14}?"
        r"\bfor (?:the )?director\b"
    ),
    # --- D43/F-04: a shape no marker has ever matched -------------------------------
    # An open task assigned to him, not a citation of a settled ruling. Twenty-two such
    # lines have shipped in every packet since `OTB-G001` and none of the eleven markers
    # above sees any of them: they carry no requesting verb and no pending-state word,
    # only an imperative label.
    #
    # Bounded by the closing parenthesis, which is what stops it reading `TODO (directory)`
    # or `TODO (directive)` -- `director` must be followed by optional space and then `)`.
    # The `re.I` change taught that a case-blind pattern without a bound trades a false
    # negative for a false positive, so the bound is regressed rather than assumed.
    "todo-for-him": r"TODO\s*\(\s*director\s*\)",
}

#: ``re.I`` is the D37 fix; ``re.M`` is what the checklist marker's ``^`` needs.
_COMPILED_MARKERS = {
    label: re.compile(pattern, re.I | re.M)
    for label, pattern in DIRECTOR_ADDRESSED_MARKERS.items()
}

#: Members whose FUNCTION is to quote the Director, so a marker in them is the artifact
#: working. Each was measured to actually carry a marker -- see :func:`inert_allowlist`.
#:
#: **This list is short on purpose, and shorter than the one proposed to me.** Eleven
#: documents were suggested; eight of them carry no marker at all, so entries for them
#: would suppress nothing while looking like protection -- the same defect
#: :func:`unknown_exclusions` exists to catch, one level out. The verification certificate
#: is among the eight, which also spares this list an entry whose filename changes at
#: every freeze and would go stale by construction.
class _Exemption(NamedTuple):
    """An allowlist entry: prose for a human, and a predicate the build actually trusts.

    **D37/F-04.** ``STATE.md``'s reason ended *"and its value here is 'none'"* while the
    shipped file carried ``F-01`` -- an exemption that read as reasoned and was resting on
    a fact that had stopped being true. The prose could not notice, because prose does not
    execute.

    So every entry now carries ``holds(text) -> bool``, checked against the member's own
    text at packaging time by :func:`false_premises`. The prose stays as the human-readable
    reason; the predicate is the part that fails the build.

    **The predicate asserts the CONCRETE thing the reason cites**, never merely "this member
    contains a marker" -- that is true by construction for every entry (:func:`inert_allowlist`
    already requires it), so it would pass always and tell nobody anything. A check whose
    passing carries no information is the shape this project counts.
    """

    reason: str
    premise: str
    holds: Callable[[str], bool]


#: The Director-addressed sentences the registry module is known to carry.
#:
#: **Keyed on the sentences, never on their line numbers.** A line number moves the instant
#: anything above it changes, so a premise keyed to one would go false on an unrelated edit
#: -- a false alarm that trains people to ignore the real one, which is the hard-coded-commit
#: shape one level out. A regression inserts blank lines above and requires the premise to
#: survive.
#:
#: **There are TWO, and the ruling was written believing there was one.** The second, at
#: line 396 -- *"it is a finding for director disposition, not a defect this build is
#: authorised to resolve"* -- was invisible to the evidence the ruling rests on, because
#: that scan reports the first match per marker and both lines fire the same marker. So the
#: premise "its only Director-addressed line is the one at 296" was false before it was
#: written. Both are enumerated here with their text; a THIRD still fails the build, which
#: is the falsifiability the exemption was granted for.
_REGISTRY_KNOWN_ADDRESSES = (
    "is a registry-level question for director disposition, not for this build",
    "it is a finding for director disposition, not a defect this",
)

#: `visual_api.py`'s single address: a standing documentation-policy statement.
_VISUAL_API_KNOWN_ADDRESSES = (
    "independent external validation. Public documentation requires project-director approval",
)

#: The S2 review record's **seven** addresses -- the member that escaped every sweep.
#:
#: **Seven, not five.** ``discover_director_addressed`` uses ``rx.search`` -- one match per
#: marker per member -- so lines 27 and 217 were invisible: each fires a marker another
#: line had already fired. A premise built from that view would have been false on
#: arrival, exactly as D38's was one member over. These come from ``finditer``.
#:
#: **Each fragment is LINE-distinctive, not the marker's own wording**, and that is not a
#: stylistic preference. The first draft keyed line 178 on ``is a director decision`` --
#: the marker phrase itself -- and a new eighth address using those same words passed the
#: check. A key that a fresh instance of the thing satisfies is not a key. Re-keyed with
#: per-line context and attacked with eight different eighth-addresses, five of them
#: deliberately reusing known wording: all eight are caught.
_S2_RECORD_KNOWN_ADDRESSES = (
    "OPEN pending director disposition + Sol cross-model review. No cross-model",
    "**Disposition:** **pending director review.** `main` untouched",
    "**Judgment call for the director.** §2 of the handoff bars",
    "## Findings requiring director disposition",
    "**Knock-on for director attention:** this also puts the registry",
    "Registry-level correction is a director decision, not a builder one",
    "Requires: (i) director disposition of **F1** and **F2**",
)


#: Vocabulary every Director-addressed line shares, so a key made only of it is a key a
#: DIFFERENT new address could satisfy. Sol's F-03 sentence -- *"it is a finding for
#: director disposition, not a repair this build owns"* -- contains the old registry key
#: verbatim while being about an entirely different subject.
_PROCESS_WORDS = frozenset(
    """director directors dan disposition dispositions dispositioned ruling rulings rule
    rules decision decisions decide judgment judgement call calls question questions
    approval approve attention review reviews closure closed close pending awaiting await
    awaits need needs needed requires require required requiring finding findings builder
    build open status asks ask sol cross model raised record records
    todo""".split()
)
# ``todo`` is marker vocabulary, added at D44. Without it the screen scored
# ``TODO (director)`` as carrying a subject token and passed it -- the exact containment
# key D44 identifies as instance twenty-one. The screen had a hole precisely at the
# shape the round was about, and the regression below is what found it.
_FUNCTION_WORDS = frozenset(
    """a an the is are was it its of for to and or not this that these those his her
    their one two three in on at by with from as be been before after than so but if each
    every all any no yes still again here there what which who whom i we you they he
    """.split()
)

#: Keys the subject-token screen cannot judge, each with the reason. Checked, not waived:
#: :func:`weak_keys` reports an entry here that does NOT fail the screen, so an exemption
#: that has stopped being needed cannot sit here looking like a decision.
_SCREEN_EXEMPT: dict[str, str] = {
    "## Findings requiring director disposition": (
        "a markdown SECTION HEADING, whose words are necessarily the generic ones -- a "
        "heading naming the section's subject would not be this section. The member-"
        "specific context is the '## ' prefix and the fact that a heading is not a "
        "sentence: a new address about a different subject is prose, and prose does not "
        "carry a level-two heading marker. The screen tokenises words and cannot see that."
    ),
}


def subject_tokens(fragment: str) -> list[str]:
    """Words in a key that name its own subject rather than the shared process."""
    return [
        token
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]*", fragment.lower())
        if token not in _PROCESS_WORDS and token not in _FUNCTION_WORDS
    ]


def weak_keys(known: tuple[str, ...]) -> list[tuple[str, str]]:
    """Keys a genuinely NEW Director-addressed line could plausibly satisfy. **A floor.**

    D43/F-03. Sol found a shipped key that a plausible new sentence about a different
    subject contains verbatim, and Cowork's mechanical probe could not: it excluded any
    probe containing a key fragment, which is exactly what a realistic reuse contains.
    The candidate replacement -- residual length after stripping the marker match --
    separated the D40 pair perfectly and left Sol's key at fifteen characters, above any
    threshold that would not condemn half the shipped set. It measured LENGTH; the
    property is SUBJECT.

    This screens on subject instead: a key containing no token outside the shared process
    vocabulary is one a different address could reuse. It separates the D40 pair AND
    catches Sol's key, which the length test could not.

    **It is a floor and not a certificate, and the difference matters.** It passes keys a
    reading still flags -- a standing policy sentence is lexically specific and
    semantically reusable, so ``Public documentation requires project-director approval``
    scores well while applying to any artifact. Passing this means "not obviously weak",
    never "strong". The twenty-one-key reading stays the authority; this catches the one
    shape a reading might tire of.
    """
    flagged = []
    for fragment in known:
        # An Exact key is matched by EQUALITY, so the question this screen asks -- could
        # a NEW address about a different subject satisfy this key? -- is already
        # answered no by the matching rule. Only a byte-identical line satisfies it, and
        # a byte-identical empty-field placeholder is not a new address (D41, D44).
        # Screening it on vocabulary would condemn the one key shape that cannot be weak.
        if isinstance(fragment, Exact):
            continue
        if subject_tokens(fragment):
            continue
        if fragment in _SCREEN_EXEMPT:
            continue
        flagged.append((fragment, "no token outside the shared process vocabulary"))
    return flagged


def inert_screen_exemptions(known: tuple[str, ...]) -> list[str]:
    """Screen exemptions that are not exempting anything -- dead weight, reported."""
    texts = {_fragment_text(f) for f in known}
    return sorted(
        fragment
        for fragment in _SCREEN_EXEMPT
        if fragment in texts and subject_tokens(fragment)
    )


class Exact(NamedTuple):
    """A key matched by EQUALITY on the stripped line, not by containment.

    **D44, and it is the difference between a key and a wish.**
    ``two-phase-flow-boiling-heat-acquisition.md:102`` is the bare token
    ``TODO (director)`` and nothing else on the line. A containment key on that fragment
    is satisfied by *any* line containing it -- including
    ``TODO (director): explain the CHF gate``, a task assigned to him. That is instance
    twenty-one's definition, in an entry created to avoid it: a key a fresh instance of
    the thing satisfies.

    Equality forecloses it. A new address carrying content does not strip to
    ``TODO (director)``, so it fails. A second *bare* placeholder does satisfy it, and
    that is correct rather than a gap -- it is the D41 ``STATE.md`` finding exactly:
    naming an empty field is not addressing him, so another empty field of the identical
    shape is the same class of content, not a new claim on his time.

    Declared here as DATA rather than built as a second predicate function, so
    :func:`_addresses_only` stays the single mechanism for all twelve exempted members.
    A second function would be a second thing to witness and a second thing to drift;
    a marker type in the key tuple is visible at the call site and cannot diverge.
    """

    text: str


def _fragment_text(fragment) -> str:
    """The literal text of a key, whichever matching rule it carries."""
    return fragment.text if isinstance(fragment, Exact) else fragment


def _addresses_only(known: tuple) -> Callable[[str], bool]:
    """Build the predicate: every Director-addressed line carries a known sentence.

    One mechanism for every exempted member, so there is one thing to witness rather
    than several that could drift apart. A key is matched by CONTAINMENT unless it is an
    :class:`Exact`, which is matched by equality on the stripped line.

    **Subset, not equality, and deliberately so.** A member that GAINS an address fails --
    that is the property the exemption is granted on. A member that LOSES one still holds:
    deleting text addressed to the Director is an improvement, and failing the build for it
    would be a false alarm that trains people to ignore the real one.

    Keyed on the sentences, never on line numbers. Measured against the real S2 record:
    twenty-five blank lines inserted at the top, a long unrelated paragraph appended, an
    address deleted, and a full reflow to 88 columns all leave it holding; eight different
    new addresses are all caught.
    """

    def accounted(line: str) -> bool:
        lowered = line.lower()
        stripped = lowered.strip()
        for fragment in known:
            if isinstance(fragment, Exact):
                if stripped == fragment.text.lower().strip():
                    return True
            elif fragment.lower() in lowered:
                return True
        return False

    def holds(text: str) -> bool:
        lines = text.splitlines()
        for rx in _COMPILED_MARKERS.values():
            for match in rx.finditer(text):
                if not accounted(lines[text.count("\n", 0, match.start())]):
                    return False
        return True

    return holds


#: ``STATE.md``'s Director-addressed lines: the generated closure-status rows.
#:
#: **D41 replaced a value-level premise with a structural one, and the value-level premise
#: had never held.** It claimed every ``awaiting the Director's status: closed`` value read
#: ``none``; the shipped file's line 95 read ``F-01``, and the review that reported F-04 had
#: already measured the values as ``{'F-01', 'none'}``. The claim was written by reading the
#: file rather than by running against it -- inside the mechanism built to abolish premises
#: written that way -- and the freeze caught it.
#:
#: ``STATE.md`` is generated from the ledgers. Its VALUES change as findings open and close;
#: its TEMPLATE does not. So the premise now rests on the template: every Director-addressed
#: line is a generated closure-status row. ``F-01`` sitting in one is the file being correct.
#:
#: Two fragments cover all twelve lines that ``finditer`` reports -- eleven generated rows
#: (35..185) and the release-blocker summary (194). ``search`` reports **one**, because every
#: row fires the same marker; a premise built from that view would have been false on
#: arrival for the third time in four rounds.
_STATE_KNOWN_ADDRESSES = (
    "**Built and verified, awaiting the Director's `status: closed`:**",
    "built and verified, **awaiting the Director's closure**",
)

#: The `OTB-G004` review record and its findings file: both quote the marker vocabulary in
#: order to rule on it, which is what `OTB-G003_dispositioned.md` is already exempted for.
#:
#: **Re-keyed from Cowork's draft after attacking it.** The draft used quotations of marker
#: wording -- ``"Judgment call for the director"``, ``"asks the Director to rule"``,
#: ``"awaiting the Director's closure"`` -- and fresh addresses reusing those words passed
#: the check: three of five on the ledger, one of three on ``STATE.md``. That is instance
#: twenty-one again, a key a new instance of the thing satisfies. Every fragment below is
#: line-distinctive and was attacked with nine probes, each asserted to fire a marker first.
_G004_DISPOSITIONED_KNOWN_ADDRESSES = (
    "Run against the shipped text: 'asks the Director to rule' fires",
    "one marker; 'need a director ruling before S3 proceeds'",
    "'Judgment call for the director.' each fire ZERO. That is why Cowork's",
    "The regression fixture hard-codes a none value, so it cannot",
    "_COUPLING_SUBJECT, 'asks Dan to rule' and 'asks the Director eleven",
    "is explicitly pending Director disposition, places a judgment call before him",
    "two findings need a Director ruling, lines 19-27",
)
_G004_FINDINGS_KNOWN_ADDRESSES = (
    "findings need a Director ruling, lines 19-27",
    "names F-01 as awaiting the Director's status field",
)

#: The two mastery-ledger members that carry NO task assigned to him (D44).
#:
#: ``two-phase-flow-boiling-heat-acquisition.md:102`` is the bare token and nothing else
#: on the line, sitting under "## Explanation in the director's own words" -- an empty
#: field. **Keyed by EQUALITY, not containment**, because the fragment IS the marker's
#: own wording: a containment key here is satisfied by
#: ``TODO (director): explain the CHF gate``, which is a task assigned to him and exactly
#: what the exemption must not cover. See :class:`Exact`.
_TWO_PHASE_ENTRY_KNOWN_ADDRESSES = (Exact("TODO (director)"),)

#: ``template.md:29`` is guidance to whoever fills a new entry and assigns him nothing.
#: It has real surrounding context, so it takes an ordinary containment key.
_LEDGER_TEMPLATE_KNOWN_ADDRESSES = (
    "Leave as `TODO (director)` until done -- do not fabricate.",
)

#: `OTB-G004`'s round-2 findings file. Three addressed lines, and the middle one
#: (110) is visible only to ``finditer`` -- the fourth member in which that gap has
#: appeared, and the third to have produced a false premise if built from ``search``.
#:
#: **Keyed on the REPORT'S OWN FRAMING, never on the sentence it quotes.** Two of these
#: lines exist because Sol quoted a Director-addressed sentence as evidence; a key taken
#: from the quotation would be satisfied by any future record quoting the same sentence,
#: and by the sentence itself appearing anywhere. So the keys carry the report's prose
#: around the quotation -- ``is itself a``, ``both fires``, ``requests for explanations``
#: -- which is this document writing about the finding rather than the finding's words.
_G004_02_FINDINGS_KNOWN_ADDRESSES = (
    'registry allowlist key "it is a finding for director disposition" is itself a',
    'not a repair this build owns" both fires',
    "requests for explanations and director-authored derivations",
)

#: `OTB-G004`'s round-2 disposition record. **SEVEN addressed lines, and D46 keyed three.**
#:
#: **D48, and the reason it exists is that D46's own reasoning was wrong on a fact.** The
#: D46 note here ended *"these are gate records deposited into a packet, not living
#: documents -- nothing reflows them."* Nothing did. But the D47 three-zone seam repair
#: **amended** the record: ``option_presented:`` must carry the exact option text the
#: Director was shown, so the F-04 question (141), the option he CHOSE (142) and an option
#: he did NOT choose (143) entered as addressed lines, and the ``action`` field describing
#: the built marker entered as a fourth (202). An amended gate record gains addressed
#: lines exactly the way a reflowed one loses keys. The premise failed in
#: :func:`false_premises` before the freeze, which is the D40 subset rule working.
#:
#: **The line numbers here are PROSE, not keys, and they have already moved once.** The
#: first render of this record was corrupt -- ``render_disposition.py`` writes the ``.md``
#: itself and also logs to stdout, so ``> file.md`` overwrote the title, the blank line and
#: the head of the ``**Gate**`` line. These seven keys were cut against that corrupt file.
#: The repaired re-render restores three lines where two stood, so every number below is
#: one higher than the file the keys were cut from -- and every key still matches, on
#: exactly one line, with the keyed text byte-identical. That is the whole argument for
#: keying on sentences: the numbers moved and nothing had to be re-cut.
#:
#: **And the D46 key for the selection line did not survive the re-render, which the
#: handoff's own table did not catch.** That key was
#: ``> D43, selected: A `TODO (director)` pattern is added to`` -- it carried the record's
#: ``> `` blockquote prefix and its ``D43, `` label. The repair moved the label to a
#: ``--- DIRECTOR SELECTION ---`` header line, dropped the blockquote, and hard-wrapped
#: the text at ~105 columns. **The key matches nothing in the shipped file.** Line 136 was
#: reported as previously keyed and was in fact a fourth broken line. The lesson is keyed
#: into every fragment below: key on what the sentence SAYS, never on how the renderer
#: decorated it. A ``> `` prefix and a ``D43, `` label are render, not content.
#:
#: **Line 184's D46 key was weak and is replaced.** It was
#: ``is itself a plausible reusable issue phrase`` -- F-03's own vocabulary, which passes
#: :func:`weak_keys` and fails the reading the screen is only a floor for. Measured: a new
#: finding about a DIFFERENT reusable key -- *"The `STATE.md` allowlist key is itself a
#: plausible reusable issue phrase: a new row awaiting the Director's closure contains it
#: verbatim"* -- fires ``awaiting`` and slips past it. The replacement names the registry
#: allowlist key it is actually about, and catches that attack.
#:
#: **Three of these seven are verbatim option text and cannot be worded away.** 141 is the
#: question, 142 the option he chose, 143 an option he rejected; D36 forbids editing a
#: record to quiet a detector, and the Director was offered "drop the verbatim option text"
#: at D48 and declined it. So the residual is stated instead: **any future record that
#: replays this same question and option set contains these fragments.** That is not the
#: weak-key shape -- it is the same option set, re-recorded, not a new address about a
#: different subject -- but the keys do not distinguish this record from that one, and 142
#: in particular is a key cut from the Director's recorded CHOICE. Each is pinned as tightly
#: to F-04's subject as its line allows: the counts (``22``, ``twelve``, ``twenty-two``),
#: the cross-reference (``D38 handled the six the case-blind change``), the named symbol.
#:
#: **NOTHING here is reflow-robust, and unlike D46 that is not a trade.** :func:`_addresses_only`
#: requires the key on the SAME LINE as the marker match, and five of these seven lines run
#: 327-525 characters. Three keyings were measured at 72/80/88/100/120 under two reflow
#: implementations: these keys, a deliberately shortened set, and a marker-hugging set whose
#: every key contains its own marker match. **All three fail at all five widths under both.**
#: Line 184 alone carries TWO marker matches, so no single key on it can cover both once a
#: wrap separates them. Weakening buys nothing measurable and costs real attacks -- the short
#: set leaks the ``STATE.md`` probe, the marker-hugging set leaks three. At D46 the frontier
#: was real and strength was bought at a price; here there is no frontier and strength is free.
_G004_02_DISPOSITIONED_KNOWN_ADDRESSES = (
    "A `TODO (director)` pattern is added to `DIRECTOR_ADDRESSED_MARKERS`",
    "12 shipped mastery-ledger members carry 22 `TODO (director)` lines that no marker sees",
    "exactly as D38 handled the six the case-blind change surfaced",
    "the next member carrying a `TODO (director)` line ships silently",
    'registry allowlist key "it is a finding for director disposition" is itself a',
    "Eleven shipped mastery-ledger entries still contain live assignments",
    "it fired and surfaced twelve members / twenty-two lines",
)


#: ``DEBTS.md``'s two addressed lines, and **both exist because D-15 was written down.**
#:
#: **D62, and it is D48's shape a third time.** Sol's F-04 found that ``visual_api.py``'s
#: allowlist key is a reusable policy sentence; the Director took it as ``debt`` /
#: ``accepted_risk`` at D56; the builder raised it as ``DEBTS.md`` D-15. **Recording the
#: debt made the record carry the marker the debt is about** -- D-15 must print the
#: reusable sentence or it does not say what the exposure is. ``DEBTS.md`` carried ZERO
#: addressed lines before D-15 and therefore had no entry at all; this is its first.
#:
#: **Line 646 is almost entirely the quoted `visual_api.py` key, and keying on that
#: quotation would give ``DEBTS.md`` the exact defect D-15 documents.** That is not a
#: worry, it is measured: D-15 prints its own attack sentence -- *"Release notes still
#: await independent external validation. Public documentation requires project-director
#: approval."* -- and a key cut from the quotation is satisfied by it. So the key carries
#: the boundary where the quotation ends and D-15's own sentence resumes.
#:
#: **That boundary is where the markdown decoration sits, and there is nowhere else to
#: cut.** The only non-quotation text on line 646 is ``. Run against``. Measured: that
#: decoration-free fragment rejects D-15's printed attack but is satisfied by a future
#: debt written in D-15's own house style -- ``*"<some other quoted key>"*. Run against
#: the shipped module, the line`` -- because "Run against the shipped module" IS the house
#: style. ``approval"*. Run against`` rejects both. **Decoration-free and strong are not
#: both available here**, and D48 taught that decoration dies at the next re-render, so
#: this key is the one to re-cut first if ``DEBTS.md`` is ever reformatted.
#:
#: **Line 653 is keyed on its whole sentence for the same reason.** The defect-class
#: clause alone -- *"classifies a genuinely new request for the Director's approval as
#: already known"* -- is satisfied by a future debt about a DIFFERENT weak key, measured.
#: Carrying D-15's own continuation pins it to this entry.
#:
#: **This premise ENUMERATES, so the next marker-bearing debt entry will falsify it.**
#: That is not a defect of these keys and it is not hidden: it is the enumerated-premise
#: question raised at D48 §2.4, which the Director has not ruled on. Until he does, the
#: failure is loud and lands in :func:`false_premises` before a freeze, which is the
#: behaviour every other entry here has.
_DEBTS_KNOWN_ADDRESSES = (
    'approval"*. Run against',
    "classifies a genuinely new request for the Director's approval as already known. "
    "**The module itself",
)


#: The `-05` and `-06` gate records, which ship for the first time at D66.
#:
#: **They are not new text; they are text that was always claimed and never shipped.**
#: Sol's F-02 (blocker) was that the `-05` records were absent from the packet while the
#: ledger said they were present -- the assembler named records as literals and left the
#: rest behind. D66 derives the set from ``dispositions/`` instead, so four rounds of
#: records now actually ship, and three of them carry addresses.
#:
#: **FOUR OF THE FIVE ADDRESSED LINES QUOTE THE ONE SENTENCE THIS MODULE ALREADY KNOWS
#: IS UNSOUND.** Sol's F-04 and the Director's D56 accepted, as debt D-15, that
#: ``visual_api.py``'s key is a reusable policy sentence. These records exist to STATE
#: that finding, so they print the sentence. Keying on it would hand these three members
#: the exact defect they are recording -- measured, not feared: with the policy sentence
#: as the key, D-15's own printed attack satisfies the premise. So every key below is cut
#: from the RECORD'S OWN framing -- Sol naming which key he is attacking, and which file
#: and line carries the original -- never from the quotation in the middle of the line.
#:
#: **The two YAML lines are keyed by EQUALITY, and that is forced rather than chosen.**
#: They are block-scalar wraps: everything before ``approval`` is the unsound sentence
#: and everything after is three or four words of Sol's. Measured, the maximal containment
#: key -- the whole wrapped line -- is still satisfied by a future ``**Evidence.**`` line
#: citing the same module lines, because that citation reproduces the whole fragment
#: verbatim. **No containment key on line 156 can distinguish it**; the line's entire
#: content is a citation any finding about any key would reproduce. :class:`Exact`
#: forecloses it for the reason D44 gives: only a byte-identical line satisfies equality,
#: and a byte-identical citation re-recorded is the same content, not a new claim on his
#: time.
_G004_05_DISPOSITIONED_KNOWN_ADDRESSES = (
    "visual-api allowlist key remains a generic policy sentence that a plausible new "
    "address can reuse",
    "visual_api.py:874 carries the original sentence",
)

#: `-06`'s single address is **Sol's F-06, which is a finding against the D62 key in this
#: module** -- that ``DEBTS.md``'s first key is generic approval wording plus markdown
#: house style. **He is right; it reproduces.** A line reading *"The release exception
#: needs the Director's approval"* followed by the italic-quote close and *"Run against"*
#: fires ``needs-his-action``, contains ``approval"*. Run against`` in full, and leaves the
#: ``DEBTS.md`` premise green. The Director dispositioned it ``accepted_risk`` at D66, so
#: it is a debt and not a repair this build owns -- the key is NOT changed here. What is
#: recorded is that the finding was reproduced rather than taken on trust, and that a
#: strictly stronger key exists if he ever reopens it: keying line 646 on
#: ``documentation requires project-director approval"*. Run against`` defeats this attack,
#: D-15's printed attack, and the house-style attack together, at the cost of length.
_G004_06_DISPOSITIONED_KNOWN_ADDRESSES = (
    "first DEBTS.md key is generic approval wording plus the register's markdown house style",
)

#: Sol's own findings file. **Its wording is the reviewer's, not this project's**, so a
#: premise keyed to it is coupled to another party's drafting: if he re-wraps his block
#: scalars these keys fail. That is the right failure -- loud, in :func:`false_premises`,
#: before a freeze -- but it should be expected rather than discovered, and it is the
#: reason both keys here are equality keys with no slack in them at all.
_G004_05_FINDINGS_KNOWN_ADDRESSES = (
    Exact('validation. Public documentation requires project-director approval." fires the'),
    Exact('validation. Public documentation requires project-director approval"; lines 427-430'),
)


QUOTATION_ALLOWLIST: dict[str, _Exemption] = {
    "SETTLED_DECISIONS.md": _Exemption(
        reason=(
            "the decision record itself. It quotes C10's own text about notes 'for Dan' "
            "and what 'the Director must decide', and D30's table quotes the very line "
            "each newly excluded report was judged on. A record of rulings must be able "
            "to state them."
        ),
        premise="it still quotes both C10 fragments the reason names",
        holds=lambda t: "for Dan" in t and "Director must decide" in t,
    ),
    "STATE.md": _Exemption(
        reason=(
            "a status document GENERATED from the ledgers, whose every Director-addressed "
            "line is a closure-status row of a fixed template. Naming the field is not "
            "addressing him, and a finding sitting in one of those rows is the file being "
            "correct: `status: closed` is his alone, so a built-and-verified finding "
            "waits there by design. The value-level claim this reason used to make -- that "
            "every value reads 'none' -- was false when it was written and is gone (D41)."
        ),
        premise="every Director-addressed line in it is a generated closure-status row",
        holds=_addresses_only(_STATE_KNOWN_ADDRESSES),
    ),
    "scripts/packet_exclusions.py": _Exemption(
        reason=(
            "this module, which quotes the reasons above. The predicted false positive: "
            "the docstring warned that a filter over Director-addressed prose would flag "
            "the filter, and on first measurement it was the only one of five hits that "
            "was not genuine."
        ),
        premise="its marker text sits inside its own exclusion reasons",
        holds=lambda t: "asks him to disposition it" in t,
    ),
    "tests/test_packet_exclusions.py": _Exemption(
        reason=(
            "the regressions for this module, whose fixtures must hold REAL marker shapes "
            "to test detection of them -- a test that detects only obfuscated markers "
            "tests nothing. Found by :func:`discover_director_addressed` refusing the D30 "
            "freeze on its first run against a changed tree, which is the same false "
            "positive as the module's, one level out: the test for the filter quotes what "
            "the filter detects."
        ),
        premise="its marker text sits inside the declared member-text fixtures",
        holds=lambda t: "_MEMBER_TEXT" in t and "asks him to disposition it" in t,
    ),
    # --- added under D31, both because the widened vocabulary reached them ---------
    "OTB-G003_dispositioned.md": _Exemption(
        reason=(
            "the dispositioned ledger, whose line 274 states the FINDING that the packet "
            "contained files addressed to the Director -- it quotes the shape in order to "
            "record that it was raised. A ledger that cannot describe a C10 finding cannot "
            "disposition one."
        ),
        premise="it still states the finding about Director-addressed files",
        holds=lambda t: "addressed to the Director" in t,
    ),
    "00_GATE_BRIEF.md": _Exemption(
        reason=(
            "the brief, which quotes the Director's rulings throughout and -- at D31 -- "
            "quotes the two wordings this round's widening was written to catch, in the "
            "paragraph explaining why they were missed. It is clean under the OLD "
            "vocabulary and fires only under the new one, which makes it the same class "
            "as this module and its tests: a document that quotes what the filter "
            "detects, in order to explain it."
        ),
        premise="it quotes a Director ruling, which is why it carries the shape",
        holds=lambda t: bool(re.search(r"\bD\d{2}\b", t)) and "Director" in t,
    ),
    # --- added under D38: the artifact stays in its own review packet ---------------
    "src/orbital_thermal/registry/two_phase.py": _Exemption(
        reason=(
            "the registry module the finding at line 296 is ABOUT: 'that is a "
            "registry-level question for director disposition, not for this build'. "
            "Excluding it would drop the artifact from the packet a reviewer must review "
            "-- and the Director declined the alternative of rewording the line, because "
            "editing it moves the src/ tree object off f36aab28 after seven unmoved "
            "commits, which is the statement every packet since 44d5b02 rests on."
        ),
        premise="every Director-addressed line in it is one of the two known sentences",
        holds=_addresses_only(_REGISTRY_KNOWN_ADDRESSES),
    ),
    # --- added under D39: allowlisted rather than excluded, because dropping either
    # breaks the packet's own suite -- measured by reconstruction, and the Director
    # ruled on the measurement rather than on the reading.
    "src/orbital_thermal/visual_api.py": _Exemption(
        reason=(
            "line 874 is a standing documentation-policy statement, not a live question: "
            "'Public documentation requires project-director approval.' Excluding it "
            "removes a source module from the packet and the shipped suite stops at "
            "collection -- ImportError in tests/test_visual_api.py, zero tests run."
        ),
        premise="its only Director-addressed line is the documentation-policy sentence",
        holds=_addresses_only(_VISUAL_API_KNOWN_ADDRESSES),
    ),
    "verification/review-records/2026-07-25-s2-two-phase-evaporator.md": _Exemption(
        reason=(
            "the record that escaped every sweep before D37, and the reason F-04 exists. "
            "Excluding it fails two tests that require a real review record on disk -- "
            "test_sibling_f05_a_real_review_record_is_accepted and "
            "test_f10_the_migration_path_is_explicit_and_requires_a_review_record. It is "
            "a historical record of a review, and its Director-addressed lines are what "
            "it is a record OF."
        ),
        premise="every Director-addressed line in it is one of the seven known sentences",
        holds=_addresses_only(_S2_RECORD_KNOWN_ADDRESSES),
    ),
    # --- added under D41: the review record quoting the vocabulary to rule on it -----
    "OTB-G004_dispositioned.md": _Exemption(
        reason=(
            "the `OTB-G004` dispositioned ledger. It quotes the marker vocabulary at "
            "length -- the sentences that fired, the ones that did not, and the stale "
            "STATE.md premise -- because ruling on a vocabulary finding means restating "
            "the vocabulary. Same class as `OTB-G003_dispositioned.md`, already exempted."
        ),
        premise="every Director-addressed line in it is one of the seven known sentences",
        holds=_addresses_only(_G004_DISPOSITIONED_KNOWN_ADDRESSES),
    ),
    "findings-OTB-G004.yaml": _Exemption(
        reason=(
            "the `OTB-G004` findings file, whose F-04 evidence field cites the review "
            "record's and STATE.md's own Director-addressed lines as the evidence FOR the "
            "finding. A findings file that could not quote what it found could not report "
            "it."
        ),
        premise="every Director-addressed line in it is one of the two known sentences",
        holds=_addresses_only(_G004_FINDINGS_KNOWN_ADDRESSES),
    ),
    # --- added under D44: the two ledger members that assign him nothing -------------
    "verification/mastery-ledger/entries/two-phase-flow-boiling-heat-acquisition.md":
        _Exemption(
            reason=(
                "the one mastery-ledger entry whose only Director-addressed line is an "
                "EMPTY FIELD: line 102 is the bare token `TODO (director)` under "
                "'## Explanation in the director's own words', with no task attached. Its "
                "ten siblings each also carry a specific write-up he owes and are excluded "
                "for that line; this one has no such line. Naming a field he will one day "
                "fill is not addressing him -- the D41 `STATE.md` finding, in a ledger."
            ),
            premise="its only Director-addressed line is exactly the bare placeholder",
            holds=_addresses_only(_TWO_PHASE_ENTRY_KNOWN_ADDRESSES),
        ),
    "verification/mastery-ledger/template.md": _Exemption(
        reason=(
            "the template, whose line 29 is instruction to whoever fills a NEW entry -- "
            "'drafting. Leave as `TODO (director)` until done -- do not fabricate.' It "
            "explains the placeholder convention and assigns the Director nothing. A "
            "template that could not describe the convention could not teach it."
        ),
        premise="its only Director-addressed line is the placeholder-convention guidance",
        holds=_addresses_only(_LEDGER_TEMPLATE_KNOWN_ADDRESSES),
    ),
    # --- added under D46: round 2's own records, which quote what they ruled on -----
    # Gate records, not repository files: they exist only inside a packet, so these two
    # premises are exercised only when the packet directory is supplied.
    "findings-OTB-G004-02.yaml": _Exemption(
        reason=(
            "the round-2 findings file. Two of its three addressed lines are Sol's F-03 "
            "evidence QUOTING the registry allowlist key -- the finding is that the key "
            "is reusable, and stating it requires reproducing it -- and the third "
            "summarises the `TODO (director)` requests F-04 is about. A findings file "
            "that could not quote what it found could not report it. Same basis as "
            "`findings-OTB-G004.yaml`, already exempted."
        ),
        premise="every Director-addressed line in it is one of the three known sentences",
        holds=_addresses_only(_G004_02_FINDINGS_KNOWN_ADDRESSES),
    ),
    "OTB-G004-02_dispositioned.md": _Exemption(
        reason=(
            "the round-2 disposition record. It quotes D43's selected option back "
            "verbatim -- the Director's own ruling, which a record of rulings must be "
            "able to state -- and restates both findings' text in order to disposition "
            "them. Since the D47 seam repair it also carries the `option_presented:` "
            "field, whose contract is the EXACT question and option text he was shown, "
            "so the question, his choice and a rejected option are quoted verbatim too. "
            "Same basis as `OTB-G003_dispositioned.md` and `OTB-G004_dispositioned.md`, "
            "already exempted."
        ),
        premise="every Director-addressed line in it is one of the seven known sentences",
        holds=_addresses_only(_G004_02_DISPOSITIONED_KNOWN_ADDRESSES),
    ),
    # --- added under D62: the debt register, which now documents a marker ------------
    "DEBTS.md": _Exemption(
        reason=(
            "the debt register. Its only Director-addressed lines are both inside D-15, "
            "the entry recording Sol's F-04 -- that `visual_api.py`'s allowlist key is a "
            "reusable policy sentence -- which the Director accepted as `accepted_risk` "
            "at D56. D-15 must PRINT that sentence and the new line that defeats it, or "
            "it does not say what was accepted; a debt register that cannot quote the "
            "defect cannot record one. Same basis as `OTB-G003_dispositioned.md`, and the "
            "same shape as D48: a record that documents an addressed line becomes a "
            "record containing an addressed line. NOT a repository file -- it is copied "
            "into the packet by the assembler, so this premise is checked against the "
            "shipped bytes and is exercised only when that copy is supplied."
        ),
        premise="every Director-addressed line in it is one of the two known sentences",
        holds=_addresses_only(_DEBTS_KNOWN_ADDRESSES),
    ),
    # --- added under D66: the records Sol's F-02 repair finally ships ----------------
    "OTB-G004-05_dispositioned.md": _Exemption(
        reason=(
            "round 5's disposition record. Its two addressed lines are F-04's Finding "
            "and Evidence fields, both of which quote `visual_api.py`'s policy sentence "
            "because the finding IS that the sentence is reusable. Stating it requires "
            "reproducing it -- the basis `findings-OTB-G004-02.yaml` is already exempted "
            "on. A record that could not print the defect could not disposition it."
        ),
        premise="every Director-addressed line in it is one of the two known sentences",
        holds=_addresses_only(_G004_05_DISPOSITIONED_KNOWN_ADDRESSES),
    ),
    "OTB-G004-06_dispositioned.md": _Exemption(
        reason=(
            "round 6's disposition record. Its single addressed line is F-06's Finding "
            "field, which quotes the approval wording of this module's own `DEBTS.md` "
            "key in order to state that the key is defeatable. Same class as "
            "`scripts/packet_exclusions.py` and its tests, already exempted: a document "
            "that quotes what the filter detects, in order to rule on it."
        ),
        premise="its only Director-addressed line is F-06's finding about the DEBTS key",
        holds=_addresses_only(_G004_06_DISPOSITIONED_KNOWN_ADDRESSES),
    ),
    "findings-OTB-G004-05.yaml": _Exemption(
        reason=(
            "Sol's round-5 findings file. Two wrapped lines of F-04's `finding` and "
            "`evidence` block scalars carry the policy sentence the finding is about, "
            "and one of them also cites this module's own definition of the key. A "
            "findings file that could not quote what it found could not report it -- the "
            "basis `findings-OTB-G004.yaml` and `findings-OTB-G004-02.yaml` are exempted "
            "on. Keyed by EQUALITY because containment cannot distinguish these lines "
            "from the same citation in a future finding about a different key."
        ),
        premise="every Director-addressed line in it is exactly one of the two known wraps",
        holds=_addresses_only(_G004_05_FINDINGS_KNOWN_ADDRESSES),
    ),
}

#: Gate-record documents a packager adds alongside the repository members. Named here
#: so :func:`unknown_exclusions` can be given the whole candidate set; a filter checked
#: only against tracked files would report the scope proposal as a stale entry while it
#: was in fact shipping.
PACKAGING_TIME_DOCUMENTS: tuple[str, ...] = (
    "00_GATE_BRIEF.md",
    "findings.schema.yaml",
    "ACCEPTANCE_CRITERIA_OTB-G002.md",
    "SETTLED_DECISIONS.md",
    "DEBTS.md",
    "STATE.md",
    "OTB-MAINT-01_dispositioned.md",
    "OTB-MAINT-02_dispositioned.md",
    "OTB-MAINT-03_dispositioned.md",
    "OTB-G003_S4_SCOPE_PROPOSAL.md",
)


def excluded_members(paths: list[str]) -> list[tuple[str, str]]:
    """The (path, reason) pairs a packager must drop, from the paths it was going to ship.

    Returns pairs rather than a filtered list so the packager can **report** what it
    dropped and why. A packaging filter that removes members silently is the same shape
    of defect as the thing it is removing: a fact about the artifact that never reaches
    the person who needs it.
    """
    return [(p, DIRECTOR_ADDRESSED_MEMBERS[p]) for p in paths if p in DIRECTOR_ADDRESSED_MEMBERS]


def unknown_exclusions(paths: list[str]) -> list[str]:
    """Entries on the list that are not in the shipping set -- a stale list is a defect.

    An exclusion naming a file that no longer exists looks like protection and is not.
    Fails loudly rather than degrading quietly, for the same reason the mutation harness
    reports a rotted anchor as a failure instead of skipping it.
    """
    return sorted(set(DIRECTOR_ADDRESSED_MEMBERS) - set(paths))


#: How a round's own two gate records are named. Kept beside the check that uses it so
#: the coupling this check rests on is visible rather than buried in an f-string.
_ROUND_RECORD_NAMES: tuple[tuple[str, str], ...] = (
    ("findings-{record_id}.yaml", "findings file"),
    ("{record_id}_dispositioned.md", "disposition record"),
)


def missing_round_records(record_id: str, paths: list[str]) -> list[str]:
    """The round's OWN records, missing from the set it is about to ship. **Fatal.**

    **D50.** :func:`unknown_exclusions` catches an entry naming a member that is not
    shipping. This is its mirror and nothing checked it: a member that must be shipping
    and is not. Round 2's entire record went missing under a freeze that passed, because
    the freeze checks bytes, the certificate and authority containment, and had no
    statement about which records a packet must contain at all.

    One comparison per name against the set :func:`unknown_exclusions` is already given.
    No traversal, no new mechanism, nothing read.

    **The residual, stated rather than engineered away, because it is the shape this
    project counts.** This keys "the record exists" on a NAMING CONVENTION. It therefore
    tests the shape imagined rather than the property needed: a record present under a
    different name reads as absent, and a correctly-named empty file reads as present.
    That objection was put to the Director at D50 as the argument against building it and
    he outweighed it -- *"a loud wrong-name failure still beats a silent absence, and it
    is disclosed either way"* -- so the failure message below says so in the words a
    reader gets, not only here.

    **It closes ONE INSTANCE, not the class.** It does not detect a ledger that exists but
    is empty, a ledger missing findings, or a ``STATE.md`` derived from a partial set. The
    completeness gap this instance came from is still open.

    **CALL IT AT THE RE-FREEZE, NEVER AT THE REVIEW FREEZE -- measured, not assumed.**
    A review packet is frozen to OPEN a round: the reviewer reads it in order to WRITE that
    round's findings, so the round's own records cannot exist yet. Checked against every
    packet in the deposit directory -- ``OTB-G002-02``, ``OTB-G003-02``, ``OTB-G004-02``,
    ``OTB-G003``, ``OTB-G004`` -- **not one contains its own round's findings file or
    disposition record**, and all five froze green. So wiring this into the review-packet
    freeze would fire on every packet this project has ever produced, which is a false
    alarm that trains people to ignore the real one -- the failure mode named at
    :data:`_REGISTRY_KNOWN_ADDRESSES` and the reason this module keys on sentences rather
    than line numbers. The caller chooses when; this function only answers whether.
    """
    present = set(paths)
    return [
        f"{name}: the {label} for {record_id} is not in the member set. "
        f"(This check matches by NAME: a record shipping under a different name "
        f"reports here as absent, and an empty file of the right name reports as present.)"
        for template, label in _ROUND_RECORD_NAMES
        for name in (template.format(record_id=record_id),)
        if name not in present
    ]


def discover_director_addressed(
    members: Mapping[str, str],
) -> list[tuple[str, str, int, str]]:
    """Members carrying a Director-addressed marker that nothing accounts for.

    **The coverage check D30 showed was missing.** ``members`` maps member name to its
    decoded text -- the packager already holds every byte it is about to ship, so this
    function reads nothing and works identically in a checkout and in a reconstruction.
    Binary members are simply not passed in.

    Returns ``(member, marker_label, line_number, line)`` for each member that carries a
    marker and is **neither** enumerated in :data:`DIRECTOR_ADDRESSED_MEMBERS` **nor** on
    :data:`QUOTATION_ALLOWLIST`. A non-empty result must fail the build.

    Enumerated members are skipped rather than exempted-and-forgotten, and that is what
    makes the two mechanisms independent: **delete an entry from the enumeration and it
    stops being skipped here, so discovery catches it.** A regression asserts exactly
    that, because without it a forgotten entry would still pass and the coverage gap
    would be back.

    The line is returned, not just the name, so the packager reports the same evidence a
    human would need to judge the call -- the reason a member qualifies is a line of its
    text, and a filter that reported only names would make the next reviewer re-derive it.
    """
    findings: list[tuple[str, str, int, str]] = []
    for name in sorted(members):
        if name in DIRECTOR_ADDRESSED_MEMBERS or name in QUOTATION_ALLOWLIST:
            continue
        text = members[name]
        for label, rx in _COMPILED_MARKERS.items():
            match = rx.search(text)
            if match is None:
                continue
            line_no = text.count("\n", 0, match.start()) + 1
            line = text.splitlines()[line_no - 1].strip()
            findings.append((name, label, line_no, line))
    return findings


def false_premises(members: Mapping[str, str]) -> list[tuple[str, str]]:
    """Allowlist entries whose stated premise is FALSE for this packet. **Fatal.**

    D37/F-04: an exemption is only as good as the fact it rests on, and ``STATE.md``'s
    fact had stopped being true without anything noticing. Each entry's ``holds``
    predicate is evaluated against the member's own text, and a false one must fail the
    build -- not warn. An exemption resting on a false premise is not a weaker exemption,
    it is an unjustified one.

    **Only entries that are actually exempting something are checked.** If a member no
    longer carries a marker, the exemption is doing no work and its premise is moot --
    that is :func:`inert_allowlist`'s advisory business, not a build failure. Checking it
    here too would make one stale entry fail twice under two different severities.

    An entry with no predicate is itself a failure: an unchecked premise is what this
    function exists to abolish, so a missing one cannot be the way to avoid the check.
    """
    bad: list[tuple[str, str]] = []
    for name, entry in sorted(QUOTATION_ALLOWLIST.items()):
        text = members.get(name)
        if text is None:
            continue
        if not any(rx.search(text) for rx in _COMPILED_MARKERS.values()):
            continue  # exempting nothing this round; inert_allowlist reports it
        if not callable(getattr(entry, "holds", None)):
            bad.append((name, "allowlisted with no checkable premise"))
            continue
        if not entry.holds(text):
            bad.append((name, f"stated premise is false for this packet: {entry.premise}"))
    return bad


def inert_allowlist(members: Mapping[str, str]) -> list[tuple[str, str]]:
    """Allowlist entries that are suppressing nothing -- dead weight, reported.

    An exemption that exempts nothing is the defect :func:`unknown_exclusions` catches,
    one level out: it reads as a considered decision and protects nothing. Two ways it
    happens, distinguished because they need different fixes -- the entry is not in the
    member set at all, or it is there and carries no marker.

    Advisory rather than fatal. A document can legitimately stop quoting the Director
    between rounds, and that is a reason to prune the entry, not to refuse the freeze.
    """
    inert: list[tuple[str, str]] = []
    for name in sorted(QUOTATION_ALLOWLIST):
        if name not in members:
            inert.append((name, "not in the member set this round"))
        elif not any(rx.search(members[name]) for rx in _COMPILED_MARKERS.values()):
            inert.append((name, "in the packet but carries no marker; suppressing nothing"))
    return inert
