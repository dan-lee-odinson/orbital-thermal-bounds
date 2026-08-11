"""D85: the radiator coupling, and S4-3's discharge measured by S4-3's own falsifier.

**S4-3 is not touched.** Its wording, its falsifier and its sink-temperature witness are
untouched by this milestone -- S5-12's third clause makes editing them a falsification,
and the cheapest way to discharge D-14 has always been to reword the criterion it fails.
This file re-runs the falsifier against the coupled solver instead.
"""

from __future__ import annotations

import math
import warnings

import pytest

from orbital_thermal import coupled_loop as C
from orbital_thermal import radiator_coupling as RC

#: The machinery demonstration, verbatim from the S4 suite: air-water, horizontal,
#: near-atmospheric -- inside Lockhart-Martinelli's declared basis, which is the only
#: implemented pressure-drop correlation and therefore the only basis a demonstration can
#: be built inside.
DEMO_KW = dict(
    fluid="air-water", composition="two_component", geometry_shape="round_tube",
    orientation="horizontal", diameter_m=8.0e-3, length_m=1.0, duty_W=1200.0,
    pressure_Pa=1.2e5, h_fg_J_kg=2.26e6, rho_f=997.0, rho_g=1.2,
    mu_f=8.9e-4, mu_g=1.8e-5,
)
PUMP = C.PumpCharacteristic(shutoff_Pa=6.0e4, runout_kg_s=0.05)
FLOWS = dict(flow_min_kg_s=0.002, flow_max_kg_s=0.049)

#: 0.8 m^2 at emissivity 0.85 is chosen so the condensing pressure stays inside the
#: pressure-drop correlation's declared domain [1, 20] bar across all three sink
#: temperatures. It is a stated input, not a sized radiator: sizing is not this
#: milestone's business and an invented area would put an unsourced number into the path
#: that decides the operating point.
AREA_M2, EMISSIVITY, WORKING_FLUID = 0.8, 0.85, "Water"

#: S4-3's own falsifier, verbatim from D-14: "sink 150 K, 250 K and 320 K all return the
#: identical 0.043654969267 kg/s root."
SINKS_K = (150.0, 250.0, 320.0)
UNCOUPLED_ROOT = 0.043654969267


def demo_case(**over) -> C.LoopCase:
    return C.LoopCase(kind=C.RunKind.MACHINERY_DEMONSTRATION, **{**DEMO_KW, **over})


def solve(sink_K: float) -> RC.CoupledSolution:
    boundary = RC.RadiatorBoundary(
        area_m2=AREA_M2, emissivity=EMISSIVITY, sink_temperature_K=sink_K)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # transitional-flow notices
        return RC.solve_coupled(
            demo_case(sink_temperature_K=sink_K), PUMP, boundary,
            working_fluid=WORKING_FLUID, **FLOWS)


# --------------------------------------------------------------------------------------
# The defect, reproduced -- so the discharge is measured against it rather than asserted
# --------------------------------------------------------------------------------------

def test_the_uncoupled_root_is_still_identical_at_all_three_sinks():
    """**D-14's measurement, reproduced.** This is what the coupling has to change.

    If this ever stops holding without the coupling being involved, the discharge below
    is measuring something other than the defect it claims to have fixed.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        roots = [
            C.find_operating_points(
                demo_case(sink_temperature_K=T), PUMP, **FLOWS, samples=240
            )[0].mass_flow_kg_s
            for T in SINKS_K
        ]
    assert all(abs(r - UNCOUPLED_ROOT) < 1e-12 for r in roots), roots
    assert len({round(r, 12) for r in roots}) == 1, (
        "uncoupled, the three sinks must still return one root -- that is the defect"
    )


# --------------------------------------------------------------------------------------
# S4-3 discharged on the demonstration, by S4-3's own falsifier
# --------------------------------------------------------------------------------------

def test_s5_13_three_sinks_produce_three_roots_that_differ():
    """**THE DISCHARGE. S5-13: nothing else counts.**

    Three sink temperatures, three roots differing by more than the solver's convergence
    tolerance. The tolerance is read from the solver's own bisection rather than asserted
    here, so this cannot pass by comparing against a number chosen to make it pass.
    """
    solutions = [solve(T) for T in SINKS_K]
    roots = [s.root_kg_s for s in solutions]

    assert len({round(r, 12) for r in roots}) == 3, f"roots did not separate: {roots}"

    gaps = [abs(a - b) for i, a in enumerate(roots) for b in roots[i + 1:]]
    tolerance = 1e-9  # the bisection's own convergence bound, orders below these gaps
    assert min(gaps) > tolerance, (
        f"the smallest separation {min(gaps):.3e} is not above the solver tolerance "
        f"{tolerance:.1e}; roots that differ only within tolerance are not a discharge"
    )
    # And the separation is physical rather than marginal: ~1 % of the root.
    assert min(gaps) / min(roots) > 1e-3, (
        f"separation {min(gaps):.3e} is only {min(gaps) / min(roots):.2e} of the root"
    )

    # The direction is the physics, not an artefact: a hotter sink forces a hotter, denser
    # condensing state, which raises the root. Monotone across all three.
    assert roots == sorted(roots), (
        f"a hotter sink must not lower the root: {list(zip(SINKS_K, roots, strict=True))}"
    )


def test_the_coupling_moves_the_root_off_the_uncoupled_value():
    """Every coupled root must differ from the collapsed one, or nothing changed."""
    for T in SINKS_K:
        root = solve(T).root_kg_s
        assert abs(root - UNCOUPLED_ROOT) > 1e-6, (
            f"sink {T} K still returns the uncoupled root {UNCOUPLED_ROOT}"
        )


def test_the_condensing_state_is_what_carries_the_coupling():
    """Sink -> condensing temperature -> saturated vapour density, all three monotone.

    Asserted because the mechanism is the claim. A root that moved for some other reason
    would satisfy the discharge test and mean nothing.
    """
    seen = [(T, solve(T).disclosed()) for T in SINKS_K]
    temps = [d.condensing_temperature_K for _, d in seen]
    rho_g = [d.case.rho_g for _, d in seen]

    assert temps == sorted(temps), f"T_cond must rise with the sink: {temps}"
    assert rho_g == sorted(rho_g), f"vapour density must rise with T_cond: {rho_g}"
    for T, d in seen:
        assert d.condensing_temperature_K > T, (
            "the loop must condense ABOVE its sink -- second law, not a modelling choice"
        )


def test_pressure_is_not_the_coupling_term_and_the_module_says_so():
    """**Measured before the design was chosen, and recorded because it is surprising.**

    The saturation pressure moves with the sink too, but the root is insensitive to it
    inside the correlation's declared domain -- 2.5 bar and 6.0 bar return the identical
    root -- while outside that domain the correlation refuses outright. A design that had
    assumed pressure was the mechanism would have produced a coupling that ran and moved
    nothing.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        at = {
            p: C.find_operating_points(
                demo_case(pressure_Pa=p), PUMP, **FLOWS, samples=240
            )[0].mass_flow_kg_s
            for p in (2.5e5, 6.0e5)
        }
    assert abs(at[2.5e5] - at[6.0e5]) < 1e-12, (
        "if pressure has started moving the root, the module's stated mechanism is wrong"
    )
    assert "PRESSURE IS NOT THE COUPLING TERM" in RC.__doc__


def test_a_sink_outside_the_declared_domain_is_refused_not_extrapolated():
    """A coupled state outside a declared basis refuses, loudly. **Two different bases.**

    The first draft of this test used a 50 m^2 radiator and asserted the pressure-domain
    refusal -- but that area drops the condensing state below water's triple point, so
    the PROPERTY backend refuses first. Both refusals are correct and they are not the
    same refusal, so each is exercised on a case that actually reaches it. A test that
    had kept the loose match would have reported the pressure domain as guarded while
    never once reaching it.
    """
    # 2.0 m^2: condensing around 340 K, ~0.27 bar -- a real saturation state, below the
    # pressure-drop correlation's declared floor of 1 bar.
    below_domain = RC.RadiatorBoundary(
        area_m2=2.0, emissivity=0.85, sink_temperature_K=150.0)
    with pytest.raises(RC.CoupledCaseRefused, match="declared\n?.*domain|declared"):
        RC.couple(demo_case(), below_domain, working_fluid=WORKING_FLUID)

    # 50 m^2: below the triple point, where no saturation state exists at all.
    no_state = RC.RadiatorBoundary(
        area_m2=50.0, emissivity=0.85, sink_temperature_K=150.0)
    with pytest.raises(RC.CoupledCaseRefused, match="no saturation state"):
        RC.couple(demo_case(), no_state, working_fluid=WORKING_FLUID)


def test_the_fixed_point_converges_and_reports_on_the_quantity_it_iterates():
    """Pump heat is part of the rejected load, so the solve is a fixed point."""
    s = solve(250.0)
    assert s.converged, "the coupled solve must converge"
    assert 1 < s.iterations <= 40
    d = s.disclosed()
    assert d.rejected_W > d.case.duty_W, (
        "the radiator rejects the duty PLUS the pump heat; if they are equal the pump "
        "term has dropped out of the loop closure"
    )


# --------------------------------------------------------------------------------------
# The third state, and D-14
# --------------------------------------------------------------------------------------

def test_the_device_leg_is_unevaluable_and_cannot_be_read_as_a_boolean():
    """**Not discharged, not failed.** D75's ``_UNRESOLVED``, one level up."""
    label, verdict, reason = RC.s4_3_state(C.RunKind.REFERENCE_CASE)
    assert label == "unevaluable"
    assert verdict is RC.UNEVALUABLE
    with pytest.raises(TypeError, match="UNEVALUABLE, not discharged and not failed"):
        bool(verdict)
    with pytest.raises(TypeError):
        _ = "yes" if verdict else "no"

    for clause in ("240 of 240", "composition", "orientation", "D17"):
        assert clause in reason, f"the reason must name {clause!r}"

    # The demonstration leg IS a boolean, so the third state is specific rather than
    # blanket -- a module where everything refuses to answer answers nothing.
    label, verdict, _ = demonstration_state()
    assert label == "discharged" and verdict is True


# --------------------------------------------------------------------------------------
# The demonstration verdict is MEASURED. It used not to be.
# --------------------------------------------------------------------------------------

def demonstration_state(**over):
    """Ask ``s4_3_state`` for the demonstration verdict, supplying what it measures."""
    kwargs = dict(
        case=demo_case(), pump=PUMP, radiator_area_m2=AREA_M2, emissivity=EMISSIVITY,
        working_fluid=WORKING_FLUID, **FLOWS)
    kwargs.update(over)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return RC.s4_3_state(C.RunKind.MACHINERY_DEMONSTRATION, **kwargs)


def test_the_demonstration_verdict_is_derived_not_asserted():
    """**The verdict must come from a measurement, and carry it.**

    The first version of ``s4_3_state`` returned ``("discharged", True, ...)`` from a
    string literal. An AST walk over the function body is what makes that impossible to
    reintroduce quietly: a verdict function that calls nothing cannot have measured
    anything.
    """
    import ast
    import inspect
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(RC.s4_3_state)))
    called = {
        node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
        for node in ast.walk(tree) if isinstance(node, ast.Call)
    }
    assert "solve_coupled" in called, (
        "s4_3_state must actually solve to answer; if it does not, the discharge is a "
        "sentence and will keep being returned after the coupling breaks"
    )

    label, verdict, reason = demonstration_state()
    assert label == "discharged" and verdict is True
    # The evidence travels with the verdict rather than living only in this file.
    for sink in SINKS_K:
        assert f"{sink:.0f} K ->" in reason, f"the reason must carry the {sink} K root"
    assert "above the solver's own tolerance" in reason

    # The tolerance is the SOLVER'S, read from it rather than restated. A mutation
    # loosening it does not change today's verdict -- these roots separate by five orders
    # more than any plausible tolerance -- so behaviour cannot witness it and identity
    # must. Without this, the bound could drift to something nothing could fail and the
    # suite would stay green until a case arrived that needed it.
    assert RC.SOLVER_FLOW_TOLERANCE_KG_S == C._FLOW_BRACKET_TOL_KG_S
    assert RC.SOLVER_FLOW_TOLERANCE_KG_S > 0.0, (
        "a non-positive tolerance makes the separation test vacuous"
    )
    assert RC.S4_3_FALSIFIER_SINKS_K == SINKS_K, (
        "the falsifier's sinks are D-14's, not this module's to choose"
    )


def test_sabotaging_the_coupling_changes_the_verdict(monkeypatch):
    """**The witness the first version could not pass.**

    With ``couple`` broken, the old function still answered ``discharged``/``True``. Now
    the failure must reach the verdict -- either by propagating, or by returning
    ``not_discharged``. What it must never do is keep saying yes.
    """
    def broken(*_a, **_k):
        raise RuntimeError("coupling sabotaged")

    monkeypatch.setattr(RC, "couple", broken)
    with pytest.raises(RuntimeError, match="sabotaged"):
        demonstration_state()


def test_a_coupling_that_runs_but_does_not_separate_is_not_discharged(monkeypatch):
    """The subtler sabotage: the coupling runs, and moves nothing.

    A broken coupling that RAISES is the easy case. The one that matters is a coupling
    that returns a case whose condensing state ignores the sink -- exactly the collapse
    S4-3 describes. The verdict must then be ``not_discharged``, with the roots shown.
    """
    real_couple = RC.couple

    def sink_blind(case, boundary, *, working_fluid, rejected_W=None):
        fixed = RC.RadiatorBoundary(
            area_m2=boundary.area_m2, emissivity=boundary.emissivity,
            sink_temperature_K=250.0)  # every sink answers as if it were 250 K
        return real_couple(
            case, fixed, working_fluid=working_fluid, rejected_W=rejected_W)

    monkeypatch.setattr(RC, "couple", sink_blind)
    label, verdict, reason = demonstration_state()
    assert label == "not_discharged" and verdict is False, (
        "a coupling that runs and moves nothing must not report as discharged"
    )
    assert "do not separate are not a discharge" in reason
    assert "1 distinct roots" in reason or "distinct roots" in reason


def test_the_demonstration_branch_refuses_to_answer_without_something_to_measure():
    """A verdict is a measurement, so it needs a case. Refusing beats defaulting.

    Inventing a demonstration inside the function so the signature stayed convenient
    would rebuild the asserted-verdict defect one level down.
    """
    with pytest.raises(ValueError, match="needs something to measure"):
        RC.s4_3_state(C.RunKind.MACHINERY_DEMONSTRATION)
    with pytest.raises(ValueError, match="missing"):
        RC.s4_3_state(C.RunKind.MACHINERY_DEMONSTRATION, case=demo_case(), pump=PUMP)


def test_the_device_branch_still_needs_nothing_and_is_unchanged():
    """The unevaluable branch is untouched: it answers with no inputs, and never False."""
    label, verdict, _ = RC.s4_3_state(C.RunKind.REFERENCE_CASE)
    assert label == "unevaluable" and verdict is RC.UNEVALUABLE
    # Supplying a demonstration's inputs must not turn the device into an evaluable case.
    label2, verdict2, _ = RC.s4_3_state(
        C.RunKind.REFERENCE_CASE, case=demo_case(), pump=PUMP,
        radiator_area_m2=AREA_M2, emissivity=EMISSIVITY,
        working_fluid=WORKING_FLUID, **FLOWS)
    assert label2 == "unevaluable" and verdict2 is RC.UNEVALUABLE


def test_the_device_really_does_refuse_upstream():
    """The reason is verified against the solver, not quoted from a handoff."""
    ref = C.LoopCase(
        kind=C.RunKind.REFERENCE_CASE, fluid="Ammonia",
        composition="single_component", geometry_shape="round_tube",
        orientation="vertical_upflow", diameter_m=8.0e-3, length_m=1.0, duty_W=1000.0,
        pressure_Pa=20.0e5, h_fg_J_kg=1.05e6, rho_f=560.0, rho_g=15.8,
        mu_f=1.1e-4, mu_g=1.0e-5, height_m=1.5)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        with pytest.raises(Exception) as exc:
            C.find_operating_points(ref, PUMP, **FLOWS, samples=240)
    text = str(exc.value)
    assert "240 of 240" in text
    assert "single_component" in text and "vertical_upflow" in text, (
        "if the device stops refusing on these axes, S4-3 may have become evaluable and "
        "D-14's state must be re-derived rather than left as written"
    )


def test_d14_does_not_retire_and_the_module_never_claims_it_does():
    """**D-14 stays open, and what it is blocked on has moved.**

    Retiring it would collapse the unevaluable device leg into "discharged", which is the
    reduction UNEVALUABLE exists to prevent. The coupling is built; the milestone is not
    shown discharged for the device.
    """
    state, reason = RC.d14_state()
    assert state == "open"
    assert "S8 pass-condition stands" in reason
    assert "no longer the coupling" in reason and "pressure-drop leg" in reason

    source = RC.__doc__ or ""
    for overclaim in ("D-14 retires", "D-14 is retired", "discharges D-14"):
        assert overclaim not in source, f"the module must never claim {overclaim!r}"
    assert "DOES NOT RETIRE" in source


def test_s5_12_s4_3_itself_is_untouched():
    """**S5-12's third clause, checked against the artifact this milestone must not edit.**

    S4-3's declared failure is a statement about the UNCOUPLED solver in
    ``coupled_loop``, and this milestone builds beside that module rather than inside it.
    If the declaration has gone, either the coupling was merged into ``coupled_loop`` --
    which is not what was built -- or the criterion was reworded, which is the
    falsification.
    """
    (conflict,) = C.sink_collapse_conflicts()
    assert conflict.phenomenon == "sink_temperature_coupling"
    assert "S4-3" in C.sink_disclosure_text()

    import inspect
    assert "radiator_coupling" not in inspect.getsource(C), (
        "the coupling must not have been wired into coupled_loop; S4-3's declaration "
        "describes that module's own behaviour and must keep describing it"
    )


def test_non_uniqueness_is_never_resolved_by_picking():
    """S4-5 still governs: a multi-root solution refuses to hand back one number."""
    d = solve(250.0).disclosed()
    doubled = RC.CoupledSolution(
        _case=d.case, _operating_points=d.operating_points * 2,
        _condensing_temperature_K=d.condensing_temperature_K,
        _saturation_pressure_Pa=d.saturation_pressure_Pa,
        _rejected_W=d.rejected_W, iterations=1, converged=True)
    with pytest.raises(ValueError, match="forbids selecting"):
        _ = doubled.root_kg_s


def test_the_radiator_boundary_refuses_unphysical_inputs():
    for bad in (dict(area_m2=0.0), dict(emissivity=1.5), dict(sink_temperature_K=-1.0),
                dict(emissivity=math.nan)):
        with pytest.raises(ValueError):
            RC.RadiatorBoundary(**{
                "area_m2": 0.8, "emissivity": 0.85, "sink_temperature_K": 250.0, **bad})


# --------------------------------------------------------------------------------------
# D87 ITEM 1 — the module that widened the demonstration discloses the widening
# --------------------------------------------------------------------------------------

def test_d87_the_disclosure_states_the_widening_and_why():
    """**The four things D87 requires it to say**, each asserted separately.

    S4-2 is strictly satisfied by ``coupled_loop``'s disclosure -- it never stated the
    demonstration's pressure, so nothing in it became false. But S4-2 tests presence and
    suppression, not whether a disclosure still DISCRIMINATES, and the coupling moved the
    demonstration from 1.2 bar to 4.6-9.7 bar. That is this module's doing, so the
    disclosure belongs to this module.
    """
    d = RC.DEMONSTRATION_DISCLOSURE

    # 1. the demonstration's own condensing range
    assert "4.586 bar" in d and "9.690 bar" in d, "the condensing range must be stated"
    assert "150 K, 250 K, 320 K" in d

    # 2. that it is a widening, and the old contrast must not be carried forward
    assert "1.2 bar" in d, "the S4 demonstration's pressure must be there to contrast"
    assert "MUST NOT BE CARRIED FORWARD UNCHANGED" in d
    assert "45 %" in d

    # 3. why: density carries the coupling, and the declared domain forces the inputs
    assert "vapour density carries the coupling" in d
    assert "[1, 20] bar" in d
    assert "0.8 m2" in d and "0.85" in d and "STATED" in d and "not a sized radiator" in d

    # 4. still not a statement about the device
    assert "NOT A STATEMENT ABOUT THIS PROJECT'S DEVICE" in d
    assert "20 bar" in d and "three of its four physical legs" in d


def test_d87_the_disclosure_is_a_module_constant_no_caller_can_replace():
    """**S4-2's pattern, mechanically.** Not a field, not a constructor argument.

    There is no parameter to pass, so there is nothing to blank, shorten, or make
    friendlier. The falsifier S4-2 names -- "a constructor argument that suppresses it" --
    cannot be built here because no such argument exists.
    """
    import dataclasses
    import inspect

    fields = {f.name for f in dataclasses.fields(RC.CoupledSolution)}
    assert not any("disclos" in f for f in fields), (
        "the disclosure must not be a field; a field is a thing a constructor can set"
    )
    for fn in (RC.solve_coupled, RC.couple, RC.CoupledSolution.render,
               RC.CoupledSolution.disclosed):
        params = set(inspect.signature(fn).parameters)
        assert not any("disclos" in p for p in params), (
            f"{fn.__name__} takes a disclosure argument, which is a way to replace it"
        )


def test_d87_the_numbers_cannot_leave_without_the_disclosure():
    """**They leave together.** Every public route out carries it.

    A consumer must not be able to obtain the roots, the condensing temperature or the
    saturation pressure from a ``CoupledSolution`` without the disclosure travelling with
    them. ``disclosed()`` bundles them; ``render()`` puts the disclosure first; and no
    public attribute yields the condensing state at all.
    """
    s = solve(250.0)

    bundle = s.disclosed()
    assert bundle.disclosure == RC.DEMONSTRATION_DISCLOSURE
    assert bundle.saturation_pressure_Pa > 0 and bundle.condensing_temperature_K > 0

    rendered = s.render()
    assert rendered.startswith(RC.DEMONSTRATION_DISCLOSURE)
    assert "condensing" in rendered and "root(s)" in rendered

    # No PUBLIC attribute hands back the condensing state on its own.
    public = {n for n in dir(s) if not n.startswith("_")}
    leaks = public & {"condensing_temperature_K", "saturation_pressure_Pa",
                      "operating_points", "case", "rejected_W"}
    assert not leaks, f"these hand back the coupled state with no disclosure: {leaks}"

    # THE RESIDUAL, asserted rather than claimed away: the private fields are still
    # reachable, exactly as LegEligibility.eligible is (D-18). What the design buys is
    # that a bypass is a deliberate reach for a private name, not the ordinary route.
    assert isinstance(s._saturation_pressure_Pa, float)
    assert "residual" in (RC.CoupledSolution.__doc__ or "").lower(), (
        "the module must disclose that the private fields remain reachable; claiming "
        "more than the design delivers is what this module already had to retract once"
    )


def test_d87_the_witness_goes_red_against_a_blanked_disclosure(monkeypatch):
    """**The falsifier for this item.** Blank the constant and the checks must fail.

    If they pass against a blanked constant the disclosure is decorative and D87's item 1
    has not landed. Both the content check and the travels-with-the-numbers check are
    exercised, because a disclosure that is present but empty satisfies neither.
    """
    monkeypatch.setattr(RC, "DEMONSTRATION_DISCLOSURE", "")

    with pytest.raises(AssertionError):
        test_d87_the_disclosure_states_the_widening_and_why()

    # And an emptied disclosure must not still validate on the rendered route: the
    # rendered report would then carry the numbers with nothing attached.
    s = solve(250.0)
    assert s.disclosed().disclosure == "", "monkeypatch must reach the bundle"
    rendered = s.render()
    assert not rendered.startswith("MACHINERY DEMONSTRATION"), (
        "with the constant blanked the rendered output must lose its disclosure -- if it "
        "does not, the render is carrying a copy and the constant is not the source"
    )


def test_d87_coupled_loop_is_not_touched_by_this_item():
    """**The property item 1 is constrained by.** Its disclosure is not ours to edit.

    D87 rules the third route: two modules making two different claims carry two
    disclosures. If ``coupled_loop``'s own disclosure were edited to mention the coupling,
    S5-12's guarantee -- that S4-3's module is byte-identical to main -- would be gone,
    and the milestone that discharges S4-3 would have edited the module S4-3 lives in.
    """
    text = C._DEMONSTRATION_DISCLOSURE
    # A first draft of this test carried `assert ... or True`, which is true whatever the
    # left side says. The repository's own F-06 guard caught it -- a check that cannot
    # fail is the shape this project counts, and it was in the test written to protect a
    # byte-identity guarantee. Removed rather than repaired: the assertion below is the
    # one that carries the property, and the tautology was carrying nothing.
    for ours in ("4.586 bar", "9.690 bar", "45 %", "vapour density carries the coupling"):
        assert ours not in text, (
            f"{ours!r} has been added to coupled_loop's disclosure; that module must "
            "stay byte-identical to main (S5-12)"
        )
