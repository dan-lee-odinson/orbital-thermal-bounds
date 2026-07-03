"""B4: coupled steady-state chip-to-radiator solution (B0 plan Sections 4.1a and 5).

The junction-to-radiator path is solved as the **simultaneous** solution of the five
per-node residuals R1-R5, *not* a one-directional ``T_rad = T_chip - sum(dT)`` subtraction.
Radiator and transport temperatures (or the radiator area) are **outputs** of the coupled
solve.

Residuals (B0 plan 4.1a; ``T_f,cp = T_f,rad = (T1+T2)/2 = T_mean``)::

    R1: T_j - T_w  - Q_chip*(R_cond+R_spread+R_contact)          = 0   (junction chain; Q_chip)
    R2: T_w - T_mean - Q_chip*R_film,cp                          = 0   (wall -> cold-plate film)
    R3: Q_chip + Q_pump - m_dot*cp*(T2 - T1)                     = 0   (loop energy; pump heat)
    R4: T_mean - T_rad - Q_rad*R_film,rad                        = 0   (radiator film)
    R5: Q_rad - sum_faces eps*sigma*A_face*(T_rad^4 - T_sink^4)  = 0   (radiator law)

**Heat-injection rule (4.1a).** ``Q_chip`` flows through the junction chain (R1, R2) only;
``Q_pump`` is added directly to the fluid (R3), never routed through the chip-side resistances.
The radiator rejects ``Q_rad = Q_chip + Q_pump_fluid`` (fluid-loop boundary, 4.7).

**Solve structure.** The Jacobian is lower-triangular in solve order R5 -> R4 -> R3 -> R2 -> R1;
the single circular dependency (pump heat / properties <-> loop temperature) is resolved as a
fixed point in loop mean temperature and pressure. The radiator law is linear in ``T_rad^4``,
so R5 (Mode T) and its inverse (Mode A) are closed form.

**Scope (B4, as directed).** Modes T and A only (Mode S -> B6). Mass/containment deferred to
B5. Direct solar: C1/C2 rank-eligible using the inherited (shielded) Phase A sink; C3 is
parametric-only (missing ``alpha_s`` blocks ranking) and adds no solar term to ``sink.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from . import pumped_loop as _pl
from . import registry
from ._validate import nonneg, positive
from .radiation import SIGMA_SB, required_area
from .solid_network import SolidPath

_COOLANT_FLUID = {"ammonia": "Ammonia", "water": "Water"}


class SolveMode(str, Enum):
    T = "T"  # fix A_rad, m_dot -> solve T_rad
    A = "A"  # fix T_rad, m_dot -> solve A_rad


class Contract(str, Enum):
    C1 = "C1"  # fully-shielded bifacial
    C2 = "C2"  # single cold-face (one-sided)
    C3 = "C3"  # explicit sunlit face (parametric-only; deferred solar term)


class CoupledError(ValueError):
    """Base class for coupled-solver failures (fail loudly, B0 plan 5)."""


class ConvergenceError(CoupledError):
    """The fixed point did not reach the nondimensional tolerance."""


class FeasibilityError(CoupledError):
    """A converged solution failed a feasibility gate and is rejected (ranked case, 5)."""


class BranchError(CoupledError):
    """Multi-start seeds converged to different roots (multiplicity reported, not chosen)."""


# --- radiator faces / contract --------------------------------------------------


@dataclass(frozen=True)
class RadiatorFace:
    """One emitting face: ``area_fraction`` multiples of the planform area ``A_plan`` at an
    effective ``sink_temperature_K`` (from the Phase A orbital sink). ``parametric_solar_flux``
    is a C3-only, user-supplied (sourced or parametric) absorbed flux; its presence forces the
    case non-rank-eligible (the inherited sink omits direct solar, 4.4a)."""

    area_fraction: float
    sink_temperature_K: float
    parametric_solar_flux_W_m2: float | None = None

    def __post_init__(self) -> None:
        positive("area_fraction", self.area_fraction)
        nonneg("sink_temperature_K", self.sink_temperature_K)
        if self.parametric_solar_flux_W_m2 is not None:
            nonneg("parametric_solar_flux_W_m2", self.parametric_solar_flux_W_m2)


@dataclass(frozen=True)
class RadiatorSpec:
    """Emitting faces + emissivity + declared direct-solar contract (4.4a)."""

    faces: tuple[RadiatorFace, ...]
    emissivity: float
    contract: Contract

    def __post_init__(self) -> None:
        if not (0.0 < self.emissivity <= 1.0):
            raise ValueError(f"emissivity must be in (0, 1], got {self.emissivity}")
        if not self.faces:
            raise ValueError("radiator must have at least one emitting face")
        c = self.contract
        has_solar = any(f.parametric_solar_flux_W_m2 is not None for f in self.faces)
        if c is Contract.C2 and len(self.faces) != 1:
            raise ValueError("C2 (single cold-face) must declare exactly one emitting face")
        if c is Contract.C3 and not has_solar:
            # a C3 face is sunlit+coupled: without a sourced/parametric alpha_s*G it cannot be
            # modeled (sink.py omits direct solar) and must never be assumed. (4.4a)
            raise registry.NotRankEligibleError(
                "C3 declares a sunlit, thermally coupled face but supplies no direct-solar flux; "
                "missing alpha_s blocks ranking and the case cannot be solved as-is (4.4a)."
            )
        if c in (Contract.C1, Contract.C2) and has_solar:
            raise ValueError(
                f"{c.value} faces are shielded; a direct-solar flux implies C3 (4.4a)."
            )

    @property
    def total_area_fraction(self) -> float:
        return math.fsum(f.area_fraction for f in self.faces)

    @property
    def max_sink_K(self) -> float:
        return max(f.sink_temperature_K for f in self.faces)

    @property
    def rank_eligible(self) -> bool:
        # C3 (direct solar) is parametric-only until sink.py grows the solar term (4.4a).
        return self.contract in (Contract.C1, Contract.C2)


# --- result ---------------------------------------------------------------------


@dataclass(frozen=True)
class CoupledResult:
    """Converged coupled steady state. Temperatures/area are solved outputs (B0 plan B4)."""

    mode: str
    contract: str
    T_j_K: float
    T_w_K: float
    T1_K: float
    T2_K: float
    T_rad_K: float
    A_plan_m2: float
    A_emit_m2: float
    Q_chip_W: float
    Q_pump_fluid_W: float
    Q_rad_W: float
    pump: _pl.PumpEnergy
    mean_fluid_K: float
    mean_pressure_Pa: float
    pressure_drop_Pa: float
    reynolds: float
    mean_htc_W_m2K: float
    residual_norm: float
    energy_closure_rel: float
    iterations: int
    converged: bool
    feasible: bool
    feasibility: dict[str, bool] = field(default_factory=dict)
    rank_eligible: bool = False


# --- radiator law (linear in T_rad^4) -------------------------------------------


def radiator_temperature(Q_rad_W: float, A_plan_m2: float, spec: RadiatorSpec) -> float:
    """Solve R5 for ``T_rad`` (closed form; the law is linear in ``T_rad^4``)."""
    positive("Q_rad_W", Q_rad_W)
    positive("A_plan_m2", A_plan_m2)
    esa = spec.emissivity * SIGMA_SB * A_plan_m2
    frac_sum = spec.total_area_fraction
    sink4 = math.fsum(f.area_fraction * f.sink_temperature_K**4 for f in spec.faces)
    t4 = (Q_rad_W + esa * sink4) / (esa * frac_sum)
    return t4**0.25


def radiator_area(Q_rad_W: float, T_rad_K: float, spec: RadiatorSpec) -> float:
    """Solve R5 for the planform area ``A_plan`` given ``T_rad`` (Mode A)."""
    positive("Q_rad_W", Q_rad_W)
    positive("T_rad_K", T_rad_K)
    per_unit = spec.emissivity * SIGMA_SB * math.fsum(
        f.area_fraction * (T_rad_K**4 - f.sink_temperature_K**4) for f in spec.faces
    )
    if per_unit <= 0.0:
        raise FeasibilityError(
            f"T_rad={T_rad_K:.2f} K does not exceed every face sink "
            f"(max {spec.max_sink_K:.2f} K); no positive emitting area rejects Q_rad."
        )
    return Q_rad_W / per_unit


def _radiator_rejection(T_rad_K: float, A_plan_m2: float, spec: RadiatorSpec) -> float:
    return spec.emissivity * SIGMA_SB * A_plan_m2 * math.fsum(
        f.area_fraction * (T_rad_K**4 - f.sink_temperature_K**4) for f in spec.faces
    )


# --- rank-eligibility (inherits B2 solid path + B3 coolant + 4.4a contract) ------


def assert_case_rank_eligible(coolant: str, solid_path: SolidPath, radiator: RadiatorSpec) -> None:
    """A ranked coupled case needs a rank-eligible coolant backend (B3), a rank-eligible solid
    path (B2: isotropic + spreading + cited contact), and a rank-eligible radiator contract
    (C1/C2). Any failure raises ``NotRankEligibleError``."""
    _pl.assert_loop_coolant_rankable(coolant)
    if not solid_path.rank_eligible:
        raise registry.NotRankEligibleError(
            "solid path is not rank-eligible (anisotropic, uncited contact, or missing "
            "spreading without a 1-D justification); run the case as a sensitivity (B2)."
        )
    if not radiator.rank_eligible:
        raise registry.NotRankEligibleError(
            f"radiator contract {radiator.contract.value} is parametric-only "
            "(direct solar omitted by the inherited sink, 4.4a); not rank-eligible."
        )


# --- coupled solve --------------------------------------------------------------


def solve_coupled(
    *,
    mode: str | SolveMode,
    q_compute_W: float,
    coolant: str,
    solid_path: SolidPath,
    radiator: RadiatorSpec,
    mass_flow_kg_s: float,
    tube_diameter_m: float,
    loop_length_m: float,
    coldplate_wetted_area_m2: float,
    radiator_wetted_area_m2: float,
    low_side_pressure_Pa: float,
    radiator_area_m2: float | None = None,
    radiator_temperature_K: float | None = None,
    boundary: str = "fluid_loop",
    eta_pump: float = 0.70,
    eta_motor: float = 0.90,
    t_junction_max_K: float | None = None,
    minor_loss_K: float = 0.0,
    rel_roughness: float = 0.0,
    subcooling_margin_Pa: float = 1.0e4,
    ranked: bool = True,
    neglect_transport_losses: bool = False,
    tol: float = 1.0e-9,
    max_iter: int = 200,
    relaxation: float = 0.5,
    multistart: bool = True,
) -> CoupledResult:
    """Solve the coupled steady state in Mode T (fix ``radiator_area_m2``) or Mode A (fix
    ``radiator_temperature_K``). Returns a :class:`CoupledResult`. For ``ranked=True`` a
    converged-but-infeasible solution is **rejected** (raises :class:`FeasibilityError`); for a
    sensitivity case it is returned with ``feasible=False``. ``neglect_transport_losses`` zeroes
    the solid/film resistances and pump heat for the Phase A baseline-recovery test."""
    mode = SolveMode(mode)
    positive("q_compute_W", q_compute_W)
    positive("mass_flow_kg_s", mass_flow_kg_s)
    positive("tube_diameter_m", tube_diameter_m)
    positive("loop_length_m", loop_length_m)
    positive("coldplate_wetted_area_m2", coldplate_wetted_area_m2)
    positive("radiator_wetted_area_m2", radiator_wetted_area_m2)
    positive("low_side_pressure_Pa", low_side_pressure_Pa)
    if mode is SolveMode.T and radiator_area_m2 is None:
        raise ValueError("Mode T requires radiator_area_m2 (the fixed design variable)")
    if mode is SolveMode.A and radiator_temperature_K is None:
        raise ValueError("Mode A requires radiator_temperature_K (the fixed design variable)")
    if ranked:
        assert_case_rank_eligible(coolant, solid_path, radiator)
    fluid = _COOLANT_FLUID.get(coolant)
    if fluid is None:
        raise registry.NotRankEligibleError(f"unknown coolant '{coolant}' (no property backend)")

    from . import fluids  # local import: CoolProp optional at package level

    q_chip = q_compute_W
    r_solid = 0.0 if neglect_transport_losses else solid_path.total_K_per_W
    area = _pl.flow_area(tube_diameter_m)
    t_crit = fluids.critical_temperature(fluid)

    def _seed_mean() -> float:
        base = radiator_temperature_K if mode is SolveMode.A else radiator.max_sink_K + 40.0
        return float(base)

    def _fixed_point(mean0: float) -> dict:
        mean = mean0
        press = low_side_pressure_Pa
        q_pump = 0.0
        iters = 0
        for iters in range(1, max_iter + 1):
            if mean >= t_crit - 1.0:
                # left the single-phase-liquid domain (supercritical excursion) -> not a
                # physical root for this seed (B0 plan 5: phase-envelope violation).
                return dict(converged=False, iters=iters, mean=mean,
                            reason='left single-phase-liquid domain', q_rad=q_chip + q_pump)
            props = fluids.transport_properties(mean, press, fluid)
            rho, cp = props["density"], props["specific_heat"]
            mu, k, pr = props["dynamic_viscosity"], props["thermal_conductivity"], props["prandtl"]
            vel = _pl.velocity(mass_flow_kg_s, rho, area)
            re = _pl.reynolds(mass_flow_kg_s, tube_diameter_m, mu, area)
            dp = _pl.pressure_drop(
                _pl.friction_factor(re, rel_roughness), loop_length_m, tube_diameter_m,
                rho, vel, minor_loss_K,
            )
            h = _pl.heat_transfer_coefficient(_pl.nusselt(re, pr), k, tube_diameter_m)
            r_film_cp = 0.0 if neglect_transport_losses else _pl.film_resistance(
                h, coldplate_wetted_area_m2)
            r_film_rad = 0.0 if neglect_transport_losses else _pl.film_resistance(
                h, radiator_wetted_area_m2)
            pump = _pl.pump_energy(
                mass_flow_kg_s, dp, rho, eta_pump=eta_pump, eta_motor=eta_motor, boundary=boundary)
            q_pump_fluid = 0.0 if neglect_transport_losses else pump.fluid_heat_W
            q_rad = q_chip + q_pump_fluid

            if mode is SolveMode.T:
                t_rad = radiator_temperature(q_rad, float(radiator_area_m2), radiator)
            else:
                t_rad = float(radiator_temperature_K)
            mean_new = t_rad + q_rad * r_film_rad
            press = low_side_pressure_Pa + 0.5 * dp

            done_mean = abs(mean_new - mean) < tol * max(1.0, mean)
            done_pump = abs(q_pump_fluid - q_pump) < tol * max(1.0, q_rad)
            if done_mean and done_pump:
                mean = mean_new
                q_pump = q_pump_fluid
                return dict(
                    mean=mean, press=press, cp=cp, rho=rho, re=re, dp=dp, h=h,
                    r_film_cp=r_film_cp, r_film_rad=r_film_rad, pump=pump,
                    q_pump_fluid=q_pump_fluid, q_rad=q_rad, t_rad=t_rad, iters=iters,
                    converged=True,
                )
            mean = (1.0 - relaxation) * mean + relaxation * mean_new
            q_pump = q_pump_fluid
        return dict(converged=False, iters=iters, mean=mean, q_rad=q_chip + q_pump)

    sol = _fixed_point(_seed_mean())
    if not sol["converged"]:
        reason = sol.get("reason", "residual above tolerance")
        raise ConvergenceError(
            f"coupled solve did not converge in {max_iter} iterations "
            f"(mode {mode.value}; {reason}); last mean T = {sol['mean']:.3f} K."
        )

    # multi-start: perturbed seeds must reach the same radiator temperature (unique root).
    if multistart:
        lo = max(radiator.max_sink_K + 2.0, 0.9 * sol["mean"])
        hi = min(t_crit - 5.0, 1.1 * sol["mean"])
        for seed in (lo, hi):
            alt = _fixed_point(seed)
            if not alt["converged"]:
                continue
            if abs(alt["t_rad"] - sol["t_rad"]) > 1.0e-6 * max(1.0, sol["t_rad"]):
                raise BranchError(
                    f"multi-start disagreement: T_rad {sol['t_rad']:.4f} vs {alt['t_rad']:.4f} K; "
                    "multiple physical roots reported, not silently chosen."
                )

    mean, press, cp = sol["mean"], sol["press"], sol["cp"]
    q_rad, t_rad = sol["q_rad"], sol["t_rad"]
    r_film_cp, r_film_rad = sol["r_film_cp"], sol["r_film_rad"]

    d_t = q_rad / (mass_flow_kg_s * cp)  # R3
    t1, t2 = mean - 0.5 * d_t, mean + 0.5 * d_t
    t_w = mean + q_chip * r_film_cp  # R2
    t_j = t_w + q_chip * r_solid  # R1

    if mode is SolveMode.T:
        a_plan = float(radiator_area_m2)
    else:
        a_plan = radiator_area(q_rad, t_rad, radiator)
    a_emit = a_plan * radiator.total_area_fraction

    # nondimensional residual vector (each residual scaled by its characteristic magnitude)
    dt_char = max(1.0, t_j - radiator.max_sink_K)
    q_char = max(1.0, q_rad)
    res = [
        (t_j - t_w - q_chip * r_solid) / dt_char,
        (t_w - mean - q_chip * r_film_cp) / dt_char,
        (q_rad - mass_flow_kg_s * cp * (t2 - t1)) / q_char,
        (mean - t_rad - q_rad * r_film_rad) / dt_char,
        (q_rad - _radiator_rejection(t_rad, a_plan, radiator)) / q_char,
    ]
    residual_norm = math.sqrt(math.fsum(r * r for r in res) / len(res))
    q_pump_boundary = sol["q_pump_fluid"]
    energy_closure_rel = abs(q_rad - (q_chip + q_pump_boundary)) / q_char

    # feasibility gates (post-convergence, B0 plan 5)
    p_sat_hot = fluids.saturation_pressure(t2, fluid)
    gates = {
        "mass_flow_positive": mass_flow_kg_s > 0.0,
        "temperature_ordering": t_j >= t_w >= mean >= t_rad and t2 >= t1,
        "efficiencies_valid": 0.0 < eta_pump <= 1.0 and 0.0 < eta_motor <= 1.0,
        "radiator_above_sink": t_rad > radiator.max_sink_K,
        "reynolds_in_range": sol["re"] <= _pl._LAMINAR_RE or sol["re"] >= _pl._TURBULENT_RE_NUSSELT,
        "pressure_above_saturation": low_side_pressure_Pa - p_sat_hot >= subcooling_margin_Pa,
        "residual_converged": residual_norm < 1.0e-6,
        "energy_closed": energy_closure_rel < 1.0e-6,
    }
    if t_junction_max_K is not None:
        gates["junction_within_limit"] = t_j <= t_junction_max_K
    feasible = all(gates.values())

    if ranked and not feasible:
        failed = [name for name, ok in gates.items() if not ok]
        raise FeasibilityError(
            f"ranked coupled case converged but failed feasibility gate(s): {failed}. "
            "A converged-but-infeasible solution is rejected (B0 plan 5)."
        )

    return CoupledResult(
        mode=mode.value, contract=radiator.contract.value,
        T_j_K=t_j, T_w_K=t_w, T1_K=t1, T2_K=t2, T_rad_K=t_rad,
        A_plan_m2=a_plan, A_emit_m2=a_emit,
        Q_chip_W=q_chip, Q_pump_fluid_W=q_pump_boundary, Q_rad_W=q_rad,
        pump=sol["pump"], mean_fluid_K=mean, mean_pressure_Pa=press,
        pressure_drop_Pa=sol["dp"], reynolds=sol["re"], mean_htc_W_m2K=sol["h"],
        residual_norm=residual_norm, energy_closure_rel=energy_closure_rel,
        iterations=sol["iters"], converged=True, feasible=feasible, feasibility=gates,
        rank_eligible=ranked and radiator.rank_eligible,
    )


def phase_a_baseline_temperature(
    q_W: float, area_m2: float, emissivity: float, sink_K: float
) -> float:
    """Phase A inverse of the area law: the ``T_rad`` that rejects ``q_W`` over ``area_m2`` at a
    single shared sink. Used by the Mode-T baseline-recovery test."""
    positive("q_W", q_W)
    positive("area_m2", area_m2)
    return (sink_K**4 + q_W / (emissivity * SIGMA_SB * area_m2)) ** 0.25


def phase_a_baseline_area(q_W: float, T_rad_K: float, emissivity: float, sink_K: float) -> float:
    """Phase A area law (thin wrapper over :func:`radiation.required_area`) for the Mode-A
    baseline-recovery test."""
    return required_area(q_W, T_rad_K, emissivity, sink_K)
