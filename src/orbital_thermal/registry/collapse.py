"""C11: what a reduced-order term throws away, and which guards it thereby blinds.

**Standing rule C11**, in its own words:

    (i)  Any term that evaluates a **varying** quantity at a **single representative
         value** declares the quantity collapsed and the phenomena thereby
         unrepresentable.
    (ii) Any guard, criterion or reported check whose target phenomenon appears in the
         active model's collapsed set must state, **in the output**, that it cannot
         detect it against that model.

Enforced at the shared boundary, not per guard (**C9**).

Why this exists
---------------
S3's pressure-drop boundary passes one mean quality where a profile is needed. That
collapses the moving boiling boundary -- the mechanism that puts a negative-slope
segment into a boiling channel's characteristic -- so the static Ledinegg guard adopted
at S4 is correct, witnessed, and structurally incapable of firing.

**Nothing was done wrong at S3.** Evaluating a section at a representative value is a
legitimate reduced-order choice and this is a reduced-order model. The defect is that
the collapse was **silent**, and a guard was later adopted against a phenomenon the
collapse had already destroyed. C11 does not forbid collapsing; it forbids collapsing
quietly.

**C11 does not close the gap it makes visible.** Integrating the friction term along
the channel is a separate, unscheduled piece of work. Nothing here retires DEBTS D-12
or discharges the requirement for a working Ledinegg guard.

The collapse belongs to the TERM, not to the correlation
--------------------------------------------------------
Lockhart-Martinelli is local in quality; evaluating it once at a section mean is
something *this boundary* does to it. A different caller integrating the same
correlation along a channel would collapse nothing. So ``collapses`` is declared on the
model term that applies a correlation, not on the registry entry for the correlation
itself -- which is also why a term with no registry entry of its own, like the static
head, can carry one.
"""

from __future__ import annotations

from dataclasses import dataclass

#: The closed vocabulary of phenomena a term may destroy and a guard may target.
#:
#: **Closed on purpose.** The whole mechanism is an intersection between two declared
#: sets, and an intersection is silent when it is empty -- so a typo on either side
#: would read exactly like "no conflict" and the guard would report itself healthy.
#: That is the DIR-01 lesson (a vocabulary that is not fixed is not enforceable) and
#: the same shape as the three defects this project has already recorded: a
#: declaration that nothing checks is not a control.
PHENOMENA: frozenset[str] = frozenset(
    {
        # The travelling point where the fluid reaches saturation. Its motion with
        # flow is what makes a boiling channel's characteristic non-monotone.
        "moving_boiling_boundary",
        # The negatively-sloped segment of the internal pressure-drop/flow-rate
        # characteristic. Ledinegg's criterion is a sign test on exactly this.
        "negative_slope_segment",
        # More than one steady solution at one pressure drop.
        "multiple_steady_states",
        # Any axial variation of a quantity along the channel.
        "axial_profile",
    }
)


def _validate_phenomena(names: tuple[str, ...], *, context: str) -> frozenset[str]:
    unknown = sorted(set(names) - PHENOMENA)
    if unknown:
        raise ValueError(
            f"{context}: unknown phenomena {unknown}. The vocabulary is closed "
            f"({sorted(PHENOMENA)}) because this mechanism works by intersecting two "
            "declared sets, and an unrecognised name would produce an EMPTY "
            "intersection -- reading exactly like 'no conflict'. Add the phenomenon to "
            "PHENOMENA deliberately, or fix the spelling."
        )
    if not names:
        raise ValueError(f"{context}: an empty phenomena set declares nothing")
    return frozenset(names)


@dataclass(frozen=True)
class Collapse:
    """One varying quantity evaluated at one representative value, and what that costs."""

    quantity: str
    representative_value: str
    phenomena: tuple[str, ...]
    basis: str

    def __post_init__(self) -> None:
        _validate_phenomena(self.phenomena, context=f"Collapse({self.quantity!r})")
        if not self.quantity.strip() or not self.representative_value.strip():
            raise ValueError("a Collapse must name both the quantity and the value used")
        if not self.basis.strip():
            raise ValueError(
                f"Collapse({self.quantity!r}) has no basis: a collapse declaration that "
                "does not say where in the code it happens cannot be checked against it"
            )

    def __str__(self) -> str:
        return (
            f"{self.quantity} collapsed to {self.representative_value} "
            f"-> unrepresentable: {', '.join(sorted(self.phenomena))}"
        )


@dataclass(frozen=True)
class ModelTerm:
    """One additive term of a model, and what evaluating it that way throws away."""

    term: str
    collapses: tuple[Collapse, ...] = ()
    #: The registry entry this term applies, when it applies one. Empty for terms with
    #: no correlation behind them, such as a static head.
    entry_id: str = ""


@dataclass(frozen=True)
class CollapsedModel:
    """A model, its terms, and the phenomena its terms have collectively destroyed."""

    model: str
    terms: tuple[ModelTerm, ...]

    def collapsed_phenomena(self) -> dict[str, tuple[str, Collapse]]:
        """Phenomenon -> (term that destroyed it, the collapse that did it).

        First declaration wins where two terms collapse the same phenomenon; the
        conflict text names one of them and the full set is on the model.
        """
        found: dict[str, tuple[str, Collapse]] = {}
        for term in self.terms:
            for collapse in term.collapses:
                for phenomenon in collapse.phenomena:
                    found.setdefault(phenomenon, (term.term, collapse))
        return found

    @property
    def collapsing_terms(self) -> tuple[ModelTerm, ...]:
        return tuple(t for t in self.terms if t.collapses)


@dataclass(frozen=True)
class CollapseConflict:
    """A guard aimed at a phenomenon the active model has already destroyed."""

    guard_id: str
    phenomenon: str
    term: str
    collapse: Collapse

    def __str__(self) -> str:
        return (
            f"{self.guard_id} detects '{self.phenomenon}', which the {self.term} term "
            f"of the active model has collapsed ({self.collapse})"
        )


def detection_conflicts(
    *, guard_id: str, detects: tuple[str, ...], model: CollapsedModel
) -> tuple[CollapseConflict, ...]:
    """**The shared boundary.** Every conflict between a guard and the active model.

    C9: this is the one place the intersection is taken. A guard does not check itself,
    and a caller does not check on its behalf -- either would put the control at the
    call site, where the next guard would have to remember to repeat it.
    """
    if not detects:
        raise ValueError(
            f"{guard_id} declares no 'detects' phenomenon, so C11(ii) cannot be applied "
            "to it. A guard whose target is undeclared cannot be shown to be blind, "
            "which is indistinguishable from a guard that is known to work."
        )
    _validate_phenomena(detects, context=f"{guard_id}.detects")
    collapsed = model.collapsed_phenomena()
    return tuple(
        CollapseConflict(guard_id, phenomenon, *collapsed[phenomenon])
        for phenomenon in sorted(detects)
        if phenomenon in collapsed
    )


class UndetectableError(RuntimeError):
    """Raised when a caller depends on a verdict the active model cannot support."""


def assert_detectable(
    *, guard_id: str, detects: tuple[str, ...], model: CollapsedModel
) -> None:
    """Raise if the guard's target has been collapsed. For callers that DEPEND on it.

    The strict half of the boundary. Use it where a negative verdict would be relied
    on -- "no excursion here" is a claim, and a guard that cannot see one has not
    earned it.
    """
    conflicts = detection_conflicts(guard_id=guard_id, detects=detects, model=model)
    if conflicts:
        raise UndetectableError(
            f"{guard_id} cannot produce a verdict against model '{model.model}': "
            + "; ".join(str(c) for c in conflicts)
        )


def undetectable_disclosure(
    conflicts: tuple[CollapseConflict, ...], *, guard_name: str
) -> str:
    """The C11(ii) statement, **derived** from the cross-check rather than written.

    The reporting half of the boundary. Returns the empty string when there is no
    conflict, so an artifact that stops collapsing stops carrying the disclosure
    without anyone editing prose.
    """
    if not conflicts:
        return ""
    lost = "; ".join(
        f"'{c.phenomenon}' (collapsed by the {c.term} term: {c.collapse.quantity} "
        f"-> {c.collapse.representative_value})"
        for c in conflicts
    )
    return (
        f"{guard_name.upper()} -- IMPLEMENTED, WITNESSED, AND UNABLE TO FIRE ON THIS "
        f"MODEL (C11). It targets {lost}. A guard that cannot trigger does not by "
        "itself discharge the requirement for one, and this statement is DERIVED from "
        "the model's own collapse declarations rather than written: it disappears when "
        "the collapse does."
    )


__all__ = [
    "PHENOMENA",
    "Collapse",
    "CollapseConflict",
    "CollapsedModel",
    "ModelTerm",
    "UndetectableError",
    "assert_detectable",
    "detection_conflicts",
    "undetectable_disclosure",
]
