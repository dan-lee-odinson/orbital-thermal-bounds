"""B3: single-phase pumped-loop hydraulics, thermics, and pump energy.

Closes the junction-to-fluid path from B2 via the convective film resistance, and
computes loop pressure drop, pump power/heat, and per-segment single-phase margins.
Consumes the B1 correlation registry (friction, Nusselt) and the coolant property
backend (per-state CoolProp evaluation via :mod:`orbital_thermal.fluids`; the B1
reference literals are cross-check anchors only).

Design (B3 scoping):
- **pump heat** -- hydraulic dissipation heats the loop; ``f`` and the control-volume
  boundary are explicit (B0 plan 4.7);
- **correlations** -- auto by Reynolds: laminar (Re <= 2300) ``f = 64/Re`` and
  ``Nu = 4.36`` (uniform flux) / ``3.66`` (uniform Ts); turbulent Gnielinski Nu +
  Haaland friction; the transition band is blended and warned;
- **discretization** -- a configurable N-segment march with per-segment freeze /
  saturation / critical margins that fail loudly.

The pure hydraulics/thermics functions take properties as arguments (numpy/stdlib
only). The coolant-aware loop march evaluates properties via CoolProp. Units: SI --
pressures Pa, temperatures K, resistances K/W.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass

from . import registry
from ._validate import nonneg, positive, positive_int
from .registry.correlations import friction_haaland, friction_laminar, nusselt_gnielinski

_LAMINAR_RE = 2300.0
_TURBULENT_RE_FRICTION = 4000.0
_TURBULENT_RE_NUSSELT = 3000.0


# --- hydraulics -----------------------------------------------------------------


def flow_area(diameter_m: float) -> float:
    """Circular cross-sectional area, m^2."""
    positive("diameter_m", diameter_m)
    return math.pi * diameter_m**2 / 4.0


def velocity(mass_flow_kg_s: float, density_kg_m3: float, area_m2: float) -> float:
    """Mean velocity ``v = m_dot / (rho A)``, m/s."""
    positive("mass_flow_kg_s", mass_flow_kg_s)
    positive("density_kg_m3", density_kg_m3)
    positive("area_m2", area_m2)
    return mass_flow_kg_s / (density_kg_m3 * area_m2)


def reynolds(
    mass_flow_kg_s: float, diameter_m: float, viscosity_Pa_s: float, area_m2: float | None = None
) -> float:
    """Reynolds number ``Re = m_dot D / (A mu)`` (= 4 m_dot / (pi D mu) for a circular tube)."""
    positive("mass_flow_kg_s", mass_flow_kg_s)
    positive("diameter_m", diameter_m)
    positive("viscosity_Pa_s", viscosity_Pa_s)
    if area_m2 is None:
        area_m2 = flow_area(diameter_m)
    return mass_flow_kg_s * diameter_m / (area_m2 * viscosity_Pa_s)


def friction_factor(reynolds_number: float, rel_roughness: float = 0.0) -> float:
    """Darcy friction factor, auto by regime (laminar / transition / turbulent)."""
    positive("reynolds_number", reynolds_number)
    nonneg("rel_roughness", rel_roughness)
    if reynolds_number <= _LAMINAR_RE:
        return friction_laminar(reynolds_number)
    if reynolds_number >= _TURBULENT_RE_FRICTION:
        return friction_haaland(reynolds_number, rel_roughness)
    warnings.warn(
        f"transitional flow (Re={reynolds_number:.0f}); friction factor is a laminar/turbulent "
        "blend and is approximate",
        RuntimeWarning,
        stacklevel=2,
    )
    f_lam = friction_laminar(_LAMINAR_RE)
    f_turb = friction_haaland(_TURBULENT_RE_FRICTION, rel_roughness)
    w = (reynolds_number - _LAMINAR_RE) / (_TURBULENT_RE_FRICTION - _LAMINAR_RE)
    return f_lam * (1.0 - w) + f_turb * w


def pressure_drop(
    friction: float,
    length_m: float,
    diameter_m: float,
    density_kg_m3: float,
    velocity_m_s: float,
    minor_loss_K: float = 0.0,
) -> float:
    """``dP = (f L/D + sum K) * rho v^2 / 2`` [Pa] (major + minor losses)."""
    positive("friction", friction)
    positive("length_m", length_m)
    positive("diameter_m", diameter_m)
    positive("density_kg_m3", density_kg_m3)
    nonneg("velocity_m_s", velocity_m_s)
    nonneg("minor_loss_K", minor_loss_K)
    dyn = 0.5 * density_kg_m3 * velocity_m_s**2
    return (friction * length_m / diameter_m + minor_loss_K) * dyn


# --- pump energy (hydraulic-into-fluid; B0 plan 4.7) ----------------------------


@dataclass(frozen=True)
class PumpEnergy:
    """Pump-energy accounting for the coupled solve's energy balance (B4)."""

    hydraulic_power_W: float
    electrical_power_W: float
    fluid_heat_W: float  # deposited in the coolant loop
    other_heat_W: float  # motor/electronics losses (rejected elsewhere unless whole-spacecraft)
    deposition_fraction: float  # f = fluid_heat / electrical
    boundary: str


def pump_energy(
    mass_flow_kg_s: float,
    pressure_drop_Pa: float,
    density_kg_m3: float,
    *,
    eta_pump: float = 0.70,
    eta_motor: float = 0.90,
    boundary: str = "fluid_loop",
) -> PumpEnergy:
    """Hydraulic-into-fluid pump-energy accounting.

    ``P_hyd = m_dot dP / rho`` heats the coolant; ``P_elec = P_hyd/(eta_pump eta_motor)``;
    motor/electronics losses (``P_elec - P_hyd``) go to ``other_heat`` (rejected elsewhere
    unless the whole-spacecraft boundary is chosen). ``f = fluid_heat / electrical``.
    """
    positive("mass_flow_kg_s", mass_flow_kg_s)
    nonneg("pressure_drop_Pa", pressure_drop_Pa)
    positive("density_kg_m3", density_kg_m3)
    if not (0.0 < eta_pump <= 1.0 and 0.0 < eta_motor <= 1.0):
        raise ValueError("efficiencies must be in (0, 1]")
    if boundary not in ("fluid_loop", "whole_spacecraft"):
        raise ValueError("boundary must be 'fluid_loop' or 'whole_spacecraft'")
    p_hyd = mass_flow_kg_s * pressure_drop_Pa / density_kg_m3
    p_elec = p_hyd / (eta_pump * eta_motor)
    fluid_heat = p_hyd
    other = p_elec - p_hyd
    f = fluid_heat / p_elec if p_elec > 0.0 else 0.0
    return PumpEnergy(p_hyd, p_elec, fluid_heat, other, f, boundary)


# --- thermics -------------------------------------------------------------------


def nusselt(reynolds_number: float, prandtl_number: float, *, uniform_flux: bool = True) -> float:
    """Nusselt number, auto by regime. Laminar: 4.36 (uniform flux) or 3.66 (uniform Ts);
    turbulent: Gnielinski; transition (2300 < Re < 3000) blended and warned."""
    positive("reynolds_number", reynolds_number)
    positive("prandtl_number", prandtl_number)
    nu_lam = 4.36 if uniform_flux else 3.66
    if reynolds_number <= _LAMINAR_RE:
        return nu_lam
    if reynolds_number >= _TURBULENT_RE_NUSSELT:
        return nusselt_gnielinski(reynolds_number, prandtl_number)
    warnings.warn(
        f"transitional flow (Re={reynolds_number:.0f}); Nusselt is a blend and is approximate",
        RuntimeWarning,
        stacklevel=2,
    )
    nu_turb = nusselt_gnielinski(_TURBULENT_RE_NUSSELT, prandtl_number)
    w = (reynolds_number - _LAMINAR_RE) / (_TURBULENT_RE_NUSSELT - _LAMINAR_RE)
    return nu_lam * (1.0 - w) + nu_turb * w


def heat_transfer_coefficient(
    nusselt_number: float, conductivity_W_mK: float, hydraulic_diameter_m: float
) -> float:
    """Convective coefficient ``h = Nu k / D_h``, W/m^2/K."""
    positive("nusselt_number", nusselt_number)
    positive("conductivity_W_mK", conductivity_W_mK)
    positive("hydraulic_diameter_m", hydraulic_diameter_m)
    return nusselt_number * conductivity_W_mK / hydraulic_diameter_m


def film_resistance(htc_W_m2K: float, wetted_area_m2: float) -> float:
    """Convective film resistance ``R = 1/(h A)`` [K/W] (closes the B2 wall-to-fluid leg)."""
    positive("htc_W_m2K", htc_W_m2K)
    positive("wetted_area_m2", wetted_area_m2)
    return 1.0 / (htc_W_m2K * wetted_area_m2)


# --- coolant-aware N-segment loop march (uses fluids / CoolProp) -----------------

_COOLANT_FLUID = {"ammonia": "Ammonia", "water": "Water"}


class LoopPhaseError(ValueError):
    """A loop segment violated a single-phase margin (freeze / saturation / critical)."""


def assert_loop_coolant_rankable(coolant: str) -> None:
    """A ranked loop must use a coolant whose per-state property backend is rank-eligible
    (ammonia/water). CO2 and PGW are blocked in the B1 registry."""
    if coolant not in _COOLANT_FLUID:
        raise registry.NotRankEligibleError(
            f"coolant '{coolant}' has no rank-eligible property backend (CO2/PGW are blocked, or "
            "the coolant is unknown). Run the case as a sensitivity."
        )
    registry.assert_rank_eligible(
        registry.get(f"coolant.{coolant}.property_backend"), context="B3 pumped loop"
    )


@dataclass(frozen=True)
class LoopResult:
    """Result of a single-phase loop march."""

    outlet_temperature_K: float
    outlet_pressure_Pa: float
    total_pressure_drop_Pa: float
    pump: PumpEnergy
    mean_htc_W_m2K: float
    min_freeze_margin_K: float
    min_subcooling_Pa: float
    min_critical_margin_K: float
    segments: int
    rank_eligible: bool


def march_single_phase_loop(
    *,
    coolant: str,
    mass_flow_kg_s: float,
    inlet_temperature_K: float,
    inlet_pressure_Pa: float,
    loop_length_m: float,
    diameter_m: float,
    heat_into_loop_W: float,
    minor_loss_K: float = 0.0,
    rel_roughness: float = 0.0,
    eta_pump: float = 0.70,
    eta_motor: float = 0.90,
    segments: int = 10,
    freeze_margin_K: float = 5.0,
    subcooling_margin_Pa: float = 1.0e4,
    ranked: bool = True,
) -> LoopResult:
    """March a single-phase liquid loop in ``segments`` steps, checking phase margins per
    segment. Properties are evaluated per-state via :mod:`orbital_thermal.fluids` (CoolProp).

    Heat is applied uniformly across segments; pressure drops down the flow path; each
    segment's ``(T, P)`` is checked for subcooling, freeze, and critical margins -- a
    violation raises :class:`LoopPhaseError`. Pump heat (hydraulic-into-fluid) is computed
    from the total ``dP`` and reported for the coupled solve to include (B4); it is not
    re-added to the per-segment heat here.
    """
    from . import fluids  # local import: CoolProp is optional at package level

    positive_int("segments", segments)
    positive("mass_flow_kg_s", mass_flow_kg_s)
    if ranked:
        assert_loop_coolant_rankable(coolant)
    fluid = _COOLANT_FLUID.get(coolant)
    if fluid is None:
        raise registry.NotRankEligibleError(f"unknown coolant '{coolant}'")

    area = flow_area(diameter_m)
    seg_len = loop_length_m / segments
    seg_minor_k = minor_loss_K / segments
    q_seg = heat_into_loop_W / segments
    temp, press = inlet_temperature_K, inlet_pressure_Pa
    total_dp = 0.0
    htc_sum = 0.0
    rho = fluids.density(temp, press, fluid)
    min_freeze = min_sub = min_crit = math.inf

    for _ in range(segments):
        props = fluids.transport_properties(temp, press, fluid)
        rho = props["density"]
        vel = velocity(mass_flow_kg_s, rho, area)
        re = reynolds(mass_flow_kg_s, diameter_m, props["dynamic_viscosity"], area)
        fric = friction_factor(re, rel_roughness)
        d_p = pressure_drop(fric, seg_len, diameter_m, rho, vel, seg_minor_k)
        nu = nusselt(re, props["prandtl"])
        htc_sum += heat_transfer_coefficient(nu, props["thermal_conductivity"], diameter_m)
        press = press - d_p
        total_dp += d_p
        temp = temp + q_seg / (mass_flow_kg_s * props["specific_heat"])
        margins = fluids.single_phase_liquid_margins(temp, max(press, 1.0), fluid)
        min_freeze = min(min_freeze, margins["freeze_margin_K"])
        min_sub = min(min_sub, margins["subcooling_Pa"])
        min_crit = min(min_crit, margins["critical_margin_K"])
        if (
            margins["freeze_margin_K"] < freeze_margin_K
            or margins["subcooling_Pa"] < subcooling_margin_Pa
            or margins["critical_margin_K"] <= 0.0
        ):
            raise LoopPhaseError(
                "single-phase margin violated in a loop segment: "
                f"freeze={margins['freeze_margin_K']:.1f} K, "
                f"subcooling={margins['subcooling_Pa']:.0f} Pa, "
                f"critical={margins['critical_margin_K']:.1f} K at T={temp:.1f} K, P={press:.0f} Pa"
            )

    pump = pump_energy(mass_flow_kg_s, total_dp, rho, eta_pump=eta_pump, eta_motor=eta_motor)
    return LoopResult(
        outlet_temperature_K=temp,
        outlet_pressure_Pa=press,
        total_pressure_drop_Pa=total_dp,
        pump=pump,
        mean_htc_W_m2K=htc_sum / segments,
        min_freeze_margin_K=min_freeze,
        min_subcooling_Pa=min_sub,
        min_critical_margin_K=min_crit,
        segments=segments,
        rank_eligible=ranked,
    )
