"""Stage 2, milestone S2: two-phase acquisition / evaporator (screening level).

The executable form of the physics the S1 two-phase registry names: vapour quality and
loop state, the flow-boiling heat-transfer coefficient, the ONB / saturated-regime
policy, the CHF / dryout bands, and the local-wall-flux discipline.

**Screening level, no coupled solve.** This module evaluates an acquisition section at
a stated operating point and classifies it. It does not solve a loop, a condenser or a
radiator boundary together (that is S4), and it computes no pressure drop (S3).

What the OTB-G001 review changed
--------------------------------

The first S2 build recorded constraints it never enforced. Five findings were that one
defect in different clothes, and the fix is a single mechanism --
:mod:`orbital_thermal.registry.applicability` -- through which every declared axis
(fluid, geometry, orientation, regime, provenance) becomes binding. This module is its
consumer, and the rule it honours is that **a violation changes the case status; it is
never merely appended to a list of reasons.**

Concretely:

* **Sourced inputs are typed, not implied.** A CHF value arrives as a
  :class:`ChfResult` that binds value, source entry, evaluated domain, fluid, geometry
  and provenance -- a bare float is no longer accepted anywhere on the assessment path.
  An ONB criterion arrives as an :class:`OnbCriterion` that is *evaluated*; object
  presence is not evidence.
* **State is bound.** Properties arrive as a
  :class:`~orbital_thermal.fluids.SaturationState` carrying its own fluid, pressure and
  backend version, and are validated against the :class:`LoopState` before evaluation,
  so the domain that was guarded is the domain that is evaluated.
* **The guarded wrapper has no bypass.** :func:`flow_boiling_htc` always range-checks.
  Explicitly labelled non-ranking analysis uses the low-level pure evaluator in the
  registry, which is a separate, obviously-unguarded seam.

Gravity basis
-------------

Every correlation reached from here is a **1-g reference correlation**. One of them,
Shah (1987), is *gravity-explicit* -- its correlating parameter divides by ``g`` -- so
it has no microgravity limit at all. Nothing here is microgravity-validated and no such
claim is made.

This module is stdlib-only.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from enum import Enum

from . import _validate as _v
from .registry import NotRankEligibleError, assert_in_domain, get
from .registry.applicability import Axis, Consequence, Violation
from .registry.two_phase import (
    STANDARD_GRAVITY_M_S2,
    gungor_winterton_1986_htc,
    shah_1987_chf,
    shah_1987_Y,
)

#: Registry ids this module evaluates against.
HTC_ID = "two_phase.htc.gungor_winterton"
CHF_ID = "two_phase.chf.shah_1987"
CHF_SUPERSEDED_ID = "two_phase.chf.shah_2015"
ONB_ID = "two_phase.onb.bergles_rohsenow"

#: Director ruling A5: a ranked case needs q''/CHF at or below this.
CHF_RANK_MAX = 0.5
#: At or above this ratio the section is in dryout and the case is rejected.
CHF_DRYOUT = 1.0


# --- vocabulary -----------------------------------------------------------------


class Regime(str, Enum):
    """Thermodynamic regime of the acquisition section at the evaluated point."""

    SUBCOOLED_LIQUID = "subcooled_liquid"
    SATURATED_TWO_PHASE = "saturated_two_phase"
    SUPERHEATED_VAPOUR = "superheated_vapour"


class RankStatus(str, Enum):
    """How a case may be used in Stage-2 reporting.

    Only ``RANK_ELIGIBLE`` is rankable. The other three are all non-rankable for
    different reasons, and the distinction is kept because they mean different things
    to a reviewer.
    """

    RANK_ELIGIBLE = "rank_eligible"
    SENSITIVITY_ONLY = "sensitivity_only"
    REJECTED = "rejected"
    BLOCKED = "blocked"


_STATUS_SEVERITY = {
    RankStatus.RANK_ELIGIBLE: 0,
    RankStatus.SENSITIVITY_ONLY: 1,
    RankStatus.REJECTED: 2,
    RankStatus.BLOCKED: 3,
}

#: How an applicability consequence maps onto a case status. The registry defines
#: consequences without knowing about Stage-2 statuses; this is the one place the two
#: vocabularies meet.
_CONSEQUENCE_TO_STATUS = {
    Consequence.DE_RANK: RankStatus.SENSITIVITY_ONLY,
    Consequence.REJECT: RankStatus.REJECTED,
    Consequence.BLOCK: RankStatus.BLOCKED,
}


def _worst(*statuses: RankStatus) -> RankStatus:
    return max(statuses, key=lambda s: _STATUS_SEVERITY[s])


class FluxBasis(str, Enum):
    """How a wall heat flux was obtained (S0 Sec. 3 / Sec. 5)."""

    LOCAL_SOURCED = "local_sourced"
    SECTION_AVERAGE = "section_average"
    CHIP_AVERAGE = "chip_average"


_NON_LOCAL_BASES = frozenset({FluxBasis.SECTION_AVERAGE, FluxBasis.CHIP_AVERAGE})


@dataclass(frozen=True)
class ChannelGeometry:
    """The channel a case is evaluated in, with whether it is sourced.

    Geometry is a *declared* axis of both implemented correlations, and channel
    geometry is source-required (S0 Sec. 5, DEBTS D-5). Carrying the shape and the
    sourced flag together is what lets the applicability mechanism enforce the geometry
    axis instead of checking a hydraulic diameter as a bare number (DEBTS D-9).
    """

    shape: str  # e.g. "round_tube", "annulus", "rectangular_channel"
    hydraulic_diameter_m: float
    orientation: str = "vertical_upflow"
    heated_length_m: float | None = None
    sourced: bool = False
    source_note: str = ""


# --- T2: loop state and vapour quality ------------------------------------------


@dataclass(frozen=True)
class LoopState:
    """The two-phase loop state at a point: pressure, enthalpy, quality, regime."""

    pressure_Pa: float
    enthalpy_J_kg: float
    h_f_J_kg: float
    h_g_J_kg: float
    h_fg_J_kg: float
    equilibrium_quality: float
    quality: float | None
    regime: Regime

    @property
    def is_two_phase(self) -> bool:
        return self.regime is Regime.SATURATED_TWO_PHASE


def vapour_quality(enthalpy_J_kg: float, h_f_J_kg: float, h_fg_J_kg: float) -> float:
    """Vapour quality ``x = (h - h_f) / h_fg`` (S0 Sec. 3), enforced to ``[0, 1]``.

    Raises outside the two-phase dome rather than clamping: a clamped quality would
    silently turn a subcooled or superheated state into a saturated one.
    """
    _v.finite("enthalpy_J_kg", enthalpy_J_kg)
    _v.finite("h_f_J_kg", h_f_J_kg)
    _v.positive("h_fg_J_kg", h_fg_J_kg)
    x = (enthalpy_J_kg - h_f_J_kg) / h_fg_J_kg
    if not (0.0 <= x <= 1.0):
        raise ValueError(
            f"vapour quality x = {x:.6g} is outside the physical range [0, 1]; "
            "the state is not saturated two-phase (use loop_state to classify it)"
        )
    return x


def loop_state(
    *,
    pressure_Pa: float,
    enthalpy_J_kg: float,
    h_f_J_kg: float,
    h_g_J_kg: float,
) -> LoopState:
    """Classify a loop state from its pressure and enthalpy."""
    _v.positive("pressure_Pa", pressure_Pa)
    _v.finite("enthalpy_J_kg", enthalpy_J_kg)
    if not h_g_J_kg > h_f_J_kg:
        raise ValueError(
            f"h_g ({h_g_J_kg}) must exceed h_f ({h_f_J_kg}); the saturation "
            "enthalpies do not bracket a two-phase dome"
        )
    h_fg = h_g_J_kg - h_f_J_kg
    x_eq = (enthalpy_J_kg - h_f_J_kg) / h_fg

    if x_eq < 0.0:
        regime, x = Regime.SUBCOOLED_LIQUID, None
    elif x_eq > 1.0:
        regime, x = Regime.SUPERHEATED_VAPOUR, None
    else:
        regime, x = Regime.SATURATED_TWO_PHASE, x_eq

    return LoopState(
        pressure_Pa=pressure_Pa,
        enthalpy_J_kg=enthalpy_J_kg,
        h_f_J_kg=h_f_J_kg,
        h_g_J_kg=h_g_J_kg,
        h_fg_J_kg=h_fg,
        equilibrium_quality=x_eq,
        quality=x,
        regime=regime,
    )


def loop_state_from(state, *, enthalpy_J_kg: float) -> LoopState:
    """Build a :class:`LoopState` from a bound
    :class:`~orbital_thermal.fluids.SaturationState`.

    Preferred over :func:`loop_state` because the saturation enthalpies and the
    pressure then provably come from the same evaluated state (OTB-G001 F-05).
    """
    return loop_state(
        pressure_Pa=state.pressure_Pa,
        enthalpy_J_kg=enthalpy_J_kg,
        h_f_J_kg=state.h_f_J_kg,
        h_g_J_kg=state.h_g_J_kg,
    )


def assert_state_consistent(loop: LoopState, state, *, fluid: str | None = None) -> None:
    """Raise unless ``state`` is genuinely the saturation state of ``loop``.

    OTB-G001-FIXES **F-03**: the previous guard called
    ``state.matches(fluid=state.fluid, ...)`` -- it compared the state's fluid field to
    *itself*, so it was true for every input and no relabelling could ever fail it. An
    ammonia state relabelled ``"Water"``, every ammonia property intact, passed.

    Three things are now checked, and the second is the one that cannot be faked:

    1. the state's pressure is the loop's pressure;
    2. the state's **properties really are** those of ``fluid`` -- re-derived from the
       backend and compared across the full property set, plus the backend and its
       version (:meth:`~orbital_thermal.fluids.SaturationState.verify_is`);
    3. the loop's saturation enthalpies came from this state.

    ``fluid`` is the **case's** declared fluid, giving a second, independent statement
    of identity that the state must agree with. It defaults to the state's own label
    and step 2 runs **either way** -- making it conditional would rebuild the hole,
    because a caller that simply omitted the argument would be back to trusting the
    label. Verification catches a relabelled state even against its own label, since
    what it compares is the re-derived properties, not the string.
    """
    if not state.matches(fluid=state.fluid, pressure_Pa=loop.pressure_Pa):
        raise NotRankEligibleError(
            f"saturation state for '{state.fluid}' was evaluated at "
            f"{state.pressure_Pa:.6g} Pa but the loop state is at "
            f"{loop.pressure_Pa:.6g} Pa: the guarded domain would not be the evaluated "
            "domain"
        )

    try:
        state.verify_is(state.fluid if fluid is None else fluid)
    except ValueError as exc:
        raise NotRankEligibleError(str(exc)) from exc

    for name in ("h_f_J_kg", "h_g_J_kg"):
        mine, theirs = getattr(state, name), getattr(loop, name)
        if abs(mine - theirs) > 1e-6 * max(abs(mine), 1.0):
            raise NotRankEligibleError(
                f"the loop state's {name} does not come from this saturation state; "
                "build the loop state with loop_state_from(state, ...)"
            )


# --- T6: local wall heat flux discipline ----------------------------------------


@dataclass(frozen=True)
class WallHeatFlux:
    """A wall heat flux together with **how it was obtained**."""

    value_W_m2: float
    basis: FluxBasis
    geometry_sourced: bool
    note: str = ""

    @property
    def is_rankable_basis(self) -> bool:
        """True only for a local flux derived from sourced geometry."""
        return self.basis is FluxBasis.LOCAL_SOURCED and self.geometry_sourced


def local_wall_heat_flux(
    *, power_W: float, wetted_area_m2: float, geometry_sourced: bool, note: str = ""
) -> WallHeatFlux:
    """Build a **local** wall heat flux from channel geometry."""
    _v.nonneg("power_W", power_W)
    _v.positive("wetted_area_m2", wetted_area_m2)
    _v.boolean("geometry_sourced", geometry_sourced)
    return WallHeatFlux(
        value_W_m2=power_W / wetted_area_m2,
        basis=FluxBasis.LOCAL_SOURCED,
        geometry_sourced=geometry_sourced,
        note=note,
    )


def averaged_wall_heat_flux(
    *, power_W: float, area_m2: float, basis: FluxBasis, note: str = ""
) -> WallHeatFlux:
    """Build an explicitly-named **average** wall heat flux, which is never rankable."""
    _v.nonneg("power_W", power_W)
    _v.positive("area_m2", area_m2)
    if basis not in _NON_LOCAL_BASES:
        raise ValueError(
            f"averaged_wall_heat_flux requires an averaging basis "
            f"({', '.join(sorted(b.value for b in _NON_LOCAL_BASES))}), got "
            f"'{basis.value}'; use local_wall_heat_flux for a local flux"
        )
    return WallHeatFlux(
        value_W_m2=power_W / area_m2,
        basis=basis,
        geometry_sourced=False,
        note=note,
    )


# --- F-01: a typed ONB criterion that is EVALUATED ------------------------------


@dataclass(frozen=True)
class OnbResult:
    """The outcome of evaluating an ONB criterion at a point."""

    above_onb: bool
    incipient_flux_W_m2: float | None
    detail: str


class OnbCriterion:
    """Base class for a **sourced, evaluated** onset-of-nucleate-boiling criterion.

    OTB-G001 F-01: the previous gate accepted any non-``None`` object as evidence that
    ONB had been established -- ``"banana"`` set ``sourced=True`` -- and never called
    it. Bulk equilibrium quality and local boiling incipience are different boundaries:
    subcooled boiling can occur while equilibrium quality is negative, and saturated
    liquid at ``x = 0`` is not by itself proof that ONB has been crossed.

    A criterion must therefore be an instance of this class, declare the fluids it is
    valid for, and **return a result** from :meth:`evaluate`. No such criterion is
    implemented in this build: three independent sources confirm the published
    Bergles & Rohsenow criterion has no closed form, and the usual algebraic surrogate
    is water-only (DEBTS D-3). The entry stays ``SOURCE_REQUIRED``; the policy gate
    ships regardless.
    """

    #: Fluids this criterion is sourced for. Empty means "none declared", which the
    #: gate treats as not usable rather than as universally valid.
    valid_fluids: frozenset[str] = frozenset()
    citation: str = ""

    def evaluate(
        self, *, wall_flux_W_m2: float, state, quality: float
    ) -> OnbResult:  # pragma: no cover - abstract
        raise NotImplementedError(
            "an ONB criterion must evaluate; see DEBTS D-3 for why none is implemented"
        )

    def applies_to(self, fluid: str) -> bool:
        return fluid.strip().lower() in {f.lower() for f in self.valid_fluids}


@dataclass(frozen=True)
class RegimeAssessment:
    """Outcome of the ONB / saturated-regime gate."""

    regime: Regime
    status: RankStatus
    onb_evaluated: bool
    onb_result: OnbResult | None
    reason: str


def classify_regime(
    state: LoopState,
    *,
    onb_criterion: OnbCriterion | None = None,
    fluid: str | None = None,
    wall_flux_W_m2: float | None = None,
    saturation_state=None,
) -> RegimeAssessment:
    """Apply the S0 Sec. 3 (F2) ONB / saturated-regime rank policy.

    The gate ships unconditionally. A criterion is honoured **only if** it is an
    :class:`OnbCriterion`, is declared valid for the case's fluid, and returns a result
    when evaluated. Anything else -- including a non-``None`` object of the wrong type
    -- is treated as *no criterion*, which is the conservative direction.

    With no usable criterion, a state that is not unambiguously in saturated flow
    boiling cannot be shown to sit above ONB and is **sensitivity-only**. The saturated
    side is described as the bulk-equilibrium crossing, not as an established ONB
    transition (F-01).
    """
    usable = (
        isinstance(onb_criterion, OnbCriterion)
        and fluid is not None
        and onb_criterion.applies_to(fluid)
    )

    if state.regime is Regime.SUPERHEATED_VAPOUR:
        return RegimeAssessment(
            regime=state.regime,
            status=RankStatus.REJECTED,
            onb_evaluated=False,
            onb_result=None,
            reason=(
                "state is superheated vapour (x > 1): the wall is dry, and the "
                "implemented flow-boiling HTC is valid only while the wall is wetted"
            ),
        )

    onb_result: OnbResult | None = None
    if usable and wall_flux_W_m2 is not None:
        onb_result = onb_criterion.evaluate(
            wall_flux_W_m2=wall_flux_W_m2,
            state=saturation_state,
            quality=state.equilibrium_quality,
        )

    if state.regime is Regime.SUBCOOLED_LIQUID:
        if onb_result is not None and onb_result.above_onb:
            return RegimeAssessment(
                regime=state.regime,
                status=RankStatus.SENSITIVITY_ONLY,
                onb_evaluated=True,
                onb_result=onb_result,
                reason=(
                    "subcooled state evaluated ABOVE onset of nucleate boiling "
                    f"({onb_result.detail}); subcooled boiling is outside the "
                    "saturated flow-boiling regime this milestone ranks, so the case "
                    "is a sensitivity"
                ),
            )
        return RegimeAssessment(
            regime=state.regime,
            status=RankStatus.SENSITIVITY_ONLY,
            onb_evaluated=onb_result is not None,
            onb_result=onb_result,
            reason=(
                "state is subcooled liquid. "
                + (
                    f"ONB criterion evaluated: {onb_result.detail}."
                    if onb_result is not None
                    else "No sourced ONB criterion is implemented "
                    "(two_phase.onb.bergles_rohsenow is SOURCE_REQUIRED; DEBTS D-3), "
                    "so the case cannot be shown to sit above the onset of nucleate "
                    "boiling and is sensitivity-only per S0 Sec. 3 (F2)."
                )
            ),
        )

    return RegimeAssessment(
        regime=state.regime,
        status=RankStatus.RANK_ELIGIBLE,
        onb_evaluated=onb_result is not None,
        onb_result=onb_result,
        reason=(
            "state is at or above the bulk-equilibrium saturation crossing "
            f"(x = {state.equilibrium_quality:.4g}), i.e. in the saturated "
            "flow-boiling regime. "
            + (
                f"ONB criterion evaluated: {onb_result.detail}."
                if onb_result is not None
                else "NOTE: this is the bulk-equilibrium crossing, not an evaluated "
                "onset-of-nucleate-boiling transition -- no sourced ONB criterion "
                "exists (DEBTS D-3)."
            )
        ),
    )


# --- F-02: CHF as a validated, sourced result -----------------------------------


@dataclass(frozen=True)
class CaseBinding:
    """The identity of the case a computed value was produced for.

    OTB-G001-FIXES **F-02**: a result honestly produced for one state could otherwise
    be replayed against another, because no consumer compared the result's labels to
    the case in front of it. The binding is what makes that comparison possible.
    """

    fluid: str
    pressure_Pa: float
    geometry_shape: str
    hydraulic_diameter_m: float
    orientation: str
    mass_flux_kg_m2s: float
    gravity_m_s2: float

    def agrees_with(self, other: CaseBinding, *, rel_tol: float = 1e-9) -> list[str]:
        """Field-by-field differences against ``other`` (empty list == same case)."""
        diffs: list[str] = []
        for name in ("fluid", "geometry_shape", "orientation"):
            a, b = getattr(self, name), getattr(other, name)
            if a.strip().lower() != b.strip().lower():
                diffs.append(f"{name}: {a!r} vs {b!r}")
        for name in (
            "pressure_Pa",
            "hydraulic_diameter_m",
            "mass_flux_kg_m2s",
            "gravity_m_s2",
        ):
            a, b = getattr(self, name), getattr(other, name)
            if abs(a - b) > rel_tol * max(abs(a), abs(b), 1.0):
                diffs.append(f"{name}: {a!r} vs {b!r}")
        return diffs


def case_binding(
    *, state, geometry: ChannelGeometry, mass_flux_kg_m2s: float, gravity_m_s2: float
) -> CaseBinding:
    """Build the :class:`CaseBinding` for an operating point."""
    return CaseBinding(
        fluid=state.fluid,
        pressure_Pa=state.pressure_Pa,
        geometry_shape=geometry.shape,
        hydraulic_diameter_m=geometry.hydraulic_diameter_m,
        orientation=geometry.orientation,
        mass_flux_kg_m2s=mass_flux_kg_m2s,
        gravity_m_s2=gravity_m_s2,
    )


#: Module-private minting token. Only :func:`critical_heat_flux` holds it, which is
#: what makes a :class:`ChfResult` unconstructible from outside the evaluator.
_CHF_MINT = object()


@dataclass(frozen=True)
class ChfResult:
    """A CHF value bound to the evidence AND the case that produced it.

    OTB-G001-FIXES **F-02**. Round 1 wrapped a bare float in labels; a label nothing
    reads is not a fix. A hand-built result with ``correlation_id='not.a.real.id'``,
    ``fluid='Unobtainium'`` and ``value_W_m2=9.9e9`` reported ``is_sourced=True`` and
    banded ``RANK_ELIGIBLE``. Two things were needed and neither alone suffices:

    * **Unconstructible from outside the evaluator.** Direct construction raises --
      only :func:`critical_heat_flux` holds the minting token. Fabricating one is not
      merely detected, it is refused.
    * **The consumer verifies.** :func:`classify_chf_band` requires the case's own
      binding and compares it to :attr:`binding`, so a result produced honestly for
      one state cannot be replayed against another.
    """

    value_W_m2: float
    correlation_id: str
    citation: str
    locator: str
    fluid: str
    geometry: str
    evaluated_domain: dict[str, float]
    gravity_m_s2: float
    #: Defaulted only so that a direct construction attempt reaches ``__post_init__``
    #: and gets the explanatory refusal, rather than an arity error that says nothing
    #: about why hand-building one is not allowed. A minted result always has it.
    binding: CaseBinding | None = None
    violations: tuple[Violation, ...] = ()
    #: Label-level caveats that must travel with the value (e.g. a conflicted numeric
    #: domain). Recorded, not status-altering -- Director ruling D1 relabels such a
    #: constraint rather than weaponising it.
    caveats: tuple[str, ...] = ()
    _mint: InitVar[object] = None

    def __post_init__(self, _mint: object) -> None:
        if _mint is not _CHF_MINT:
            raise TypeError(
                "ChfResult cannot be constructed directly: it asserts that a CHF value "
                "was produced by a sourced correlation for a specific case, and a "
                "hand-built one asserts that falsely. Obtain one from "
                "critical_heat_flux(), which mints it only after every applicability "
                "axis and the declared numeric domain have been satisfied "
                "(OTB-G001-FIXES F-02)."
            )
        if self.binding is None:
            raise TypeError("a minted ChfResult must carry the case binding it was produced for")

    @property
    def is_sourced(self) -> bool:
        """True only when nothing on any declared applicability axis was violated."""
        return not self.violations


def _check_applicability(
    entry,
    *,
    fluid: str | None,
    geometry: ChannelGeometry | None,
    liquid_reynolds: float | None,
    gravity_m_s2: float | None,
    branch_value: float | None = None,
    branch_value_at_reference_gravity: float | None = None,
) -> tuple[Violation, ...]:
    """Run an entry's applicability spec, if it declares one."""
    spec = entry.applicability_spec
    if spec is None:
        return ()
    return spec.check(
        fluid=fluid,
        geometry=None if geometry is None else geometry.shape,
        orientation=None if geometry is None else geometry.orientation,
        liquid_reynolds=liquid_reynolds,
        gravity_m_s2=gravity_m_s2,
        branch_value=branch_value,
        branch_value_at_reference_gravity=branch_value_at_reference_gravity,
        has_executable_form=entry.evaluate is not None,
    )


def critical_heat_flux(
    *,
    state,
    geometry: ChannelGeometry,
    mass_flux_kg_m2s: float,
    inlet_quality: float,
    critical_quality: float,
    gravity_m_s2: float = STANDARD_GRAVITY_M_S2,
) -> ChfResult:
    """Evaluate the CHF reference correlation into a validated :class:`ChfResult`.

    The reference is Shah (1987) (Director ruling D3). Every declared applicability
    axis is checked and every declared numeric bound enforced before a value is
    produced; a violation is recorded *on the result*, and a result carrying violations
    is not ``is_sourced`` and cannot rank.

    Raises ``NotRankEligibleError`` when the case cannot produce a value at all --
    unsourced geometry, a missing heated length, or an applicability failure whose
    consequence is ``BLOCK`` or ``REJECT``.
    """
    entry = get(CHF_ID)
    if geometry.heated_length_m is None:
        raise NotRankEligibleError(
            f"'{CHF_ID}' needs the heated length to the CHF location, which this "
            "geometry does not state; channel geometry is source-required (DEBTS D-5)"
        )
    if not geometry.sourced:
        raise NotRankEligibleError(
            f"'{CHF_ID}' was asked to evaluate on unsourced channel geometry "
            f"({geometry.shape}); geometry is source-required (S0 Sec. 5, DEBTS D-5), "
            "so no CHF value is produced"
        )

    # The correlating parameter at the stated gravity and at the gravity the database
    # was taken at. Both are needed for the branch-straddle test: gravity moving a case
    # across Shah's own Y >= 1e6 boundary changes the calculation procedure, whereas
    # crossing it at 1 g under high mass flux is ordinary and must not be flagged.
    y_kwargs = dict(
        mass_flux_kg_m2s=mass_flux_kg_m2s,
        diameter_m=geometry.hydraulic_diameter_m,
        cp_f=state.cp_f_J_kgK,
        k_f=state.k_f_W_mK,
        rho_f=state.rho_f_kg_m3,
        mu_f=state.mu_f_Pa_s,
        mu_g=state.mu_g_Pa_s,
    )
    y_here = shah_1987_Y(**y_kwargs, gravity_m_s2=gravity_m_s2) if gravity_m_s2 > 0 else None
    y_ref = shah_1987_Y(**y_kwargs, gravity_m_s2=STANDARD_GRAVITY_M_S2)

    violations = _check_applicability(
        entry,
        fluid=state.fluid,
        geometry=geometry,
        liquid_reynolds=None,
        gravity_m_s2=gravity_m_s2,
        branch_value=y_here,
        branch_value_at_reference_gravity=y_ref,
    )
    blocking = [
        v for v in violations if v.consequence in (Consequence.BLOCK, Consequence.REJECT)
    ]
    if blocking:
        raise NotRankEligibleError(
            f"'{entry.id}' is not applicable to this case: "
            + "; ".join(str(v) for v in blocking)
        )

    assert_in_domain(
        entry,
        context="S2 CHF",
        pr_reduced=state.p_reduced,
        D_m=geometry.hydraulic_diameter_m,
        G_kg_m2s=mass_flux_kg_m2s,
        critical_quality=critical_quality,
        inlet_quality=inlet_quality,
    )

    value = shah_1987_chf(
        mass_flux_kg_m2s=mass_flux_kg_m2s,
        h_fg_J_kg=state.h_fg_J_kg,
        diameter_m=geometry.hydraulic_diameter_m,
        length_to_chf_m=geometry.heated_length_m,
        p_reduced=state.p_reduced,
        inlet_quality=inlet_quality,
        critical_quality=critical_quality,
        cp_f=state.cp_f_J_kgK,
        k_f=state.k_f_W_mK,
        rho_f=state.rho_f_kg_m3,
        mu_f=state.mu_f_Pa_s,
        mu_g=state.mu_g_Pa_s,
        gravity_m_s2=gravity_m_s2,
    )
    return ChfResult(
        value_W_m2=value,
        correlation_id=entry.id,
        citation=entry.source.citation,
        locator=entry.source.locator,
        fluid=state.fluid,
        geometry=geometry.shape,
        evaluated_domain={
            "pr_reduced": state.p_reduced,
            "D_m": geometry.hydraulic_diameter_m,
            "G_kg_m2s": mass_flux_kg_m2s,
            "critical_quality": critical_quality,
        },
        gravity_m_s2=gravity_m_s2,
        binding=case_binding(
            state=state,
            geometry=geometry,
            mass_flux_kg_m2s=mass_flux_kg_m2s,
            gravity_m_s2=gravity_m_s2,
        ),
        violations=violations,
        caveats=entry.applicability_spec.provenance_caveats()
        if entry.applicability_spec is not None
        else (),
        _mint=_CHF_MINT,
    )


@dataclass(frozen=True)
class ChfAssessment:
    """Outcome of the CHF / dryout banding gate (Director ruling A5)."""

    ratio: float
    status: RankStatus
    reason: str


def classify_chf_band(
    wall_flux: WallHeatFlux, chf: ChfResult, *, binding: CaseBinding
) -> ChfAssessment:
    """Band a case by ``q'' / CHF`` per S0 Sec. 3 and Director ruling A5.

    ``q''/CHF <= 0.5`` rank-eligible; ``0.5 < q''/CHF < 1`` sensitivity-only, reported
    but not ranked; ``q''/CHF >= 1`` dryout, rejected. A **modelling margin, not
    flight certification.**

    ``binding`` is the **case's own** identity, and the result's binding must match it.
    That is the consumer half of OTB-G001-FIXES F-02: without it a CHF honestly
    produced for one state could be handed to the band function alongside a different
    state's wall flux, and nothing would notice. Being unforgeable is not enough if
    nobody checks who it was made for.
    """
    if not isinstance(chf, ChfResult):
        raise TypeError(
            "classify_chf_band requires a ChfResult binding value, source, domain, "
            f"fluid, geometry and provenance -- got {type(chf).__name__}. A naked CHF "
            "number is not evidence that a sourced CHF exists (OTB-G001 F-02)."
        )
    diffs = chf.binding.agrees_with(binding)
    if diffs:
        raise NotRankEligibleError(
            "the CHF value was produced for a different case than the one being "
            f"banded: {'; '.join(diffs)}. A CHF is only evidence about the case it was "
            "evaluated for."
        )
    _v.positive("chf.value_W_m2", chf.value_W_m2)
    ratio = wall_flux.value_W_m2 / chf.value_W_m2

    if ratio >= CHF_DRYOUT:
        return ChfAssessment(
            ratio=ratio,
            status=RankStatus.REJECTED,
            reason=f"q''/CHF = {ratio:.4g} >= {CHF_DRYOUT:g}: dryout, case rejected",
        )

    if ratio > CHF_RANK_MAX:
        return ChfAssessment(
            ratio=ratio,
            status=RankStatus.SENSITIVITY_ONLY,
            reason=(
                f"q''/CHF = {ratio:.4g} is in the parametric band "
                f"({CHF_RANK_MAX:g} < q''/CHF < {CHF_DRYOUT:g}): reported as a "
                "sensitivity, not ranked"
            ),
        )

    if not wall_flux.is_rankable_basis:
        return ChfAssessment(
            ratio=ratio,
            status=RankStatus.SENSITIVITY_ONLY,
            reason=(
                f"q''/CHF = {ratio:.4g} is inside the rank band, but the flux basis is "
                f"'{wall_flux.basis.value}' with geometry_sourced="
                f"{wall_flux.geometry_sourced}: q''/CHF must be computed on the local "
                "modeled wall flux from sourced geometry (S0 Sec. 3)"
            ),
        )

    if not chf.is_sourced:
        return ChfAssessment(
            ratio=ratio,
            status=RankStatus.SENSITIVITY_ONLY,
            reason=(
                f"q''/CHF = {ratio:.4g} is inside the rank band, but the CHF value "
                "carries applicability violations: "
                + "; ".join(str(v) for v in chf.violations)
            ),
        )

    return ChfAssessment(
        ratio=ratio,
        status=RankStatus.RANK_ELIGIBLE,
        reason=f"q''/CHF = {ratio:.4g} <= {CHF_RANK_MAX:g}: within the ranked margin",
    )


# --- T3: flow-boiling HTC through the registry ----------------------------------


@dataclass(frozen=True)
class HtcResult:
    """A flow-boiling coefficient together with the applicability verdict on it.

    OTB-G001-FIXES **F-04**: the wrapper used to return a bare ``float``, so there was
    nowhere to put violations and the mechanism was simply never called -- applicability
    was a caller convention that only :func:`assess_acquisition` happened to follow. A
    ``float`` cannot carry a verdict, so the return type had to change with it.
    """

    value_W_m2: float
    violations: tuple[Violation, ...] = ()
    caveats: tuple[str, ...] = ()

    @property
    def is_applicable(self) -> bool:
        """True only when no declared applicability axis was violated."""
        return not self.violations


def flow_boiling_htc(
    *,
    mass_flux_kg_m2s: float,
    quality: float,
    wall_flux: WallHeatFlux,
    geometry: ChannelGeometry,
    state,
    fluid: str | None = None,
    loop: LoopState | None = None,
    gravity_m_s2: float = STANDARD_GRAVITY_M_S2,
) -> HtcResult:
    """Flow-boiling HTC from ``two_phase.htc.gungor_winterton``.

    **This is the enforcement boundary, not a call site.** Everything outside the
    module reaches the correlation through here, so the applicability mechanism runs
    here -- previously it ran only inside :func:`assess_acquisition`, which made
    class-level enforcement a convention a caller could simply not follow. Measured
    before the fix: this function returned 20,687.1 W/m^2/K for **ammonia**, which is
    outside Gungor & Winterton's development database, with no violation raised or
    reported.

    Behaviour, and why it is split this way:

    * ``BLOCK`` or ``REJECT`` on any axis -> **raises**. The value would be meaningless.
    * ``DE_RANK`` -> **returns** an :class:`HtcResult` carrying the value *and* the
      violations. It does not raise, because ammonia must remain evaluable as a
      **sensitivity** (Director ruling D4 de-ranks it rather than blocking it); raising
      would wrongly escalate every de-ranked coolant to rejected.

    Checking applicability and discarding the answer is explicitly excluded, so the
    violations are on the return value and every caller moves with them.

    **Always range-checked**; there is no domain bypass. Explicitly labelled non-ranking
    analysis calls :func:`~orbital_thermal.registry.two_phase.gungor_winterton_1986_htc`
    directly, which is an obviously unguarded seam.

    ``fluid`` is the case's declared fluid, used to verify the state really is that
    fluid rather than merely labelled so (F-03).
    """
    entry = get(HTC_ID)
    if loop is not None:
        assert_state_consistent(loop, state, fluid=fluid)
    else:
        # No loop to cross-check against, but the state's identity is still verified --
        # unconditionally, for the same reason as in assert_state_consistent.
        try:
            state.verify_is(state.fluid if fluid is None else fluid)
        except ValueError as exc:
            raise NotRankEligibleError(str(exc)) from exc

    assert_in_domain(
        entry,
        context="S2 flow-boiling HTC",
        G_kg_m2s=mass_flux_kg_m2s,
        q_flux_W_m2=wall_flux.value_W_m2,
        quality=quality,
        P_Pa=state.pressure_Pa,
        D_m=geometry.hydraulic_diameter_m,
    )

    violations = _check_applicability(
        entry,
        fluid=state.fluid,
        geometry=geometry,
        liquid_reynolds=state.liquid_reynolds(
            mass_flux_kg_m2s=mass_flux_kg_m2s,
            quality=quality,
            diameter_m=geometry.hydraulic_diameter_m,
        ),
        gravity_m_s2=gravity_m_s2,
    )
    blocking = [
        v for v in violations if v.consequence in (Consequence.BLOCK, Consequence.REJECT)
    ]
    if blocking:
        raise NotRankEligibleError(
            f"'{entry.id}' is not applicable to this case: "
            + "; ".join(str(v) for v in blocking)
        )

    value = gungor_winterton_1986_htc(
        mass_flux_kg_m2s=mass_flux_kg_m2s,
        quality=quality,
        q_flux_W_m2=wall_flux.value_W_m2,
        diameter_m=geometry.hydraulic_diameter_m,
        rho_f=state.rho_f_kg_m3,
        rho_g=state.rho_g_kg_m3,
        mu_f=state.mu_f_Pa_s,
        mu_g=state.mu_g_Pa_s,
        k_f=state.k_f_W_mK,
        cp_f=state.cp_f_J_kgK,
        h_fg_J_kg=state.h_fg_J_kg,
        p_reduced=state.p_reduced,
        molar_mass_g_mol=state.molar_mass_g_mol,
    )
    spec = entry.applicability_spec
    return HtcResult(
        value_W_m2=value,
        violations=violations,
        caveats=spec.provenance_caveats() if spec is not None else (),
    )


# --- combined screening assessment ----------------------------------------------


@dataclass(frozen=True)
class AcquisitionAssessment:
    """Screening-level verdict for one acquisition (evaporator) operating point."""

    loop: LoopState
    regime: RegimeAssessment
    chf: ChfAssessment | None
    htc_W_m2K: float | None
    status: RankStatus
    reasons: tuple[str, ...]
    violations: tuple[Violation, ...] = field(default_factory=tuple)
    #: Label-level caveats carried with the result without altering its status.
    caveats: tuple[str, ...] = field(default_factory=tuple)

    @property
    def rankable(self) -> bool:
        return self.status is RankStatus.RANK_ELIGIBLE


def assess_acquisition(
    *,
    loop: LoopState,
    state,
    geometry: ChannelGeometry,
    wall_flux: WallHeatFlux,
    mass_flux_kg_m2s: float,
    chf: ChfResult | None = None,
    onb_criterion: OnbCriterion | None = None,
    gravity_m_s2: float = STANDARD_GRAVITY_M_S2,
    fluid: str | None = None,
) -> AcquisitionAssessment:
    """Run every S2 gate over one operating point and combine them.

    The combined status is the **worst** of the gate outcomes, so no gate can be
    outvoted by a more permissive one.

    **Applicability violations alter the status** (OTB-G001 F-04). The previous build
    appended a warning and deliberately did not worsen the verdict, so the reference
    coolant could rank on a correlation outside its documented fluid basis. Recording
    an applicability failure is not enforcing it.
    """
    assert_state_consistent(loop, state, fluid=fluid or state.fluid)
    reasons: list[str] = []
    binding = case_binding(
        state=state,
        geometry=geometry,
        mass_flux_kg_m2s=mass_flux_kg_m2s,
        gravity_m_s2=gravity_m_s2,
    )

    regime = classify_regime(
        loop,
        onb_criterion=onb_criterion,
        fluid=state.fluid,
        wall_flux_W_m2=wall_flux.value_W_m2,
        saturation_state=state,
    )
    reasons.append(regime.reason)
    status = regime.status

    # --- the one enforcement mechanism, applied to the HTC entry ---
    re_l = state.liquid_reynolds(
        mass_flux_kg_m2s=mass_flux_kg_m2s,
        quality=loop.quality if loop.quality is not None else 0.0,
        diameter_m=geometry.hydraulic_diameter_m,
    )
    htc_entry = get(HTC_ID)
    violations = _check_applicability(
        htc_entry,
        fluid=state.fluid,
        geometry=geometry,
        liquid_reynolds=re_l,
        gravity_m_s2=gravity_m_s2,
    )
    caveats: list[str] = []
    if htc_entry.applicability_spec is not None:
        caveats.extend(htc_entry.applicability_spec.provenance_caveats())
    if chf is not None:
        caveats.extend(f"CHF: {c}" for c in chf.caveats)
    for v in violations:  # noqa: B007 - loop body below folds each into the status
        reasons.append(str(v))
        status = _worst(status, _CONSEQUENCE_TO_STATUS[v.consequence])

    if not wall_flux.is_rankable_basis:
        reasons.append(
            f"wall heat flux basis is '{wall_flux.basis.value}' "
            f"(geometry_sourced={wall_flux.geometry_sourced}); channel geometry is "
            "source-required (S0 Sec. 5), so the case cannot be ranked on it"
        )
        status = _worst(status, RankStatus.SENSITIVITY_ONLY)

    if chf is None:
        chf_assessment = None
        reasons.append(
            "no validated CHF result supplied: the CHF band cannot be evaluated, so "
            "the case is blocked rather than assumed below CHF"
        )
        status = _worst(status, RankStatus.BLOCKED)
    else:
        chf_assessment = classify_chf_band(wall_flux, chf, binding=binding)
        reasons.append(chf_assessment.reason)
        status = _worst(status, chf_assessment.status)
        for v in chf.violations:
            reasons.append(f"CHF: {v}")
            status = _worst(status, _CONSEQUENCE_TO_STATUS[v.consequence])

    htc: float | None = None
    if loop.is_two_phase and loop.quality is not None:
        try:
            htc_result = flow_boiling_htc(
                mass_flux_kg_m2s=mass_flux_kg_m2s,
                quality=loop.quality,
                wall_flux=wall_flux,
                geometry=geometry,
                state=state,
                fluid=fluid or state.fluid,
                loop=loop,
                gravity_m_s2=gravity_m_s2,
            )
            htc = htc_result.value_W_m2
        except NotRankEligibleError as exc:
            reasons.append(f"HTC not evaluated: {exc}")
            status = _worst(status, RankStatus.REJECTED)

    return AcquisitionAssessment(
        loop=loop,
        regime=regime,
        chf=chf_assessment,
        htc_W_m2K=htc,
        status=status,
        reasons=tuple(reasons),
        violations=violations,
        caveats=tuple(caveats),
    )


__all__ = [
    "CHF_DRYOUT",
    "CHF_RANK_MAX",
    "CHF_ID",
    "CHF_SUPERSEDED_ID",
    "HTC_ID",
    "ONB_ID",
    "STANDARD_GRAVITY_M_S2",
    "AcquisitionAssessment",
    "Axis",
    "CaseBinding",
    "ChannelGeometry",
    "ChfAssessment",
    "ChfResult",
    "Consequence",
    "FluxBasis",
    "HtcResult",
    "case_binding",
    "LoopState",
    "OnbCriterion",
    "OnbResult",
    "Regime",
    "RegimeAssessment",
    "RankStatus",
    "Violation",
    "WallHeatFlux",
    "assert_state_consistent",
    "assess_acquisition",
    "averaged_wall_heat_flux",
    "classify_chf_band",
    "classify_regime",
    "critical_heat_flux",
    "flow_boiling_htc",
    "local_wall_heat_flux",
    "loop_state",
    "loop_state_from",
    "vapour_quality",
]
