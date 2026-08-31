"""S6 (``OTB-G006``): the two-phase trade-study extension.

S5 answered *which coolants are rank-eligible*. **S6 uses that answer to rank**, and
ranks nothing it is not entitled to rank.

**This module adds no physics.** Every number here is produced by an S1-S5 boundary --
:func:`orbital_thermal.two_phase.critical_heat_flux`,
:func:`orbital_thermal.two_phase_loop.two_phase_pressure_drop`,
:func:`orbital_thermal.two_phase_loop.pump_inlet_feasibility`, and
:func:`orbital_thermal.pumped_loop.pump_energy` -- and this module maps their verdicts
onto the Stage-1 ranking vocabulary. The mapping is the milestone's new claim; the
values are inherited.

**The eligibility source is the PRODUCTION applicability result, never**
``two_phase_architecture_cases.assess_leg``. That boundary has no mass flux, no numeric
diameter and no fluid state, so it cannot derive the branch parameter and refuses to
pretend it checked: measured at ``8e094d9`` it blocks every fluid on ``geometry`` and
``orientation``, both ``Cause.NOT_EVALUATED``. A trade study built on it would produce
an empty front for the wrong reason. Here the case is stated, so the axes are evaluated
and the verdicts are real.

**Eligibility is PER LEG, because applicability is.** Measured at ``8e094d9``:

===============  ===========================  ==============================
leg              Ammonia                      Water
===============  ===========================  ==============================
CHF              ``fluid`` DE_RANK            rank-eligible (``is_sourced``)
pressure drop    ``composition``+             ``composition``+
                 ``orientation`` DE_RANK      ``orientation`` DE_RANK
===============  ===========================  ==============================

The pressure-drop correlation is declared for **horizontal two-component** flow and
this loop is neither, so :attr:`PressureDropResult.is_applicable` is ``False`` for every
point of both fluids -- its own docstring says so, and the probe confirms it. Anything
computed *through* the pressure drop, pump work included, inherits that de-rank. **S6-1
therefore forces the outcome**: no pressure-drop-dependent two-phase point may be
categorised ``FEASIBLE_RANKED``, so none enters a non-dominated set. They appear in the
exported tables, de-ranked, with the reason on the row. That is a finding about the
state of Stage-2 evidence, not a defect in this engine, and it is not engineered around.

**What two-phase points must never acquire (D144, hard line).**
``radiator_temperature_K`` and ``radiator_area_m2`` are the Biswas/Suncatcher
harmonization's axes -- published single-side area versus the harmonized double-sided
convention. A two-phase point carrying either would intersect a harmonization that is a
separate gate (R3). :data:`FORBIDDEN_METRICS` names them and
:func:`_assert_no_forbidden_metric` enforces it at construction, so the falsifier is
mechanical rather than a matter of review attention.

**S6-5 containment.** Nothing here touches the Stage-1 export. ``_CSV_FIELDS`` is not
extended, :data:`orbital_thermal.trade_study.TRADES` still holds exactly six trades, and
``build_trade_study()`` with default arguments still yields the same 144 points and the
same export-rows sha. The two-phase fronts live in :data:`TWO_PHASE_TRADES` and
:data:`MIXED_TRADES` here, and two-phase output leaves by :func:`to_two_phase_csv_rows`.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field

from . import fluids as _fluids
from . import pumped_loop as _pl
from . import two_phase as _tp
from . import two_phase_loop as _tpl
from .fluids import SourceGatedFluidError
from .registry.applicability import Cause, Consequence
from .registry.collapse import Collapse, CollapsedModel, ModelTerm
from .registry.provenance import NotRankEligibleError
from .trade_study import ParetoFront, PointCategory, ReasonCode, TradeDef, pareto_front

# ``_CONSEQUENCE_TO_STATUS`` is the single place the applicability vocabulary meets the
# Stage-2 status vocabulary. Imported rather than restated: D144 -- "the vocabulary is a
# lookup, not an invention". A second copy here would be a second thing to keep true.
from .two_phase import _CONSEQUENCE_TO_STATUS, RankStatus  # noqa: PLC2701 - see above

# --- the ranking-scope limitation, F6 -------------------------------------------

#: Scoping note section 7, verbatim. Carried on every ranked export that contains at
#: least one two-phase case (S6-3, as amended at D140). NOT added to the Stage-1
#: single-phase CSV, where it would both overclaim and move the sha S6-5 pins.
F6_RANKING_SCOPE_LIMITATION = (
    "Two-phase ranked cases are rank-eligible only within the adopted 1-g "
    "reference-correlation model. Rankings are not microgravity-validated and may "
    "change under microgravity-specific correlations or dynamic-stability constraints."
)


# --- the collapse this milestone extends the scope of, declared where it happens ---

#: **C11.** ``two_phase_loop`` declares the homogeneous mixture density at ``x_mean`` as
#: a collapse of the **static** term -- a head. S6 carries the same representative value
#: into the **pump-work** denominator, which is a different term doing different work, so
#: it gets its own entry here rather than inheriting the static one silently. D144:
#: inheriting it silently is a falsifier of S6-4.
PUMP_WORK_MODEL = CollapsedModel(
    model="S6 two-phase pump work (two_phase_pump_power)",
    terms=(
        ModelTerm(
            term="hydraulic_power",
            collapses=(
                Collapse(
                    quantity="mixture density in the pump-work denominator",
                    representative_value=(
                        "the homogeneous density at the section mean quality, "
                        "rho_mix = 1/(x_mean/rho_g + (1 - x_mean)/rho_f)"
                    ),
                    phenomena=("axial_profile",),
                    basis=(
                        "pump_energy computes P_hyd = m_dot * dP / rho and needs one "
                        "density for a channel whose density varies by orders of "
                        "magnitude from inlet to exit. It is given the same "
                        "homogeneous rho_mix at x_mean that two_phase_loop already "
                        "declares for the STATIC term, so the representative value is "
                        "reused rather than invented and its provenance is the one "
                        "already recorded in PRESSURE_DROP_MODEL. What is new is its "
                        "SCOPE: there the collapse stood behind a rho*g*h head, here "
                        "it stands behind a work term that is reported as a ranked "
                        "objective. C11 requires the collapse to be declared where it "
                        "happens, and a work term is not the term the static "
                        "declaration covered. With no axial profile the pump work is a "
                        "single-density screening estimate and cannot represent the "
                        "density excursion along a boiling channel."
                    ),
                ),
            ),
        ),
    ),
)


# --- declared two-phase case, held fixed --------------------------------------------

#: Metrics a two-phase point may never carry (D144 hard line). See the module docstring.
FORBIDDEN_METRICS = frozenset({"radiator_temperature_K", "radiator_area_m2"})

#: Fixed declared channel geometry, in the Stage-1 spirit: geometry is held, not swept.
CHANNEL_DIAMETER_M = 1.0e-2
CHANNEL_LENGTH_M = 1.0
CHANNEL_SHAPE = "round_tube"
CHANNEL_ORIENTATION = "vertical_upflow"
#: Single-component: a fluid boiling in its own vapour, which is what the loop is and
#: what the Lockhart-Martinelli composition axis is declared against.
COMPOSITION = "single_component"
#: Registered two-phase coolants. R134a is source-gated and is included so the seam's
#: source-required branch is exercised by the grid rather than only by a test.
FLUIDS: tuple[str, ...] = ("Ammonia", "Water", "R134a")
OPERATING_PRESSURE_PA = 1.0e6

_A_CROSS_M2 = math.pi * CHANNEL_DIAMETER_M**2 / 4.0
_A_WETTED_M2 = math.pi * CHANNEL_DIAMETER_M * CHANNEL_LENGTH_M


def declared_channel() -> _tp.ChannelGeometry:
    """The declared channel, stated once, here.

    **It is passed INTO the evaluator, never constructed inside it.** ``geometry`` is a
    declared case fact (``two_phase_architecture_cases.CASE_FACTS``), and the S5
    apparatus classifies a ``geometry=`` argument whose value production works out --
    rather than receives -- as a quantity the computation derives. That is the D118
    refusal, and it is right: a rule whose input is manufactured at the point the rule is
    applied is a rule whose input nobody stated. Reading a field off a caller-owned
    object stays a case fact; constructing the object does not.
    """
    return _tp.ChannelGeometry(
        shape=CHANNEL_SHAPE, hydraulic_diameter_m=CHANNEL_DIAMETER_M,
        orientation=CHANNEL_ORIENTATION, heated_length_m=CHANNEL_LENGTH_M, sourced=True)


#: The declared channel as a default, so the evaluator receives it as a bare parameter.
DECLARED_CHANNEL = declared_channel()


@dataclass(frozen=True)
class TwoPhaseGrid:
    """The declared two-phase sweep. Modest, and stated rather than tuned.

    ``heat_load_W`` deliberately matches the Stage-1 grid so the one mixed front shares
    an x-axis that means the same thing on both sides.
    """

    heat_load_W: tuple[float, ...] = (800.0, 1200.0, 1600.0)
    mass_flux_kg_m2s: tuple[float, ...] = (300.0, 500.0)
    exit_quality: tuple[float, ...] = (0.3, 0.6)
    inlet_subcooling_K: tuple[float, ...] = (5.0, 15.0)

    def points(self):
        for q in self.heat_load_W:
            for g in self.mass_flux_kg_m2s:
                for x in self.exit_quality:
                    for sub in self.inlet_subcooling_K:
                        yield q, g, x, sub

    def size(self) -> int:
        return (len(self.heat_load_W) * len(self.mass_flux_kg_m2s)
                * len(self.exit_quality) * len(self.inlet_subcooling_K))

    def metadata(self) -> dict[str, object]:
        return {
            "heat_load_W": list(self.heat_load_W),
            "mass_flux_kg_m2s": list(self.mass_flux_kg_m2s),
            "exit_quality": list(self.exit_quality),
            "inlet_subcooling_K": list(self.inlet_subcooling_K),
            "grid_points_per_fluid": self.size(),
            "channel_diameter_m": CHANNEL_DIAMETER_M,
            "channel_length_m": CHANNEL_LENGTH_M,
            "operating_pressure_Pa": OPERATING_PRESSURE_PA,
            "composition": COMPOSITION,
            "orientation": CHANNEL_ORIENTATION,
        }


# --- the two-phase point ------------------------------------------------------------


def _assert_no_forbidden_metric(metrics: dict[str, float]) -> None:
    bad = FORBIDDEN_METRICS & set(metrics)
    if bad:
        raise ValueError(
            f"a two-phase point may not carry {sorted(bad)}: those are the "
            "Biswas/Suncatcher harmonization's axes (published single-side area vs the "
            "harmonized double-sided convention), and acquiring them would put S6 "
            "inside a separate gate's scope (D144 hard line, R3)"
        )


@dataclass
class TwoPhasePoint:
    """One two-phase design point.

    Presents the attribute surface :func:`orbital_thermal.trade_study.pareto_front`
    consumes -- ``feasible``, ``metrics``, ``case_id``, ``point_id``, ``pareto_fronts``,
    ``dominated_reasons`` -- so the Stage-1 dominance construction is reused unchanged
    rather than reimplemented. ``_metric`` is ``point.metrics[key]``, so a point that
    lacks an objective raises ``KeyError`` in any front that ranks on it instead of
    ranking as a silent zero. That is the candidate filter's witness.
    """

    fluid: str
    grid_heat_load_W: float
    grid_mass_flux_kg_m2s: float
    grid_exit_quality: float
    grid_inlet_subcooling_K: float
    feasible: bool
    category: PointCategory
    reason_codes: tuple[ReasonCode, ...]
    metrics: dict[str, float]
    #: Per-leg verdict from the production applicability result. The point-level
    #: ``category`` is the worst of these; a *trade* admits on the leg its axes depend on.
    leg_status: dict[str, RankStatus] = field(default_factory=dict)
    #: Axes an applicability result could not evaluate, derived from
    #: ``Cause.NOT_EVALUATED`` -- never from ``BLOCK``, which carries both meanings
    #: (D119/D120). S6-2: "could not be checked" stays distinguishable from "passed".
    unevaluable_axes: tuple[str, ...] = ()
    #: The exclusion text as the registry states it, carried onto the row (S6-6).
    exclusion_notes: tuple[str, ...] = ()
    architecture: str = "two_phase"
    pareto_fronts: set[str] = field(default_factory=set)
    dominated_reasons: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _assert_no_forbidden_metric(self.metrics)

    @property
    def case_id(self) -> str:
        return f"{self.fluid}-two_phase"

    @property
    def point_id(self) -> str:
        return (f"{self.case_id}|Q={self.grid_heat_load_W:g}"
                f"|G={self.grid_mass_flux_kg_m2s:g}|x={self.grid_exit_quality:g}"
                f"|dTsub={self.grid_inlet_subcooling_K:g}")


# --- the eligibility seam -----------------------------------------------------------
#
# This is the milestone's central new claim: the mapping from a PRODUCTION applicability
# result onto PointCategory and ReasonCode. Everything above it is inherited physics;
# everything below it is ranking.


def _status_of(violations) -> RankStatus:
    """Worst status implied by ``violations``; ``RANK_ELIGIBLE`` when there are none."""
    status = RankStatus.RANK_ELIGIBLE
    for v in violations:
        mapped = _CONSEQUENCE_TO_STATUS[v.consequence]
        if _tp._STATUS_SEVERITY[mapped] > _tp._STATUS_SEVERITY[status]:
            status = mapped
    return status


_STATUS_TO_CATEGORY = {
    RankStatus.RANK_ELIGIBLE: PointCategory.FEASIBLE_RANKED,
    RankStatus.SENSITIVITY_ONLY: PointCategory.SENSITIVITY_ONLY,
    RankStatus.REJECTED: PointCategory.INFEASIBLE_RANKED,
    RankStatus.BLOCKED: PointCategory.SOURCE_REQUIRED,
}


def _reasons_for(violations) -> tuple[ReasonCode, ...]:
    """Reason codes for one leg's violations, deduped and order-preserving.

    S6-2: an axis that could not be evaluated gets its own code, distinct from one that
    was evaluated and failed. The distinction comes from ``Cause`` because only the site
    raising a violation knows which it is (D119/D120).
    """
    out: list[ReasonCode] = []
    for v in violations:
        if v.cause is Cause.NOT_EVALUATED:
            out.append(ReasonCode.AXIS_NOT_EVALUATED)
        elif v.consequence is Consequence.DE_RANK:
            out.append(ReasonCode.APPLICABILITY_DE_RANK)
        else:
            out.append(ReasonCode.OTHER_FEASIBILITY_FAILURE)
    return tuple(dict.fromkeys(out))


def _unevaluable(violations) -> tuple[str, ...]:
    return tuple(sorted({v.axis.value for v in violations if v.cause is Cause.NOT_EVALUATED}))


def two_phase_pump_power_W(
    *, mass_flow_kg_s: float, pressure_drop_Pa: float, rho_mix_kg_m3: float
) -> float:
    """Pump electrical power through the **section 4.7 convention**, same as Stage-1.

    Both architectures reach ``pump_power_W`` by this route (D144), which is what makes
    the one mixed front comparable rather than a ranking across a definitional
    difference. The density is the declared collapse recorded in :data:`PUMP_WORK_MODEL`.
    """
    return _pl.pump_energy(
        mass_flow_kg_s, pressure_drop_Pa, rho_mix_kg_m3, boundary="fluid_loop"
    ).electrical_power_W


def evaluate_two_phase_point(
    fluid: str, q_W: float, mass_flux: float, x_out: float, subcool_K: float,
    *, channel: _tp.ChannelGeometry = DECLARED_CHANNEL,
    pressure_Pa: float = OPERATING_PRESSURE_PA,
) -> TwoPhasePoint:
    """Evaluate one two-phase point through the production boundaries."""
    coords = (q_W, mass_flux, x_out, subcool_K)

    def blocked(category: PointCategory, reasons: tuple[ReasonCode, ...],
                notes: tuple[str, ...] = (), unevaluable: tuple[str, ...] = ()
                ) -> TwoPhasePoint:
        return TwoPhasePoint(fluid, *coords, False, category, reasons, {},
                             leg_status={}, unevaluable_axes=unevaluable,
                             exclusion_notes=notes)

    try:
        state = _fluids.saturation_state(pressure_Pa, fluid)
    except SourceGatedFluidError as e:
        # No registry entry declares a validity domain for this fluid. Not a failure of
        # the case: a statement that the evidence to judge it does not exist.
        return blocked(PointCategory.SOURCE_REQUIRED, (ReasonCode.SOURCE_GATED_FLUID,),
                       (str(e),))

    mass_flow = mass_flux * _A_CROSS_M2
    # Subcooled inlet expressed as a negative equilibrium quality, which is the form the
    # CHF correlation's inlet-quality domain is declared in.
    x_in = -(state.cp_f_J_kgK * subcool_K) / state.h_fg_J_kg

    leg_status: dict[str, RankStatus] = {}
    reasons: list[ReasonCode] = []
    notes: list[str] = []
    unevaluable: set[str] = set()
    metrics: dict[str, float] = {
        "heat_load_W": q_W,
        "mass_flux_kg_m2s": mass_flux,
        "exit_quality": x_out,
    }

    # --- leg: CHF ---------------------------------------------------------------
    try:
        chf = _tp.critical_heat_flux(
            state=state, geometry=channel, mass_flux_kg_m2s=mass_flux,
            inlet_quality=x_in, critical_quality=x_out,
            gravity_m_s2=_tp.STANDARD_GRAVITY_M_S2)
    except NotRankEligibleError as e:
        # BLOCK/REJECT: the case cannot produce a value at all.
        return blocked(PointCategory.SOURCE_REQUIRED,
                       (ReasonCode.AXIS_NOT_EVALUATED,), (str(e),))
    leg_status["chf"] = _status_of(chf.violations)
    reasons.extend(_reasons_for(chf.violations))
    unevaluable.update(_unevaluable(chf.violations))
    notes.extend(v.detail for v in chf.violations)
    wall_flux = q_W / _A_WETTED_M2
    metrics["chf_W_m2"] = chf.value_W_m2
    metrics["chf_ratio"] = wall_flux / chf.value_W_m2

    # --- leg: pressure drop (and, through it, pump work) ------------------------
    dp = _tpl.two_phase_pressure_drop(
        mass_flow_kg_s=mass_flow, diameter_m=CHANNEL_DIAMETER_M,
        length_m=CHANNEL_LENGTH_M, quality_in=0.0, quality_out=x_out,
        rho_f=state.rho_f_kg_m3, rho_g=state.rho_g_kg_m3,
        mu_f=state.mu_f_Pa_s, mu_g=state.mu_g_Pa_s, pressure_Pa=pressure_Pa,
        composition=COMPOSITION, geometry_shape=CHANNEL_SHAPE,
        orientation=CHANNEL_ORIENTATION, fluid=fluid, height_m=CHANNEL_LENGTH_M)
    leg_status["pressure_drop"] = _status_of(dp.violations)
    reasons.extend(_reasons_for(dp.violations))
    unevaluable.update(_unevaluable(dp.violations))
    notes.extend(v.detail for v in dp.violations)
    metrics["pressure_drop_Pa"] = dp.total_Pa

    x_mean = 0.5 * (0.0 + x_out)
    rho_mix = 1.0 / (x_mean / state.rho_g_kg_m3 + (1.0 - x_mean) / state.rho_f_kg_m3)
    metrics["rho_mix_kg_m3"] = rho_mix
    pump_W = two_phase_pump_power_W(
        mass_flow_kg_s=mass_flow, pressure_drop_Pa=dp.total_Pa, rho_mix_kg_m3=rho_mix)
    metrics["pump_power_W"] = pump_W
    metrics["parasitic_power_W"] = pump_W

    # --- leg: pump inlet --------------------------------------------------------
    inlet = _tpl.pump_inlet_feasibility(
        saturation_temperature_K=state.T_sat_K,
        inlet_temperature_K=state.T_sat_K - subcool_K, inlet_is_liquid=True)
    metrics["subcooling_margin_K"] = inlet.subcooling_margin_K
    if not inlet.feasible:
        leg_status["pump_inlet"] = RankStatus.REJECTED
        reasons.append(ReasonCode.OTHER_FEASIBILITY_FAILURE)
        notes.append(inlet.reason)
    else:
        leg_status["pump_inlet"] = RankStatus.RANK_ELIGIBLE

    worst = RankStatus.RANK_ELIGIBLE
    for s in leg_status.values():
        if _tp._STATUS_SEVERITY[s] > _tp._STATUS_SEVERITY[worst]:
            worst = s
    category = _STATUS_TO_CATEGORY[worst]
    if not reasons:
        reasons.append(ReasonCode.FEASIBLE)

    return TwoPhasePoint(
        fluid, *coords,
        category is PointCategory.FEASIBLE_RANKED, category,
        tuple(dict.fromkeys(reasons)), metrics,
        leg_status=leg_status, unevaluable_axes=tuple(sorted(unevaluable)),
        exclusion_notes=tuple(dict.fromkeys(notes)))


def evaluate_two_phase_grid(
    grid: TwoPhaseGrid | None = None, fluids: tuple[str, ...] = FLUIDS
) -> list[TwoPhasePoint]:
    grid = grid or TwoPhaseGrid()
    return [evaluate_two_phase_point(f, q, g, x, sub)
            for f in fluids for (q, g, x, sub) in grid.points()]


# --- candidate filters --------------------------------------------------------------


def _admits(leg: str):
    """A per-trade candidate filter: rank-eligible **on the leg this trade ranks on**.

    A Stage-1 point carries no ``leg_status``; for it the Stage-1 rule is used unchanged,
    so the honesty rule "only rank-eligible feasible points enter a front" is preserved
    on both sides rather than widened (D144 Q2=2b).
    """
    def admit(p) -> bool:
        status = getattr(p, "leg_status", None)
        if not status:
            return bool(p.feasible)
        return status.get(leg) is RankStatus.RANK_ELIGIBLE
    return admit


# --- trades ---------------------------------------------------------------------------
#
# These are NOT appended to trade_study.TRADES: doing so would move
# summary()['fronts'] from 6 and break S6-5.

#: **Exactly one mixed front** (D144 Q1=1c). Both architectures reach ``pump_power_W``
#: through the same section 4.7 convention, which is what makes the axis mean the same
#: thing on both sides. No other Stage-1 trade is servable by
#: {heat_load_W, pump_power_W, parasitic_power_W} alone.
MIXED_TRADES: tuple[TradeDef, ...] = (
    TradeDef(
        "heat_load_vs_pump_power", "heat_load_W", True, "pump_power_W", False,
        "both architectures compute pump power through the section 4.7 "
        "hydraulic-into-fluid convention (pump_energy, boundary='fluid_loop'); the "
        "two-phase side supplies dP from two_phase_pressure_drop and the homogeneous "
        "rho_mix at x_mean, whose collapse is declared in PUMP_WORK_MODEL. Admission is "
        "on the pressure-drop leg, because pump work is computed through it.",
        _admits("pressure_drop"),
    ),
)

#: Two-phase-native fronts. These rank two-phase points against each other only, on axes
#: no single-phase point defines, so nothing is ranked across a definitional difference.
TWO_PHASE_TRADES: tuple[TradeDef, ...] = (
    TradeDef("chf_margin_vs_load", "heat_load_W", True, "chf_ratio", False,
             "CHF margin as the local wall flux over the Shah (1987) critical flux; S0 "
             "decision 5 ranks only at q''/CHF <= 0.5. Admission is on the CHF leg.",
             _admits("chf")),
    TradeDef("pressure_drop_vs_mass_flux", "mass_flux_kg_m2s", True, "pressure_drop_Pa",
             False,
             "Lockhart-Martinelli/Chisholm frictional term plus acceleration and static; "
             "the static term carries its own declared density collapse. Admission is on "
             "the pressure-drop leg.",
             _admits("pressure_drop")),
    TradeDef("quality_vs_pump_power", "exit_quality", True, "pump_power_W", False,
             "higher exit quality buys heat capacity per unit mass flow and pays "
             "pressure drop, hence pump work. Admission is on the pressure-drop leg, "
             "because pump work is computed through it.",
             _admits("pressure_drop")),
    TradeDef("subcooling_margin_vs_pressure_drop", "subcooling_margin_K", True,
             "pressure_drop_Pa", False,
             "pump-inlet subcooling margin by the AMS-02 criterion (ruling D8) against "
             "loop pressure drop. Admission is on the pressure-drop leg.",
             _admits("pressure_drop")),
)


# --- result ---------------------------------------------------------------------------


@dataclass
class TwoPhaseStudyResult:
    points: list[TwoPhasePoint]
    single_phase_points: list[object]
    fronts: list[ParetoFront]
    grid_metadata: dict[str, object]

    def summary(self) -> dict[str, int]:
        cats = [p.category for p in self.points]
        return {
            "two_phase_points": len(self.points),
            "feasible_ranked": sum(1 for c in cats if c is PointCategory.FEASIBLE_RANKED),
            "sensitivity_only": sum(1 for c in cats if c is PointCategory.SENSITIVITY_ONLY),
            "source_required": sum(1 for c in cats if c is PointCategory.SOURCE_REQUIRED),
            "infeasible_ranked": sum(1 for c in cats
                                     if c is PointCategory.INFEASIBLE_RANKED),
            "fronts": len(self.fronts),
            "degenerate_fronts": sum(1 for f in self.fronts if f.degenerate),
        }

    def front(self, name: str) -> ParetoFront:
        for f in self.fronts:
            if f.name == name:
                return f
        raise KeyError(name)


def _detached(point):
    """A copy of a Stage-1 point whose front-membership state this module cannot reach.

    **This guard exists because its absence broke S6-5 in exactly the D140 shape.**
    :func:`~orbital_thermal.trade_study.pareto_front` records membership by MUTATING
    ``point.pareto_fronts`` and ``point.dominated_reasons``, and both are carried in
    ``_CSV_FIELDS``. Ranking the caller's own Stage-1 points in the mixed front therefore
    wrote a seventh front name into their export rows: ``total_points``,
    ``feasible_ranked``/``gate_rejected``/``nonconverged`` and the six front sizes were
    all still exactly right, and the export sha had moved. Three of the four S6-5 fields
    matched the form while the rows had changed -- which is why D140 insists the hash is
    the field doing the work.

    ``test_s6_5_building_the_two_phase_study_does_not_move_the_stage1_export`` computes
    the sha AFTER building, because computing it before is blind to this.
    """
    clone = copy.copy(point)
    clone.pareto_fronts = set()
    clone.dominated_reasons = {}
    return clone


def build_two_phase_study(
    grid: TwoPhaseGrid | None = None, single_phase_points: list | None = None
) -> TwoPhaseStudyResult:
    """Two-phase-native fronts, plus the one mixed front when Stage-1 points are given.

    ``single_phase_points`` is optional and defaulted to none so that the two-phase
    engine can be exercised without running the Stage-1 grid. When supplied it must be
    the Stage-1 ``EvaluatedPoint`` list; those points are ranked in the mixed front by
    the Stage-1 rule, unchanged.
    """
    grid = grid or TwoPhaseGrid()
    tp_points = evaluate_two_phase_grid(grid)
    sp_points = [_detached(p) for p in (single_phase_points or [])]

    fronts = [pareto_front(tp_points, t) for t in TWO_PHASE_TRADES]
    if sp_points:
        fronts += [pareto_front(sp_points + tp_points, t) for t in MIXED_TRADES]

    meta = dict(grid.metadata())
    meta["fluids"] = list(FLUIDS)
    meta["ranking_scope_limitation"] = F6_RANKING_SCOPE_LIMITATION
    meta["forbidden_metrics"] = sorted(FORBIDDEN_METRICS)
    meta["n_single_phase_points"] = len(sp_points)
    return TwoPhaseStudyResult(tp_points, sp_points, fronts, meta)


# --- export ---------------------------------------------------------------------------

_TP_CSV_FIELDS = (
    "point_id", "case_id", "fluid", "architecture", "grid_heat_load_W",
    "grid_mass_flux_kg_m2s", "grid_exit_quality", "grid_inlet_subcooling_K",
    "feasible", "category", "reason_codes", "unevaluable_axes", "leg_status",
    "heat_load_W", "mass_flux_kg_m2s", "exit_quality", "chf_W_m2", "chf_ratio",
    "pressure_drop_Pa", "rho_mix_kg_m3", "pump_power_W", "parasitic_power_W",
    "subcooling_margin_K", "pareto_front_membership", "exclusion_notes",
)

_METRIC_FIELDS = (
    "heat_load_W", "mass_flux_kg_m2s", "exit_quality", "chf_W_m2", "chf_ratio",
    "pressure_drop_Pa", "rho_mix_kg_m3", "pump_power_W", "parasitic_power_W",
    "subcooling_margin_K",
)


def _csv_escape(text: str) -> str:
    return '"' + text.replace('"', '""') + '"'


def to_two_phase_csv_rows(result: TwoPhaseStudyResult) -> list[str]:
    """Machine-readable two-phase rows, F6-tagged.

    **S6-3.** The tag is carried once, on the export as a whole, as the first line --
    not per row. This export contains two-phase cases, so it is in scope. The Stage-1
    single-phase CSV contains none, is out of scope, and is frozen untouched: tagging it
    would move the sha S6-5 pins and is itself a falsifier.
    """
    rows = [f"# {F6_RANKING_SCOPE_LIMITATION}", ",".join(_TP_CSV_FIELDS)]
    for p in result.points:
        vals = [
            p.point_id, p.case_id, p.fluid, p.architecture,
            f"{p.grid_heat_load_W:g}", f"{p.grid_mass_flux_kg_m2s:g}",
            f"{p.grid_exit_quality:g}", f"{p.grid_inlet_subcooling_K:g}",
            str(p.feasible), p.category.value,
            "|".join(r.value for r in p.reason_codes),
            "|".join(p.unevaluable_axes),
            "|".join(f"{k}={v.value}" for k, v in sorted(p.leg_status.items())),
        ]
        vals += [f"{p.metrics[k]:g}" if k in p.metrics else "" for k in _METRIC_FIELDS]
        vals.append("|".join(sorted(p.pareto_fronts)))
        vals.append(_csv_escape(" || ".join(p.exclusion_notes)))
        rows.append(",".join(vals))
    return rows


def front_table_rows(result: TwoPhaseStudyResult, front_name: str) -> list[str]:
    """The exported table for one front, F6-tagged.

    **S6-6 binds here.** A de-ranked point appears in this table, in its de-ranked
    category, with the exclusion text on its row -- and never in the front's
    ``member_point_ids``. The rule "only rank-eligible feasible points enter a front" is
    not widened; what widens is what the *export* shows (D144 Q2=2b).
    """
    front = result.front(front_name)
    members = set(front.member_point_ids)
    x_key, y_key = front.x_axis, front.y_axis
    rows = [
        f"# {F6_RANKING_SCOPE_LIMITATION}",
        f"# front: {front.name} | x={x_key} ({front.x_sense}) "
        f"| y={y_key} ({front.y_sense}) | degenerate={front.degenerate}"
        + (f" | {front.note}" if front.note else ""),
        "point_id,architecture,category,in_non_dominated_set,"
        f"{x_key},{y_key},exclusion_notes",
    ]
    considered = [p for p in (result.points + result.single_phase_points)
                  if x_key in p.metrics and y_key in p.metrics]
    for p in considered:
        notes = " || ".join(getattr(p, "exclusion_notes", ()) or ())
        rows.append(",".join([
            p.point_id, getattr(p, "architecture", "single_phase"), p.category.value,
            str(p.point_id in members),
            f"{p.metrics[x_key]:g}", f"{p.metrics[y_key]:g}", _csv_escape(notes),
        ]))
    return rows
