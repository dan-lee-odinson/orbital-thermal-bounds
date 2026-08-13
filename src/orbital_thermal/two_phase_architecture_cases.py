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

import contextlib as _contextlib
import contextvars as _contextvars
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
        # Sol's F-04. The basis STRING is evidence, not decoration: D6 makes the gravity a
        # SOURCED boundary, so a blank basis is a number with nothing standing behind it,
        # and defaulting it to "" was one of the five shapes S5-4 forbids. Checked AFTER
        # the reference so an entry missing both still reports the more specific reason.
        basis_text = (getattr(spec, "gravity_basis", "") or "").strip()
        if not basis_text:
            raise ValueError(
                f"{entry.id}: declares reference gravity {reference} but no "
                "gravity_basis text. The boundary is sourced under Director ruling D6, "
                "and a basis string that is blank is a number with no source behind it."
            )
        return cls(entry.id, float(reference), basis_text)


def _registry_gravity_bases(
    entries: tuple[CorrelationEntry, ...] | None = None,
) -> dict[str, GravityBasis]:
    """Every gravity basis the registry can actually produce, keyed by entry id.

    **The construction boundary F-04 asked for.** A CHF-dependent record is closed around
    this map rather than around whatever a caller passed, so ``GravityBasis`` staying a
    public NamedTuple with an ordinary constructor no longer matters: a fabricated one
    does not appear here and is refused. Entries with no declared reference gravity are
    simply absent, which is why naming one is refused rather than defaulted.
    """
    bases: dict[str, GravityBasis] = {}
    for entry in (REGISTRY_ENTRIES if entries is None else entries):
        # D100, hole 1: this filtered on NEITHER kind NOR status, so a pressure-drop
        # correlation and a NOT_RANK_ELIGIBLE entry were both accepted as CHF producers.
        # Filtering is not a fourth check on the caller -- it makes the helper's own
        # claim true. The mint is what closes the boundary.
        if entry.kind not in CHF_DEPENDENT_LEGS or entry.status not in ADOPTED_FOR_RANKING:
            continue
        try:
            bases[entry.id] = GravityBasis.from_entry(entry)
        except ValueError:
            continue
    return bases


#: **D101/R1: the minting scope, held PER EXECUTION CONTEXT.**
#:
#: It was a plain module-level ``bool``, which is a global. One thread inside
#: :func:`assess_leg` held it open for every thread, so the public constructor D100
#: removed succeeded whenever anybody else happened to be minting. Measured at **100 %**,
#: not at a race's edge: four minter threads against one constructor thread fabricated
#: 367 896 records out of 367 896 attempts in five seconds, each carrying
#: ``eligible=True``, ``violations=()``, the genuine Shah-1987 basis and a gravity the
#: computation never saw. Deterministically, one minter holding the scope open on a
#: barrier is enough.
#:
#: **``ContextVar`` rather than ``threading.local``**, and the difference is real. A
#: ``threading.local`` is per-thread, so within one thread every ``await`` point shares
#: the flag -- an async caller suspended inside the scope would let another task on the
#: same thread construct. That is the identical defect one level narrower. A
#: ``ContextVar`` is per-context: threads start with their own, and tasks copy at
#: creation. This module has no async today; the choice is for what S6 inherits.
#:
#: **The residual, stated because it is not zero -- and WIDER than first written.** The
#: mechanism is ``contextvars.copy_context()`` generally: any context captured inside an
#: open scope carries the mint, and ``.run()`` on it later replays that. A task created
#: inside the scope is one instance of this and was the only one named at D101; a copied
#: context needs no task at all. Nothing here copies contexts or creates tasks, so none of
#: it is reachable today -- but the class is context capture, not task creation.
_MINTING: _contextvars.ContextVar[bool] = _contextvars.ContextVar(
    "orbital_thermal.two_phase_architecture_cases._MINTING", default=False
)


@_contextlib.contextmanager
def _minting():
    token = _MINTING.set(True)
    try:
        yield
    finally:
        _MINTING.reset(token)


@dataclass(frozen=True)
class LegEligibility:
    """Whether one fluid is rank-eligible on one leg, and the evidence for it.

    **D100: a CHF-dependent record is constructible ONLY by the computation that
    produces it.** Three review rounds attacked this boundary field by field -- the basis
    was fabricable (round 1), the producer id was free of the basis (round 2), the
    outcome and the producer's kind were free of both (round 3) -- and every repair was
    witnessed against its own falsifiers and looked complete when written. That is the
    evidence the boundary cannot be closed field by field, so the Director ruled the door
    shut rather than guarded: :func:`assess_leg` mints, and direct construction refuses.

    Nothing needs authenticating if nothing is caller-supplied. The checks below are kept
    because they are witnessed and cost nothing, but they are no longer the boundary --
    the mint is.

    **THE ONE ROUTE THAT REMAINS, DISCLOSED RATHER THAN CLAIMED SHUT.**
    ``object.__new__(LegEligibility)`` followed by writing ``__dict__`` bypasses
    ``__init__`` entirely, so no ``__post_init__`` check can see it. Python offers no way
    to prevent that for any type. It was found by the derived witness rather than by
    inspection, and it is recorded here because the alternative -- saying the boundary is
    closed -- would be the overclaim this module has already had to retract once. What the
    mint buys is that every ORDINARY route refuses: the constructor,
    ``dataclasses.replace``, and ``copy.replace``. Reaching for ``object.__new__`` is a
    deliberate act no consumer performs by accident.

    **This type also refuses two reductions**, both criteria rather than defensive code:

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

    def __replace__(self, **changes: object) -> LegEligibility:
        """``dataclasses.replace`` is a construction route and it carried the mint.

        Found by enumerating the object-creation protocols rather than the routes I
        thought of. **D101/R2: on 3.10-3.12 this method is DEAD CODE**, measured by
        instrumenting it -- it is invoked zero times by any protocol, including for a
        non-CHF leg where its own return path lives, because ``copy.replace`` does not
        exist before 3.13 and ``dataclasses.replace`` goes straight to ``__init__``. This
        project declares ``requires-python = ">=3.10"`` and tests 3.10/3.11/3.12, so on
        every supported interpreter neither its refusal nor its message reaches a caller.
        It is live only on 3.13+, and it is kept for that. The previous docstring said it
        "cannot be witnessed", which was more generous than the measurement.
        """
        if self.leg in CHF_DEPENDENT_LEGS:
            raise TypeError(
                f"{self.fluid}/{self.leg}: a CHF-dependent eligibility cannot be "
                "replaced -- a replaced record is not the record the computation "
                "produced (D100). Re-run assess_leg."
            )
        return LegEligibility(**{**self.__dict__, **changes})

    def __post_init__(self) -> None:
        if self.leg not in CHF_DEPENDENT_LEGS:
            return
        if not _MINTING.get():
            raise TypeError(
                f"{self.fluid}/{self.leg}: a CHF-dependent eligibility is constructible "
                "only by the computation that produces it. Call assess_leg; its "
                "`eligible` and `violations` are computed from the case and the "
                "registry, and a caller-supplied outcome is what D100 removed."
            )
        # --- Sol's F-04. S5-4 forbids FIVE shapes and __post_init__ rejected one. ------
        # Absent was refused; empty, defaulted, caller-supplied and caller-overridden all
        # constructed. A record built around a caller's basis fields is a record whose
        # evidence the caller invented, so construction is closed around the REGISTRY:
        # the basis must be one this module could have produced from an adopted entry.
        basis = self.gravity_basis
        if basis is None:
            raise ValueError(
                f"{self.fluid}/{self.leg}: a CHF-dependent eligibility cannot be built "
                "without the gravity basis of the correlation that produced it "
                "(Director ruling D6, debt D-7)."
            )
        if not str(basis.entry_id).strip() or not str(basis.basis).strip():
            raise ValueError(
                f"{self.fluid}/{self.leg}: the gravity basis carries an empty "
                f"entry_id={basis.entry_id!r} or basis={basis.basis!r}. S5-4 names an "
                "EMPTY basis as a falsifier alongside an absent one."
            )
        reference = basis.reference_gravity_m_s2
        if reference is None or not isinstance(reference, (int, float)) or reference <= 0:
            raise ValueError(
                f"{self.fluid}/{self.leg}: reference_gravity_m_s2={reference!r} is not a "
                "positive gravity. A fabricated 0.0 is the shape F-04 constructed."
            )
        # **D97/F-02: the two identities must be ONE.** Round 1 authenticated the basis
        # against the registry and never bound it to `entry_id` -- the field naming the
        # correlation the eligibility came from. So a genuine Shah-1987 basis could be
        # attached to a record claiming producer 'MADE-UP', and `as_record()` serialised
        # both contradictory identities as valid. S5-4 forbids a caller-OVERRIDDEN basis,
        # and overriding which correlation a genuine basis is said to support is that
        # falsifier. All six round-1 witnesses aligned the two ids, so none exercised it.
        if basis.entry_id != self.entry_id:
            raise ValueError(
                f"{self.fluid}/{self.leg}: the record names producer "
                f"{self.entry_id!r} while its gravity basis was produced by "
                f"{basis.entry_id!r}. One record cannot carry two producer identities -- "
                "the basis must be the basis of the correlation the eligibility came "
                "from, not a genuine basis borrowed from another entry."
            )
        registry = _registry_gravity_bases()
        if basis.entry_id not in registry:
            raise ValueError(
                f"{self.fluid}/{self.leg}: gravity basis names {basis.entry_id!r}, which "
                "is not a registry entry. The basis must come from the correlation that "
                "produced the eligibility, not from a caller -- a basis a caller can "
                f"supply is a basis a caller can get wrong. Known: {sorted(registry)}."
            )
        if registry[basis.entry_id] != basis:
            raise ValueError(
                f"{self.fluid}/{self.leg}: gravity basis does not match the registry's "
                f"for {basis.entry_id!r}. Supplied {basis!r}; the registry says "
                f"{registry[basis.entry_id]!r}. S5-4 names a caller-OVERRIDDEN basis as "
                "a falsifier, and an overridden one is exactly a mismatched one."
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
    with _minting():
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
    #: **Required when the adopted correlation is NOT the best-scoring one.** It must
    #: print both deviation figures, so a reader cannot mistake the adoption for a choice
    #: on accuracy. D75's ruling: *"a reader must not be able to mistake this for a choice
    #: on accuracy."* A disclaimer that does not carry the numbers is a disclaimer a
    #: reader can skim past, so the numbers are what is checked.
    accuracy_disclaimer: str = ""
    #: **Required when a better-scoring candidate exists.** Naming the rejected candidate
    #: and the STRUCTURAL ground for rejecting it -- S5-9's falsifier is "a comparison
    #: table that ranks the three by deviation and stops there", and a record that adopts
    #: the worse number without saying why the better one was refused is that table.
    structural_rejection: str = ""
    #: **Required when the disposition is ``adopt_with_scope``.** The bound the adoption
    #: is limited to. A verb naming a bound that no text supplies is weaker than plain
    #: ``adopt``: it reads as narrower while constraining nothing, so the empty case is
    #: refused rather than defaulted (D84).
    scope: str = ""

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
        better = [m for m in AMMONIA_HTC_MEASUREMENTS
                  if m.deviation_percent < measurement.deviation_percent]
        if better and self.disposition in ("adopt", "adopt_with_scope"):
            if not self.accuracy_disclaimer:
                raise ValueError(
                    f"{self.acted_on} is adopted at {measurement.deviation_percent} % "
                    f"while {better[0].correlation} is recorded at "
                    f"{better[0].deviation_percent} %. This is NOT a choice on accuracy "
                    "and the record must say so in terms a reader cannot skim past."
                )
            for number in (measurement.deviation_percent, better[0].deviation_percent):
                if f"{number}" not in self.accuracy_disclaimer:
                    raise ValueError(
                        f"the accuracy disclaimer must print {number} %. A disclaimer "
                        "without the figures lets a reader assume the adopted "
                        "correlation scored better, which is the reading it exists to "
                        "prevent."
                    )
            if not self.structural_rejection:
                raise ValueError(
                    f"{better[0].correlation} scores better and was not adopted. The "
                    "STRUCTURAL ground for rejecting it must be recorded (S5-9); "
                    "otherwise this record is a deviation table that stops at the "
                    "numbers."
                )
        if self.disposition == "adopt_with_scope" and not self.scope.strip():
            raise ValueError(
                "adopt_with_scope names a bound; an empty scope supplies none. A verb "
                "that reads as narrower while constraining nothing is WEAKER than plain "
                "'adopt', because a reader takes the narrowing on trust. Either supply "
                "the scope or use 'adopt' and say the adoption is unbounded (D84)."
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


#: **D-6 IS DISPOSITIONED. The Director ruled it, and this is his ruling, not a builder's.**
#:
#: Steiner-Taborek (1992) is adopted with scope. **This adopts the WORSE recorded
#: deviation** -- 41.9 % against Gungor-Winterton (1987)'s 37.2 % on the same ammonia data
#: -- on the strength of Taboas (2006)'s pooled endorsement across five datasets, and NOT
#: on a deviation figure. The record is built so that a reader cannot mistake it for a
#: choice on accuracy: :class:`AmmoniaHtcEvaluation` refuses to construct an adoption over
#: a better-scoring candidate unless the disclaimer prints both numbers.
#:
#: **Kattan-Thome-Favrat is rejected on STRUCTURE, not on accuracy**, and its 19.5 % is
#: the best of the three. Its accuracy is earned by resolving gravitational flow-pattern
#: regimes -- the mechanism that does not exist in orbit -- so adopting a 1-g fit whose
#: accuracy mechanism vanishes is not adoption. **This is not a new principle here.** The
#: same ground already stripped Gungor-Winterton (1986)'s Froude stratification de-rating
#: at ``registry/two_phase.py:379``: *"stratification is a 1g horizontal-channel effect
#: with no microgravity meaning, and applying a gravity-driven de-rating in a microgravity
#: screening model would be a silent physical assumption."* D-6 applies that reasoning one
#: level out -- from a single gravity-driven TERM to a whole correlation whose accuracy
#: mechanism is gravity-driven.
#: --- §7.2 DIRECTOR SELECTION -- BUILDER WORDING, DIRECTOR CHOICE (D84) ---
#:
#: **The three-zone authority seam, carried into the artifact rather than left in the
#: ledger.** DIR-02 exists to stop unmarked builder prose sitting in the Director's field,
#: and D47 is the round where exactly that was found inside a frozen packet. The seam has
#: to survive into the code for the same reason it has to survive into the ledger: a
#: reader of this module cannot check the ledger, and a scope paragraph in a
#: Director-dispositioned record reads as his words unless something says otherwise.
#:
#: **So, precisely: the text below is the BUILDER'S WORDING. The Director's act was the
#: CHOICE to adopt it as the scope at D84.** His own prose in this disposition is the
#: ``rationale`` field and nothing else. Anyone quoting the paragraph below as a Director
#: ruling is quoting a builder.
#:
#: **It states a DIRECTION, and that is correct rather than an oversight.** Hammer (2021)
#: is about the HEAT-TRANSFER COEFFICIENT, where the direction is known. D-7's own
#: refinement is that the direction is *not* simple for **CHF**, and that conflating the
#: two is the error its title invites. This scope is an HTC adoption, so the HTC direction
#: belongs in it. ``test_s5_7_no_s5_text_states_a_direction_for_chf_error_in_microgravity`` keeps
#: the distinction honest, and records the correction that forced it to be encoded.
#: --- END DIRECTOR SELECTION ---
AMMONIA_HTC_SCOPE = (
    "Adopted for 1-g-referenced ammonia heat-transfer screening only. "
    "Steiner-Taborek (1992) is 1-g derived and this project claims no microgravity "
    "validation (D-7). Hammer (2021) records that microgravity flow-boiling heat "
    "transfer typically depreciates, so this correlation is expected to overpredict in "
    "orbit -- non-conservative, and the direction of the error is known. This adoption "
    "licenses no microgravity heat-transfer claim and does not discharge D-7."
)

#: Who authored what, as data, so a consumer can render the seam without re-reading prose.
AMMONIA_HTC_SCOPE_AUTHORITY = {
    "zone": "§7.2 DIRECTOR SELECTION",
    "wording": "builder",
    "choice": "Director, D84",
    "director_prose_field": "rationale",
}

AMMONIA_HTC_DISPOSITION: AmmoniaHtcEvaluation | None = AmmoniaHtcEvaluation(
    disposition="adopt_with_scope",
    acted_on="steiner_taborek_1992",
    rationale=(
        "Let's go with Steiner-Taborek, cite Taboas' work pooling the five datasets and "
        "calling it the only correlation that predicts ammonia."
    ),
    accuracy_disclaimer=(
        "ADOPTED ON THE WORSE DEVIATION. Steiner-Taborek is recorded at 41.9 % against "
        "Gungor-Winterton (1987)'s 37.2 % on the same Zurcher ammonia data, and against "
        "Kattan-Thome-Favrat's 19.5 %. It is adopted on Taboas (2006)'s pooled "
        "endorsement across five ammonia datasets -- the only correlation that predicts "
        "ammonia -- NOT because it fits better. Any reading of this adoption as a choice "
        "on accuracy is wrong."
    ),
    structural_rejection=(
        "Kattan-Thome-Favrat (19.5 %) is rejected on STRUCTURE, not accuracy: its "
        "accuracy is earned by resolving gravitational flow-pattern regimes, the "
        "mechanism absent in orbit. Adopting a 1-g fit whose accuracy mechanism vanishes "
        "is not adoption. Same ground as the Gungor-Winterton (1986) Froude "
        "stratification de-rating already stripped at registry/two_phase.py:379."
    ),
    # --- SCOPE. See AMMONIA_HTC_SCOPE_AUTHORITY immediately below: this wording is the
    # BUILDER'S, under the Director's choice at D84. It is not his prose.
    scope=AMMONIA_HTC_SCOPE,
)


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
    d = AMMONIA_HTC_DISPOSITION
    return (
        "retired",
        f"D-6 retires at S5 as its own text says. Dispositioned {d.disposition} on "
        f"{d.acted_on} at {d.measurement.deviation_percent} % -- which is NOT the best "
        f"recorded deviation. {d.accuracy_disclaimer} {d.structural_rejection}",
    )
