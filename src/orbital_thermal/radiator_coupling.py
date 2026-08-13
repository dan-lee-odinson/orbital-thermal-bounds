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

WHAT THIS DISCHARGES -- NOTHING -- AND THE THIRD STATE IT MUST NOT COLLAPSE
---------------------------------------------------------------------------
**THIS HEADER USED TO SAY S4-3 WAS DISCHARGED ON THE MACHINERY DEMONSTRATION. IT IS NOT,
AND THE WITHDRAWAL IS D90/F-01.** The demonstration that produced three separated roots
was a hybrid case, and no consistent one is available under the implemented correlation
set. S4-3 is UNEVALUABLE on BOTH legs, terminally, and this module discharges nothing.

**On the device it is unevaluable for a second and independent reason.**
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

**D-14 THEREFORE DOES NOT RETIRE AT S5.** Its S8 pass-condition stands, and it is
blocked on THE COUPLING -- the mechanism exists but has no case it can be demonstrated
on. This header previously said the blocker was "no longer the coupling ... but the
pressure-drop leg"; that was true between D85 and D90 and is not true now.
:func:`d14_state` is the operative statement, and
``test_f03_every_current_surface_agrees_with_the_operative_verdict`` compares this
header against it rather than trusting either.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple

from . import coupled_loop as _cl
from . import fluids as _fluids
from .registry import two_phase as _tp
from .registry.provenance import Status as _Status

#: Stefan-Boltzmann, W/m^2/K^4 (CODATA, exact under the 2019 SI redefinition).
STEFAN_BOLTZMANN = 5.670374419e-8

#: The registry key under which the pressure-drop correlation declares its pressure
#: domain. Named as data so the resolution is auditable and so a renamed key fails loudly
#: rather than silently falling back to a literal.
_DP_PRESSURE_KEY = "P_Pa"


def _dp_pressure_domain() -> tuple[float, float]:
    """The adopted pressure-drop correlation's declared pressure domain, **resolved**.

    **D97/F-04.** This module used to carry ``_DP_PRESSURE_DOMAIN = (1.0e5, 2.0e6)`` under
    a comment claiming it was "read from the registry rather than restated, so this module
    cannot drift from the enforced bound". It was a second literal. It happened to equal
    the registry's ``P_Pa`` and nothing held it equal -- no test and no certificate row
    bound them. The comment described a protection that did not exist, which is this
    project's signature defect written into a source file.

    Now it is resolved at the boundary, every call, from the entry that is actually
    adopted. A missing, malformed or ambiguous range refuses rather than falling back:
    a coupling that cannot find the bound it is enforcing must not proceed on a guess.
    """
    adopted = [
        e for e in _tp.TWO_PHASE_CORRELATIONS
        if e.kind == "dp" and e.status is _Status.RESOLVED
    ]
    if len(adopted) != 1:
        raise CoupledCaseRefused(
            f"{len(adopted)} pressure-drop correlations are adopted for ranking "
            f"({', '.join(e.id for e in adopted)}); which one's declared pressure domain "
            "bounds the coupling is a decision, not something this function may pick."
        )
    ranges = getattr(getattr(adopted[0], "domain", None), "ranges", None) or {}
    declared = ranges.get(_DP_PRESSURE_KEY)
    if declared is None or len(declared) != 2:
        raise CoupledCaseRefused(
            f"{adopted[0].id} declares no usable {_DP_PRESSURE_KEY} range "
            f"({declared!r}). The coupling enforces the correlation's own bound and has "
            "no bound of its own to fall back on."
        )
    low, high = (float(declared[0]), float(declared[1]))
    if not (low < high):
        raise CoupledCaseRefused(
            f"{adopted[0].id} declares an inverted or empty {_DP_PRESSURE_KEY} range "
            f"({low}, {high})."
        )
    return low, high


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


#: Case ``fluid`` labels that name the same substance as a CoolProp fluid name. Kept as
#: data because the check must be a comparison a reader can audit, not a fuzzy match: a
#: guard against substituting one fluid's properties into another fluid's case cannot
#: itself guess which two names mean the same thing.
_FLUID_ALIASES: dict[str, str] = {
    "water": "water",
    "h2o": "water",
    "ammonia": "ammonia",
    "nh3": "ammonia",
    "r717": "ammonia",
}


def _refuse_inconsistent_fluid(case: _cl.LoopCase, working_fluid: str) -> None:
    """**Sol's F-01, and the guard this module never had.**

    Measured on the shipped demonstration at the 250 K sink: the case was admitted to the
    pressure-drop correlation as ``two_component`` ``air-water``, and then evolved with
    single-component WATER saturation properties -- ``rho_g`` 1.2 -> 3.218 (saturated
    steam), ``rho_f`` 997 -> 907.97, pressure 1.2 -> 6.099 bar -- while ``mu_g`` stayed at
    air's 1.8e-5 against steam's 1.429e-5, 26 % wrong. **The ``rho_g`` that moved the
    roots, which is the mechanism D87 was built around, was steam density inside a case
    represented to the applicability guard as air-water.**

    Nothing related ``working_fluid`` to ``case.fluid`` or ``case.composition``, so the
    case passed the guard on labels the saturation model contradicts. Substituting one
    fluid's densities into another fluid's case is the defect; this refusal is what makes
    it unrepeatable.

    **Two conditions, both necessary.** A saturation state exists only for ONE substance,
    so a ``two_component`` case has no condensing state this coupling could use; and the
    substance the properties come from must be the substance the case declares.
    """
    if case.composition != "single_component":
        raise CoupledCaseRefused(
            f"the case declares composition {case.composition!r}, but a condensing "
            f"state exists only for a single substance. Coupling it to "
            f"{working_fluid!r}'s saturation curve would put one fluid's densities into "
            "another fluid's case -- which is exactly Sol's F-01, measured on the "
            "shipped demonstration."
        )
    declared = _FLUID_ALIASES.get(case.fluid.strip().lower())
    supplied = _FLUID_ALIASES.get(working_fluid.strip().lower())
    if declared is None or supplied is None or declared != supplied:
        raise CoupledCaseRefused(
            f"the case declares fluid {case.fluid!r} and the coupling was asked for "
            f"{working_fluid!r}'s saturation properties. They must name the same "
            "substance, and a name this guard does not recognise is refused rather than "
            "assumed to match: a guard against fluid substitution cannot guess which two "
            f"names mean the same thing. Recognised: {sorted(set(_FLUID_ALIASES))}."
        )


#: Every physical property a ``LoopCase`` carries that is a function of the saturation
#: state. **All of them are derived; none is retained.** Named as data so the witness can
#: enumerate them rather than list them, and so adding a property to ``LoopCase`` without
#: deriving it is visible here rather than silent.
SATURATION_DEPENDENT_FIELDS: tuple[str, ...] = (
    "pressure_Pa", "h_fg_J_kg", "rho_f", "rho_g", "mu_f", "mu_g",
)


def couple(
    case: _cl.LoopCase,
    boundary: RadiatorBoundary,
    *,
    working_fluid: str,
    rejected_W: float | None = None,
) -> _cl.LoopCase:
    """A copy of ``case`` at the condensing state the radiator permits.

    **D97/F-01: built from ONE verified saturation state, and nothing is retained.**

    The previous version substituted three saturation-dependent properties -- pressure and
    the two densities -- and copied three others that are equally saturation-dependent and
    equally consumed by the characteristic. Measured on a case whose BOTH labels were
    correct, so no label comparison could have caught it: ``mu_f`` was **420 % wrong**,
    ``mu_g`` 26 % wrong (the same air viscosity as round 1), ``h_fg`` 8.5 % wrong. The
    round-1 repair compared labels, and labels were all it compared.

    So the shape is removed rather than guarded. Every field in
    :data:`SATURATION_DEPENDENT_FIELDS` is taken from a single
    :class:`fluids.SaturationState`, and that state is verified with
    :meth:`fluids.SaturationState.verify_is`, which **re-derives every property from the
    pinned backend and compares them** -- its own docstring records this defect class, and
    the round-1 repair reached past it for a string comparison.

    A hybrid is therefore not refused; it cannot be constructed. What ``verify_is`` still
    catches at the boundary is a state that has been relabelled or produced under a
    different pinned backend version.
    """
    _refuse_inconsistent_fluid(case, working_fluid)
    load = case.duty_W if rejected_W is None else rejected_W
    t_cond = condensing_temperature_K(load, boundary)
    try:
        p_sat = _fluids.saturation_pressure(t_cond, working_fluid)
    except ValueError as exc:
        raise CoupledCaseRefused(
            f"sink {boundary.sink_temperature_K} K forces a condensing temperature of "
            f"{t_cond:.2f} K, at which {working_fluid} has no saturation state: {exc}"
        ) from exc

    low, high = _dp_pressure_domain()
    if not (low <= p_sat <= high):
        raise CoupledCaseRefused(
            f"sink {boundary.sink_temperature_K} K forces condensing at {t_cond:.2f} K "
            f"and {p_sat:.0f} Pa, outside the pressure-drop correlation's declared "
            f"domain [{low:.0f}, {high:.0f}] Pa. The case is refused rather than "
            "evaluated outside a declared basis."
        )

    # ONE state, and it is verified before a single property is read off it.
    try:
        state = _fluids.saturation_state(p_sat, working_fluid)
        state.verify_is(case.fluid)
    except ValueError as exc:
        raise CoupledCaseRefused(
            f"the saturation state at {p_sat:.0f} Pa does not verify as "
            f"{case.fluid!r}: {exc}"
        ) from exc

    derived = {
        "pressure_Pa": state.pressure_Pa,
        "h_fg_J_kg": state.h_fg_J_kg,
        "rho_f": state.rho_f_kg_m3,
        "rho_g": state.rho_g_kg_m3,
        "mu_f": state.mu_f_Pa_s,
        "mu_g": state.mu_g_Pa_s,
    }
    assert set(derived) == set(SATURATION_DEPENDENT_FIELDS), (
        "every saturation-dependent field must be derived from the state; a field named "
        "in SATURATION_DEPENDENT_FIELDS and missing here would be silently retained"
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
        quality_in=case.quality_in,
        sink_temperature_K=boundary.sink_temperature_K,
        saturation_temperature_K=state.T_sat_K,
        inlet_temperature_K=case.inlet_temperature_K,
        height_m=case.height_m,
        rel_roughness=case.rel_roughness,
        **derived,
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
    iterations: int
    converged: bool


class DisclosedRoot(NamedTuple):
    """A root and its disclosure. They leave together or the root does not leave."""

    disclosure: str
    root_kg_s: float


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
    _iterations: int
    _converged: bool

    def disclosed(self) -> DisclosedCoupledResult:
        """Every coupled quantity, bundled with the disclosure. The only public route."""
        return DisclosedCoupledResult(
            disclosure=DEMONSTRATION_DISCLOSURE,
            case=self._case,
            operating_points=self._operating_points,
            condensing_temperature_K=self._condensing_temperature_K,
            saturation_pressure_Pa=self._saturation_pressure_Pa,
            rejected_W=self._rejected_W,
            iterations=self._iterations,
            converged=self._converged,
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

    def disclosed_root(self) -> DisclosedRoot:
        """The single root, WITH the disclosure. **Sol's F-03, ruled at D92.**

        ``root_kg_s`` was a public property returning ``0.046404853853`` bare, while this
        class's own docstring said the coupled numbers were reachable only through
        :meth:`disclosed` or :meth:`render`. That was not the D-19 private-field residual
        -- it was the ordinary public route the tests, the certificate and the withdrawn
        S4-3 discharge all used, and the docstring was false about it.

        Sol's fix, adopted verbatim: the public root route carries the same disclosure as
        every other coupled result, or ceases to be public. It does both -- the bare
        property is gone, and what replaces it is disclosed.

        Non-uniqueness is still S4-5's business and still refuses rather than picking.
        """
        return DisclosedRoot(DEMONSTRATION_DISCLOSURE, self._root_kg_s())

    def _root_kg_s(self) -> float:
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
        _iterations=iterations,
        _converged=converged,
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


class S4_3_Verdict(NamedTuple):
    """The state of S4-3 for one run kind. **Its own truth test refuses.**

    **Sol's F-05.** The sentinel was fine and the wrapper was not: ``s4_3_state`` returned
    an ordinary non-empty 3-tuple, so ``if s4_3_state(RunKind.REFERENCE_CASE):`` put the
    UNEVALUABLE device in the true branch without ``_Unevaluable.__bool__`` ever running.
    A protection that is real at the member and absent at the surface transporting it is
    no protection -- the same class as F-03.

    Destructuring still works, so ``label, verdict, reason = ...`` is unaffected. What is
    refused is the collapse: reading the whole result as a boolean.
    """

    label: str
    verdict: object
    reason: str

    def __bool__(self) -> bool:
        raise TypeError(
            f"S4-3 is {self.label!r} and this result has no bare truth value. Reading it "
            "as one is how a third state becomes a claim the evidence does not support "
            "(F-05). Destructure it, or read .label and handle every state."
        )


def s4_3_state(kind: _cl.RunKind) -> S4_3_Verdict:
    """The state of S4-3 for a run kind. **UNEVALUABLE on BOTH legs, and there is no
    path to True for either.**

    **D90/F-01: the discharge is withdrawn.** The demonstration that produced three
    separated roots was not one fluid. It was admitted to the pressure-drop correlation as
    ``two_component`` ``air-water`` and evolved with single-component WATER saturation
    properties; nothing related ``working_fluid`` to ``case.fluid`` or
    ``case.composition``, and its ``mu_g`` stayed at air's value while its densities became
    steam's. Three separated roots from a hybrid case do not discharge S4-3, so the
    demonstration branch no longer returns ``discharged``.

    **And a consistent demonstration is not available, measured rather than assumed.** The
    only implemented pressure-drop correlation admits ``two_component`` ONLY -- a
    ``single_component`` case is de-ranked on the composition axis. The coupling needs a
    saturation state, which exists only for one substance: ``air-water`` is not a fluid,
    and ``Air`` has no saturation state above its 132.53 K critical temperature. The
    correlation demands two components and the coupling demands one condensable substance,
    so no case satisfies both. **Unevaluable on both legs is the terminal state**, and it
    is the same structural refusal that makes the device unevaluable -- D17 call 3 left no
    single-component pressure-drop half registered.

    There is deliberately still no path returning ``False``: a criterion that cannot be
    evaluated has not failed.
    """
    if kind is _cl.RunKind.MACHINERY_DEMONSTRATION:
        return S4_3_Verdict(
            "unevaluable",
            UNEVALUABLE,
            "the demonstration that produced three separated roots was NOT ONE FLUID: it "
            "was admitted to the pressure-drop correlation as two_component 'air-water' "
            "and evolved with single-component water saturation properties (rho_g "
            "1.2 -> 3.218 saturated steam, rho_f 997 -> 907.97, pressure 1.2 -> 6.099 bar) "
            "while mu_g stayed at air's 1.8e-5 against steam's 1.429e-5. No consistency "
            "check related working_fluid to case.fluid or case.composition, so the case "
            "passed the applicability guard on labels the saturation model contradicts. "
            "Three separated roots from that hybrid do not discharge S4-3, and the "
            "discharge is withdrawn (D90/F-01). A consistent demonstration is not "
            "available either: the only implemented pressure-drop correlation admits "
            "two_component only, and a condensing state exists only for a single "
            "substance, so no case satisfies both.",
        )
    return S4_3_Verdict(
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

class D14State(NamedTuple):
    """D-14's state. **Its own truth test refuses, for F-05's reason.**

    Found by doing what F-05 says to do -- "check the other public returns in this module
    for the same shape before you finish". ``d14_state()`` returned a plain 2-tuple, so
    ``if d14_state():`` was true whether the debt was open or retired. That is the same
    defect one function over: a state a consumer can collapse without ever reading it.
    """

    state: str
    reason: str

    def __bool__(self) -> bool:
        raise TypeError(
            f"D-14 is {self.state!r}; this result has no bare truth value. A 2-tuple is "
            "always true, so `if d14_state():` reads the same open or retired (F-05). "
            "Destructure it, or read .state."
        )


def d14_state() -> D14State:
    """D-14's state. **Open, and the blocker HAS MOVED BACK to the coupling.**

    **This is a moving claim and it moved back, which is why it is stated rather than
    implied.** After D85 it read "no longer the coupling, but the pressure-drop leg" --
    the coupling existed and S4-3 was discharged on the demonstration. D90/F-01 withdrew
    that discharge: the demonstration was a hybrid case, and no consistent one is
    available under the implemented correlation set. So the coupling is again what D-14
    waits on, not the pressure-drop leg.

    The mechanism built at D85 is not deleted and is not wrong -- the radiative closure,
    the fixed point and the density path all stand. What is gone is any case it can be
    demonstrated on, which is a different failure and is recorded as one.
    """
    return D14State(
        "open",
        "the coupling MECHANISM is built -- radiative closure, fixed point on the "
        "condensing state, density carrying the coupling -- but S4-3 is UNEVALUABLE on "
        "BOTH legs and no discharge stands. The demonstration that once discharged it "
        "was a hybrid case (D90/F-01, discharge withdrawn), and no consistent "
        "demonstration is available: the only implemented pressure-drop correlation "
        "admits two_component only, while a condensing state exists for a single "
        "substance only. THE BLOCKER HAS MOVED BACK TO THE COUPLING -- after D85 this "
        "reason said the pressure-drop leg, and that is no longer true. D-14's S8 "
        "pass-condition stands.",
    )
