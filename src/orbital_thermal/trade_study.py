"""B6: trade-study engine (Stage-1 Pareto fronts over the rank-eligible reference cases).

The engine sweeps a **declared modest grid** of design variables (heat load ``Q``, mass flow
``m_dot``, radiator area ``A_plan``, low-side pressure ``P_lo``) across the **rank-eligible B5
reference cases only**, evaluates every point through the verified B4 coupled model (via B5's
:func:`architecture_cases.evaluate_case`, so the **physics inherits B1-B5** and is not newly
validated here), and assembles the **minimum Pareto set** of six named trade fronts.

**What B6 newly verifies (level c):** the *engine* -- grid enumeration, feasible/infeasible
classification with reason codes, Pareto-dominance construction, degenerate/empty-front
handling, and reproducible, fully-labelled machine-readable output. It does **not** re-validate
the underlying physics.

**Constraints and honesty rules.** ``T_j <= T_j_max`` is a **filter** (infeasible points are
reported with a reason, never silently dropped); only rank-eligible feasible points enter a
front; every point carries a category, reason codes, and per-front dominance flags; mass is
**modeled component mass (incomplete Stage-1 accounting, 4.8a)** -- never total-system, launch,
or flight mass. Tube diameter, loop length, cold-plate/radiator geometry, contact resistance,
material geometry, and the junction-limit threshold are held fixed (declared Stage-1
assumptions), not swept, in this first pass. **Figures are deferred to B7**; B6 emits plot-ready
data only.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import Enum

from . import architecture_cases as _ac
from .architecture_cases import Classification, Stage1Envelope


class PointCategory(str, Enum):
    FEASIBLE_RANKED = "feasible_ranked"
    INFEASIBLE_RANKED = "infeasible_ranked"  # provenance-eligible but gate-rejected (physics)
    NONCONVERGED = "nonconverged"  # solver did not converge -- NOT evidence of infeasibility
    SENSITIVITY_ONLY = "sensitivity_only"
    SOURCE_REQUIRED = "source_required"
    UNSUPPORTED_DEFERRED = "unsupported_deferred"


class ReasonCode(str, Enum):
    FEASIBLE = "feasible"
    JUNCTION_LIMIT_FAILURE = "junction_limit_failure"
    PHASE_MARGIN_FAILURE = "phase_margin_failure"
    REYNOLDS_DOMAIN_FAILURE = "reynolds_domain_failure"
    RESIDUAL_NONCONVERGENCE = "residual_nonconvergence"
    OTHER_FEASIBILITY_FAILURE = "other_feasibility_failure"
    MASS_ACCOUNTING_INCOMPLETE = "mass_accounting_incomplete"  # standing note on every mass point


# map B5 architecture-case reasons -> B6 reason codes
_REASON_MAP = {
    _ac.Reason.JUNCTION_LIMIT_FAILURE: ReasonCode.JUNCTION_LIMIT_FAILURE,
    _ac.Reason.SINGLE_PHASE_MARGIN_FAILURE: ReasonCode.PHASE_MARGIN_FAILURE,
    _ac.Reason.CORRELATION_DOMAIN_FAILURE: ReasonCode.REYNOLDS_DOMAIN_FAILURE,
    _ac.Reason.NONCONVERGENCE: ReasonCode.RESIDUAL_NONCONVERGENCE,
    _ac.Reason.OTHER_FEASIBILITY_FAILURE: ReasonCode.OTHER_FEASIBILITY_FAILURE,
}


# --- declared design grid -------------------------------------------------------


@dataclass(frozen=True)
class DesignGrid:
    """The declared modest sweep. Exact values are recorded in the output metadata."""

    heat_load_W: tuple[float, ...] = (800.0, 1200.0, 1600.0)
    mass_flow_kg_s: tuple[float, ...] = (0.03, 0.05, 0.08)
    radiator_area_m2: tuple[float, ...] = (1.5, 2.5)
    low_side_pressure_Pa: tuple[float, ...] = (15.0e5, 25.0e5)

    def points(self):
        for q in self.heat_load_W:
            for md in self.mass_flow_kg_s:
                for a in self.radiator_area_m2:
                    for p in self.low_side_pressure_Pa:
                        yield q, md, a, p

    def size(self) -> int:
        return (len(self.heat_load_W) * len(self.mass_flow_kg_s)
                * len(self.radiator_area_m2) * len(self.low_side_pressure_Pa))

    def metadata(self) -> dict[str, object]:
        return {
            "heat_load_W": list(self.heat_load_W),
            "mass_flow_kg_s": list(self.mass_flow_kg_s),
            "radiator_area_m2": list(self.radiator_area_m2),
            "low_side_pressure_Pa": list(self.low_side_pressure_Pa),
            "grid_points_per_case": self.size(),
        }


# --- evaluated point ------------------------------------------------------------

# objective keys and whether "better" means larger (maximize) for the Pareto sense
_OBJECTIVES = (
    "heat_load_W", "modeled_mass_kg", "fluid_delta_T_K", "pump_power_W",
    "radiator_temperature_K", "radiator_area_m2", "junction_margin_K",
    "fluid_inventory_kg", "containment_mass_kg", "inventory_plus_containment_kg",
    "operating_pressure_Pa", "parasitic_power_W", "min_subcooling_Pa",
)


@dataclass
class EvaluatedPoint:
    case_id: str
    coolant: str
    material: str
    # grid coordinates
    grid_heat_load_W: float
    grid_mass_flow_kg_s: float
    grid_radiator_area_m2: float
    grid_low_side_pressure_Pa: float
    feasible: bool
    category: PointCategory
    reason_codes: tuple[ReasonCode, ...]
    metrics: dict[str, float]  # objective values (empty for infeasible)
    active_constraint: str = "none"
    pareto_fronts: set[str] = field(default_factory=set)  # fronts this point is non-dominated in
    dominated_reasons: dict[str, str] = field(default_factory=dict)  # front -> why dominated

    @property
    def point_id(self) -> str:
        """Stable per-point identity: case + grid coordinates (re-review F6)."""
        return (f"{self.case_id}|Q={self.grid_heat_load_W:g}|mdot={self.grid_mass_flow_kg_s:g}"
                f"|A={self.grid_radiator_area_m2:g}|Plo={self.grid_low_side_pressure_Pa:g}")


def _metric(point: EvaluatedPoint, key: str) -> float:
    return point.metrics[key]


def _active_constraint(coupled, envelope: Stage1Envelope) -> str:
    """The feasibility margin closest to binding (informational)."""
    j_margin = envelope.t_junction_max_K - coupled.T_j_K
    sub = coupled.min_subcooling_Pa - envelope.subcooling_margin_Pa
    candidates = [("junction limit", j_margin / max(1.0, envelope.t_junction_max_K)),
                  ("subcooling margin", sub / max(1.0, envelope.low_side_pressure_Pa))]
    name, _ = min(candidates, key=lambda c: c[1])
    return name


def _evaluate_point(base: Stage1Envelope, coolant: str, material: str,
                    q: float, md: float, area: float, p: float) -> EvaluatedPoint:
    env = dataclasses.replace(
        base, q_compute_W=q, mass_flow_kg_s=md, radiator_area_m2=area, low_side_pressure_Pa=p)
    cr = _ac.evaluate_case(env, coolant, material)  # physics inherits B1-B5
    case_id = f"{coolant}-{material}"
    if cr.classification is Classification.RANK_ELIGIBLE:
        c = cr.coupled
        comp = {m.name: m.mass_kg for m in cr.mass.components if m.mass_kg is not None}
        inv = comp.get("coolant inventory (tube)", 0.0)
        cont = comp.get("tube containment shell", 0.0)
        metrics = {
            "heat_load_W": q,
            "modeled_mass_kg": cr.mass.total_modeled_kg,
            "fluid_delta_T_K": c.T2_K - c.T1_K,
            "pump_power_W": c.pump.electrical_power_W,
            "parasitic_power_W": c.pump.electrical_power_W,
            "radiator_temperature_K": c.T_rad_K,
            "radiator_area_m2": c.A_emit_m2,
            "junction_margin_K": env.t_junction_max_K - c.T_j_K,
            "fluid_inventory_kg": inv,
            "containment_mass_kg": cont,
            "inventory_plus_containment_kg": inv + cont,
            "operating_pressure_Pa": p,
            "min_subcooling_Pa": c.min_subcooling_Pa,
        }
        return EvaluatedPoint(
            case_id, coolant, material, q, md, area, p, True, PointCategory.FEASIBLE_RANKED,
            (ReasonCode.FEASIBLE, ReasonCode.MASS_ACCOUNTING_INCOMPLETE), metrics,
            active_constraint=_active_constraint(c, env))
    # provenance-eligible but physics-rejected: preserve ALL reason codes (deduped, F1)
    reasons = tuple(dict.fromkeys(
        _REASON_MAP.get(r, ReasonCode.OTHER_FEASIBILITY_FAILURE) for r in cr.reason_codes
    )) or (ReasonCode.OTHER_FEASIBILITY_FAILURE,)
    # nonconvergence is a distinct category -- NOT evidence of physical infeasibility (F5)
    category = (PointCategory.NONCONVERGED if ReasonCode.RESIDUAL_NONCONVERGENCE in reasons
                else PointCategory.INFEASIBLE_RANKED)
    return EvaluatedPoint(
        case_id, coolant, material, q, md, area, p, False, category, reasons, {})


def evaluate_grid(
    envelope: Stage1Envelope, grid: DesignGrid, cases=None
) -> list[EvaluatedPoint]:
    """Evaluate every grid point across the rank-eligible reference cases (only). ``cases`` is a
    list of ``(coolant, material)`` pairs; defaults to the B5 rank-eligible set."""
    if cases is None:
        cases = [(r.coolant, r.material)
                 for r in _ac.ranked_cases(_ac.build_case_matrix(envelope))]
    return [_evaluate_point(envelope, c, m, q, md, a, p)
            for (c, m) in cases for (q, md, a, p) in grid.points()]


# --- Pareto fronts --------------------------------------------------------------


@dataclass(frozen=True)
class TradeDef:
    name: str
    x_key: str
    x_maximize: bool
    y_key: str
    y_maximize: bool
    dominating_assumption: str


TRADES: tuple[TradeDef, ...] = (
    TradeDef("modeled_mass_vs_load", "heat_load_W", True, "modeled_mass_kg", False,
             "modeled mass is radiator-panel-dominated (areal density is a design variable); "
             "total-system mass is NOT closed (4.8a)."),
    TradeDef("pump_power_vs_delta_T", "fluid_delta_T_K", False, "pump_power_W", False,
             "pump power uses the hydraulic-into-fluid deposition convention (4.7); low delta_T "
             "needs high m_dot and pays pump power."),
    TradeDef("radiator_area_vs_temp", "radiator_temperature_K", False, "radiator_area_m2", False,
             "area-temperature trade follows the T^4 rejection law; emissivity and sink are "
             "design variables."),
    TradeDef("junction_margin_vs_load", "heat_load_W", True, "junction_margin_K", True,
             "junction margin is set by the solid path (spreading dominates) and the junction-"
             "limit design variable."),
    TradeDef("inventory_containment_mass_vs_pressure", "operating_pressure_Pa", True,
             "inventory_plus_containment_kg", False,
             "containment is an ideal-shell lower bound (minimum gauge unmodeled, 4.6). "
             "Pressure is a **design-capability proxy** for phase margin (see "
             "min_subcooling_Pa), not an intrinsic benefit: higher pressure buys margin at a "
             "containment-mass penalty."),
    TradeDef("modeled_mass_vs_parasitic_power", "parasitic_power_W", False, "modeled_mass_kg",
             False, "mass-vs-parasitic-power trade; parasitic power is the pump electrical input "
             "(fluid-loop boundary, 4.7)."),
)


def _dominates(a: EvaluatedPoint, b: EvaluatedPoint, t: TradeDef) -> bool:
    ax, ay = _metric(a, t.x_key), _metric(a, t.y_key)
    bx, by = _metric(b, t.x_key), _metric(b, t.y_key)
    x_ge = ax >= bx if t.x_maximize else ax <= bx
    y_ge = ay >= by if t.y_maximize else ay <= by
    x_gt = ax > bx if t.x_maximize else ax < bx
    y_gt = ay > by if t.y_maximize else ay < by
    return x_ge and y_ge and (x_gt or y_gt)


@dataclass
class ParetoFront:
    name: str
    x_axis: str
    y_axis: str
    x_sense: str  # "maximize" | "minimize"
    y_sense: str
    dominating_assumption: str
    member_case_ids: list[str]
    member_point_ids: list[str]
    n_feasible: int
    degenerate: bool
    note: str = ""


def pareto_front(points: list[EvaluatedPoint], t: TradeDef) -> ParetoFront:
    """Non-dominated subset over the **feasible** points for trade ``t``. Records dominance
    flags on each point. Empty / single-member fronts are marked ``degenerate`` (never silently
    omitted)."""
    feasible = [p for p in points if p.feasible]
    members: list[EvaluatedPoint] = []
    for p in feasible:
        dominators = [q for q in feasible if q is not p and _dominates(q, p, t)]
        if not dominators:
            p.pareto_fronts.add(t.name)
            members.append(p)
        else:
            # record why dominated: the objective the first dominator strictly improves
            d = dominators[0]
            axis = t.y_key if (
                (_metric(d, t.y_key) > _metric(p, t.y_key)) == t.y_maximize
                and _metric(d, t.y_key) != _metric(p, t.y_key)) else t.x_key
            p.dominated_reasons[t.name] = f"dominated_on_{axis}"
    degenerate = len(members) < 2
    note = ""
    if not feasible:
        note = "empty: no feasible point for this trade"
    elif degenerate:
        note = "degenerate: fewer than two non-dominated points"
    return ParetoFront(
        t.name, t.x_key, t.y_key, "maximize" if t.x_maximize else "minimize",
        "maximize" if t.y_maximize else "minimize", t.dominating_assumption,
        [m.case_id for m in members], [m.point_id for m in members], len(feasible),
        degenerate, note)


# --- top-level result -----------------------------------------------------------


@dataclass
class TradeStudyResult:
    points: list[EvaluatedPoint]
    fronts: list[ParetoFront]
    grid_metadata: dict[str, object]

    def summary(self) -> dict[str, int]:
        feas = sum(1 for p in self.points if p.feasible)
        nonconv = sum(1 for p in self.points if p.category is PointCategory.NONCONVERGED)
        gate_rej = sum(1 for p in self.points
                       if p.category is PointCategory.INFEASIBLE_RANKED)
        return {
            "total_points": len(self.points),
            "feasible_ranked": feas,
            "gate_rejected": gate_rej,
            "nonconverged": nonconv,
            "fronts": len(self.fronts),
            "degenerate_fronts": sum(1 for f in self.fronts if f.degenerate),
        }


def build_trade_study(
    envelope: Stage1Envelope | None = None, grid: DesignGrid | None = None, cases=None
) -> TradeStudyResult:
    """Run the declared grid across the rank-eligible cases and build all six Pareto fronts."""
    envelope = envelope or Stage1Envelope()
    grid = grid or DesignGrid()
    points = evaluate_grid(envelope, grid, cases)
    fronts = [pareto_front(points, t) for t in TRADES]
    meta = dict(grid.metadata())
    meta["model_version"] = _model_version()
    meta["n_cases"] = len({p.case_id for p in points})
    meta["objectives"] = list(_OBJECTIVES)
    return TradeStudyResult(points, fronts, meta)


def _model_version() -> str:
    try:
        from importlib.metadata import version
        return version("orbital-thermal")
    except Exception:
        return "unknown"


# --- machine-readable export ----------------------------------------------------

_CSV_FIELDS = (
    "point_id", "case_id", "coolant", "material", "grid_heat_load_W", "grid_mass_flow_kg_s",
    "grid_radiator_area_m2", "grid_low_side_pressure_Pa", "feasible", "category",
    "reason_codes", "active_constraint",
    *_OBJECTIVES, "pareto_front_membership", "dominated_reasons",
)


def to_csv_rows(result: TradeStudyResult) -> list[str]:
    """Flat, machine-readable rows (header first). Every point, every objective, feasibility,
    category, reason codes, and per-front Pareto membership."""
    rows = [",".join(_CSV_FIELDS)]
    for p in result.points:
        vals = [
            p.point_id, p.case_id, p.coolant, p.material, f"{p.grid_heat_load_W:g}",
            f"{p.grid_mass_flow_kg_s:g}", f"{p.grid_radiator_area_m2:g}",
            f"{p.grid_low_side_pressure_Pa:g}", str(p.feasible), p.category.value,
            "|".join(r.value for r in p.reason_codes), p.active_constraint,
        ]
        vals += [f"{p.metrics.get(k, ''):g}" if k in p.metrics else "" for k in _OBJECTIVES]
        vals.append("|".join(sorted(p.pareto_fronts)))  # fronts this point is non-dominated in
        vals.append("|".join(f"{fr}={why}" for fr, why in sorted(p.dominated_reasons.items())))
        rows.append(",".join(vals))
    return rows
