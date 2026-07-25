"""Executable thermophysical-property checks for the AI1 coolant screen.

Computes the ammonia properties that the companion paper ("The AI1 Design
Point", doi:10.5281/zenodo.20670771) quotes as NIST Chemistry WebBook
reference values: critical point, saturation pressures at the modeled
radiator-surface temperatures, and phase state. With this module the
properties are CALCULATED rather than transcribed, upgrading the paper's
verification scope (its Option B exclusion) to executable form.

Backend: CoolProp HEOS (Helmholtz-energy equation of state). Use
:func:`provenance` to record the exact CoolProp version and the underlying
EOS citation next to any generated table; property values are only
reproducible against a pinned version.

This module is intentionally NOT imported by ``orbital_thermal/__init__``:
CoolProp is an optional dependency, and importing the core package must not
require it. Import explicitly::

    from orbital_thermal import fluids

Scope limit (companion paper, Phase 3 plan): property calculations verify
thermodynamic consistency only. They establish nothing about component
pressure ratings, pump feasibility, seal compatibility, or reliability.

Units: SI (kelvin, pascal, kg/m^3). ``PA_PER_BAR`` converts for display.
"""

try:
    import CoolProp
    from CoolProp.CoolProp import PhaseSI, PropsSI, get_BibTeXKey
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "orbital_thermal.fluids requires CoolProp. "
        'Install it with: pip install "orbital-thermal[fluids]" '
        "or: pip install CoolProp"
    ) from exc

from . import _validate as _v
from .registry.two_phase import TWO_PHASE_PROPERTIES as _TWO_PHASE_PROPERTIES

#: Pascals per bar.
PA_PER_BAR: float = 1e5

#: Default working fluid for the AI1 coolant screen.
DEFAULT_FLUID: str = "Ammonia"


def critical_temperature(fluid: str = DEFAULT_FLUID) -> float:
    """Critical temperature, K. Paper's NIST anchor for ammonia: 405.5 K."""
    return PropsSI("Tcrit", fluid)


def critical_pressure(fluid: str = DEFAULT_FLUID) -> float:
    """Critical pressure, Pa. Paper's NIST anchor for ammonia: ~113 bar."""
    return PropsSI("pcrit", fluid)


def saturation_pressure(T: float, fluid: str = DEFAULT_FLUID) -> float:
    """Saturation (vapor) pressure at temperature ``T``, in Pa.

    This is the lower bound on loop pressure for keeping the coolant
    liquid at the radiator-surface temperature -- the quantity behind the
    paper's 41.4 / 46.8 / 63.8 / 88.4 bar ladder.

    Raises ValueError above the critical temperature, where a saturation
    curve no longer exists.
    """
    _v.positive("T", T)
    T_crit = critical_temperature(fluid)
    if T >= T_crit:
        raise ValueError(
            f"T = {T} K is at or above the critical temperature of "
            f"{fluid} ({T_crit:.2f} K); no saturation pressure exists"
        )
    return PropsSI("P", "T", T, "Q", 0.0, fluid)


def phase_state(T: float, P: float, fluid: str = DEFAULT_FLUID) -> str:
    """CoolProp phase label at (``T`` K, ``P`` Pa).

    Typical labels: 'liquid', 'gas', 'supercritical', 'supercritical_gas',
    'supercritical_liquid', 'twophase'.
    """
    _v.positive("T", T)
    _v.positive("P", P)
    return PhaseSI("T", T, "P", P, fluid)


def critical_margin(T: float, fluid: str = DEFAULT_FLUID) -> float:
    """Temperature headroom to the critical point: T_crit - T, in K.

    Positive means a subcritical liquid loop is possible at sufficient
    pressure; negative means no liquid phase exists at any pressure. The
    paper's screen: >50 K margin for the two-sided readings, <14 K for
    one-sided sustained, negative for one-sided continuous-peak.
    """
    _v.finite("T", T)
    return critical_temperature(fluid) - T


def saturated_densities(
    T: float, fluid: str = DEFAULT_FLUID
) -> tuple[float, float]:
    """(liquid, vapor) densities on the saturation curve at ``T``, kg/m^3.

    Raises ValueError for non-finite/non-positive ``T`` and at or above the
    critical temperature, where the saturation curve no longer exists (audit r8 P3)."""
    _v.positive("T", T)
    T_crit = critical_temperature(fluid)
    if T >= T_crit:
        raise ValueError(
            f"T = {T} K is at or above the critical temperature of "
            f"{fluid} ({T_crit:.2f} K); no saturation densities exist"
        )
    rho_liq = PropsSI("D", "T", T, "Q", 0.0, fluid)
    rho_vap = PropsSI("D", "T", T, "Q", 1.0, fluid)
    return rho_liq, rho_vap


# --- S2 two-phase saturation backend (Stage 2, milestone S2) --------------------
# The saturation properties the flow-boiling evaporator needs, evaluated on the
# pinned CoolProp HEOS backend named by ``registry.two_phase.COOLPROP_PIN``.
#
# Every call is guarded twice:
#
# 1. against the **declared** validity domain of the corresponding
#    ``TWO_PHASE_PROPERTIES`` registry entry (ammonia 195.5-405.4 K, water
#    273.16-647.1 K), so a two-phase call cannot silently leave the registered
#    domain; and
# 2. against the **actual** backend triple/critical bounds, so no call can be
#    evaluated at or above the critical point even where the declared domain
#    nominally permits it (the declared water upper bound 647.1 K sits a few
#    millikelvin above the CoolProp critical temperature 647.096 K).
#
# A coolant with no ``TWO_PHASE_PROPERTIES`` entry is **source-gated** and raises:
# S0 Section 9.1 admits ammonia (reference) and water (secondary) only, and an
# unregistered coolant has no sourced saturation domain to evaluate against.

#: Declared two-phase saturation domains, keyed by lowercased fluid name. Read from
#: the registry rather than restated, so the domain has exactly one definition.
_SAT_T_DOMAIN_K: dict[str, tuple[float, float]] = {
    e.material.lower(): e.domain.ranges["T_K"]
    for e in _TWO_PHASE_PROPERTIES
    if "T_K" in e.domain.ranges
}


class SourceGatedFluidError(ValueError):
    """Raised for a two-phase saturation call on a coolant with no registry entry.

    Not an invented default: S0 Section 9.1 admits ammonia (reference) and water
    (secondary); every other coolant is source-gated until a registry entry with a
    sourced validity domain exists.
    """


def two_phase_domain_K(fluid: str = DEFAULT_FLUID) -> tuple[float, float]:
    """Declared two-phase saturation temperature domain ``(T_min, T_max)`` in K.

    Raises :class:`SourceGatedFluidError` for a coolant with no registry entry.
    """
    key = fluid.strip().lower()
    if key not in _SAT_T_DOMAIN_K:
        allowed = ", ".join(sorted(_SAT_T_DOMAIN_K))
        raise SourceGatedFluidError(
            f"two-phase saturation properties for '{fluid}' are source-gated: no "
            f"registry entry declares a validity domain for it. Registered "
            f"two-phase coolants: {allowed}. Add a sourced "
            "TWO_PHASE_PROPERTIES entry before evaluating it (no-invention policy)."
        )
    return _SAT_T_DOMAIN_K[key]


def assert_two_phase_domain(T: float, fluid: str = DEFAULT_FLUID) -> None:
    """Raise unless ``T`` is inside both the declared domain and the real
    triple/critical bounds of ``fluid``. Never silently extrapolated."""
    _v.positive("T", T)
    lo, hi = two_phase_domain_K(fluid)
    if not (lo <= T <= hi):
        raise ValueError(
            f"T = {T} K is outside the declared two-phase domain of {fluid} "
            f"[{lo}, {hi}] K; the case is out of domain, not extrapolated"
        )
    t_crit = critical_temperature(fluid)
    t_triple = triple_temperature(fluid)
    if T >= t_crit:
        raise ValueError(
            f"T = {T} K is at or above the critical temperature of {fluid} "
            f"({t_crit:.3f} K); no saturation state exists (no blanket "
            "supercritical treatment)"
        )
    if T < t_triple:
        raise ValueError(
            f"T = {T} K is below the triple-point temperature of {fluid} "
            f"({t_triple:.3f} K); no saturation state exists"
        )


def triple_pressure(fluid: str = DEFAULT_FLUID) -> float:
    """Triple-point pressure, Pa (lower bound of the saturation curve)."""
    return PropsSI("p_triple", fluid)


def saturation_temperature(P: float, fluid: str = DEFAULT_FLUID) -> float:
    """Saturation temperature at pressure ``P`` [Pa], in K.

    The inverse of :func:`saturation_pressure`. Enforces the S0 Section 3 loop-state
    bound ``P_triple < P < P_crit``: outside it there is no saturation state and the
    call raises rather than returning a supercritical or sub-triple value.
    """
    _v.positive("P", P)
    p_crit = critical_pressure(fluid)
    p_triple = triple_pressure(fluid)
    if P >= p_crit:
        raise ValueError(
            f"P = {P} Pa is at or above the critical pressure of {fluid} "
            f"({p_crit:.4g} Pa); no saturation temperature exists (no blanket "
            "supercritical treatment)"
        )
    if P <= p_triple:
        raise ValueError(
            f"P = {P} Pa is at or below the triple-point pressure of {fluid} "
            f"({p_triple:.4g} Pa); no saturation temperature exists"
        )
    T_sat = PropsSI("T", "P", P, "Q", 0.0, fluid)
    assert_two_phase_domain(T_sat, fluid)
    return T_sat


def saturation_enthalpies(
    P: float, fluid: str = DEFAULT_FLUID
) -> tuple[float, float, float]:
    """Saturated ``(h_f, h_g, h_fg)`` at pressure ``P`` [Pa], in J/kg.

    ``h_f`` is the saturated-liquid enthalpy, ``h_g`` the saturated-vapour enthalpy,
    and ``h_fg = h_g - h_f`` the latent heat of vaporisation. These are the terms
    behind the vapour quality ``x = (h - h_f) / h_fg`` (S0 Section 3).
    """
    T_sat = saturation_temperature(P, fluid)  # validates P and the domain
    h_f = PropsSI("H", "T", T_sat, "Q", 0.0, fluid)
    h_g = PropsSI("H", "T", T_sat, "Q", 1.0, fluid)
    return h_f, h_g, h_g - h_f


def surface_tension(T: float, fluid: str = DEFAULT_FLUID) -> float:
    """Liquid-vapour surface tension at saturation temperature ``T`` [K], in N/m."""
    assert_two_phase_domain(T, fluid)
    return PropsSI("I", "T", T, "Q", 0.0, fluid)


def saturation_properties(P: float, fluid: str = DEFAULT_FLUID) -> dict[str, float]:
    """Every saturation property the S2 evaporator needs, at pressure ``P`` [Pa].

    Bundles the two-phase state so a caller takes one guarded trip to the pinned
    backend instead of several unguarded ones.
    """
    T_sat = saturation_temperature(P, fluid)
    h_f, h_g, h_fg = saturation_enthalpies(P, fluid)
    rho_f, rho_g = saturated_densities(T_sat, fluid)
    return {
        "T_sat_K": T_sat,
        "h_f_J_kg": h_f,
        "h_g_J_kg": h_g,
        "h_fg_J_kg": h_fg,
        "rho_f_kg_m3": rho_f,
        "rho_g_kg_m3": rho_g,
        "mu_f_Pa_s": PropsSI("V", "T", T_sat, "Q", 0.0, fluid),
        "mu_g_Pa_s": PropsSI("V", "T", T_sat, "Q", 1.0, fluid),
        "k_f_W_mK": PropsSI("L", "T", T_sat, "Q", 0.0, fluid),
        "cp_f_J_kgK": PropsSI("C", "T", T_sat, "Q", 0.0, fluid),
        "sigma_N_m": surface_tension(T_sat, fluid),
        "p_reduced": P / critical_pressure(fluid),
        "molar_mass_kg_mol": PropsSI("M", fluid),
    }


def provenance(fluid: str = DEFAULT_FLUID) -> dict[str, str]:
    """Version and equation-of-state citation for reproducibility records.

    Include this next to every generated property table: values are only
    comparable against the same CoolProp version and EOS.
    """
    return {
        "package": "CoolProp",
        "version": CoolProp.__version__,
        "backend": "HEOS",
        "fluid": fluid,
        "eos_bibtex_key": get_BibTeXKey(fluid, "EOS"),
    }


# --- per-state transport properties (fulfils the B1 property_backend; used by B3) ---


def density(T: float, P: float, fluid: str = DEFAULT_FLUID) -> float:
    """Density at (T [K], P [Pa]), kg/m^3."""
    _v.positive("T", T)
    _v.positive("P", P)
    return PropsSI("D", "T", T, "P", P, fluid)


def specific_heat(T: float, P: float, fluid: str = DEFAULT_FLUID) -> float:
    """Isobaric specific heat cp at (T, P), J/kg/K."""
    _v.positive("T", T)
    _v.positive("P", P)
    return PropsSI("C", "T", T, "P", P, fluid)


def thermal_conductivity(T: float, P: float, fluid: str = DEFAULT_FLUID) -> float:
    """Thermal conductivity at (T, P), W/m/K."""
    _v.positive("T", T)
    _v.positive("P", P)
    return PropsSI("L", "T", T, "P", P, fluid)


def dynamic_viscosity(T: float, P: float, fluid: str = DEFAULT_FLUID) -> float:
    """Dynamic viscosity at (T, P), Pa*s."""
    _v.positive("T", T)
    _v.positive("P", P)
    return PropsSI("V", "T", T, "P", P, fluid)


def prandtl(T: float, P: float, fluid: str = DEFAULT_FLUID) -> float:
    """Prandtl number Pr = cp * mu / k at (T, P) [-]."""
    return (
        specific_heat(T, P, fluid)
        * dynamic_viscosity(T, P, fluid)
        / thermal_conductivity(T, P, fluid)
    )


def triple_temperature(fluid: str = DEFAULT_FLUID) -> float:
    """Triple-point temperature, K (lower bound for the liquid; a freeze proxy)."""
    return PropsSI("T_triple", fluid)


def transport_properties(T: float, P: float, fluid: str = DEFAULT_FLUID) -> dict[str, float]:
    """All per-state properties the pumped-loop model needs, at (T, P)."""
    return {
        "density": density(T, P, fluid),
        "specific_heat": specific_heat(T, P, fluid),
        "thermal_conductivity": thermal_conductivity(T, P, fluid),
        "dynamic_viscosity": dynamic_viscosity(T, P, fluid),
        "prandtl": prandtl(T, P, fluid),
    }


def single_phase_liquid_margins(T: float, P: float, fluid: str = DEFAULT_FLUID) -> dict[str, float]:
    """Margins that keep a coolant a subcooled single-phase liquid at (T, P).

    - ``subcooling_Pa`` = P - P_sat(T) (must be > 0: loop pressure exceeds saturation);
    - ``freeze_margin_K`` = T - T_triple;
    - ``critical_margin_K`` = T_crit - T.

    ``ok`` is True iff all three are positive. Above the critical temperature the
    saturation curve does not exist and ``subcooling_Pa`` is ``-inf``.
    """
    _v.positive("T", T)
    _v.positive("P", P)
    t_crit = critical_temperature(fluid)
    crit = t_crit - T
    freeze = T - triple_temperature(fluid)
    subcool = float("-inf") if T >= t_crit else P - saturation_pressure(T, fluid)
    return {
        "subcooling_Pa": subcool,
        "freeze_margin_K": freeze,
        "critical_margin_K": crit,
        "ok": bool(subcool > 0 and freeze > 0 and crit > 0),
    }
