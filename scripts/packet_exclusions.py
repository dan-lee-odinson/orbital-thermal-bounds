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
    "is a registry-level question for director disposition",
    "it is a finding for director disposition",
)


def _only_known_registry_lines_address_him(text: str) -> bool:
    """Every Director-addressed line in the registry module is one of the known sentences.

    Falsifiable in the direction that matters: if the module grows another address, some
    marker match lands on a line carrying neither known sentence and the exemption fails
    the build. The 27 provenance citations of "Director ruling D9" match no marker at all,
    so they neither excuse nor trigger anything here.
    """
    lines = text.splitlines()
    for rx in _COMPILED_MARKERS.values():
        for match in rx.finditer(text):
            line = lines[text.count("\n", 0, match.start())]
            if not any(known in line for known in _REGISTRY_KNOWN_ADDRESSES):
                return False
    return True


def _all_awaiting_values_are_none(text: str) -> bool:
    """Every ``awaiting the Director's status: closed`` value in the member reads ``none``.

    The literal claim ``STATE.md``'s reason makes. Line 95 of the shipped file read
    ``F-01`` and this returns False for it.
    """
    values = re.findall(
        r"awaiting the Director's[^\n]*?status: closed[^\n]*?:\*\*\s*([^\n]+)", text
    )
    return bool(values) and all(v.strip().rstrip(".").lower() == "none" for v in values)


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
            "a status document with a standing field for what awaits the Director's "
            "'status: closed'. Naming the field is not addressing him -- and its value "
            "here is 'none'."
        ),
        premise="every 'awaiting the Director's status: closed' value reads 'none'",
        holds=_all_awaiting_values_are_none,
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
        holds=_only_known_registry_lines_address_him,
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
