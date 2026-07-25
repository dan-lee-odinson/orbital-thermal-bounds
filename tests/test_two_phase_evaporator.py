"""S2 two-phase acquisition / evaporator tests, mapped to the S0 Sec. 6 gates.

Gate coverage (S0 Sec. 6):

* **Gate 1 -- limiting case AND transition coverage.** Four separate tests, because
  S0 states the endpoint check is necessary-but-not-sufficient: (a) subcooled forced
  convection, (b) the ONB transition, (c) saturated flow boiling, (d) ``x -> 0``
  recovery to the Stage-1 single-phase coefficient.
* **Gate 3 -- pressure / quality / domain validity.** ``0 <= x <= 1``;
  ``P_triple < P < P_crit``; ``T_sat(P)`` monotonic; no blanket supercritical.
* **Gate 4 -- correlation validity ranges.** Every call range-checked, and
  ``assert_in_domain`` proven to FIRE on an out-of-range input on every axis of the
  one implemented correlation.
* **Gate 5 -- rejection / de-ranking.** All three CHF bands exercised, plus a case
  whose local flux is underivable.

Gate 2 (energy closure) and gate 6 (no regression) are not S2 tests: gate 2 needs the
condenser and the coupled solve (S3/S4), and gate 6 is the full suite itself.

Tests that need saturation properties are skipped without CoolProp; the policy gates
are deliberately property-free so they run either way.
"""

from __future__ import annotations

import math
from itertools import pairwise

import pytest

from orbital_thermal import two_phase as tp
from orbital_thermal.registry import NotRankEligibleError, assert_in_domain, get
from orbital_thermal.registry.two_phase import (
    cooper_pool_boiling_htc,
    dittus_boelter_liquid_htc,
    gungor_winterton_1986_htc,
)

try:  # CoolProp is an optional dependency; the policy gates must not need it.
    from orbital_thermal import fluids as _fluids
except ImportError:  # pragma: no cover - exercised only without CoolProp
    _fluids = None

requires_coolprop = pytest.mark.skipif(
    _fluids is None, reason="CoolProp not installed (optional dependency)"
)

#: A representative ammonia operating point, inside the declared HTC domain.
P_REF = 1.0e6  # Pa
G_REF = 300.0  # kg/m^2/s
D_REF = 3.0e-3  # m
Q_REF = 5.0e4  # W/m^2


def _props(P: float = P_REF) -> dict[str, float]:
    return _fluids.saturation_properties(P)


def _flux(q: float = Q_REF) -> tp.WallHeatFlux:
    """A local, sourced-geometry wall flux of the requested magnitude."""
    return tp.local_wall_heat_flux(
        power_W=q * 1.0e-3, wetted_area_m2=1.0e-3, geometry_sourced=True
    )


def _state(quality: float, props: dict[str, float]) -> tp.LoopState:
    h = props["h_f_J_kg"] + quality * props["h_fg_J_kg"]
    return tp.loop_state(
        pressure_Pa=P_REF,
        enthalpy_J_kg=h,
        h_f_J_kg=props["h_f_J_kg"],
        h_g_J_kg=props["h_g_J_kg"],
    )


# =============================================================================
# Gate 1 -- limiting case AND transition coverage (FOUR separate tests)
# =============================================================================


@requires_coolprop
def test_gate1a_subcooled_forced_convection_is_not_rank_eligible():
    """(a) Subcooled forced convection: classified subcooled, sensitivity-only.

    S0 Sec. 3 (F2): absent a sourced ONB criterion, a case at or below ONB is
    sensitivity-only and never rank-eligible. A subcooled state is by definition at
    or below ONB.
    """
    props = _props()
    state = _state(-0.05, props)  # enthalpy below h_f

    assert state.regime is tp.Regime.SUBCOOLED_LIQUID
    assert state.quality is None, "subcooled state must not carry a vapour quality"
    assert state.equilibrium_quality < 0.0

    verdict = tp.classify_regime(state)
    assert verdict.status is tp.RankStatus.SENSITIVITY_ONLY
    assert verdict.onb_criterion_sourced is False
    assert "onset of nucleate boiling" in verdict.reason


@requires_coolprop
def test_gate1b_onb_transition_is_resolved_and_de_ranks_the_subcooled_side():
    """(b) The ONB transition: the gate changes verdict exactly at x = 0.

    The transition itself is the object under test, not either endpoint -- S0 warns
    that a single endpoint check must not stand in for the transition.
    """
    props = _props()
    just_below = _state(-1e-6, props)
    just_above = _state(+1e-6, props)

    assert just_below.regime is tp.Regime.SUBCOOLED_LIQUID
    assert just_above.regime is tp.Regime.SATURATED_TWO_PHASE

    below = tp.classify_regime(just_below)
    above = tp.classify_regime(just_above)

    assert below.status is tp.RankStatus.SENSITIVITY_ONLY
    assert above.status is tp.RankStatus.RANK_ELIGIBLE, (
        "the saturated side of the ONB transition must be rank-eligible; the gate "
        "must discriminate across the transition, not de-rank everything"
    )


@requires_coolprop
def test_gate1c_saturated_flow_boiling_is_evaluated_and_rank_eligible():
    """(c) Saturated flow boiling: HTC evaluates and the regime gate passes."""
    props = _props()
    state = _state(0.30, props)

    assert state.regime is tp.Regime.SATURATED_TWO_PHASE
    assert state.quality == pytest.approx(0.30)
    assert tp.classify_regime(state).status is tp.RankStatus.RANK_ELIGIBLE

    htc = tp.flow_boiling_htc(
        mass_flux_kg_m2s=G_REF,
        quality=state.quality,
        wall_flux=_flux(),
        diameter_m=D_REF,
        pressure_Pa=P_REF,
        props=props,
        fluid="ammonia",
    )
    assert math.isfinite(htc) and htc > 0.0

    single_phase = dittus_boelter_liquid_htc(
        mass_flux_kg_m2s=G_REF,
        quality=state.quality,
        diameter_m=D_REF,
        rho_f=props["rho_f_kg_m3"],
        mu_f=props["mu_f_Pa_s"],
        k_f=props["k_f_W_mK"],
        cp_f=props["cp_f_J_kgK"],
    )
    assert htc > single_phase, "boiling must exceed the liquid-only coefficient"

    # The convective enhancement must be real, not just the additive nucleate term.
    # With E = 1 and S <= 1 the correlation could only reach alpha_L + alpha_nb, so
    # requiring a STRICT excess over that sum is exactly the assertion that E > 1.
    # (A weaker "htc > alpha_L" check passes even with the enhancement disabled --
    # the mutation witness in scripts/witness_s2_checks.py caught that.)
    nucleate = cooper_pool_boiling_htc(
        p_reduced=props["p_reduced"],
        molar_mass_g_mol=props["molar_mass_kg_mol"] * 1000.0,
        q_flux_W_m2=Q_REF,
    )
    assert htc > single_phase + nucleate, (
        "the two-phase coefficient must exceed the unenhanced liquid term plus the "
        "full nucleate term; that excess can only come from E > 1, so this fails if "
        "the convective enhancement is ever disabled"
    )


@requires_coolprop
def test_gate1d_x_to_zero_recovers_the_single_phase_limit():
    """(d) ``x -> 0`` recovery -- exact to GW86's own base, banded against Stage 1.

    Two distinct claims, kept separate because only the first is exact:

    1. **Exact.** As ``x -> 0`` with ``q'' -> 0``, GW86 collapses to its own
       single-phase convective base (Dittus-Boelter): ``E -> 1``, the nucleate term
       vanishes with ``q''^0.67``. Asserted to floating-point tolerance.
    2. **Banded, and NOT exact.** Stage-1 ``pumped_loop`` uses **Gnielinski**, not
       Dittus-Boelter, so exact recovery to the Stage-1 number is not expected and
       must not be manufactured. The two agree to within ~1% at Re ~ 1.1e4, widening
       to ~10% near Re ~ 4.5e3. This is a recorded correlation difference, not a
       tolerance chosen to make a test pass -- and it is Reynolds-dependent, so the
       band is asserted per-Reynolds rather than as one flattering global number.
    """
    from orbital_thermal import pumped_loop as pl

    props = _props()

    # 1. Exact recovery to GW86's own single-phase base.
    for G in (100.0, 300.0, 500.0):
        gw = gungor_winterton_1986_htc(
            mass_flux_kg_m2s=G,
            quality=0.0,
            q_flux_W_m2=0.0,
            diameter_m=D_REF,
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
        db = dittus_boelter_liquid_htc(
            mass_flux_kg_m2s=G,
            quality=0.0,
            diameter_m=D_REF,
            rho_f=props["rho_f_kg_m3"],
            mu_f=props["mu_f_Pa_s"],
            k_f=props["k_f_W_mK"],
            cp_f=props["cp_f_J_kgK"],
        )
        assert gw == pytest.approx(db, rel=1e-12), (
            f"at G={G}, x=0, q''=0 the GW86 form must reduce exactly to its "
            "Dittus-Boelter base"
        )

    # 2. Banded agreement with the Stage-1 single-phase coefficient.
    pr = props["cp_f_J_kgK"] * props["mu_f_Pa_s"] / props["k_f_W_mK"]
    for G, tol in ((200.0, 0.11), (300.0, 0.05), (500.0, 0.01)):
        re = G * D_REF / props["mu_f_Pa_s"]
        assert re > 4000.0, "band is claimed for fully turbulent flow only"
        db = dittus_boelter_liquid_htc(
            mass_flux_kg_m2s=G,
            quality=0.0,
            diameter_m=D_REF,
            rho_f=props["rho_f_kg_m3"],
            mu_f=props["mu_f_Pa_s"],
            k_f=props["k_f_W_mK"],
            cp_f=props["cp_f_J_kgK"],
        )
        stage1 = pl.heat_transfer_coefficient(
            pl.nusselt(re, pr), props["k_f_W_mK"], D_REF
        )
        assert db == pytest.approx(stage1, rel=tol), (
            f"at Re={re:.0f} the x->0 limit and the Stage-1 coefficient must agree "
            f"within {tol:.0%}"
        )


@requires_coolprop
def test_gate1d_recovery_is_not_claimed_near_the_laminar_transition():
    """The recovery band is a turbulent claim, and is recorded as failing below it.

    Near Re ~ 2300 Stage-1 correctly switches to the laminar Nusselt number while
    Dittus-Boelter is simply out of its own validity range. Asserting the mismatch
    keeps the limitation honest: without this test the banded claim above could be
    read as holding everywhere.
    """
    from orbital_thermal import pumped_loop as pl

    props = _props()
    G = 100.0
    re = G * D_REF / props["mu_f_Pa_s"]
    assert re < 2300.0, "this test is about the laminar/transition region"

    db = dittus_boelter_liquid_htc(
        mass_flux_kg_m2s=G,
        quality=0.0,
        diameter_m=D_REF,
        rho_f=props["rho_f_kg_m3"],
        mu_f=props["mu_f_Pa_s"],
        k_f=props["k_f_W_mK"],
        cp_f=props["cp_f_J_kgK"],
    )
    pr = props["cp_f_J_kgK"] * props["mu_f_Pa_s"] / props["k_f_W_mK"]
    stage1 = pl.heat_transfer_coefficient(pl.nusselt(re, pr), props["k_f_W_mK"], D_REF)

    assert db > 2.0 * stage1, (
        "below the turbulent threshold the two coefficients are expected to diverge "
        "strongly; if they ever agree here, the recovery claim needs re-deriving"
    )


# =============================================================================
# Gate 3 -- pressure / quality / domain validity
# =============================================================================


def test_gate3_quality_outside_zero_one_is_rejected():
    """``0 <= x <= 1`` is enforced, not clamped."""
    h_f, h_fg = 100.0, 1000.0
    assert tp.vapour_quality(h_f + 0.5 * h_fg, h_f, h_fg) == pytest.approx(0.5)

    with pytest.raises(ValueError, match=r"outside the physical range"):
        tp.vapour_quality(h_f - 1.0, h_f, h_fg)  # subcooled -> x < 0
    with pytest.raises(ValueError, match=r"outside the physical range"):
        tp.vapour_quality(h_f + 2.0 * h_fg, h_f, h_fg)  # superheated -> x > 1


def test_gate3_loop_state_classifies_instead_of_clamping():
    """The three regimes stay distinguishable; nothing is clamped into silence."""
    h_f, h_g = 100.0, 1100.0
    assert tp.loop_state(
        pressure_Pa=1e6, enthalpy_J_kg=50.0, h_f_J_kg=h_f, h_g_J_kg=h_g
    ).regime is tp.Regime.SUBCOOLED_LIQUID
    assert tp.loop_state(
        pressure_Pa=1e6, enthalpy_J_kg=600.0, h_f_J_kg=h_f, h_g_J_kg=h_g
    ).regime is tp.Regime.SATURATED_TWO_PHASE
    assert tp.loop_state(
        pressure_Pa=1e6, enthalpy_J_kg=5000.0, h_f_J_kg=h_f, h_g_J_kg=h_g
    ).regime is tp.Regime.SUPERHEATED_VAPOUR


@requires_coolprop
def test_gate3_pressure_bounds_triple_to_critical_are_enforced():
    """``P_triple < P < P_crit``: outside, there is no saturation state."""
    p_crit = _fluids.critical_pressure("Ammonia")
    p_triple = _fluids.triple_pressure("Ammonia")

    with pytest.raises(ValueError, match=r"critical pressure"):
        _fluids.saturation_temperature(p_crit * 1.01)
    with pytest.raises(ValueError, match=r"triple-point pressure"):
        _fluids.saturation_temperature(p_triple * 0.5)

    # Just inside the band still evaluates.
    assert _fluids.saturation_temperature(p_crit * 0.5) > 0.0


@requires_coolprop
def test_gate3_no_blanket_supercritical_treatment():
    """A supercritical state raises rather than being treated as two-phase.

    This is the B0 CO2 straddle discipline carried into Stage 2: the model must not
    quietly extend a saturation curve past the critical point.

    The second half is the load-bearing part. The registry's declared water domain
    tops out at 647.1 K while the pinned backend's critical temperature is 647.096 K,
    so there is a ~4 mK window that the **declared** domain admits but which is
    genuinely supercritical. A guard that only checked the declared domain would let
    that window through; this proves the backend-bounds guard closes it.
    """
    t_crit_nh3 = _fluids.critical_temperature("Ammonia")
    with pytest.raises(ValueError):
        _fluids.assert_two_phase_domain(t_crit_nh3 + 1.0, "Ammonia")
    with pytest.raises(ValueError):
        _fluids.surface_tension(t_crit_nh3 + 1.0, "Ammonia")

    lo, hi = _fluids.two_phase_domain_K("Water")
    t_crit_h2o = _fluids.critical_temperature("Water")
    assert lo < t_crit_h2o < hi, (
        "this test relies on the declared water domain extending past the critical "
        "temperature; if the declared domain is ever tightened, retire this case"
    )
    straddle = 0.5 * (t_crit_h2o + hi)  # inside the declared domain, above T_crit
    with pytest.raises(ValueError, match=r"critical temperature"):
        _fluids.assert_two_phase_domain(straddle, "Water")


@requires_coolprop
def test_gate3_saturation_temperature_is_monotonic_in_pressure():
    """``T_sat(P)`` is strictly increasing across the registered domain."""
    pressures = [2.0e5 * k for k in range(1, 26)]  # 0.2 -> 5.0 MPa
    temps = [_fluids.saturation_temperature(p) for p in pressures]
    assert all(b > a for a, b in pairwise(temps)), "T_sat(P) must be monotonic"


@requires_coolprop
def test_gate3_saturation_temperature_inverts_saturation_pressure():
    """``T_sat`` really is the inverse of the Stage-1 ``saturation_pressure``."""
    for T in (250.0, 300.0, 350.0):
        assert _fluids.saturation_temperature(
            _fluids.saturation_pressure(T)
        ) == pytest.approx(T, rel=1e-9)


@requires_coolprop
def test_gate3_unregistered_coolant_is_source_gated():
    """S0 Sec. 9.1 admits ammonia and water; anything else is source-gated."""
    with pytest.raises(_fluids.SourceGatedFluidError, match=r"source-gated"):
        _fluids.two_phase_domain_K("CO2")
    assert _fluids.two_phase_domain_K("Ammonia") == (195.5, 405.4)


# =============================================================================
# Gate 4 -- correlation validity ranges (prove the guard FIRES on every axis)
# =============================================================================


@pytest.mark.parametrize(
    "axis,bad_value",
    [
        ("G_kg_m2s", 5000.0),  # above 600
        ("G_kg_m2s", 1.0),  # below 10
        ("q_flux_W_m2", 1.0e7),  # above 2.4e5
        ("quality", 0.9999),  # above 0.997
        ("quality", 0.0001),  # below 0.002
        ("P_Pa", 5.0e6),  # above 1.6e6
        ("P_Pa", 1.0e4),  # below 1.9e5
        ("D_m", 0.5),  # above 32 mm
        ("D_m", 1.0e-4),  # below 1.224 mm
    ],
)
def test_gate4_assert_in_domain_fires_on_every_axis(axis, bad_value):
    """``assert_in_domain`` raises for an out-of-range value on each declared axis.

    A checker that has never failed is not a check. Every axis of the one implemented
    correlation is driven out of range and the guard is required to fire.
    """
    entry = get(tp.HTC_ID)
    with pytest.raises(NotRankEligibleError, match=r"outside its validity domain"):
        assert_in_domain(entry, **{axis: bad_value})


@requires_coolprop
def test_gate4_out_of_domain_htc_call_is_rejected_not_extrapolated():
    """A ranking-path HTC call outside the domain raises instead of extrapolating."""
    props = _props()
    with pytest.raises(NotRankEligibleError, match=r"outside its validity domain"):
        tp.flow_boiling_htc(
            mass_flux_kg_m2s=5000.0,  # far above the declared 600 kg/m^2/s
            quality=0.3,
            wall_flux=_flux(),
            diameter_m=D_REF,
            pressure_Pa=P_REF,
            props=props,
            fluid="ammonia",
        )


@requires_coolprop
def test_gate4_in_domain_htc_call_is_accepted():
    """The guard is not vacuous: an in-domain call must still evaluate."""
    assert (
        tp.flow_boiling_htc(
            mass_flux_kg_m2s=G_REF,
            quality=0.3,
            wall_flux=_flux(),
            diameter_m=D_REF,
            pressure_Pa=P_REF,
            props=_props(),
            fluid="ammonia",
        )
        > 0.0
    )


def test_gate4_no_sourced_chf_evaluator_exists():
    """Asking the registry for CHF raises a blocker naming the reason.

    The gap is loud at the point of use rather than silently absent -- and above all
    it does not return a plausible number.
    """
    with pytest.raises(NotRankEligibleError, match=r"Shah \(1987\)"):
        tp.critical_heat_flux()


# =============================================================================
# Gate 5 -- rejection / de-ranking
# =============================================================================


def test_gate5_chf_band_at_or_above_one_is_rejected():
    """``q''/CHF >= 1`` -> dryout -> rejected."""
    verdict = tp.classify_chf_band(_flux(1.0e5), chf_W_m2=1.0e5)
    assert verdict.ratio == pytest.approx(1.0)
    assert verdict.status is tp.RankStatus.REJECTED
    assert "dryout" in verdict.reason


def test_gate5_chf_band_between_half_and_one_is_sensitivity_not_ranked():
    """``0.5 < q''/CHF < 1`` -> reported as a sensitivity, excluded from ranking."""
    verdict = tp.classify_chf_band(_flux(7.5e4), chf_W_m2=1.0e5)
    assert verdict.ratio == pytest.approx(0.75)
    assert verdict.status is tp.RankStatus.SENSITIVITY_ONLY
    assert verdict.status is not tp.RankStatus.RANK_ELIGIBLE, "must not be ranked"


def test_gate5_chf_band_at_or_below_half_is_rank_eligible():
    """``q''/CHF <= 0.5`` -> rank-eligible (director ruling 9.5)."""
    verdict = tp.classify_chf_band(_flux(5.0e4), chf_W_m2=1.0e5)
    assert verdict.ratio == pytest.approx(0.5)
    assert verdict.status is tp.RankStatus.RANK_ELIGIBLE


def test_gate5_band_boundaries_are_closed_on_the_conservative_side():
    """Exactly 0.5 ranks and exactly 1.0 rejects -- the boundaries are not ambiguous."""
    assert tp.classify_chf_band(_flux(5.0e4), 1.0e5).status is tp.RankStatus.RANK_ELIGIBLE
    assert (
        tp.classify_chf_band(_flux(5.0001e4), 1.0e5).status
        is tp.RankStatus.SENSITIVITY_ONLY
    )
    assert tp.classify_chf_band(_flux(1.0e5), 1.0e5).status is tp.RankStatus.REJECTED


def test_gate5_underivable_local_flux_is_never_silently_averaged():
    """An average flux cannot reach a ranked case, however small the CHF ratio.

    S0 Sec. 3: ``q''`` must be the local modeled wall flux from sourced geometry. A
    section- or chip-average is permitted only when explicitly named and categorised,
    and is never substituted for a local flux.
    """
    averaged = tp.averaged_wall_heat_flux(
        power_W=50.0, area_m2=1.0e-3, basis=tp.FluxBasis.CHIP_AVERAGE
    )
    assert averaged.is_rankable_basis is False

    verdict = tp.classify_chf_band(averaged, chf_W_m2=1.0e7)  # ratio 0.005, deep in band
    assert verdict.ratio < tp.CHF_RANK_MAX
    assert verdict.status is tp.RankStatus.SENSITIVITY_ONLY, (
        "a chip-average flux must not produce a rank-eligible band even when the "
        "ratio is far inside the ranked margin"
    )
    assert "local modeled wall flux" in verdict.reason


def test_gate5_unsourced_geometry_de_ranks_a_local_flux():
    """Local basis is not enough: the geometry behind it must be sourced."""
    unsourced = tp.local_wall_heat_flux(
        power_W=50.0, wetted_area_m2=1.0e-3, geometry_sourced=False
    )
    assert unsourced.is_rankable_basis is False
    assert (
        tp.classify_chf_band(unsourced, chf_W_m2=1.0e7).status
        is tp.RankStatus.SENSITIVITY_ONLY
    )


def test_gate5_averaged_flux_helper_refuses_to_masquerade_as_local():
    """The average-flux constructor cannot be used to mint a 'local' flux."""
    with pytest.raises(ValueError, match=r"requires an averaging basis"):
        tp.averaged_wall_heat_flux(
            power_W=50.0, area_m2=1.0e-3, basis=tp.FluxBasis.LOCAL_SOURCED
        )


@requires_coolprop
def test_gate5_missing_chf_blocks_the_case_rather_than_assuming_it_is_safe():
    """With no CHF value and no sourced correlation, the case is blocked."""
    props = _props()
    verdict = tp.assess_acquisition(
        state=_state(0.3, props),
        wall_flux=_flux(),
        mass_flux_kg_m2s=G_REF,
        diameter_m=D_REF,
        props=props,
        fluid="ammonia",
        chf_W_m2=None,
    )
    assert verdict.status is tp.RankStatus.BLOCKED
    assert verdict.rankable is False
    assert any("blocked rather than assumed below CHF" in r for r in verdict.reasons)


@requires_coolprop
def test_gate5_combined_assessment_takes_the_worst_gate_outcome():
    """No gate can be outvoted by a more permissive one."""
    props = _props()
    # Saturated (rank-eligible regime) but in dryout -> the CHF rejection must win.
    verdict = tp.assess_acquisition(
        state=_state(0.3, props),
        wall_flux=_flux(),
        mass_flux_kg_m2s=G_REF,
        diameter_m=D_REF,
        props=props,
        fluid="ammonia",
        chf_W_m2=Q_REF * 0.5,  # ratio 2.0 -> dryout
    )
    assert verdict.regime.status is tp.RankStatus.RANK_ELIGIBLE
    assert verdict.status is tp.RankStatus.REJECTED


@requires_coolprop
def test_gate5_superheated_state_is_rejected_outright():
    """Past x = 1 the wall is dry and the wetted-wall HTC is not valid."""
    props = _props()
    assert (
        tp.classify_regime(_state(1.2, props)).status is tp.RankStatus.REJECTED
    )


# =============================================================================
# Physics sanity of the implemented correlation
# =============================================================================


@requires_coolprop
def test_gw86_htc_increases_with_quality_and_with_mass_flux():
    """Monotonic in the two variables whose direction is unambiguous."""
    props = _props()
    kw = dict(
        q_flux_W_m2=Q_REF,
        diameter_m=D_REF,
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
    by_quality = [
        gungor_winterton_1986_htc(mass_flux_kg_m2s=G_REF, quality=x, **kw)
        for x in (0.05, 0.2, 0.4, 0.6)
    ]
    assert all(b > a for a, b in pairwise(by_quality))

    by_flux = [
        gungor_winterton_1986_htc(mass_flux_kg_m2s=G, quality=0.3, **kw)
        for G in (50.0, 150.0, 300.0, 500.0)
    ]
    assert all(b > a for a, b in pairwise(by_flux))


def test_cooper_term_matches_the_independently_cross_checked_source():
    """Cooper (1984) reproduced from two independent sources, checked by hand.

    ``alpha_nb = 55 p_r^0.12 (-0.4343 ln p_r)^-0.55 M^-0.5 q''^0.67``, rebuilt here
    factor by factor to pin the leading constant and every exponent independently of
    the implementation.

    The literal ``0.4343`` is used exactly as printed in both sources and is
    deliberately **not** replaced by ``1/ln(10) = 0.43429448...``. The two differ in
    the fifth significant figure, which shifts the result by ~7e-6 relative -- small,
    but it would be a silent edit of a published constant, so the printed value
    stands and this test locks it in.
    """
    from orbital_thermal.registry.two_phase import cooper_pool_boiling_htc

    got = cooper_pool_boiling_htc(
        p_reduced=0.1, molar_mass_g_mol=18.0, q_flux_W_m2=1.0e5
    )
    expected = (
        55.0
        * (0.1**0.12)
        * ((-0.4343 * math.log(0.1)) ** -0.55)
        * (18.0**-0.5)
        * (1.0e5**0.67)
    )
    assert got == pytest.approx(expected, rel=1e-12)
    assert got == pytest.approx(2.2e4, rel=5e-3)  # ~2.2e4 W/m^2/K for water

    # The published 0.4343 is not silently "corrected" to 1/ln(10).
    idealised = (
        55.0
        * (0.1**0.12)
        * 1.0  # (-log10(0.1))^-0.55 == 1 exactly
        * (18.0**-0.5)
        * (1.0e5**0.67)
    )
    assert got != pytest.approx(idealised, rel=1e-9), (
        "the implementation must use the printed constant 0.4343, not the exact "
        "1/ln(10); if these ever agree, someone has edited the published constant"
    )


def test_martinelli_parameter_falls_with_quality():
    """``X_tt`` decreases as quality rises, so the convective enhancement grows."""
    from orbital_thermal.registry.two_phase import martinelli_xtt

    xs = [martinelli_xtt(x, 600.0, 8.0, 1.3e-4, 9e-6) for x in (0.05, 0.2, 0.5, 0.8)]
    assert all(b < a for a, b in pairwise(xs))
