"""B1 registry framework: typed records, provenance/status vocabulary, and the
rank-eligibility rule (Phase B, Stage 1).

Every load-bearing Phase B property and correlation is registered as a frozen
record carrying an explicit **provenance class** and a **resolution status**, so
that no value can silently enter a *ranked* Phase B case. Unresolved items are
recorded with a machine-visible blocker status -- they are never invented
(no-invention policy; B0 plan Sections 2 and 4.8).

This module is stdlib-only and imports without CoolProp. Coolant values that are
DERIVED from CoolProp are stored as pinned literals with a backend citation; the
re-derivation is checked in the test suite (which skips when CoolProp is absent).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum


class Provenance(str, Enum):
    """How a value is justified (B0 plan Section 2 provenance classes)."""

    PUBLISHED = "published"
    DERIVED = "derived"
    ASSUMED = "assumed"
    CORRECTED = "corrected"
    DESIGN_VARIABLE = "design_variable"
    SENSITIVITY = "sensitivity"
    UNSUPPORTED = "unsupported"


class Status(str, Enum):
    """Resolution state of a registry entry. Every status other than ``RESOLVED``
    is a machine-visible blocker that keeps the entry out of ranked cases."""

    RESOLVED = "resolved"
    SENSITIVITY = "sensitivity"
    FUTURE = "future"
    SOURCE_REQUIRED = "source_required"
    BACKEND_REQUIRED = "backend_required"
    UNSUPPORTED = "unsupported"
    NOT_RANK_ELIGIBLE = "not_rank_eligible"
    #: Sourced, domain-fixed, and settled -- but **no executable form exists anywhere
    #: yet**. DIR-02: ``RESOLVED`` was carrying two meanings, "the sourcing question is
    #: settled" and "this can supply an evaluated value", and an entry that was only the
    #: first was admitted as though it were the second. Splitting the vocabulary is the
    #: fix; the eligibility rule below is what makes it binding.
    IMPLEMENTATION_REQUIRED = "implementation_required"


class PropertyKind(str, Enum):
    """What a property entry *is*, which governs how it may be used in a ranked case:

    - ``OPERATIONAL`` -- a directly usable value (e.g. a near-constant solid conductivity
      or a true material constant); rank-eligible when resolved and sourced.
    - ``REFERENCE_ANCHOR`` -- a single reference-state literal kept for cross-check only
      (e.g. a coolant transport property at one temperature). **Never** rank-eligible as an
      operational loop property: a ranked case must obtain per-state values via the
      corresponding backend-evaluation entry, not this static literal.
    - ``BACKEND_EVALUATION`` -- a per-state property-evaluation capability (backend + required
      inputs + validity domain), with no single scalar value; rank-eligible when resolved.
    """

    OPERATIONAL = "operational"
    REFERENCE_ANCHOR = "reference_anchor"
    BACKEND_EVALUATION = "backend_evaluation"


#: Only a RESOLVED entry may enter a ranked case.
_RANKABLE_STATUS = frozenset({Status.RESOLVED})

#: Provenance classes acceptable for a ranked case (no invented / sensitivity /
#: unsupported values).
_RANKABLE_PROVENANCE = frozenset(
    {
        Provenance.PUBLISHED,
        Provenance.DERIVED,
        Provenance.CORRECTED,
        Provenance.DESIGN_VARIABLE,
    }
)


def is_rank_eligible(provenance: Provenance, status: Status, has_value: bool) -> bool:
    """A value may enter a *ranked* Phase B case only if it is RESOLVED, carries a
    rankable provenance class, and actually has a value."""
    return status in _RANKABLE_STATUS and provenance in _RANKABLE_PROVENANCE and has_value


#: Only paths inside this package may be declared as an executable form. A registry
#: entry naming an arbitrary importable target would let a declaration reach outside
#: the project entirely, and there is no case for it: every implementation a registry
#: entry can legitimately point at is in here.
_EXECUTABLE_FORM_ROOT = "orbital_thermal."

#: Resolution cache. Resolving is an import, so it is paid once per path.
_EXECUTABLE_FORM_CACHE: dict[str, object] = {}


def resolve_executable_form(path: str) -> object | None:
    """Resolve a dotted ``module.attribute`` path to a callable, or ``None``.

    Returns ``None`` -- never raises -- when the path is empty, malformed, outside
    :data:`_EXECUTABLE_FORM_ROOT`, names a module or attribute that does not exist, or
    resolves to something that is not callable. Each of those is a declaration that
    cannot be honoured, and the caller's job is to refuse eligibility, not to crash.

    Resolution is deliberately **lazy**: the modules that implement registry entries
    import the registry (``solid_network`` and ``pumped_loop`` both do), so resolving
    at registry construction time would be circular.
    """
    path = (path or "").strip()
    if not path:
        return None
    if path in _EXECUTABLE_FORM_CACHE:
        return _EXECUTABLE_FORM_CACHE[path]

    resolved: object | None = None
    if path.startswith(_EXECUTABLE_FORM_ROOT) and "." in path:
        module_name, _, attribute = path.rpartition(".")
        try:
            import importlib

            candidate = getattr(importlib.import_module(module_name), attribute, None)
        except ImportError:
            candidate = None
        if callable(candidate):
            resolved = candidate

    _EXECUTABLE_FORM_CACHE[path] = resolved
    return resolved


def unresolved_executable_forms(
    entries: list[PropertyEntry | CorrelationEntry],
) -> list[str]:
    """Every entry whose declared ``executable_form`` does not resolve, and why.

    The loud half of the V-01 fix. :attr:`CorrelationEntry.has_executable_form` fails
    closed and says nothing; this names the offender, so a broken declaration is a
    reported defect rather than a silently de-ranked entry.
    """
    problems: list[str] = []
    for e in entries:
        declared = getattr(e, "executable_form", "")
        if not declared.strip():
            continue
        if not declared.strip().startswith(_EXECUTABLE_FORM_ROOT):
            problems.append(
                f"{e.id}: executable_form {declared!r} is outside {_EXECUTABLE_FORM_ROOT}*"
            )
        elif resolve_executable_form(declared) is None:
            problems.append(
                f"{e.id}: executable_form {declared!r} does not resolve to a callable"
            )
    return problems


@dataclass(frozen=True)
class Source:
    """A citation for a value or correlation."""

    citation: str
    locator: str = ""  # DOI, URL, table/section
    note: str = ""


@dataclass(frozen=True)
class Domain:
    """Closed validity ranges per named variable, e.g. ``{"T_K": (250.0, 350.0)}``.

    A variable that is not listed is treated as unconstrained by this entry.
    """

    ranges: dict[str, tuple[float, float]] = field(default_factory=dict)

    def out_of_domain(self, **values: float) -> list[str]:
        """Return a list of human-readable reasons for every supplied value that
        falls outside a constrained range (empty list == in domain)."""
        bad: list[str] = []
        for name, x in values.items():
            if name in self.ranges:
                lo, hi = self.ranges[name]
                if not (math.isfinite(x) and lo <= x <= hi):
                    bad.append(f"{name}={x} outside [{lo}, {hi}]")
        return bad

    def contains(self, **values: float) -> bool:
        """True iff every supplied, constrained value is within its range."""
        return not self.out_of_domain(**values)


@dataclass(frozen=True)
class PropertyEntry:
    """A single material/fluid property (SI units). ``value`` is ``None`` when the
    entry is unresolved; the status then records why it is blocked."""

    id: str
    name: str
    material: str
    quantity: str
    provenance: Provenance
    status: Status
    kind: PropertyKind = PropertyKind.OPERATIONAL
    value: float | None = None
    units: str = ""
    domain: Domain = field(default_factory=Domain)
    source: Source | None = None
    backend: str = ""
    version: str = ""
    applicability: str = ""
    note: str = ""

    @property
    def rank_eligible(self) -> bool:
        # A single-state reference literal is never an operational ranked value; a ranked
        # case must use the backend-evaluation entry for per-state properties.
        if self.kind is PropertyKind.REFERENCE_ANCHOR:
            return False
        has_value = self.value is not None or self.kind is PropertyKind.BACKEND_EVALUATION
        return is_rank_eligible(self.provenance, self.status, has_value)


@dataclass(frozen=True)
class CorrelationEntry:
    """A thermal or hydraulic correlation. ``evaluate`` is an optional callable; a
    correlation can be rank-eligible on its source/domain even before its
    executable form is wired in (that happens in B2/B3)."""

    id: str
    name: str
    kind: str  # nusselt | friction | minor_loss | maldistribution | spreading | contact
    provenance: Provenance
    status: Status
    formula: str = ""
    domain: Domain = field(default_factory=Domain)
    source: Source | None = None
    evaluate: object = None  # Callable | None
    applicability: str = ""
    note: str = ""
    # S1 two-phase extension: optional, backward-compatible microgravity/gravity-basis
    # metadata for HTC/dP/CHF correlations (rankings are 1g reference-only; ISS/microgravity
    # literature shows gravity-dependent behavior). Defaults keep all existing entries valid.
    microgravity_validated: bool | None = None
    gravity_basis: str = ""
    rank_scope: str = ""
    limitation: str = ""
    # OTB-G001 fix: the enforceable applicability spec (fluid / geometry / orientation /
    # regime / provenance). Optional and defaulting to None, so every Stage-1 B1 entry
    # stays valid; `None` means "declares no enforceable applicability", which is
    # deliberately distinguishable from an empty spec that declares none.
    applicability_spec: object = None  # applicability.Applicability | None
    #: Where the executable form lives when it is not the ``evaluate`` callable --
    #: e.g. ``"orbital_thermal.solid_network.spreading_resistance"``. Some B1 entries
    #: are evaluated by a module function rather than by a callable hung on the entry;
    #: before DIR-02 that was indistinguishable from "not implemented at all", because
    #: both simply had ``evaluate=None``. Naming the location is what separates them.
    executable_form: str = ""

    @property
    def has_executable_form(self) -> bool:
        """Whether an executable form can actually be **reached**.

        V-01: the first version of this returned true for any non-empty
        ``executable_form`` string, so ``"x"`` -- or a well-formed but non-existent
        dotted path -- made an entry rank-eligible. That admits a *declaration* where
        the rule needs a *fact*, which is the same shape as the defect it was written
        to close, one level down.

        A declared path is now resolved (see :func:`resolve_executable_form`). The
        resolution is **lazy and cached**: doing it while the registry module is being
        built would be circular, because the implementing modules import the registry.

        Resolution failure returns ``False`` rather than raising, so this stays a
        total predicate and the boundary **fails closed** -- an entry whose declaration
        does not resolve simply cannot rank. That is deliberately quiet, and is paired
        with a registry-integrity test that fails **loudly** and names the offender;
        see the reasoning recorded in ``OTB-G002_FIXES_REPORT.md``.
        """
        if self.evaluate is not None:
            return True
        return resolve_executable_form(self.executable_form) is not None

    @property
    def rank_eligible(self) -> bool:
        """Whether this entry may enter a ranked case.

        **DIR-02 -- closed generically, at the boundary.** An entry that cannot supply
        an evaluated value is not rank-eligible, full stop. This is deliberately *not*
        opt-in: the previous version gated on
        ``applicability_spec.requires_executable_form``, so an entry simply not
        declaring that flag was admitted -- which is the same call-site-not-boundary
        shape that produced OTB-G001-FIXES, and DIR-02 is its third occurrence.

        "Can supply a value" means :attr:`has_executable_form`, which is true for a
        callable on the entry *or* a named module implementation. That distinction is
        what lets the rule be generic without demoting the B1 entries whose executable
        form has always lived in a module (``thermal.spreading_resistance``,
        ``hydraulic.minor_losses``) -- they were never unimplemented, only
        undocumented, and the fix records where they live rather than changing what
        they do.
        """
        if not is_rank_eligible(self.provenance, self.status, has_value=True):
            return False
        return self.has_executable_form


class NotRankEligibleError(ValueError):
    """Raised when a ranked Phase B case references a non-rank-eligible entry, or
    uses a correlation outside its validity domain."""


def assert_rank_eligible(entry: PropertyEntry | CorrelationEntry, *, context: str = "") -> None:
    """Guard for the Phase B ranking path: raise unless ``entry`` may be ranked."""
    if not entry.rank_eligible:
        prefix = f"{context}: " if context else ""
        raise NotRankEligibleError(
            f"{prefix}registry entry '{entry.id}' is not rank-eligible "
            f"(provenance={entry.provenance.value}, status={entry.status.value}). "
            "A ranked Phase B case may not use it; resolve the entry, or run the case "
            "as a labelled sensitivity / parametric result."
        )


def assert_in_domain(
    entry: PropertyEntry | CorrelationEntry, *, context: str = "", **values: float
) -> None:
    """Raise unless every supplied value is within ``entry``'s validity domain."""
    bad = entry.domain.out_of_domain(**values)
    if bad:
        prefix = f"{context}: " if context else ""
        raise NotRankEligibleError(
            f"{prefix}'{entry.id}' evaluated outside its validity domain: {', '.join(bad)}"
        )


def blockers(entries: list[PropertyEntry | CorrelationEntry]) -> list[str]:
    """List, for reporting, every entry that is not rank-eligible and why."""
    return [
        f"{e.id}: provenance={e.provenance.value}, status={e.status.value}"
        for e in entries
        if not e.rank_eligible
    ]
