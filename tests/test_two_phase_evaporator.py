"""S2 two-phase acquisition / evaporator tests, mapped to the S0 Sec. 6 gates.

Gate coverage (S0 Sec. 6):

* **Gate 1 -- limiting case AND transition coverage.** Four separate tests, because
  S0 states the endpoint check is necessary-but-not-sufficient. The ``x -> 0`` leg was
  rebuilt after OTB-G001 F-07: it now runs on a **domain-valid path** through the
  guarded wrapper, and records that the correlation does **not** recover its
  single-phase base anywhere inside the declared domain -- rather than reaching
  agreement by also sending ``q'' -> 0`` at points the domain excludes.
* **Gate 3 -- pressure / quality / domain validity.**
* **Gate 4 -- correlation validity ranges**, with the guard proven to fire on every axis.
* **Gate 5 -- rejection / de-ranking**, including the CHF bands and flux basis.

Gate 2 (energy closure) and gate 6 (no regression) are not S2 tests.

The OTB-G001 findings each have a named test below: F-01 (evaluated ONB criterion),
F-02 (validated CHF result), F-05 (bound saturation state), F-07 (domain-valid
limiting case), F-09 (no guard bypass), F-10 (backend pin enforced). F-03/F-04/F-06 and
DEBTS D-9 are covered class-level in ``test_applicability_enforcement.py``.
"""

from __future__ import annotations

import math
from itertools import pairwise

import pytest

from orbital_thermal import two_phase as tp
from orbital_thermal.registry import NotRankEligibleError, assert_in_domain, get
from orbital_thermal.registry.applicability import Axis, Consequence
from orbital_thermal.registry.two_phase import (
    cooper_pool_boiling_htc,
    dittus_boelter_liquid_htc,
    gungor_winterton_1986_htc,
    shah_1987_bo_zero,
    shah_1987_fx,
    shah_1987_Y,
)

try:  # CoolProp is an optional dependency; the policy gates must not need it.
    from orbital_thermal import fluids as _fluids
except ImportError:  # pragma: no cover - exercised only without CoolProp
    _fluids = None

requires_coolprop = pytest.mark.skipif(
    _fluids is None, reason="CoolProp not installed (optional dependency)"
)

#: A representative operating point, inside both correlations' declared domains.
#: WATER is used where a rank-eligible case is needed: it is in the Gungor & Winterton
#: seven-fluid database. Ammonia -- the project's reference coolant -- is not, which is
#: the subject of its own tests.
P_REF = 1.0e6  # Pa
G_REF = 500.0  # kg/m^2/s
D_REF = 1.0e-2  # m
Q_REF = 1.0e5  # W/m^2
FLUID = "Water"

# GW86 declared numeric domain (provenance-unestablished, but enforced).
X_MIN, X_MAX = 0.002, 0.997
Q_MIN, Q_MAX = 2.0e3, 2.4e5


def _state(fluid: str = FLUID, P: float = P_REF):
    return _fluids.saturation_state(P, fluid)


def _geometry(**kw) -> tp.ChannelGeometry:
    base = dict(
        shape="round_tube",
        hydraulic_diameter_m=D_REF,
        orientation="vertical_upflow",
        heated_length_m=1.0,
        sourced=True,
    )
    base.update(kw)
    return tp.ChannelGeometry(**base)


def _flux(q: float = Q_REF) -> tp.WallHeatFlux:
    return tp.local_wall_heat_flux(
        power_W=q * 1.0e-3, wetted_area_m2=1.0e-3, geometry_sourced=True
    )


def _loop(quality: float, state) -> tp.LoopState:
    return tp.loop_state_from(
        state, enthalpy_J_kg=state.h_f_J_kg + quality * state.h_fg_J_kg
    )


def _chf(state, geometry=None, **kw) -> tp.ChfResult:
    return tp.critical_heat_flux(
        state=state,
        geometry=geometry or _geometry(),
        mass_flux_kg_m2s=kw.pop("mass_flux_kg_m2s", G_REF),
        inlet_quality=kw.pop("inlet_quality", -0.1),
        critical_quality=kw.pop("critical_quality", 0.3),
        **kw,
    )


def _db_base(state, *, mass_flux_kg_m2s: float, quality: float) -> float:
    return dittus_boelter_liquid_htc(
        mass_flux_kg_m2s=mass_flux_kg_m2s,
        quality=quality,
        diameter_m=D_REF,
        rho_f=state.rho_f_kg_m3,
        mu_f=state.mu_f_Pa_s,
        k_f=state.k_f_W_mK,
        cp_f=state.cp_f_J_kgK,
    )


# =============================================================================
# Gate 1 -- limiting case AND transition coverage (FOUR separate tests)
# =============================================================================


@requires_coolprop
def test_gate1a_subcooled_forced_convection_is_not_rank_eligible():
    """(a) Subcooled forced convection: classified subcooled, sensitivity-only."""
    state = _state()
    loop = _loop(-0.05, state)

    assert loop.regime is tp.Regime.SUBCOOLED_LIQUID
    assert loop.quality is None
    assert loop.equilibrium_quality < 0.0

    verdict = tp.classify_regime(loop, fluid=FLUID)
    assert verdict.status is tp.RankStatus.SENSITIVITY_ONLY
    assert verdict.onb_evaluated is False
    assert "onset of nucleate boiling" in verdict.reason


@requires_coolprop
def test_gate1b_the_transition_is_the_bulk_saturation_crossing_and_says_so():
    """(b) The transition at x = 0 -- named for what it actually is (F-01).

    The gate changes verdict exactly at the bulk-equilibrium saturation crossing. The
    review's point was not that this boundary is uninteresting but that calling it an
    *onset-of-nucleate-boiling* transition overstated it: subcooled boiling can occur
    while equilibrium quality is negative, and saturated liquid at x = 0 is not proof
    that ONB has been crossed. The reason string must therefore not claim ONB.
    """
    state = _state()
    below, above = _loop(-1e-6, state), _loop(+1e-6, state)

    assert below.regime is tp.Regime.SUBCOOLED_LIQUID
    assert above.regime is tp.Regime.SATURATED_TWO_PHASE

    v_below = tp.classify_regime(below, fluid=FLUID)
    v_above = tp.classify_regime(above, fluid=FLUID)

    assert v_below.status is tp.RankStatus.SENSITIVITY_ONLY
    assert v_above.status is tp.RankStatus.RANK_ELIGIBLE

    assert "bulk-equilibrium" in v_above.reason
    assert "not an evaluated" in v_above.reason, (
        "with no sourced ONB criterion the saturated side must be described as the "
        "bulk-equilibrium crossing, not as an established ONB transition (F-01)"
    )


@requires_coolprop
def test_gate1c_saturated_flow_boiling_is_evaluated_and_rank_eligible():
    """(c) Saturated flow boiling: HTC evaluates and the regime gate passes."""
    state = _state()
    loop = _loop(0.30, state)

    assert loop.regime is tp.Regime.SATURATED_TWO_PHASE
    assert loop.quality == pytest.approx(0.30)
    assert tp.classify_regime(loop, fluid=FLUID).status is tp.RankStatus.RANK_ELIGIBLE

    htc = tp.flow_boiling_htc(
        mass_flux_kg_m2s=G_REF,
        quality=loop.quality,
        wall_flux=_flux(),
        geometry=_geometry(),
        state=state,
        loop=loop,
    )
    assert math.isfinite(htc) and htc > 0.0

    single_phase = _db_base(state, mass_flux_kg_m2s=G_REF, quality=loop.quality)
    nucleate = cooper_pool_boiling_htc(
        p_reduced=state.p_reduced,
        molar_mass_g_mol=state.molar_mass_g_mol,
        q_flux_W_m2=Q_REF,
    )
    # A strict excess over alpha_L + alpha_nb is reachable only if E > 1, so this
    # fails if the convective enhancement is ever disabled. A weaker
    # "htc > alpha_L" check passes even with E = 1 -- the mutation witness caught that.
    assert htc > single_phase + nucleate


@requires_coolprop
def test_gate1d_x_to_zero_on_a_domain_valid_path_does_not_reach_the_base():
    """(d) ``x -> 0`` recovery, rebuilt on a DOMAIN-VALID path (OTB-G001 F-07).

    The previous version of this test reached the single-phase base only by *also*
    sending ``q'' -> 0``, and evaluated at ``x = 0``, ``q'' = 0`` -- both outside the
    declared domain, which starts at 0.002 and 2000 W/m^2 -- by calling the unguarded
    evaluator directly. It could not establish a ranked-path limiting case.

    What is actually true, measured through the **guarded** wrapper at the domain's own
    lower edge: the correlation does **not** recover its single-phase base anywhere
    inside the declared domain. At the lower corner it still sits ~1.2x above it, and
    the excess grows with quality and heat flux. That is recorded here as the result,
    not engineered away.
    """
    state = _state()
    geometry = _geometry()

    corner_loop = _loop(X_MIN, state)
    htc = tp.flow_boiling_htc(
        mass_flux_kg_m2s=600.0,  # top of the declared G range -> most turbulent
        quality=X_MIN,
        wall_flux=_flux(Q_MIN),
        geometry=geometry,
        state=state,
        loop=corner_loop,
    )
    base = _db_base(state, mass_flux_kg_m2s=600.0, quality=X_MIN)
    ratio = htc / base

    assert ratio > 1.0, "boiling never reduces transport below the liquid-only base"
    assert 1.1 < ratio < 1.5, (
        f"at the domain's lower corner the ratio is {ratio:.4f}; the correlation "
        "approaches but does not reach its single-phase base inside the declared "
        "domain. This band records the measured behaviour -- if it moves, the "
        "limiting-case claim must be re-derived, not the band re-fitted"
    )


@requires_coolprop
def test_gate1d_the_excess_over_the_base_falls_monotonically_toward_the_corner():
    """The approach to the single-phase base is monotone, so 'x -> 0' is meaningful.

    Establishing the *direction* is what the limiting case can honestly claim on a
    domain-valid path: the excess shrinks as quality and heat flux fall toward the
    domain's lower edge, without ever reaching unity inside the domain.
    """
    state = _state()
    geometry = _geometry()
    ratios = []
    for quality in (0.30, 0.10, 0.02, X_MIN):
        htc = tp.flow_boiling_htc(
            mass_flux_kg_m2s=600.0,
            quality=quality,
            wall_flux=_flux(Q_MIN),
            geometry=geometry,
            state=state,
            loop=_loop(quality, state),
        )
        ratios.append(htc / _db_base(state, mass_flux_kg_m2s=600.0, quality=quality))

    assert all(b < a for a, b in pairwise(ratios)), (
        f"the excess over the single-phase base must fall as x -> x_min; got {ratios}"
    )
    assert ratios[-1] > 1.0, "and must not reach the base inside the declared domain"


@requires_coolprop
def test_gate1d_the_analytic_zero_limit_is_recorded_as_out_of_domain_only():
    """The exact ``x=0, q''=0`` collapse is an analytic property, not ranked evidence.

    It is retained because it is a real and useful property of the formula -- ``E -> 1``
    and the nucleate term vanishes with ``q''^0.67`` -- but it is evaluated through the
    **unguarded** low-level evaluator and labelled out-of-domain, so it can never again
    be mistaken for the domain-valid limiting case that S0 Sec. 6 gate 1 requires.
    """
    state = _state()

    # Explicitly outside the declared domain: this is why the guarded path refuses it.
    entry = get(tp.HTC_ID)
    with pytest.raises(NotRankEligibleError):
        assert_in_domain(entry, quality=0.0, q_flux_W_m2=0.0)

    gw = gungor_winterton_1986_htc(
        mass_flux_kg_m2s=G_REF,
        quality=0.0,
        q_flux_W_m2=0.0,
        diameter_m=D_REF,
        rho_f=state.rho_f_kg_m3,
        rho_g=state.rho_g_kg_m3,
        mu_f=state.mu_f_Pa_s,
        mu_g=state.mu_g_Pa_s,
        k_f=state.k_f_W_mK,
        cp_f=state.cp_f_J_kgK,
        h_fg_J_kg=state.h_fg_J_kg,
        p_reduced=state.p_reduced,
        molar_mass_g_mol=state.molar_mass_g_mol,
    )
    assert gw == pytest.approx(
        _db_base(state, mass_flux_kg_m2s=G_REF, quality=0.0), rel=1e-12
    )


# =============================================================================
# F-01 -- an ONB criterion must be typed and EVALUATED, not merely present
# =============================================================================


class _StubOnb(tp.OnbCriterion):
    """A test double that records whether it was actually called."""

    valid_fluids = frozenset({"water"})
    citation = "test stub -- not a sourced criterion"

    def __init__(self, above: bool):
        self.above = above
        self.calls = 0

    def evaluate(self, *, wall_flux_W_m2, state, quality):
        self.calls += 1
        return tp.OnbResult(
            above_onb=self.above,
            incipient_flux_W_m2=1234.0,
            detail=f"stub says above_onb={self.above}",
        )


@requires_coolprop
@pytest.mark.parametrize("junk", ["banana", object(), 0.0, 1, []])
def test_f01_a_non_criterion_object_is_not_treated_as_a_sourced_criterion(junk):
    """Object presence is not evidence (OTB-G001 F-01).

    Before the fix ``onb_criterion="banana"`` set ``onb_criterion_sourced=True`` and
    the object was never called or interpreted.
    """
    state = _state()
    verdict = tp.classify_regime(_loop(-0.05, state), onb_criterion=junk, fluid=FLUID)
    assert verdict.onb_evaluated is False
    assert verdict.onb_result is None
    assert "No sourced ONB criterion is implemented" in verdict.reason


@requires_coolprop
def test_f01_a_typed_criterion_is_actually_called():
    """A real criterion is evaluated, and its result reaches the verdict."""
    state = _state()
    criterion = _StubOnb(above=True)
    verdict = tp.classify_regime(
        _loop(-0.05, state),
        onb_criterion=criterion,
        fluid=FLUID,
        wall_flux_W_m2=Q_REF,
        saturation_state=state,
    )
    assert criterion.calls == 1, "the criterion must be evaluated, not merely present"
    assert verdict.onb_evaluated is True
    assert verdict.onb_result is not None and verdict.onb_result.above_onb is True
    assert "ABOVE onset of nucleate boiling" in verdict.reason
    # Still not rank-eligible: subcooled boiling is outside the ranked regime.
    assert verdict.status is tp.RankStatus.SENSITIVITY_ONLY


@requires_coolprop
def test_f01_a_criterion_not_valid_for_the_fluid_is_not_used():
    """A water-only criterion must not be applied to ammonia (DEBTS D-3)."""
    state = _state("Ammonia")
    criterion = _StubOnb(above=True)
    verdict = tp.classify_regime(
        _loop(-0.05, state),
        onb_criterion=criterion,
        fluid="Ammonia",
        wall_flux_W_m2=Q_REF,
        saturation_state=state,
    )
    assert criterion.calls == 0
    assert verdict.onb_evaluated is False


def test_f01_the_base_criterion_refuses_to_pretend_it_evaluates():
    with pytest.raises(NotImplementedError):
        tp.OnbCriterion().evaluate(wall_flux_W_m2=1.0, state=None, quality=0.1)


# =============================================================================
# F-02 -- CHF must be a validated, sourced result, never a naked float
# =============================================================================


@requires_coolprop
def test_f02_a_naked_float_is_rejected_by_type():
    """OTB-G001 F-02: any positive number used to carry a case to RANK_ELIGIBLE."""
    for naked in (1.0e5, 1.0e9, 1):
        with pytest.raises(TypeError, match=r"requires a ChfResult"):
            tp.classify_chf_band(_flux(), naked)


@requires_coolprop
def test_f02_a_chf_result_binds_its_evidence():
    """The result carries value, source, domain, fluid, geometry and provenance."""
    state = _state()
    chf = _chf(state)
    assert chf.value_W_m2 > 0.0
    assert chf.correlation_id == "two_phase.chf.shah_1987"
    assert "Shah" in chf.citation and "8(4)" in chf.citation
    assert chf.locator.strip()
    assert chf.fluid == FLUID
    assert chf.geometry == "round_tube"
    assert set(chf.evaluated_domain) >= {"pr_reduced", "D_m", "G_kg_m2s"}
    assert chf.gravity_m_s2 > 0.0
    assert chf.is_sourced is True


@requires_coolprop
def test_f02_unsourced_geometry_produces_no_chf_value_at_all():
    """Geometry is source-required (DEBTS D-5), so it blocks before any number exists."""
    state = _state()
    with pytest.raises(NotRankEligibleError, match=r"unsourced channel geometry"):
        _chf(state, geometry=_geometry(sourced=False))


@requires_coolprop
def test_f02_missing_heated_length_blocks_rather_than_defaulting():
    state = _state()
    with pytest.raises(NotRankEligibleError, match=r"heated length"):
        _chf(state, geometry=_geometry(heated_length_m=None))


@requires_coolprop
def test_f02_a_chf_result_with_violations_cannot_rank():
    """Ammonia is outside Shah (1987)'s database too, so its CHF cannot rank."""
    state = _state("Ammonia")
    chf = _chf(state)
    assert chf.is_sourced is False
    assert any(v.axis is Axis.FLUID for v in chf.violations)
    verdict = tp.classify_chf_band(_flux(1.0e3), chf)  # ratio far inside the rank band
    assert verdict.ratio < tp.CHF_RANK_MAX
    assert verdict.status is tp.RankStatus.SENSITIVITY_ONLY


# =============================================================================
# F-05 -- state, properties and fluid identity are one bound value
# =============================================================================


@requires_coolprop
def test_f05_saturation_state_carries_its_own_identity():
    state = _state()
    assert state.fluid == FLUID
    assert state.pressure_Pa == P_REF
    assert state.backend_version == _fluids.backend_version()
    assert state.matches(fluid=FLUID, pressure_Pa=P_REF) is True
    assert state.matches(fluid="Ammonia", pressure_Pa=P_REF) is False
    assert state.matches(fluid=FLUID, pressure_Pa=3.0e5) is False


@requires_coolprop
def test_f05_a_loop_state_from_another_pressure_is_rejected():
    """The 18 % shift the review found: properties at 0.3 MPa under a 1.0 MPa guard."""
    state_low = _state(P=3.0e5)
    loop_high = _loop(0.3, _state(P=P_REF))
    with pytest.raises(NotRankEligibleError, match=r"guarded domain would not be"):
        tp.assert_state_consistent(loop_high, state_low)


@requires_coolprop
def test_f05_mismatched_enthalpies_are_detected():
    """A loop state built from a different fluid's dome cannot pass as this one's."""
    ammonia = _state("Ammonia")
    water = _state("Water")
    loop = _loop(0.3, ammonia)
    with pytest.raises(NotRankEligibleError):
        tp.assert_state_consistent(loop, water)


@requires_coolprop
def test_f05_the_fluid_label_can_no_longer_be_swapped_independently():
    """The exact bypass the review demonstrated is now unconstructible.

    Ammonia properties could previously be passed with ``fluid="Water"`` and return an
    identical coefficient with the applicability flag flipped. Fluid identity now lives
    inside the state, so there is no separate label to swap.
    """
    ammonia = _state("Ammonia")
    assert not hasattr(tp.flow_boiling_htc, "fluid")
    verdict = tp.assess_acquisition(
        loop=_loop(0.3, ammonia),
        state=ammonia,
        geometry=_geometry(),
        wall_flux=_flux(),
        mass_flux_kg_m2s=G_REF,
        chf=_chf(ammonia),
    )
    assert any(v.axis is Axis.FLUID for v in verdict.violations), (
        "the fluid checked must be the fluid the properties came from"
    )
    assert verdict.status is not tp.RankStatus.RANK_ELIGIBLE


# =============================================================================
# F-09 -- the guarded wrapper has no bypass
# =============================================================================


@requires_coolprop
def test_f09_the_public_wrapper_exposes_no_domain_bypass():
    """OTB-G001 F-09: ``check_domain=False`` disabled the only range guard."""
    import inspect

    params = inspect.signature(tp.flow_boiling_htc).parameters
    assert "check_domain" not in params, (
        "the ranked-facing wrapper must not offer a way to switch its guard off; "
        "labelled non-ranking analysis uses the low-level pure evaluator"
    )


@requires_coolprop
def test_f09_out_of_domain_always_raises_through_the_wrapper():
    state = _state()
    with pytest.raises(NotRankEligibleError, match=r"outside its validity domain"):
        tp.flow_boiling_htc(
            mass_flux_kg_m2s=5000.0,  # far above the declared 600 kg/m^2/s
            quality=0.3,
            wall_flux=_flux(),
            geometry=_geometry(),
            state=state,
            loop=_loop(0.3, state),
        )


def test_f09_the_unguarded_seam_is_the_low_level_evaluator_and_is_obvious():
    """The escape hatch still exists, but only where it is unmistakable."""
    import inspect

    doc = inspect.getdoc(gungor_winterton_1986_htc) or ""
    assert "no domain checking" in doc.lower()


# =============================================================================
# F-10 -- the backend pin is enforced, not merely recorded
# =============================================================================


@requires_coolprop
def test_f10_the_installed_backend_matches_the_pin():
    from orbital_thermal.registry.two_phase import COOLPROP_PIN

    _fluids.assert_backend_pin()  # must not raise in a correctly pinned environment
    assert _fluids.backend_version() == COOLPROP_PIN.pinned_version


@requires_coolprop
def test_f10_a_mismatched_backend_version_fails_evaluation(monkeypatch):
    """A different installed version must stop saturation evaluation, not be reported."""
    import CoolProp

    monkeypatch.setattr(CoolProp, "__version__", "8.0.0", raising=False)
    with pytest.raises(_fluids.BackendPinMismatchError, match=r"8\.0\.0"):
        _fluids.assert_backend_pin()
    with pytest.raises(_fluids.BackendPinMismatchError):
        _fluids.saturation_state(P_REF, FLUID)


@requires_coolprop
def test_f10_the_migration_path_is_explicit_and_requires_a_review_record(monkeypatch):
    """Advancing the pin needs a stated review, not an environment variable."""
    import CoolProp

    monkeypatch.setattr(CoolProp, "__version__", "8.0.0", raising=False)
    try:
        with pytest.raises(ValueError, match=r"review_record"):
            _fluids.override_backend_pin("8.0.0", review_record="  ")

        _fluids.override_backend_pin("8.0.0", review_record="verification/…/S9-drift")
        _fluids.assert_backend_pin()  # now accepted
    finally:
        _fluids.clear_backend_pin_override()


# =============================================================================
# Gate 3 -- pressure / quality / domain validity
# =============================================================================


def test_gate3_quality_outside_zero_one_is_rejected():
    h_f, h_fg = 100.0, 1000.0
    assert tp.vapour_quality(h_f + 0.5 * h_fg, h_f, h_fg) == pytest.approx(0.5)
    with pytest.raises(ValueError, match=r"outside the physical range"):
        tp.vapour_quality(h_f - 1.0, h_f, h_fg)
    with pytest.raises(ValueError, match=r"outside the physical range"):
        tp.vapour_quality(h_f + 2.0 * h_fg, h_f, h_fg)


def test_gate3_loop_state_classifies_instead_of_clamping():
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
    p_crit = _fluids.critical_pressure("Ammonia")
    p_triple = _fluids.triple_pressure("Ammonia")
    with pytest.raises(ValueError, match=r"critical pressure"):
        _fluids.saturation_temperature(p_crit * 1.01)
    with pytest.raises(ValueError, match=r"triple-point pressure"):
        _fluids.saturation_temperature(p_triple * 0.5)
    assert _fluids.saturation_temperature(p_crit * 0.5) > 0.0


@requires_coolprop
def test_gate3_no_blanket_supercritical_treatment():
    """The declared water domain admits ~4 mK above T_crit; the backend guard closes it."""
    t_crit_nh3 = _fluids.critical_temperature("Ammonia")
    with pytest.raises(ValueError):
        _fluids.assert_two_phase_domain(t_crit_nh3 + 1.0, "Ammonia")

    lo, hi = _fluids.two_phase_domain_K("Water")
    t_crit_h2o = _fluids.critical_temperature("Water")
    assert lo < t_crit_h2o < hi
    with pytest.raises(ValueError, match=r"critical temperature"):
        _fluids.assert_two_phase_domain(0.5 * (t_crit_h2o + hi), "Water")


@requires_coolprop
def test_gate3_saturation_temperature_is_monotonic_in_pressure():
    temps = [_fluids.saturation_temperature(2.0e5 * k) for k in range(1, 26)]
    assert all(b > a for a, b in pairwise(temps))


@requires_coolprop
def test_gate3_saturation_temperature_inverts_saturation_pressure():
    for T in (250.0, 300.0, 350.0):
        assert _fluids.saturation_temperature(
            _fluids.saturation_pressure(T)
        ) == pytest.approx(T, rel=1e-9)


@requires_coolprop
def test_gate3_unregistered_coolant_is_source_gated():
    with pytest.raises(_fluids.SourceGatedFluidError, match=r"source-gated"):
        _fluids.two_phase_domain_K("CO2")
    assert _fluids.two_phase_domain_K("Ammonia") == (195.5, 405.4)


# =============================================================================
# Gate 4 -- correlation validity ranges (the guard must FIRE on every axis)
# =============================================================================


@pytest.mark.parametrize(
    "axis,bad_value",
    [
        ("G_kg_m2s", 5000.0),
        ("G_kg_m2s", 1.0),
        ("q_flux_W_m2", 1.0e7),
        ("quality", 0.9999),
        ("quality", 0.0001),
        ("P_Pa", 5.0e6),
        ("P_Pa", 1.0e4),
        ("D_m", 0.5),
        ("D_m", 1.0e-4),
    ],
)
def test_gate4_htc_guard_fires_on_every_axis(axis, bad_value):
    entry = get(tp.HTC_ID)
    with pytest.raises(NotRankEligibleError, match=r"outside its validity domain"):
        assert_in_domain(entry, **{axis: bad_value})


@pytest.mark.parametrize(
    "axis,bad_value",
    [
        ("pr_reduced", 0.99),
        ("pr_reduced", 1.0e-5),
        ("D_m", 0.1),
        ("D_m", 1.0e-5),
        ("G_kg_m2s", 5000.0),
        ("critical_quality", 0.99),
    ],
)
def test_gate4_chf_guard_fires_on_every_axis(axis, bad_value):
    """The promoted CHF reference is guarded on its own re-attributed domain."""
    entry = get(tp.CHF_ID)
    with pytest.raises(NotRankEligibleError, match=r"outside its validity domain"):
        assert_in_domain(entry, **{axis: bad_value})


@requires_coolprop
def test_gate4_in_domain_calls_are_accepted():
    """The guards are not vacuous."""
    state = _state()
    assert (
        tp.flow_boiling_htc(
            mass_flux_kg_m2s=G_REF,
            quality=0.3,
            wall_flux=_flux(),
            geometry=_geometry(),
            state=state,
            loop=_loop(0.3, state),
        )
        > 0.0
    )
    assert _chf(state).value_W_m2 > 0.0


# =============================================================================
# Gate 5 -- rejection / de-ranking
# =============================================================================


@requires_coolprop
def test_gate5_chf_band_at_or_above_one_is_rejected():
    state = _state()
    chf = _chf(state)
    verdict = tp.classify_chf_band(_flux(chf.value_W_m2), chf)
    assert verdict.ratio == pytest.approx(1.0)
    assert verdict.status is tp.RankStatus.REJECTED
    assert "dryout" in verdict.reason


@requires_coolprop
def test_gate5_chf_band_between_half_and_one_is_sensitivity_not_ranked():
    state = _state()
    chf = _chf(state)
    verdict = tp.classify_chf_band(_flux(0.75 * chf.value_W_m2), chf)
    assert verdict.ratio == pytest.approx(0.75)
    assert verdict.status is tp.RankStatus.SENSITIVITY_ONLY


@requires_coolprop
def test_gate5_chf_band_at_or_below_half_is_rank_eligible():
    state = _state()
    chf = _chf(state)
    verdict = tp.classify_chf_band(_flux(0.5 * chf.value_W_m2), chf)
    assert verdict.ratio == pytest.approx(0.5)
    assert verdict.status is tp.RankStatus.RANK_ELIGIBLE


@requires_coolprop
def test_gate5_band_boundaries_are_closed_on_the_conservative_side():
    state = _state()
    chf = _chf(state)
    v = chf.value_W_m2
    assert tp.classify_chf_band(_flux(0.5 * v), chf).status is tp.RankStatus.RANK_ELIGIBLE
    assert (
        tp.classify_chf_band(_flux(0.5001 * v), chf).status
        is tp.RankStatus.SENSITIVITY_ONLY
    )
    assert tp.classify_chf_band(_flux(v), chf).status is tp.RankStatus.REJECTED


@requires_coolprop
def test_gate5_underivable_local_flux_is_never_silently_averaged():
    state = _state()
    chf = _chf(state)
    averaged = tp.averaged_wall_heat_flux(
        power_W=1.0, area_m2=1.0e-3, basis=tp.FluxBasis.CHIP_AVERAGE
    )
    assert averaged.is_rankable_basis is False
    verdict = tp.classify_chf_band(averaged, chf)
    assert verdict.ratio < tp.CHF_RANK_MAX
    assert verdict.status is tp.RankStatus.SENSITIVITY_ONLY
    assert "local modeled wall flux" in verdict.reason


@requires_coolprop
def test_gate5_unsourced_geometry_de_ranks_a_local_flux():
    state = _state()
    chf = _chf(state)
    unsourced = tp.local_wall_heat_flux(
        power_W=1.0, wetted_area_m2=1.0e-3, geometry_sourced=False
    )
    assert unsourced.is_rankable_basis is False
    assert tp.classify_chf_band(unsourced, chf).status is tp.RankStatus.SENSITIVITY_ONLY


def test_gate5_averaged_flux_helper_refuses_to_masquerade_as_local():
    with pytest.raises(ValueError, match=r"requires an averaging basis"):
        tp.averaged_wall_heat_flux(
            power_W=50.0, area_m2=1.0e-3, basis=tp.FluxBasis.LOCAL_SOURCED
        )


@requires_coolprop
def test_gate5_missing_chf_blocks_the_case_rather_than_assuming_it_is_safe():
    state = _state()
    verdict = tp.assess_acquisition(
        loop=_loop(0.3, state),
        state=state,
        geometry=_geometry(),
        wall_flux=_flux(),
        mass_flux_kg_m2s=G_REF,
        chf=None,
    )
    assert verdict.status is tp.RankStatus.BLOCKED
    assert verdict.rankable is False


@requires_coolprop
def test_gate5_combined_assessment_takes_the_worst_gate_outcome():
    state = _state()
    chf = _chf(state)
    verdict = tp.assess_acquisition(
        loop=_loop(0.3, state),
        state=state,
        geometry=_geometry(),
        wall_flux=_flux(2.0 * chf.value_W_m2),  # dryout
        mass_flux_kg_m2s=G_REF,
        chf=chf,
    )
    assert verdict.regime.status is tp.RankStatus.RANK_ELIGIBLE
    assert verdict.status is tp.RankStatus.REJECTED


@requires_coolprop
def test_gate5_superheated_state_is_rejected_outright():
    state = _state()
    assert (
        tp.classify_regime(_loop(1.2, state), fluid=FLUID).status
        is tp.RankStatus.REJECTED
    )


@requires_coolprop
def test_gate5_a_fully_applicable_water_case_still_ranks():
    """The control: the enforcement must not de-rank everything."""
    state = _state()
    chf = _chf(state)
    verdict = tp.assess_acquisition(
        loop=_loop(0.3, state),
        state=state,
        geometry=_geometry(),
        wall_flux=_flux(0.1 * chf.value_W_m2),
        mass_flux_kg_m2s=G_REF,
        chf=chf,
    )
    assert verdict.violations == ()
    assert verdict.status is tp.RankStatus.RANK_ELIGIBLE
    assert verdict.htc_W_m2K is not None
    # The provenance caveat travels with the ranked result without de-ranking it.
    assert any("NOT the authors' declared range" in c for c in verdict.caveats)


@requires_coolprop
def test_gate5_ammonia_is_de_ranked_through_gungor_winterton():
    """Director ruling D4: the applicability failure alters status, not just a note."""
    state = _state("Ammonia")
    chf = _chf(state)
    verdict = tp.assess_acquisition(
        loop=_loop(0.3, state),
        state=state,
        geometry=_geometry(),
        wall_flux=_flux(0.1 * chf.value_W_m2),
        mass_flux_kg_m2s=G_REF,
        chf=chf,
    )
    assert any(v.axis is Axis.FLUID for v in verdict.violations)
    assert verdict.status is tp.RankStatus.SENSITIVITY_ONLY
    assert verdict.rankable is False


@requires_coolprop
def test_gate5_laminar_liquid_reynolds_rejects_the_case():
    """F-06: combinations inside the declared box can be laminar; they must not rank."""
    state = _state()
    geometry = _geometry()
    quality = 0.9
    re_l = state.liquid_reynolds(
        mass_flux_kg_m2s=10.0, quality=quality, diameter_m=D_REF
    )
    assert re_l < 3000.0, "this case must actually be laminar for the test to mean anything"

    verdict = tp.assess_acquisition(
        loop=_loop(quality, state),
        state=state,
        geometry=geometry,
        wall_flux=_flux(Q_MIN),
        mass_flux_kg_m2s=10.0,
        chf=_chf(state),
    )
    assert any(
        v.axis is Axis.REGIME and v.consequence is Consequence.REJECT
        for v in verdict.violations
    )
    assert verdict.status is tp.RankStatus.REJECTED


# =============================================================================
# Physics sanity of the implemented correlations
# =============================================================================


@requires_coolprop
def test_gw86_htc_increases_with_quality_and_with_mass_flux():
    state = _state()
    kw = dict(
        q_flux_W_m2=Q_REF,
        diameter_m=D_REF,
        rho_f=state.rho_f_kg_m3,
        rho_g=state.rho_g_kg_m3,
        mu_f=state.mu_f_Pa_s,
        mu_g=state.mu_g_Pa_s,
        k_f=state.k_f_W_mK,
        cp_f=state.cp_f_J_kgK,
        h_fg_J_kg=state.h_fg_J_kg,
        p_reduced=state.p_reduced,
        molar_mass_g_mol=state.molar_mass_g_mol,
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
    """Cooper (1984), rebuilt factor by factor; the printed 0.4343 is not "corrected"."""
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
    assert got == pytest.approx(2.2e4, rel=5e-3)

    idealised = 55.0 * (0.1**0.12) * 1.0 * (18.0**-0.5) * (1.0e5**0.67)
    assert got != pytest.approx(idealised, rel=1e-9), (
        "the implementation must use the printed constant 0.4343, not 1/ln(10)"
    )


def test_martinelli_parameter_falls_with_quality():
    from orbital_thermal.registry.two_phase import martinelli_xtt

    xs = [martinelli_xtt(x, 600.0, 8.0, 1.3e-4, 9e-6) for x in (0.05, 0.2, 0.5, 0.8)]
    assert all(b < a for a, b in pairwise(xs))


# --- Shah (1987): the transcription reconciliation, asserted -------------------


def test_shah_1987_f2_exponent_is_negative_by_continuity():
    """The sign the supplied extract lost, settled without appeal to authority.

    ``F2`` is piecewise at ``F1 = 4``. The implemented (negative) exponent makes the
    two branches join -- ``4^-0.42 = 0.5588`` against the ``F1 > 4`` value ``0.55`` --
    whereas the positive exponent printed in the Springer extract would jump apart by
    3.25x. That is why the subcooled branch could be implemented rather than blocked.

    This exercises the **implementation** across the crossing, not just the arithmetic:
    at ``Y = 1e6`` the branch boundary ``F1 = 4`` sits at ``x_crit = -2.1988``, and
    ``Fx`` is sampled either side of it. With the wrong sign the jump is unmissable.
    """
    y, p_r = 1.0e6, 0.7  # p_r > 0.6 so the F2 term is actually active
    x_at_f1_equals_4 = -(((4.0 - 1.0) / (0.0052 * y**0.41)) ** (1.0 / 0.88))
    assert x_at_f1_equals_4 == pytest.approx(-2.1988, rel=1e-3)

    eps = 1.0e-6
    below = shah_1987_fx(y, p_r, x_at_f1_equals_4 * (1 - eps))  # F1 just under 4
    above = shah_1987_fx(y, p_r, x_at_f1_equals_4 * (1 + eps))  # F1 just over 4

    # The implemented (negative) exponent leaves a residual step of ~0.3 %: F2 goes
    # 4^-0.42 = 0.5588 -> 0.55, damped by the (p_r-0.6)/0.35 factor. The positive
    # exponent would give F2 = 1.789 -> 0.55 and a ~40 % step. The tolerance sits
    # between the two, and is a measured value rather than a fitted one.
    step = abs(below - above) / above
    assert step < 0.01, (
        f"Fx steps by {step:.1%} across the F1 = 4 branch boundary. The reconciled "
        "negative exponent gives ~0.3 %; a ~40 % step means the sign is wrong."
    )


def test_shah_1987_bo_zero_third_candidate_uses_the_reconciled_constant():
    """``Bo0`` candidate 3 is ``0.00024``, not the extract's ``0.0024``.

    ``Bo0`` is the **highest** of three candidates, so the factor of ten only shows up
    where candidate 3 could win -- at large ``Y``. At ``Y = 1e9`` the correct answer is
    candidate 2 (1.636e-4); with the extract's constant, candidate 3 would take over at
    2.724e-4 and silently raise every CHF in that regime by ~66 %.
    """
    y, p_r = 1.0e9, 0.05
    candidate_2 = 0.082 * y**-0.3 * (1.0 + 1.45 * p_r**4.03)
    candidate_3_wrong = 0.0024 * y**-0.105 * (1.0 + 1.15 * p_r**3.39)

    got = shah_1987_bo_zero(y, p_r)
    assert got == pytest.approx(candidate_2, rel=1e-12), (
        "at Y = 1e9 the second candidate must win; if the third does, the leading "
        "constant has been taken from the printing with the transcription errors"
    )
    assert got < candidate_3_wrong, "sanity: the wrong constant really would take over"


def test_shah_1987_high_y_rule_matches_the_second_printing_numerically():
    """[A]'s "evaluate at Y = 1.4e7" reproduces [S]'s printed constant 4.452.

    The two consulted printings describe the same function by different routes; that
    they agree numerically is independent evidence the reconciliation is right.
    """
    assert 0.0052 * (1.4e7**0.41) == pytest.approx(4.452, rel=0.01)


@requires_coolprop
def test_shah_1987_y_is_gravity_explicit():
    """Y divides by g, so the correlation has no microgravity limit."""
    state = _state()
    kw = dict(
        mass_flux_kg_m2s=G_REF,
        diameter_m=D_REF,
        cp_f=state.cp_f_J_kgK,
        k_f=state.k_f_W_mK,
        rho_f=state.rho_f_kg_m3,
        mu_f=state.mu_f_Pa_s,
        mu_g=state.mu_g_Pa_s,
    )
    y_1g = shah_1987_Y(**kw)
    y_low = shah_1987_Y(**kw, gravity_m_s2=1.0e-4)
    assert y_low > y_1g, "as g falls, Y rises -- the parameter diverges toward zero g"
    with pytest.raises(ValueError, match=r"gravity-explicit"):
        shah_1987_Y(**kw, gravity_m_s2=0.0)


@requires_coolprop
def test_shah_1987_chf_is_physically_plausible_for_water():
    """Order-of-magnitude sanity: water CHF in a 10 mm tube is MW/m^2 scale."""
    state = _state()
    chf = _chf(state)
    assert 1.0e5 < chf.value_W_m2 < 1.0e8


@requires_coolprop
def test_shah_1987_chf_rises_with_mass_flux():
    state = _state()
    values = [
        _chf(state, mass_flux_kg_m2s=G).value_W_m2 for G in (200.0, 500.0, 1000.0)
    ]
    assert all(b > a for a, b in pairwise(values))
