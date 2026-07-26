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

from dataclasses import dataclass, field

from . import _validate as _v
from .registry import NotRankEligibleError, assert_in_domain, get
from .registry.applicability import Consequence, Violation
from .registry.two_phase import (
    STANDARD_GRAVITY_M_S2,
    accelerational_pressure_drop,
    lockhart_martinelli_frictional_gradient,
    pump_inlet_subcooling_margin,
    static_pressure_drop,
)

DP_ID = "two_phase.dp.lockhart_martinelli_chisholm"
NPSH_ID = "two_phase.pump.npsh"
HTC_ID = "two_phase.htc.gungor_winterton"
CHF_ID = "two_phase.chf.shah_1987"


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


@dataclass(frozen=True)
class PressureDropResult:
    """Total two-phase pressure drop, its components, and its applicability verdict."""

    total_Pa: float
    frictional_Pa: float
    accelerational_Pa: float
    static_Pa: float
    violations: tuple[Violation, ...] = ()
    caveats: tuple[str, ...] = ()

    @property
    def is_applicable(self) -> bool:
        """True only when no declared applicability axis was violated.

        For this project's loop this is **always False**: the frictional correlation is
        declared for horizontal two-component flow and the loop is neither.
        """
        return not self.violations


def two_phase_pressure_drop(
    *,
    dp_dz_liquid_Pa_m: float,
    dp_dz_gas_Pa_m: float,
    liquid_regime: str,
    gas_regime: str,
    length_m: float,
    mass_flux_kg_m2s: float,
    quality_in: float,
    quality_out: float,
    rho_f: float,
    rho_g: float,
    pressure_Pa: float,
    composition: str,
    geometry_shape: str,
    orientation: str,
    height_m: float = 0.0,
    gravity_m_s2: float = STANDARD_GRAVITY_M_S2,
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

    assert_in_domain(entry, context="S3 two-phase pressure drop", P_Pa=pressure_Pa)

    violations: tuple[Violation, ...] = ()
    if spec is not None:
        violations = spec.check(
            composition=composition,
            geometry=geometry_shape,
            orientation=orientation,
            gravity_m_s2=gravity_m_s2,
            has_executable_form=entry.has_executable_form,
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
            dp_dz_liquid=dp_dz_liquid_Pa_m,
            dp_dz_gas=dp_dz_gas_Pa_m,
            liquid_regime=liquid_regime,
            gas_regime=gas_regime,
        )
        * length_m
    )
    accel = accelerational_pressure_drop(
        mass_flux_kg_m2s=mass_flux_kg_m2s,
        quality_in=quality_in,
        quality_out=quality_out,
        rho_f=rho_f,
        rho_g=rho_g,
    )
    # Mixture density in the homogeneous limit, consistent with the acceleration term.
    x_mean = 0.5 * (quality_in + quality_out)
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
    dp_dz_liquid_Pa_m: float,
    dp_dz_gas_Pa_m: float,
    liquid_regime: str,
    gas_regime: str,
    mass_flux_kg_m2s: float,
    quality_in: float,
    quality_out: float,
    rho_f: float,
    rho_g: float,
    pressure_Pa: float,
    composition: str,
    geometry_shape: str,
    orientation: str,
    height_m: float = 0.0,
    gravity_m_s2: float = STANDARD_GRAVITY_M_S2,
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
                dp_dz_liquid_Pa_m=dp_dz_liquid_Pa_m,
                dp_dz_gas_Pa_m=dp_dz_gas_Pa_m,
                liquid_regime=liquid_regime,
                gas_regime=gas_regime,
                length_m=length,
                mass_flux_kg_m2s=mass_flux_kg_m2s,
                quality_in=quality_in,
                quality_out=quality_out,
                rho_f=rho_f,
                rho_g=rho_g,
                pressure_Pa=pressure_Pa,
                composition=composition,
                geometry_shape=geometry_shape,
                orientation=orientation,
                height_m=height_m,
                gravity_m_s2=gravity_m_s2,
            )
            points.append(BorePoint(diameter_m=d, required_length_m=length, pressure_drop=dp))
        except NotRankEligibleError as exc:
            points.append(
                BorePoint(
                    diameter_m=d,
                    required_length_m=length,
                    pressure_drop=None,
                    blocked_reason=str(exc),
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
