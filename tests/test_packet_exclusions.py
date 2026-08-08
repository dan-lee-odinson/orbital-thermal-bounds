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
    # D44: the ten mastery-ledger entries carrying a task assigned to him.
    "verification/mastery-ledger/entries/architecture-cases.md",
    "verification/mastery-ledger/entries/beta-angle-albedo-model.md",
    "verification/mastery-ledger/entries/coupled-steady-state-solution.md",
    "verification/mastery-ledger/entries/earth-view-factors.md",
    "verification/mastery-ledger/entries/emitting-face-convention.md",
    "verification/mastery-ledger/entries/radiative-equilibrium-and-net-rejection.md",
    "verification/mastery-ledger/entries/radiator-attitude-and-sun-shielding.md",
    "verification/mastery-ledger/entries/single-phase-pumped-loop.md",
    "verification/mastery-ledger/entries/solid-thermal-network.md",
    "verification/mastery-ledger/entries/spectral-separation-of-loads.md",
)

#: The two D44 members that assign him nothing, in the shapes their real files carry.
_TWO_PHASE_KEY = ("verification/mastery-ledger/entries/"
                  "two-phase-flow-boiling-heat-acquisition.md")
_TEMPLATE_KEY = "verification/mastery-ledger/template.md"

_TWO_PHASE_MEMBER = "\n".join((
    "# Two-phase flow boiling",
    "",
    "## Explanation in the director's own words",
    "",
    "TODO (director)",
    "",
    "## Reproduction method",
)) + "\n"

_TEMPLATE_MEMBER = "\n".join((
    "# <entry title>",
    "",
    "## Explanation in the director's own words",
    "",
    "<Written by the director, in his own words, without model",
    "drafting. Leave as `TODO (director)` until done -- do not fabricate.>",
)) + "\n"

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
def _state_md(*awaiting_values: str, extra: str = "") -> str:
    """The shipped STATE.md shape, with whatever awaiting-values it is given.

    **D41 changed what falsifies, not how the fixture is built.** F-04 §2.2's clause -- the
    fixture derives from the member shape so a real Director action cannot hide behind a
    hand-written example -- is untouched: the rows are still generated from the values
    passed in, and the values are still free to be anything a real ledger would produce.

    What changed is which difference counts. A non-``none`` value is a CORRECT generated row
    (``status: closed`` is the Director's field, so a built-and-verified finding waits there
    by design), and the old assertion called that falsifying. ``extra`` is how the fixture
    now expresses the thing that really is falsifying: a Director-addressed line of a shape
    this file does not generate. Both cases come from the same generator, so neither can be
    special-cased -- which is the property §2.2 was protecting.
    """
    lines = ["# STATE", ""]
    for value in awaiting_values:
        lines += [
            f"- **Built and verified, awaiting the Director's `status: closed`:** {value}",
        ]
    if extra:
        lines += ["", extra]
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
    all_none = _state_md("none", "none")
    a_real_finding = _state_md("none", "F-01")
    a_new_kind_of_address = _state_md(
        "none", "none", extra="Two items need a director ruling before this ships."
    )

    assert discover_director_addressed({"STATE.md": all_none}) == []
    assert discover_director_addressed({"STATE.md": a_real_finding}) == []

    # **A different VALUE is a correct generated row and must NOT falsify (D41).** The
    # old assertion said the opposite, and the shipped file had carried F-01 all along.
    assert false_premises({"STATE.md": all_none}) == []
    assert false_premises({"STATE.md": a_real_finding}) == [], (
        "a built-and-verified finding waiting on `status: closed` is STATE.md being "
        "correct; failing the build for it is the premise that was false on arrival"
    )

    # **A different KIND of line does falsify** -- an address this file does not generate.
    bad = false_premises({"STATE.md": a_new_kind_of_address})
    assert [n for n, _ in bad] == ["STATE.md"], (
        "a hand-added question to the Director is not a generated closure-status row, "
        "and the premise must not survive one"
    )
    assert "premise is false" in bad[0][1]

    # The §2.2 property itself: the fixture derives, so the falsifying case and the
    # holding case come from one generator and neither can be quietly special-cased.
    assert a_real_finding != all_none and a_new_kind_of_address != all_none
    assert "F-01" in a_real_finding and "F-01" not in all_none


def test_witness_d37_a_false_allowlist_premise_is_fatal_not_advisory():
    """**Witness 3: a false premise FAILS, and it fails differently from an inert entry.**

    Two conditions that look similar and are not: an entry exempting nothing is advisory
    (:func:`inert_allowlist`), an entry exempting something on a false premise is fatal
    (:func:`false_premises`). Collapsing them would let a false premise ship as a warning.
    """
    def for_state(pairs):
        return [p for p in pairs if p[0] == "STATE.md"]

    # D41: the falsifying case is a line STATE.md does not generate, not a new VALUE.
    dirty = _state_md("none", extra="Two items need a director ruling before this ships.")
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
        "> **Judgment call for the director.** §2 of the handoff bars implementing",
        "> from a secondary source.",
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
        "**Not closable by the builder.** Requires: (i) director disposition of **F1** and **F2**; (ii) Sol's re-review.",
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
    # D43: unwrapped, as the real line 874 is. The re-keyed fragment now carries the
    # clause that precedes the policy sentence, and a fixture wrap would orphan it.
    '        "Author cross-check is source-author review, not "\n'
    '        "independent external validation. Public documentation requires project-director approval."\n'
    "    ),\n"
    "}\n"
)


#: Registered into the member set so the two D39 exemptions are EXERCISED by
#: :func:`inert_allowlist` and :func:`false_premises` rather than merely declared. An
#: allowlist entry whose member never appears in any fixture is an entry nothing tests.
_MEMBER_TEXT[_VISUAL_KEY] = _VISUAL_MEMBER
_MEMBER_TEXT[_S2_KEY] = _S2_MEMBER


#: The two D41 members. Both are review records that quote the marker vocabulary in order
#: to rule on it, so their fixtures must carry the real quoting lines.
_G004_DISP_KEY = "OTB-G004_dispositioned.md"
_G004_FIND_KEY = "findings-OTB-G004.yaml"

#: Each addressed line is kept UNWRAPPED, as the real member has them. Hand-wrapping put
#: the fragment on one line and the marker match on the next, so no single line carried
#: both and the premise failed -- the third time a fixture's line breaks have been the
#: bug rather than the key. The real member's lines 174-183 and 219-221 are long single
#: lines; the fixture mirrors that.
_G004_DISP_MEMBER = "\n".join(
    (
        "# OTB-G004 dispositioned",
        "",
        "**F-04.** The marker regex is case-sensitive. Run against the shipped text: 'asks the Director to rule' fires",
        "one marker; 'need a director ruling before S3 proceeds', 'OPEN pending director disposition' and",
        "'Judgment call for the director.' each fire ZERO. That is why Cowork's coverage sweep returned 0 unaccounted.",
        "",
        "STATE.md separately names a finding awaiting the Director's closure. The regression fixture hard-codes a none value, so it cannot notice.",
        "",
        "This is _COUPLING_SUBJECT, 'asks Dan to rule' and 'asks the Director eleven decisions'.",
        "",
        "**Finding.** The S2 review record is explicitly pending Director disposition, places a judgment call before him.",
        "",
        "**Evidence.** The record says two findings need a Director ruling, lines 19-27 name pending Director review.",
    )
) + "\n"

_G004_FIND_MEMBER = "\n".join(
    (
        "review:",
        "  gate: OTB-G004",
        "findings:",
        "  - id: F-04",
        "    evidence: >-",
        "      The record says two findings need a Director ruling, lines 19-27 name "
        "pending Director review, and",
        "      the packaging allowlist names F-01 as awaiting the Director's status field "
        "while the fixture tests none.",
    )
) + "\n"

_MEMBER_TEXT[_G004_DISP_KEY] = _G004_DISP_MEMBER
_MEMBER_TEXT[_G004_FIND_KEY] = _G004_FIND_MEMBER
#: D44's two, so their exemptions are exercised by the staleness and premise checks.
_MEMBER_TEXT[_TWO_PHASE_KEY] = _TWO_PHASE_MEMBER
_MEMBER_TEXT[_TEMPLATE_KEY] = _TEMPLATE_MEMBER


def test_witness_d41_state_md_holds_on_a_new_value_and_fails_on_a_new_kind_of_line():
    """**D41's replacement premise, both directions, from the derived fixture.**

    Green on the first is the old defect restated; red on the second is D41 unimplemented.
    """
    assert false_premises({"STATE.md": _state_md("none", "F-01", "F-02, F-03")}) == []
    grown = _state_md("none", extra="Judgment call for the director on the bore bound.")
    assert [n for n, _ in false_premises({"STATE.md": grown})] == ["STATE.md"]


def test_witness_d41_the_two_new_premises_hold_and_fail_on_one_more_address():
    """Each new entry must name itself, and only itself, when its member grows."""
    both = {_G004_DISP_KEY: _G004_DISP_MEMBER, _G004_FIND_KEY: _G004_FIND_MEMBER}
    assert false_premises(both) == []

    for key, member in both.items():
        grown = dict(both)
        grown[key] = member + "\n\nOPEN pending director disposition of the new item.\n"
        assert [n for n, _ in false_premises(grown)] == [key], (
            f"{key} gained an address and must be the only member reported"
        )


def test_witness_d41_the_new_fragments_resist_a_fresh_address_reusing_their_wording():
    """**Cowork's draft fragments were quotations of marker wording. These are not.**

    Attacked with probes each asserted to fire a marker first -- a probe that fires
    nothing is not an attack, and one in the first run read as a slipped key when the
    member had simply not gained an address.
    """
    import packet_exclusions as pe

    attacks = (
        "Judgment call for the director on the 20 bar point.",
        "This asks the Director to rule on the axis choice.",
        "Two more findings need a director ruling before S5.",
        "OPEN pending director disposition of the new item.",
        "S7 is awaiting the Director's closure on eta_pump.",
        "New rows are pending Director review before S6.",
        "That is a Director question about the tooling.",
    )
    for attack in attacks:
        assert any(rx.search(attack) for rx in pe._COMPILED_MARKERS.values()), (
            f"probe fires no marker, so it is not an attack: {attack!r}"
        )
        for key, member in (
            (_G004_DISP_KEY, _G004_DISP_MEMBER),
            (_G004_FIND_KEY, _G004_FIND_MEMBER),
            ("STATE.md", _state_md("none")),
        ):
            grown = member + "\n\n" + attack + "\n"
            assert [n for n, _ in false_premises({key: grown})] == [key], (
                f"{key}: an address reusing known wording slipped through: {attack!r}"
            )


def test_witness_d41_a_search_built_state_premise_would_fail_against_the_real_twelve():
    """**Witness 4: the search gap has now produced two false premises in three rounds.**

    ``STATE.md`` is the sharpest case in the project: ``rx.search`` reports ONE addressed
    line because all eleven generated rows fire the same marker. A premise built from that
    view describes one row and is false against the other eleven.
    """
    import packet_exclusions as pe

    member = _state_md("none", "F-01", "none", "none")
    lines = member.splitlines()

    search_lines = sorted({
        member.count("\n", 0, m.start())
        for rx in pe._COMPILED_MARKERS.values() if (m := rx.search(member))
    })
    finditer_lines = sorted({
        member.count("\n", 0, m.start())
        for rx in pe._COMPILED_MARKERS.values() for m in rx.finditer(member)
    })
    assert len(search_lines) < len(finditer_lines), (
        "if search and finditer agreed on this member there would be no defect to encode"
    )

    search_premise = pe._addresses_only(tuple(lines[i].strip() for i in search_lines))
    assert not search_premise(member), (
        "a premise built from the search view MUST be false against the real member -- "
        "this is the regression that stops the next person building one the same way"
    )
    assert pe._addresses_only(tuple(lines[i].strip() for i in finditer_lines))(member)


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


#: Sol's F-03 sentence, verbatim. A genuinely new Director-addressed line, about the
#: dryout basis rather than the CHF classification, which contained the shipped registry
#: key word for word and left the premise holding.
_SOL_F03_SENTENCE = (
    "The incomplete dryout basis remains open; it is a finding for director disposition, "
    "not a repair this build owns"
)

#: The `TODO (director)` wording as it actually ships, from a mastery-ledger entry --
#: not a synthetic probe. The regression that matters is written from the text that
#: escaped, and 22 lines of this shape have shipped in every packet since `OTB-G001`.
_TODO_SHIPPED_LINES = (
    "`TODO (director)` -- to be written without model drafting before status advances to",
    "- `TODO (director)`: plain-language explanation of the case-space classification and",
    "TODO (director)",
    "drafting. Leave as `TODO (director)` until done -- do not fabricate.>",
)


def test_witness_d43_sols_sentence_fails_the_registry_premise():
    """**Witness 1: the exact wording Sol found, not a paraphrase of it.**

    It fires a marker -- asserted first, because a probe that fires nothing is not an
    address and holding would be correct -- and it must now falsify the registry premise.
    Before the re-key it did not, and that is the whole of F-03.
    """
    import packet_exclusions as pe

    assert any(rx.search(_SOL_F03_SENTENCE) for rx in pe._COMPILED_MARKERS.values()), (
        "the sentence must be a Director-addressed line or there is nothing to catch"
    )
    key = "src/orbital_thermal/registry/two_phase.py"
    grown = _REGISTRY_MEMBER + "\n# " + _SOL_F03_SENTENCE + "\n"
    assert [n for n, _ in false_premises({key: grown})] == [key], (
        "a new Director-addressed line about a different subject must fail the premise; "
        "the old key was contained in it verbatim and the build stayed green"
    )
    # And the member without it still holds, so the failure is the sentence's doing.
    assert false_premises({key: _REGISTRY_MEMBER}) == []


def test_witness_d43_no_shipped_key_is_pure_process_vocabulary():
    """**The screen: a floor on key strength, and it catches what the length test missed.**

    Not a certificate. It passes keys a reading still flags -- a standing policy sentence
    is lexically specific and semantically reusable. Passing means "not obviously weak".
    """
    import packet_exclusions as pe

    for name, known in (
        ("registry", pe._REGISTRY_KNOWN_ADDRESSES),
        ("visual_api", pe._VISUAL_API_KNOWN_ADDRESSES),
        ("S2 record", pe._S2_RECORD_KNOWN_ADDRESSES),
        ("STATE.md", pe._STATE_KNOWN_ADDRESSES),
        ("G004 dispositioned", pe._G004_DISPOSITIONED_KNOWN_ADDRESSES),
        ("G004 findings", pe._G004_FINDINGS_KNOWN_ADDRESSES),
    ):
        assert pe.weak_keys(known) == [], f"{name} carries a pure-process-vocabulary key"
        assert pe.inert_screen_exemptions(known) == [], (
            f"{name} has a screen exemption that is no longer exempting anything"
        )


def test_witness_d43_the_screen_separates_the_recorded_pair_and_catches_sols_key():
    """The screen must not be vacuous: it has to fail on the shapes it was built from."""
    import packet_exclusions as pe

    assert pe.weak_keys(("is a director decision",)), (
        "the D40 withdrawn key must be flagged or the screen measures nothing"
    )
    assert pe.weak_keys(("it is a finding for director disposition",)), (
        "Sol's key must be flagged -- the length test could not, and that is the point"
    )
    assert pe.weak_keys(
        ("Registry-level correction is a director decision, not a builder one",)
    ) == [], "the D40 replacement must pass, or the screen condemns good keys too"


def test_witness_d43_the_todo_marker_fires_on_the_real_shipped_wording():
    """**Witness 3: from the text that escaped, not from a synthetic probe.**

    Twenty-two lines of this shape have shipped in every packet since `OTB-G001` and no
    marker has ever seen one: they carry no requesting verb and no pending-state word,
    only an imperative label naming him.
    """
    for line in _TODO_SHIPPED_LINES:
        found = discover_director_addressed({"verification~ledger~entry.md": line})
        assert found, f"the shipped wording must be discovered: {line!r}"
        assert "todo-for-him" in {f[1] for f in found}

    # Spacing tolerance, since the shape varies across entries.
    for variant in ("TODO(director)", "todo ( DIRECTOR )", "Todo (Director)"):
        assert discover_director_addressed({"m.md": variant}), variant


def test_witness_d43_the_todo_marker_is_word_bounded():
    """**Witness 4: the `re.I` trap again -- a case-blind pattern needs its bound.**

    ``director`` must be followed by optional space and then the closing parenthesis, so
    the longer words cannot satisfy it.
    """
    for benign in (
        "TODO (directory) -- move these files into place",
        "TODO (directive) from the style guide",
        "TODO (directorate) review of the schedule",
        "TODO (direct) fix the sign convention",
        "a directory listing for the director",
    ):
        assert discover_director_addressed({"ordinary.md": benign}) == [], (
            f"{benign!r} is not a task assigned to him and must stay quiet"
        )


def test_witness_d43_the_surfaced_members_are_reported_not_silenced():
    """**Witness 5: green by REPORTING them, never by their absence.**

    D38's rule stands -- nothing may be quieted by an entry the Director has not ruled on
    -- so the members the new marker surfaces must still come back as unaccounted. A test
    that passed because they had been enumerated or allowlisted would be the inversion of
    his ruling, so both lists are asserted not to contain them.
    """
    # D44 RULED ON ALL TWELVE, so the assertion this test used to make -- that they are
    # in neither list -- is now false BY RULING rather than by oversight. The property
    # it was protecting survives and is what is asserted instead: nothing the marker
    # surfaces is quiet unless a ruling put it there, and every one of them carries the
    # evidence for that ruling. A member silenced with no reason would still fail here.
    ruled_excluded = "verification/mastery-ledger/entries/architecture-cases.md"
    ruled_exempt = "verification/mastery-ledger/template.md"

    assert ruled_excluded in DIRECTOR_ADDRESSED_MEMBERS
    assert "plain-language explanation of the case-space classification" in (
        DIRECTOR_ADDRESSED_MEMBERS[ruled_excluded]
    ), "an excluded member must carry the line that makes it qualify, not just a name"

    assert ruled_exempt in QUOTATION_ALLOWLIST
    assert callable(QUOTATION_ALLOWLIST[ruled_exempt].holds), (
        "an exempted member must carry a premise the build checks, not prose alone"
    )

    # And a member the marker surfaces that NOBODY has ruled on is still reported.
    unruled = {"verification/mastery-ledger/entries/not-yet-ruled.md":
               "`TODO (director)`: plain-language explanation of something new"}
    assert {n for n, _, _, _ in discover_director_addressed(unruled)} == set(unruled), (
        "a surfaced member with no ruling behind it must still come back unaccounted"
    )


_D44_EXCLUDED = {
    "architecture-cases.md": "case-space classification and the modeled-component-mass",
    "beta-angle-albedo-model.md": "sub-point albedo factor and its beta = 90 limitation",
    "coupled-steady-state-solution.md": "chip heat through R1/R2; pump heat into R3",
    "earth-view-factors.md": "~12x underestimate of the exact ~0.258",
    "emitting-face-convention.md": "why emitting area, not planform, is correct",
    "radiative-equilibrium-and-net-rejection.md": "plain-language explanation.",
    "radiator-attitude-and-sun-shielding.md": "attitude/shielding assumption",
    "single-phase-pumped-loop.md": "hydraulic-into-fluid pump-heat convention",
    "solid-thermal-network.md": "spreading resistance and the isothermal vs convective",
    "spectral-separation-of-loads.md": "why two bands (and Kirchhoff) are needed",
}


def test_witness_d44_each_of_the_ten_is_dropped_for_its_own_line():
    """**Witness 1: the pair, and the reason must quote the member's own Shape-B line.**

    The ten were split from the twelve on a distinction in the text: they carry a task
    assigned to him WITH CONTENT, their two siblings do not. A reason that did not quote
    that line would not record which distinction was applied.
    """
    dropped = dict(excluded_members(_assembled()))
    for name, quoted in _D44_EXCLUDED.items():
        member = f"verification/mastery-ledger/entries/{name}"
        assert member in dropped, f"{member} was ruled excluded and is not dropped"
        assert quoted in dropped[member], (
            f"{member}'s reason must quote its own assigned-task line; got "
            f"{dropped[member]!r}"
        )
        assert len(dropped[member]) > 40


def test_witness_d44_the_equality_key_rejects_what_a_containment_would_accept():
    """**Witness 3, and the reason the `Exact` type exists at all.**

    ``two-phase-flow-boiling-heat-acquisition.md:102`` is the bare token and nothing
    else. A containment key on that fragment is the marker's own wording, so it is
    satisfied by any line containing it -- including a task assigned to him. This drives
    both key shapes over the same mutated member and requires them to DISAGREE. If they
    ever agree, the equality key has stopped doing anything and the next person writes
    the containment.
    """
    import packet_exclusions as pe

    gains_a_task = _TWO_PHASE_MEMBER + "\nTODO (director): explain the CHF gate\n"

    equality = pe._addresses_only((pe.Exact("TODO (director)"),))
    containment = pe._addresses_only(("TODO (director)",))

    assert equality(_TWO_PHASE_MEMBER), "the real member must hold under equality"
    assert containment(_TWO_PHASE_MEMBER), "and under containment, before the mutation"

    assert not equality(gains_a_task), (
        "a task assigned to him is not an empty field; the equality key must fail"
    )
    assert containment(gains_a_task), (
        "a containment key ACCEPTS the task line -- that is instance twenty-one, and "
        "the whole reason this entry is keyed by equality"
    )

    # And the shipped entry is the equality one, not the containment one.
    assert [n for n, _ in false_premises({_TWO_PHASE_KEY: gains_a_task})] == [
        _TWO_PHASE_KEY]


def test_witness_d44_a_second_bare_placeholder_is_not_a_new_address():
    """Equality accepts another EMPTY field, and that is D41's finding, not a gap.

    Naming a field he will one day fill is not addressing him. A second field of the
    identical shape is the same class of content -- as a second generated `STATE.md`
    closure row is. Stated as a test so the acceptance is a decision, not an accident.
    """
    second_field = _TWO_PHASE_MEMBER + "\n## Another section\n\nTODO (director)\n"
    assert false_premises({_TWO_PHASE_KEY: second_field}) == []


def test_witness_d44_the_two_new_premises_fail_on_one_more_address():
    """**Witness 2.** Each new entry must name itself, and only itself, when it grows."""
    both = {_TWO_PHASE_KEY: _TWO_PHASE_MEMBER, _TEMPLATE_KEY: _TEMPLATE_MEMBER}
    assert false_premises(both) == []

    grown = dict(both)
    grown[_TWO_PHASE_KEY] = _TWO_PHASE_MEMBER + "\nTODO (director): write the CHF note\n"
    assert [n for n, _ in false_premises(grown)] == [_TWO_PHASE_KEY]

    grown = dict(both)
    grown[_TEMPLATE_KEY] = _TEMPLATE_MEMBER + (
        "\n- `TODO (director)`: plain-language explanation of the new convention.\n")
    assert [n for n, _ in false_premises(grown)] == [_TEMPLATE_KEY]


def test_witness_d44_the_two_new_premises_survive_unrelated_edits():
    """Blank lines, appended prose, and a deleted address (D40: subset, not equality)."""
    both = {_TWO_PHASE_KEY: "\n" * 20 + _TWO_PHASE_MEMBER,
            _TEMPLATE_KEY: _TEMPLATE_MEMBER + "\n" + ("Ordinary prose. " * 30) + "\n"}
    assert false_premises(both) == []

    trimmed = "\n".join(line for line in _TWO_PHASE_MEMBER.splitlines()
                        if line.strip() != "TODO (director)")
    assert false_premises({_TWO_PHASE_KEY: trimmed}) == []


def test_witness_d44_false_premise_and_inert_stay_distinguishable():
    """**Witness 4.** The two conditions must not collapse into one severity."""
    grown = _TWO_PHASE_MEMBER + "\nTODO (director): write the CHF note\n"
    assert [n for n, _ in false_premises({_TWO_PHASE_KEY: grown})] == [_TWO_PHASE_KEY]
    assert [p for p in inert_allowlist({_TWO_PHASE_KEY: grown})
            if p[0] == _TWO_PHASE_KEY] == []

    quiet = "# Two-phase flow boiling\n\nNothing outstanding.\n"
    assert false_premises({_TWO_PHASE_KEY: quiet}) == []
    assert [p for p in inert_allowlist({_TWO_PHASE_KEY: quiet})
            if p[0] == _TWO_PHASE_KEY] == [
        (_TWO_PHASE_KEY, "in the packet but carries no marker; suppressing nothing")]


def test_witness_d44_an_exact_key_is_not_screened_as_weak_vocabulary():
    """The screen asks what a NEW address could satisfy; equality already answers it.

    ``TODO (director)`` is pure marker wording, so as a CONTAINMENT key it is exactly
    what :func:`weak_keys` exists to flag -- and it is flagged. As an ``Exact`` key only
    a byte-identical line satisfies it, so the question is closed by the matching rule
    and screening it on vocabulary would condemn the one shape that cannot be weak.
    """
    import packet_exclusions as pe

    assert pe.weak_keys(("TODO (director)",)), (
        "as a containment key this is weak, and the screen must say so"
    )
    assert pe.weak_keys((pe.Exact("TODO (director)"),)) == [], (
        "as an equality key it is not weak, and the screen must not condemn it"
    )


def test_the_marker_set_is_narrow_and_each_shape_is_reachable():
    """Twelve shapes, each traceable to a case. A marker nothing triggers is not a check."""
    assert len(DIRECTOR_ADDRESSED_MARKERS) == 13
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
        "todo-for-him": "`TODO (director)` -- to be written before status advances",
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
