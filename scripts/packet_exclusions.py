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
from collections.abc import Mapping

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
}

#: The marker shapes, each traceable to what `OTB-G002` F-05 was actually raised on.
#:
#: **Deliberately narrow.** The rejected alternative is a sweep for ``Director``, which
#: this module's own docstring explains would fire on provenance and delete the artifact
#: to protect the packet. These fire on a member *addressing* him -- asking him to rule,
#: naming him in an open checklist item, or waiting on him -- not on one *citing* him.
#: Measured on the assembled member set: ten members carry a marker, seven are enumerated
#: exclusions and three are quotation (see :data:`QUOTATION_ALLOWLIST`).
DIRECTOR_ADDRESSED_MARKERS: dict[str, str] = {
    "for-dan": r"for Dan",
    "director-question": r"is a Director question",
    "asks-him-to": r"asks (?:him|the Director) to",
    "unchecked-checklist": r"^[ \t]*-[ \t]*\[ \].*Director",
    "director-must-rule": (
        r"Director (?:must|needs to|should) (?:rule|decide|choose|disposition)"
    ),
    "awaiting": r"awaiting (?:Dan|the Director)",
}

_COMPILED_MARKERS = {
    label: re.compile(pattern, re.M) for label, pattern in DIRECTOR_ADDRESSED_MARKERS.items()
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
QUOTATION_ALLOWLIST: dict[str, str] = {
    "SETTLED_DECISIONS.md": (
        "the decision record itself. It quotes C10's own text about notes 'for Dan' and "
        "what 'the Director must decide', and D30's table quotes the very line each newly "
        "excluded report was judged on. A record of rulings must be able to state them."
    ),
    "STATE.md": (
        "a status document with a standing field for what awaits the Director's "
        "'status: closed'. Naming the field is not addressing him -- and its value here "
        "is 'none'."
    ),
    "scripts/packet_exclusions.py": (
        "this module, which quotes the reasons above. The predicted false positive: the "
        "docstring warned that a filter over Director-addressed prose would flag the "
        "filter, and on first measurement it was the only one of five hits that was not "
        "genuine."
    ),
    "tests/test_packet_exclusions.py": (
        "the regressions for this module, whose fixtures must hold REAL marker shapes to "
        "test detection of them -- a test that detects only obfuscated markers tests "
        "nothing. Found by :func:`discover_director_addressed` refusing the D30 freeze on "
        "its first run against a changed tree, which is the same false positive as the "
        "module's, one level out: the test for the filter quotes what the filter detects."
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
