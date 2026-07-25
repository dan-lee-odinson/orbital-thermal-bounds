"""R1 class-level regression: enforcement lives at the BOUNDARY, not at a call site.

**The defect class (OTB-G001-FIXES).** Four of the six findings were round-1 fixes
coming back. Each round-1 fix was real and was built -- but built at *one call site*
instead of at the boundary, so the same wrong answer stayed reachable through a
different door:

| Sibling | The door that stayed open |
|---|---|
| F-01 | the gravity axis rejected only ``g <= 0``; every positive value passed, to 1e-12 |
| F-02 | ``ChfResult`` was a labelled number -- fabricable, and no consumer read the labels |
| F-03 | the fluid guard compared ``state.fluid`` to ``state.fluid`` -- true for every input |
| F-04 | ``flow_boiling_htc`` never called the mechanism; only ``assess_acquisition`` did |
| F-05 | the pin override accepted any non-blank string, including ``'TODO'`` |

The R1 standard asks for at least three sibling instances plus a control. Five siblings
are exercised below, plus two controls.

**The class-level statement is the first test in this module**: every public entry point
that can produce a physical value must enforce, and it is asserted by *enumerating the
entry points* rather than by checking the one that was reported. A fix that closes the
reported path and leaves a sibling open is what produced this round.

The control matters as much as the siblings: an enforcement that refuses everything is
breakage, not rigour, so the legitimate case is pinned through every entry point too.
"""

from __future__ import annotations

import dataclasses

import pytest

from orbital_thermal import two_phase as tp
from orbital_thermal.registry import NotRankEligibleError, get
from orbital_thermal.registry.applicability import Axis, Consequence

try:
    from orbital_thermal import fluids as _fluids
except ImportError:  # pragma: no cover
    _fluids = None

requires_coolprop = pytest.mark.skipif(_fluids is None, reason="CoolProp not installed")

P_REF, G_REF, D_REF, Q_REF = 1.0e6, 500.0, 1.0e-2, 1.0e5
G0 = tp.STANDARD_GRAVITY_M_S2


def _state(fluid="Water", P=P_REF):
    return _fluids.saturation_state(P, fluid)


def _geometry(**kw):
    base = dict(
        shape="round_tube",
        hydraulic_diameter_m=D_REF,
        orientation="vertical_upflow",
        heated_length_m=1.0,
        sourced=True,
    )
    base.update(kw)
    return tp.ChannelGeometry(**base)


def _flux(q=Q_REF):
    return tp.local_wall_heat_flux(
        power_W=q * 1.0e-3, wetted_area_m2=1.0e-3, geometry_sourced=True
    )


def _loop(x, state):
    return tp.loop_state_from(state, enthalpy_J_kg=state.h_f_J_kg + x * state.h_fg_J_kg)


def _binding(state, **kw):
    return tp.case_binding(
        state=state,
        geometry=kw.pop("geometry", None) or _geometry(),
        mass_flux_kg_m2s=kw.pop("mass_flux_kg_m2s", G_REF),
        gravity_m_s2=kw.pop("gravity_m_s2", G0),
    )


def _chf(state, **kw):
    return tp.critical_heat_flux(
        state=state,
        geometry=kw.pop("geometry", None) or _geometry(),
        mass_flux_kg_m2s=kw.pop("mass_flux_kg_m2s", G_REF),
        inlet_quality=kw.pop("inlet_quality", -0.1),
        critical_quality=kw.pop("critical_quality", 0.3),
        **kw,
    )


# =============================================================================
# THE CLASS-LEVEL STATEMENT — every value-producing entry point enforces
# =============================================================================


@requires_coolprop
def test_every_public_value_producing_entry_point_enforces_applicability():
    """Ammonia is outside Gungor & Winterton's database. **No** public route may
    hand back a coefficient for it without saying so.

    This is the class, stated as a property of the API surface rather than of one
    function. Round 1 fixed ``assess_acquisition`` and left ``flow_boiling_htc`` open;
    the measured symptom was 20,687.1 W/m^2/K for ammonia with no violation reported --
    the exact number round 1's own F-05 had reported for a different bypass.
    """
    ammonia = _state("Ammonia")
    loop = _loop(0.3, ammonia)
    geom, wf = _geometry(), _flux()

    # Route 1 -- the public HTC wrapper.
    htc = tp.flow_boiling_htc(
        mass_flux_kg_m2s=G_REF,
        quality=0.3,
        wall_flux=wf,
        geometry=geom,
        state=ammonia,
        fluid="Ammonia",
        loop=loop,
    )
    assert not htc.is_applicable, "the public wrapper must not silently return a value"
    assert any(v.axis is Axis.FLUID for v in htc.violations)

    # Route 2 -- the combined assessment.
    verdict = tp.assess_acquisition(
        loop=loop,
        state=ammonia,
        geometry=geom,
        wall_flux=wf,
        mass_flux_kg_m2s=G_REF,
        chf=_chf(ammonia),
        fluid="Ammonia",
    )
    assert verdict.status is not tp.RankStatus.RANK_ELIGIBLE
    assert any(v.axis is Axis.FLUID for v in verdict.violations)

    # Route 3 -- the CHF evaluator (ammonia is outside Shah 1987's database too).
    assert any(v.axis is Axis.FLUID for v in _chf(ammonia).violations)


@requires_coolprop
def test_control_a_legitimate_case_still_works_through_every_entry_point():
    """The control. Enforcement that refuses everything is breakage, not rigour."""
    water = _state()
    loop = _loop(0.3, water)
    geom, wf = _geometry(), _flux()

    htc = tp.flow_boiling_htc(
        mass_flux_kg_m2s=G_REF,
        quality=0.3,
        wall_flux=wf,
        geometry=geom,
        state=water,
        fluid="Water",
        loop=loop,
    )
    assert htc.is_applicable and htc.value_W_m2 > 0.0

    chf = _chf(water)
    assert chf.is_sourced and chf.value_W_m2 > 0.0

    band = tp.classify_chf_band(_flux(0.1 * chf.value_W_m2), chf, binding=_binding(water))
    assert band.status is tp.RankStatus.RANK_ELIGIBLE

    verdict = tp.assess_acquisition(
        loop=loop,
        state=water,
        geometry=geom,
        wall_flux=_flux(0.1 * chf.value_W_m2),
        mass_flux_kg_m2s=G_REF,
        chf=chf,
        fluid="Water",
    )
    assert verdict.status is tp.RankStatus.RANK_ELIGIBLE


# =============================================================================
# SIBLING F-04 — the public wrapper runs the mechanism
# =============================================================================


@requires_coolprop
def test_sibling_f04_the_public_wrapper_returns_the_verdict_not_a_bare_number():
    """A ``float`` has nowhere to carry a violation, so the return type moved."""
    water = _state()
    result = tp.flow_boiling_htc(
        mass_flux_kg_m2s=G_REF,
        quality=0.3,
        wall_flux=_flux(),
        geometry=_geometry(),
        state=water,
        fluid="Water",
    )
    assert isinstance(result, tp.HtcResult)
    assert hasattr(result, "violations") and hasattr(result, "value_W_m2")


@requires_coolprop
def test_sibling_f04_a_blocking_axis_raises_rather_than_returning():
    """``BLOCK``/``REJECT`` make the number meaningless, so the wrapper refuses.

    ``DE_RANK`` deliberately does not raise -- ammonia must stay evaluable as a
    sensitivity (ruling D4 de-ranks rather than blocks it), and raising would wrongly
    escalate every de-ranked coolant to rejected.
    """
    water = _state()
    # Laminar liquid Reynolds -- a REJECT, because the Dittus-Boelter base the
    # correlation is built on is a turbulent form. Every input is inside the declared
    # numeric box, so the guard that fires is the applicability mechanism, not the
    # domain check.
    re_l = water.liquid_reynolds(mass_flux_kg_m2s=10.0, quality=0.9, diameter_m=D_REF)
    assert re_l < 3000.0, "this case must actually be laminar for the test to mean anything"

    with pytest.raises(NotRankEligibleError, match=r"not applicable"):
        tp.flow_boiling_htc(
            mass_flux_kg_m2s=10.0,
            quality=0.9,
            wall_flux=_flux(2.0e3),
            geometry=_geometry(),
            state=water,
            fluid="Water",
        )

    # ...whereas a DE_RANK axis (geometry outside the basis) returns with the violation
    # recorded, rather than raising. The split is deliberate: see the docstring.
    de_ranked = tp.flow_boiling_htc(
        mass_flux_kg_m2s=G_REF,
        quality=0.3,
        wall_flux=_flux(),
        geometry=_geometry(shape="chevron_plate"),
        state=water,
        fluid="Water",
    )
    assert not de_ranked.is_applicable
    assert any(v.axis is Axis.GEOMETRY for v in de_ranked.violations)


@requires_coolprop
def test_sibling_f04_the_docstring_no_longer_claims_a_check_it_does_not_make():
    """The old docstring said applicability "is checked but not raised on here".

    It was not checked at all. A docstring that describes a guard that does not exist
    is worse than silence: it is what a reader relies on instead of looking.
    """
    import inspect

    doc = inspect.getdoc(tp.flow_boiling_htc) or ""
    assert "checked but" not in doc
    assert "enforcement boundary" in doc


# =============================================================================
# SIBLING F-02 — every way a CHF value can reach the band
# =============================================================================


def test_sibling_f02_a_fabricated_chf_result_cannot_be_constructed():
    """Unconstructible outside the evaluator -- fabrication is refused, not detected."""
    with pytest.raises(TypeError, match=r"cannot be constructed directly"):
        tp.ChfResult(
            value_W_m2=9.9e9,
            correlation_id="not.a.real.id",
            citation="fabricated",
            locator="fabricated",
            fluid="Unobtainium",
            geometry="klein_bottle",
            evaluated_domain={},
            gravity_m_s2=1e-9,
        )


@requires_coolprop
def test_sibling_f02_a_replayed_chf_result_is_refused_by_the_consumer():
    """The other door: a result honestly produced for one case, used for another.

    Being unforgeable is not enough if nobody checks who it was made for.
    """
    water = _state()
    chf = _chf(water, mass_flux_kg_m2s=G_REF)
    other_case = _binding(water, mass_flux_kg_m2s=250.0)  # different case
    with pytest.raises(NotRankEligibleError, match=r"produced for a different case"):
        tp.classify_chf_band(_flux(), chf, binding=other_case)


@requires_coolprop
def test_sibling_f02_a_mutated_chf_result_cannot_be_rebuilt():
    """``dataclasses.replace`` goes through ``__init__``, so it is refused too."""
    chf = _chf(_state())
    with pytest.raises(TypeError, match=r"cannot be constructed directly"):
        dataclasses.replace(chf, value_W_m2=1.0)


@requires_coolprop
def test_sibling_f02_the_binding_covers_every_identifying_field():
    """A replay differing in any one field must be caught, not just the obvious one."""
    water = _state()
    chf = _chf(water)
    for changed in (
        dict(mass_flux_kg_m2s=123.0),
        dict(geometry=_geometry(shape="annulus")),
        dict(gravity_m_s2=3.71),
    ):
        with pytest.raises(NotRankEligibleError, match=r"different case"):
            tp.classify_chf_band(_flux(), chf, binding=_binding(water, **changed))


# =============================================================================
# SIBLING F-03 — fluid identity cannot be asserted by relabelling
# =============================================================================


@requires_coolprop
def test_sibling_f03_a_relabelled_state_is_refused():
    """Ammonia properties with the string ``"Water"`` -- the reported bypass."""
    ammonia = _state("Ammonia")
    relabelled = dataclasses.replace(ammonia, fluid="Water")
    loop = tp.loop_state_from(
        relabelled, enthalpy_J_kg=(relabelled.h_f_J_kg + relabelled.h_g_J_kg) / 2
    )
    with pytest.raises(NotRankEligibleError, match=r"properties are not"):
        tp.assert_state_consistent(loop, relabelled)


@requires_coolprop
def test_sibling_f03_verification_is_not_optional():
    """Omitting the case fluid must not skip the check.

    The first attempt at this fix made ``fluid`` optional and skipped verification when
    it was absent -- which rebuilt the hole exactly, because the probe simply did not
    pass it. Verification now runs either way: what catches a relabelling is the
    re-derived properties, not the string.
    """
    ammonia = _state("Ammonia")
    relabelled = dataclasses.replace(ammonia, fluid="Water")
    loop = tp.loop_state_from(
        relabelled, enthalpy_J_kg=(relabelled.h_f_J_kg + relabelled.h_g_J_kg) / 2
    )
    with pytest.raises(NotRankEligibleError):
        tp.assert_state_consistent(loop, relabelled)  # no fluid= argument
    with pytest.raises(NotRankEligibleError):
        tp.assert_state_consistent(loop, relabelled, fluid="Water")


@requires_coolprop
def test_sibling_f03_the_full_property_set_is_compared():
    """A single perturbed property is enough to fail, not only the labelled ones."""
    water = _state()
    for field in ("h_g_J_kg", "mu_g_Pa_s", "sigma_N_m", "molar_mass_kg_mol"):
        tampered = dataclasses.replace(water, **{field: getattr(water, field) * 1.05})
        with pytest.raises(ValueError, match=r"properties are not"):
            tampered.verify_is("Water")


@requires_coolprop
def test_sibling_f03_a_genuine_state_verifies():
    """Control: the real thing passes, and cheaply enough to sit on the hot path."""
    _state().verify_is("Water")
    _state("Ammonia").verify_is("Ammonia")


# =============================================================================
# SIBLING F-05 — the override needs a record that resolves
# =============================================================================


@requires_coolprop
@pytest.mark.parametrize(
    "bogus", ["x", "...", "TODO", "no such record exists", "2099-01-01-nope.md"]
)
def test_sibling_f05_an_unresolvable_review_record_is_refused(bogus):
    with pytest.raises(ValueError, match=r"does not (name|resolve)"):
        _fluids.override_backend_pin("8.0.0", review_record=bogus)


@requires_coolprop
def test_sibling_f05_a_real_review_record_is_accepted():
    """Control: the mechanism must not be unusable."""
    try:
        _fluids.override_backend_pin(
            "8.0.0", review_record="2026-07-25-s2-two-phase-evaporator.md"
        )
    finally:
        _fluids.clear_backend_pin_override()


# =============================================================================
# SIBLING F-01 — gravity is enforced across its range, not only at zero
# =============================================================================


@pytest.mark.parametrize("g", [1e-12, 1e-6, 1e-3, 0.0098, 1.62, 3.71])
def test_sibling_f01_reduced_gravity_is_an_applicability_violation(g):
    """Milli-g, lunar and Martian gravity are all outside a terrestrial database.

    Before the fix only ``g <= 0`` was refused: 1e-12 m/s^2 -- a trillionth of standard
    gravity, emptier than any orbit -- produced no violation at all.
    """
    spec = get("two_phase.chf.shah_1987").applicability_spec
    v = spec.check(
        fluid="Water",
        geometry="round_tube",
        orientation="vertical_upflow",
        gravity_m_s2=g,
    )
    gravity = [x for x in v if x.axis is Axis.ORIENTATION]
    assert gravity, f"g = {g} m/s^2 must violate the gravity axis"
    assert gravity[0].consequence is Consequence.DE_RANK


def test_sibling_f01_standard_gravity_passes_and_zero_is_rejected():
    """Control at both ends: 1 g works, and ``g <= 0`` is refused outright."""
    spec = get("two_phase.chf.shah_1987").applicability_spec
    common = dict(
        fluid="Water", geometry="round_tube", orientation="vertical_upflow"
    )
    assert spec.check(**common, gravity_m_s2=G0) == ()
    assert spec.check(**common, gravity_m_s2=9.78) == (), "terrestrial variation passes"

    rejected = spec.check(**common, gravity_m_s2=0.0)
    assert rejected and rejected[0].consequence is Consequence.REJECT


def test_sibling_f01_the_threshold_is_sourced_not_invented():
    """The boundary is the database's gravity; only the tolerance is a convention."""
    spec = get("two_phase.chf.shah_1987").applicability_spec
    assert spec.reference_gravity_m_s2 == G0
    assert spec.branch_threshold == 1.0e6, "Shah's own transitional criterion"
    assert "10^6" in spec.branch_threshold_basis


@requires_coolprop
def test_sibling_f01_gravity_moving_a_case_across_shahs_branch_is_rejected():
    """The sharper, sourced test: gravity flipping the calculation procedure.

    Used as a **straddle** against the value at standard gravity, never as an absolute
    bound -- see the control below for why.
    """
    water = _state()
    with pytest.raises(NotRankEligibleError, match=r"branch threshold|not applicable"):
        _chf(water, gravity_m_s2=1.0e-4)


@requires_coolprop
def test_sibling_f01_an_absolute_branch_test_would_misfire_at_one_g():
    """Why the straddle formulation, and not ``Y >= 1e6`` as a cutoff.

    ``Y`` exceeds 1e6 legitimately at **standard gravity** under high mass flux, well
    inside Shah's declared 4-2905 kg/m^2/s range. An absolute test would reject
    ordinary terrestrial cases, so the handoff's suggested reading is used as a
    comparison against the 1-g value rather than as a bound on the value itself.
    """
    water = _state()
    y_high_flux = shah_1987_Y_for(water, mass_flux_kg_m2s=2000.0, gravity_m_s2=G0)
    assert y_high_flux >= 1.0e6, "this case must actually exceed the threshold at 1 g"

    # ...and it is NOT a gravity violation, because gravity did not move it there.
    chf = _chf(water, mass_flux_kg_m2s=2000.0, critical_quality=0.3)
    assert not [
        v for v in chf.violations if "branch threshold" in v.detail
    ], "a case that crosses Y >= 1e6 at 1 g is ordinary, not a gravity violation"


def shah_1987_Y_for(state, *, mass_flux_kg_m2s: float, gravity_m_s2: float) -> float:
    from orbital_thermal.registry.two_phase import shah_1987_Y

    return shah_1987_Y(
        mass_flux_kg_m2s=mass_flux_kg_m2s,
        diameter_m=D_REF,
        cp_f=state.cp_f_J_kgK,
        k_f=state.k_f_W_mK,
        rho_f=state.rho_f_kg_m3,
        mu_f=state.mu_f_Pa_s,
        mu_g=state.mu_g_Pa_s,
        gravity_m_s2=gravity_m_s2,
    )


# =============================================================================
# SIBLING F-06 — the inlet-quality axis is enforced, and honestly labelled
# =============================================================================


@requires_coolprop
@pytest.mark.parametrize("x_in", [-1000.0, -4.0, -2.61, 0.86])
def test_sibling_f06_out_of_range_inlet_quality_is_refused(x_in):
    """``x_in = -1000`` inflated CHF ~1000x and still reported sourced.

    CHF is the **denominator** of ``q''/CHF``, so the error made cases look *safer* --
    non-conservative, the same direction as the microgravity problem.
    """
    with pytest.raises(NotRankEligibleError, match=r"validity domain"):
        _chf(_state(), inlet_quality=x_in)


@requires_coolprop
def test_sibling_f06_the_enforced_bound_is_closed_and_usable():
    """Control: the bound itself must remain evaluable, per "keep the correlation usable"."""
    for x_in in (-2.6, -1.0, 0.0, 0.85):
        assert _chf(_state(), inlet_quality=x_in).value_W_m2 > 0.0


def test_sibling_f06_the_provenance_is_recorded_as_it_actually_is():
    """The handoff's attribution for this bound was wrong; the registry says so.

    The round-2 handoff stated the printings conflict on inlet quality, "Springer gives
    -2.6, Shah 2023 gives -4.00". Both attributions are reversed and the two quality
    axes are conflated: Springer prints inlet -4.00 to 0.85 and *critical* -2.6 to 1,
    and Shah 2023 states no inlet range at all. The ruling is still applied -- -2.6 is
    tighter than the only sourced inlet bound, so it is conservative for ``q''/CHF`` --
    but the registry records what the sources say, not what the handoff said they say.
    """
    from orbital_thermal.registry.two_phase import SHAH_1987_INLET_QUALITY_NOTE as note

    assert "-2.6" in note and "-4.00" in note
    assert "single-source" in note
    assert "conservative" in note

    entry = get("two_phase.chf.shah_1987")
    assert entry.domain.ranges["inlet_quality"] == (-2.6, 0.85)
    spec = entry.applicability_spec
    assert not any("inlet quality" in a for a in spec.unenforced_axes), (
        "the stale 'axis not enforced' caveat must go once the axis is enforced"
    )
