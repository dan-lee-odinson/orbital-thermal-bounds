"""Phase B, Stage 1 property / source / correlation registry (milestone B1).

Every load-bearing Phase B property and correlation is registered with an explicit
provenance class and a resolution status. The single invariant this package
enforces: **a non-rank-eligible entry cannot silently enter a ranked Phase B
case** (use :func:`assert_rank_eligible`). Unresolved items are recorded with a
machine-visible blocker status, never invented.

This package is stdlib/numpy-light and imports without CoolProp. Resolved coolant
transport values are DERIVED from CoolProp 7.2.0 and re-checked in the test suite.

Typical use::

    from orbital_thermal import registry
    e = registry.get("coolant.ammonia.density")
    registry.assert_rank_eligible(e, context="B5 case")   # ok
    registry.assert_rank_eligible(registry.get("coolant.co2.loop_use"))  # raises
"""

from __future__ import annotations

from .applicability import (
    UNCONSTRAINED,
    Applicability,
    Axis,
    Consequence,
    DomainProvenance,
    Violation,
    worst,
)
from .correlations import CORRELATIONS, CORRELATIONS_BY_ID
from .properties import PROPERTIES, PROPERTIES_BY_ID
from .provenance import (
    CorrelationEntry,
    Domain,
    NotRankEligibleError,
    PropertyEntry,
    PropertyKind,
    Provenance,
    Source,
    Status,
    assert_in_domain,
    assert_rank_eligible,
    blockers,
    is_rank_eligible,
)
from .two_phase import (
    COOLPROP_PIN,
    TWO_PHASE_BY_ID,
    TWO_PHASE_CORRELATIONS,
    TWO_PHASE_PROPERTIES,
)

__all__ = [
    "Applicability",
    "Axis",
    "Consequence",
    "DomainProvenance",
    "Violation",
    "UNCONSTRAINED",
    "worst",
    "Provenance",
    "Status",
    "PropertyKind",
    "Source",
    "Domain",
    "PropertyEntry",
    "CorrelationEntry",
    "NotRankEligibleError",
    "assert_rank_eligible",
    "assert_in_domain",
    "blockers",
    "is_rank_eligible",
    "PROPERTIES",
    "CORRELATIONS",
    "TWO_PHASE_CORRELATIONS",
    "TWO_PHASE_PROPERTIES",
    "TWO_PHASE_BY_ID",
    "COOLPROP_PIN",
    "ALL_ENTRIES",
    "get",
    "rank_eligible_entries",
    "blocked_entries",
    "summary",
]

#: Every registered entry (properties + correlations).
ALL_ENTRIES: list[PropertyEntry | CorrelationEntry] = [
    *PROPERTIES,
    *CORRELATIONS,
    *TWO_PHASE_PROPERTIES,
    *TWO_PHASE_CORRELATIONS,
]

_BY_ID: dict[str, PropertyEntry | CorrelationEntry] = {
    **PROPERTIES_BY_ID,
    **CORRELATIONS_BY_ID,
    **TWO_PHASE_BY_ID,
}


def get(entry_id: str) -> PropertyEntry | CorrelationEntry:
    """Return the entry with ``entry_id`` or raise ``KeyError``."""
    return _BY_ID[entry_id]


def rank_eligible_entries() -> list[PropertyEntry | CorrelationEntry]:
    """Entries that may enter a ranked Phase B case."""
    return [e for e in ALL_ENTRIES if e.rank_eligible]


def blocked_entries() -> list[PropertyEntry | CorrelationEntry]:
    """Entries that are registered but not rank-eligible (with a blocker status)."""
    return [e for e in ALL_ENTRIES if not e.rank_eligible]


def summary() -> dict[str, int]:
    """Counts by status, for the completion report / registry table header."""
    counts: dict[str, int] = {}
    for e in ALL_ENTRIES:
        counts[e.status.value] = counts.get(e.status.value, 0) + 1
    counts["rank_eligible"] = len(rank_eligible_entries())
    counts["total"] = len(ALL_ENTRIES)
    return counts
