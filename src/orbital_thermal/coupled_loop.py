"""S4: the four legs stop being independent calculations and become a loop.

S2 built the evaporator, S3 built pressure drop, the condenser energy boundary and
pump-inlet feasibility. This module solves them **together**: one operating point that
satisfies the loop's hydraulics, the condenser's energy books, the pump-inlet liquid
condition and an energy balance carrying pump heat in the rejected load -- with the
static Ledinegg guard on the solution it finds.

Two runs, and they are not interchangeable
------------------------------------------
The same machinery is exercised twice:

* :func:`demonstrate_machinery` on a case **inside** the declared basis of the
  correlations it uses, which is what makes the machinery executable-verified rather
  than asserted; and
* :func:`solve_reference_case` on this project's own device, where three of the four
  physical legs decline to produce a number.

**A demonstration mistaken for a result about the orbital loop is the worst outcome
available at this milestone**, so the two are separate types returning separate result
types, the demonstration's own rendered output carries its disclosure, and
:func:`demonstrate_machinery` refuses any case that is not actually in basis --
behaviourally, by running the leg and checking that it evaluates, not by trusting the
label it was handed. See ``ACCEPTANCE_CRITERIA_OTB-G003.md``, criteria S4-1 and S4-2.

What "coupled" does and does not mean here (C11, and read this before quoting a result)
---------------------------------------------------------------------------------------
The operating point is the intersection of the loop's internal characteristic with the
pump's. Duty, bore, length and the pump curve all reach it. **The sink temperature does
not:** it enters only the condenser's post-root bookkeeping, so the sink is collapsed to
a single representative value as far as the operating point is concerned and a 170 K
sink swing moves the solved mass flow by nothing at all.

That is a **declared collapse, not a solved coupling**. S0 asks for loop, condenser and
radiator "solved together" and this module does not do that; acceptance criterion S4-3
fails on its own terms and is reported failing rather than quietly satisfied. Closing it
means coupling through the radiator energy balance so that rejection sets the condensing
temperature, which sets saturation pressure, properties and hence the pressure drop --
a milestone of work, not a fix, and deliberately not attempted here.

What this module does not do
----------------------------
It emits **no ranked value** and no ordering (S4-13). It does not model dynamic
instability: the Ledinegg guard is **static**, per the adopted source, which defers
instability treatment to another volume (S4-6). It computes no condensation
coefficient, because there is no condensation entry of any kind in the registry
(Director ruling D10, DEBTS D-11). And it resolves nothing about the pump efficiency,
which is DEBTS D-13 and the Director's to rule -- it carries the disclosure instead.
"""

from __future__ import annotations

import math
import warnings
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from itertools import pairwise

from . import _validate as _v
from . import pumped_loop as _pl
from .dp_basis_assessment import (
    KIM_MUDAWAR_ID,
    assess_declared_basis,
    classify_pressure_drop_refusal,
    qualities_admitting_any_bore,
)
from .registry import NotRankEligibleError, get
from .registry.collapse import (
    Collapse,
    CollapseConflict,
    CollapsedModel,
    ModelTerm,
    Transcription,
    detection_conflicts,
    undetectable_disclosure,
)
from .registry.two_phase import ledinegg_static_criterion
from .two_phase_loop import (
    CHF_ID,
    DP_ID,
    HTC_ID,
    NPSH_ID,
    PRESSURE_DROP_MODEL,
    condenser_energy_boundary,
    pump_inlet_feasibility,
    two_phase_pressure_drop,
)

#: Registry id of the adopted static flow-excursion guard.
LEDINEGG_ID = "two_phase.stability.ledinegg_static"
#: The ammonia flow-boiling source registered at S4 against DEBTS D-6, not ranked.
SHAH_1974_ID = "two_phase.htc.shah_1974_ammonia"


class RunKind(str, Enum):
    """Which question a run is answering. Carried on the case and on the result.

    This is the type-level half of criterion S4-1. It is deliberately *not* sufficient
    on its own -- a label can be wrong -- so the entry points also check behaviour.
    """

    #: This project's device: single-component ammonia, non-horizontal, to 20 bar.
    REFERENCE_CASE = "reference_case"
    #: A case inside the declared basis of the correlations used, run to verify that
    #: the machinery works. **Says nothing about this project's device.**
    MACHINERY_DEMONSTRATION = "machinery_demonstration"


#: The disclosure a demonstration carries. A module constant rather than a field, so
#: no caller can blank it, shorten it, or pass a friendlier one (S4-2).
_DEMONSTRATION_DISCLOSURE = (
    "MACHINERY DEMONSTRATION -- NOT A RESULT ABOUT THIS PROJECT'S DEVICE. "
    "This case was chosen because it lies INSIDE the declared basis of the "
    "correlations used, which is the only reason the solver produces numbers for it. "
    "The orbital loop is single-component ammonia, non-horizontal, at 20 bar, and "
    "three of its four physical legs refuse to produce a number at all. Nothing here "
    "may be quoted, compared, or carried forward as a statement about that loop."
)

#: DEBTS D-13. Travels with every result carrying pump heat in the rejected load
#: (S4-11). The value is unchanged and the question is not answered here.
_PUMP_EFFICIENCY_DISCLOSURE = (
    "UNRESOLVED PROVENANCE (DEBTS D-13): the pump efficiency used in this energy "
    "balance is 0.70, which carries no visible provenance. Whether it is a design "
    "variable or stands in for a physical claim about a real pump is recorded as "
    "unresolved and is not decided here. The value is unchanged from its pre-S4 "
    "setting. Pump heat is load-bearing in the rejected load below, so this balance "
    "depends on an unresolved input."
)

# --- C11(i): what the COUPLED SOLVE collapses -------------------------------------
#
# Distinct from PRESSURE_DROP_MODEL, which is about one boundary's terms. This is about
# the solve as a whole: which declared inputs actually reach the operating point.
COUPLED_SOLVE_MODEL = CollapsedModel(
    model="S4 coupled steady-state solve (demonstrate_machinery / solve_reference_case)",
    terms=(
        ModelTerm(
            term="condenser/radiator",
            collapses=(
                Collapse(
                    quantity="sink temperature's influence on the operating point",
                    representative_value=(
                        "a post-root bookkeeping input, reaching only the condenser "
                        "energy boundary and never the characteristic"
                    ),
                    phenomena=("sink_temperature_coupling",),
                    basis=(
                        "The operating point is a root of (internal characteristic - "
                        "pump characteristic). Neither depends on sink_temperature_K, "
                        "so the solved mass flow is invariant under it: 150 K, 250 K "
                        "and 320 K all return the same root to twelve decimal places. "
                        "Rejection would have to set the condensing temperature, and "
                        "through it the saturation pressure and the properties, before "
                        "the sink could move the hydraulics."
                    ),
                    transcription=Transcription(
                        module="orbital_thermal.coupled_loop",
                        verbatim=(
                            "a single representative value as far as the operating "
                            "point is concerned"
                        ),
                        repo_path="src/orbital_thermal/coupled_loop.py",
                        context_line=(
                            "a single representative value as far as the operating "
                            "point is concerned and a 170 K"
                        ),
                    ),
                ),
            ),
        ),
        ModelTerm(term="loop hydraulics", collapses=()),
    ),
)

#: C11(ii). Acceptance criterion S4-3 ("the solver couples -- the legs are not
#: independent calculations reported together") is a guard, and its target phenomenon is
#: in the collapsed set above. It is named here so the boundary can say so.
S4_3_GUARD_ID = "ACCEPTANCE_CRITERIA_OTB-G003.md :: S4-3 (the solver couples)"
S4_3_DETECTS: tuple[str, ...] = ("sink_temperature_coupling",)


def sink_collapse_conflicts() -> tuple[CollapseConflict, ...]:
    """C11(ii) for criterion S4-3, taken at the shared boundary."""
    return detection_conflicts(
        guard_id=S4_3_GUARD_ID, detects=S4_3_DETECTS, model=COUPLED_SOLVE_MODEL
    )


def sink_disclosure_text() -> str:
    """Derived, like the Ledinegg one: it disappears when the collapse does."""
    return undetectable_disclosure(
        sink_collapse_conflicts(), guard_name="Criterion S4-3 (sink coupling)"
    )


def ledinegg_collapse_conflicts() -> tuple[CollapseConflict, ...]:
    """The C11(ii) cross-check for the Ledinegg guard, taken at the shared boundary.

    The guard's ``detects`` comes off its registry entry and the collapsed set comes
    off the active pressure-drop model; neither is restated here. This function only
    says *which* guard and *which* model -- everything that could disagree with the
    code lives in one of those two declarations.
    """
    return detection_conflicts(
        guard_id=LEDINEGG_ID,
        detects=get(LEDINEGG_ID).detects,
        model=PRESSURE_DROP_MODEL,
    )


def ledinegg_disclosure_text() -> str:
    """C11(ii), **derived**: empty when the model stops collapsing the target.

    Previously this was a hand-written constant that happened to be true. Deriving it
    is the whole of C11's second limb: the sentence and the condition it describes can
    no longer drift apart, and an integration along the channel that removed the
    collapse would remove the disclosure without anyone editing prose.
    """
    return undetectable_disclosure(
        ledinegg_collapse_conflicts(), guard_name="Ledinegg guard"
    )

#: The pump characteristic is a DESIGN VARIABLE, not a sourced pump curve (C1).
_PUMP_CURVE_DISCLOSURE = (
    "DESIGN VARIABLE: the external (pump) characteristic below is a declared "
    "quadratic droop, not a sourced pump curve. No pump has been selected and none is "
    "claimed. It sets where the loop's internal characteristic is intersected, so the "
    "operating point moves with it."
)


# --- the external characteristic --------------------------------------------------


@dataclass(frozen=True)
class PumpCharacteristic:
    """External characteristic ``Δp_available(ṁ)`` -- a declared design variable.

    A quadratic droop from shutoff to runout. Chosen for shape, not sourced: what the
    Ledinegg guard needs from it is a monotonically falling curve to intersect the
    loop's internal characteristic against, and any real pump supplies that.
    """

    shutoff_Pa: float
    runout_kg_s: float

    def __post_init__(self) -> None:
        _v.positive("shutoff_Pa", self.shutoff_Pa)
        _v.positive("runout_kg_s", self.runout_kg_s)

    def available_Pa(self, mass_flow_kg_s: float) -> float:
        """Pressure rise the pump supplies at a given flow. Zero beyond runout."""
        if mass_flow_kg_s >= self.runout_kg_s:
            return 0.0
        return self.shutoff_Pa * (1.0 - (mass_flow_kg_s / self.runout_kg_s) ** 2)

    @property
    def disclosure(self) -> str:
        return _PUMP_CURVE_DISCLOSURE


# --- the case ---------------------------------------------------------------------


@dataclass(frozen=True)
class LoopCase:
    """One physical loop, stated completely enough to be solved.

    ``quality_out`` is deliberately **absent**: outlet quality is not an input to a
    coupled solve, it is what the duty and the flow produce. Accepting it would let a
    caller hold it fixed while the flow moved, which is the shape of the defect the
    previous milestone's bore sweep was rejected for -- and here it would additionally
    flatten the internal characteristic and hide the Ledinegg mechanism entirely.
    """

    kind: RunKind
    fluid: str
    composition: str
    geometry_shape: str
    orientation: str
    diameter_m: float
    length_m: float
    duty_W: float
    pressure_Pa: float
    #: Latent heat, J/kg. With the duty, this is what sets outlet quality per flow.
    h_fg_J_kg: float
    rho_f: float
    rho_g: float
    mu_f: float
    mu_g: float
    quality_in: float = 0.0
    sink_temperature_K: float = 250.0
    saturation_temperature_K: float = 322.52
    inlet_temperature_K: float = 310.0
    height_m: float = 0.0
    rel_roughness: float = 0.0

    def __post_init__(self) -> None:
        """**The boundary** for F-05, and it is one place rather than every call site.

        A ``LoopCase`` had no validation at all: duty, latent heat, densities,
        viscosities, temperatures, geometry and quality could all be NaN, and the first
        thing that noticed was a result object carrying a NaN nobody could distinguish
        from a number. C9 says the check belongs where the case is constructed -- past
        here, every consumer can assume finite, physical inputs, and no consumer has to
        remember to.
        """
        for name in (
            "diameter_m", "length_m", "duty_W", "pressure_Pa", "h_fg_J_kg",
            "rho_f", "rho_g", "mu_f", "mu_g",
            "sink_temperature_K", "saturation_temperature_K", "inlet_temperature_K",
        ):
            _v.positive(name, getattr(self, name))
        _v.in_range("quality_in", self.quality_in, 0.0, 1.0)
        _v.finite("height_m", self.height_m)
        _v.nonneg("rel_roughness", self.rel_roughness)
        if self.rho_g >= self.rho_f:
            raise ValueError(
                f"vapour density {self.rho_g} is not below liquid density {self.rho_f}; "
                "the two-phase construction assumes rho_g < rho_f"
            )

    def quality_out_at(self, mass_flow_kg_s: float) -> float:
        """Outlet quality the duty produces at this flow. **The coupling term.**

        ``x_out = x_in + Q/(ṁ h_fg)``, capped at unity. Falling flow raises outlet
        quality, which raises the frictional multiplier -- the mechanism that puts a
        negative-slope segment into the internal characteristic and gives the Ledinegg
        guard something to find.
        """
        _v.positive("mass_flow_kg_s", mass_flow_kg_s)
        return min(1.0, self.quality_in + self.duty_W / (mass_flow_kg_s * self.h_fg_J_kg))


# --- the internal characteristic and its roots ------------------------------------


@dataclass(frozen=True)
class CharacteristicPoint:
    """One sample of the loop's internal pressure-drop/flow-rate characteristic.

    ``pressure_drop_Pa`` and :attr:`evaluated` are **not** the same question, and the
    gap between them is where a coupled solve can go quietly wrong. S3's pressure-drop
    boundary splits its refusals deliberately: ``BLOCK`` and ``REJECT`` raise, while
    ``DE_RANK`` *returns a number* with violations attached, so that a de-ranked case
    stays reportable as a sensitivity. Both of Lockhart-Martinelli's refusals for this
    project -- single-component composition and non-horizontal orientation -- are
    ``DE_RANK``, so the reference case comes back with a perfectly finite pressure drop
    and ``is_applicable == False``.

    A sensitivity report may use that number. **A coupled solve may not**: an operating
    point built on it would be a root of a characteristic the correlation disclaims,
    and nothing downstream could tell it from a real one. So the point is blocked on
    inapplicability, and the number it came with is kept only so the refusal can say
    what was declined.
    """

    mass_flow_kg_s: float
    quality_out: float
    pressure_drop_Pa: float | None
    blocked_reason: str = ""
    #: Present when the correlation returned a number it does not stand behind.
    inapplicable_value_Pa: float | None = None

    @property
    def evaluated(self) -> bool:
        """True only when an **applicable** pressure drop was produced."""
        return self.pressure_drop_Pa is not None


def internal_characteristic(
    case: LoopCase, mass_flows_kg_s: tuple[float, ...]
) -> tuple[CharacteristicPoint, ...]:
    """Sample ``Δp_int(ṁ)`` for the loop, one point per flow.

    A flow at which the pressure-drop correlation refuses yields a **blocked** point
    rather than an exception or a substituted number: the characteristic of a loop
    whose correlation does not apply is not zero, and it is not an estimate.
    """
    points: list[CharacteristicPoint] = []
    for mdot in mass_flows_kg_s:
        x_out = case.quality_out_at(mdot)
        try:
            result = two_phase_pressure_drop(
                mass_flow_kg_s=mdot,
                diameter_m=case.diameter_m,
                length_m=case.length_m,
                quality_in=case.quality_in,
                quality_out=x_out,
                rho_f=case.rho_f,
                rho_g=case.rho_g,
                mu_f=case.mu_f,
                mu_g=case.mu_g,
                pressure_Pa=case.pressure_Pa,
                composition=case.composition,
                geometry_shape=case.geometry_shape,
                orientation=case.orientation,
                fluid=case.fluid,
                height_m=case.height_m,
                rel_roughness=case.rel_roughness,
            )
        except (NotRankEligibleError, ValueError) as exc:
            points.append(
                CharacteristicPoint(mdot, x_out, None, blocked_reason=str(exc))
            )
        else:
            if not result.is_applicable:
                points.append(
                    CharacteristicPoint(
                        mdot,
                        x_out,
                        None,
                        blocked_reason=(
                            "the pressure-drop correlation returned a de-ranked value "
                            "it does not stand behind: "
                            + "; ".join(str(v) for v in result.violations)
                        ),
                        inapplicable_value_Pa=result.total_Pa,
                    )
                )
            else:
                points.append(CharacteristicPoint(mdot, x_out, result.total_Pa))
    return tuple(points)


@dataclass(frozen=True)
class OperatingPoint:
    """One steady solution: internal and external characteristics agree.

    ``slope_dP_dmdot_Pa_s_kg`` is the slope of the **internal** characteristic, which
    is the quantity the adopted Ledinegg criterion is about.
    """

    mass_flow_kg_s: float
    pressure_drop_Pa: float
    residual_Pa: float
    slope_dP_dmdot_Pa_s_kg: float
    #: ``None`` when the point came from a characteristic supplied directly rather
    #: than from a :class:`LoopCase`.
    quality_out: float | None = None

    @property
    def ledinegg_unstable(self) -> bool:
        """Whether the static flow-excursion criterion fires here."""
        return ledinegg_static_criterion(self.slope_dP_dmdot_Pa_s_kg)


#: Bracket width below which bisection stops, in kg/s. **A flow tolerance in its own
#: right**, not a scaled pressure one. The previous stop was `(hi - lo) <= tol * 1e-6`,
#: comparing a mass-flow interval in kg/s against a pressure in Pa -- dimensionally
#: incoherent, and numerically 1e-9 kg/s by accident rather than by choice. 1e-12 kg/s
#: is far below any flow this project resolves, so the residual test is what normally
#: terminates and this is the backstop.
_FLOW_BRACKET_TOL_KG_S = 1.0e-12

#: How finely each sampling interval is searched for roots the endpoints cannot reveal
#: -- a tangential touch, or two roots inside one interval. A STATED resolution limit,
#: not a completeness guarantee: no finite sampling can promise completeness on an
#: arbitrary callable, and claiming otherwise would be the defect this fix is for.
_SUBDIVISIONS = 16


def _bisect(
    f,
    lo: float,
    hi: float,
    tol_Pa: float,
    max_iter: int = 200,
    flow_tol_kg_s: float = _FLOW_BRACKET_TOL_KG_S,
) -> float:
    """Plain bisection on a sign-changing bracket. No secant acceleration.

    The characteristic can be steep and is only piecewise smooth, and bisection's
    guaranteed bracket-preserving convergence is worth more here than iteration count.

    Returns the best estimate; **the caller checks the residual.** This function cannot
    guarantee one -- a bracket can close on a discontinuity where no root exists -- so
    the guarantee belongs where it can be enforced, which is at the point of emission.
    """
    f_lo = f(lo)
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        f_mid = f(mid)
        if abs(f_mid) <= tol_Pa or (hi - lo) <= flow_tol_kg_s:
            return mid
        if (f_lo < 0.0) != (f_mid < 0.0):
            hi = mid
        else:
            lo, f_lo = mid, f_mid
    return 0.5 * (lo + hi)


#: A loop's internal characteristic: mass flow in, pressure drop out.
Characteristic = Callable[[float], float]


def _slope(characteristic: Characteristic, mdot: float, h_rel: float = 1e-4) -> float:
    """Central-difference slope of a characteristic at ``ṁ``."""
    h = max(mdot * h_rel, 1e-12)
    return (characteristic(mdot + h) - characteristic(mdot - h)) / (2.0 * h)


def operating_points_from_characteristic(
    characteristic: Characteristic,
    pump: PumpCharacteristic,
    *,
    flow_min_kg_s: float,
    flow_max_kg_s: float,
    samples: int = 240,
    residual_tol_Pa: float = 1.0e-3,
) -> tuple[OperatingPoint, ...]:
    """**Every** flow at which a supplied characteristic meets the pump's. None is preferred.

    Criterion S4-5. The Ledinegg picture in the adopted source is three intersections
    at one pressure drop, of which the middle is unstable and the operating point
    migrates away from it to one of the outer two. Which one it reaches is a question
    about the transient, and the transient is out of scope -- so returning "the"
    operating point here would be choosing an answer this milestone does not have.

    **The characteristic is a parameter, and that is deliberate.** The adopted source
    states a criterion about the shape of a pressure-drop/flow-rate curve; it says
    nothing about where the curve came from. Keeping the guard separable from this
    project's own pressure-drop model is what lets the guard be exercised against a
    curve that genuinely has a negative-slope segment -- which, as
    :func:`characteristic_is_monotone` records, the current model does not produce.
    """
    if not (0.0 < flow_min_kg_s < flow_max_kg_s):
        raise ValueError("need 0 < flow_min_kg_s < flow_max_kg_s")
    if samples < 3:
        raise ValueError("need at least 3 samples to bracket a root")

    grid = tuple(
        flow_min_kg_s + (flow_max_kg_s - flow_min_kg_s) * i / (samples - 1)
        for i in range(samples)
    )
    values = [characteristic(m) - pump.available_Pa(m) for m in grid]

    def residual(mdot: float) -> float:
        return characteristic(mdot) - pump.available_Pa(mdot)

    # One refined sampling of the whole range. `_SUBDIVISIONS` per coarse interval is a
    # STATED resolution limit, not a completeness guarantee: no finite sampling can
    # promise completeness on an arbitrary callable, and claiming otherwise would be
    # the defect this fix is for. What it buys is that a root no longer has to be
    # separated from its neighbours by a whole coarse interval to be found.
    fine: list[float] = []
    for (m_lo, _), (m_hi, _) in pairwise(list(zip(grid, values, strict=True))):
        fine.extend(
            m_lo + (m_hi - m_lo) * k / _SUBDIVISIONS for k in range(_SUBDIVISIONS)
        )
    fine.append(grid[-1])
    fine_v = [residual(m) for m in fine]

    candidates: list[float] = []

    # (1) SIGN CHANGES -- the reliable case, bisected.
    for (a, va), (b, vb) in pairwise(list(zip(fine, fine_v, strict=True))):
        if va == 0.0:
            candidates.append(a)
        elif (va < 0.0) != (vb < 0.0):
            candidates.append(_bisect(residual, a, b, residual_tol_Pa))

    # (2) TANGENTIAL roots -- the curve touches zero without crossing, so no sign
    # change exists to bracket. Accepted only at a LOCAL MINIMUM of |residual| that
    # actually reaches the tolerance. Accepting every sample merely *below* tolerance
    # would flood a shallow region with spurious roots and corrupt the multiplicity
    # verdict -- and multiplicity IS the Ledinegg verdict.
    for i in range(1, len(fine) - 1):
        here = abs(fine_v[i])
        if here <= residual_tol_Pa and here <= abs(fine_v[i - 1]) and here <= abs(fine_v[i + 1]):
            candidates.append(fine[i])

    # (3) ENDPOINTS. The old loop tested only the `lo` of each bracket, so a root
    # sitting exactly on `flow_max` was never examined: it is the `hi` of the last
    # bracket and never the `lo` of any.
    for m, v in ((fine[0], fine_v[0]), (fine[-1], fine_v[-1])):
        if abs(v) <= residual_tol_Pa:
            candidates.append(m)

    # Two roots closer together than one sub-interval are not resolvable by this
    # search; merging them and keeping the better residual is the honest outcome.
    cluster_tol = (flow_max_kg_s - flow_min_kg_s) / ((samples - 1) * _SUBDIVISIONS)
    merged: list[float] = []
    for root in sorted(candidates):
        if merged and (root - merged[-1]) <= cluster_tol:
            if abs(residual(root)) < abs(residual(merged[-1])):
                merged[-1] = root
            continue
        merged.append(root)

    roots: list[OperatingPoint] = []
    for root in merged:
        # (iii) A NON-ROOT IS NEVER EMITTED. Neither the bracket-width branch nor the
        # max_iter fall-through can promise a residual, so the promise is made here,
        # where it can be kept. Multiplicity IS the Ledinegg verdict and `_slope` is
        # computed on every emitted point -- a fabricated root would get a slope and a
        # stability verdict.
        r = residual(root)
        if not math.isfinite(r) or abs(r) > residual_tol_Pa:
            continue
        roots.append(
            OperatingPoint(
                mass_flow_kg_s=root,
                pressure_drop_Pa=characteristic(root),
                residual_Pa=r,
                slope_dP_dmdot_Pa_s_kg=_slope(characteristic, root),
            )
        )
    return tuple(roots)


def loop_characteristic(case: LoopCase) -> Characteristic:
    """The loop's own internal characteristic, as a callable.

    Raises :class:`NotRankEligibleError` at any flow where the pressure-drop
    correlation declines -- including where it declines by returning a de-ranked
    number, which is how it declines for this project's reference case.
    """

    def characteristic(mdot: float) -> float:
        (point,) = internal_characteristic(case, (mdot,))
        if not point.evaluated:
            raise NotRankEligibleError(point.blocked_reason)
        return point.pressure_drop_Pa

    return characteristic


def characteristic_is_monotone(
    characteristic: Characteristic,
    *,
    flow_min_kg_s: float,
    flow_max_kg_s: float,
    samples: int = 60,
) -> bool:
    """Whether a characteristic rises everywhere on the sampled range.

    A monotonically rising internal characteristic **cannot** satisfy the adopted
    Ledinegg criterion anywhere, so this answers, for a given model, whether a flow
    excursion is reachable at all. It exists because for this project's current
    pressure-drop model the answer is no, and that is a property worth pinning rather
    than rediscovering.
    """
    grid = [
        flow_min_kg_s + (flow_max_kg_s - flow_min_kg_s) * i / (samples - 1)
        for i in range(samples)
    ]
    values = [characteristic(m) for m in grid]
    return all(b > a for a, b in pairwise(values))


def find_operating_points(
    case: LoopCase,
    pump: PumpCharacteristic,
    *,
    flow_min_kg_s: float,
    flow_max_kg_s: float,
    samples: int = 240,
    residual_tol_Pa: float = 1.0e-3,
) -> tuple[OperatingPoint, ...]:
    """Every operating point of a :class:`LoopCase`, with its outlet quality attached."""
    grid = tuple(
        flow_min_kg_s + (flow_max_kg_s - flow_min_kg_s) * i / (samples - 1)
        for i in range(max(samples, 3))
    )
    blocked = [p for p in internal_characteristic(case, grid) if not p.evaluated]
    if blocked:
        raise NotRankEligibleError(
            "the loop's internal characteristic cannot be built: the pressure-drop "
            f"correlation refuses this case at {len(blocked)} of {len(grid)} sampled "
            "flows. First refusal: " + blocked[0].blocked_reason
        )
    points = operating_points_from_characteristic(
        loop_characteristic(case),
        pump,
        flow_min_kg_s=flow_min_kg_s,
        flow_max_kg_s=flow_max_kg_s,
        samples=samples,
        residual_tol_Pa=residual_tol_Pa,
    )
    return tuple(
        OperatingPoint(
            mass_flow_kg_s=p.mass_flow_kg_s,
            pressure_drop_Pa=p.pressure_drop_Pa,
            residual_Pa=p.residual_Pa,
            slope_dP_dmdot_Pa_s_kg=p.slope_dP_dmdot_Pa_s_kg,
            quality_out=case.quality_out_at(p.mass_flow_kg_s),
        )
        for p in points
    )


# --- energy closure ---------------------------------------------------------------


@dataclass(frozen=True)
class EnergyClosure:
    """Rejected load against applied duty plus the pump heat that enters the fluid."""

    duty_W: float
    pump_heat_into_fluid_W: float
    rejected_W: float
    residual_W: float
    boundary: str

    @property
    def closes(self) -> bool:
        return abs(self.residual_W) <= 1e-9 * max(abs(self.rejected_W), 1.0)

    @property
    def disclosures(self) -> tuple[str, ...]:
        """DEBTS D-13 travels with any balance carrying pump heat (S4-11)."""
        return (
            (_PUMP_EFFICIENCY_DISCLOSURE,) if self.pump_heat_into_fluid_W > 0.0 else ()
        )


def energy_closure(
    *,
    duty_W: float,
    mass_flow_kg_s: float,
    pressure_drop_Pa: float,
    density_kg_m3: float,
    boundary: str = "fluid_loop",
) -> EnergyClosure:
    """Close the loop's energy books **with pump heat in the rejected load** (S0).

    The hydraulic power the pump puts into the fluid is heat the radiator has to
    reject on top of the applied duty. It is obtained from Stage-1's own pump-energy
    accounting rather than recomputed, so the two stages cannot drift apart.
    """
    pump = _pl.pump_energy(
        mass_flow_kg_s=mass_flow_kg_s,
        pressure_drop_Pa=pressure_drop_Pa,
        density_kg_m3=density_kg_m3,
        boundary=boundary,
    )
    rejected = duty_W + pump.fluid_heat_W
    return EnergyClosure(
        duty_W=duty_W,
        pump_heat_into_fluid_W=pump.fluid_heat_W,
        rejected_W=rejected,
        residual_W=rejected - (duty_W + pump.fluid_heat_W),
        boundary=boundary,
    )


# --- legs, and why they refuse ----------------------------------------------------


@dataclass(frozen=True)
class LegStatus:
    """One physical leg of the loop, and whether it produced a number."""

    leg: str
    entry_id: str
    available: bool
    axis: str = ""
    reason: str = ""
    would_unblock: str = ""
    refusal_kind: str = ""

    def __str__(self) -> str:
        if self.available:
            return f"{self.leg}: AVAILABLE ({self.entry_id})"
        kind = f" [{self.refusal_kind} refusal]" if self.refusal_kind else ""
        return f"{self.leg}: BLOCKED on {self.axis}{kind} -- {self.reason}"


# --- results: two types, deliberately ---------------------------------------------


@dataclass(frozen=True)
class _CoupledResultBase:
    """What both runs carry. Never returned directly -- see the two subclasses."""

    case: LoopCase
    pump: PumpCharacteristic
    legs: tuple[LegStatus, ...]
    operating_points: tuple[OperatingPoint, ...] = ()
    closure: EnergyClosure | None = None
    pump_inlet_feasible: bool | None = None
    pump_inlet_reason: str = ""
    condenser_energy_closes: bool | None = None
    #: Whether the condenser duty computed from the SOLVED state matches the applied
    #: duty. ``None`` when no operating point was reached. This is the check that
    #: ``energy_closes`` could not be: that one compared the boundary against its own
    #: inputs and was true by construction.
    condenser_duty_matches_applied: bool | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def blocked_legs(self) -> tuple[LegStatus, ...]:
        return tuple(leg for leg in self.legs if not leg.available)

    @property
    def solved(self) -> bool:
        return bool(self.operating_points)

    @property
    def non_unique(self) -> bool:
        """More than one steady solution. Reported, never resolved (S4-5)."""
        return len(self.operating_points) > 1

    @property
    def unstable_points(self) -> tuple[OperatingPoint, ...]:
        return tuple(p for p in self.operating_points if p.ledinegg_unstable)

    def _body(self) -> list[str]:
        lines = [f"run kind: {self.case.kind.value}", f"fluid: {self.case.fluid}", ""]
        lines += [str(leg) for leg in self.legs]
        lines.append("")
        if self.operating_points:
            lines.append(f"operating points found: {len(self.operating_points)}")
            for i, p in enumerate(self.operating_points, 1):
                # A point taken from a supplied characteristic has no outlet quality;
                # printing "None" is better than inventing one or crashing the render.
                x_out = "n/a" if p.quality_out is None else f"{p.quality_out:.4g}"
                lines.append(
                    f"  [{i}] mdot = {p.mass_flow_kg_s:.6g} kg/s, "
                    f"dP = {p.pressure_drop_Pa:.6g} Pa, x_out = {x_out}, "
                    f"slope = {p.slope_dP_dmdot_Pa_s_kg:.6g} Pa.s/kg, "
                    f"{'LEDINEGG-UNSTABLE' if p.ledinegg_unstable else 'stable'}"
                )
            if self.non_unique:
                lines.append(
                    "  NON-UNIQUE: more than one steady solution satisfies this "
                    "system. Every root is reported and none is selected -- which one "
                    "the loop reaches is a question about the transient, and the "
                    "transient is out of scope."
                )
        else:
            lines.append("operating points found: none -- the loop was not solved")
        if self.closure is not None:
            lines += [
                "",
                f"energy closure on the {self.closure.boundary} boundary: "
                f"duty {self.closure.duty_W:.6g} W + pump heat "
                f"{self.closure.pump_heat_into_fluid_W:.6g} W = rejected "
                f"{self.closure.rejected_W:.6g} W "
                f"({'closes' if self.closure.closes else 'DOES NOT CLOSE'})",
            ]
            lines += [f"  {d}" for d in self.closure.disclosures]
        if self.condenser_duty_matches_applied is not None:
            lines += [
                f"condenser duty from the SOLVED state matches the applied duty: "
                f"{self.condenser_duty_matches_applied}"
            ]
        lines += [self.pump.disclosure, self.ledinegg_disclosure, self.sink_disclosure]
        lines += list(self.notes)
        return lines

    @property
    def ledinegg_disclosure(self) -> str:
        """Not a field, so no caller can construct a result without it (C6/C11)."""
        return ledinegg_disclosure_text()

    @property
    def sink_disclosure(self) -> str:
        """C11(ii) for criterion S4-3. Derived, and not suppressible."""
        return sink_disclosure_text()


@dataclass(frozen=True)
class DemonstrationResult(_CoupledResultBase):
    """The machinery, verified on a case inside the correlations' declared basis.

    **This type exists so that it cannot be mistaken for the other one.** A reader
    holding one of these -- with no filename, no comment and no surrounding prose --
    knows from its type and from its own rendered text that it says nothing about this
    project's device.
    """

    @property
    def disclosure(self) -> str:
        """Not a field. There is no way to construct one of these without it."""
        return _DEMONSTRATION_DISCLOSURE

    def render(self) -> str:
        return "\n".join(["=" * 78, self.disclosure, "=" * 78, "", *self._body()])

    __str__ = render


@dataclass(frozen=True)
class ReferenceCaseResult(_CoupledResultBase):
    """This project's own device: single-component ammonia, non-horizontal, 20 bar."""

    #: How the pressure-drop refusal should be characterised (S4-8).
    pressure_drop_refusal: str = ""

    def render(self) -> str:
        lines = ["REFERENCE CASE -- this project's device.", ""]
        lines += self._body()
        if self.pressure_drop_refusal:
            lines += ["", self.pressure_drop_refusal]
        return "\n".join(lines)

    __str__ = render


# --- the two entry points ---------------------------------------------------------


@contextmanager
def _collected_transitional_warnings() -> Iterator[list[int]]:
    """Collect Stage-1's transitional-flow warnings instead of broadcasting them.

    Sweeping a flow range crosses the Reynolds band where the friction factor blends
    the laminar and turbulent forms, so the warning fires once per sampled point --
    hundreds of times for one solve. That is a real caveat on the numbers and a
    useless way to deliver it: it drowns any *other* warning in the same run, and it
    reaches a log rather than the result. The count is yielded so the caller can put
    it where it belongs.
    """
    count = [0]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        yield count
    for w in caught:
        if "transitional flow" in str(w.message):
            count[0] += 1
        else:  # anything else is re-raised: this suppresses one thing, not everything
            warnings.warn_explicit(
                w.message, w.category, w.filename, w.lineno
            )


def _pressure_drop_leg(case: LoopCase, probe_flow_kg_s: float = 1.0e-2) -> LegStatus:
    """Run the pressure-drop leg once and report what it did.

    Behavioural, not structural: the leg is **evaluated**, and what it says is the
    verdict. Reading its applicability off the registry instead would report what the
    entry declares rather than what it does, and those came apart once already.
    """
    (probe,) = internal_characteristic(case, (probe_flow_kg_s,))
    if not probe.evaluated:
        return LegStatus(
            leg="pressure drop",
            entry_id=DP_ID,
            available=False,
            axis="composition/orientation",
            reason=probe.blocked_reason,
        )
    return LegStatus(leg="pressure drop", entry_id=DP_ID, available=True)


#: What "this project's device" means, as facts rather than as a label. Every one is a
#: settled decision: single-component ammonia, non-horizontal, at the 20 bar design
#: point (D14 decision 10, pushed and not ruled -- so it is pinned, not chosen here).
_DEVICE_FLUID = "ammonia"
_DEVICE_COMPOSITION = "single_component"
_DEVICE_NON_HORIZONTAL = frozenset({"vertical_upflow", "vertical_downflow", "inclined"})
_DEVICE_PRESSURE_MIN_PA = 1.0e6


def closure_for(points: tuple[OperatingPoint, ...], case: LoopCase) -> EnergyClosure | None:
    """The energy closure, or ``None`` where computing one would be a selection.

    **F-03.** Exactly one steady state gets a closure. Zero gets none because there is
    nothing to close on; **more than one gets none because choosing is what this
    milestone has said it cannot do.** The previous code took ``points[0]`` and
    disclosed that it had -- and a disclosure does not undo a selection, the same
    principle the Ledinegg guard was held to at MAINT-02-01.

    Reporting every root's closure was the other option and is worse: it invites the
    reader to compare branches the artifact has just said it cannot choose between.
    Reporting none states exactly what is known.

    Separated from :func:`demonstrate_machinery` so the decision is testable at a
    multiplicity the current pressure-drop model cannot produce -- its characteristic
    is monotone, which is itself a pinned property.
    """
    if len(points) != 1:
        return None
    chosen = points[0]
    return energy_closure(
        duty_W=case.duty_W,
        mass_flow_kg_s=chosen.mass_flow_kg_s,
        pressure_drop_Pa=chosen.pressure_drop_Pa,
        density_kg_m3=case.rho_f,
    )


def _assert_describes_the_device(case: LoopCase) -> None:
    """Refuse a case that carries the reference-case LABEL without the device's facts.

    F-02. The guard existed in one direction only: ``demonstrate_machinery`` refuses a
    case labelled ``REFERENCE_CASE``, but ``solve_reference_case`` checked the enum and
    nothing else -- so changing one field on the air-water, horizontal, 1.2 bar
    demonstration returned a ``ReferenceCaseResult``, an object that presents itself as
    a statement about this project's ammonia device. A one-way door is not a door.

    Checked on the case's own declared facts, not on a second label: the fluid, the
    composition, the orientation and the pressure.
    """
    wrong: list[str] = []
    if case.fluid.strip().lower() != _DEVICE_FLUID:
        wrong.append(f"fluid is {case.fluid!r}, not {_DEVICE_FLUID}")
    if case.composition.strip().lower() != _DEVICE_COMPOSITION:
        wrong.append(f"composition is {case.composition!r}, not {_DEVICE_COMPOSITION}")
    if case.orientation.strip().lower() not in _DEVICE_NON_HORIZONTAL:
        wrong.append(
            f"orientation is {case.orientation!r}; the device is non-horizontal "
            f"({sorted(_DEVICE_NON_HORIZONTAL)})"
        )
    if case.pressure_Pa < _DEVICE_PRESSURE_MIN_PA:
        wrong.append(
            f"pressure is {case.pressure_Pa:.4g} Pa, below the {_DEVICE_PRESSURE_MIN_PA:.4g} Pa "
            "floor the device's design point sits above"
        )
    if wrong:
        raise ValueError(
            "this case is labelled REFERENCE_CASE but does not describe this project's "
            "device, so a ReferenceCaseResult would present it as one: "
            + "; ".join(wrong)
            + ". The label is not the identity."
        )


def demonstrate_machinery(
    case: LoopCase,
    pump: PumpCharacteristic,
    *,
    flow_min_kg_s: float,
    flow_max_kg_s: float,
    samples: int = 240,
) -> DemonstrationResult:
    """Solve an **in-basis** case, to verify the machinery rather than the device.

    Two guards, and the second is the one that matters:

    1. the case must declare :attr:`RunKind.MACHINERY_DEMONSTRATION`; and
    2. **the pressure-drop leg must actually evaluate.** A case that refuses is not a
       machinery demonstration however it is labelled -- it is a reference-case run
       wearing the wrong label, and letting it through here is precisely the confusion
       criterion S4-1 exists to prevent. The check is behavioural: the leg is run.
    """
    if case.kind is not RunKind.MACHINERY_DEMONSTRATION:
        raise ValueError(
            "demonstrate_machinery requires a case declared as a machinery "
            f"demonstration; this one declares {case.kind.value}. The two runs are not "
            "interchangeable and the type system is not the only thing saying so."
        )
    with _collected_transitional_warnings() as transitional_count:
        leg = _pressure_drop_leg(case)
        if not leg.available:
            raise NotRankEligibleError(
                "this case is NOT inside the declared basis of the correlations it "
                "uses, so it cannot serve as a machinery demonstration -- a "
                "demonstration that refuses demonstrates nothing, and reporting it as "
                "one would put a reference-case refusal behind a demonstration label. "
                f"The leg said: {leg.reason}"
            )
        points = find_operating_points(
            case,
            pump,
            flow_min_kg_s=flow_min_kg_s,
            flow_max_kg_s=flow_max_kg_s,
            samples=samples,
        )
    transitional = transitional_count[0]
    closure = None

    # F-01(b): the leg reports the COMPUTED feasibility, and an infeasible inlet
    # REFUSES rather than returning points. A cavitating loop behind a green leg with a
    # solved operating point is the worst of both -- it is neither a refusal nor a
    # result. The verdict is returned rather than raised because cavitation is a
    # physical answer about the case, not a labelling error.
    inlet = pump_inlet_feasibility(
        saturation_temperature_K=case.saturation_temperature_K,
        inlet_temperature_K=case.inlet_temperature_K,
        inlet_is_liquid=True,
    )
    inlet_leg = LegStatus(
        leg="pump-inlet criterion",
        entry_id=NPSH_ID,
        available=inlet.feasible,
        axis="" if inlet.feasible else "subcooling margin",
        reason="" if inlet.feasible else inlet.reason,
        would_unblock=(
            ""
            if inlet.feasible
            else "an inlet subcooled below saturation, per the AMS-02 criterion (D8)."
        ),
        refusal_kind="" if inlet.feasible else "knowledge",
    )
    if not inlet.feasible:
        points = ()

    # F-01(2.2): the condenser must reject what the SOLVED STATE carries, so the closure
    # can disagree with the applied duty. Previously h_in/h_out were fixed literals
    # independent of the solution, which made `energy_closes` true by construction --
    # a restatement of its own inputs rather than a check.
    condenser = None
    condenser_duty_matches_applied: bool | None = None
    if points:
        x_out = case.quality_out_at(points[0].mass_flow_kg_s)
        condenser = condenser_energy_boundary(
            mass_flow_kg_s=points[0].mass_flow_kg_s,
            h_in_J_kg=x_out * case.h_fg_J_kg,
            h_out_J_kg=0.0,
            sink_temperature_K=case.sink_temperature_K,
            saturation_temperature_K=case.saturation_temperature_K,
            outlet_is_liquid=True,
        )
        condenser_duty_matches_applied = (
            abs(condenser.duty_W - case.duty_W) <= 1e-6 * max(abs(case.duty_W), 1.0)
        )

    closure = closure_for(points, case)
    return DemonstrationResult(
        case=case,
        pump=pump,
        legs=(leg, inlet_leg),
        operating_points=points,
        closure=closure,
        pump_inlet_feasible=inlet.feasible,
        pump_inlet_reason=inlet.reason,
        condenser_energy_closes=condenser.energy_closes if condenser else None,
        condenser_duty_matches_applied=condenser_duty_matches_applied,
        notes=tuple(
            note
            for note in (
                (
                    "NO ENERGY CLOSURE IS REPORTED: the solution is non-unique "
                    f"({len(points)} steady states). A closure computed on one root "
                    "would be a selection, and a note saying which root was picked "
                    "does not undo the picking. Reporting none states what is known."
                )
                if len(points) > 1
                else "",
                (
                    "NO OPERATING POINT IS REPORTED: the pump inlet is not feasible, "
                    "so the loop cavitates and there is nothing to report a steady "
                    f"state about. {inlet.reason}"
                )
                if not inlet.feasible
                else "",
                (
                    f"TRANSITIONAL FLOW: {transitional} of the sampled points fell in "
                    "the Reynolds band where Stage-1's friction factor blends the "
                    "laminar and turbulent forms, so the characteristic is "
                    "approximate there. Sweeping a flow range crosses that band by "
                    "construction; the caveat is recorded here rather than left in a "
                    "warnings log."
                )
                if transitional
                else "",
            )
            if note
        ),
    )


def solve_reference_case(
    case: LoopCase,
    pump: PumpCharacteristic,
    *,
    flow_min_kg_s: float,
    flow_max_kg_s: float,
    samples: int = 240,
    band_min_m: float,
    band_max_m: float,
    reduced_pressure: float,
    nominal_mass_flow_kg_s: float = 1.0e-2,
) -> ReferenceCaseResult:
    """Solve this project's device, and report honestly what refuses.

    **The refusal is the deliverable, not a failure of the run.** Each blocked leg
    names the axis that refuses, the registry entry that refuses on it, and the state
    that would lift it (S4-7); the pressure-drop leg additionally reports whether its
    refusal is an absence of knowledge or a policy position (S4-8), on the strength of
    a computed assessment rather than a recollection.
    """
    if case.kind is not RunKind.REFERENCE_CASE:
        raise ValueError(
            "solve_reference_case requires a case declared as the reference case; "
            f"this one declares {case.kind.value}"
        )
    _assert_describes_the_device(case)

    with _collected_transitional_warnings():
        dp_leg = _pressure_drop_leg(case)

    # The candidate's basis is assessed at THIS loop's own mean quality, not at a
    # convenient one. Two of its declared axes are functions of quality, and the
    # window they admit is empty on both sides of a middle band -- so a quality picked
    # for tidiness would decide the answer.
    x_mean = 0.5 * (case.quality_in + case.quality_out_at(nominal_mass_flow_kg_s))
    assessment = assess_declared_basis(
        mass_flow_kg_s=nominal_mass_flow_kg_s,
        band_min_m=band_min_m,
        band_max_m=band_max_m,
        reduced_pressure=reduced_pressure,
        quality=x_mean,
        mu_f=case.mu_f,
        mu_g=case.mu_g,
    )
    refusal = classify_pressure_drop_refusal(
        assessment,
        admitting_qualities=qualities_admitting_any_bore(
            mass_flow_kg_s=nominal_mass_flow_kg_s,
            band_min_m=band_min_m,
            band_max_m=band_max_m,
            reduced_pressure=reduced_pressure,
            mu_f=case.mu_f,
            mu_g=case.mu_g,
        ),
    )
    if not dp_leg.available:
        dp_leg = LegStatus(
            leg="pressure drop",
            entry_id=DP_ID,
            available=False,
            axis="composition/orientation",
            reason=dp_leg.reason,
            would_unblock=(
                f"an adopted correlation whose declared basis covers single-component "
                f"ammonia in non-horizontal flow. {KIM_MUDAWAR_ID} is registered as a "
                "sensitivity and assessed; adopting it would require amending A4."
            ),
            refusal_kind=refusal.kind,
        )

    htc_leg = LegStatus(
        leg="boiling HTC",
        entry_id=HTC_ID,
        available=False,
        axis="fluid",
        reason=(
            "ammonia is absent from the development database of "
            f"{HTC_ID} (DEBTS D-6), so the correlation is out of database for this "
            "loop's working fluid."
        ),
        would_unblock=(
            f"an ammonia-valid flow-boiling correlation. {SHAH_1974_ID} is the only "
            "ammonia source in the registry and refuses this loop on four axes of its "
            "own declared range -- pressure, heat flux, mass flow and orientation."
        ),
        refusal_kind="knowledge",
    )
    condensation_leg = LegStatus(
        leg="condensation",
        entry_id="(none)",
        available=False,
        axis="existence",
        reason=(
            "the registry contains NO condensation entry of any kind (DEBTS D-11). "
            "The condenser is an energy boundary only (Director ruling D10) and any "
            "quantity needing a condensation coefficient is blocked, not estimated."
        ),
        would_unblock="a sourced condensation heat-transfer correlation valid for ammonia.",
        refusal_kind="knowledge",
    )
    chf_leg = LegStatus(leg="CHF", entry_id=CHF_ID, available=True)

    points: tuple[OperatingPoint, ...] = ()
    note_lines: list[str] = []
    if dp_leg.available:
        with _collected_transitional_warnings():
            points = find_operating_points(
                case,
                pump,
                flow_min_kg_s=flow_min_kg_s,
                flow_max_kg_s=flow_max_kg_s,
                samples=samples,
            )
    else:
        note_lines.append(
            "NO OPERATING POINT WAS COMPUTED, and none is estimated. The loop's "
            "internal pressure-drop/flow-rate characteristic cannot be built, so "
            "there is nothing for the external characteristic to intersect and "
            "nothing for the static Ledinegg guard to evaluate. The guard is "
            f"implemented and verified against {LEDINEGG_ID}; it has no argument "
            "here. That is a SECOND and separate reason it does not fire on this "
            "case -- the first is in the guard disclosure above, and applies even "
            "where the characteristic CAN be built."
        )
        note_lines.append(
            "ENERGY CLOSURE IS NOT REPORTED. Pump heat in the rejected load needs a "
            "pressure drop, and the pressure drop is the leg that refused. Reporting "
            "a balance without it would be reporting a balance about a different loop."
        )

    return ReferenceCaseResult(
        case=case,
        pump=pump,
        legs=(dp_leg, htc_leg, condensation_leg, chf_leg),
        operating_points=points,
        notes=tuple(note_lines),
        pressure_drop_refusal=(
            f"PRESSURE-DROP REFUSAL, CHARACTERISED: {refusal.detail}\n\n"
            f"ASSESSMENT IT RESTS ON: {assessment.summary()}"
        ),
    )


def registered_s4_entries() -> tuple[str, ...]:
    """The registry ids S4 depends on, resolved so a rename cannot go unnoticed."""
    ids = (DP_ID, HTC_ID, CHF_ID, NPSH_ID, LEDINEGG_ID, KIM_MUDAWAR_ID, SHAH_1974_ID)
    for entry_id in ids:
        get(entry_id)
    return ids


__all__ = [
    "Characteristic",
    "CharacteristicPoint",
    "characteristic_is_monotone",
    "loop_characteristic",
    "operating_points_from_characteristic",
    "DemonstrationResult",
    "EnergyClosure",
    "LegStatus",
    "LoopCase",
    "OperatingPoint",
    "PumpCharacteristic",
    "ReferenceCaseResult",
    "RunKind",
    "demonstrate_machinery",
    "energy_closure",
    "find_operating_points",
    "internal_characteristic",
    "registered_s4_entries",
    "solve_reference_case",
]
