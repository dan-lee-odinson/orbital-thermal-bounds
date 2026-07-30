"""OTB-G003 F-08: the packaging-time half of C10, and its list must stay honest.

**HERMETIC. These tests shell out to nothing and read no repository.**

They used to call ``git ls-files``. That works in a checkout and fails in a review
packet: the freeze reconstructs the tree from ``PACKET_LAYOUT.tsv`` into a bare
directory with no ``.git``, so four of these tests died with
``CalledProcessError: 'git ls-files' returned 128`` when the round-2 packet was
verified. A test that reads something the packet does not ship is exactly the defect
``verify_packet.py`` exists to catch, and it caught mine.

``excluded_members`` and ``unknown_exclusions`` are pure functions over a candidate
list. They are tested as such, against explicit inputs, which runs identically in a
checkout and in a reconstruction and is a stronger test than one coupled to the state
of a git index.

**The real-tree binding is checked where the real tree exists** -- the freeze tooling
calls ``unknown_exclusions`` over the assembled member set and reports entries that
match nothing. That check needs the packager's actual candidate set, which is knowable
at freeze time and not from inside a packet that excludes the very files it names.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from packet_exclusions import (  # noqa: E402
    DIRECTOR_ADDRESSED_MARKERS,
    DIRECTOR_ADDRESSED_MEMBERS,
    PACKAGING_TIME_DOCUMENTS,
    QUOTATION_ALLOWLIST,
    discover_director_addressed,
    excluded_members,
    inert_allowlist,
    unknown_exclusions,
)

#: An explicit stand-in for what a packager offers: ordinary members that must survive,
#: plus every name the exclusion list knows about. Written out rather than discovered,
#: so the test states its own inputs.
_ORDINARY = (
    "src/orbital_thermal/coupled_loop.py",
    "src/orbital_thermal/registry/two_phase.py",
    "tests/test_coupled_loop.py",
    "scripts/packet_exclusions.py",
    "README.md",
    "ACCEPTANCE_CRITERIA_OTB-G003.md",
    "pyproject.toml",
)


#: The names a packager could offer, written out INDEPENDENTLY of the exclusion list.
#:
#: Deriving this from ``DIRECTOR_ADDRESSED_MEMBERS`` made the staleness check vacuous:
#: every key was in the candidate set by construction, so a renamed or invented entry
#: could never be reported stale. The mutation harness caught it on the first run after
#: the change. An independent universe is what makes the check a check.
_PACKET_CANDIDATES = (
    "OTB-G001_BUILD_REPORT.md",
    "OTB-G001_FIXES_REPORT.md",
    "OTB-G001-FIXES_ROUND2_REPORT.md",
    "OTB-G002_BUILD_REPORT.md",
    "OTB-G002_FIXES_REPORT.md",
    "OTB-G002_FINDINGS_REPORT.md",
    "OTB-G001-FIXES_PACKAGING_REPORT.md",
    "OTB-G003_S4_SCOPE_PROPOSAL.md",
)

#: Member text for the discovery checks, written out rather than read from anywhere.
#:
#: The strings are the real shapes: the line each newly excluded report was judged on,
#: the provenance citation that must NOT fire, and the self-quoting module that was the
#: one measured false positive.
_MEMBER_TEXT: dict[str, str] = {
    "OTB-G002_BUILD_REPORT.md": (
        "# Build report\n\n## Remaining\n\n"
        "- [ ] Sol review and Director disposition -- not the builder's\n"
    ),
    "OTB-G001-FIXES_PACKAGING_REPORT.md": (
        "# Packaging report\n\nWhether METHOD's packet checker should accept an honest\n"
        "`xfail` is a Director question about the tool, not something a build can\n"
        "resolve.\n"
    ),
    "src/orbital_thermal/registry/two_phase.py": (
        '"""Two-phase registry."""\n\n'
        "# Bound enforced per Director ruling D9.\n"
        "# Director ruling D9 is the basis for the de-ranking below.\n"
        "# See Director ruling D14 for the admitted window.\n"
    ),
    "scripts/packet_exclusions.py": (
        '"""C10 at packaging time."""\n\n'
        'REASONS = {"OTB-G001_BUILD_REPORT.md": "a build report addressed to the '
        'Director: it reports completion of work he commissioned and asks him to '
        'disposition it."}\n'
    ),
    "SETTLED_DECISIONS.md": (
        "# Settled decisions\n\nD-11: Notes seeking a ruling, flagging something\n"
        '"for Dan", or listing what the Director must decide belong in review-inbox/.\n'
    ),
    "STATE.md": (
        "# State\n\n- **Built and verified, awaiting the Director's `status: closed`:**"
        " none\n"
    ),
    "README.md": "# orbital-thermal-bounds\n\nRadiator sizing bounds.\n",
    "ACCEPTANCE_CRITERIA_OTB-G003.md": "# Acceptance criteria\n\nS4-3: fails.\n",
    # This very file. Its fixtures hold real marker shapes, so it carries markers and
    # must be allowlisted -- see QUOTATION_ALLOWLIST. Stated here so the allowlist
    # staleness check has it in the member set and stays honest about it.
    "tests/test_packet_exclusions.py": (
        "MARKER_FIXTURES = {\n"
        '    "q": "that is a Director question about the tool",\n'
        '    "a": "the report asks him to disposition it",\n'
        "}\n"
    ),
}


def _assembled() -> list[str]:
    """Repo members AND gate-record docs -- the distinction the filter turns on.

    ``OTB-G003_S4_SCOPE_PROPOSAL.md`` is not a tracked file; it enters at packaging
    time. A filter run over tracked files alone would never see the sharpest entry on
    the list, which is what the round-1 version of this test caught.
    """
    return list(_ORDINARY) + list(_PACKET_CANDIDATES) + list(PACKAGING_TIME_DOCUMENTS)


def _tracked() -> list[str]:
    """The ordinary members, as the controls use them."""
    return list(_ORDINARY)


def test_every_excluded_member_is_named_with_a_reason():
    assert DIRECTOR_ADDRESSED_MEMBERS
    for path, reason in DIRECTOR_ADDRESSED_MEMBERS.items():
        assert path.endswith(".md")
        assert len(reason) > 40, f"{path} is excluded without a stated reason"


def test_the_exclusion_list_is_not_stale():
    """A list naming files that no longer exist looks like protection and is not."""
    assert unknown_exclusions(_assembled()) == []


def test_the_four_director_addressed_reports_are_excluded():
    dropped = dict(excluded_members(_assembled()))
    assert set(dropped) == set(DIRECTOR_ADDRESSED_MEMBERS)
    assert "OTB-G003_S4_SCOPE_PROPOSAL.md" in dropped


def test_control_ordinary_members_are_not_excluded():
    """The control. An over-broad filter would delete the artifact to protect the packet."""
    tracked = _tracked()
    dropped = {p for p, _ in excluded_members(_assembled())}
    for keeper in (
        "src/orbital_thermal/coupled_loop.py",
        "src/orbital_thermal/registry/two_phase.py",
        "tests/test_coupled_loop.py",
        "README.md",
        "ACCEPTANCE_CRITERIA_OTB-G003.md",
    ):
        assert keeper in tracked and keeper not in dropped


def test_the_filter_is_enumerated_not_pattern_matched():
    """A regex over 'Director' would sweep in registry provenance notes.

    ``registry/two_phase.py`` cites "Director ruling D9" and similar dozens of times as
    the basis for an enforced bound. Those citations are the artifact working, not C10
    breaking, and a filter that could not tell them apart would be worse than none.

    Read through the package rather than off a path, so it resolves from wherever the
    module was imported -- including a reconstruction.
    """
    import orbital_thermal.registry.two_phase as reg

    registry = pathlib.Path(reg.__file__).read_text(encoding="utf-8")
    assert registry.count("Director ruling") > 3
    assert "src/orbital_thermal/registry/two_phase.py" not in DIRECTOR_ADDRESSED_MEMBERS


def test_the_filter_reports_what_it_drops_rather_than_dropping_silently():
    pairs = excluded_members(_assembled())
    assert all(isinstance(p, tuple) and len(p) == 2 and p[1] for p in pairs), (
        "a packaging filter that removes members silently is the same shape of defect "
        "as the thing it removes"
    )


def test_no_committed_history_is_rewritten_by_this_module():
    """F-08 explicitly: the fix is packaging-time, not a rewrite of the record."""
    import packet_exclusions

    src = pathlib.Path(packet_exclusions.__file__).read_text(encoding="utf-8")
    for forbidden in ("unlink", "remove(", "git rm", "rewrite", "filter-branch"):
        assert forbidden not in src


# --- D30: the enumeration cannot certify its own coverage --------------------------


def test_the_enumeration_alone_did_not_catch_the_d30_four():
    """Why discovery exists. Four members qualified and were not on the list.

    Not a hypothetical: each of these was measured carrying a marker in the deposited
    `OTB-G003-FIXES` packet, and each is on the list now BECAUSE discovery would have
    found it. The enumeration certified its entries and said nothing about its coverage.
    """
    for late in (
        "OTB-G001-FIXES_PACKAGING_REPORT.md",
        "OTB-G002_BUILD_REPORT.md",
        "OTB-G002_FIXES_REPORT.md",
        "OTB-G002_FINDINGS_REPORT.md",
    ):
        assert late in DIRECTOR_ADDRESSED_MEMBERS
        assert len(DIRECTOR_ADDRESSED_MEMBERS[late]) > 40


def test_witness_1_a_new_member_carrying_a_marker_fails_the_check():
    """A member nobody enumerated, carrying a marker, must be found."""
    members = dict(_MEMBER_TEXT)
    members["OTB-G004_BUILD_REPORT.md"] = (
        "# Build report\n\n- [ ] Director disposition of the three findings\n"
    )

    found = discover_director_addressed(members)
    names = {n for n, _, _, _ in found}
    assert "OTB-G004_BUILD_REPORT.md" in names, (
        "a member carrying a Director-addressed marker that is neither enumerated nor "
        "allowlisted must fail the build -- that is the coverage D30 exposed"
    )
    hit = next(f for f in found if f[0] == "OTB-G004_BUILD_REPORT.md")
    assert hit[1] == "unchecked-checklist"
    assert hit[2] == 3, "the line number must locate the evidence, not just the file"
    assert "Director disposition" in hit[3]


def test_witness_2_removing_an_enumerated_entry_is_still_caught_by_discovery():
    """**The one that makes list and discovery independent.**

    Without this, a forgotten entry still passes: discovery skips whatever the
    enumeration names, so an enumeration that silently shrinks would take discovery's
    coverage with it. Deleting an entry must reopen the finding.
    """
    members = dict(_MEMBER_TEXT)

    # With the entry present, the packager drops it and discovery stays quiet.
    assert "OTB-G002_BUILD_REPORT.md" in DIRECTOR_ADDRESSED_MEMBERS
    assert "OTB-G002_BUILD_REPORT.md" not in {
        n for n, _, _, _ in discover_director_addressed(members)
    }

    # Now remove it, exactly as a careless edit would.
    import packet_exclusions

    saved = dict(packet_exclusions.DIRECTOR_ADDRESSED_MEMBERS)
    try:
        del packet_exclusions.DIRECTOR_ADDRESSED_MEMBERS["OTB-G002_BUILD_REPORT.md"]
        found = discover_director_addressed(members)
    finally:
        packet_exclusions.DIRECTOR_ADDRESSED_MEMBERS.clear()
        packet_exclusions.DIRECTOR_ADDRESSED_MEMBERS.update(saved)

    assert "OTB-G002_BUILD_REPORT.md" in {n for n, _, _, _ in found}, (
        "discovery must catch a member the enumeration forgot; if it only reports what "
        "the list already names, the two mechanisms are one mechanism"
    )
    # And the enumeration is restored, so this test leaves no residue.
    assert "OTB-G002_BUILD_REPORT.md" in DIRECTOR_ADDRESSED_MEMBERS


def test_witness_3_negative_control_provenance_citations_do_not_fire():
    """``Director ruling D9`` as provenance is the artifact working, not C10 breaking.

    The rejected design -- a sweep for "Director" -- would delete the registry to protect
    the packet. This is the control that keeps the marker set narrow.
    """
    members = dict(_MEMBER_TEXT)
    registry = "src/orbital_thermal/registry/two_phase.py"

    assert members[registry].count("Director ruling") > 2
    names = {n for n, _, _, _ in discover_director_addressed(members)}
    assert registry not in names, (
        "a provenance citation must not fire; an exclusion that cannot tell citing the "
        "Director from addressing him would be worse than none"
    )
    assert registry not in DIRECTOR_ADDRESSED_MEMBERS


def test_the_assembled_set_is_clean_once_the_d30_four_are_enumerated():
    """The whole point: with the list correct, discovery reports nothing."""
    assert discover_director_addressed(dict(_MEMBER_TEXT)) == []


def test_ordinary_members_never_fire():
    """Controls that carry no marker at all."""
    for keeper in ("README.md", "ACCEPTANCE_CRITERIA_OTB-G003.md"):
        assert discover_director_addressed({keeper: _MEMBER_TEXT[keeper]}) == []


def test_every_allowlist_entry_is_named_with_a_reason_and_suppresses_something():
    """An exemption that exempts nothing reads as a decision and protects nothing."""
    assert QUOTATION_ALLOWLIST
    for name, reason in QUOTATION_ALLOWLIST.items():
        assert len(reason) > 40, f"{name} is allowlisted without a stated reason"
    assert inert_allowlist(dict(_MEMBER_TEXT)) == [], (
        "every allowlisted member must actually carry a marker; otherwise the entry is "
        "dead weight that looks like protection"
    )


def test_the_allowlist_staleness_check_can_actually_fail():
    """The staleness check must not be vacuous -- the round-1 lesson, applied to itself."""
    thinned = {k: v for k, v in _MEMBER_TEXT.items() if k != "STATE.md"}
    assert ("STATE.md", "not in the member set this round") in inert_allowlist(thinned)

    blanked = dict(_MEMBER_TEXT)
    blanked["STATE.md"] = "# State\n\nNothing outstanding.\n"
    assert ("STATE.md", "in the packet but carries no marker; suppressing nothing") in (
        inert_allowlist(blanked)
    )


def test_the_marker_set_is_narrow_and_each_shape_is_reachable():
    """Six shapes, each traceable to F-05. A marker nothing can trigger is not a check."""
    assert len(DIRECTOR_ADDRESSED_MARKERS) == 6
    probes = {
        "for-dan": "a knock-on finding for Dan to weigh",
        "director-question": "that is a Director question about the tool",
        "asks-him-to": "the report asks him to disposition it",
        "unchecked-checklist": "- [ ] Director disposition of the findings",
        "director-must-rule": "the Director must decide the 20 bar point",
        "awaiting": "awaiting the Director's closure",
    }
    assert set(probes) == set(DIRECTOR_ADDRESSED_MARKERS)
    for label, probe in probes.items():
        found = discover_director_addressed({"PROBE.md": probe})
        assert [f[1] for f in found] == [label], f"{label} did not fire on its own shape"


def test_the_allowlist_and_the_exclusion_list_do_not_overlap():
    """A member cannot be both dropped and exempted -- that would be a silent decision."""
    overlap = set(QUOTATION_ALLOWLIST) & set(DIRECTOR_ADDRESSED_MEMBERS)
    assert overlap == set(), f"{sorted(overlap)} is both excluded and allowlisted"


def test_these_tests_read_no_repository():
    """The self-containment regression. A packet has no `.git` and no `git`.

    Four tests here died with ``CalledProcessError`` inside the round-2 freeze
    reconstruction. This is the check that stops it recurring.
    """
    import ast

    import packet_exclusions

    # Parsed, not grepped: a text search finds this test's OWN assertion strings and
    # reports itself as the offender -- which it did on the first attempt.
    banned = {"subprocess", "shutil", "os"}
    for path in (pathlib.Path(__file__), pathlib.Path(packet_exclusions.__file__)):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert not (imported & banned), (
            f"{path.name} imports {sorted(imported & banned)}; a packet has no "
            "repository and no git, so these tests must read neither"
        )
