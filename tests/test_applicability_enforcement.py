"""R1 class-level regression: declared applicability must be BINDING, on every axis.

**The defect class.** Five of the ten OTB-G001 findings were one defect wearing
different clothes -- *a declared constraint that is recorded but never enforced*:

| Sibling | The constraint that existed but did nothing |
|---|---|
| F-02 | a CHF value had no required provenance -- any bare float was accepted |
| F-03 | an entry with no evaluator still passed the rank-eligibility guard |
| F-04 | the fluid-applicability failure was written to a note, then ignored |
| F-06 | the correlation's turbulent basis was documented, never checked |
| D-9  | "tubes and annuli" was in the docstring, enforced nowhere |

The project's R1 standard requires a regression exercising **at least three sibling
instances of the class plus a control**, or a stated reason the class is a singleton.
It is not a singleton: five siblings are named above, and this module exercises all
five plus two controls.

**The control matters as much as the siblings.** A guard that de-ranks everything is
not enforcement, it is breakage; these tests therefore also pin the cases that must
still pass, so over-enforcement fails just as loudly as under-enforcement.

The sibling tests here are deliberately written against the *mechanism*
(:mod:`orbital_thermal.registry.applicability`) rather than against each correlation,
because that is the thing whose absence caused all five. Per-correlation wiring is
checked in ``test_two_phase_evaporator.py``.
"""

from __future__ import annotations

import pytest

from orbital_thermal.registry import get
from orbital_thermal.registry.applicability import (
    UNCONSTRAINED,
    Applicability,
    Axis,
    Consequence,
    DomainProvenance,
    worst,
)

# A spec that declares every enforceable axis, used to exercise the mechanism itself.
FULL = Applicability(
    fluids=frozenset({"water", "r-22"}),
    fluids_basis="test basis",
    geometries=frozenset({"round_tube", "annulus"}),
    geometries_basis="test basis",
    orientations=frozenset({"vertical_upflow"}),
    orientations_basis="test basis",
    min_liquid_reynolds=3000.0,
    reynolds_basis="test basis",
)

FULLY_STATED = dict(
    fluid="water",
    geometry="round_tube",
    orientation="vertical_upflow",
    liquid_reynolds=1.0e4,
)


# =============================================================================
# CONTROL 1 -- a fully applicable case passes cleanly
# =============================================================================


def test_control_a_fully_applicable_case_has_no_violations():
    """The control. Enforcement that never passes anything is not enforcement."""
    assert FULL.check(**FULLY_STATED) == ()


def test_control_an_unconstrained_spec_constrains_nothing():
    """A correlation that declares no axis is not silently constrained by the mechanism."""
    assert UNCONSTRAINED.check() == ()
    assert UNCONSTRAINED.declared_axes == ()


# =============================================================================
# SIBLING 1 (F-04) -- fluid applicability alters status, not just a note
# =============================================================================


def test_sibling_fluid_outside_the_database_is_de_ranked():
    v = FULL.check(**{**FULLY_STATED, "fluid": "ammonia"})
    assert [x.axis for x in v] == [Axis.FLUID]
    assert v[0].consequence is Consequence.DE_RANK


def test_sibling_explicitly_excluded_fluid_is_de_ranked():
    """The exclusion form, used where the inclusive list cannot be enumerated.

    Shah (1987)'s 23-fluid database is not enumerated in either consulted printing, so
    no inclusive list may be asserted (C1) -- but ammonia's absence IS established, and
    that is what gets enforced.
    """
    spec = Applicability(excluded_fluids=frozenset({"ammonia"}), fluids_basis="b")
    assert spec.check(fluid="water") == ()
    v = spec.check(fluid="Ammonia")
    assert v and v[0].axis is Axis.FLUID and v[0].consequence is Consequence.DE_RANK


# =============================================================================
# SIBLING 2 (F-06) -- the turbulent basis is checked, not merely documented
# =============================================================================


@pytest.mark.parametrize("re_l", [0.3, 100.0, 2999.0])
def test_sibling_laminar_liquid_reynolds_is_rejected(re_l):
    """Re_L = 0.3 is the worst combination the review found inside the declared box."""
    v = FULL.check(**{**FULLY_STATED, "liquid_reynolds": re_l})
    assert [x.axis for x in v] == [Axis.REGIME]
    assert v[0].consequence is Consequence.REJECT


def test_sibling_turbulent_liquid_reynolds_passes():
    assert FULL.check(**{**FULLY_STATED, "liquid_reynolds": 3000.0}) == ()


# =============================================================================
# SIBLING 3 (D-9) -- geometry is enforced, closing the tubes-and-annuli hole
# =============================================================================


def test_sibling_geometry_outside_the_basis_is_de_ranked():
    """DEBTS D-9: the geometry basis lived in a title and was enforced nowhere.

    It becomes live the moment a cold-plate or chevron-channel geometry with a
    plausible hydraulic diameter is supplied -- which is exactly this case.
    """
    v = FULL.check(**{**FULLY_STATED, "geometry": "chevron_plate"})
    assert [x.axis for x in v] == [Axis.GEOMETRY]
    assert v[0].consequence is Consequence.DE_RANK


def test_sibling_both_declared_geometries_are_accepted():
    """"Tubes AND annuli" -- the basis is not narrowed to tubes by the fix."""
    for shape in ("round_tube", "annulus"):
        assert FULL.check(**{**FULLY_STATED, "geometry": shape}) == ()


# =============================================================================
# SIBLING 4 (F-03) -- provenance: no evaluator, no eligibility
# =============================================================================


def test_sibling_missing_executable_form_blocks_when_a_value_is_needed():
    spec = Applicability(requires_executable_form=True)
    assert spec.check(has_executable_form=True) == ()
    v = spec.check(has_executable_form=False)
    assert [x.axis for x in v] == [Axis.PROVENANCE]
    assert v[0].consequence is Consequence.BLOCK


# =============================================================================
# SIBLING 5 (F-02) -- provenance of a supplied value; see the ChfResult tests in
# test_two_phase_evaporator.py for the wiring. Here: the axis exists and is typed.
# =============================================================================


def test_sibling_declared_axes_are_discoverable():
    """Every declared axis is enumerable, so "declared but unenforced" is detectable."""
    assert set(FULL.declared_axes) == {
        Axis.FLUID,
        Axis.GEOMETRY,
        Axis.ORIENTATION,
        Axis.REGIME,
    }


# =============================================================================
# THE RULE THAT MAKES THE CLASS CLOSED: silence is not consent
# =============================================================================


@pytest.mark.parametrize(
    "omitted,axis",
    [
        ("fluid", Axis.FLUID),
        ("geometry", Axis.GEOMETRY),
        ("orientation", Axis.ORIENTATION),
        ("liquid_reynolds", Axis.REGIME),
    ],
)
def test_a_declared_axis_with_no_stated_value_blocks(omitted, axis):
    """An unstated axis is a BLOCK, not a pass.

    This is the rule that actually closes the class. Without it, "declared but never
    enforced" simply returns as "declared, enforced only when someone remembers to pass
    it" -- which is what D-9 already was.
    """
    stated = {**FULLY_STATED, omitted: None}
    v = FULL.check(**stated)
    assert [x.axis for x in v] == [axis]
    assert v[0].consequence is Consequence.BLOCK


def test_multiple_axis_failures_are_all_reported():
    """Enforcement reports every failing axis, not just the first."""
    v = FULL.check(fluid="ammonia", geometry="chevron_plate", orientation="horizontal",
                   liquid_reynolds=10.0)
    assert {x.axis for x in v} == {Axis.FLUID, Axis.GEOMETRY, Axis.ORIENTATION, Axis.REGIME}


def test_every_consequence_maps_to_a_status_that_actually_de_ranks():
    """The seam between the registry's consequences and Stage-2 statuses (F-04).

    This mapping is where "recorded but not enforced" would come back: if
    ``DE_RANK`` mapped to ``RANK_ELIGIBLE`` the violations would still be *reported*
    on every assessment and change nothing at all -- which is precisely the defect.

    The mutation witness showed this needs its own test: a full ammonia case is
    de-ranked by two independent paths (the fluid axis and the CHF result's
    ``is_sourced`` check), so breaking the mapping alone left those tests green.
    """
    from orbital_thermal.two_phase import _CONSEQUENCE_TO_STATUS, RankStatus

    assert _CONSEQUENCE_TO_STATUS[Consequence.DE_RANK] is RankStatus.SENSITIVITY_ONLY
    assert _CONSEQUENCE_TO_STATUS[Consequence.REJECT] is RankStatus.REJECTED
    assert _CONSEQUENCE_TO_STATUS[Consequence.BLOCK] is RankStatus.BLOCKED
    assert RankStatus.RANK_ELIGIBLE not in _CONSEQUENCE_TO_STATUS.values(), (
        "no violation may map to a rankable status -- that would make enforcement a "
        "no-op while still printing the violations"
    )
    assert set(_CONSEQUENCE_TO_STATUS) == set(Consequence), (
        "every consequence must have a status, or a new one would silently do nothing"
    )


def test_worst_consequence_selects_the_most_severe():
    assert worst([]) is None
    assert worst([Consequence.DE_RANK]) is Consequence.DE_RANK
    assert worst([Consequence.DE_RANK, Consequence.BLOCK]) is Consequence.BLOCK
    assert worst([Consequence.REJECT, Consequence.DE_RANK]) is Consequence.REJECT


# =============================================================================
# The gravity axis -- Shah (1987) is gravity-EXPLICIT, not merely 1g-derived
# =============================================================================


def test_gravity_explicit_correlation_rejects_zero_gravity():
    """A literal g in the correlating parameter, not the standing 1g caveat.

    Shah (1987)'s Y divides by g, so as g -> 0 the correlation diverges: it has no
    microgravity limit at all. For an orbital thermal project that must be a guard,
    not a sentence in a docstring.
    """
    spec = Applicability(gravity_explicit=True, gravity_basis="Y contains g")
    assert spec.check(gravity_m_s2=9.80665) == ()

    blocked = spec.check(gravity_m_s2=None)
    assert blocked and blocked[0].consequence is Consequence.BLOCK

    rejected = spec.check(gravity_m_s2=0.0)
    assert rejected and rejected[0].consequence is Consequence.REJECT
    assert "no zero-gravity limit" in rejected[0].detail


# =============================================================================
# Provenance labelling is a LABEL, not a weapon (Director ruling D1 / F-08)
# =============================================================================


def test_unestablished_numeric_provenance_is_a_caveat_not_a_violation():
    """Director direction on F-08 is that the relabelling is "labelling only".

    The numeric box stays enforced by ``assert_in_domain`` and is surfaced as a
    caveat, but it must not de-rank a case on its own -- doing so would over-enforce
    past the ruling and de-rank every case through Gungor & Winterton regardless of
    merit.
    """
    spec = Applicability(
        numeric_domain_provenance=DomainProvenance.UNESTABLISHED,
        numeric_domain_note="not in any consulted source",
    )
    assert spec.check() == (), "an unsourced numeric box must not itself de-rank"
    caveats = spec.provenance_caveats()
    assert caveats and "NOT the authors' declared range" in caveats[0]


def test_unenforced_axes_are_recorded_rather_than_silently_absent():
    spec = Applicability(unenforced_axes=("liquid Prandtl: no sourced band obtained",))
    assert any("Prandtl" in c for c in spec.provenance_caveats())


# =============================================================================
# The mechanism is actually wired to the shipped entries
# =============================================================================


@pytest.mark.parametrize(
    "cid", ["two_phase.htc.gungor_winterton", "two_phase.chf.shah_1987"]
)
def test_shipped_reference_correlations_declare_an_enforceable_spec(cid):
    """Both implemented references carry a spec -- the fix is applied, not just built."""
    spec = get(cid).applicability_spec
    assert spec is not None, f"{cid} must declare an enforceable applicability spec"
    assert spec.declared_axes, f"{cid}'s spec declares no axis"
    assert Axis.FLUID in spec.declared_axes
    assert Axis.GEOMETRY in spec.declared_axes, "closes DEBTS D-9 for this entry"


def test_gw86_spec_matches_the_sourced_seven_fluid_database():
    from orbital_thermal.registry.two_phase import GW86_DATABASE_FLUIDS

    spec = get("two_phase.htc.gungor_winterton").applicability_spec
    assert spec.fluids == GW86_DATABASE_FLUIDS
    assert len(spec.fluids) == 7, "the database agreed by five independent sources"
    assert "ammonia" not in {f.lower() for f in spec.fluids}
    assert spec.min_liquid_reynolds == 3000.0
    assert spec.numeric_domain_provenance is DomainProvenance.UNESTABLISHED


def test_shah_1987_spec_carries_the_gravity_axis_and_the_ammonia_exclusion():
    spec = get("two_phase.chf.shah_1987").applicability_spec
    assert spec.gravity_explicit is True
    assert "ammonia" in {f.lower() for f in spec.excluded_fluids}
    assert spec.geometries == frozenset({"round_tube"})
    assert spec.numeric_domain_provenance is DomainProvenance.CONFLICTED
