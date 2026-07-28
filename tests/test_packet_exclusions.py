"""OTB-G003 F-08: the packaging-time half of C10, and its list must stay honest."""

from __future__ import annotations

import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from packet_exclusions import (  # noqa: E402
    DIRECTOR_ADDRESSED_MEMBERS,
    PACKAGING_TIME_DOCUMENTS,
    excluded_members,
    unknown_exclusions,
)


def _assembled() -> list[str]:
    """What a packager is actually about to ship: repo members AND gate-record docs.

    The distinction matters: ``OTB-G003_S4_SCOPE_PROPOSAL.md`` is not tracked, so a
    filter run over ``git ls-files`` alone would never see the sharpest entry on the
    list. This test caught that.
    """
    return _tracked() + list(PACKAGING_TIME_DOCUMENTS)


def _tracked() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=pathlib.Path(__file__).resolve().parents[1],
        capture_output=True, text=True, check=True,
    ).stdout
    return [p for p in out.splitlines() if p.strip()]


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
    """
    repo = pathlib.Path(__file__).resolve().parents[1]
    registry = (repo / "src/orbital_thermal/registry/two_phase.py").read_text(encoding="utf-8")
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
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "scripts/packet_exclusions.py").read_text(encoding="utf-8")
    for forbidden in ("unlink", "remove(", "git rm", "rewrite", "filter-branch"):
        assert forbidden not in src
