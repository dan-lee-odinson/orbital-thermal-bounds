"""Binding applicability enforcement for registry correlations (OTB-G001 fix).

**The defect class this closes.** Five of the ten OTB-G001 findings were the same
defect wearing different clothes: *a declared constraint that is recorded but never
enforced.* The fluid basis lived in a docstring and a note; the geometry basis
("tubes and annuli") lived in a title and nowhere else (DEBTS D-9); the turbulent
basis of the Dittus-Boelter term was documented and never checked; the provenance of
a CHF value was described in prose while any bare float was accepted.

Writing five patches would have left the class alive -- the next declared-but-unchecked
axis would simply be the sixth. This module is the single mechanism, and every axis a
correlation constrains goes through it.

**The rule that makes it binding.** An axis that a correlation *declares* but which the
caller does *not* state is itself a violation, consequence ``BLOCK``. Silence is not
consent. Without that rule, "declared but never enforced" walks straight back in as
"declared, enforced only when someone remembers to pass it" -- which is what D-9
already is.

**Consequences, not annotations.** ``check`` returns typed :class:`Violation` values
carrying a :class:`Consequence`. A caller that records them without acting on them has
reintroduced the very defect (that was OTB-G001 F-04); the consumer in
:mod:`orbital_thermal.two_phase` folds the worst consequence into the case status.

This module is stdlib-only and defines its own consequence vocabulary rather than
importing the Stage-2 ``RankStatus``, so the registry keeps no dependency on the
physics layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .. import _validate as _v


class Axis(str, Enum):
    """The axes on which a correlation may declare applicability."""

    FLUID = "fluid"
    #: Single- vs two-component flow. Distinct from FLUID: Lockhart-Martinelli was
    #: developed for **two-component** systems (air-liquid), and a single-component
    #: system (a fluid boiling in its own vapour) is outside it however well the
    #: individual fluid is covered.
    COMPOSITION = "composition"
    GEOMETRY = "geometry"
    ORIENTATION = "orientation"
    REGIME = "regime"
    PROVENANCE = "provenance"


class Consequence(str, Enum):
    """What a violation does to a case.

    Deliberately ordered by severity so the worst can be selected: ``DE_RANK`` <
    ``REJECT`` < ``BLOCK``. ``DE_RANK`` means the case is reported but never ranked;
    ``REJECT`` means it fails a physical gate; ``BLOCK`` means it cannot be evaluated
    because a required statement or source is missing.
    """

    DE_RANK = "de_rank"
    REJECT = "reject"
    BLOCK = "block"


class Cause(str, Enum):
    r"""Why a violation was raised, which is a different question from what it does.

    **D119.** :class:`Consequence` answers *what happens to the case*; it does not
    answer *whether the axis was evaluated*, and ``BLOCK`` was carrying both meanings.
    Seven of the eight sites that emit it do so because the case states nothing on the
    axis -- genuinely not evaluated. The eighth fires when the entry declares it
    requires an executable form and does not have one: that axis WAS evaluated and the
    entry failed it. A consumer deriving "never checked" from ``BLOCK`` alone therefore
    reported a conclusion as the absence of one, on exactly the record whose purpose was
    to show that the entry's executable form moves the outcome.

    The distinction lives here, on the violation, because only the site that raises one
    knows which it is. Deriving it downstream -- from the axis, from the consequence,
    from the wording -- is guessing, and guessing right seven times out of eight is how
    this arose.

    **The default is** ``NOT_EVALUATED``\ **, and D120 corrected it from the other
    direction.** D119 defaulted to ``EVALUATED_AND_FAILED`` on the reasoning that "the
    failure being repaired is a conclusion presented as an absence, never the reverse".
    That generalised from the single site D119 repaired to a population running 8:1 the
    other way -- eight of the nine ``BLOCK`` sites in the package are absences -- which
    is the same shape as the defect it was guarding against.

    It is also the wrong half to be safe on. An absence misreported as a conclusion is a
    record asserting that a case failed an axis nothing checked: a claim with no basis,
    which is the error this whole gate exists to refuse. A conclusion misreported as an
    absence only understates. So a site that forgets understates.

    No site relies on it. ``test_d120_every_violation_site_states_whether_its_axis_was_evaluated``
    scans every file in the package that constructs a :class:`Violation` -- not one
    module by name -- and fails on any site that does not say. The default is for the
    type; the rule is for the author.
    """

    #: The axis could not be evaluated: no value for it was stated.
    NOT_EVALUATED = "not_evaluated"
    #: The axis was evaluated and the case, or the entry, failed it.
    EVALUATED_AND_FAILED = "evaluated_and_failed"

_SEVERITY: dict[Consequence, int] = {
    Consequence.DE_RANK: 0,
    Consequence.REJECT: 1,
    Consequence.BLOCK: 2,
}


def worst(consequences: list[Consequence] | tuple[Consequence, ...]) -> Consequence | None:
    """The most severe consequence in ``consequences``, or ``None`` if empty."""
    if not consequences:
        return None
    return max(consequences, key=lambda c: _SEVERITY[c])


@dataclass(frozen=True)
class Violation:
    """One applicability failure, with the axis, its consequence, and why."""

    axis: Axis
    consequence: Consequence
    detail: str
    #: Whether the axis was evaluated. Defaults to the UNDERSTATING reading; see
    #: :class:`Cause` for why that is the safe direction (D120 corrects D119).
    cause: Cause = Cause.NOT_EVALUATED

    def __str__(self) -> str:  # pragma: no cover - formatting only
        return f"[{self.axis.value}/{self.consequence.value}] {self.detail}"


#: Provenance states a declared numeric domain may be in.
#:
#: ``ESTABLISHED`` -- traceable to a named source.
#: ``UNESTABLISHED`` -- retained as a useful guard but not found in any consulted
#: source, so it must never be presented as the authors' declared range
#: (Director ruling D1; DEBTS D-1).
#: ``CONFLICTED`` -- two sources disagree; the adopted value and the reason are
#: recorded on the entry.
class DomainProvenance(str, Enum):
    ESTABLISHED = "established"
    UNESTABLISHED = "unestablished"
    CONFLICTED = "conflicted"


@dataclass(frozen=True)
class Applicability:
    """What a correlation is applicable to, in a form that can be enforced.

    Every collection is empty by default, meaning *unconstrained on that axis* -- a
    correlation only opts in to the axes it actually declares. An axis that is opted
    into is then binding, including the requirement that the caller state a value for
    it.

    ``*_basis`` fields carry the citation that establishes each constraint; they exist
    so an enforced limit can always be traced to why it is enforced.
    """

    # --- fluid axis ---
    fluids: frozenset[str] = frozenset()
    excluded_fluids: frozenset[str] = frozenset()
    fluids_basis: str = ""

    # --- composition axis ---
    compositions: frozenset[str] = frozenset()
    compositions_basis: str = ""

    # --- geometry axis (closes DEBTS D-9) ---
    geometries: frozenset[str] = frozenset()
    geometries_basis: str = ""

    # --- orientation / gravity axis ---
    orientations: frozenset[str] = frozenset()
    orientations_basis: str = ""
    gravity_explicit: bool = False
    gravity_basis: str = ""
    #: The gravity the correlation's database was taken at. For every 1g-derived
    #: correlation this is standard gravity, and it is a SOURCED boundary: the database
    #: exists at that gravity and nowhere else (Director ruling D6 -- "the default is
    #: standard gravity because the database is terrestrial").
    reference_gravity_m_s2: float | None = None
    #: Fractional tolerance on ``reference_gravity_m_s2``. A CONVENTION, not a sourced
    #: bound: it admits the ordinary variation of Earth surface gravity (~0.3 % between
    #: equator and pole) with margin, so that terrestrial laboratories anywhere pass.
    #: The *boundary* is sourced; only this tolerance is chosen.
    gravity_rel_tol: float = 0.01
    #: A branch threshold in the correlation's own correlating parameter. Crossing it
    #: changes the calculation procedure, so if gravity moves a case across it the
    #: correlation is no longer being evaluated the way the same hardware would be
    #: evaluated on the ground. Sourced: for Shah (1987) this is ``Y >= 1e6``.
    branch_threshold: float | None = None
    branch_threshold_basis: str = ""

    # --- flow-regime axis ---
    min_liquid_reynolds: float | None = None
    reynolds_basis: str = ""

    # --- provenance axis ---
    numeric_domain_provenance: DomainProvenance = DomainProvenance.ESTABLISHED
    numeric_domain_note: str = ""
    requires_executable_form: bool = False

    #: Axes deliberately NOT enforced, each with the reason. Recorded rather than
    #: silently absent, so an unenforced axis is a visible gap and not an oversight.
    unenforced_axes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def declared_axes(self) -> tuple[Axis, ...]:
        """Every axis this correlation actually constrains."""
        axes: list[Axis] = []
        if self.fluids or self.excluded_fluids:
            axes.append(Axis.FLUID)
        if self.compositions:
            axes.append(Axis.COMPOSITION)
        if self.geometries:
            axes.append(Axis.GEOMETRY)
        if self.orientations or self.gravity_explicit:
            axes.append(Axis.ORIENTATION)
        if self.min_liquid_reynolds is not None:
            axes.append(Axis.REGIME)
        if (
            self.numeric_domain_provenance is not DomainProvenance.ESTABLISHED
            or self.requires_executable_form
        ):
            axes.append(Axis.PROVENANCE)
        return tuple(axes)

    def check(
        self,
        *,
        fluid: str | None = None,
        composition: str | None = None,
        geometry: str | None = None,
        orientation: str | None = None,
        liquid_reynolds: float | None = None,
        gravity_m_s2: float | None = None,
        branch_value: float | None = None,
        branch_value_at_reference_gravity: float | None = None,
        has_executable_form: bool = True,
    ) -> tuple[Violation, ...]:
        """Every applicability violation for the stated case.

        An empty result means the case is applicable on every declared axis. A
        declared axis with no stated value yields a ``BLOCK`` violation: an unstated
        geometry is not a licence to assume a tube.

        ``numeric_domain_provenance`` deliberately yields **no violation**. Director
        direction on F-08 is that relabelling an unsourced numeric box is "labelling
        only" and that the limits "remain enforced as guards" -- so the box is enforced
        numerically by ``assert_in_domain`` and surfaced by :meth:`provenance_caveats`,
        but it does not by itself change a case's status. Making it de-rank would
        over-enforce past the ruling and would de-rank every case through Gungor &
        Winterton regardless of merit, which is not what "demoted" meant.

        **Non-finite inputs are refused before any axis is evaluated (D110).** Every
        ordered comparison below is false for ``NaN`` -- ``nan <= 0`` and ``nan > 0``
        are *both* false -- so a NaN gravity skipped the non-positive branch and the
        off-reference branch alike, and the caller received an empty violation tuple.
        An absence produced by an unorderable value is indistinguishable from an
        absence produced by a compliant case, so S5 minted ``eligible=True`` for it,
        carrying the genuine adopted basis. That is OTB-G002 criterion 6's falsifier
        exactly: *"any non-number or out-of-range quantity crossing the boundary marked
        applicable"*, and its own wording anticipated the mechanism -- *"a sign test
        does not exclude NaN"*.

        Checked here rather than at each caller because this is where the comparisons
        are, and checked over **every** numeric input rather than the one that was
        reported: ``liquid_reynolds``, ``branch_value`` and
        ``branch_value_at_reference_gravity`` admitted ``nan`` and both infinities the
        same way. ``_validate.finite`` is the project's existing helper and is used
        rather than a second spelling of it, for the reason
        ``two_phase_loop._validate_hydraulic_inputs`` records beside the identical
        repair: three copies of a check is the per-instance pattern C9 forbids, and a
        guard that a mutation cannot single out is not witnessable.

        The refusal travels as ``ValueError``, not as a :class:`Violation`, and the
        distinction is deliberate. A ``Violation`` grades a *case*: it says a
        well-formed quantity falls outside a declared basis, and it is consumed
        downstream as a finding. ``NaN`` is not a value of the quantity, so a
        ``DE_RANK`` or ``REJECT`` for it would answer a question that was never posed
        and would serialise as a physical claim about a case. That is the collapse D75
        and D90 exist to prevent, one level out. It also matches the precedent: the
        same criterion, the same value and the same helper already refuse a non-finite
        gravity in :func:`two_phase_loop.two_phase_pressure_drop`.
        """
        for _name, _value in (
            ("liquid_reynolds", liquid_reynolds),
            ("gravity_m_s2", gravity_m_s2),
            ("branch_value", branch_value),
            ("branch_value_at_reference_gravity", branch_value_at_reference_gravity),
        ):
            if _value is not None:
                _v.finite(_name, _value)

        v: list[Violation] = []

        # --- fluid ---
        if self.fluids or self.excluded_fluids:
            if fluid is None:
                v.append(
                    Violation(
                        Axis.FLUID,
                        Consequence.BLOCK,
                        "the correlation declares a fluid applicability but the case "
                        "states no fluid; an unstated fluid cannot be checked against it",
                        cause=Cause.NOT_EVALUATED,
                    )
                )
            else:
                key = fluid.strip().lower()
                if key in {f.lower() for f in self.excluded_fluids}:
                    v.append(
                        Violation(
                            Axis.FLUID,
                            Consequence.DE_RANK,
                            f"'{fluid}' is explicitly outside the correlation's fluid "
                            f"basis. {self.fluids_basis}",
                            cause=Cause.EVALUATED_AND_FAILED,
                        )
                    )
                elif self.fluids and key not in {f.lower() for f in self.fluids}:
                    v.append(
                        Violation(
                            Axis.FLUID,
                            Consequence.DE_RANK,
                            f"'{fluid}' is not in the correlation's development "
                            f"database ({', '.join(sorted(self.fluids))}). "
                            f"{self.fluids_basis}",
                            cause=Cause.EVALUATED_AND_FAILED,
                        )
                    )

        # --- composition ---
        if self.compositions:
            if composition is None:
                v.append(
                    Violation(
                        Axis.COMPOSITION,
                        Consequence.BLOCK,
                        "the correlation declares a composition basis "
                        f"({', '.join(sorted(self.compositions))}) but the case states "
                        "none",
                        cause=Cause.NOT_EVALUATED,
                    )
                )
            elif composition.strip().lower() not in {
                c.lower() for c in self.compositions
            }:
                v.append(
                    Violation(
                        Axis.COMPOSITION,
                        Consequence.DE_RANK,
                        f"composition '{composition}' is outside the correlation's "
                        f"basis ({', '.join(sorted(self.compositions))}). "
                        f"{self.compositions_basis}",
                        cause=Cause.EVALUATED_AND_FAILED,
                    )
                )

        # --- geometry (DEBTS D-9) ---
        if self.geometries:
            if geometry is None:
                v.append(
                    Violation(
                        Axis.GEOMETRY,
                        Consequence.BLOCK,
                        "the correlation declares a geometry basis "
                        f"({', '.join(sorted(self.geometries))}) but the case states no "
                        "geometry; channel geometry is source-required (S0 Sec. 5)",
                        cause=Cause.NOT_EVALUATED,
                    )
                )
            elif geometry.strip().lower() not in {g.lower() for g in self.geometries}:
                v.append(
                    Violation(
                        Axis.GEOMETRY,
                        Consequence.DE_RANK,
                        f"geometry '{geometry}' is outside the correlation's basis "
                        f"({', '.join(sorted(self.geometries))}). {self.geometries_basis}",
                        cause=Cause.EVALUATED_AND_FAILED,
                    )
                )

        # --- orientation / gravity ---
        if self.orientations:
            if orientation is None:
                v.append(
                    Violation(
                        Axis.ORIENTATION,
                        Consequence.BLOCK,
                        "the correlation declares an orientation basis "
                        f"({', '.join(sorted(self.orientations))}) but the case states "
                        "none",
                        cause=Cause.NOT_EVALUATED,
                    )
                )
            elif orientation.strip().lower() not in {o.lower() for o in self.orientations}:
                v.append(
                    Violation(
                        Axis.ORIENTATION,
                        Consequence.DE_RANK,
                        f"orientation '{orientation}' is outside the correlation's basis "
                        f"({', '.join(sorted(self.orientations))}). "
                        f"{self.orientations_basis}",
                        cause=Cause.EVALUATED_AND_FAILED,
                    )
                )

        if self.gravity_explicit:
            if gravity_m_s2 is None:
                v.append(
                    Violation(
                        Axis.ORIENTATION,
                        Consequence.BLOCK,
                        "the correlation is gravity-explicit (its correlating parameter "
                        "contains g) but the case states no gravitational acceleration. "
                        f"{self.gravity_basis}",
                        cause=Cause.NOT_EVALUATED,
                    )
                )
            elif gravity_m_s2 <= 0.0:
                v.append(
                    Violation(
                        Axis.ORIENTATION,
                        Consequence.REJECT,
                        f"gravitational acceleration {gravity_m_s2} m/s^2 is not "
                        "positive, and the correlating parameter divides by it: the "
                        "correlation has no zero-gravity limit and cannot be evaluated "
                        f"for this case. {self.gravity_basis}",
                        cause=Cause.EVALUATED_AND_FAILED,
                    )
                )
        # The gravity the DATABASE was taken at is a separate declaration from whether
        # the FORMULA contains g, and is checked independently. Nesting it under
        # `gravity_explicit` was a real defect: Lockhart-Martinelli's multiplier carries
        # no g, but its database is still terrestrial, so a 1e-6 m/s^2 case slipped
        # through unflagged until the D12 consistency test caught it.
        if self.reference_gravity_m_s2 is not None:
            ref = self.reference_gravity_m_s2
            if gravity_m_s2 is None and not self.gravity_explicit:
                v.append(
                    Violation(
                        Axis.ORIENTATION,
                        Consequence.BLOCK,
                        "the correlation's database was taken at a stated gravity "
                        f"({ref:.5g} m/s^2) but the case states none",
                        cause=Cause.NOT_EVALUATED,
                    )
                )
            elif (
                gravity_m_s2 is not None
                and gravity_m_s2 > 0.0
                and abs(gravity_m_s2 - ref) > self.gravity_rel_tol * ref
            ):
                v.append(
                    Violation(
                        Axis.ORIENTATION,
                        Consequence.DE_RANK,
                        f"gravitational acceleration {gravity_m_s2:.4g} m/s^2 is "
                        f"{gravity_m_s2 / ref:.3g} times the gravity the "
                        f"correlation's database was taken at ({ref:.5g} m/s^2). "
                        "The database exists at that gravity and nowhere else, so any "
                        "other value is an extrapolation across the axis the "
                        "correlating parameter is most sensitive to -- an "
                        "applicability violation, not a parameter change "
                        f"(Director ruling D6). {self.gravity_basis}",
                        cause=Cause.EVALUATED_AND_FAILED,
                    )
                )

            # Branch-threshold straddle. Not an absolute test on the parameter: the
            # threshold is crossed legitimately at 1 g by high mass flux (for Shah
            # (1987), measured at G ~ 1400 kg/m2s with the rest of the reference case,
            # well inside its declared 4-2905 domain). What is NOT legitimate is
            # gravity moving a case across it, because then the correlation picks a
            # different calculation procedure than the same hardware would use on the
            # ground -- which is what makes the reduced-gravity value untrustworthy
            # rather than merely unranked.
            if (
                self.branch_threshold is not None
                and branch_value is not None
                and branch_value_at_reference_gravity is not None
            ):
                here = branch_value >= self.branch_threshold
                there = branch_value_at_reference_gravity >= self.branch_threshold
                if here != there:
                    v.append(
                        Violation(
                            Axis.ORIENTATION,
                            Consequence.REJECT,
                            f"gravity moves this case across the correlation's own "
                            f"branch threshold: the correlating parameter is "
                            f"{branch_value:.4g} at the stated gravity against "
                            f"{branch_value_at_reference_gravity:.4g} at the database's "
                            f"gravity, and the threshold is "
                            f"{self.branch_threshold:.4g}. The calculation procedure "
                            "itself changes, so this is not the same correlation the "
                            f"ground data validated. {self.branch_threshold_basis}",
                            cause=Cause.EVALUATED_AND_FAILED,
                        )
                    )

        # --- flow regime ---
        if self.min_liquid_reynolds is not None:
            if liquid_reynolds is None:
                v.append(
                    Violation(
                        Axis.REGIME,
                        Consequence.BLOCK,
                        "the correlation declares a minimum liquid Reynolds number "
                        f"({self.min_liquid_reynolds:g}) but the case states none",
                        cause=Cause.NOT_EVALUATED,
                    )
                )
            elif liquid_reynolds < self.min_liquid_reynolds:
                v.append(
                    Violation(
                        Axis.REGIME,
                        Consequence.REJECT,
                        f"liquid Reynolds number {liquid_reynolds:.4g} is below the "
                        f"turbulent threshold {self.min_liquid_reynolds:g} required by "
                        f"the correlation's convective base. {self.reynolds_basis}",
                        cause=Cause.EVALUATED_AND_FAILED,
                    )
                )

        # --- provenance ---
        if self.requires_executable_form and not has_executable_form:
            v.append(
                Violation(
                    Axis.PROVENANCE,
                    Consequence.BLOCK,
                    "an evaluated value is needed but the entry carries no executable "
                    "form; a registry entry without an evaluator cannot supply one",
                    cause=Cause.EVALUATED_AND_FAILED,
                )
            )
        return tuple(v)

    def provenance_caveats(self) -> tuple[str, ...]:
        """Label-level caveats that must travel with a result but do not change status.

        Kept separate from :meth:`check` on purpose. A constraint that cannot be traced
        to a source is **relabelled**, not weaponised: Director ruling D1 retains it as
        an enforced guard while forbidding it to be presented as the authors' declared
        range. These strings are what carry that distinction into a report.
        """
        out: list[str] = []
        if self.numeric_domain_provenance is not DomainProvenance.ESTABLISHED:
            out.append(
                f"declared numeric domain is {self.numeric_domain_provenance.value}: "
                f"retained and ENFORCED as a guard, but it is NOT the authors' "
                f"declared range. {self.numeric_domain_note}"
            )
        for axis_note in self.unenforced_axes:
            out.append(f"axis not enforced -- {axis_note}")
        return tuple(out)


#: An entry that constrains nothing. Used where a correlation genuinely declares no
#: applicability axis, so that "no spec" and "no constraints" stay distinguishable.
UNCONSTRAINED = Applicability()


# --- contradictions between a case's own declarations (OTB-G002 F-02) -------------


def case_contradictions(
    *,
    fluid: str | None = None,
    composition: str | None = None,
    orientation: str | None = None,
    height_m: float | None = None,
    single_component_fluids: frozenset[str] = frozenset(),
) -> tuple[Violation, ...]:
    """Violations where a case's own declarations contradict each other.

    Distinct from :meth:`Applicability.check`, which compares a case against a
    correlation's declared basis. This compares the case against **itself**: some
    declarations are not derivable from the numbers, so they stay declarations -- but
    they must not be *freely* assertable (Director ruling on F-02, "derive what is
    derivable, and make the rest mutually consistency-checked rather than independently
    assertable").

    Two contradictions are checkable today:

    * a **single-component fluid** declared as ``two_component`` flow. Composition
      cannot be recovered from densities -- ammonia and some mixture can present the
      same numbers -- but a case naming a pure registered coolant *and* claiming two
      components has contradicted itself.
    * ``horizontal`` orientation with a **non-zero static height**. The static head is
      identically zero in horizontal flow; a non-zero height says the flow is not
      horizontal, whatever the label says.

    Lives here rather than in a caller so that every boundary gets the same check from
    one place (C9: boundary fixes are class-level, never per-instance).
    """
    v: list[Violation] = []

    if fluid is not None and composition is not None:
        pure = {f.strip().lower() for f in single_component_fluids}
        if fluid.strip().lower() in pure and composition.strip().lower() == "two_component":
            v.append(
                Violation(
                    Axis.COMPOSITION,
                    Consequence.REJECT,
                    f"the case declares fluid '{fluid}', a single-component coolant "
                    "registered as a pure substance, and simultaneously declares "
                    "two_component flow. Those cannot both be true, so the case is "
                    "self-contradictory rather than merely out of basis.",
                    cause=Cause.EVALUATED_AND_FAILED,
                )
            )

    if orientation is not None and height_m is not None:
        if orientation.strip().lower() == "horizontal" and abs(height_m) > 0.0:
            v.append(
                Violation(
                    Axis.ORIENTATION,
                    Consequence.REJECT,
                    f"the case declares horizontal orientation but supplies a static "
                    f"height of {height_m:.6g} m. The static head is identically zero "
                    "in horizontal flow, so a non-zero height contradicts the label.",
                    cause=Cause.EVALUATED_AND_FAILED,
                )
            )

    return tuple(v)
