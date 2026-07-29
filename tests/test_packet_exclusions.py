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
    DIRECTOR_ADDRESSED_MEMBERS,
    PACKAGING_TIME_DOCUMENTS,
    excluded_members,
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
