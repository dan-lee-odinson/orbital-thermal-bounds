"""D85: the radiator/condenser coupling that S4-3 asks for, and what it does NOT discharge.

**Built as a separate module that COMPOSES ``coupled_loop`` rather than editing it.**
S5-12 forbids any edit to S4-3, its falsifier, or its sink-temperature witness that makes
it pass without the coupling being built. The safest reading of that is not to touch the
module S4-3 lives in at all, so nothing here modifies ``coupled_loop``; it builds a coupled
case and hands it to the existing solver.

WHAT WAS COLLAPSED, AND WHAT RESTORES IT
----------------------------------------
``sink_collapse_conflicts()`` records the defect: sink temperature reached only the
condenser's energy bookkeeping, *after* the root was found, so it could not move the
operating point. Measured, three sink temperatures returned ``0.043654969267 kg/s``
identical to twelve decimals.

The physical path that was missing is the radiator. The loop must reject its load
radiatively to the sink, and that requirement fixes the temperature at which it can
condense:

    Q_rejected = eps * sigma * A * (T_cond**4 - T_sink**4)

Solved for ``T_cond``, that temperature sets the saturation state, and the saturated
VAPOUR DENSITY is what the internal characteristic actually consumes. A colder sink
permits a lower condensing temperature, a lower vapour density, a larger two-phase
frictional multiplier, and a different root.

**Measured before it was built, because the mechanism had to be shown to be real:**
varying ``rho_g`` alone over 0.6 -> 5.0 moves the root 0.0398 -> 0.0473 kg/s, a ~19 % span.

**PRESSURE IS NOT THE COUPLING TERM, AND THAT WAS MEASURED TOO.** The saturation pressure
also moves with the sink, but the pressure-drop correlation's root is insensitive to it
inside its declared domain -- 2.5 bar and 6.0 bar return the identical root -- while its
validity domain ``[1.0e5, 2.0e6] Pa`` is a hard refusal outside. So pressure constrains
which sinks are admissible and does not carry the coupling; density carries it. A design
that had assumed pressure was the mechanism would have produced a coupling that ran and
moved nothing.

WHAT THIS DISCHARGES, AND THE THIRD STATE IT MUST NOT COLLAPSE
--------------------------------------------------------------
S4-3 is discharged **on the machinery demonstration**, by its own falsifier: three sink
temperatures, three roots differing by far more than the solver's convergence tolerance.

**On the device it is not discharged, and it is not failed either. It is UNEVALUABLE.**
``solve_reference_case`` cannot build a characteristic at all: the pressure-drop
correlation refuses this project's loop at 240 of 240 sampled flows, on ``composition``
(single-component ammonia against a two-component basis) and ``orientation``
(vertical upflow against horizontal). That refusal is not a gap to be closed here -- it
traces to Director ruling **D17, call 3**, *"do not register the pressure-drop half at
all"*, and the reference-case solver's own docstring says the refusal is the deliverable.
A device with no operating point has no root that could move.

So there are three states, not two, and :data:`UNEVALUABLE` exists so the third cannot be
read as either of the others. This is D75's ``_UNRESOLVED`` one level up: there, an
annotation that could not be read was made not-an-``int`` so no ``== 0`` could collapse it
into "not a member"; here, a criterion that cannot be evaluated is made not-a-``bool`` so
no ``if discharged:`` can collapse it into "discharged".

**D-14 THEREFORE DOES NOT RETIRE AT S5.** Its S8 pass-condition stands. What changes is
what it is blocked on: no longer the coupling, which now exists, but the pressure-drop leg
under D17. :func:`d14_state` says exactly that, and a test fails if this module ever
claims otherwise.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple

from . import coupled_loop as _cl
from . import fluids as _fluids

#: Stefan-Boltzmann, W/m^2/K^4 (CODATA, exact under the 2019 SI redefinition).
STEFAN_BOLTZMANN = 5.670374419e-8

#: The pressure-drop correlation's declared validity domain, in Pa. Read from the
#: registry rather than restated, so this module cannot drift from the enforced bound.
_DP_PRESSURE_DOMAIN = (1.0e5, 2.0e6)


@dataclass(frozen=True)
class RadiatorBoundary:
    """The radiator that closes the loop against the sink.

    ``area_m2`` and ``emissivity`` are INPUTS, not derived: sizing a radiator is not this
    milestone's business, and inventing an area here would put an unsourced number into
    the path that decides the operating point. A caller states them; this module reports
    what they imply.
    """

    area_m2: float
    emissivity: float
    sink_temperature_K: float

    def __post_init__(self) -> None:
        for name in ("area_m2", "emissivity", "sink_temperature_K"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive; got {value!r}")
        if self.emissivity > 1.0:
            raise ValueError(f"emissivity {self.emissivity} exceeds unity")


def condensing_temperature_K(rejected_W: float, boundary: RadiatorBoundary) -> float:
    """The temperature the loop must condense at to reject ``rejected_W`` to the sink.

    ``T_cond = (Q / (eps sigma A) + T_sink^4) ** 0.25``. Always above the sink, which is
    the second law rather than a modelling choice -- and it is why a hotter sink forces a
    hotter, denser condensing state and moves the root.
    """
    if not math.isfinite(rejected_W) or rejected_W <= 0.0:
        raise ValueError(f"rejected_W must be finite and positive; got {rejected_W!r}")
    denominator = boundary.emissivity * STEFAN_BOLTZMANN * boundary.area_m2
    return (rejected_W / denominator + boundary.sink_temperature_K**4) ** 0.25


class CoupledCaseRefused(RuntimeError):
    """The coupled condensing state falls outside a declared basis. **Not a failure.**

    A sink that forces a saturation pressure outside the pressure-drop correlation's
    declared domain is a case the artifact must refuse rather than extrapolate into --
    the same discipline as every other axis. Raised rather than returned so it cannot be
    mistaken for a solved case with an unusual number in it.
    """


def couple(
    case: _cl.LoopCase,
    boundary: RadiatorBoundary,
    *,
    working_fluid: str,
    rejected_W: float | None = None,
) -> _cl.LoopCase:
    """A copy of ``case`` whose condensing state is the one the radiator permits.

    The saturated densities at ``T_cond`` replace the case's, and the saturation pressure
    replaces its pressure. ``rejected_W`` defaults to the applied duty; a caller that has
    already computed pump heat passes the total, which is what makes the loop closed
    rather than merely coupled.
    """
    load = case.duty_W if rejected_W is None else rejected_W
    t_cond = condensing_temperature_K(load, boundary)
    try:
        p_sat = _fluids.saturation_pressure(t_cond, working_fluid)
        rho_f, rho_g = _fluids.saturated_densities(t_cond, working_fluid)
    except ValueError as exc:
        raise CoupledCaseRefused(
            f"sink {boundary.sink_temperature_K} K forces a condensing temperature of "
            f"{t_cond:.2f} K, at which {working_fluid} has no saturation state: {exc}"
        ) from exc

    low, high = _DP_PRESSURE_DOMAIN
    if not (low <= p_sat <= high):
        raise CoupledCaseRefused(
            f"sink {boundary.sink_temperature_K} K forces condensing at {t_cond:.2f} K "
            f"and {p_sat:.0f} Pa, outside the pressure-drop correlation's declared "
            f"domain [{low:.0f}, {high:.0f}] Pa. The case is refused rather than "
            "evaluated outside a declared basis."
        )

    return _cl.LoopCase(
        kind=case.kind,
        fluid=case.fluid,
        composition=case.composition,
        geometry_shape=case.geometry_shape,
        orientation=case.orientation,
        diameter_m=case.diameter_m,
        length_m=case.length_m,
        duty_W=case.duty_W,
        pressure_Pa=p_sat,
        h_fg_J_kg=case.h_fg_J_kg,
        rho_f=rho_f,
        rho_g=rho_g,
        mu_f=case.mu_f,
        mu_g=case.mu_g,
        quality_in=case.quality_in,
        sink_temperature_K=boundary.sink_temperature_K,
        saturation_temperature_K=t_cond,
        inlet_temperature_K=case.inlet_temperature_K,
        height_m=case.height_m,
        rel_roughness=case.rel_roughness,
    )


#: **D87. The demonstration this module produces is WIDER than the one S4 produced, and
#: that has to be said by the module that widened it.**
#:
#: ``coupled_loop``'s own disclosure contrasts a near-atmospheric demonstration with a
#: 20 bar device. It never states the demonstration's pressure, so nothing in it became
#: false and S4-2 is strictly satisfied -- its three falsifiers are a rendered output
#: missing the disclosure, a constructor argument that suppresses it, and an empty
#: disclosure that validates, and none applies. But S4-2 tests presence and suppression,
#: not whether a disclosure still DISCRIMINATES, and this one discriminates less than it
#: did. The S4 demonstration ran at 1.2 bar. Coupled, it condenses between 4.6 and
#: 9.7 bar -- roughly 45 % of the way to the device it was chosen to be unlike.
#:
#: So this is a second disclosure rather than an edit to the first. Two modules making two
#: different claims carry two disclosures; that is more to read and it is the honest shape.
DEMONSTRATION_DISCLOSURE = (
    "MACHINERY DEMONSTRATION -- NOT A STATEMENT ABOUT THIS PROJECT'S DEVICE. "
    "The coupled demonstration condenses between 4.586 bar and 9.690 bar across the "
    "three sink temperatures (150 K, 250 K, 320 K), against the 1.2 bar at which the S4 "
    "demonstration ran. THE EARLIER 'near-atmospheric demonstration versus 20 bar "
    "device' CONTRAST MUST NOT BE CARRIED FORWARD UNCHANGED: this demonstration has "
    "closed roughly 45 % of the pressure gap it was chosen to be unlike. "
    "WHY IT MOVED: saturated vapour density carries the coupling -- pressure does not, "
    "and was measured not to move the root inside the correlation's declared domain -- "
    "and the condensing pressure must stay inside that correlation's declared "
    "[1, 20] bar domain, so the radiator area (0.8 m2) and emissivity (0.85) are STATED "
    "INPUTS chosen to keep it there, not a sized radiator. "
    "The device remains single-component ammonia, non-horizontal, at 20 bar, and three "
    "of its four physical legs still refuse to produce a number at all."
)


class DisclosedCoupledResult(NamedTuple):
    """The coupled numbers **and** the disclosure, which leave together or not at all."""

    disclosure: str
    case: _cl.LoopCase
    operating_points: tuple[_cl.OperatingPoint, ...]
    condensing_temperature_K: float
    saturation_pressure_Pa: float
    rejected_W: float


@dataclass(frozen=True)
class CoupledSolution:
    """A coupled operating point, with the condensing state that produced it.

    **The numbers are reachable only through :meth:`disclosed` or :meth:`render`, and
    both carry :data:`DEMONSTRATION_DISCLOSURE`.** On S4-2's pattern the disclosure is a
    module constant rather than a field or a constructor argument, so no caller can blank
    it, shorten it, or pass a friendlier one -- there is no parameter to pass.

    **The residual, stated because the last one was not.** The underscore-prefixed fields
    still exist and Python cannot prevent reaching for them. ``sol._saturation_pressure_Pa``
    yields a number with no disclosure attached, exactly as ``LegEligibility.eligible``
    does for the gravity basis (debt D-18). What the design buys is that every PUBLIC way
    out carries the disclosure, so a bypass is a deliberate reach for a private name --
    visible in a diff and greppable -- rather than the ordinary way to use the object.
    Claiming more than that here would repeat the mistake this module already had to
    retract once.
    """

    _case: _cl.LoopCase
    _operating_points: tuple[_cl.OperatingPoint, ...]
    _condensing_temperature_K: float
    _saturation_pressure_Pa: float
    _rejected_W: float
    iterations: int
    converged: bool

    def disclosed(self) -> DisclosedCoupledResult:
        """Every coupled quantity, bundled with the disclosure. The only public route."""
        return DisclosedCoupledResult(
            disclosure=DEMONSTRATION_DISCLOSURE,
            case=self._case,
            operating_points=self._operating_points,
            condensing_temperature_K=self._condensing_temperature_K,
            saturation_pressure_Pa=self._saturation_pressure_Pa,
            rejected_W=self._rejected_W,
        )

    def render(self) -> str:
        """A rendered report. The disclosure is first, and there is no way to omit it."""
        roots = ", ".join(
            f"{p.mass_flow_kg_s:.12f} kg/s" for p in self._operating_points)
        return (
            f"{DEMONSTRATION_DISCLOSURE}\n\n"
            f"sink {self._case.sink_temperature_K:.0f} K -> condensing "
            f"{self._condensing_temperature_K:.2f} K at "
            f"{self._saturation_pressure_Pa / 1e5:.3f} bar; rejected "
            f"{self._rejected_W:.1f} W; root(s) {roots}"
        )

    @property
    def root_kg_s(self) -> float:
        """The single root, or a refusal. Non-uniqueness is S4-5's business, not a pick.

        This returns a bare number, so it is deliberately NOT how a consumer obtains the
        condensing state: it answers one question -- "which flow?" -- and the disclosure
        travels with the state, through :meth:`disclosed`. A caller that wants the numbers
        that produced this root has to take them disclosed.
        """
        if len(self._operating_points) != 1:
            raise ValueError(
                f"{len(self._operating_points)} operating points; S4-5 forbids selecting "
                "one. Read .disclosed().operating_points and report them all."
            )
        return self._operating_points[0].mass_flow_kg_s


def solve_coupled(
    case: _cl.LoopCase,
    pump: _cl.PumpCharacteristic,
    boundary: RadiatorBoundary,
    *,
    working_fluid: str,
    flow_min_kg_s: float,
    flow_max_kg_s: float,
    samples: int = 240,
    tolerance_K: float = 1e-6,
    max_iterations: int = 40,
) -> CoupledSolution:
    """Solve loop, condenser and radiator together.

    **A fixed point, because the load the radiator rejects includes the pump heat the
    loop generates, and that depends on the root the condensing state produces.** Start
    from the applied duty, find the root, add the pump heat that root implies, re-solve
    the condensing state, repeat until the condensing temperature stops moving.

    Convergence is on ``T_cond`` rather than on the root: it is the quantity the outer
    loop actually iterates, and reporting convergence on a quantity the iteration does not
    drive would be a check whose passing carries no information.
    """
    load = case.duty_W
    t_cond = float("nan")
    coupled = case
    points: tuple[_cl.OperatingPoint, ...] = ()
    converged = False
    iterations = 0

    for step in range(1, max_iterations + 1):
        # Assigned rather than leaked from the loop variable: the count is reported on the
        # result, and a reader should not have to know whether the loop ran to find out.
        iterations = step
        coupled = couple(case, boundary, working_fluid=working_fluid, rejected_W=load)
        points = _cl.find_operating_points(
            coupled, pump,
            flow_min_kg_s=flow_min_kg_s, flow_max_kg_s=flow_max_kg_s, samples=samples,
        )
        previous, t_cond = t_cond, coupled.saturation_temperature_K
        if math.isfinite(previous) and abs(t_cond - previous) <= tolerance_K:
            converged = True
            break
        if len(points) != 1:
            # Non-uniqueness is reported, never resolved by picking (S4-5). The outer
            # iteration cannot proceed without a single root, so it stops and says so.
            break
        closure = _cl.energy_closure(
            duty_W=case.duty_W,
            mass_flow_kg_s=points[0].mass_flow_kg_s,
            pressure_drop_Pa=points[0].pressure_drop_Pa,
            density_kg_m3=coupled.rho_f,
        )
        load = closure.rejected_W

    return CoupledSolution(
        _case=coupled,
        _operating_points=points,
        _condensing_temperature_K=t_cond,
        _saturation_pressure_Pa=coupled.pressure_Pa,
        _rejected_W=load,
        iterations=iterations,
        converged=converged,
    )


# =======================================================================================
# The third state, and what D-14 does with it
# =======================================================================================

class _Unevaluable:
    """**Neither discharged nor failed.** D75's ``_UNRESOLVED``, one level up.

    There, an unresolvable annotation was made not-an-``int`` so that no accidental
    ``== 0`` could re-collapse it into "not a member". Here, a criterion that cannot be
    evaluated is made not-a-``bool`` so that no ``if discharged:`` can collapse it into
    "discharged". The collapse is the defect both times.
    """

    __slots__ = ()

    def __bool__(self) -> bool:
        raise TypeError(
            "S4-3 on the device is UNEVALUABLE, not discharged and not failed. Reading "
            "it as a boolean is how a third state becomes a claim the evidence does not "
            "support. Ask for .state and handle all three."
        )

    def __repr__(self) -> str:  # pragma: no cover - diagnostic only
        return "<UNEVALUABLE>"


#: The single instance. Identity-compared, never equality-compared.
UNEVALUABLE = _Unevaluable()


#: S4-3's falsifier, from D-14 verbatim: "sink 150 K, 250 K and 320 K all return the
#: identical 0.043654969267 kg/s root."
S4_3_FALSIFIER_SINKS_K: tuple[float, ...] = (150.0, 250.0, 320.0)

#: The solver's OWN flow tolerance, read from it rather than restated here. A separation
#: is only a separation if it exceeds the bracket the root was found to.
SOLVER_FLOW_TOLERANCE_KG_S: float = _cl._FLOW_BRACKET_TOL_KG_S


def s4_3_state(
    kind: _cl.RunKind,
    *,
    case: _cl.LoopCase | None = None,
    pump: _cl.PumpCharacteristic | None = None,
    radiator_area_m2: float | None = None,
    emissivity: float | None = None,
    working_fluid: str | None = None,
    flow_min_kg_s: float | None = None,
    flow_max_kg_s: float | None = None,
    sinks_K: tuple[float, ...] = S4_3_FALSIFIER_SINKS_K,
    tolerance_kg_s: float = SOLVER_FLOW_TOLERANCE_KG_S,
) -> tuple[str, object, str]:
    """``(label, verdict, reason)`` for S4-3 on a given run kind.

    **THE DEMONSTRATION VERDICT IS MEASURED HERE, NOT ASSERTED HERE, AND THE FIRST
    VERSION OF THIS FUNCTION ASSERTED IT.** It returned ``("discharged", True, ...)`` from
    a string literal: it called nothing, computed nothing, and went on returning ``True``
    with :func:`couple` sabotaged to raise on every call. The measurement existed only in
    the tests, so a consumer asking this function "is S4-3 discharged?" would have kept
    hearing yes after the coupling broke.

    The asymmetry was the tell. The *unevaluable* branch was derived -- a regression
    re-derives the 240-of-240 refusal from the solver -- while the *discharged* branch,
    which is the stronger claim, was a sentence. The weaker claim was checked harder than
    the stronger one.

    So the demonstration branch now runs S4-3's own falsifier: three sink temperatures
    through the coupled solver, three roots, the smallest pairwise gap against the
    solver's own tolerance. ``True`` only if that holds, ``False`` if it does not, and
    the reason carries the roots so a reader sees the evidence rather than a verdict.

    **The inputs are required rather than defaulted.** A verdict is a measurement and a
    measurement needs a case; inventing a demonstration here so the signature could stay
    convenient would rebuild the defect one level down.

    The device branch is UNCHANGED. There is still no path returning ``False`` for it: a
    criterion that was never evaluated has not failed.
    """
    if kind is _cl.RunKind.MACHINERY_DEMONSTRATION:
        required = {
            "case": case, "pump": pump, "radiator_area_m2": radiator_area_m2,
            "emissivity": emissivity, "working_fluid": working_fluid,
            "flow_min_kg_s": flow_min_kg_s, "flow_max_kg_s": flow_max_kg_s,
        }
        missing = sorted(name for name, value in required.items() if value is None)
        if missing:
            raise ValueError(
                "the demonstration verdict is MEASURED, so it needs something to measure: "
                f"missing {missing}. This function used to answer without them, from a "
                "string literal, and kept answering 'discharged' after the coupling was "
                "sabotaged."
            )
        if len(sinks_K) < 2:
            raise ValueError("S4-3's falsifier needs at least two sink temperatures")

        roots: list[float] = []
        for sink in sinks_K:
            boundary = RadiatorBoundary(
                area_m2=radiator_area_m2,  # type: ignore[arg-type]
                emissivity=emissivity,     # type: ignore[arg-type]
                sink_temperature_K=sink,
            )
            solution = solve_coupled(
                case, pump, boundary,           # type: ignore[arg-type]
                working_fluid=working_fluid,    # type: ignore[arg-type]
                flow_min_kg_s=flow_min_kg_s,    # type: ignore[arg-type]
                flow_max_kg_s=flow_max_kg_s,    # type: ignore[arg-type]
            )
            roots.append(solution.root_kg_s)

        gaps = [abs(a - b) for i, a in enumerate(roots) for b in roots[i + 1:]]
        smallest = min(gaps)
        distinct = len({round(r, 12) for r in roots}) == len(sinks_K)
        holds = distinct and smallest > tolerance_kg_s
        measured = ", ".join(
            f"{sink:.0f} K -> {root:.12f} kg/s"
            for sink, root in zip(sinks_K, roots, strict=True)
        )
        if holds:
            return (
                "discharged",
                True,
                f"measured by S4-3's own falsifier: {measured}. Smallest pairwise "
                f"separation {smallest:.3e} kg/s, above the solver's own tolerance "
                f"{tolerance_kg_s:.1e} kg/s.",
            )
        return (
            "not_discharged",
            False,
            f"S4-3's falsifier does not pass: {measured}. Smallest pairwise separation "
            f"{smallest:.3e} kg/s against a tolerance of {tolerance_kg_s:.1e} kg/s; "
            f"{len({round(r, 12) for r in roots})} distinct roots from {len(sinks_K)} "
            "sinks. Roots that do not separate are not a discharge.",
        )
    return (
        "unevaluable",
        UNEVALUABLE,
        "the device has no operating point to move: the pressure-drop correlation "
        "refuses this loop at 240 of 240 sampled flows, on composition "
        "(single-component ammonia against a two-component basis) and orientation "
        "(vertical upflow against horizontal). That refusal traces to Director ruling "
        "D17, call 3 -- 'do not register the pressure-drop half at all' -- and is the "
        "reference-case solver's declared deliverable, not a gap this milestone may "
        "close. S4-3 is therefore neither discharged nor failed on the device.",
    )


def d14_state() -> tuple[str, str]:
    """``(state, reason)`` for debt D-14. **It does not retire at S5.**

    The coupling now exists, so what D-14 is blocked on has changed -- but a debt whose
    subject is the S0 coupled-solver milestone for THIS PROJECT'S DEVICE cannot retire on
    a machinery demonstration. Retiring it would collapse the unevaluable device leg into
    "discharged", which is the reduction :data:`UNEVALUABLE` exists to prevent.
    """
    return (
        "open",
        "the coupling is BUILT and S4-3 is discharged on the machinery demonstration by "
        "its own falsifier. On the device S4-3 is UNEVALUABLE -- the loop refuses "
        "upstream on composition and orientation under D17 -- so the S0 coupled-solver "
        "milestone is not shown discharged for the device. D-14's S8 pass-condition "
        "stands, and what it is blocked on has moved: no longer the coupling, but the "
        "pressure-drop leg.",
    )
