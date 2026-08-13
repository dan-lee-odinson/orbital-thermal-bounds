"""D90: the coupling, its fluid-consistency guard, and why S4-3 is now unevaluable twice.

**S4-3 is not touched.** Its wording, its falsifier and its sink-temperature witness are
untouched — S5-12's third clause makes editing them a falsification.

**The discharge is withdrawn (D90/F-01).** The demonstration that produced three separated
roots was not one fluid: it was admitted to the pressure-drop correlation as
``two_component`` ``air-water`` and evolved with single-component water saturation
properties. Every test here that once asserted that discharge is gone, replaced by the
guard that makes the hybrid unrepeatable and by the measurement showing no consistent
demonstration exists.
"""

from __future__ import annotations

import math
import warnings

import pytest

from orbital_thermal import coupled_loop as C
from orbital_thermal import fluids
from orbital_thermal import radiator_coupling as RC

#: The demonstration as it was shipped — air-water, two-component, horizontal. It remains
#: here because it is the case F-01 is ABOUT; it is no longer solved through the coupling.
DEMO_KW = dict(
    fluid="air-water", composition="two_component", geometry_shape="round_tube",
    orientation="horizontal", diameter_m=8.0e-3, length_m=1.0, duty_W=1200.0,
    pressure_Pa=1.2e5, h_fg_J_kg=2.26e6, rho_f=997.0, rho_g=1.2,
    mu_f=8.9e-4, mu_g=1.8e-5,
)
PUMP = C.PumpCharacteristic(shutoff_Pa=6.0e4, runout_kg_s=0.05)
FLOWS = dict(flow_min_kg_s=0.002, flow_max_kg_s=0.049)
AREA_M2, EMISSIVITY, WORKING_FLUID = 0.8, 0.85, "Water"
SINKS_K = (150.0, 250.0, 320.0)
UNCOUPLED_ROOT = 0.043654969267


def demo_case(**over) -> C.LoopCase:
    return C.LoopCase(kind=C.RunKind.MACHINERY_DEMONSTRATION, **{**DEMO_KW, **over})


def boundary(sink_K: float = 250.0) -> RC.RadiatorBoundary:
    return RC.RadiatorBoundary(
        area_m2=AREA_M2, emissivity=EMISSIVITY, sink_temperature_K=sink_K)


# ======================================================================================
# F-01 — the guard, and the measurement that says no consistent demonstration exists
# ======================================================================================

def test_f01_the_hybrid_demonstration_is_now_refused():
    """**F-01's guard.** The case that produced the withdrawn discharge no longer couples.

    Measured at the 250 K sink before the guard: admitted as ``two_component``
    ``air-water``, then evolved with water saturation properties — ``rho_g`` 1.2 -> 3.218,
    ``rho_f`` 997 -> 907.97, pressure 1.2 -> 6.099 bar — while ``mu_g`` stayed at air's
    1.8e-5 against steam's 1.429e-5. The applicability guard admitted it on labels the
    saturation model contradicts.
    """
    with pytest.raises(RC.CoupledCaseRefused, match="single substance"):
        RC.couple(demo_case(), boundary(), working_fluid=WORKING_FLUID)

    # And through the solver, so the refusal is not merely reachable but unavoidable.
    with pytest.raises(RC.CoupledCaseRefused):
        RC.solve_coupled(demo_case(), PUMP, boundary(),
                         working_fluid=WORKING_FLUID, **FLOWS)


def test_f01_a_mismatched_fluid_is_refused_even_when_the_composition_is_right():
    """The second half of the guard: right composition, wrong substance.

    A single-component ammonia case coupled to water's saturation curve is the same
    substitution defect with the composition label corrected, and must refuse too.
    """
    ammonia = demo_case(fluid="Ammonia", composition="single_component")
    with pytest.raises(RC.CoupledCaseRefused, match="same substance"):
        RC.couple(ammonia, boundary(), working_fluid="Water")

    # An unrecognised name is refused rather than assumed to match — a guard against
    # fluid substitution cannot guess which two names mean the same thing.
    with pytest.raises(RC.CoupledCaseRefused, match="does not recognise|same substance"):
        RC.couple(demo_case(fluid="R-134a", composition="single_component"),
                  boundary(), working_fluid="Water")

    # Consistent naming passes the guard (it may still refuse further downstream).
    consistent = demo_case(fluid="Water", composition="single_component")
    try:
        RC.couple(consistent, boundary(), working_fluid="Water")
    except RC.CoupledCaseRefused as exc:
        assert "single substance" not in str(exc) and "same substance" not in str(exc), (
            "a consistent case must not be refused BY THE FLUID GUARD"
        )


def test_f01_no_consistent_demonstration_exists_and_this_is_measured():
    """**F-01's question, answered by execution: NO.** And the reason is structural.

    A coupled demonstration needs two things at once, and the implemented set cannot give
    both:

    * the only implemented pressure-drop correlation admits ``two_component`` ONLY — a
      ``single_component`` case is de-ranked on the composition axis;
    * a condensing state exists only for ONE substance — ``air-water`` is not a fluid, and
      ``Air`` has no saturation state above its critical temperature.

    So unevaluable on both legs is terminal, not a gap awaiting a better fixture.
    """
    from orbital_thermal.registry import two_phase as tp

    entry = next(e for e in tp.TWO_PHASE_CORRELATIONS
                 if e.id == "two_phase.dp.lockhart_martinelli_chisholm")
    spec = entry.applicability_spec
    assert set(spec.compositions) == {"two_component"}, (
        "if the correlation has started admitting single-component flow, a consistent "
        "demonstration may now exist and F-01's answer must be re-derived"
    )

    single = spec.check(fluid="Water", composition="single_component",
                        geometry="round_tube", orientation="horizontal")
    assert any(v.axis is C.Axis.COMPOSITION if hasattr(C, "Axis") else True
               for v in single), "a single-component case must be refused on composition"
    assert single, "single-component must not be admitted"

    for mixture in ("air-water", "Air"):
        with pytest.raises(ValueError):
            fluids.saturation_pressure(400.0, mixture)


def test_f01_the_uncoupled_root_is_unchanged_and_stays_the_baseline():
    """The D-14 measurement is preserved: it is the historical baseline, not a claim."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        roots = [
            C.find_operating_points(
                demo_case(sink_temperature_K=T), PUMP, **FLOWS, samples=240
            )[0].mass_flow_kg_s
            for T in SINKS_K
        ]
    assert len({round(r, 12) for r in roots}) == 1
    assert all(abs(r - UNCOUPLED_ROOT) < 1e-12 for r in roots)


def test_f01_the_mechanism_itself_is_not_deleted():
    """The radiative closure is still correct; what is gone is a case to demonstrate it on.

    D-14's reason says the mechanism is built. That claim must remain checkable, or the
    debt's own text would be resting on nothing.
    """
    t_cond = RC.condensing_temperature_K(1200.0, boundary(250.0))
    assert t_cond > 250.0, "the loop must condense above its sink — second law"
    hotter = RC.condensing_temperature_K(1200.0, boundary(320.0))
    assert hotter > t_cond, "a hotter sink must force a hotter condensing state"
    bigger = RC.condensing_temperature_K(1200.0, RC.RadiatorBoundary(
        area_m2=2 * AREA_M2, emissivity=EMISSIVITY, sink_temperature_K=250.0))
    assert bigger < t_cond, "a larger radiator must reject at a lower temperature"


# ======================================================================================
# F-05 — the third state must survive the public boundary
# ======================================================================================

def test_f05_the_public_verdict_refuses_its_own_truth_test():
    """**F-05.** The sentinel was fine; the wrapper was not.

    ``s4_3_state`` returned an ordinary non-empty 3-tuple, so
    ``if s4_3_state(RunKind.REFERENCE_CASE):`` put the unevaluable device in the true
    branch without ``_Unevaluable.__bool__`` ever running. The witness truth-tests the
    RETURNED OBJECT, not a member of it — every earlier test destructured first, which is
    the path the member guard already covered.
    """
    for kind in (C.RunKind.REFERENCE_CASE, C.RunKind.MACHINERY_DEMONSTRATION):
        result = RC.s4_3_state(kind)
        with pytest.raises(TypeError, match="no bare truth value"):
            bool(result)
        with pytest.raises(TypeError):
            _ = "yes" if result else "no"
        # Destructuring is unaffected, so callers that handle the state still work.
        label, verdict, reason = result
        assert label == "unevaluable" and verdict is RC.UNEVALUABLE and reason


def test_f05_the_same_shape_was_checked_on_the_module_s_other_public_return():
    """F-05 says to check the other public returns before finishing. ``d14_state`` had it.

    A plain 2-tuple is true whether the debt is open or retired, so ``if d14_state():``
    read the same either way — the same defect one function over, found by looking.
    """
    result = RC.d14_state()
    with pytest.raises(TypeError, match="no bare truth value"):
        bool(result)
    state, reason = result
    assert state == "open" and reason


# ======================================================================================
# F-01 — the withdrawn discharge, and D-14's blocker moving back
# ======================================================================================

def test_f01_s4_3_is_unevaluable_on_both_legs_with_no_path_to_true():
    """**The discharge is withdrawn.** Neither leg returns discharged, and none can."""
    for kind in (C.RunKind.MACHINERY_DEMONSTRATION, C.RunKind.REFERENCE_CASE):
        label, verdict, _ = RC.s4_3_state(kind)
        assert label == "unevaluable", f"{kind} must be unevaluable"
        assert verdict is RC.UNEVALUABLE

    demo_reason = RC.s4_3_state(C.RunKind.MACHINERY_DEMONSTRATION).reason
    for clause in ("NOT ONE FLUID", "two_component", "working_fluid",
                   "do not discharge S4-3", "not available"):
        assert clause in demo_reason, f"the reason must say: {clause!r}"

    # There is no path returning a discharged verdict, checked on the RETURN VALUES
    # rather than on the source text. A first draft banned the token "discharged" in the
    # function source and fired on the docstring EXPLAINING the withdrawal -- a check on
    # prose instead of on behaviour, which is the error this milestone has now produced
    # more than once. Every S4_3_Verdict(...) constructed here must open with
    # "unevaluable", and that is a property of the code rather than of its comments.
    import ast
    import inspect
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(RC.s4_3_state)))
    labels = [
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", "") == "S4_3_Verdict"
        and node.args and isinstance(node.args[0], ast.Constant)
    ]
    assert labels and set(labels) == {"unevaluable"}, (
        f"every verdict this function constructs must be unevaluable; got {labels}"
    )


def test_f01_d14_is_blocked_on_the_coupling_again_and_says_the_claim_moved():
    """**D-14's blocker moved back**, and a moving claim must say that it moved."""
    state, reason = RC.d14_state()
    assert state == "open"
    assert "MOVED BACK TO THE COUPLING" in reason
    assert "no longer true" in reason, (
        "the reason must retract its own previous wording, not merely replace it"
    )
    assert "mechanism is built" in reason.lower()


# ======================================================================================
# D87 — the disclosure still travels with whatever numbers exist
# ======================================================================================

def _solution() -> RC.CoupledSolution:
    """A CoupledSolution built directly: no case can be coupled any more."""
    return RC.CoupledSolution(
        _case=demo_case(), _operating_points=(), _condensing_temperature_K=432.62,
        _saturation_pressure_Pa=6.099e5, _rejected_W=1234.0,
        iterations=1, converged=True)


def test_d87_the_disclosure_states_the_widening_and_why():
    """The four things D87 requires it to say, each asserted separately."""
    d = RC.DEMONSTRATION_DISCLOSURE
    assert "4.586 bar" in d and "9.690 bar" in d
    assert "150 K, 250 K, 320 K" in d
    assert "1.2 bar" in d and "MUST NOT BE CARRIED FORWARD UNCHANGED" in d and "45 %" in d
    assert "vapour density carries the coupling" in d and "[1, 20] bar" in d
    assert "0.8 m2" in d and "not a sized radiator" in d
    assert "NOT A STATEMENT ABOUT THIS PROJECT'S DEVICE" in d


def test_d87_the_disclosure_is_a_module_constant_no_caller_can_replace():
    import dataclasses
    import inspect

    fields = {f.name for f in dataclasses.fields(RC.CoupledSolution)}
    assert not any("disclos" in f for f in fields)
    for fn in (RC.solve_coupled, RC.couple, RC.CoupledSolution.render,
               RC.CoupledSolution.disclosed):
        assert not any("disclos" in p for p in inspect.signature(fn).parameters)


def test_d87_the_numbers_cannot_leave_without_the_disclosure():
    s = _solution()
    assert s.disclosed().disclosure == RC.DEMONSTRATION_DISCLOSURE
    assert s.render().startswith(RC.DEMONSTRATION_DISCLOSURE)
    public = {n for n in dir(s) if not n.startswith("_")}
    assert not (public & {"condensing_temperature_K", "saturation_pressure_Pa",
                          "operating_points", "case", "rejected_W"})
    assert "residual" in (RC.CoupledSolution.__doc__ or "").lower()


def test_d87_the_witness_goes_red_against_a_blanked_disclosure(monkeypatch):
    monkeypatch.setattr(RC, "DEMONSTRATION_DISCLOSURE", "")
    with pytest.raises(AssertionError):
        test_d87_the_disclosure_states_the_widening_and_why()
    assert not _solution().render().startswith("MACHINERY DEMONSTRATION")


def test_d87_coupled_loop_is_not_touched():
    """Its blob must stay byte-identical to origin/main; D87 turns on it."""
    text = C._DEMONSTRATION_DISCLOSURE
    for ours in ("4.586 bar", "9.690 bar", "45 %", "vapour density carries the coupling"):
        assert ours not in text
    import inspect
    assert "radiator_coupling" not in inspect.getsource(C)


# ======================================================================================
# F-06 — the vacuous test is deleted, and replaced by the operative state
# ======================================================================================

def test_f06_s5_13_is_not_discharged_asserted_across_the_modules_that_decide_it():
    """**F-06's replacement.** The deleted test inferred absence and could never notice.

    ``test_s5_13_is_vacuous_and_says_so`` asserted that S5 had not built the coupling, by
    reading ``coupled_loop.sink_collapse_conflicts`` — in a packet that ships
    ``radiator_coupling.py``. D87 requires ``coupled_loop`` to stay byte-identical while
    the coupling composes it from another module, so that predicate was structurally
    incapable of detecting that the coupling was built and was guaranteed to keep
    certifying the obsolete state forever.

    The conflict record stays as a HISTORICAL BASELINE. What is asserted instead is the
    operative state, read from the module that actually decides it.
    """
    # The baseline is still the baseline: coupled_loop still declares the collapse.
    (conflict,) = C.sink_collapse_conflicts()
    assert conflict.phenomenon == "sink_temperature_coupling"
    assert "S4-3" in C.sink_disclosure_text()

    # The operative state comes from radiator_coupling, not from an inference.
    for kind in (C.RunKind.MACHINERY_DEMONSTRATION, C.RunKind.REFERENCE_CASE):
        label, verdict, _ = RC.s4_3_state(kind)
        assert label == "unevaluable" and verdict is RC.UNEVALUABLE
    assert RC.d14_state().state == "open"


# ======================================================================================
# Standing guards
# ======================================================================================

def test_a_state_outside_a_declared_basis_is_refused_not_extrapolated():
    """Property-side refusals still fire, on a fluid-consistent case."""
    consistent = demo_case(fluid="Water", composition="single_component")
    no_state = RC.RadiatorBoundary(
        area_m2=50.0, emissivity=0.85, sink_temperature_K=150.0)
    with pytest.raises(RC.CoupledCaseRefused, match="no saturation state"):
        RC.couple(consistent, no_state, working_fluid="Water")


def test_non_uniqueness_is_never_resolved_by_picking():
    s = _solution()
    with pytest.raises(ValueError, match="forbids selecting"):
        _ = s.root_kg_s


def test_the_radiator_boundary_refuses_unphysical_inputs():
    for bad in (dict(area_m2=0.0), dict(emissivity=1.5), dict(sink_temperature_K=-1.0),
                dict(emissivity=math.nan)):
        with pytest.raises(ValueError):
            RC.RadiatorBoundary(**{
                "area_m2": 0.8, "emissivity": 0.85, "sink_temperature_K": 250.0, **bad})
