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

The list is **enumerated, not pattern-matched**. A regex over "Director" or "approval"
would sweep in registry notes that legitimately cite a ruling -- ``two_phase.py`` says
"Director ruling D9" dozens of times as provenance -- and an exclusion that fires on
provenance would delete the artifact to protect the packet. Every entry below was read
and is named, with the reason it qualifies.
"""

from __future__ import annotations

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
