"""Stage 2, milestone S3: the rest of the loop — pressure drop, condenser, pump inlet.

S2 built the evaporator. S3 adds the three remaining components, so that after this
milestone all four exist and S4 can solve them together.

**What is here**

* **Two-phase pressure drop** — frictional (Lockhart–Martinelli/Chisholm), acceleration,
  and **static**. Assembled at a boundary that enforces the frictional correlation's
  declared applicability and returns a result carrying its own violations.
* **The condenser as an ENERGY BOUNDARY** (Director ruling D10) — heat out, state
  change, bookkeeping against the A3 fixed effective sink.
* **Pump-inlet feasibility** as a **subcooling margin** (ruling D8), on the AMS-02
  flight precedent.
* **The bore sweep** (ruling D11) — bore is the one free parameter, read from the
  registry; **length is derived from the heat duty, never swept**.

**What is deliberately NOT here**

* **No condensation heat-transfer coefficient.** D10 makes the condenser an energy
  boundary at S3 and defers condensation to S4; the registry contains no condensation
  entry of any kind and none is added. Anything needing a condensation coefficient is
  **blocked, not estimated** (DEBTS D-11).
* **No Friedel, no Müller–Steinhagen–Heck.** A4 makes them named sensitivities and this
  milestone implements the reference only; both keep ``evaluate=None``.
* **No coupled solve.** The components are evaluated and classified individually; S4
  solves them as one system.

**The frictional correlation does not apply to this loop, and that is the result.**
Lockhart–Martinelli's declared basis is horizontal, two-component, near-atmospheric
flow. This loop is single-component ammonia, not horizontal, to 20 bar. The pressure
drop is therefore computed and reported with its violations attached, never as a
rank-eligible number. See :mod:`orbital_thermal.registry.two_phase` for the source.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import _validate as _v
from .registry import NotRankEligibleError, assert_in_domain, get
from .registry.applicability import Consequence, Violation, case_contradictions
from .registry.collapse import Collapse, CollapsedModel, ModelTerm
from .registry.two_phase import (
    STANDARD_GRAVITY_M_S2,
    TWO_PHASE_PROPERTIES,
    accelerational_pressure_drop,
    lockhart_martinelli_frictional_gradient,
    pump_inlet_subcooling_margin,
    static_pressure_drop,
)

DP_ID = "two_phase.dp.lockhart_martinelli_chisholm"
NPSH_ID = "two_phase.pump.npsh"
HTC_ID = "two_phase.htc.gungor_winterton"
CHF_ID = "two_phase.chf.shah_1987"

#: The pure coolants the registry carries a saturation backend for. Read from the
#: registry rather than restated, so it tracks the entries. Every one of them is a
#: single substance, which is what makes "this fluid, and also two-component flow" a
#: contradiction rather than merely an out-of-basis case (F-02).
REGISTERED_SINGLE_COMPONENT_FLUIDS: frozenset[str] = frozenset(
    e.material.lower() for e in TWO_PHASE_PROPERTIES
)


# --- the bore band, DERIVED from the registry (ruling D11) -----------------------


@dataclass(frozen=True)
class BoreBand:
    """The bore range the adopted correlations jointly admit, with its provenance."""

    min_m: float
    max_m: float
    binding_entry_id: str
    provenance_label: str
    contributors: tuple[str, ...]

    def contains(self, diameter_m: float) -> bool:
        return self.min_m <= diameter_m <= self.max_m


def bore_band(entry_ids: tuple[str, ...] = (HTC_ID, CHF_ID)) -> BoreBand:
    """The intersection of the adopted correlations' declared ``D_m`` domains.

    **Read from the registry, not hard-coded** (ruling D11), so the band tracks the
    entries: if a correlation's declared diameter domain changes, the sweep band moves
    with it rather than silently disagreeing.

    Today this is Gungor & Winterton 1.224–32 mm against Shah (1987) 0.315–37.5 mm, so
    GW86 binds both ends. Its limits are **provenance-unestablished** (DEBTS D-1: they
    appear in none of twenty-one consulted sources), and that label travels on the band
    so it reaches the reported output rather than a comment.
    """
    lo, hi, binder = -float("inf"), float("inf"), ""
    labels: list[str] = []
    for eid in entry_ids:
        entry = get(eid)
        rng = entry.domain.ranges.get("D_m")
        if rng is None:
            continue
        if rng[0] > lo:
            lo, binder = rng[0], eid
        if rng[1] < hi:
            hi, binder = rng[1], eid
        spec = entry.applicability_spec
        if spec is not None:
            labels.extend(spec.provenance_caveats())
    if not (lo < hi):
        raise NotRankEligibleError(
            f"the adopted correlations' declared D_m domains do not intersect: "
            f"[{lo}, {hi}]"
        )
    return BoreBand(
        min_m=lo,
        max_m=hi,
        binding_entry_id=binder,
        provenance_label=(
            "PROVENANCE-UNESTABLISHED: the binding diameter limits come from "
            f"'{binder}', whose declared numeric domain appears in none of the "
            "twenty-one consulted sources (DEBTS D-1). They are enforced as guards but "
            "are not the authors' declared range."
        ),
        contributors=tuple(entry_ids),
    )


# --- length is DERIVED from the duty, never swept (ruling D11) -------------------


def required_length_m(
    *,
    duty_W: float,
    mass_flow_kg_s: float,
    h_in_J_kg: float,
    h_out_J_kg: float,
    diameter_m: float,
    wall_flux_W_m2: float,
) -> float:
    """Heated length needed to collect ``duty_W``, m.

    From the energy balance: the wall area required to move the duty at the modelled
    wall flux, converted to a length at this bore. **Length is not a second sweep
    axis** — for a given duty and mass flow it follows from the physics, and sweeping
    it independently would be sweeping something already determined (ruling D11).

    ``mass_flow_kg_s``, ``h_in_J_kg`` and ``h_out_J_kg`` are taken so the caller's duty
    is checked against the enthalpy rise it claims, rather than trusted.
    """
    _v.positive("duty_W", duty_W)
    _v.positive("mass_flow_kg_s", mass_flow_kg_s)
    _v.positive("diameter_m", diameter_m)
    _v.positive("wall_flux_W_m2", wall_flux_W_m2)

    energy_duty = mass_flow_kg_s * (h_out_J_kg - h_in_J_kg)
    if energy_duty <= 0.0:
        raise ValueError(
            f"the stated enthalpy rise carries {energy_duty:.6g} W, so it cannot "
            f"deliver a duty of {duty_W:.6g} W; check h_in/h_out against the duty"
        )
    if abs(energy_duty - duty_W) > 1e-6 * max(abs(duty_W), 1.0):
        raise ValueError(
            f"duty {duty_W:.6g} W disagrees with the enthalpy rise "
            f"m_dot*(h_out-h_in) = {energy_duty:.6g} W; the two must be the same duty"
        )

    area_m2 = duty_W / wall_flux_W_m2
    import math

    return area_m2 / (math.pi * diameter_m)


# --- pressure drop, assembled at a boundary that enforces ------------------------


# --- hydraulic state DERIVED from bore (OTB-G002 F-01) ---------------------------


@dataclass(frozen=True)
class HydraulicState:
    """The hydraulic state a bore implies, derived rather than supplied.

    OTB-G002 **F-01**: the sweep previously took mass flux and both phase-alone
    gradients as scalars *outside* the diameter loop and passed them unchanged at every
    point. Mass flux is ``m_dot / (pi D^2 / 4)``, so it moves with bore by construction
    -- a factor of 683 across the adopted 1.224-32 mm band at a fixed 0.01 kg/s -- and
    Reynolds number, both phase-alone gradients, the Martinelli parameter and the whole
    acceleration term follow from it. Held constant, friction varied only through length
    and acceleration did not vary with bore at all.
    """

    diameter_m: float
    mass_flux_kg_m2s: float
    quality: float
    reynolds_liquid: float
    reynolds_gas: float
    liquid_regime: str
    gas_regime: str
    dp_dz_liquid_Pa_m: float
    dp_dz_gas_Pa_m: float


#: Liquid/gas regime boundary, reusing Stage-1's own laminar threshold so the two stages
#: classify flow regime by one convention rather than two.
_LAMINAR_RE_MAX = 2300.0


def _regime(reynolds: float) -> str:
    return "laminar" if reynolds <= _LAMINAR_RE_MAX else "turbulent"


def hydraulic_state_from_bore(
    *,
    mass_flow_kg_s: float,
    diameter_m: float,
    quality: float,
    rho_f: float,
    rho_g: float,
    mu_f: float,
    mu_g: float,
    rel_roughness: float = 0.0,
) -> HydraulicState:
    """Derive the whole hydraulic state from the bore and the mass flow.

    Each phase is taken to flow **alone** in the channel at its own mass flow, which is
    the Lockhart-Martinelli postulate (Collier & Thome Sec. 2.4.3(a)): the phase-alone
    frictional gradients are ``f rho v^2 / (2 D)`` with ``f`` from Stage-1's own
    single-phase friction machinery, and the **flow regimes are computed from Reynolds
    number, never declared** (F-02).

    **A named modelling difference.** The source's own basis is a Blasius-type friction
    factor (its Eq. 2.60, ``f = K (rho u D / mu)^-n``); Stage 1 uses ``64/Re`` in laminar
    flow and Haaland in turbulent. Measured against Blasius over its declared 4e3-1e5
    window the two agree to **0.3-2.3 %**, and reusing Stage-1's machinery keeps one
    friction convention across the project rather than two. Recorded rather than
    silently substituted.
    """
    from . import pumped_loop as _pl

    _validate_hydraulic_inputs(
        mass_flow_kg_s=mass_flow_kg_s,
        diameter_m=diameter_m,
        rho_f=rho_f,
        rho_g=rho_g,
        mu_f=mu_f,
        mu_g=mu_g,
        quality=quality,
        rel_roughness=rel_roughness,
    )

    area_m2 = math.pi * diameter_m**2 / 4.0
    mass_flux = mass_flow_kg_s / area_m2

    # Each phase flowing alone, at its own share of the mass flux.
    g_f, g_g = mass_flux * (1.0 - quality), mass_flux * quality
    if g_f <= 0.0 or g_g <= 0.0:
        raise ValueError(
            f"quality {quality} leaves one phase with no mass flow, so the "
            "Lockhart-Martinelli 'each phase flowing alone' construction has no "
            "meaning; the two-phase multiplier is undefined at x = 0 and x = 1"
        )

    re_f, re_g = g_f * diameter_m / mu_f, g_g * diameter_m / mu_g
    f_f = _pl.friction_factor(re_f, rel_roughness)
    f_g = _pl.friction_factor(re_g, rel_roughness)
    v_f, v_g = g_f / rho_f, g_g / rho_g

    return HydraulicState(
        diameter_m=diameter_m,
        mass_flux_kg_m2s=mass_flux,
        quality=quality,
        reynolds_liquid=re_f,
        reynolds_gas=re_g,
        liquid_regime=_regime(re_f),
        gas_regime=_regime(re_g),
        dp_dz_liquid_Pa_m=f_f * rho_f * v_f**2 / (2.0 * diameter_m),
        dp_dz_gas_Pa_m=f_g * rho_g * v_g**2 / (2.0 * diameter_m),
    )


#: Inputs that may legitimately be zero, and (``height_m``) negative -- a loop leg can
#: descend. They still have to be numbers.
_NONNEGATIVE_INPUTS = frozenset({"rel_roughness"})
_SIGNED_INPUTS = frozenset({"height_m"})


def _validate_hydraulic_inputs(**values: float) -> None:
    """Reject non-finite and non-physical hydraulic inputs (OTB-G002 F-04).

    NaN comparisons are always false, so ``> 0`` guards passed NaN straight through and
    the boundary returned ``total_Pa = nan`` marked applicable. Finiteness is therefore
    checked **explicitly** -- a sign test does not exclude NaN -- and quality is bounded
    to ``[0, 1]`` because it is a mass fraction.

    **Every** hydraulic entry point validates through here. The first version of this fix
    left ``hydraulic_state_from_bore`` and ``two_phase_pressure_drop`` validating the same
    inputs independently, which the witness harness caught: breaking one guard left two
    others standing, so no mutation could show any single one was load-bearing. Three
    copies of a check is the per-instance pattern C9 forbids, and an unwitnessable check
    is the symptom of it.
    """
    for name, value in values.items():
        if name.startswith("quality"):
            _v.in_range(name, value, 0.0, 1.0)
        elif name in _SIGNED_INPUTS:
            _v.finite(name, value)
        elif name in _NONNEGATIVE_INPUTS:
            _v.nonneg(name, value)
        else:
            _v.positive(name, value)


# --- C11(i): what this boundary collapses, declared where it collapses it ----------

#: The pressure-drop boundary's terms and what each throws away.
#:
#: Both collapsing terms are here, not just the one a finding named. ``x_mean`` reaches
#: the frictional term through the phase-alone gradients (``G_f = G(1-x)``,
#: ``G_g = Gx``) and the static term through the mixture density; a fix to one would
#: have left the other silently collapsing the same quantity, which is why C11 is a
#: standing rule rather than a patch.
#:
#: The acceleration term is deliberately listed with NO collapse. It takes the inlet
#: and outlet qualities as endpoints rather than a representative value, so it does not
#: collapse the profile -- and saying so is the difference between a swept model and an
#: unswept one. A term that collapses nothing is a result too.
PRESSURE_DROP_MODEL = CollapsedModel(
    model="S3 two-phase pressure drop (two_phase_pressure_drop)",
    terms=(
        ModelTerm(
            term="frictional",
            entry_id=DP_ID,
            collapses=(
                Collapse(
                    quantity="vapour quality profile along the channel",
                    representative_value="the section mean x_mean = (x_in + x_out)/2",
                    phenomena=(
                        "axial_profile",
                        "moving_boiling_boundary",
                        "negative_slope_segment",
                    ),
                    basis=(
                        "two_phase_pressure_drop evaluates the Lockhart-Martinelli "
                        "multiplier ONCE, at x_mean, and scales it by length_m rather "
                        "than integrating along the channel (the source integrates, "
                        "its Eq. 2.54). The correlation itself is local in x; the "
                        "collapse is this boundary's screening simplification. With no "
                        "axial profile there is no travelling saturation point, and "
                        "without that the internal characteristic cannot acquire the "
                        "negatively-sloped segment a flow excursion needs."
                    ),
                ),
            ),
        ),
        ModelTerm(
            term="static",
            collapses=(
                Collapse(
                    quantity="mixture density along the channel",
                    representative_value="the homogeneous density at x_mean",
                    phenomena=("axial_profile",),
                    basis=(
                        "static_pressure_drop is given one mixture density computed at "
                        "x_mean, so the head is a single rho*g*h rather than an "
                        "integral of a varying column. Named by C11 alongside the "
                        "frictional term: a friction-only fix would have left this "
                        "collapsing the same quantity untouched."
                    ),
                ),
            ),
        ),
        ModelTerm(term="accelerational", collapses=()),
    ),
)


@dataclass(frozen=True)
class PressureDropResult:
    """Total two-phase pressure drop, its components, and its applicability verdict."""

    total_Pa: float
    frictional_Pa: float
    accelerational_Pa: float
    static_Pa: float
    violations: tuple[Violation, ...] = ()
    caveats: tuple[str, ...] = ()
    #: The state the bore implied. Carried so a sweep can show that its hydraulics
    #: actually moved -- the absence of which was F-01.
    hydraulics: HydraulicState | None = None

    @property
    def is_applicable(self) -> bool:
        """True only when no declared applicability axis was violated.

        For this project's loop this is **always False**: the frictional correlation is
        declared for horizontal two-component flow and the loop is neither.
        """
        return not self.violations


def two_phase_pressure_drop(
    *,
    mass_flow_kg_s: float,
    diameter_m: float,
    length_m: float,
    quality_in: float,
    quality_out: float,
    rho_f: float,
    rho_g: float,
    mu_f: float,
    mu_g: float,
    pressure_Pa: float,
    composition: str,
    geometry_shape: str,
    orientation: str,
    fluid: str | None = None,
    height_m: float = 0.0,
    gravity_m_s2: float = STANDARD_GRAVITY_M_S2,
    rel_roughness: float = 0.0,
) -> PressureDropResult:
    """Frictional + acceleration + static pressure drop, with enforcement.

    **This is the boundary.** The frictional correlation's declared applicability is
    checked here, not by whichever caller remembers to; the result carries the
    violations rather than a naked float, so a caller cannot use the number without
    also receiving the verdict on it.

    ``BLOCK``/``REJECT`` raise. ``DE_RANK`` returns with violations attached — the same
    split as :func:`orbital_thermal.two_phase.flow_boiling_htc`, and for the same
    reason: a de-ranked case must remain reportable as a sensitivity.

    The **static** term is computed, not dropped (ruling D12). At ``g <= 0`` the static
    helper refuses rather than silently contributing zero, because summing a
    microgravity-exact term with a 1g-derived frictional one is the seam the ruling
    exists to prevent.
    """
    entry = get(DP_ID)
    spec = entry.applicability_spec

    # F-04: finiteness and physicality FIRST, before anything can produce a number.
    _validate_hydraulic_inputs(
        mass_flow_kg_s=mass_flow_kg_s,
        diameter_m=diameter_m,
        length_m=length_m,
        rho_f=rho_f,
        rho_g=rho_g,
        mu_f=mu_f,
        mu_g=mu_g,
        pressure_Pa=pressure_Pa,
        quality_in=quality_in,
        quality_out=quality_out,
        height_m=height_m,
        gravity_m_s2=gravity_m_s2,
    )

    assert_in_domain(entry, context="S3 two-phase pressure drop", P_Pa=pressure_Pa)

    # F-01/F-02: the hydraulic state and both flow regimes are DERIVED from the bore.
    # The frictional multiplier is local in x; it is evaluated at the section's mean
    # quality rather than integrated over it (the source integrates, its Eq. 2.54) --
    # a stated screening simplification, consistent with the acceleration term.
    x_mean = 0.5 * (quality_in + quality_out)
    hydraulics = hydraulic_state_from_bore(
        mass_flow_kg_s=mass_flow_kg_s,
        diameter_m=diameter_m,
        quality=x_mean,
        rho_f=rho_f,
        rho_g=rho_g,
        mu_f=mu_f,
        mu_g=mu_g,
        rel_roughness=rel_roughness,
    )

    violations: tuple[Violation, ...] = ()
    if spec is not None:
        violations = spec.check(
            composition=composition,
            geometry=geometry_shape,
            orientation=orientation,
            gravity_m_s2=gravity_m_s2,
            has_executable_form=entry.has_executable_form,
        )
    # F-02: the declarations that cannot be derived are cross-checked against each
    # other, so they are not independently assertable.
    violations = violations + case_contradictions(
        fluid=fluid,
        composition=composition,
        orientation=orientation,
        height_m=height_m,
        single_component_fluids=REGISTERED_SINGLE_COMPONENT_FLUIDS,
    )

    blocking = [
        v for v in violations if v.consequence in (Consequence.BLOCK, Consequence.REJECT)
    ]
    if blocking:
        raise NotRankEligibleError(
            f"'{entry.id}' is not applicable to this case: "
            + "; ".join(str(v) for v in blocking)
        )

    frictional = (
        lockhart_martinelli_frictional_gradient(
            dp_dz_liquid=hydraulics.dp_dz_liquid_Pa_m,
            dp_dz_gas=hydraulics.dp_dz_gas_Pa_m,
            liquid_regime=hydraulics.liquid_regime,
            gas_regime=hydraulics.gas_regime,
        )
        * length_m
    )
    accel = accelerational_pressure_drop(
        mass_flux_kg_m2s=hydraulics.mass_flux_kg_m2s,
        quality_in=quality_in,
        quality_out=quality_out,
        rho_f=rho_f,
        rho_g=rho_g,
    )
    # Mixture density in the homogeneous limit, consistent with the acceleration term.
    rho_mix = 1.0 / (x_mean / rho_g + (1.0 - x_mean) / rho_f)
    static = static_pressure_drop(
        rho_mixture_kg_m3=rho_mix, height_m=height_m, gravity_m_s2=gravity_m_s2
    )

    return PressureDropResult(
        total_Pa=frictional + accel + static,
        frictional_Pa=frictional,
        accelerational_Pa=accel,
        static_Pa=static,
        violations=violations,
        caveats=spec.provenance_caveats() if spec is not None else (),
        hydraulics=hydraulics,
    )


# --- the condenser as an ENERGY BOUNDARY (ruling D10) ----------------------------


@dataclass(frozen=True)
class CondenserBoundary:
    """Condenser energy bookkeeping — heat out and state change, nothing more.

    **No condensation heat-transfer coefficient is computed here, and none may be
    claimed** (Director ruling D10). Condensation is a different physics family from
    boiling, the registry contains no condensation entry of any kind, and the gap is
    recorded as DEBTS D-11 and scoped to S4. Anything that would need a condensation
    coefficient — a condenser area, a wall temperature, a UA — is **blocked, not
    estimated**, and :meth:`required_area_m2` says so rather than returning a number.
    """

    duty_W: float
    h_in_J_kg: float
    h_out_J_kg: float
    mass_flow_kg_s: float
    sink_temperature_K: float
    saturation_temperature_K: float
    outlet_is_liquid: bool

    @property
    def energy_closes(self) -> bool:
        """Whether the stated duty matches the enthalpy drop it claims."""
        return abs(
            self.mass_flow_kg_s * (self.h_in_J_kg - self.h_out_J_kg) - self.duty_W
        ) <= 1e-6 * max(abs(self.duty_W), 1.0)

    @property
    def rejects_to_a_colder_sink(self) -> bool:
        """Heat only flows out if the sink is colder than the condensing fluid."""
        return self.sink_temperature_K < self.saturation_temperature_K

    def required_area_m2(self) -> float:
        """Always raises — sizing the condenser needs a condensation coefficient.

        Deliberately a raising method rather than an absent one: a caller that needs an
        area gets a machine-visible blocker naming the debt, instead of an
        ``AttributeError`` or, far worse, a plausible number.
        """
        raise NotRankEligibleError(
            "condenser area cannot be computed at S3: it needs a condensation "
            "heat-transfer coefficient, the registry contains no condensation entry of "
            "any kind, and Director ruling D10 makes the condenser an ENERGY BOUNDARY "
            "at this milestone with condensation deferred to S4 (DEBTS D-11). No "
            "coefficient is estimated here."
        )


def condenser_energy_boundary(
    *,
    mass_flow_kg_s: float,
    h_in_J_kg: float,
    h_out_J_kg: float,
    sink_temperature_K: float,
    saturation_temperature_K: float,
    outlet_is_liquid: bool,
) -> CondenserBoundary:
    """Close the condenser's energy books against the A3 fixed effective sink."""
    _v.positive("mass_flow_kg_s", mass_flow_kg_s)
    _v.positive("sink_temperature_K", sink_temperature_K)
    _v.positive("saturation_temperature_K", saturation_temperature_K)
    if h_out_J_kg >= h_in_J_kg:
        raise ValueError(
            f"a condenser removes heat, so h_out ({h_out_J_kg}) must be below h_in "
            f"({h_in_J_kg})"
        )
    return CondenserBoundary(
        duty_W=mass_flow_kg_s * (h_in_J_kg - h_out_J_kg),
        h_in_J_kg=h_in_J_kg,
        h_out_J_kg=h_out_J_kg,
        mass_flow_kg_s=mass_flow_kg_s,
        sink_temperature_K=sink_temperature_K,
        saturation_temperature_K=saturation_temperature_K,
        outlet_is_liquid=outlet_is_liquid,
    )


# --- pump-inlet feasibility (ruling D8) ------------------------------------------


@dataclass(frozen=True)
class PumpInletFeasibility:
    """Whether the pump is fed liquid, by the AMS-02 subcooling criterion."""

    subcooling_margin_K: float
    inlet_is_liquid: bool
    feasible: bool
    reason: str


def pump_inlet_feasibility(
    *,
    saturation_temperature_K: float,
    inlet_temperature_K: float,
    inlet_is_liquid: bool,
    required_margin_K: float = 0.0,
) -> PumpInletFeasibility:
    """Assess pump-inlet feasibility as a **subcooling margin** (ruling D8).

    ``required_margin_K`` defaults to 0 — bare saturation. It is exposed so a caller
    can demand a real margin, but **no non-zero default is invented**: the AMS-02
    precedent establishes the *criterion* ("sub-cooled well below the saturation
    point"), not a number, and choosing one here would be exactly the guess C1 forbids.

    This is feasibility, not pump selection. The quantitative NPSHA/NPSH3 route is
    recorded on the registry entry and not implemented, together with the warning that
    ``NPSHA = NPSHR`` is the onset of damage rather than a safe point.
    """
    _v.nonneg("required_margin_K", required_margin_K)
    margin = pump_inlet_subcooling_margin(
        saturation_temperature_K=saturation_temperature_K,
        inlet_temperature_K=inlet_temperature_K,
    )
    if not inlet_is_liquid:
        return PumpInletFeasibility(
            subcooling_margin_K=margin,
            inlet_is_liquid=False,
            feasible=False,
            reason=(
                "the inlet state is not liquid: incomplete condensation feeds vapour to "
                "the pump, which the AMS-02 criterion exists to exclude"
            ),
        )
    if margin <= required_margin_K:
        return PumpInletFeasibility(
            subcooling_margin_K=margin,
            inlet_is_liquid=True,
            feasible=False,
            reason=(
                f"subcooling margin {margin:.4g} K does not exceed the required "
                f"{required_margin_K:.4g} K: the inlet is at or past saturation, which "
                "is the cavitation condition"
            ),
        )
    return PumpInletFeasibility(
        subcooling_margin_K=margin,
        inlet_is_liquid=True,
        feasible=True,
        reason=(
            f"inlet is liquid and subcooled by {margin:.4g} K, so the pump is fed "
            "liquid (AMS-02 criterion, Director ruling D8)"
        ),
    )


# --- the bore sweep (ruling D11) -------------------------------------------------


@dataclass(frozen=True)
class BorePoint:
    """One bore evaluated in the sweep."""

    diameter_m: float
    required_length_m: float
    pressure_drop: PressureDropResult | None
    blocked_reason: str = ""
    #: The mass flux this bore implied, surfaced on the point itself so a sweep is
    #: self-evidencing: whether its hydraulics actually moved across bore is readable
    #: without reaching into the nested result. F-01 was precisely the case where they
    #: did not, and nothing in the output would have shown it.
    mass_flux_kg_m2s: float | None = None

    @property
    def evaluated(self) -> bool:
        return self.pressure_drop is not None


@dataclass(frozen=True)
class BoreSweep:
    """The sweep result, carrying the band's provenance into the output."""

    band: BoreBand
    points: tuple[BorePoint, ...]
    provenance_label: str
    caveats: tuple[str, ...] = field(default_factory=tuple)

    @property
    def any_applicable(self) -> bool:
        return any(p.evaluated and p.pressure_drop.is_applicable for p in self.points)

    def summary(self) -> str:
        """A reportable summary that **carries the provenance label in the output**.

        Ruling D11 requires the provenance-unestablished label to appear in the
        reported result, not in a comment, so it is rendered here rather than left for
        a reader to look up.
        """
        head = (
            f"bore sweep over [{self.band.min_m * 1e3:.3f}, {self.band.max_m * 1e3:.3f}] mm "
            f"({len(self.points)} points), band bound by '{self.band.binding_entry_id}'"
        )
        lines = [head, self.provenance_label]
        if not self.any_applicable:
            lines.append(
                "NEGATIVE RESULT: no bore in the band produces an applicable pressure "
                "drop. That is the bound this sweep reports; the band is not widened "
                "until something passes (Director ruling D7)."
            )
        lines.extend(f"  - {c}" for c in self.caveats)
        return "\n".join(lines)


def sweep_bore(
    *,
    diameters_m: tuple[float, ...],
    duty_W: float,
    mass_flow_kg_s: float,
    h_in_J_kg: float,
    h_out_J_kg: float,
    wall_flux_W_m2: float,
    quality_in: float,
    quality_out: float,
    rho_f: float,
    rho_g: float,
    mu_f: float,
    mu_g: float,
    pressure_Pa: float,
    composition: str,
    geometry_shape: str,
    orientation: str,
    fluid: str | None = None,
    height_m: float = 0.0,
    gravity_m_s2: float = STANDARD_GRAVITY_M_S2,
    rel_roughness: float = 0.0,
) -> BoreSweep:
    """Sweep bore across the registry-derived band, deriving length at each point.

    **Bore is the one free parameter; length is computed from the duty** (ruling D11).
    The question the sweep answers is: at what bore does the required length produce a
    pressure drop that breaks the temperature budget?

    A bore outside the band, or one whose evaluation is refused, is recorded as a
    blocked point rather than dropped — **a negative result is a result** (ruling D7),
    and a sweep that silently omitted its failures could not report one.
    """
    band = bore_band()
    points: list[BorePoint] = []

    for d in diameters_m:
        if not band.contains(d):
            points.append(
                BorePoint(
                    diameter_m=d,
                    required_length_m=float("nan"),
                    pressure_drop=None,
                    blocked_reason=(
                        f"bore {d * 1e3:.3f} mm is outside the registry-derived band "
                        f"[{band.min_m * 1e3:.3f}, {band.max_m * 1e3:.3f}] mm"
                    ),
                )
            )
            continue

        length = required_length_m(
            duty_W=duty_W,
            mass_flow_kg_s=mass_flow_kg_s,
            h_in_J_kg=h_in_J_kg,
            h_out_J_kg=h_out_J_kg,
            diameter_m=d,
            wall_flux_W_m2=wall_flux_W_m2,
        )
        try:
            dp = two_phase_pressure_drop(
                mass_flow_kg_s=mass_flow_kg_s,
                diameter_m=d,
                length_m=length,
                quality_in=quality_in,
                quality_out=quality_out,
                rho_f=rho_f,
                rho_g=rho_g,
                mu_f=mu_f,
                mu_g=mu_g,
                pressure_Pa=pressure_Pa,
                composition=composition,
                geometry_shape=geometry_shape,
                orientation=orientation,
                fluid=fluid,
                height_m=height_m,
                gravity_m_s2=gravity_m_s2,
                rel_roughness=rel_roughness,
            )
            points.append(
                BorePoint(
                    diameter_m=d,
                    required_length_m=length,
                    pressure_drop=dp,
                    mass_flux_kg_m2s=dp.hydraulics.mass_flux_kg_m2s
                    if dp.hydraulics is not None
                    else None,
                )
            )
        except NotRankEligibleError as exc:
            points.append(
                BorePoint(
                    diameter_m=d,
                    required_length_m=length,
                    pressure_drop=None,
                    blocked_reason=str(exc),
                    mass_flux_kg_m2s=mass_flow_kg_s / (math.pi * d * d / 4.0),
                )
            )

    caveats: tuple[str, ...] = ()
    for p in points:
        if p.evaluated:
            caveats = p.pressure_drop.caveats
            break

    return BoreSweep(
        band=band,
        points=tuple(points),
        provenance_label=band.provenance_label,
        caveats=caveats,
    )


__all__ = [
    "CHF_ID",
    "DP_ID",
    "HTC_ID",
    "NPSH_ID",
    "REGISTERED_SINGLE_COMPONENT_FLUIDS",
    "HydraulicState",
    "hydraulic_state_from_bore",
    "BoreBand",
    "BorePoint",
    "BoreSweep",
    "CondenserBoundary",
    "PressureDropResult",
    "PumpInletFeasibility",
    "bore_band",
    "condenser_energy_boundary",
    "pump_inlet_feasibility",
    "required_length_m",
    "sweep_bore",
    "two_phase_pressure_drop",
]
