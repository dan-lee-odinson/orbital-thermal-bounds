"""Stage 2, milestone S2: two-phase acquisition / evaporator (screening level).

The executable form of the physics the S1 two-phase registry names: vapour quality
and loop state, the flow-boiling heat-transfer coefficient, the ONB / saturated-
regime policy, the CHF / dryout bands, and the local-wall-flux discipline.

**Screening level, no coupled solve.** This module evaluates an acquisition section
at a stated operating point and classifies it. It does not solve a loop, a condenser
or a radiator boundary together (that is S4), and it computes no pressure drop (that
is S3 / OTB-G002).

Scope of what is and is not modelled here
-----------------------------------------

*Implemented.* Vapour quality from enthalpy (S0 Sec. 3), the Gungor & Winterton
(1986) flow-boiling HTC via the registry, the regime/ONB rank policy, the CHF bands
of S0 Sec. 3 and director ruling 9.5, and the local-flux basis discipline of
S0 Sec. 5.

*Deliberately absent, with the gap machine-visible rather than filled by a guess:*

* **No sourced ONB criterion.** ``two_phase.onb.bergles_rohsenow`` is graphical in
  the original and water-only in its usual algebraic surrogate, so it is not
  implemented. The regime gate therefore applies the S0 Sec. 3 (F2) fallback: absent
  a sourced criterion, a case that is not unambiguously in saturated flow boiling is
  **sensitivity-only, never rank-eligible**. Pass a sourced criterion to
  :func:`classify_regime` if one is ever obtained -- the gate works either way.
* **No sourced CHF correlation.** ``two_phase.chf.shah_2015`` carries an ambiguous
  citation and a domain that traces to a different paper, so it is not implemented.
  :func:`classify_chf_band` is a pure policy gate over a CHF *value*; obtaining that
  value from the registry raises, because no rank-eligible CHF evaluator exists.

Gravity basis
-------------

Every correlation reached from here is a **1g reference correlation**
(``microgravity_validated=False``). Nothing in this module is microgravity-validated
and no such claim is made; ranked outputs carry the S0 Sec. 7 ranking-scope wording.

This module is stdlib-only. Saturation properties come from
:mod:`orbital_thermal.fluids`, which the caller evaluates and passes in, so the
policy gates here remain testable without CoolProp installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from . import _validate as _v
from .registry import NotRankEligibleError, assert_in_domain, get
from .registry.two_phase import (
    fluid_in_gw86_database,
    gungor_winterton_1986_htc,
)

#: Registry ids this module evaluates against.
HTC_ID = "two_phase.htc.gungor_winterton"
CHF_ID = "two_phase.chf.shah_2015"
ONB_ID = "two_phase.onb.bergles_rohsenow"

#: Director ruling 9.5 (S0 Sec. 3): a ranked case needs q''/CHF at or below this.
CHF_RANK_MAX = 0.5
#: At or above this ratio the section is in dryout and the case is rejected.
CHF_DRYOUT = 1.0


# --- vocabulary -----------------------------------------------------------------


class Regime(str, Enum):
    """Thermodynamic regime of the acquisition section at the evaluated point."""

    SUBCOOLED_LIQUID = "subcooled_liquid"
    SATURATED_TWO_PHASE = "saturated_two_phase"
    SUPERHEATED_VAPOUR = "superheated_vapour"


class RankStatus(str, Enum):
    """How a case may be used in Stage-2 reporting.

    ``RANK_ELIGIBLE`` may enter a ranked comparison; ``SENSITIVITY_ONLY`` is reported
    but never ranked; ``REJECTED`` fails a physical gate; ``BLOCKED`` cannot be
    evaluated at all because a required input is unsourced. Only ``RANK_ELIGIBLE``
    is rankable -- the other three are all non-rankable, for different reasons, and
    the distinction is kept because they mean different things to a reviewer.
    """

    RANK_ELIGIBLE = "rank_eligible"
    SENSITIVITY_ONLY = "sensitivity_only"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class FluxBasis(str, Enum):
    """How a wall heat flux was obtained (S0 Sec. 3 / Sec. 5).

    ``LOCAL_SOURCED`` is the only basis a ranked case may use. The two average bases
    exist so that an average flux can be *named and categorised* when one is
    deliberately used -- never silently substituted for a local flux.
    """

    LOCAL_SOURCED = "local_sourced"
    SECTION_AVERAGE = "section_average"
    CHIP_AVERAGE = "chip_average"


_NON_LOCAL_BASES = frozenset({FluxBasis.SECTION_AVERAGE, FluxBasis.CHIP_AVERAGE})


# --- T2: loop state and vapour quality ------------------------------------------


@dataclass(frozen=True)
class LoopState:
    """The two-phase loop state at a point: pressure, enthalpy, quality, regime.

    ``equilibrium_quality`` is the raw thermodynamic ratio ``(h - h_f)/h_fg`` and may
    be negative (subcooled) or above 1 (superheated). ``quality`` is the *physical*
    vapour quality and is populated only inside the two-phase dome, where
    ``0 <= x <= 1`` holds by construction; elsewhere it is ``None``. Keeping both
    means the subcooled and superheated cases stay distinguishable for the regime
    gate instead of being clamped into silence.
    """

    pressure_Pa: float
    enthalpy_J_kg: float
    h_f_J_kg: float
    h_g_J_kg: float
    h_fg_J_kg: float
    equilibrium_quality: float
    quality: float | None
    regime: Regime

    @property
    def is_two_phase(self) -> bool:
        return self.regime is Regime.SATURATED_TWO_PHASE


def vapour_quality(
    enthalpy_J_kg: float, h_f_J_kg: float, h_fg_J_kg: float
) -> float:
    """Vapour quality ``x = (h - h_f) / h_fg`` (S0 Sec. 3), enforced to ``[0, 1]``.

    Raises ``ValueError`` outside the two-phase dome rather than clamping: a clamped
    quality would silently turn a subcooled or superheated state into a saturated
    one. Use :func:`loop_state` when the state may legitimately be outside the dome.
    """
    _v.finite("enthalpy_J_kg", enthalpy_J_kg)
    _v.finite("h_f_J_kg", h_f_J_kg)
    _v.positive("h_fg_J_kg", h_fg_J_kg)
    x = (enthalpy_J_kg - h_f_J_kg) / h_fg_J_kg
    if not (0.0 <= x <= 1.0):
        raise ValueError(
            f"vapour quality x = {x:.6g} is outside the physical range [0, 1]; "
            "the state is not saturated two-phase (use loop_state to classify it)"
        )
    return x


def loop_state(
    *,
    pressure_Pa: float,
    enthalpy_J_kg: float,
    h_f_J_kg: float,
    h_g_J_kg: float,
) -> LoopState:
    """Classify a loop state from its pressure and enthalpy.

    The caller supplies the saturation enthalpies at ``pressure_Pa`` -- from
    :func:`orbital_thermal.fluids.saturation_enthalpies`, which already enforces
    ``P_triple < P < P_crit`` and the registered temperature domain, so no blanket
    supercritical treatment can reach this function.
    """
    _v.positive("pressure_Pa", pressure_Pa)
    _v.finite("enthalpy_J_kg", enthalpy_J_kg)
    if not h_g_J_kg > h_f_J_kg:
        raise ValueError(
            f"h_g ({h_g_J_kg}) must exceed h_f ({h_f_J_kg}); the saturation "
            "enthalpies do not bracket a two-phase dome"
        )
    h_fg = h_g_J_kg - h_f_J_kg
    x_eq = (enthalpy_J_kg - h_f_J_kg) / h_fg

    if x_eq < 0.0:
        regime, x = Regime.SUBCOOLED_LIQUID, None
    elif x_eq > 1.0:
        regime, x = Regime.SUPERHEATED_VAPOUR, None
    else:
        regime, x = Regime.SATURATED_TWO_PHASE, x_eq

    return LoopState(
        pressure_Pa=pressure_Pa,
        enthalpy_J_kg=enthalpy_J_kg,
        h_f_J_kg=h_f_J_kg,
        h_g_J_kg=h_g_J_kg,
        h_fg_J_kg=h_fg,
        equilibrium_quality=x_eq,
        quality=x,
        regime=regime,
    )


# --- T6: local wall heat flux discipline ----------------------------------------


@dataclass(frozen=True)
class WallHeatFlux:
    """A wall heat flux together with **how it was obtained**.

    S0 Sec. 3 requires ``q''`` in ``q''/CHF`` to be the *local modeled* wall heat
    flux derived from sourced geometry / heat-spreading. Carrying the basis in the
    value itself is what makes a section- or chip-average impossible to substitute
    silently: the basis travels with the number to every gate that consumes it.
    """

    value_W_m2: float
    basis: FluxBasis
    geometry_sourced: bool
    note: str = ""

    @property
    def is_rankable_basis(self) -> bool:
        """True only for a local flux derived from sourced geometry."""
        return self.basis is FluxBasis.LOCAL_SOURCED and self.geometry_sourced


def local_wall_heat_flux(
    *, power_W: float, wetted_area_m2: float, geometry_sourced: bool, note: str = ""
) -> WallHeatFlux:
    """Build a **local** wall heat flux from sourced channel geometry.

    ``geometry_sourced=False`` is accepted and recorded rather than rejected: the
    resulting value is simply not of a rankable basis, so the case degrades to
    sensitivity-only at :func:`assess_acquisition` instead of failing here. Channel
    geometry is source-required (S0 Sec. 5), so an unsourced geometry must never
    produce a rank-eligible case.
    """
    _v.nonneg("power_W", power_W)
    _v.positive("wetted_area_m2", wetted_area_m2)
    _v.boolean("geometry_sourced", geometry_sourced)
    return WallHeatFlux(
        value_W_m2=power_W / wetted_area_m2,
        basis=FluxBasis.LOCAL_SOURCED,
        geometry_sourced=geometry_sourced,
        note=note,
    )


def averaged_wall_heat_flux(
    *, power_W: float, area_m2: float, basis: FluxBasis, note: str = ""
) -> WallHeatFlux:
    """Build an explicitly-named **average** wall heat flux.

    Permitted only because it is named and categorised (S0 Sec. 3): the returned
    value is never of a rankable basis, so it cannot reach a ranked case. Raises if
    handed ``FluxBasis.LOCAL_SOURCED``, which would defeat the point.
    """
    _v.nonneg("power_W", power_W)
    _v.positive("area_m2", area_m2)
    if basis not in _NON_LOCAL_BASES:
        raise ValueError(
            f"averaged_wall_heat_flux requires an averaging basis "
            f"({', '.join(sorted(b.value for b in _NON_LOCAL_BASES))}), got "
            f"'{basis.value}'; use local_wall_heat_flux for a local flux"
        )
    return WallHeatFlux(
        value_W_m2=power_W / area_m2,
        basis=basis,
        geometry_sourced=False,
        note=note,
    )


# --- T4: ONB / saturated-regime policy gate -------------------------------------


@dataclass(frozen=True)
class RegimeAssessment:
    """Outcome of the ONB / saturated-regime gate."""

    regime: Regime
    status: RankStatus
    onb_criterion_sourced: bool
    reason: str


def classify_regime(
    state: LoopState, *, onb_criterion: object = None
) -> RegimeAssessment:
    """Apply the S0 Sec. 3 (F2) ONB / saturated-regime rank policy.

    Rank-eligible Stage-2 cases are restricted to a defined **saturated flow-boiling**
    regime. The gate ships unconditionally and works with or without a sourced ONB
    criterion:

    * ``onb_criterion=None`` (the state of this build -- no sourced criterion exists,
      see :mod:`orbital_thermal.registry.two_phase`): a case that is not
      unambiguously in saturated flow boiling cannot be shown to sit above ONB, so it
      is **sensitivity-only, not rank-eligible**. This is the conservative direction:
      the unknown de-ranks the case rather than admitting it.
    * A sourced criterion supplied by a caller is recorded as such; separating the
      two states is what keeps "we checked ONB" distinct from "we could not".

    A superheated / post-dryout state is rejected outright: the implemented HTC is a
    wetted-wall correlation and is not valid once the wall dries out.
    """
    sourced = onb_criterion is not None

    if state.regime is Regime.SUPERHEATED_VAPOUR:
        return RegimeAssessment(
            regime=state.regime,
            status=RankStatus.REJECTED,
            onb_criterion_sourced=sourced,
            reason=(
                "state is superheated vapour (x > 1): the wall is dry, and the "
                "implemented flow-boiling HTC is valid only while the wall is wetted"
            ),
        )

    if state.regime is Regime.SUBCOOLED_LIQUID:
        return RegimeAssessment(
            regime=state.regime,
            status=RankStatus.SENSITIVITY_ONLY,
            onb_criterion_sourced=sourced,
            reason=(
                "state is subcooled liquid, so it is at or below the onset of "
                "nucleate boiling. "
                + (
                    "A sourced ONB criterion was supplied but the S2 policy still "
                    "restricts ranking to the saturated flow-boiling regime."
                    if sourced
                    else "No sourced ONB criterion exists "
                    "(two_phase.onb.bergles_rohsenow is SOURCE_REQUIRED), so the "
                    "case cannot be shown to sit above ONB and is sensitivity-only "
                    "per S0 Sec. 3 (F2)."
                )
            ),
        )

    return RegimeAssessment(
        regime=state.regime,
        status=RankStatus.RANK_ELIGIBLE,
        onb_criterion_sourced=sourced,
        reason="state is in the saturated flow-boiling regime (0 <= x <= 1)",
    )


# --- T5: CHF / dryout bands -----------------------------------------------------


@dataclass(frozen=True)
class ChfAssessment:
    """Outcome of the CHF / dryout banding gate (director ruling 9.5)."""

    ratio: float
    status: RankStatus
    reason: str


def classify_chf_band(
    wall_flux: WallHeatFlux, chf_W_m2: float
) -> ChfAssessment:
    """Band a case by ``q'' / CHF`` per S0 Sec. 3 and director ruling 9.5.

    ``q''/CHF <= 0.5`` rank-eligible; ``0.5 < q''/CHF < 1`` sensitivity-only,
    reported but not ranked; ``q''/CHF >= 1`` dryout, rejected.

    ``q''`` must be the **local modeled** wall flux: a non-local basis cannot produce
    a rank-eligible band however small the ratio, because the ratio would then be
    computed on the wrong quantity. This is a **modelling margin, not flight
    certification.**
    """
    _v.positive("chf_W_m2", chf_W_m2)
    ratio = wall_flux.value_W_m2 / chf_W_m2

    if ratio >= CHF_DRYOUT:
        return ChfAssessment(
            ratio=ratio,
            status=RankStatus.REJECTED,
            reason=(
                f"q''/CHF = {ratio:.4g} >= {CHF_DRYOUT:g}: dryout, case rejected"
            ),
        )

    if ratio > CHF_RANK_MAX:
        return ChfAssessment(
            ratio=ratio,
            status=RankStatus.SENSITIVITY_ONLY,
            reason=(
                f"q''/CHF = {ratio:.4g} is in the parametric band "
                f"({CHF_RANK_MAX:g} < q''/CHF < {CHF_DRYOUT:g}): reported as a "
                "sensitivity, not ranked"
            ),
        )

    if not wall_flux.is_rankable_basis:
        return ChfAssessment(
            ratio=ratio,
            status=RankStatus.SENSITIVITY_ONLY,
            reason=(
                f"q''/CHF = {ratio:.4g} is inside the rank band, but the flux basis "
                f"is '{wall_flux.basis.value}' with geometry_sourced="
                f"{wall_flux.geometry_sourced}: q''/CHF must be computed on the local "
                "modeled wall flux from sourced geometry (S0 Sec. 3), so the case is "
                "sensitivity-only and an average is not substituted for it"
            ),
        )

    return ChfAssessment(
        ratio=ratio,
        status=RankStatus.RANK_ELIGIBLE,
        reason=f"q''/CHF = {ratio:.4g} <= {CHF_RANK_MAX:g}: within the ranked margin",
    )


def critical_heat_flux(**_kwargs: float) -> float:
    """Obtain CHF from the registry reference correlation -- **always raises**.

    ``two_phase.chf.shah_2015`` has no executable form: its citation is ambiguous
    (two distinct 2015 Shah CHF papers) and its declared ``pr_reduced`` domain
    provably belongs to Shah (1987). Rather than attach maths whose attribution
    cannot be established, S2 leaves the entry unimplemented and makes the gap loud
    at the point of use.

    This is deliberately a *raising* function and not a missing one: a caller that
    needs CHF gets a machine-visible blocker naming the reason, instead of an
    ``AttributeError`` or, far worse, a plausible number.
    """
    entry = get(CHF_ID)
    raise NotRankEligibleError(
        f"no executable CHF correlation is available: registry entry '{entry.id}' "
        "carries no evaluate callable because its source attribution could not be "
        "established (ambiguous 'Shah (2015)' citation; declared pr_reduced domain "
        "0.0014-0.96 traces to Shah (1987), Int. J. Heat and Fluid Flow 8(4):326-335). "
        "Supply a CHF value from a sourced correlation to classify_chf_band, or treat "
        "the case as blocked. No value is invented here."
    )


# --- T3: flow-boiling HTC through the registry ----------------------------------


def flow_boiling_htc(
    *,
    mass_flux_kg_m2s: float,
    quality: float,
    wall_flux: WallHeatFlux,
    diameter_m: float,
    pressure_Pa: float,
    props: dict[str, float],
    fluid: str,
    check_domain: bool = True,
) -> float:
    """Flow-boiling HTC from ``two_phase.htc.gungor_winterton``, W/m^2/K.

    ``props`` is the mapping returned by
    :func:`orbital_thermal.fluids.saturation_properties`. With ``check_domain=True``
    (the default, and the only setting permitted on the ranking path) every call is
    range-checked against the entry's declared validity domain and raises
    ``NotRankEligibleError`` if any input is outside it -- never silently
    extrapolated (S0 Sec. 6 gate 4).

    The molar mass is converted from the CoolProp kg/mol convention to the g/mol that
    the dimensional Cooper term requires; getting that conversion wrong would shift
    the nucleate contribution by a factor of about 32, so it is done once, here.
    """
    entry = get(HTC_ID)
    if check_domain:
        assert_in_domain(
            entry,
            context="S2 flow-boiling HTC",
            G_kg_m2s=mass_flux_kg_m2s,
            q_flux_W_m2=wall_flux.value_W_m2,
            quality=quality,
            P_Pa=pressure_Pa,
            D_m=diameter_m,
        )
    return gungor_winterton_1986_htc(
        mass_flux_kg_m2s=mass_flux_kg_m2s,
        quality=quality,
        q_flux_W_m2=wall_flux.value_W_m2,
        diameter_m=diameter_m,
        rho_f=props["rho_f_kg_m3"],
        rho_g=props["rho_g_kg_m3"],
        mu_f=props["mu_f_Pa_s"],
        mu_g=props["mu_g_Pa_s"],
        k_f=props["k_f_W_mK"],
        cp_f=props["cp_f_J_kgK"],
        h_fg_J_kg=props["h_fg_J_kg"],
        p_reduced=props["p_reduced"],
        molar_mass_g_mol=props["molar_mass_kg_mol"] * 1000.0,
    )


# --- combined screening assessment ----------------------------------------------


@dataclass(frozen=True)
class AcquisitionAssessment:
    """Screening-level verdict for one acquisition (evaporator) operating point."""

    state: LoopState
    regime: RegimeAssessment
    chf: ChfAssessment | None
    htc_W_m2K: float | None
    status: RankStatus
    reasons: tuple[str, ...]
    fluid_in_htc_database: bool

    @property
    def rankable(self) -> bool:
        return self.status is RankStatus.RANK_ELIGIBLE


#: Ordering used to combine gate outcomes: the worst outcome wins.
_STATUS_SEVERITY = {
    RankStatus.RANK_ELIGIBLE: 0,
    RankStatus.SENSITIVITY_ONLY: 1,
    RankStatus.REJECTED: 2,
    RankStatus.BLOCKED: 3,
}


def _worst(*statuses: RankStatus) -> RankStatus:
    return max(statuses, key=lambda s: _STATUS_SEVERITY[s])


def assess_acquisition(
    *,
    state: LoopState,
    wall_flux: WallHeatFlux,
    mass_flux_kg_m2s: float,
    diameter_m: float,
    props: dict[str, float],
    fluid: str,
    chf_W_m2: float | None = None,
    onb_criterion: object = None,
) -> AcquisitionAssessment:
    """Run every S2 gate over one operating point and combine them.

    The combined status is the **worst** of the individual gate outcomes, so no gate
    can be outvoted by a more permissive one. ``chf_W_m2=None`` means no sourced CHF
    value was supplied; because no CHF correlation is implemented, the case is then
    **blocked** rather than assumed safe.

    ``fluid_in_htc_database`` reports whether the coolant is inside the HTC
    correlation's *fluid* database. It is surfaced rather than enforced: ammonia is
    the S0 Sec. 9.1 reference coolant and is **not** in the Gungor & Winterton (1986)
    database, and reconciling those two director-level facts is a disposition
    decision, not something this build may settle by silently de-ranking.
    """
    reasons: list[str] = []

    regime = classify_regime(state, onb_criterion=onb_criterion)
    reasons.append(regime.reason)
    status = regime.status

    in_db = fluid_in_gw86_database(fluid)
    if not in_db:
        reasons.append(
            f"'{fluid}' is not in the Gungor & Winterton (1986) fluid database "
            "(water, R-11, R-12, R-22, R-113, R-114, ethylene glycol): the HTC is "
            "outside the correlation's fluid basis even where every numeric input is "
            "in domain -- recorded for disposition, not auto-de-ranked"
        )

    if not wall_flux.is_rankable_basis:
        reasons.append(
            f"wall heat flux basis is '{wall_flux.basis.value}' "
            f"(geometry_sourced={wall_flux.geometry_sourced}); channel geometry is "
            "source-required (S0 Sec. 5), so the case cannot be ranked on it"
        )
        status = _worst(status, RankStatus.SENSITIVITY_ONLY)

    if chf_W_m2 is None:
        chf = None
        reasons.append(
            "no CHF value supplied and no sourced CHF correlation is implemented "
            "(two_phase.chf.shah_2015 attribution blocker): the CHF band cannot be "
            "evaluated, so the case is blocked rather than assumed below CHF"
        )
        status = _worst(status, RankStatus.BLOCKED)
    else:
        chf = classify_chf_band(wall_flux, chf_W_m2)
        reasons.append(chf.reason)
        status = _worst(status, chf.status)

    htc: float | None = None
    if state.is_two_phase and state.quality is not None:
        try:
            htc = flow_boiling_htc(
                mass_flux_kg_m2s=mass_flux_kg_m2s,
                quality=state.quality,
                wall_flux=wall_flux,
                diameter_m=diameter_m,
                pressure_Pa=state.pressure_Pa,
                props=props,
                fluid=fluid,
            )
        except NotRankEligibleError as exc:
            reasons.append(f"HTC not evaluated: {exc}")
            status = _worst(status, RankStatus.REJECTED)

    return AcquisitionAssessment(
        state=state,
        regime=regime,
        chf=chf,
        htc_W_m2K=htc,
        status=status,
        reasons=tuple(reasons),
        fluid_in_htc_database=in_db,
    )


__all__ = [
    "CHF_DRYOUT",
    "CHF_RANK_MAX",
    "CHF_ID",
    "HTC_ID",
    "ONB_ID",
    "AcquisitionAssessment",
    "ChfAssessment",
    "FluxBasis",
    "LoopState",
    "Regime",
    "RegimeAssessment",
    "RankStatus",
    "WallHeatFlux",
    "assess_acquisition",
    "averaged_wall_heat_flux",
    "classify_chf_band",
    "classify_regime",
    "critical_heat_flux",
    "flow_boiling_htc",
    "local_wall_heat_flux",
    "loop_state",
    "vapour_quality",
]
