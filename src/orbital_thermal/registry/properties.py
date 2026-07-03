"""B1 property registry: coolant, solid, and containment-material entries.

Resolved coolant transport values are **DERIVED** from CoolProp's HEOS backend at
a stated reference state and pinned to CoolProp 7.2.0 (re-derived in the test
suite). Everything that cannot yet be authoritatively sourced is registered with
a machine-visible blocker status and ``value=None`` -- no value is invented
(no-invention policy; B0 plan Sections 2, 4.2, 4.5, 4.6).

Reference state for the resolved liquid-coolant transport values: **saturated
liquid at T = 300 K (Q = 0)**. These are single representative values for the
registry; per-state property evaluation over the loop happens in B3 via
:mod:`orbital_thermal.fluids`. Single-phase operation additionally requires the
loop pressure contract of B0 plan Section 4.3.
"""

from __future__ import annotations

from .provenance import (
    Domain,
    PropertyEntry,
    Provenance,
    Source,
    Status,
)

_COOLPROP = "CoolProp HEOS"
_COOLPROP_VERSION = "7.2.0"
_REF_STATE = "saturated liquid, T=300 K (Q=0)"
_LIQUID_BAND = Domain(ranges={"T_K": (278.0, 360.0)})  # intended Stage-1 single-phase band

_NIST = Source(
    citation="NIST Chemistry WebBook, SRD 69 (via CoolProp HEOS, Gao et al. JPCRD 2020)",
    locator="doi:10.18434/T4D303",
)
_INCROPERA = Source(
    citation="Incropera & DeWitt, Fundamentals of Heat and Mass Transfer, Table A.1 (300 K)",
)


def _coolprop_prop(
    fid: str, name: str, material: str, quantity: str, value: float, units: str
) -> PropertyEntry:
    return PropertyEntry(
        id=fid,
        name=name,
        material=material,
        quantity=quantity,
        provenance=Provenance.DERIVED,
        status=Status.RESOLVED,
        value=value,
        units=units,
        domain=_LIQUID_BAND,
        source=_NIST,
        backend=_COOLPROP,
        version=_COOLPROP_VERSION,
        applicability=f"{_REF_STATE}; per-state evaluation via orbital_thermal.fluids in B3",
    )


# --- Coolants -------------------------------------------------------------------

# Ammonia: DERIVED from CoolProp 7.2.0 at 300 K saturated liquid (Q=0).
_AMMONIA = [
    _coolprop_prop("coolant.ammonia.density", "Ammonia density", "ammonia",
                   "density", 600.170, "kg/m^3"),
    _coolprop_prop("coolant.ammonia.specific_heat", "Ammonia specific heat", "ammonia",
                   "specific_heat_cp", 4796.38, "J/kg/K"),
    _coolprop_prop("coolant.ammonia.thermal_conductivity", "Ammonia thermal conductivity",
                   "ammonia", "thermal_conductivity", 0.48064, "W/m/K"),
    _coolprop_prop("coolant.ammonia.viscosity", "Ammonia dynamic viscosity", "ammonia",
                   "dynamic_viscosity", 1.2948896e-04, "Pa*s"),
    PropertyEntry(
        id="coolant.ammonia.critical_temperature",
        name="Ammonia critical temperature",
        material="ammonia",
        quantity="critical_temperature",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        value=405.4,
        units="K",
        source=_NIST,
        backend=_COOLPROP,
        version=_COOLPROP_VERSION,
        applicability="phase-margin anchor (B0 4.2); paper NIST anchor ~405.5 K",
    ),
]

# Water: DERIVED from CoolProp 7.2.0 at 300 K saturated liquid (Q=0).
_WATER = [
    _coolprop_prop("coolant.water.density", "Water density", "water",
                   "density", 996.513, "kg/m^3"),
    _coolprop_prop("coolant.water.specific_heat", "Water specific heat", "water",
                   "specific_heat_cp", 4180.91, "J/kg/K"),
    _coolprop_prop("coolant.water.thermal_conductivity", "Water thermal conductivity",
                   "water", "thermal_conductivity", 0.60944, "W/m/K"),
    _coolprop_prop("coolant.water.viscosity", "Water dynamic viscosity", "water",
                   "dynamic_viscosity", 8.5375135e-04, "Pa*s"),
]

# Propylene-glycol / water (PGW): the incompressible-mixture backend exists
# (CoolProp INCOMP::MPG), but the concentration is not yet standardized and its
# freeze-protection basis is not sourced (B0 4.2). Blocked pending that source.
_PGW = [
    PropertyEntry(
        id="coolant.pgw.concentration",
        name="PGW mass-fraction concentration",
        material="propylene_glycol_water",
        quantity="mass_fraction_propylene_glycol",
        provenance=Provenance.ASSUMED,
        status=Status.SOURCE_REQUIRED,
        value=None,
        units="-",
        backend="CoolProp INCOMP::MPG (available)",
        version=_COOLPROP_VERSION,
        applicability="concentration must be set from the mission cold-case freeze margin",
        note="backend available; concentration + freeze basis SOURCE_REQUIRED",
    ),
    PropertyEntry(
        id="coolant.pgw.transport_properties",
        name="PGW transport properties",
        material="propylene_glycol_water",
        quantity="density_cp_k_mu",
        provenance=Provenance.ASSUMED,
        status=Status.SOURCE_REQUIRED,
        value=None,
        units="SI",
        backend="CoolProp INCOMP::MPG (available)",
        version=_COOLPROP_VERSION,
        applicability="derivable once concentration is fixed; blocked until then",
    ),
]

# CO2: Stage-1 SENSITIVITY-ONLY and NOT rank-eligible (B0 4.2 -- 278-308 K
# straddles the critical point; needs a compressible/near-critical treatment).
# The critical point itself is a published anchor.
_CO2 = [
    PropertyEntry(
        id="coolant.co2.critical_temperature",
        name="CO2 critical temperature",
        material="co2",
        quantity="critical_temperature",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        value=304.128,
        units="K",
        source=_NIST,
        backend=_COOLPROP,
        version=_COOLPROP_VERSION,
        applicability="phase-envelope anchor only; does NOT make CO2 a rankable coolant",
    ),
    PropertyEntry(
        id="coolant.co2.critical_pressure",
        name="CO2 critical pressure",
        material="co2",
        quantity="critical_pressure",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        value=7.3773e6,
        units="Pa",
        source=_NIST,
        backend=_COOLPROP,
        version=_COOLPROP_VERSION,
        applicability="phase-envelope anchor only",
    ),
    PropertyEntry(
        id="coolant.co2.loop_use",
        name="CO2 as a Stage-1 loop coolant",
        material="co2",
        quantity="single_phase_loop_properties",
        provenance=Provenance.SENSITIVITY,
        status=Status.SENSITIVITY,
        value=None,
        units="SI",
        applicability="sensitivity-only in Stage 1; requires a compressible/near-critical "
        "treatment before any ranked use (B0 4.2)",
        note="NOT rank-eligible in Stage 1",
    ),
]

# --- Solids ---------------------------------------------------------------------

_SOLIDS = [
    PropertyEntry(
        id="solid.aluminum.thermal_conductivity",
        name="Aluminum (pure) thermal conductivity",
        material="aluminum",
        quantity="thermal_conductivity",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        value=237.0,
        units="W/m/K",
        source=_INCROPERA,
        applicability="isotropic reference material; alloy/temper selection is a design variable",
    ),
    PropertyEntry(
        id="solid.copper.thermal_conductivity",
        name="Copper thermal conductivity",
        material="copper",
        quantity="thermal_conductivity",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        value=401.0,
        units="W/m/K",
        source=_INCROPERA,
        applicability="isotropic reference material",
    ),
    PropertyEntry(
        id="solid.apg.in_plane_conductivity",
        name="APG in-plane thermal conductivity",
        material="annealed_pyrolytic_graphite",
        quantity="in_plane_thermal_conductivity",
        provenance=Provenance.SENSITIVITY,
        status=Status.SOURCE_REQUIRED,
        value=None,
        units="W/m/K",
        applicability="anisotropic; product/process-specific directional data required (B0 4.5)",
        note="NOT rank-eligible without cited directional data; sensitivity-only otherwise",
    ),
    PropertyEntry(
        id="solid.apg.through_plane_conductivity",
        name="APG through-plane thermal conductivity",
        material="annealed_pyrolytic_graphite",
        quantity="through_plane_thermal_conductivity",
        provenance=Provenance.SENSITIVITY,
        status=Status.SOURCE_REQUIRED,
        value=None,
        units="W/m/K",
        applicability="anisotropic; product/process-specific directional data required (B0 4.5)",
    ),
    PropertyEntry(
        id="solid.diamond_composite.thermal_conductivity",
        name="Diamond-composite thermal conductivity",
        material="diamond_composite",
        quantity="thermal_conductivity",
        provenance=Provenance.SENSITIVITY,
        status=Status.SOURCE_REQUIRED,
        value=None,
        units="W/m/K",
        applicability="highly product-specific (MMC vs CVD); directional data required (B0 4.5)",
    ),
]

# --- Containment materials (B0 4.6) ---------------------------------------------
# Density and yield are published; the allowable stress is SOURCE_REQUIRED until
# the design code and single safety-factor convention are fixed (B0 4.6: SF is
# applied once, never twice).

_MMPDS = Source(citation="ASM / MMPDS handbook room-temperature properties")

_CONTAINMENT = [
    PropertyEntry(
        id="containment.al6061t6.density",
        name="Al 6061-T6 density",
        material="aluminum_6061_t6",
        quantity="density",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        value=2700.0,
        units="kg/m^3",
        source=_MMPDS,
    ),
    PropertyEntry(
        id="containment.al6061t6.yield_strength",
        name="Al 6061-T6 yield strength",
        material="aluminum_6061_t6",
        quantity="yield_strength",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        value=276.0e6,
        units="Pa",
        source=_MMPDS,
        applicability="room temperature; on-orbit temperature derating not yet applied",
    ),
    PropertyEntry(
        id="containment.al6061t6.allowable_stress",
        name="Al 6061-T6 allowable stress",
        material="aluminum_6061_t6",
        quantity="allowable_stress",
        provenance=Provenance.ASSUMED,
        status=Status.SOURCE_REQUIRED,
        value=None,
        units="Pa",
        applicability="requires a design code and a single SF convention (B0 4.6)",
        note="SF applied once; blocked until code + SF fixed",
    ),
    PropertyEntry(
        id="containment.ti6al4v.density",
        name="Ti-6Al-4V density",
        material="titanium_6al_4v",
        quantity="density",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        value=4430.0,
        units="kg/m^3",
        source=_MMPDS,
    ),
    PropertyEntry(
        id="containment.ti6al4v.allowable_stress",
        name="Ti-6Al-4V allowable stress",
        material="titanium_6al_4v",
        quantity="allowable_stress",
        provenance=Provenance.ASSUMED,
        status=Status.SOURCE_REQUIRED,
        value=None,
        units="Pa",
        applicability="requires a design code and a single SF convention (B0 4.6)",
    ),
    PropertyEntry(
        id="containment.safety_factor_convention",
        name="Containment safety-factor convention",
        material="(all)",
        quantity="safety_factor_convention",
        provenance=Provenance.ASSUMED,
        status=Status.SOURCE_REQUIRED,
        value=None,
        units="-",
        applicability="one design code (e.g., ASME BPVC / AIAA S-080); SF applied once (B0 4.6)",
    ),
]

PROPERTIES: list[PropertyEntry] = (
    _AMMONIA + _WATER + _PGW + _CO2 + _SOLIDS + _CONTAINMENT
)

PROPERTIES_BY_ID: dict[str, PropertyEntry] = {e.id: e for e in PROPERTIES}
