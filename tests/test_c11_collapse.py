"""C11 regressions: declared collapses, declared detections, and the boundary between.

The check `MAINT-02-01` names has four limbs, and they are the four blocks below:

1. every collapsing term carries a non-empty ``collapses`` naming quantity and phenomena
   -- at minimum the frictional AND static terms of ``two_phase_pressure_drop()``;
2. every guard carries a ``detects`` naming its target phenomenon;
3. the shared boundary raises or annotates when ``detects`` meets ``collapses`` (C9);
4. the Ledinegg guard's output states it cannot fire against the current model.
"""

from __future__ import annotations

import pytest

from orbital_thermal import coupled_loop as C
from orbital_thermal.registry import get
from orbital_thermal.registry.collapse import (
    PHENOMENA,
    Collapse,
    CollapsedModel,
    ModelTerm,
    UndetectableError,
    assert_detectable,
    detection_conflicts,
    undetectable_disclosure,
)
from orbital_thermal.two_phase_loop import PRESSURE_DROP_MODEL

LEDINEGG = "two_phase.stability.ledinegg_static"


def _collapse(**over) -> Collapse:
    kw = dict(
        quantity="q",
        representative_value="one value",
        phenomena=("axial_profile",),
        basis="somewhere in the code",
    )
    return Collapse(**{**kw, **over})


# =============================================================================
# Limb 1 -- C11(i): collapsing terms declare what they cost
# =============================================================================


@pytest.mark.parametrize("term_name", ["frictional", "static"])
def test_c11_the_named_terms_declare_a_non_empty_collapse(term_name):
    """BOTH terms, not only the one the finding named.

    ``x_mean`` reaches the frictional term through the phase-alone gradients and the
    static term through the mixture density. A friction-only fix would have left the
    static term silently collapsing the same quantity.
    """
    (term,) = [t for t in PRESSURE_DROP_MODEL.terms if t.term == term_name]
    assert term.collapses, f"the {term_name} term declares no collapse"
    for collapse in term.collapses:
        assert collapse.quantity.strip()
        assert collapse.representative_value.strip()
        assert collapse.phenomena
        assert collapse.basis.strip()


def test_c11_the_frictional_collapse_names_the_quality_profile_and_what_it_costs():
    (term,) = [t for t in PRESSURE_DROP_MODEL.terms if t.term == "frictional"]
    (collapse,) = term.collapses
    assert "quality" in collapse.quantity.lower()
    assert "x_mean" in collapse.representative_value
    assert set(collapse.phenomena) >= {"moving_boiling_boundary", "negative_slope_segment"}


def test_c11_control_a_term_that_collapses_nothing_says_so():
    """The control. If every term declared a collapse the mechanism would say nothing.

    The acceleration term takes inlet and outlet qualities as endpoints rather than a
    representative value, so it does not collapse the profile.
    """
    (term,) = [t for t in PRESSURE_DROP_MODEL.terms if t.term == "accelerational"]
    assert term.collapses == ()
    assert [t.term for t in PRESSURE_DROP_MODEL.collapsing_terms] == ["frictional", "static"]


def test_c11_the_sweep_result_is_pinned_so_a_new_term_cannot_arrive_undeclared():
    """A term added to this boundary without a collapse verdict fails here."""
    assert [t.term for t in PRESSURE_DROP_MODEL.terms] == [
        "frictional",
        "static",
        "accelerational",
    ]


# --- the vocabulary is closed, because an empty intersection is silent -----------


def test_c11_an_unknown_phenomenon_is_refused_not_silently_ignored():
    """A typo would produce an empty intersection, reading exactly like 'no conflict'."""
    with pytest.raises(ValueError, match=r"unknown phenomena"):
        _collapse(phenomena=("negative_slope_segmnet",))


def test_c11_an_empty_phenomena_set_declares_nothing_and_is_refused():
    with pytest.raises(ValueError, match=r"declares nothing"):
        _collapse(phenomena=())


def test_c11_a_collapse_without_a_basis_is_refused():
    """A declaration that does not say where it happens cannot be checked against it."""
    with pytest.raises(ValueError, match=r"no basis"):
        _collapse(basis="   ")


def test_c11_the_declared_vocabulary_is_the_one_the_terms_and_guards_use():
    used = {p for t in PRESSURE_DROP_MODEL.terms for c in t.collapses for p in c.phenomena}
    used |= set(get(LEDINEGG).detects)
    assert used <= PHENOMENA


# =============================================================================
# Limb 2 -- C11(ii): guards declare their target
# =============================================================================


def test_c11_the_ledinegg_guard_declares_what_it_detects():
    assert get(LEDINEGG).detects == ("negative_slope_segment",)


def test_c11_a_guard_with_no_declared_target_is_refused_at_the_boundary():
    """Undeclared is indistinguishable from known-to-work, so it is not allowed."""
    with pytest.raises(ValueError, match=r"declares no 'detects'"):
        detection_conflicts(guard_id="x", detects=(), model=PRESSURE_DROP_MODEL)


def test_c11_a_guard_declaring_an_unknown_target_is_refused():
    with pytest.raises(ValueError, match=r"unknown phenomena"):
        detection_conflicts(
            guard_id="x", detects=("not_a_phenomenon",), model=PRESSURE_DROP_MODEL
        )


# =============================================================================
# Limb 3 -- the shared boundary takes the intersection (C9)
# =============================================================================


def test_c11_the_boundary_reports_the_conflict_naming_guard_term_and_phenomenon():
    (conflict,) = C.ledinegg_collapse_conflicts()
    assert conflict.guard_id == LEDINEGG
    assert conflict.phenomenon == "negative_slope_segment"
    assert conflict.term == "frictional"
    assert "x_mean" in conflict.collapse.representative_value


def test_c11_the_crosscheck_is_taken_at_the_boundary_not_restated_by_the_caller():
    """C9. The caller names a guard and a model; both declarations live elsewhere.

    Falsifiable: if ``coupled_loop`` restated either the detected phenomenon or the
    collapsed set, the two copies could drift and the guard could report itself
    healthy while the model had changed underneath it.
    """
    import inspect

    src = inspect.getsource(C.ledinegg_collapse_conflicts)
    assert "negative_slope_segment" not in src, (
        "the detected phenomenon must come from the registry entry, not be restated here"
    )
    assert "moving_boiling_boundary" not in src
    assert "detection_conflicts(" in src


def test_c11_a_model_that_collapses_nothing_produces_no_conflict():
    """The control that keeps the mechanism from being a constant.

    Without this, everything above is satisfied by a function that always reports a
    conflict.
    """
    intact = CollapsedModel(
        model="hypothetical model that integrates along the channel",
        terms=(ModelTerm(term="frictional", collapses=()),),
    )
    assert detection_conflicts(
        guard_id=LEDINEGG, detects=("negative_slope_segment",), model=intact
    ) == ()


def test_c11_a_guard_aimed_at_an_uncollapsed_phenomenon_is_not_flagged():
    """The other control: the intersection must be an intersection, not a catch-all."""
    assert detection_conflicts(
        guard_id="hypothetical", detects=("multiple_steady_states",),
        model=PRESSURE_DROP_MODEL,
    ) == ()


def test_c11_assert_detectable_raises_for_a_caller_that_depends_on_the_verdict():
    """The strict half. 'No excursion here' is a claim a blind guard has not earned."""
    with pytest.raises(UndetectableError, match=r"cannot produce a verdict"):
        assert_detectable(
            guard_id=LEDINEGG,
            detects=get(LEDINEGG).detects,
            model=PRESSURE_DROP_MODEL,
        )


def test_c11_assert_detectable_is_silent_where_the_phenomenon_survives():
    intact = CollapsedModel(model="intact", terms=(ModelTerm(term="frictional"),))
    assert_detectable(guard_id=LEDINEGG, detects=("negative_slope_segment",), model=intact)


# =============================================================================
# Limb 4 -- the output statement, and it is DERIVED
# =============================================================================


def test_c11_the_disclosure_is_derived_and_disappears_when_the_collapse_does():
    """The whole of C11's second limb.

    The statement used to be a hand-written constant that happened to be true. Derived,
    the sentence and the condition it describes cannot drift apart -- and an
    integration along the channel would remove the disclosure without anyone editing
    prose.
    """
    assert "UNABLE TO FIRE ON THIS MODEL" in C.ledinegg_disclosure_text()
    assert undetectable_disclosure((), guard_name="Ledinegg guard") == ""


def test_c11_the_disclosure_names_the_phenomenon_and_the_term_that_took_it():
    text = C.ledinegg_disclosure_text()
    assert "negative_slope_segment" in text
    assert "frictional" in text
    assert "x_mean" in text


def test_c11_it_does_not_claim_the_gap_is_closed():
    """C11 makes the gap visible; it does not close it, and must not say it does."""
    text = C.ledinegg_disclosure_text().lower()
    assert "does not by itself discharge the requirement" in text
    for forbidden in ("d-12 retired", "requirement discharged", "gap closed"):
        assert forbidden not in text


@pytest.mark.parametrize("solve", ["demo", "ref"])
def test_c11_both_run_kinds_carry_the_derived_disclosure_in_the_output(solve):
    from tests.test_coupled_loop import solve_demo, solve_ref

    result = (solve_demo if solve == "demo" else solve_ref)()
    text = C.ledinegg_disclosure_text()
    # The emptiness assertion is not decoration. `"" in anything` is True, so without
    # it this test passes vacuously the moment the cross-check stops finding a
    # conflict -- which is exactly the state the mutation harness puts the tree in.
    assert text, "the derived disclosure is empty, so the containment check is vacuous"
    assert text in result.render()
