"""B5: Stage-1 common-envelope architecture cases (coolant x solid path).

Assembles the coolant x material case space, **classifies every combination by the actual
B1-B4 gates** (no hardcoded verdicts), solves the rank-eligible cases through the B4 coupled
model under one declared common operating envelope, and computes a **modeled component mass**
(incomplete Stage-1 accounting, 4.8a). The point is to show the entire case space and prove the
gates work -- not to pretend all combinations are equally valid.

Classification (per 4.8):
- ``rank-eligible``   : passes coolant (B3), solid (B2), and contract (B4) gates AND is feasible
  under the common envelope; only these enter ranked comparison outputs.
- ``sensitivity-only``: a property is sensitivity-status (e.g., CO2 near-critical loop use).
- ``source-required`` : a property needs a cited source (PGW composition; anisotropic APG/
  diamond directional conductivity).
- ``unsupported``     : a deferred model path (C3 direct solar).
- ``rejected``        : provenance-eligible but **physics-infeasible** under the envelope
  (junction limit, single-phase margin, correlation domain, non-convergence).

No-invention rules: sensitivity/source-required/unsupported cases are **never** ranked, never
averaged into ranked conclusions, and never reported as published performance. A non-ranked
case is only *evaluated* if the required parametric inputs are explicitly supplied and labelled.

Mass scope (as directed): **modeled component mass only**, labelled
``"modeled component mass (incomplete Stage-1 accounting)"``; no total-system / launch /
flight-qualified mass is claimed. Containment follows 4.6 (gauge pressure, safety factor once,
thin-wall only when r/t >= 10 else Lame thick-wall, ideal-shell lower bound when endcaps /
joints / minimum gauge / launch transient are absent).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from . import coupled_model as _cm
from . import pumped_loop as _pl
from . import registry
from ._validate import positive
from .coupled_model import Contract, RadiatorFace, RadiatorSpec
from .solid_network import SolidPath, build_ranked_path, build_sensitivity_path

COOLANTS = ("ammonia", "water", "pgw", "co2")
MATERIALS = ("aluminum", "copper", "apg", "diamond_composite")


class Classification(str, Enum):
    RANK_ELIGIBLE = "rank-eligible"
    SENSITIVITY_ONLY = "sensitivity-only"
    SOURCE_REQUIRED = "source-required"
    UNSUPPORTED = "unsupported/deferred"
    REJECTED = "rejected"


class Reason(str, Enum):
    RANK_ELIGIBLE_FEASIBLE = "rank-eligible and feasible under the Stage-1 envelope"
    COOLANT_BACKEND_BLOCKED = (
        "coolant loop-use is sensitivity-status (near-critical); no rank-eligible backend")
    COOLANT_SOURCE_REQUIRED = "coolant composition source-required; no rank-eligible backend"
    MATERIAL_ANISOTROPIC_SOURCE_REQUIRED = (
        "anisotropic material; isotropic conduction path not rank-eligible (directional "
        "conductivity source required)")
    CONTRACT_C3_UNSUPPORTED = "C3 direct-solar contract deferred (sink omits direct solar)"
    CONTRACT_C2_SOURCE_REQUIRED = "C2 excluded-face-outside-thermal-CV evidence required"
    JUNCTION_LIMIT_FAILURE = "junction temperature over limit under the Stage-1 envelope"
    SINGLE_PHASE_MARGIN_FAILURE = "single-phase margin failure under the Stage-1 envelope"
    CORRELATION_DOMAIN_FAILURE = "Reynolds outside a valid correlation domain under the envelope"
    OTHER_FEASIBILITY_FAILURE = "feasibility gate failure under the Stage-1 envelope"
    NONCONVERGENCE = "coupled solve did not converge under the Stage-1 envelope"
    NOT_EVALUATED = "classified only; not evaluated (no backend, or no parametric inputs supplied)"


# map every B4 feasibility gate name -> a reason code (all failed gates are preserved, F1)
_GATE_REASON = {
    "junction_within_limit": Reason.JUNCTION_LIMIT_FAILURE,
    "subcooling_margin": Reason.SINGLE_PHASE_MARGIN_FAILURE,
    "freeze_margin": Reason.SINGLE_PHASE_MARGIN_FAILURE,
    "critical_margin": Reason.SINGLE_PHASE_MARGIN_FAILURE,
    "radiator_above_sink": Reason.SINGLE_PHASE_MARGIN_FAILURE,
    "reynolds_in_range": Reason.CORRELATION_DOMAIN_FAILURE,
}


# --- Stage-1 common envelope ----------------------------------------------------


@dataclass(frozen=True)
class Stage1Envelope:
    """The single declared Stage-1 common operating point. Every field is a **design variable**
    (or a sourced/declared basis for mass), not a published-architecture value. Loop/cold-plate
    geometry and the heat load are Stage-1 design variables; the sink is the inherited Phase A
    shielded boundary (design variable)."""

    # thermal / hydraulic design point
    q_compute_W: float = 1200.0
    sink_temperature_K: float = 250.0
    emissivity: float = 0.9
    area_fraction: float = 2.0  # C1 bifacial: A_emit = 2 * A_plan
    contract: Contract = Contract.C1
    radiator_area_m2: float = 2.0  # Mode T design variable
    mass_flow_kg_s: float = 0.05
    tube_diameter_m: float = 0.004
    loop_length_m: float = 2.0
    coldplate_wetted_area_m2: float = 0.05
    radiator_wetted_area_m2: float = 4.0
    low_side_pressure_Pa: float = 20.0e5
    eta_pump: float = 0.70
    eta_motor: float = 0.90
    t_junction_max_K: float = 398.15  # 125 C design-variable limit
    subcooling_margin_Pa: float = 1.0e4
    # solid path geometry (design variables)
    solid_length_m: float = 0.002
    solid_area_m2: float = 5.0e-3
    source_radius_m: float = 0.02
    plate_radius_m: float = 0.03
    thickness_m: float = 0.02
    contact_conductance_W_m2K: float = 2.0e4
    contact_source: str = "Madhusudana 1996 (Stage-1 design variable)"
    # mass bases (design-variable / sourced; used only for modeled component mass)
    wall_density_kg_m3: float = 2700.0  # Al 6061 tube wall (design variable)
    wall_allowable_stress_Pa: float = 138.0e6  # SF already applied once (design variable)
    radiator_areal_density_kg_m2: float = 4.0  # design variable
    solid_density_kg_m3: dict[str, float] = field(
        default_factory=lambda: {"aluminum": 2700.0, "copper": 8960.0})

    def radiator_spec(self) -> RadiatorSpec:
        return RadiatorSpec(
            faces=(RadiatorFace(self.area_fraction, self.sink_temperature_K),),
            emissivity=self.emissivity, contract=self.contract)

    def ranked_solid_path(self, material: str) -> SolidPath:
        return build_ranked_path(
            material=material, length_m=self.solid_length_m, area_m2=self.solid_area_m2,
            source_radius_m=self.source_radius_m, plate_radius_m=self.plate_radius_m,
            thickness_m=self.thickness_m, contact_conductance_W_m2K=self.contact_conductance_W_m2K,
            contact_source=self.contact_source)

    def sensitivity_solid_path(self, k_W_mK: float, note: str) -> SolidPath:
        return build_sensitivity_path(
            k_W_mK=k_W_mK, length_m=self.solid_length_m, area_m2=self.solid_area_m2,
            source_radius_m=self.source_radius_m, plate_radius_m=self.plate_radius_m,
            thickness_m=self.thickness_m,
            contact_conductance_W_m2K=self.contact_conductance_W_m2K, note=note)


# --- gate-driven classification (probes the real B2/B3/B4 gates) ----------------


def _coolant_verdict(coolant: str) -> tuple[Classification | None, Reason | None]:
    """None if the coolant has a rank-eligible backend (B3); else its blocking category."""
    try:
        _pl.assert_loop_coolant_rankable(coolant)
        return None, None
    except registry.NotRankEligibleError:
        # distinguish sensitivity (CO2 near-critical) vs source-required (PGW) via registry status
        status_entry = {
            "co2": "coolant.co2.loop_use",
            "pgw": "coolant.pgw.concentration",
            "propylene_glycol_water": "coolant.pgw.concentration",
        }.get(coolant)
        status = None
        if status_entry is not None:
            try:
                status = registry.get(status_entry).status.value
            except Exception:
                status = None
        if status == "sensitivity":
            return Classification.SENSITIVITY_ONLY, Reason.COOLANT_BACKEND_BLOCKED
        return Classification.SOURCE_REQUIRED, Reason.COOLANT_SOURCE_REQUIRED


def _material_verdict(
    envelope: Stage1Envelope, material: str
) -> tuple[Classification | None, Reason | None]:
    """None if a rank-eligible ranked solid path builds (B2); else source-required (anisotropic)."""
    try:
        envelope.ranked_solid_path(material)
        return None, None
    except registry.NotRankEligibleError:
        return Classification.SOURCE_REQUIRED, Reason.MATERIAL_ANISOTROPIC_SOURCE_REQUIRED


def _contract_verdict(spec: RadiatorSpec) -> tuple[Classification | None, Reason | None]:
    if spec.contract is Contract.C3:
        return Classification.UNSUPPORTED, Reason.CONTRACT_C3_UNSUPPORTED
    if spec.contract is Contract.C2 and not spec.rank_eligible:
        return Classification.SOURCE_REQUIRED, Reason.CONTRACT_C2_SOURCE_REQUIRED
    return None, None


# provenance-block precedence (most-binding first): unsupported > sensitivity-only > source-required
_PRECEDENCE = {
    Classification.UNSUPPORTED: 0,
    Classification.SENSITIVITY_ONLY: 1,
    Classification.SOURCE_REQUIRED: 2,
}


def classify_provenance(
    envelope: Stage1Envelope, coolant: str, material: str
) -> tuple[Classification | None, tuple[Reason, ...]]:
    """Run the coolant / material / contract gates. Returns (None, ()) if the combination is
    provenance-eligible (still subject to a physics feasibility check), else the blocking
    classification and **all** applicable reason codes."""
    verdicts = [
        _contract_verdict(envelope.radiator_spec()),
        _coolant_verdict(coolant),
        _material_verdict(envelope, material),
    ]
    blocking = [(c, r) for c, r in verdicts if c is not None]
    if not blocking:
        return None, ()
    reasons = tuple(r for _, r in blocking)
    primary = min((c for c, _ in blocking), key=lambda c: _PRECEDENCE.get(c, 9))
    return primary, reasons


# --- modeled component mass (4.6 / 4.8a) ----------------------------------------


@dataclass(frozen=True)
class MassComponent:
    name: str
    mass_kg: float | None  # None => excluded / not modeled
    basis: str  # design-variable | sourced | derived
    included: bool
    completeness: str  # modeled | lower-bound | excluded
    note: str = ""


@dataclass(frozen=True)
class ModeledMass:
    components: tuple[MassComponent, ...]
    total_modeled_kg: float
    label: str = "modeled component mass (incomplete Stage-1 accounting)"
    excluded_components: tuple[str, ...] = ()


# components explicitly NOT modeled at Stage-1 (named so the incompleteness is visible)
_EXCLUDED = (
    "accumulator", "pump", "motor", "valves", "manifolds", "fittings", "supports", "MLI",
    "sensors", "harness", "redundancy", "structural margin", "minimum manufacturable gauge",
    "endcaps/joints", "integration hardware",
)


def containment_ideal_shell(
    p_abs_Pa: float, radius_m: float, length_m: float, wall_density_kg_m3: float,
    allowable_stress_Pa: float,
) -> MassComponent:
    """Tube containment mass, ideal thin/thick-wall shell (4.6). Pressure is **gauge**
    (``P_g = P_abs`` in vacuum). The safety factor is assumed **already applied once** in
    ``allowable_stress_Pa``. Thin-wall hoop ``t = P_g r / sigma`` is used only when r/t >= 10;
    otherwise the Lame thick-wall wall thickness is used. Endcaps / joints / minimum gauge /
    launch-transient allowance are **absent**, so this is an **ideal-shell lower bound**."""
    positive("p_abs_Pa", p_abs_Pa)
    positive("radius_m", radius_m)
    p_g = p_abs_Pa  # vacuum ambient ~ 0
    t_thin = p_g * radius_m / allowable_stress_Pa
    if radius_m / t_thin >= 10.0:
        t = t_thin
        model = "thin-wall hoop"
    else:
        # Lame thick-wall: outer radius from sigma_theta at the bore = sigma_allow
        ratio2 = (allowable_stress_Pa + p_g) / (allowable_stress_Pa - p_g)
        r_o = radius_m * math.sqrt(ratio2) if allowable_stress_Pa > p_g else float("inf")
        t = r_o - radius_m
        model = "Lame thick-wall"
    mass = wall_density_kg_m3 * (2.0 * math.pi * radius_m * t) * length_m
    return MassComponent(
        name="tube containment shell", mass_kg=mass, basis="design-variable", included=True,
        completeness="lower-bound",
        note=f"{model}; gauge P_g={p_g:.3e} Pa; t={t*1e3:.4f} mm; ideal-shell lower bound "
        "(no endcaps/joints/min-gauge/launch transient)")


def modeled_component_mass(
    result_coupled, envelope: Stage1Envelope, material: str, fluid_name: str
) -> ModeledMass:
    """Modeled component mass for a solved case. Includes only components whose geometry +
    material basis is present; everything else is named in ``excluded_components``."""
    from . import fluids
    comps: list[MassComponent] = []

    area = _pl.flow_area(envelope.tube_diameter_m)
    # density at the solved mean state; the coupled result carries the coolant via its solve
    rho = fluids.density(
        result_coupled.mean_fluid_K, result_coupled.mean_pressure_Pa, fluid_name)
    v_tube = area * envelope.loop_length_m
    comps.append(MassComponent(
        name="coolant inventory (tube)", mass_kg=rho * v_tube, basis="derived", included=True,
        completeness="lower-bound",
        note="tube volume only; cold-plate/manifold volume excluded"))

    # containment shell (4.6) sized for the maximum absolute pressure P_lo + dP
    p_abs_max = envelope.low_side_pressure_Pa + result_coupled.pressure_drop_Pa
    comps.append(containment_ideal_shell(
        p_abs_max, envelope.tube_diameter_m / 2.0, envelope.loop_length_m,
        envelope.wall_density_kg_m3, envelope.wall_allowable_stress_Pa))

    # solid conduction element + spreader disk
    rho_solid = envelope.solid_density_kg_m3.get(material)
    if rho_solid is not None:
        v_cond = envelope.solid_area_m2 * envelope.solid_length_m
        v_spread = math.pi * envelope.plate_radius_m**2 * envelope.thickness_m
        comps.append(MassComponent(
            name="solid conduction + spreader element", mass_kg=rho_solid * (v_cond + v_spread),
            basis="derived", included=True, completeness="modeled",
            note=f"rho={rho_solid:.0f} kg/m^3 (design variable)"))
    else:
        comps.append(MassComponent(
            name="solid conduction + spreader element", mass_kg=None, basis="sourced",
            included=False, completeness="excluded", note="no declared material density"))

    # radiator panel (only if areal density declared)
    if envelope.radiator_areal_density_kg_m2 > 0:
        rad_mass = envelope.radiator_areal_density_kg_m2 * result_coupled.A_emit_m2
        areal = envelope.radiator_areal_density_kg_m2
        comps.append(MassComponent(
            name="radiator panel", mass_kg=rad_mass, basis="design-variable", included=True,
            completeness="modeled",
            note=f"areal density {areal:.1f} kg/m^2 (design variable)"))

    total = math.fsum(c.mass_kg for c in comps if c.included and c.mass_kg is not None)
    return ModeledMass(
        components=tuple(comps), total_modeled_kg=total, excluded_components=_EXCLUDED)



# --- case evaluation ------------------------------------------------------------


@dataclass(frozen=True)
class CaseResult:
    coolant: str
    material: str
    contract: str
    classification: Classification
    reason_codes: tuple[Reason, ...]
    evaluated: bool
    rank_eligible: bool
    coupled: object | None = None  # CoupledResult when evaluated
    mass: ModeledMass | None = None


def evaluate_case(
    envelope: Stage1Envelope, coolant: str, material: str, *,
    parametric_conductivity_W_mK: float | None = None,
    parametric_note: str = "",
) -> CaseResult:
    """Classify one combination by the gates, then act:

    - **provenance-eligible** -> solve ranked under the envelope. Feasible => ``rank-eligible``
      (enters ranked outputs) with a modeled component mass; infeasible => ``rejected`` with the
      failing-gate reason.
    - **non-eligible** -> classified only; **evaluated as a sensitivity only if**
      ``parametric_conductivity_W_mK`` is supplied *and* the coolant has a backend
      (ammonia/water). Never rank-eligible; never enters ranked outputs."""
    spec = envelope.radiator_spec()
    cls, reasons = classify_provenance(envelope, coolant, material)

    if cls is None:
        # provenance-eligible: run the physics under the common envelope
        try:
            r = _cm.solve_coupled(
                mode="T", q_compute_W=envelope.q_compute_W, coolant=coolant,
                solid_path=envelope.ranked_solid_path(material), radiator=spec,
                mass_flow_kg_s=envelope.mass_flow_kg_s, tube_diameter_m=envelope.tube_diameter_m,
                loop_length_m=envelope.loop_length_m,
                coldplate_wetted_area_m2=envelope.coldplate_wetted_area_m2,
                radiator_wetted_area_m2=envelope.radiator_wetted_area_m2,
                low_side_pressure_Pa=envelope.low_side_pressure_Pa,
                radiator_area_m2=envelope.radiator_area_m2, eta_pump=envelope.eta_pump,
                eta_motor=envelope.eta_motor, t_junction_max_K=envelope.t_junction_max_K,
                subcooling_margin_Pa=envelope.subcooling_margin_Pa, ranked=True)
            mass = modeled_component_mass(r, envelope, material, _cm._COOLANT_FLUID[coolant])
            return CaseResult(coolant, material, spec.contract.value, Classification.RANK_ELIGIBLE,
                              (Reason.RANK_ELIGIBLE_FEASIBLE,), True, True, r, mass)
        except _cm.FeasibilityError as exc:
            reasons = tuple(dict.fromkeys(  # every failed gate -> a reason (deduped, F1)
                _GATE_REASON.get(g, Reason.OTHER_FEASIBILITY_FAILURE) for g in exc.failed_gates
            )) or (Reason.OTHER_FEASIBILITY_FAILURE,)
            return CaseResult(coolant, material, spec.contract.value, Classification.REJECTED,
                              reasons, True, False, None, None)
        except _cm.ConvergenceError:
            return CaseResult(coolant, material, spec.contract.value, Classification.REJECTED,
                              (Reason.NONCONVERGENCE,), True, False, None, None)

    # non-eligible: sensitivity evaluation only if a parametric conductivity is supplied AND the
    # coolant has a backend (CO2/PGW have none, so they stay classification-only).
    if parametric_conductivity_W_mK is not None and coolant in _cm._COOLANT_FLUID:
        r = _cm.solve_coupled(
            mode="T", q_compute_W=envelope.q_compute_W, coolant=coolant,
            solid_path=envelope.sensitivity_solid_path(parametric_conductivity_W_mK,
                                                       parametric_note or "parametric sensitivity"),
            radiator=spec, mass_flow_kg_s=envelope.mass_flow_kg_s,
            tube_diameter_m=envelope.tube_diameter_m, loop_length_m=envelope.loop_length_m,
            coldplate_wetted_area_m2=envelope.coldplate_wetted_area_m2,
            radiator_wetted_area_m2=envelope.radiator_wetted_area_m2,
            low_side_pressure_Pa=envelope.low_side_pressure_Pa,
            radiator_area_m2=envelope.radiator_area_m2, eta_pump=envelope.eta_pump,
            eta_motor=envelope.eta_motor, t_junction_max_K=envelope.t_junction_max_K,
            subcooling_margin_Pa=envelope.subcooling_margin_Pa, ranked=False)
        return CaseResult(
            coolant, material, spec.contract.value, cls, reasons, True, False, r, None)

    return CaseResult(
        coolant, material, spec.contract.value, cls, reasons, False, False, None, None)


def build_case_matrix(
    envelope: Stage1Envelope, coolants=COOLANTS, materials=MATERIALS
) -> list[CaseResult]:
    """Classify (and, where provenance-eligible, solve) every coolant x material combination.
    Non-eligible combinations are classification-only here; supply parametric inputs via
    :func:`evaluate_case` to add a labelled sensitivity."""
    return [evaluate_case(envelope, c, m) for c in coolants for m in materials]


def matrix_summary(results: list[CaseResult]) -> dict[str, int]:
    """Count total / rank-eligible / non-ranked (by category)."""
    out = {"total": len(results), "rank_eligible": 0, "sensitivity_only": 0,
           "source_required": 0, "unsupported": 0, "rejected": 0}
    key = {
        Classification.RANK_ELIGIBLE: "rank_eligible",
        Classification.SENSITIVITY_ONLY: "sensitivity_only",
        Classification.SOURCE_REQUIRED: "source_required",
        Classification.UNSUPPORTED: "unsupported",
        Classification.REJECTED: "rejected",
    }
    for r in results:
        out[key[r.classification]] += 1
    out["non_ranked"] = out["total"] - out["rank_eligible"]
    return out


def ranked_cases(results: list[CaseResult]) -> list[CaseResult]:
    """Only the rank-eligible, feasible cases -- the sole cases allowed in ranked outputs."""
    return [r for r in results if r.classification is Classification.RANK_ELIGIBLE]
