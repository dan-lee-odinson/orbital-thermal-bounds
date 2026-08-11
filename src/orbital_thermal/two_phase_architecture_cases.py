"""S5 TWO-PHASE architecture cases: which coolants are rank-eligible, and on which legs.

**Named ``two_phase_architecture_cases`` and not ``architecture_cases``.** That name is
taken by the Phase-B stage-1 module -- ``Classification``, ``Stage1Envelope``,
``classify_provenance`` -- which ``trade_study.py`` imports. S5's subject is the two-phase
milestone: different legs, different question. The roadmap calls both "architecture
cases", and two things sharing one name is how one of them gets overwritten.

**S5 decides eligibility. S6 emits the rankings.** Everything recorded here is consumed by
a milestone that publishes ordered results, and the project's standing position is that no
ranking is microgravity-validated. So the hazard this module is built against is not a
wrong answer -- it is a *lossy* one: an eligibility record that is true when written and
has shed its gravity basis by the time something orders it.

Acceptance criteria ``OTB-G005`` S5-1 … S5-11 are carried here; S5-12 … S5-14 are guards
that live in the tests, because what they constrain is the repository rather than this
module. The mechanisms:

``S5-1``  :func:`assess_fluid` derives eligibility from :data:`REGISTRY_ENTRIES` and the
          entries' own applicability specs. There is no eligible-fluids list to edit, and
          no caller argument that sets an outcome.
``S5-2``  :class:`FluidEligibility` holds one :class:`LegEligibility` per leg and
          **refuses to collapse**: ``bool(fluid_eligibility)`` raises.
``S5-3``  nothing here sorts, scores or orders. There is no comparison operator on any
          type in this module, by construction.
``S5-4``  a CHF-dependent :class:`LegEligibility` cannot be constructed without a
          :class:`GravityBasis`, and the basis is read off the registry entry rather than
          supplied by the caller.
``S5-5``  ``bool(chf_leg)`` **raises**, and :meth:`LegEligibility.as_record` carries the
          basis. **This makes dropping the basis VISIBLE, not impossible** -- see the
          residual below, which is the honest statement of what the guard buys.
``S5-6``  enforcement is the registry's existing ``Axis.ORIENTATION`` /
          ``Consequence.DE_RANK`` path, called through :meth:`Applicability.check`. There
          is no second gravity comparison in this module that could disagree with it.
``S5-7``  no text in this module states a direction for CHF error in microgravity.
          ``tests/test_two_phase_architecture_cases.py`` asserts that over the module's
          own source, because the conflation D-7 warns about is a *wording* failure and a
          reviewer reading for it is exactly what D-7 says has already gone wrong once.

**Why ``__bool__`` raises rather than returning something safe.** A sentinel that is merely
*unusual* gets read as falsy or truthy by the first ``if`` that meets it -- the D75 lesson,
where an unresolvable annotation had to be made not-an-``int`` so no ``== 0`` could
re-collapse it. Here the equivalent collapse is ``if eligible:``, and the only version of
that which cannot happen quietly is one that raises.

**THE RESIDUAL, AND IT IS A REAL HOLE IN S5-5 RATHER THAN A DESIGN NOTE.**
``LegEligibility.eligible`` is a **public field**. ``chf_leg.eligible`` yields a bare
``True``/``False`` with no gravity basis attached, in one attribute access, and nothing
stops it. S5-5's falsifier names *"any projection, serialisation, export, or convenience
accessor that yields CHF-dependent eligibility without its basis"*, and a public attribute
is a convenience accessor. **So this module does not make the basis non-droppable. It makes
dropping it VISIBLE**: a consumer that wants the bare flag has to write ``.eligible``
explicitly, which is a deliberate act that shows up in a diff and that a reviewer can grep
for, where ``if leg:`` would have looked like ordinary code.

That is a weaker property than the criterion asks for, and it is stated here rather than
engineered away because the alternatives were worse: a private field with an accessor that
raises pushes every legitimate caller through a second name and invites a
``_eligible``-shaped workaround; removing the flag entirely would mean the module could not
report a refusal at all. The carve-out is deliberate and the overclaim was not --
``test_s5_5_the_residual_public_eligible_field_is_recorded`` pins this, so the guarantee
cannot quietly re-inflate in a docstring later.

**What would actually close it**, if the Director wants it closed at S6 rather than
disclosed: make ``eligible`` return a type that carries its own basis for CHF legs, so
there is no bare flag anywhere in the object graph. That is a shape change to every
consumer, which is why it is not taken unilaterally at S5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple

from .registry.applicability import Applicability, Axis, Consequence, Violation
from .registry.provenance import CorrelationEntry, Status
from .registry.two_phase import TWO_PHASE_CORRELATIONS

#: The registry this module derives eligibility from. Named rather than imported at each
#: call site so a test can substitute a registry and watch eligibility move (S5-1).
REGISTRY_ENTRIES: tuple[CorrelationEntry, ...] = tuple(TWO_PHASE_CORRELATIONS)

#: The legs a two-phase ranking consumes, from the S0 scoping note §8 table: a ranked
#: architecture case needs a heat-transfer coefficient, a frictional pressure drop, and a
#: critical-heat-flux limit. ``onb``, ``stability``, ``npsh`` are constraints on a case
#: rather than quantities a ranking orders, so they are not eligibility legs.
RANKING_LEGS: tuple[str, ...] = ("htc", "dp", "chf")

#: Legs whose eligibility is a claim about CHF, and therefore inherits Director ruling D6
#: and debt D-7. Kept as data beside :data:`RANKING_LEGS` so that adding a CHF-derived leg
#: cannot forget the obligation: :class:`LegEligibility` refuses to build without a basis.
CHF_DEPENDENT_LEGS: frozenset[str] = frozenset({"chf"})

#: A correlation counts as adopted for ranking at exactly one status. ``SENSITIVITY``
#: entries inform a result and do not ground a rank; ``NOT_RANK_ELIGIBLE`` says so in its
#: name; the ``*_REQUIRED`` statuses have no executable form to rank with.
ADOPTED_FOR_RANKING: frozenset[Status] = frozenset({Status.RESOLVED})


class GravityBasis(NamedTuple):
    """The gravity a correlation's database was taken at, carried with the claim.

    Director ruling D6: *"the default is standard gravity because the database is
    terrestrial."* The boundary is **sourced** -- the database exists at that gravity and
    nowhere else -- so this is evidence travelling with a result, not a caveat attached
    to one.

    Built only by :meth:`from_entry`, which reads the registry. There is deliberately no
    path that takes a gravity from a caller: a basis a caller can supply is a basis a
    caller can get wrong, and the whole point of D6's enforcement is that the number comes
    from the source.
    """

    entry_id: str
    reference_gravity_m_s2: float
    basis: str

    @classmethod
    def from_entry(cls, entry: CorrelationEntry) -> GravityBasis:
        """Read the basis off a registry entry, or refuse.

        Refusing is the correct behaviour rather than a defensive check: a CHF entry with
        no declared reference gravity cannot ground a claim about whether a ranking is
        gravity-valid, and manufacturing a default here would be inventing the sourced
        boundary D6 rests on.
        """
        spec = getattr(entry, "applicability_spec", None)
        reference = getattr(spec, "reference_gravity_m_s2", None) if spec else None
        if reference is None:
            raise ValueError(
                f"{entry.id}: no declared reference gravity, so it cannot ground a "
                "CHF-dependent eligibility claim. Director ruling D6 makes the gravity "
                "of the correlation's database a sourced boundary; a default invented "
                "here would not be sourced."
            )
        return cls(entry.id, float(reference), getattr(spec, "gravity_basis", ""))


@dataclass(frozen=True)
class LegEligibility:
    """Whether one fluid is rank-eligible on one leg, and the evidence for it.

    **This type refuses two reductions**, and both refusals are the criteria rather than
    defensive programming:

    * a CHF-dependent leg cannot be *constructed* without a :class:`GravityBasis` (S5-4);
    * a CHF-dependent leg cannot be *read as a bool* at all (S5-5), because that is the
      operation a downstream ranking performs when it drops the basis.
    """

    fluid: str
    leg: str
    entry_id: str
    eligible: bool
    violations: tuple[Violation, ...] = ()
    gravity_basis: GravityBasis | None = None

    def __post_init__(self) -> None:
        if self.leg in CHF_DEPENDENT_LEGS and self.gravity_basis is None:
            raise ValueError(
                f"{self.fluid}/{self.leg}: a CHF-dependent eligibility cannot be built "
                "without the gravity basis of the correlation that produced it "
                "(Director ruling D6, debt D-7)."
            )

    @property
    def chf_dependent(self) -> bool:
        return self.leg in CHF_DEPENDENT_LEGS

    def __bool__(self) -> bool:
        """Truth-testing is how the basis gets dropped, so for CHF it is refused."""
        if self.chf_dependent:
            raise TypeError(
                f"{self.fluid}/{self.leg}: a CHF-dependent eligibility has no bare "
                "truth value. Reading it as one is how a ranking loses the gravity "
                "basis it is required to carry. Use .as_record(), which carries the "
                "basis, or .eligible if you have already accounted for it."
            )
        return self.eligible

    def as_record(self) -> dict[str, object]:
        """The projection a consumer should take. Carries the basis, or raises.

        S5-5 names *"any projection, serialisation, export, or convenience accessor that
        yields CHF-dependent eligibility without its basis"* as the falsifier. **This
        projection cannot produce that shape; the public ``eligible`` field can.** See the
        residual in the module docstring -- the guard makes the drop visible in a diff, it
        does not prevent it, and saying otherwise here would be the overclaim the module
        exists to avoid making about gravity.
        """
        record: dict[str, object] = {
            "fluid": self.fluid,
            "leg": self.leg,
            "entry_id": self.entry_id,
            "eligible": self.eligible,
            "violations": tuple(v.detail for v in self.violations),
        }
        if self.chf_dependent:
            basis = self.gravity_basis
            if basis is None:  # pragma: no cover - __post_init__ forecloses it
                raise ValueError("CHF-dependent record without a gravity basis")
            record["gravity_basis"] = {
                "entry_id": basis.entry_id,
                "reference_gravity_m_s2": basis.reference_gravity_m_s2,
                "basis": basis.basis,
            }
        return record


@dataclass(frozen=True)
class FluidEligibility:
    """One fluid's eligibility, **per leg**, with no overall verdict.

    S5-2: partial eligibility is never summarised. A fluid eligible on ``dp`` and refused
    on ``htc`` is that, and there is no attribute, property or truth value that turns the
    pair into one answer. ``bool()`` raises for the same reason it raises on a
    CHF-dependent leg: the collapse is the defect.
    """

    fluid: str
    legs: dict[str, LegEligibility] = field(default_factory=dict)

    def __bool__(self) -> bool:
        raise TypeError(
            f"{self.fluid}: eligibility is per leg and does not collapse to one value "
            f"(S5-2). Legs assessed: {sorted(self.legs)}. Ask about a leg."
        )

    def as_records(self) -> list[dict[str, object]]:
        """Per-leg records, in leg order. Not a ranking -- see S5-3."""
        return [self.legs[leg].as_record() for leg in RANKING_LEGS if leg in self.legs]


def adopted_entry(
    leg: str, entries: tuple[CorrelationEntry, ...] | None = None
) -> CorrelationEntry | None:
    """The correlation adopted for ranking on a leg, or ``None`` if none is.

    Derived from status, so an entry moving out of ``RESOLVED`` moves eligibility with it
    -- which is S5-1's falsifier ("an eligibility that does not change when a
    correlation's declared basis, adoption status, or applicability axis changes").
    """
    pool = REGISTRY_ENTRIES if entries is None else entries
    adopted = [e for e in pool if e.kind == leg and e.status in ADOPTED_FOR_RANKING]
    if not adopted:
        return None
    if len(adopted) > 1:
        raise ValueError(
            f"{leg}: {len(adopted)} correlations are adopted for ranking "
            f"({', '.join(e.id for e in adopted)}). Which one grounds a rank is a "
            "decision, not something this function may pick."
        )
    return adopted[0]


def assess_leg(
    fluid: str,
    leg: str,
    *,
    gravity_m_s2: float,
    entries: tuple[CorrelationEntry, ...] | None = None,
    **case: object,
) -> LegEligibility | None:
    """Assess one leg for one fluid. ``None`` when no correlation is adopted for it.

    ``None`` is *not* "ineligible": no adopted correlation is an absence of knowledge,
    and S4-8 requires that to stay distinguishable from a refusal. The caller sees the
    difference because it gets no record rather than a negative one.
    """
    entry = adopted_entry(leg, entries)
    if entry is None:
        return None

    spec: Applicability | None = getattr(entry, "applicability_spec", None)
    violations: tuple[Violation, ...] = ()
    if spec is not None:
        violations = spec.check(fluid=fluid, gravity_m_s2=gravity_m_s2, **case)  # type: ignore[arg-type]

    disqualifying = tuple(
        v for v in violations
        if v.consequence in (Consequence.DE_RANK, Consequence.REJECT, Consequence.BLOCK)
    )
    basis = GravityBasis.from_entry(entry) if leg in CHF_DEPENDENT_LEGS else None
    return LegEligibility(
        fluid=fluid,
        leg=leg,
        entry_id=entry.id,
        eligible=not disqualifying,
        violations=violations,
        gravity_basis=basis,
    )


def assess_fluid(
    fluid: str,
    *,
    gravity_m_s2: float,
    entries: tuple[CorrelationEntry, ...] | None = None,
    **case: object,
) -> FluidEligibility:
    """Assess every ranking leg for one fluid. Computed, never declared (S5-1)."""
    legs: dict[str, LegEligibility] = {}
    for leg in RANKING_LEGS:
        outcome = assess_leg(fluid, leg, gravity_m_s2=gravity_m_s2, entries=entries, **case)
        if outcome is not None:
            legs[leg] = outcome
    return FluidEligibility(fluid=fluid, legs=legs)


def gravity_derank_axis() -> Axis:
    """The axis D6's enforcement travels on, named so a test can assert the route.

    S5-6 requires that this module not carry a second gravity comparison beside the
    registry's. It carries none: the only gravity argument in this module is the one
    handed to :meth:`Applicability.check`.
    """
    return Axis.ORIENTATION


# =======================================================================================
# D-6: the Steiner-Taborek (1992) evaluation, which the debt says "Retires at S5"
# =======================================================================================

class AmmoniaMeasurement(NamedTuple):
    """One recorded deviation of a correlation against ammonia data.

    These are the numbers D-6 records, with who measured them. They are declared as data
    because S5-8 requires a disposition to NAME the measurement it acted on, and a
    disposition citing a number that lives only in prose cannot be checked against it.
    """

    correlation: str
    deviation_percent: float
    source: str
    #: True where the correlation's accuracy comes from resolving gravitational
    #: flow-pattern regimes -- the mechanism that does not exist in orbit. D-6's closing
    #: line about Kattan-Thome-Favrat, and the reason S5-9 exists.
    accuracy_is_gravity_dependent: bool = False


#: The three measurements D-6 records, and they DISAGREE. Steiner-Taborek is worse than
#: the correlation ammonia is already de-ranked through; the best score belongs to a
#: flow-pattern method; and a separate pooled study calls Steiner-Taborek the only one
#: that predicts ammonia at all. An evaluation that does not say which of these it acted
#: on has not evaluated -- that is S5-8, and it is why they are enumerated rather than
#: summarised.
AMMONIA_HTC_MEASUREMENTS: tuple[AmmoniaMeasurement, ...] = (
    AmmoniaMeasurement(
        "steiner_taborek_1992", 41.9,
        "Zurcher, Thome & Favrat -- VDI/Steiner against ammonia data"),
    AmmoniaMeasurement(
        "gungor_winterton_1987", 37.2,
        "Zurcher, Thome & Favrat -- GW87 against the same data"),
    AmmoniaMeasurement(
        "kattan_thome_favrat", 19.5,
        "Zurcher, Thome & Favrat -- best of the three",
        accuracy_is_gravity_dependent=True),
)

#: Táboas (2006), pooling five ammonia datasets, calls Steiner-Taborek the only
#: correlation that predicts ammonia. Recorded beside the deviations because it is
#: evidence pointing the OTHER way, and an evaluation that cites only the deviations
#: would be citing half the record.
TABOAS_2006_ENDORSEMENT = (
    "Taboas (2006), pooling five ammonia datasets, calls Steiner-Taborek the only "
    "correlation that predicts ammonia."
)

#: The dispositions D-6 can reach. ``DECLINE_POLICY`` and ``DECLINE_NO_KNOWLEDGE`` are
#: kept apart because S4-8 requires it: "no correlation exists" and "one exists whose
#: declared basis admits part of this space and was not adopted" are different claims and
#: only one of them is true.
DISPOSITIONS = ("adopt", "adopt_with_scope", "decline_policy", "decline_no_knowledge")


@dataclass(frozen=True)
class AmmoniaHtcEvaluation:
    """A recorded disposition of D-6, with the evidence that decided it.

    **Refuses three things, and each refusal is a criterion:**

    * a disposition that names no measurement (S5-8);
    * a disposition preferring a correlation whose accuracy is gravity-dependent, without
      that being recorded (S5-9 -- Kattan-Thome-Favrat is the named case);
    * a decline reported as an absence of knowledge when the correlation exists (S5-10,
      resting on S4-8).
    """

    disposition: str
    acted_on: str
    rationale: str
    #: Required when :attr:`acted_on` names a measurement whose accuracy is
    #: gravity-dependent. Prose, because what must be recorded is a judgement.
    gravity_dependence_note: str = ""

    def __post_init__(self) -> None:
        if self.disposition not in DISPOSITIONS:
            raise ValueError(
                f"{self.disposition!r} is not a disposition: {DISPOSITIONS}")
        named = {m.correlation for m in AMMONIA_HTC_MEASUREMENTS}
        if self.acted_on not in named:
            raise ValueError(
                f"a disposition must name the measurement it acted on (S5-8). "
                f"{self.acted_on!r} is not one of {sorted(named)}."
            )
        measurement = self.measurement
        if measurement.accuracy_is_gravity_dependent and not self.gravity_dependence_note:
            raise ValueError(
                f"{self.acted_on} scores well BECAUSE it resolves gravitational "
                "flow-pattern regimes -- the mechanism that does not exist in orbit "
                "(D-6, D-7). A disposition resting on its accuracy must record that "
                "(S5-9); accuracy alone is not adoptability."
            )
        if self.disposition == "decline_no_knowledge":
            raise ValueError(
                "Steiner-Taborek (1992) exists and its basis admits part of this space, "
                "so a decline here is a POLICY refusal, not an absence of knowledge "
                "(S5-10, resting on S4-8). Use 'decline_policy' and name the decision."
            )

    @property
    def measurement(self) -> AmmoniaMeasurement:
        return next(
            m for m in AMMONIA_HTC_MEASUREMENTS if m.correlation == self.acted_on)


#: **D-6 IS NOT DISPOSITIONED, AND THAT IS THE STATE THIS BUILD REPORTS.**
#:
#: The debt says "Retires at S5". S5-11 says retirement follows a recorded DISPOSITION,
#: not the evaluation having been performed -- and the evidence D-6 records genuinely
#: conflicts: Steiner-Taborek is measured WORSE (41.9 %) than the correlation ammonia is
#: already de-ranked through (37.2 %), while a separate pooled study calls it the only
#: correlation that predicts ammonia. Choosing between those is a decision on evidence,
#: which is the Director's, and a builder recording one here would be the D51 shape --
#: applying a ruling before it is made.
#:
#: So the mechanism is built, the evidence is enumerated and checkable, and this is
#: ``None``. :func:`d6_retirement_state` reports it as open, by name.
AMMONIA_HTC_DISPOSITION: AmmoniaHtcEvaluation | None = None


def d6_retirement_state() -> tuple[str, str]:
    """``(state, reason)`` for debt D-6. **Administrative, and paired -- see S5-11.**

    Performing an evaluation and retiring a debt are different states, and the artifact
    must be able to show which one obtains rather than leaving a reader to infer it from
    the presence of code.
    """
    if AMMONIA_HTC_DISPOSITION is None:
        return (
            "open",
            "the evaluation mechanism is built and the recorded measurements conflict "
            "(41.9 % vs 37.2 %, against Taboas's endorsement); no disposition has been "
            "recorded, so D-6 does not retire. S5-11.",
        )
    return (
        "retired",
        f"dispositioned {AMMONIA_HTC_DISPOSITION.disposition} on "
        f"{AMMONIA_HTC_DISPOSITION.acted_on} "
        f"({AMMONIA_HTC_DISPOSITION.measurement.deviation_percent} %).",
    )
