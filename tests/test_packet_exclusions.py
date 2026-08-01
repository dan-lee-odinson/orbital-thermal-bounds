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
    false_premises,
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
    # D38: the three the Director ruled excluded that can be excluded.
    "docs/development/phase-b-stage-2-scoping-note.md",
    "verification/mastery-ledger/index.md",
    "external_models/biswas_suncatcher/author_clarifications.md",
)

#: The registry module's real Director-addressed lines, in a stand-in with its shape.
#:
#: Both are present because the module carries both -- the ruling's premise named only the
#: first, and the second was invisible to a scan that reports one match per marker.
_REGISTRY_MEMBER = (
    '"""Two-phase registry."""\n'
    "\n"
    "# Bound enforced per Director ruling D9.\n"
    "# Director ruling D9 is the basis for the de-ranking below.\n"
    "# See Director ruling D14 for the admitted window.\n"
    "\n"
    '        "that is a registry-level question for director disposition, not for this build."\n'
    "\n"
    "# not buried in prose; it is a finding for director disposition, not a defect this\n"
    "# build is authorised to resolve by changing a director ruling.\n"
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
    # D38: the REAL shape -- provenance citations AND both Director-addressed lines, so
    # the exemption added for this member is exercised rather than merely declared. The
    # provenance-only control moved to a name nothing exempts.
    "src/orbital_thermal/registry/two_phase.py": _REGISTRY_MEMBER,
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
    # The marker cannot span a line break -- `[^.\n]` excludes the newline on purpose,
    # so a bridging match cannot be manufactured across two sentences. This fixture is
    # therefore kept unwrapped, as the real line 274 is: wrapping it turned the witness
    # green-by-accident on the first attempt, and the test caught that.
    "OTB-G003_dispositioned.md": (
        "# Dispositioned\n\n**Finding.** The packet again contains files addressed to "
        "the Director rather than the reviewer: OTB-G001_BUILD_REPORT asks Dan for "
        "rulings it should not be asking for.\n"
    ),
    "00_GATE_BRIEF.md": (
        "# Gate brief\n\nThe old marker missed the scope proposal's own wording --\n"
        "its section 8 asks the Director eleven decisions -- and also missed\n"
        '"asks Dan to rule". Both are widened this round.\n'
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
    # **Deliberately NOT the allowlisted name.** Under D38 the registry module carries an
    # exemption, so asking discovery about it would answer "quiet" because it is
    # allowlisted rather than because provenance does not fire -- the control would pass
    # for the wrong reason and stop being a control. The same bytes are put under a name
    # nothing exempts, so genuine non-firing is what is measured.
    provenance_only = "\n".join(
        line for line in _REGISTRY_MEMBER.splitlines()
        if "director disposition" not in line.lower()
    )
    assert provenance_only.count("Director ruling") > 2
    assert discover_director_addressed({"src/some/other_registry.py": provenance_only}) == [], (
        "a provenance citation must not fire; an exclusion that cannot tell citing the "
        "Director from addressing him would be worse than none"
    )
    assert "src/orbital_thermal/registry/two_phase.py" not in DIRECTOR_ADDRESSED_MEMBERS


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
    for name, entry in QUOTATION_ALLOWLIST.items():
        assert len(entry.reason) > 40, f"{name} is allowlisted without a stated reason"
        assert len(entry.premise) > 10, f"{name} has no stated checkable premise"
        assert callable(entry.holds), f"{name} has no predicate; the premise is unchecked"
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


def test_witness_d31_the_scope_proposals_own_wording_is_caught():
    """**The D31 witness, and the wording is the case's, not one chosen to match.**

    The module's docstring cites ``section 8 asks the Director eleven decisions`` as the
    most flagrant entry on the list. No marker fired on it: ``asks-him-to`` required the
    verb to be followed by ``to``. Picking a phrasing that suited the new vocabulary
    would witness nothing -- that is the mistake that produced the miss -- so this
    mutation uses the sentence the module itself quotes.
    """
    scope_proposal_wording = (
        "S4 - scope proposal for Director approval. Nothing is built until this is "
        "approved, and its section 8 asks the Director eleven decisions."
    )
    found = discover_director_addressed({"OTB-G004_SCOPE_PROPOSAL.md": scope_proposal_wording})
    labels = {f[1] for f in found}
    assert "asks-him-for-a-decision" in labels, (
        "discovery must fire on the wording of the case the module cites; a marker "
        "written from a case that cannot match that case is the sixteenth instance"
    )


def test_witness_d31_the_name_dan_is_recognised_by_the_asks_marker_too():
    """``asks Dan to rule`` was a miss: the noun decided whether the marker fired."""
    found = discover_director_addressed({"OTB-G004_REPORT.md": "it asks Dan to rule on the bore"})
    assert [f[1] for f in found] == ["asks-him-to"]


def test_witness_d31_removing_the_new_allowlist_entry_fails_the_build():
    """The fifth entry is inert-checked: remove it and the ledger must be flagged.

    An allowlist entry that could be deleted without anything noticing would be
    indistinguishable from one that was never needed.
    """
    import packet_exclusions

    members = dict(_MEMBER_TEXT)
    assert "OTB-G003_dispositioned.md" not in {
        n for n, _, _, _ in discover_director_addressed(members)
    }

    saved = dict(packet_exclusions.QUOTATION_ALLOWLIST)
    try:
        del packet_exclusions.QUOTATION_ALLOWLIST["OTB-G003_dispositioned.md"]
        found = discover_director_addressed(members)
    finally:
        packet_exclusions.QUOTATION_ALLOWLIST.clear()
        packet_exclusions.QUOTATION_ALLOWLIST.update(saved)

    hit = [f for f in found if f[0] == "OTB-G003_dispositioned.md"]
    assert hit, "removing the allowlist entry must reopen the finding"
    assert hit[0][1] == "asks-him-for-a-decision"
    assert "OTB-G003_dispositioned.md" in QUOTATION_ALLOWLIST


def test_the_sibling_ledger_is_not_allowlisted_because_it_does_not_fire():
    """``OTB-G003-02_dispositioned.md`` must NOT be added -- it carries no marker.

    Entries exist only for documents that measurably fire. Adding the sibling because
    it looks like its twin is exactly the dead weight :func:`inert_allowlist` reports.
    """
    assert "OTB-G003-02_dispositioned.md" not in QUOTATION_ALLOWLIST


#: **D37/F-04 §2.2: the STATE.md fixture is DERIVED, not written.**
#:
#: The old fixture hard-coded ``none`` as the awaiting-value, so a real non-``none``
#: Director action could not make it differ -- and one had already shipped. This builds
#: the member text from a value, so the same generator produces both the premise-true and
#: the premise-false member and neither can be quietly special-cased.
def _state_md(*awaiting_values: str) -> str:
    """The shipped STATE.md shape, with whatever awaiting-values it is given."""
    lines = ["# STATE", ""]
    for value in awaiting_values:
        lines += [
            f"- **Built and verified, awaiting the Director's `status: closed`:** {value}",
        ]
    return "\n".join(lines) + "\n"


def test_witness_d37_a_lower_case_director_line_is_discovered():
    """**Witness 1, in the escaped record's own words -- not a synthetic upper-case probe.**

    ``verification/review-records/2026-07-25-s2-two-phase-evaporator.md`` sat inside the
    packet saying two findings needed a ruling, and discovery reported zero unaccounted
    members over all 199. Its lines are used verbatim here.

    **Case-blindness alone would not have caught any of them**, and that is worth pinning:
    every line below was measured to miss as-is, capitalised AND case-insensitively under
    the old vocabulary. The shapes were missing, not just the casing.
    """
    escaped = {
        "pending-his-action": "OPEN pending director disposition + Sol cross-model review",
        "needs-his-action": "two findings below need a director ruling before S3",
        "for-his-attention": "**Knock-on for director attention:** the registry entry",
        "is-his-call": "Registry-level correction is a director decision, not a builder one.",
        "his-call-to-make": "> **Judgment call for the director.** §2 of the handoff bars",
    }
    for label, line in escaped.items():
        found = discover_director_addressed({"verification~s2-record.md": line})
        assert found, f"the record's own line was not discovered: {line!r}"
        assert label in {f[1] for f in found}, (
            f"expected {label} on {line!r}, got {[f[1] for f in found]}"
        )

    # And upper case still works: the fix widened the vocabulary, it did not move it.
    upper = discover_director_addressed({"m.md": "Two findings need a Director ruling"})
    assert upper and upper[0][1] == "needs-his-action"


def test_witness_d37_case_blindness_does_not_bleed_into_ordinary_words():
    """The paired control for ``re.I``: a case-blind rule must not become a loose one.

    Measured before the flag went on -- bare ``for Dan`` matches "waiting **for dan**ger"
    under ``re.I``, and ``awaiting (?:Dan|...)`` matches "**awaiting dan**gerous". Trading
    a false negative for a false positive would not be a fix.
    """
    for benign in (
        "we waited for danger to pass",
        "awaiting dangerous weather at the site",
        "the bound is enforced per Director ruling D9",
        "See Director ruling D14 for the admitted window.",
        "director ruling 9.5 bands (gate 5)",
    ):
        assert discover_director_addressed({"ordinary.md": benign}) == [], (
            f"{benign!r} is not addressed to anyone and must stay quiet"
        )


def test_witness_d37_the_fixture_is_derived_so_a_real_action_cannot_hide():
    """**Witness 2: mutate the member text and discovery/premise must follow it.**

    The old regression asserted against a hand-written ``none``. A fixture that cannot
    differ from what it asserts is not a fixture, so the member text is generated from the
    value and the same generator produces both cases.
    """
    clean = _state_md("none", "none")
    dirty = _state_md("none", "F-01")

    assert discover_director_addressed({"STATE.md": clean}) == []
    assert discover_director_addressed({"STATE.md": dirty}) == []  # still allowlisted

    assert false_premises({"STATE.md": clean}) == []
    bad = false_premises({"STATE.md": dirty})
    assert [n for n, _ in bad] == ["STATE.md"], (
        "a real non-'none' Director action must make the allowlist premise false; the "
        "hard-coded fixture could not notice one that had already shipped"
    )
    assert "premise is false" in bad[0][1]


def test_witness_d37_a_false_allowlist_premise_is_fatal_not_advisory():
    """**Witness 3: a false premise FAILS, and it fails differently from an inert entry.**

    Two conditions that look similar and are not: an entry exempting nothing is advisory
    (:func:`inert_allowlist`), an entry exempting something on a false premise is fatal
    (:func:`false_premises`). Collapsing them would let a false premise ship as a warning.
    """
    def for_state(pairs):
        return [p for p in pairs if p[0] == "STATE.md"]

    dirty = _state_md("F-01")
    assert false_premises({"STATE.md": dirty}), "false premise must be reported"
    assert for_state(inert_allowlist({"STATE.md": dirty})) == [], (
        "the entry IS suppressing a marker, so it is not inert -- only its premise is false"
    )

    # An entry whose member carries no marker is inert and NOT a premise failure.
    quiet = "# STATE\n\nnothing outstanding.\n"
    assert false_premises({"STATE.md": quiet}) == [], (
        "an exemption doing no work has a moot premise; failing it here would make one "
        "stale entry fail twice under two different severities"
    )
    assert for_state(inert_allowlist({"STATE.md": quiet})) == [
        ("STATE.md", "in the packet but carries no marker; suppressing nothing")
    ]


def test_witness_d37_every_entry_carries_a_predicate_and_a_missing_one_is_fatal():
    """An unchecked premise cannot be the way to avoid the premise check."""
    import packet_exclusions

    saved = dict(packet_exclusions.QUOTATION_ALLOWLIST)
    try:
        packet_exclusions.QUOTATION_ALLOWLIST["STATE.md"] = saved["STATE.md"]._replace(
            holds=None
        )
        bad = packet_exclusions.false_premises({"STATE.md": _state_md("none")})
    finally:
        packet_exclusions.QUOTATION_ALLOWLIST.clear()
        packet_exclusions.QUOTATION_ALLOWLIST.update(saved)

    assert bad == [("STATE.md", "allowlisted with no checkable premise")]
    assert callable(QUOTATION_ALLOWLIST["STATE.md"].holds)


def test_witness_d38_each_newly_excluded_member_is_dropped_for_its_stated_reason():
    """**Witness 1: the pair, not the name.** A name with no evidence is what the
    enumeration exists not to be, so the reason must carry the qualifying line."""
    dropped = dict(excluded_members(_assembled()))
    expected = {
        "docs/development/phase-b-stage-2-scoping-note.md": "no S1 code proceeds",
        "verification/mastery-ledger/index.md": "director disposition",
        "external_models/biswas_suncatcher/author_clarifications.md": "requires the project",
    }
    for member, quoted in expected.items():
        assert member in dropped, f"{member} was ruled excluded and is not dropped"
        assert quoted in dropped[member], (
            f"{member}'s reason must quote the line that makes it qualify, got "
            f"{dropped[member]!r}"
        )
        assert len(dropped[member]) > 40


def test_witness_d38_the_registry_premise_fails_on_another_address():
    """**Witness 2: green under this mutation would mean the predicate is decorative.**"""
    key = "src/orbital_thermal/registry/two_phase.py"
    assert false_premises({key: _REGISTRY_MEMBER}) == []

    grown = _REGISTRY_MEMBER + "\n# The 20 bar point is a director decision, not ours.\n"
    bad = false_premises({key: grown})
    assert [n for n, _ in bad] == [key], (
        "a module that grows another Director-addressed line must fail the exemption; "
        "an exemption that cannot go false is not falsifiable"
    )


def test_witness_d38_the_registry_premise_survives_an_unrelated_edit():
    """**Witness 3: the line-number hazard, regressed.**

    Keying on line 296 would go false the moment anything above it changed -- a false
    alarm on an unrelated edit, which is the hard-coded-commit shape one level out. The
    premise is keyed on the sentences, so inserting lines above must not disturb it.
    """
    key = "src/orbital_thermal/registry/two_phase.py"
    lines = _REGISTRY_MEMBER.splitlines(True)
    index = next(i for i, line in enumerate(lines) if "registry-level question" in line)
    shifted = "".join(lines[:index] + ["\n"] * 12 + lines[index:])

    assert "registry-level question" in shifted
    assert shifted.splitlines().index(
        next(x for x in shifted.splitlines() if "registry-level question" in x)
    ) == index + 12, "the line really did move"
    assert false_premises({key: shifted}) == [], (
        "an unrelated edit above the line must not falsify the premise"
    )


def test_witness_d38_the_provenance_citations_still_stay_quiet():
    """**Witness 4: the standing control.** 'Director ruling D9' is the artifact working."""
    key = "src/orbital_thermal/registry/two_phase.py"
    assert _REGISTRY_MEMBER.count("Director ruling") == 3

    provenance_only = "\n".join(
        line for line in _REGISTRY_MEMBER.splitlines()
        if "director disposition" not in line.lower()
    )
    assert discover_director_addressed({key: provenance_only}) == [], (
        "a module that only CITES rulings must not fire at all; an exclusion that could "
        "not tell citing from addressing would delete the artifact to protect the packet"
    )


def test_witness_d38_the_registry_module_is_exempted_not_excluded():
    """The artifact stays in its own review packet -- and is not in the drop list."""
    key = "src/orbital_thermal/registry/two_phase.py"
    assert key in QUOTATION_ALLOWLIST
    assert key not in DIRECTOR_ADDRESSED_MEMBERS
    assert key not in {p for p, _ in excluded_members(_assembled() + [key])}
    assert discover_director_addressed({key: _REGISTRY_MEMBER}) == [], (
        "the exemption must actually silence it, or the build fails on the artifact"
    )


#: A stand-in for the S2 review record carrying all SEVEN of its addressed lines.
#:
#: Seven, because ``rx.search`` shows five: lines 27 and 217 each fire a marker another
#: line already fired, so a fixture built the way the evidence was built would be missing
#: exactly the two that make the point.
_S2_MEMBER = "\n".join(
    (
        "OPEN pending director disposition + Sol cross-model review. No cross-model",
        "review is mandatory at S2.",
        "",
        "- **Disposition:** **pending director review.** `main` untouched; no tag.",
        "",
        "> **Judgment call for the director.** The handoff bars implementing from a",
        "> secondary source.",
        "",
        "## Findings requiring director disposition",
        "",
        "**Knock-on for director attention:** this also puts the registry's",
        "classification in question. Do not touch it.",
        # Unwrapped, as line 178 of the real record is: a fragment that spans a line
        # break cannot be found on any single line, and the first draft of this fixture
        # wrapped it -- which the premise caught immediately.
        "touch it. **Registry-level correction is a director decision, not a builder one.**",
        "",
        "**Not closable by the builder.** Requires: (i) director disposition of **F1**",
        "and **F2**; (ii) Sol's re-review.",
        "",
        "Ordinary prose citing Director ruling D9 as provenance, which must not fire.",
    )
) + "\n"

_S2_KEY = "verification/review-records/2026-07-25-s2-two-phase-evaporator.md"
_VISUAL_KEY = "src/orbital_thermal/visual_api.py"
_VISUAL_MEMBER = (
    '"""Visual API."""\n\n'
    "STATUS = {\n"
    '    "status": (\n'
    '        "Author cross-check is source-author review, not independent external "\n'
    '        "validation. Public documentation requires project-director approval."\n'
    "    ),\n"
    "}\n"
)


#: Registered into the member set so the two D39 exemptions are EXERCISED by
#: :func:`inert_allowlist` and :func:`false_premises` rather than merely declared. An
#: allowlist entry whose member never appears in any fixture is an entry nothing tests.
_MEMBER_TEXT[_VISUAL_KEY] = _VISUAL_MEMBER
_MEMBER_TEXT[_S2_KEY] = _S2_MEMBER


def test_witness_d39_the_new_premises_hold_and_fail_on_one_more_address():
    """**Witness 1: an exemption that cannot go false is not falsifiable.**"""
    assert false_premises({_S2_KEY: _S2_MEMBER, _VISUAL_KEY: _VISUAL_MEMBER}) == []

    grown_s2 = _S2_MEMBER + "\nAn eighth item needs a director ruling before S7.\n"
    assert [n for n, _ in false_premises({_S2_KEY: grown_s2})] == [_S2_KEY]

    grown_visual = _VISUAL_MEMBER + "\n# The axis choice is a director decision, not ours.\n"
    assert [n for n, _ in false_premises({_VISUAL_KEY: grown_visual})] == [_VISUAL_KEY]


def test_witness_d39_a_new_address_reusing_known_wording_is_still_caught():
    """The first draft keyed a line on the MARKER's wording and this slipped through.

    ``is a director decision`` is what the marker matches, so keying line 178 on it let a
    fresh eighth address using those same words pass. A key that a new instance of the
    thing satisfies is not a key. Every fragment is line-distinctive now, and the five
    attacks below all reuse wording that is already present somewhere in the member.
    """
    for attack in (
        "The 20 bar point is a director decision, not ours.",
        "S5 is pending director review before any build proceeds.",
        "New item for director attention: the bore bound.",
        "Items requiring director disposition: three of them.",
        "Judgment call for the director on eta_pump.",
    ):
        grown = _S2_MEMBER + "\n" + attack + "\n"
        assert [n for n, _ in false_premises({_S2_KEY: grown})] == [_S2_KEY], (
            f"an eighth address reusing known wording slipped through: {attack!r}"
        )


def test_witness_d39_the_new_premises_survive_unrelated_edits():
    """**Witness 2: the line-number hazard, for both new members.**"""
    shifted_s2 = "\n" * 25 + _S2_MEMBER
    shifted_visual = "\n" * 25 + _VISUAL_MEMBER
    assert false_premises({_S2_KEY: shifted_s2, _VISUAL_KEY: shifted_visual}) == []

    appended = _S2_MEMBER + "\n" + ("Ordinary prose about ammonia viscosity. " * 20) + "\n"
    assert false_premises({_S2_KEY: appended}) == []

    # Deleting one of his lines is an improvement, not a build failure: subset, not equality.
    trimmed = "\n".join(
        line for line in _S2_MEMBER.splitlines()
        if "Knock-on for director attention" not in line
    )
    assert false_premises({_S2_KEY: trimmed}) == []


def test_witness_d39_false_premise_and_inert_stay_distinguishable():
    """**Witness 3: the two conditions must not collapse into one severity.**"""
    grown = _S2_MEMBER + "\nAn eighth item needs a director ruling before S7.\n"
    assert [n for n, _ in false_premises({_S2_KEY: grown})] == [_S2_KEY]
    assert [n for n, _ in inert_allowlist({_S2_KEY: grown}) if n == _S2_KEY] == []

    quiet = "# S2 record\n\nNothing outstanding.\n"
    assert false_premises({_S2_KEY: quiet}) == []
    assert [p for p in inert_allowlist({_S2_KEY: quiet}) if p[0] == _S2_KEY] == [
        (_S2_KEY, "in the packet but carries no marker; suppressing nothing")
    ]


def test_witness_d39_a_search_built_premise_would_fail_against_the_real_seven():
    """**Witness 4: today's error, encoded so the next person cannot repeat it.**

    ``discover_director_addressed`` uses ``rx.search`` -- one match per marker per member.
    Lines 27 and 217 each fire a marker another line already fired, so a premise built
    from that view enumerates FIVE sentences and is false against the real seven. D38's
    premise was built exactly that way, one member over, and was false on arrival.
    """
    import re

    import packet_exclusions as pe

    # What `search` shows: first match per marker. This is how the evidence was made.
    search_view = {
        m.group(0)
        for rx in pe._COMPILED_MARKERS.values()
        if (m := rx.search(_S2_MEMBER)) is not None
    }
    finditer_view = {
        m.group(0)
        for rx in pe._COMPILED_MARKERS.values()
        for m in rx.finditer(_S2_MEMBER)
    }
    assert len(search_view) < len(finditer_view), (
        "if these agreed there would be no defect to encode"
    )

    # Build the premise the way the evidence was built: from the lines `search` reveals.
    lines = _S2_MEMBER.splitlines()
    search_lines = sorted(
        {_S2_MEMBER.count("\n", 0, rx.search(_S2_MEMBER).start())
         for rx in pe._COMPILED_MARKERS.values() if rx.search(_S2_MEMBER)}
    )
    search_fragments = tuple(lines[i].strip() for i in search_lines)
    finditer_lines = sorted(
        {_S2_MEMBER.count("\n", 0, m.start())
         for rx in pe._COMPILED_MARKERS.values() for m in rx.finditer(_S2_MEMBER)}
    )
    assert len(search_fragments) < len(finditer_lines), (
        f"search saw {len(search_fragments)} lines, finditer saw {len(finditer_lines)}"
    )

    assert not pe._addresses_only(search_fragments)(_S2_MEMBER), (
        "a premise built from the search view MUST be false against the real member -- "
        "that is the whole defect, and this is the regression that encodes it"
    )
    assert pe._addresses_only(tuple(lines[i].strip() for i in finditer_lines))(_S2_MEMBER)
    assert re.search(r"director", _S2_MEMBER, re.I)


def test_the_marker_set_is_narrow_and_each_shape_is_reachable():
    """Twelve shapes, each traceable to a case. A marker nothing triggers is not a check."""
    assert len(DIRECTOR_ADDRESSED_MARKERS) == 12
    probes = {
        "for-dan": "a knock-on finding for Dan to weigh",
        "director-question": "that is a Director question about the tool",
        "asks-him-to": "the report asks him to disposition it",
        "asks-him-for-a-decision": "its section 8 asks the Director eleven decisions",
        "unchecked-checklist": "- [ ] Director disposition of the findings",
        "director-must-rule": "the Director must decide the 20 bar point",
        "awaiting": "awaiting the Director's closure",
        # D37: the shapes the escaped review record actually uses.
        "pending-his-action": "OPEN pending director disposition + Sol cross-model review",
        "needs-his-action": "two findings below need a director ruling before S3",
        "for-his-attention": "Knock-on for director attention: the registry classification",
        "is-his-call": "Registry-level correction is a director decision, not a builder one",
        "his-call-to-make": "Judgment call for the director",
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
