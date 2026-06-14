"""Executable thermophysical-property checks for the AI1 coolant screen.

Computes the ammonia properties that the companion paper ("The AI1 Design
Point", doi:10.5281/zenodo.20670772) quotes as NIST Chemistry WebBook
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
    """(liquid, vapor) densities on the saturation curve at ``T``, kg/m^3."""
    rho_liq = PropsSI("D", "T", T, "Q", 0.0, fluid)
    rho_vap = PropsSI("D", "T", T, "Q", 1.0, fluid)
    return rho_liq, rho_vap


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
