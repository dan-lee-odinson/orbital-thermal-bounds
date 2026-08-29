"""S5 two-phase architecture cases — one witness per acceptance criterion it holds.

Criteria file: ``ACCEPTANCE_CRITERIA_OTB-G005.md``. All fourteen criteria have a witness.

**Two of them are honest about being weaker than they look, and that is deliberate.**
S5-5 is only PARTIALLY discharged -- ``LegEligibility.eligible`` is a public field, so the
gravity basis can be dropped in one attribute access; the guard buys visibility, not
impossibility, and ``test_s5_5_the_residual_public_eligible_field_is_recorded`` pins that
so the claim cannot re-inflate (D-18, closing at S6).

**S5-13 IS NOT VACUOUS AND THIS HEADER USED TO SAY IT WAS.** The coupling IS built
(D85), and S5-13 is NOT DISCHARGED -- terminally, on both legs. The demonstration that
once discharged it was a hybrid case and the discharge was withdrawn at D90/F-01; no
consistent demonstration is available, because the only implemented pressure-drop
correlation admits ``two_component`` only while a condensing state exists for a single
substance only. The operative state lives in ``radiator_coupling`` and is asserted in
``tests/test_radiator_coupling.py``; the test that used to assert vacuity here is
deleted, not repaired (D90/F-06).

**Every test below is named for the criterion it holds and fails when that criterion's own
falsifier is introduced.** `OTB-G002` criterion 8 — every new check has been witnessed
failing — is discharged for these by ``tests/../scripts/witness_s2_checks.py`` anchors and,
where the falsifier is structural rather than numeric, by the test constructing the
falsifying shape itself and requiring it to be refused.
"""

from __future__ import annotations

import ast
import builtins
import dataclasses
import enum
import inspect
import math
import pathlib
import re
import subprocess
import sys
import warnings
from typing import NamedTuple

import pytest
from conftest import _child_env

from orbital_thermal import two_phase_architecture_cases as ac
from orbital_thermal.registry import applicability as _applicability
from orbital_thermal.registry import two_phase as _tp_module
from orbital_thermal.registry.applicability import (
    Applicability,
    Axis,
    Cause,
    Consequence,
)
from orbital_thermal.registry.provenance import CorrelationEntry, Status

#: Standard gravity, as the registry declares it. Read from the adopted CHF entry rather
#: than written here, so this file cannot drift from the source the ruling rests on.
_ADOPTED_CHF = ac.adopted_entry("chf")
_REFERENCE_G = _ADOPTED_CHF.applicability_spec.reference_gravity_m_s2
_MICROGRAVITY = 1e-6  # LEO, the D-10 divergence table's own case

#: A case specified on every axis the adopted CHF correlation declares. Without it the
#: geometry and orientation axes BLOCK and every result is refused for reasons that have
#: nothing to do with gravity -- which would make the D6 witnesses pass for the wrong
#: reason. Water is the fluid because ammonia is explicitly OUTSIDE Shah (1987)'s fluid
#: basis, which is debt D-6's subject, not D6's.
_FULL_CASE = {"geometry": "round_tube", "orientation": "vertical_upflow"}


#: The values the computation states from the entry rather than accepting from a caller.
_STATED_BY_THE_COMPUTATION = frozenset({"fluid", "gravity_m_s2", "has_executable_form"})


#: Values chosen so that a refusal in the S5-1 property means the input was REFUSED
#: rather than merely malformed. Anything not named here is probed with a float.
_PLAUSIBLE_VALUE_FOR = {
    "fluid": "water",
    "composition": "two_component",
    "geometry": "round_tube",
    "orientation": "vertical_upflow",
    "has_executable_form": True,
}

def _checked(leg):
    """Violations from axes that were actually evaluated.

    D118: ``BLOCK`` is the vocabulary's word for *"cannot be evaluated because a
    required statement or source is missing"*, so a ``BLOCK`` is not a finding about the
    case -- it is the absence of one. Assertions about what the mechanism CONCLUDED are
    written against this; assertions about what it could not reach use
    :func:`_unevaluable`. Before D118 the two were indistinguishable at the CHF leg,
    because the branch axis passed in silence instead of blocking.
    """
    # D119: split on WHY, not on WHAT. A BLOCK raised because the entry failed a
    # declared requirement is a conclusion the mechanism reached, so it belongs
    # here; only a BLOCK raised because nothing was stated is an absence.
    return tuple(v for v in leg.violations if v.cause is Cause.EVALUATED_AND_FAILED)


def _unevaluable(leg):
    """The axes the assessment could not check, as violations."""
    return tuple(v for v in leg.violations if v.cause is Cause.NOT_EVALUATED)

class _RouteNotExercised(UserWarning):
    """A construction route this interpreter cannot offer, so the witness could not run it.

    Its own category so a reader can tell it from an ordinary warning, and so the
    visibility check below can find it without matching on prose.
    """


# --------------------------------------------------------------------------------------
# S5-1 — eligibility is derived, not declared
# --------------------------------------------------------------------------------------

def test_s5_1_eligibility_moves_when_the_adopted_correlation_set_moves():
    """**S5-1.** The falsifier is "an eligibility that does not change when a
    correlation's adoption status changes". So change one and require it to move.

    This is the whole difference between a rule and a list: a list would score the same
    either way.
    """
    before = ac.assess_fluid("ammonia", gravity_m_s2=_REFERENCE_G)
    assert "chf" in before.legs, "the adopted CHF correlation must produce a leg"

    # De-adopt the CHF correlation by moving it out of RESOLVED. Nothing else changes.
    demoted = tuple(
        dataclasses.replace(e, status=Status.SENSITIVITY)
        if e.id == _ADOPTED_CHF.id else e
        for e in ac.REGISTRY_ENTRIES
    )
    # D104: the seam, not the API. It is private and named so this line cannot be
    # mistaken for something a consumer would write.
    after = ac._assess_fluid_against_a_supplied_registry(
        demoted, "ammonia", gravity_m_s2=_REFERENCE_G)
    assert "chf" not in after.legs, (
        "de-adopting the CHF correlation must remove the CHF leg; if it does not, "
        "eligibility is a list rather than a rule"
    )


def test_s5_1_no_caller_argument_can_set_an_outcome():
    """**S5-1**'s third falsifier: "an eligibility that can be set by a caller".

    **D119 rewrote this witness. The criterion is unchanged; only the evidence is.**

    It used to check five spellings -- ``eligible``, ``eligibility``, ``force``,
    ``override``, ``result`` -- against the *named* parameters of the two entry points.
    ``inspect.signature`` reports ``**case`` as a single ``VAR_KEYWORD`` entry, so the
    witness for "no caller argument can set an outcome" could not see the forwarding
    channel -- and that channel is the one both of the last two findings arrived
    through, and the only one that has ever carried one. A name-list guarding two
    signatures could not have caught ``has_executable_form`` or ``branch_value``,
    because neither is spelled like an outcome.

    So the property is derived over the whole public surface instead. Every input a
    caller can supply, from the entry points' signatures *and* from
    :meth:`Applicability.check` whose parameters ``**case`` forwards, must be one of:

    * **refused** -- it never reaches the computation; or
    * **accepted, and primitive** -- a declared case fact, which
      ``test_d118_no_case_fact_is_a_derived_quantity`` separately certifies is not a
      quantity production code works out.

    An input that is accepted *and* derived is exactly "a caller setting an outcome",
    stated as a property rather than as a vocabulary. The five spellings are kept below
    because they cost nothing, but they are corroboration now, not the check.
    """
    for fn in (ac.assess_fluid, ac.assess_leg):
        params = set(inspect.signature(fn).parameters)
        assert not (params & {"eligible", "eligibility", "force", "override", "result"}), (
            f"{fn.__name__} takes an argument that could set an outcome: {sorted(params)}"
        )

    derived = _derived_quantities_in_production()
    assert derived, "the derivation found nothing, so the property below is vacuous"

    accepted_and_derived = []
    for name in sorted(_public_case_inputs()):
        if name in _STATED_BY_THE_COMPUTATION or name == "leg":
            continue  # stated by the computation, or the leg being assessed
        try:
            _assess_with(name, _PLAUSIBLE_VALUE_FOR.get(name, 1.0e6))
        except TypeError as refusal:
            assert "not a case fact" in str(refusal), (
                f"{name} was refused for an unrelated reason: {refusal}"
            )
            continue
        except ValueError:
            continue  # reached a validator and was refused by it -- still not accepted
        if name in derived:
            accepted_and_derived.append(name)

    assert not accepted_and_derived, (
        "these inputs are accepted from a caller AND are quantities production code "
        f"derives, so a caller supplies the value the rule is applied to: "
        f"{accepted_and_derived}. That is an eligibility a caller can set."
    )


def test_s5_1_an_absent_correlation_is_not_an_ineligibility():
    """No adopted correlation returns ``None``, which S4-8 requires to stay distinct from
    a refusal: "no correlation exists" and "one exists and refuses" are different claims.
    """
    stripped = tuple(e for e in ac.REGISTRY_ENTRIES if e.kind != "chf")
    assert ac._assess_leg_against_a_supplied_registry(
        stripped, "ammonia", "chf", gravity_m_s2=_REFERENCE_G) is None
    refused = ac.assess_leg("ammonia", "chf", gravity_m_s2=_MICROGRAVITY)
    assert refused is not None and refused.eligible is False, (
        "a correlation that exists and refuses must produce a record, not an absence"
    )


# --------------------------------------------------------------------------------------
# S5-2 — per leg, never collapsed
# --------------------------------------------------------------------------------------

def test_s5_2_a_fluid_eligibility_refuses_to_collapse_to_one_value():
    """**S5-2.** The falsifier is "a single boolean covering several legs"."""
    result = ac.assess_fluid("ammonia", gravity_m_s2=_REFERENCE_G)
    with pytest.raises(TypeError, match="does not collapse"):
        bool(result)

    assert not any(
        isinstance(getattr(type(result), n, None), property) and "overall" in n
        for n in dir(result)
    ), "no overall-verdict property may exist"
    assert set(result.legs) <= set(ac.RANKING_LEGS)


def test_s5_2_partial_eligibility_is_reported_as_partial():
    """A fluid refused on one leg and admitted on another reports exactly that."""
    result = ac.assess_fluid("ammonia", gravity_m_s2=_MICROGRAVITY)
    outcomes = {leg: result.legs[leg].eligible for leg in result.legs}
    assert outcomes["chf"] is False, "microgravity must refuse the CHF leg (D6)"
    assert len(set(outcomes.values())) >= 1
    # The records keep the legs apart rather than merging them.
    records = result.as_records()
    assert [r["leg"] for r in records] == [
        leg for leg in ac.RANKING_LEGS if leg in result.legs]


# --------------------------------------------------------------------------------------
# S5-3 — no ordering
# --------------------------------------------------------------------------------------

def test_s5_3_the_module_emits_no_ordering():
    """**S5-3.** Falsifier: "any S5 entry point returning a rank, a score, an ordering".

    Checked structurally, over the module's own source and its public types: no ordering
    dunder, no sort, no comparison. A test that only checked today's return values would
    pass the moment someone added ``rank()`` next week.
    """
    source = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    for forbidden in ("__lt__", "__gt__", "__le__", "__ge__"):
        assert forbidden not in source, f"{forbidden} appears in an S5 module"

    # NOT a ban on ``sorted``: the module sorts LEG NAMES alphabetically inside a
    # diagnostic message, which orders nothing a reader could mistake for a result. The
    # first draft of this test banned the token and failed on exactly that, which is a
    # check measuring the wrong property -- the same shape as a probe that fires no
    # marker. What S5-3 forbids is an ordering OF COOLANTS, so that is what is asserted:
    # record order is the DECLARED leg order, fixed in data, not computed from any value.
    result = ac.assess_fluid("water", gravity_m_s2=_REFERENCE_G, **_FULL_CASE)
    assert [r["leg"] for r in result.as_records()] == [
        leg for leg in ac.RANKING_LEGS if leg in result.legs]

    for name in dir(ac):
        if name.startswith("_"):
            continue
        obj = getattr(ac, name)
        if not callable(obj) or isinstance(obj, type):
            continue
        # "de-rank" is the ENFORCEMENT verb -- Consequence.DE_RANK, the mechanism D6
        # travels on -- and it is the opposite of emitting an ordering. The first draft
        # of this check flagged `gravity_derank_axis` on a bare substring match, which
        # would have condemned the very mechanism the criteria require.
        stem = re.sub(r"de[-_]?rank", "", name, flags=re.I)
        assert not re.search(r"\brank|score|order|best|prefer", stem, re.I), (
            f"{name} names an ordering operation"
        )


# --------------------------------------------------------------------------------------
# S5-4 / S5-5 — the gravity basis is present, and non-droppable   [D6 · due at S5]
# --------------------------------------------------------------------------------------

def test_s5_4_a_chf_leg_cannot_be_constructed_without_a_gravity_basis():
    """**S5-4.** Falsifier: "a CHF-dependent eligibility record constructible with an
    absent, empty, or defaulted gravity basis"."""
    with pytest.raises(TypeError, match="constructible only by the computation"):
        ac.LegEligibility(
            fluid="ammonia", leg="chf", entry_id="two_phase.chf.shah_1987", eligible=True)

    # A non-CHF leg is unaffected -- the obligation is specific, not blanket.
    ok = ac.LegEligibility(
        fluid="ammonia", leg="dp", entry_id="two_phase.dp.lockhart_martinelli_chisholm",
        eligible=True)
    assert ok.gravity_basis is None and bool(ok) is True


def test_s5_4_the_basis_comes_from_the_registry_not_from_a_caller():
    """**S5-4.** Falsifier: "a basis suppliable or overridable by a caller".

    ``GravityBasis`` has exactly one constructor that reads a source, and an entry with no
    declared reference gravity is REFUSED rather than defaulted -- inventing standard
    gravity here would fabricate the sourced boundary D6 rests on.
    """
    basis = ac.GravityBasis.from_entry(_ADOPTED_CHF)
    assert basis.reference_gravity_m_s2 == _REFERENCE_G
    assert basis.entry_id == _ADOPTED_CHF.id
    assert basis.basis, "the sourced sentence must travel with the number"

    no_gravity = next(
        e for e in ac.REGISTRY_ENTRIES
        if getattr(getattr(e, "applicability_spec", None), "reference_gravity_m_s2", None) is None
    )
    with pytest.raises(ValueError, match="no declared reference gravity"):
        ac.GravityBasis.from_entry(no_gravity)

    assert "gravity_m_s2" not in inspect.signature(ac.GravityBasis.from_entry).parameters


def test_s5_5_a_chf_eligibility_has_no_bare_truth_value():
    """**S5-5, and this is the criterion that actually discharges D6's S5 half.**

    S5-4 makes the basis present. Only this makes it non-droppable: ``if eligible:`` is
    precisely the reduction a downstream ranking performs when it loses the basis, so for
    a CHF-dependent record that reduction raises.

    The D75 lesson one level out — a sentinel that is merely unusual gets read as falsy or
    truthy by the first ``if`` that meets it.
    """
    chf = ac.assess_leg("water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE)
    assert chf is not None and chf.gravity_basis is not None
    with pytest.raises(TypeError, match="no bare truth value"):
        bool(chf)
    with pytest.raises(TypeError):
        _ = "yes" if chf else "no"
    # .eligible remains available for a caller that HAS accounted for the basis.
    # What it SAYS is not this test's subject -- D118 made the CHF leg unevaluable
    # on the branch axis, and S5-5 is about the accessor existing, not the verdict.
    assert isinstance(chf.eligible, bool)


def test_s5_5_no_projection_yields_chf_eligibility_without_its_basis():
    """**S5-5.** Falsifier: "any projection, serialisation, export, or convenience
    accessor that yields CHF-dependent eligibility without its basis and still validates".
    """
    chf = ac.assess_leg("ammonia", "chf", gravity_m_s2=_REFERENCE_G)
    record = chf.as_record()
    assert "gravity_basis" in record and record["gravity_basis"]["reference_gravity_m_s2"] == _REFERENCE_G

    # Every public projection out of the module is enumerated and checked, so a new one
    # cannot be added without this test being updated deliberately.
    projections = {
        n for n in dir(ac.LegEligibility)
        if not n.startswith("_") and callable(getattr(ac.LegEligibility, n))
    }
    assert projections == {"as_record"}, (
        f"a new projection appeared on LegEligibility: {sorted(projections)}. "
        "S5-5 requires every one of them to carry the basis or refuse."
    )

    for rec in ac.assess_fluid("ammonia", gravity_m_s2=_REFERENCE_G).as_records():
        if rec["leg"] in ac.CHF_DEPENDENT_LEGS:
            assert rec.get("gravity_basis"), "a CHF record reached a consumer basis-less"


def test_s5_5_the_residual_public_eligible_field_is_recorded():
    """**S5-5 is NOT fully discharged, and this test exists so nobody can say it is.**

    ``LegEligibility.eligible`` is a public field: ``chf_leg.eligible`` yields a bare
    boolean with no gravity basis, in one attribute access. S5-5's falsifier names *"any
    convenience accessor that yields CHF-dependent eligibility without its basis"*, and a
    public attribute is one. The guard on ``__bool__`` therefore buys **visibility, not
    impossibility**: a consumer that wants the bare flag must write ``.eligible``, which
    is a deliberate act a reviewer can see in a diff, where ``if leg:`` reads as ordinary
    code.

    This test asserts the hole is real and that the module's own text still says so. It is
    the anti-drift check: the first version of that docstring claimed the basis was
    "non-droppable" and that the module "cannot produce that shape", and both were false
    while this field was public. A claim about a guarantee is exactly the kind of thing
    that re-inflates during a later edit, so it is pinned rather than trusted.
    """
    chf = ac.assess_leg("water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE)

    # The hole, demonstrated rather than described.
    bare = chf.eligible
    assert isinstance(bare, bool), (
        "if .eligible has stopped being a bare bool the residual may be closed -- "
        "re-read the module docstring and update it before deleting this test"
    )

    # The module must keep DISCLOSING it, in these words or better.
    source = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    assert "RESIDUAL" in source.upper(), "the residual must stay disclosed in the module"
    assert "public field" in source, "the disclosure must name the mechanism"
    assert "VISIBLE, not impossible" in source, (
        "the module must state what the guard actually buys"
    )

    # The two sentences that were WRONG must not come back. Checked as whole claims and
    # not as substrings: the first draft of this check banned the token "non-droppable",
    # which fired on the disclaimer "this module does NOT make the basis non-droppable"
    # -- a check tripping on the statement of the rule instead of on a breach of it, the
    # same error as scanning the criteria document for the words it forbids. Three times
    # now in this milestone, which is itself the finding.
    for overclaim in (
        "That is what makes the basis non-droppable",
        "only projection this module offers, and it cannot produce that shape",
    ):
        assert overclaim not in source, (
            f"the retracted claim {overclaim!r} has returned while .eligible is public"
        )


# --------------------------------------------------------------------------------------
# S5-6 — enforcement is the registry's path, not a second one   [D6 · due at S5]
# --------------------------------------------------------------------------------------

def test_s5_6_microgravity_de_ranks_the_chf_leg_through_the_orientation_axis():
    """**S5-6.** Falsifier: "a CHF-dependent eligibility returned as True at a gravity
    outside ``reference_gravity_m_s2 ± gravity_rel_tol``; a caveat string substituted for
    the de-rank".

    D-10's own divergence table is the measurement the ruling rests on: at LEO
    micro-gravity Shah's ``Y`` reaches 1.111e8 against 1.774e5 at Earth, and the method's
    branch threshold is crossed somewhere between Mars and milli-g.
    """
    chf = ac.assess_leg("ammonia", "chf", gravity_m_s2=_MICROGRAVITY)
    assert chf.eligible is False, "microgravity CHF eligibility must be refused, not caveated"
    axes = {v.axis for v in chf.violations}
    assert Axis.ORIENTATION in axes, (
        "the refusal must travel on the orientation axis -- that is D6's mechanism"
    )
    assert any(v.consequence is Consequence.DE_RANK for v in chf.violations)
    assert any("Director ruling D6" in v.detail for v in chf.violations), (
        "the refusal must cite the ruling it enforces"
    )


def test_s5_6_the_module_carries_no_second_gravity_comparison():
    """**S5-6.** Falsifier: "a second, parallel gravity check that can disagree with the
    registry's". The only gravity arithmetic permitted here is handing the value to
    ``Applicability.check``."""
    source = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    body = _executable_lines(source)
    assert "def assess_leg(" in body, (
        "the docstring stripper removed executable code too, so an empty body would pass"
    )
    for forbidden in ("gravity_rel_tol", "9.80665", "abs(gravity", "> ref", "< ref"):
        assert forbidden not in body, (
            f"{forbidden!r} appears in executable code: this module must not re-implement "
            "the registry's gravity comparison beside it"
        )
    assert ac.gravity_derank_axis() is Axis.ORIENTATION


def test_s5_6_eligibility_holds_at_the_reference_gravity_negative_control():
    """The de-rank is not a way to refuse everything: at 1 g the CHF leg is eligible."""
    chf = ac.assess_leg("water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE)
    assert _checked(chf) == (), (
        "at 1 g no evaluated axis may find against the case; the branch axis is "
        "unevaluable here (D118) and that is an absence of a finding, not one"
    )
    assert not [
        v for v in chf.violations
        if v.axis is Axis.ORIENTATION and v.consequence is Consequence.DE_RANK
    ]

    # And the D6 refusal is ISOLATED: at micro-gravity the same fully-specified water
    # case is refused on the orientation axis and on nothing else, so the de-rank cannot
    # be an artefact of an unrelated axis happening to fire.
    micro = ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    assert micro.eligible is False
    assert {v.axis for v in micro.violations} == {Axis.ORIENTATION}


# --------------------------------------------------------------------------------------
# S5-7 — no direction claimed for CHF error   [D-7 · S6, anticipated only]
# --------------------------------------------------------------------------------------

def test_s5_7_no_s5_text_states_a_direction_for_chf_error_in_microgravity():
    """**S5-7.** Falsifier: any output, docstring or doc claiming 1-g CHF correlations
    over-predict, under-predict, are conservative, or are non-conservative in microgravity.

    D-7's refinement is why: the "known direction" is Hammer (2021) and is about the
    **HTC**; for **CHF**, Kharangate (2015) places microgravity predictions *between* the
    Earth-gravity orientation extremes, so the sign depends on the orientation the 1-g
    correlation was taken at. D-7 says its own title invites the conflation.

    Checked over the S5 module's own text -- see the note on the scan below for why that
    is the only one of the three candidate targets this instrument can judge.
    """
    directional = re.compile(
        r"(over[- ]?predict\w*|under[- ]?predict\w*|non-?conservative|conservative|"
        r"depreciat\w*|optimistic|pessimistic)", re.I)

    # SCANNED: the S5 module only. NOT the criteria document, and NOT this file.
    #
    # A line-level text scan cannot tell a CLAIM from a PROHIBITION, and the criteria
    # document's whole job is to state the prohibition -- it must print the forbidden
    # words in order to forbid them, as must this test in order to search for them. The
    # first draft scanned all three and flagged the criteria file's own falsifier clause
    # and this file's own regex. That is a check that fires on the rule instead of on a
    # breach of it: the same error as a probe that quotes the key it is attacking, which
    # this project has now recorded four times.
    #
    # What is left is the instrument that CAN be trusted: the artifact's own text, which
    # has no reason to name the prohibition and every opportunity to assert the claim.
    # THE DISTINCTION, AND THE CORRECTION THAT FORCED IT INTO THIS CHECK.
    #
    # The first version flagged every directional word. It then fired on the D84 scope --
    # "Hammer (2021) records that microgravity flow-boiling heat transfer typically
    # depreciates, so this correlation is expected to overpredict in orbit" -- which is
    # CORRECT. Hammer is about the HEAT-TRANSFER COEFFICIENT, where the direction IS
    # known; D-7's refinement is that the direction is not simple for CHF, and that
    # conflating the two is the error its own title invites. A check that forbids the HTC
    # direction forbids a true statement and pushes the artifact toward saying less than
    # it knows -- which is the opposite of what D-7 asks for.
    #
    # So the distinction is encoded rather than the scope exempted: a directional claim is
    # permitted where its surrounding text is about heat transfer and NOT about CHF.
    # Exempting the scope by name would have made this check pass without encoding
    # anything, which is the shape this milestone has now caught three times.
    source = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    chf_terms = re.compile(r"\bCHF\b|critical heat flux", re.I)
    htc_terms = re.compile(r"heat[- ]transfer|\bHTC\b", re.I)

    offenders = []
    for match in directional.finditer(source):
        window = source[max(0, match.start() - 320): match.end() + 320]
        line_no = source.count("\n", 0, match.start()) + 1
        about_chf = bool(chf_terms.search(window))
        about_htc = bool(htc_terms.search(window))
        if about_htc and not about_chf:
            continue  # a known HTC direction, which D-7 supports
        offenders.append(
            f"two_phase_architecture_cases.py:{line_no}: {match.group(0)!r} "
            f"(chf_context={about_chf}, htc_context={about_htc})"
        )
    assert not offenders, (
        "the S5 module asserts a direction for CHF error in microgravity, which D-7's "
        "own refinement forbids:\n  " + "\n  ".join(offenders)
    )

    # And the module does carry the qualification, so the absence above is a considered
    # silence rather than the subject never coming up.
    assert "D-7" in source and "D6" in source


def test_s5_7_s5_does_not_deliver_d7s_sharpening_either():
    """**Scope, and it cuts the other way.** D-7 assigns the sharpened ranking-scope
    wording to S6 — *"Sharpen at S6, where ranked outputs carry it."* S5 owes the
    prohibition, not the delivery, so S5 producing that wording would be S6 work landing
    in S5. This fails if the S5 module starts carrying ranking-scope prose.
    """
    source = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    assert "rank_scope" not in source, (
        "the ranking-scope limitation string belongs to S6's ranked outputs; an S5 "
        "eligibility module carrying it is scope creep, not thoroughness"
    )


# --------------------------------------------------------------------------------------
# S5-8 … S5-11 — the Steiner-Taborek evaluation (debt D-6)
# --------------------------------------------------------------------------------------

def test_s5_8_a_disposition_must_name_the_measurement_it_acted_on():
    """**S5-8.** Falsifier: "a disposition citing no measurement"."""
    with pytest.raises(ValueError, match="name the measurement it acted on"):
        ac.AmmoniaHtcEvaluation(
            disposition="adopt", acted_on="something_unmeasured", rationale="because")

    # A DECLINE, so this stays a test of S5-8 alone: adopting the worse deviation trips
    # the separate guard added when the Director dispositioned D-6, and a test that had
    # to satisfy two criteria at once would stop telling you which one it holds.
    ok = ac.AmmoniaHtcEvaluation(
        disposition="decline_policy", acted_on="steiner_taborek_1992",
        rationale="the pooled endorsement does not outweigh the single-study deviation")
    assert ok.measurement.deviation_percent == 41.9

    with pytest.raises(ValueError, match="not a disposition"):
        ac.AmmoniaHtcEvaluation(
            disposition="probably", acted_on="steiner_taborek_1992", rationale="x")


def test_s5_8_the_recorded_measurements_actually_conflict():
    """The premise S5-8 rests on: the evidence disagrees, so "which one" is a real question.

    If these ever stop disagreeing, the criterion is easier than it was written for, and
    that should be noticed rather than inherited.
    """
    by_name = {m.correlation: m for m in ac.AMMONIA_HTC_MEASUREMENTS}
    assert (by_name["steiner_taborek_1992"].deviation_percent
            > by_name["gungor_winterton_1987"].deviation_percent), (
        "Steiner-Taborek is recorded WORSE than the correlation ammonia is already "
        "de-ranked through -- that conflict is why a disposition must name its evidence"
    )
    assert "only correlation that predicts ammonia" in ac.TABOAS_2006_ENDORSEMENT, (
        "the evidence pointing the other way must be recorded too"
    )


def test_s5_9_a_gravity_dependent_accuracy_cannot_carry_a_disposition_silently():
    """**S5-9**, and Kattan-Thome-Favrat is the named case.

    It scores best (19.5 %) BECAUSE it resolves gravitational flow-pattern regimes -- the
    mechanism that does not exist in orbit. Falsifier: "an adoption or preference for KTF
    resting on the 19.5 % figure with no recorded treatment of its gravity dependence".
    """
    ktf = next(m for m in ac.AMMONIA_HTC_MEASUREMENTS
               if m.correlation == "kattan_thome_favrat")
    assert ktf.accuracy_is_gravity_dependent, "the trap must be marked in the data"
    assert ktf.deviation_percent < 20.0, "and it must still be the best score"

    with pytest.raises(ValueError, match="flow-pattern regimes"):
        ac.AmmoniaHtcEvaluation(
            disposition="adopt", acted_on="kattan_thome_favrat",
            rationale="it scores best at 19.5 %")

    # Recording the judgement is what makes it available -- not a keyword that waives it.
    allowed = ac.AmmoniaHtcEvaluation(
        disposition="adopt_with_scope", acted_on="kattan_thome_favrat",
        rationale="best available fit for a 1-g screening case",
        gravity_dependence_note=(
            "its accuracy comes from resolving gravitational flow-pattern regimes, which "
            "do not exist in orbit; scoped to 1-g screening only"),
        scope="1-g screening only")
    assert allowed.gravity_dependence_note


def test_s5_10_a_decline_is_a_policy_refusal_not_an_absence_of_knowledge():
    """**S5-10**, resting on S4-8. Falsifier: "a decline reported as absence"."""
    with pytest.raises(ValueError, match="POLICY refusal, not an absence"):
        ac.AmmoniaHtcEvaluation(
            disposition="decline_no_knowledge", acted_on="steiner_taborek_1992",
            rationale="nothing covers ammonia")

    ok = ac.AmmoniaHtcEvaluation(
        disposition="decline_policy", acted_on="steiner_taborek_1992",
        rationale="41.9 % is worse than the 37.2 % ammonia is already de-ranked through")
    assert ok.disposition == "decline_policy"


def test_s5_11_d6_retires_because_a_disposition_is_recorded():
    """**S5-11.** Retirement follows a recorded disposition, and one now exists.

    The Director dispositioned D-6: Steiner-Taborek adopted with scope. Retirement is
    therefore a state the artifact can show, not an inference from the presence of code --
    which is the whole point of the criterion, and the reason the previous build reported
    ``open`` rather than assuming.
    """
    d = ac.AMMONIA_HTC_DISPOSITION
    assert d is not None
    assert d.disposition == "adopt_with_scope"
    assert d.acted_on == "steiner_taborek_1992"

    state, reason = ac.d6_retirement_state()
    assert state == "retired"
    assert "retires at S5" in reason


def test_s5_11_the_adoption_cannot_be_read_as_a_choice_on_accuracy():
    """**The Director's explicit condition on the disposition.**

    Steiner-Taborek is adopted at 41.9 % over Gungor-Winterton (1987)'s 37.2 % and
    Kattan-Thome-Favrat's 19.5 %. He required that a reader must not be able to mistake
    this for a choice on accuracy. So the record carries both numbers, and the retirement
    reason carries them too -- a disclaimer filed somewhere a reader does not look is not
    a disclaimer.
    """
    d = ac.AMMONIA_HTC_DISPOSITION
    better = [m for m in ac.AMMONIA_HTC_MEASUREMENTS
              if m.deviation_percent < d.measurement.deviation_percent]
    assert len(better) == 2, "the adoption must still be over TWO better-scoring records"

    for number in ("41.9", "37.2"):
        assert number in d.accuracy_disclaimer, (
            f"the disclaimer must print {number} % so the trade is legible"
        )
    assert "NOT because it fits better" in d.accuracy_disclaimer

    _, reason = ac.d6_retirement_state()
    assert "NOT the best recorded deviation" in reason and "41.9" in reason, (
        "the retirement reason is what a downstream reader sees; the trade must survive "
        "into it rather than living only in the record it summarises"
    )


def test_s5_11_ktf_is_rejected_on_structure_and_the_precedent_is_real():
    """**S5-9 discharged by the ruling, and the cited precedent is verified, not quoted.**

    Kattan-Thome-Favrat scores best and is rejected because its accuracy is earned by
    resolving gravitational flow-pattern regimes -- absent in orbit. The Director grounded
    that on an existing decision rather than a new principle: Gungor-Winterton (1986)'s
    Froude stratification de-rating was already stripped for the same reason. This test
    reads the registry to confirm the precedent says what the record claims it says.
    """
    d = ac.AMMONIA_HTC_DISPOSITION
    assert "STRUCTURE, not accuracy" in d.structural_rejection
    assert "kattan" in d.structural_rejection.lower()
    assert "registry/two_phase.py:379" in d.structural_rejection

    registry = pathlib.Path(ac.__file__).parent / "registry" / "two_phase.py"
    text = registry.read_text(encoding="utf-8")
    assert "no microgravity meaning" in text and "Froude" in text, (
        "the cited precedent must exist in the registry. If this fails the citation has "
        "rotted and the rejection's ground needs re-stating, not the citation deleting"
    )


def test_s5_11_adopting_a_worse_deviation_without_saying_so_is_refused():
    """The guard behind the condition, exercised in both directions."""
    with pytest.raises(ValueError, match="NOT a choice on accuracy"):
        ac.AmmoniaHtcEvaluation(
            disposition="adopt_with_scope", acted_on="steiner_taborek_1992",
            rationale="the pooled endorsement")

    # A disclaimer that omits the numbers is refused too: it can be skimmed past.
    with pytest.raises(ValueError, match="must print"):
        ac.AmmoniaHtcEvaluation(
            disposition="adopt_with_scope", acted_on="steiner_taborek_1992",
            rationale="the pooled endorsement",
            accuracy_disclaimer="this is not a choice on accuracy",
            structural_rejection="KTF rejected on structure")

    # And an adoption over a better score with no structural ground is refused (S5-9).
    with pytest.raises(ValueError, match="STRUCTURAL ground"):
        ac.AmmoniaHtcEvaluation(
            disposition="adopt_with_scope", acted_on="steiner_taborek_1992",
            rationale="the pooled endorsement",
            accuracy_disclaimer="adopted at 41.9 % against 37.2 % and 19.5 %")

    # The BEST-scoring correlation needs no disclaimer -- the guard is specific.
    ok = ac.AmmoniaHtcEvaluation(
        disposition="adopt_with_scope", acted_on="kattan_thome_favrat",
        rationale="best fit for a 1-g screening case",
        gravity_dependence_note="scoped to 1 g; the mechanism is gravitational",
        scope="1-g screening only")
    assert ok.accuracy_disclaimer == ""


# --------------------------------------------------------------------------------------
# S5-12 / S5-13 — debt D-14, whose gate is S8
# --------------------------------------------------------------------------------------

def test_s5_12_s5_does_not_weaken_s4_3():
    """**S5-12**, and the third clause is the one that matters.

    The cheapest way to discharge D-14 is to reword the criterion it fails. So this
    asserts that S4-3's declared failure is still declared -- the artifact's own D28
    statement -- and that the criteria document still carries the measured falsifier.
    """
    from orbital_thermal import coupled_loop as C

    (conflict,) = C.sink_collapse_conflicts()
    assert conflict.phenomenon == "sink_temperature_coupling", (
        "S4-3's declared failure must still be declared. If the coupling was built, this "
        "is D-14's discharge and S5-13 governs it -- do not simply delete this assertion"
    )
    assert "S4-3" in C.sink_disclosure_text()

    root = pathlib.Path(ac.__file__).parents[2]
    s5 = (root / "ACCEPTANCE_CRITERIA_OTB-G005.md").read_text(encoding="utf-8")
    assert "0.043654969267" in s5 and "150 K, 250 K and 320 K" in s5, (
        "S5-12 names the measured falsifier; a criteria file that has lost it can no "
        "longer tell whether the coupling was built or the criterion was reworded"
    )
    module = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    for claim in ("coupling is built", "S4-3 passes", "milestone is discharged"):
        assert claim not in module


# --------------------------------------------------------------------------------------
# S5-14 — traceability
# --------------------------------------------------------------------------------------

def test_s5_14_every_number_s5_introduces_cites_a_source():
    """**S5-14.** Each recorded deviation carries who measured it."""
    assert ac.AMMONIA_HTC_MEASUREMENTS, "the evidence set must not be empty"
    for m in ac.AMMONIA_HTC_MEASUREMENTS:
        assert m.source.strip(), f"{m.correlation} carries no source"
        assert isinstance(m.deviation_percent, float)


def test_s5_14_s5_declares_no_new_enforced_bound():
    """**S5-14**, discharged by absence -- and the absence is asserted, not assumed.

    Every number this milestone introduces is a recorded DEVIATION with a named source,
    not an enforced bound. The bounds it consumes are the registry's, already traceable,
    and S5 adding one would put an unsourced limit into the enforcement path.
    """
    module = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    assert "Applicability(" not in module, "S5 must not declare a new applicability box"
    assert "Domain(" not in module


# --------------------------------------------------------------------------------------
# D84 — the scope, its guard, and the authority seam
# --------------------------------------------------------------------------------------

def test_d84_adopt_with_scope_refuses_an_empty_scope():
    """**A verb naming a bound that no text supplies is weaker than plain ``adopt``.**

    ``adopt_with_scope`` reads as narrower than ``adopt``, so a reader takes the narrowing
    on trust. If no scope text exists, that reader has been given a limit that constrains
    nothing -- worse than an unbounded adoption honestly labelled. Same shape as the
    ``gravity_dependence_note`` guard: the qualifier is required by the verb that promises
    it, not defaulted.
    """
    for empty in ("", "   ", "\n"):
        with pytest.raises(ValueError, match="empty scope supplies none"):
            ac.AmmoniaHtcEvaluation(
                disposition="adopt_with_scope", acted_on="steiner_taborek_1992",
                rationale="the pooled endorsement",
                accuracy_disclaimer="adopted at 41.9 % against 37.2 %",
                structural_rejection="KTF rejected on structure",
                scope=empty)

    # A plain `adopt` needs no scope -- the guard belongs to the verb that promises one.
    ok = ac.AmmoniaHtcEvaluation(
        disposition="adopt", acted_on="steiner_taborek_1992",
        rationale="unbounded, and said so",
        accuracy_disclaimer="adopted at 41.9 % against 37.2 %",
        structural_rejection="KTF rejected on structure")
    assert ok.scope == ""


def test_d84_the_shipped_scope_is_present_and_says_what_it_bounds():
    """The scope the Director approved, carried on the record he dispositioned."""
    d = ac.AMMONIA_HTC_DISPOSITION
    assert d.disposition == "adopt_with_scope"
    assert d.scope.strip(), "the shipped disposition must carry its scope"
    for clause in (
        "1-g-referenced ammonia heat-transfer screening only",
        "claims no microgravity validation",
        "licenses no microgravity heat-transfer claim",
        "does not discharge D-7",
    ):
        assert clause in d.scope, f"the scope must still say: {clause!r}"


def test_d84_the_authority_seam_survives_into_the_artifact():
    """**DIR-02's three-zone seam, carried into the code and not left in the ledger.**

    A scope paragraph sitting in a Director-dispositioned record reads as his words unless
    something says otherwise, and a reader of this module cannot check the ledger. D47 is
    the round where unmarked builder prose was found inside the Director's field in a
    frozen packet, so the distinction is asserted here rather than trusted to prose.

    The Director's own prose in this disposition is the ``rationale`` and nothing else.
    """
    authority = ac.AMMONIA_HTC_SCOPE_AUTHORITY
    assert authority["wording"] == "builder"
    assert authority["choice"] == "Director, D84"
    assert authority["director_prose_field"] == "rationale"

    source = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    assert "DIRECTOR SELECTION -- BUILDER WORDING, DIRECTOR CHOICE" in source, (
        "the seam header must be in the module text, not only in this test"
    )
    assert "END DIRECTOR SELECTION" in source, "the zone must be closed"

    # And the Director's verbatim rationale must not have been absorbed into the scope.
    assert "Let's go with Steiner-Taborek" in ac.AMMONIA_HTC_DISPOSITION.rationale
    assert "Let's go with" not in ac.AMMONIA_HTC_SCOPE, (
        "his prose belongs in the rationale; merging it into builder-worded scope text "
        "is the exact blurring the seam exists to prevent"
    )


def test_s5_7_still_catches_a_chf_direction_after_the_htc_carve_out():
    """**The refinement must not have gutted the guard.**

    S5-7's check now permits a directional claim whose surrounding text is about heat
    transfer and not about CHF -- because the D84 scope makes exactly that claim, and
    Hammer (2021) supports it for the HTC. A carve-out that also let a CHF direction
    through would have traded a false negative for the defect the criterion exists to
    catch, which is the D37 lesson about case-blindness.

    So the classifier is exercised on both sides here rather than only on the artifact.
    """
    directional = re.compile(
        r"(over[- ]?predict\w*|under[- ]?predict\w*|non-?conservative|conservative|"
        r"depreciat\w*|optimistic|pessimistic)", re.I)
    chf_terms = re.compile(r"\bCHF\b|critical heat flux", re.I)
    htc_terms = re.compile(r"heat[- ]transfer|\bHTC\b", re.I)

    def verdict(text: str) -> str:
        m = directional.search(text)
        if m is None:
            return "no directional claim"
        window = text[max(0, m.start() - 320): m.end() + 320]
        if htc_terms.search(window) and not chf_terms.search(window):
            return "permitted"
        return "offender"

    assert verdict(ac.AMMONIA_HTC_SCOPE) == "permitted", (
        "the D84 scope is an HTC direction, which D-7 supports"
    )
    assert verdict(
        "1-g CHF correlations are non-conservative in microgravity."
    ) == "offender", "a bare CHF direction must still be caught"
    assert verdict(
        "Microgravity flow-boiling heat transfer depreciates, so the CHF correlation "
        "overpredicts in orbit."
    ) == "offender", (
        "carrying the HTC direction ACROSS to CHF is the conflation D-7's own title "
        "invites, and the carve-out must not license it"
    )
    assert verdict("Eligibility is derived from the registry.") == "no directional claim"


# --------------------------------------------------------------------------------------
# D90 / F-04 — the construction boundary, one witness per falsifier
# --------------------------------------------------------------------------------------
#
# S5-4 forbids FIVE shapes: absent, empty, defaulted, caller-supplied, caller-overridden.
# `__post_init__` rejected ONE. The existing test quoted all five and exercised one; that
# is the shape Sol named, so each falsifier gets its own witness below rather than one
# test standing in for the set.

def _real_basis():
    """The basis the registry actually produces for the adopted CHF entry."""
    return ac._registry_gravity_bases()[_ADOPTED_CHF.id]


def test_f04_a_fabricated_gravity_basis_is_refused():
    """**Falsifier 1: caller-supplied.** This constructed before, with no refusal at all.

    ``GravityBasis`` is a public NamedTuple with an ordinary constructor, so the record
    could be closed around a basis the caller invented. Construction is now closed around
    the REGISTRY: a basis naming no registry entry is refused.
    """
    fabricated = ac.GravityBasis(
        entry_id="MADE-UP", reference_gravity_m_s2=9.80665, basis="invented")
    with pytest.raises(TypeError, match="constructible only by the computation"):
        ac.LegEligibility(fluid="water", leg="chf", entry_id="MADE-UP",
                          eligible=True, gravity_basis=fabricated)


def test_f04_an_empty_gravity_basis_is_refused():
    """**Falsifier 2: empty.** Blank basis text and a blank entry id both refuse.

    ``from_entry`` used to default a missing basis string to ``""``, so an entry could
    supply a number with nothing standing behind it. D6 makes the gravity a SOURCED
    boundary; a blank source is not one.
    """
    for bad in (
        ac.GravityBasis(entry_id="", reference_gravity_m_s2=9.80665, basis="text"),
        ac.GravityBasis(entry_id=_ADOPTED_CHF.id, reference_gravity_m_s2=9.80665,
                        basis="   "),
    ):
        with pytest.raises(TypeError, match="constructible only by the computation"):
            ac.LegEligibility(fluid="water", leg="chf", entry_id=_ADOPTED_CHF.id,
                              eligible=True, gravity_basis=bad)


def test_f04_an_overridden_gravity_basis_is_refused():
    """**Falsifier 3: caller-overridden.** The right entry id with the wrong numbers.

    This is the subtlest of the five: the basis names a real entry, so an id check alone
    passes it, while the gravity it carries is not the gravity that entry declares. An
    overridden basis IS a mismatched one, so the whole tuple is compared.
    """
    real = _real_basis()
    overridden = ac.GravityBasis(
        entry_id=real.entry_id, reference_gravity_m_s2=1.62, basis=real.basis)
    with pytest.raises(TypeError, match="constructible only by the computation"):
        ac.LegEligibility(fluid="water", leg="chf", entry_id=real.entry_id,
                          eligible=True, gravity_basis=overridden)

    reworded = ac.GravityBasis(
        entry_id=real.entry_id,
        reference_gravity_m_s2=real.reference_gravity_m_s2,
        basis="a friendlier basis sentence")
    with pytest.raises(TypeError, match="constructible only by the computation"):
        ac.LegEligibility(fluid="water", leg="chf", entry_id=real.entry_id,
                          eligible=True, gravity_basis=reworded)


def test_f04_a_zero_or_defaulted_reference_gravity_is_refused():
    """**Falsifier 4: defaulted.** The literal shape Sol constructed: 0.0 with no basis."""
    with pytest.raises(TypeError, match="constructible only by the computation"):
        ac.LegEligibility(
            fluid="water", leg="chf", entry_id="MADE-UP", eligible=True,
            gravity_basis=ac.GravityBasis(
                entry_id="MADE-UP", reference_gravity_m_s2=0.0, basis=""))


def test_f04_the_real_registry_basis_still_constructs():
    """**The negative control.** The boundary is closed, not sealed shut.

    A guard that refused everything would satisfy the four witnesses above and break the
    module. The basis the registry actually produces must still build a record.
    """
    real = _real_basis()
    # D100: the record is no longer constructible here, so the positive control is the
    # computation itself. `is not None`, NOT a truth test: bool() on a CHF record raises
    # by design (S5-5).
    ok = ac.assess_leg("water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE)
    assert ok is not None
    assert ok.gravity_basis == real


def test_f04_from_entry_refuses_a_reference_gravity_with_no_basis_text():
    """**Falsifier 5: defaulted basis text**, and it needed a constructed entry.

    No shipped registry entry has a reference gravity with a blank ``gravity_basis``, so
    the guard added for F-04 had no reachable witness -- a check whose branch nothing
    exercises, which is the shape this project counts. The entry is built here so the
    branch is actually taken.

    ``from_entry`` used to end ``getattr(spec, "gravity_basis", "")``, defaulting a
    missing source to the empty string. D6 makes the gravity a SOURCED boundary; a number
    with a blank source behind it is not one.
    """
    import dataclasses

    spec = _ADOPTED_CHF.applicability_spec
    blanked = dataclasses.replace(spec, gravity_basis="   ")
    entry = dataclasses.replace(_ADOPTED_CHF, applicability_spec=blanked)

    with pytest.raises(ValueError, match="gravity_basis text"):
        ac.GravityBasis.from_entry(entry)

    # And such an entry contributes no basis to the construction boundary, so a record
    # cannot be closed around it either.
    assert entry.id not in ac._registry_gravity_bases((entry,))


# --------------------------------------------------------------------------------------
# D97 / F-02 — one record, one producer identity
# --------------------------------------------------------------------------------------

def test_f02_a_real_basis_on_a_fabricated_producer_is_refused():
    """**The cross-wiring round 1 left open.** A genuine basis, a producer that is not it.

    ``LegEligibility(entry_id='MADE-UP', gravity_basis=from_entry(shah_1987))``
    constructed, and ``as_record()`` serialised BOTH identities as valid: the record said
    its producer was ``MADE-UP`` while its basis said ``two_phase.chf.shah_1987``. The
    round-1 repair authenticated the basis against the registry and never bound it to the
    field naming the correlation the eligibility came from. All six of its witnesses
    aligned the two ids, so none of them could see this.
    """
    real = _real_basis()
    with pytest.raises(TypeError, match="constructible only by the computation"):
        ac.LegEligibility(fluid="water", leg="chf", entry_id="MADE-UP",
                          eligible=True, gravity_basis=real)


def test_f02_a_real_basis_on_another_real_producer_is_refused():
    """The same defect without any fabrication: two genuine entries, cross-wired.

    **D100 changed what this test can even set up, and that is the repair showing.**
    ``_registry_gravity_bases`` used to accept every entry carrying a gravity -- a
    pressure-drop correlation, a ``NOT_RANK_ELIGIBLE`` heat-transfer entry -- as a CHF
    producer. It now filters on kind and status, so the population is one entry and there
    are no mismatched pairs left inside it to build from.

    So the cross-wire is built from OUTSIDE that population, which is where the round-2
    instance came from: a real basis minted off a real pressure-drop entry, attached to a
    CHF record. It is unconstructible, and so is every other pairing.
    """
    from orbital_thermal.registry import two_phase as tp

    accepted = ac._registry_gravity_bases()
    assert set(accepted) == {"two_phase.chf.shah_1987"}, (
        f"the CHF producer population must be exactly the adopted CHF entry; got "
        f"{sorted(accepted)}. If it has widened, hole 1 has reopened."
    )

    foreign = [
        ac.GravityBasis.from_entry(e)
        for e in tp.TWO_PHASE_CORRELATIONS
        if e.kind != "chf"
        and getattr(getattr(e, "applicability_spec", None), "reference_gravity_m_s2", None)
    ]
    assert foreign, "no non-CHF entry carries a gravity, so this test proves nothing"

    producers = ["MADE-UP", *accepted]
    for basis in foreign:
        for producer_id in producers:
            with pytest.raises(
                TypeError, match="constructible only by the computation"
            ):
                ac.LegEligibility(fluid="ammonia", leg="chf", entry_id=producer_id,
                                  eligible=True, violations=(), gravity_basis=basis)


def test_f02_aligned_identities_still_construct_and_serialise_one_producer():
    """**The negative control**, and the serialisation the finding was reported through.

    A record whose two identities agree must still build, and ``as_record()`` must never
    emit a producer id in the record that differs from the one in its basis.
    """
    real = _real_basis()
    ok = ac.assess_leg("water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE)
    assert ok is not None
    record = ok.as_record()
    assert record["entry_id"] == record["gravity_basis"]["entry_id"] == real.entry_id, (
        "one record, one producer identity — the contradiction is what F-02 reported"
    )

    # And the real assessment path still produces records that satisfy it.
    leg = ac.assess_leg("water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE)
    assert leg is not None
    rec = leg.as_record()
    assert rec["entry_id"] == rec["gravity_basis"]["entry_id"]


# --------------------------------------------------------------------------------------
# D100 — the door, and a DERIVED enumeration of the routes through it
# --------------------------------------------------------------------------------------

def _recompute(record):
    """What the computation says for this record's own case, independently."""
    return ac.assess_leg(record.fluid, record.leg, gravity_m_s2=_MICROGRAVITY,
                         **_FULL_CASE)


def test_d100_every_object_creation_protocol_is_enumerated_and_reported():
    """**The derived witness.** Enumerate the PROTOCOLS, not the routes I thought of.

    Round 2's lesson was that a listed surface goes stale when a sixth name appears. The
    same applies here: naming ``LegEligibility(...)`` and stopping would miss whatever
    else Python offers. So this walks the standard ways an object of a type can come into
    existence and classifies each one, and **reports any it could not evaluate** rather
    than silently covering less than it claims -- which is the behaviour Cowork's rebuilt
    M5 showed when it found its own fixture underspecified.

    **Two routes were found this way and neither by inspection.** ``dataclasses.replace``
    carried a mint held as a FIELD, so a minted record could be replayed with a
    caller-chosen ``eligible`` -- which is why the mint is now a SCOPE, which cannot be
    copied off an existing record. And ``object.__new__`` bypasses ``__init__`` entirely;
    that one is unclosable in Python and is DISCLOSED in the module rather than claimed
    shut. Both were reported by this witness within minutes of it existing.
    """
    import copy
    import pickle
    import sys

    minted = ac.assess_leg("ammonia", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    assert minted is not None and minted.eligible is False

    routes = {}

    # 1. the ordinary constructor
    try:
        ac.LegEligibility(fluid="ammonia", leg="chf", entry_id=_ADOPTED_CHF.id,
                          eligible=True, violations=(),
                          gravity_basis=_real_basis())
        routes["constructor"] = ("PRODUCED", None)
    except TypeError as exc:
        routes["constructor"] = ("refused", str(exc)[:140])
    except Exception as exc:  # noqa: BLE001 - a refusal for another reason is not closed
        routes["constructor"] = ("UNEXPECTED", type(exc).__name__)

    # 2. dataclasses.replace -- carries the mint forward
    try:
        dataclasses.replace(minted, eligible=True, violations=())
        routes["dataclasses.replace"] = ("PRODUCED", None)
    except TypeError as exc:
        routes["dataclasses.replace"] = ("refused", str(exc)[:140])
    except Exception as exc:  # noqa: BLE001 - a refusal for another reason is not closed
        routes["dataclasses.replace"] = ("UNEXPECTED", type(exc).__name__)

    # 3. copy.replace -- a 3.13 ADDITION. On 3.10-3.12, which is what this project
    #    declares and what CI tests, the attribute does not exist. The first version of
    #    this route caught `Exception`, filed the AttributeError as "refused", and the
    #    unevaluated-route check then accepted "refused" as one of its four literals -- so
    #    the check whose stated purpose is to report what it could not evaluate did not
    #    report the one route it could not evaluate. Instance eight of the class, inside
    #    the witness certifying D100. UNAVAILABLE is now its own outcome.
    if hasattr(copy, "replace"):
        try:
            copy.replace(minted, eligible=True, violations=())
            routes["copy.replace"] = ("PRODUCED", None)
        except TypeError as exc:
            routes["copy.replace"] = ("refused", str(exc)[:140])
        except Exception as exc:  # noqa: BLE001 - surfaced, never filed as closed
            routes["copy.replace"] = ("UNEXPECTED", type(exc).__name__)
    else:
        routes["copy.replace"] = ("UNAVAILABLE", f"python {sys.version_info[:2]}")

    # 4. shallow and deep copy -- bypass __init__ entirely
    for name, fn in (("copy.copy", copy.copy), ("copy.deepcopy", copy.deepcopy)):
        try:
            clone = fn(minted)
            routes[name] = ("PRODUCED-COPY", clone)
        except Exception as exc:
            routes[name] = ("refused", type(exc).__name__)

    # 4. pickle round-trip
    try:
        routes["pickle"] = ("PRODUCED-COPY", pickle.loads(pickle.dumps(minted)))
    except Exception as exc:
        routes["pickle"] = ("refused", type(exc).__name__)

    # 5. object.__new__ with a hand-built __dict__ -- the rawest route there is
    try:
        raw = object.__new__(type(minted))
        object.__setattr__(raw, "__dict__", {**minted.__dict__, "eligible": True,
                                            "violations": ()})
        routes["object.__new__"] = ("PRODUCED-RAW", raw)
    except Exception as exc:
        routes["object.__new__"] = ("refused", type(exc).__name__)

    # THE VERDICT. A route that PRODUCES a record asserting an outcome the computation
    # contradicts is a hole. A route that only clones a minted record faithfully is not.
    # object.__new__ + __dict__ bypasses __init__ and Python cannot prevent it for any
    # type. It is a KNOWN, DISCLOSED residual rather than a hole -- the module says so in
    # its own text, and this asserts the disclosure so the claim cannot quietly inflate.
    import pathlib as _pl
    module_text = _pl.Path(ac.__file__).read_text(encoding="utf-8")
    assert "THE ONE ROUTE THAT REMAINS, DISCLOSED RATHER THAN CLAIMED SHUT" in module_text, (
        "the unclosable raw-construction route must stay disclosed in the module, under "
        "a heading a reader cannot miss. The first version of this check accepted any "
        "mention of 'object.__new__' plus the word 'disclosed' anywhere, which deleting "
        "the heading still satisfied."
    )
    disclosed = {"object.__new__"}

    holes = []
    for name, (kind, payload) in routes.items():
        if name in disclosed:
            continue
        if kind == "PRODUCED":
            holes.append(f"{name}: constructed a caller-specified CHF outcome")
        elif kind in ("PRODUCED-COPY", "PRODUCED-RAW"):
            truth = _recompute(minted)
            if (payload.eligible, tuple(payload.violations)) != (
                    truth.eligible, tuple(truth.violations)):
                holes.append(
                    f"{name}: yielded eligible={payload.eligible!r} while the "
                    f"computation says {truth.eligible!r}")
    assert not holes, (
        "routes into a CHF-dependent record that a caller can steer:\n  "
        + "\n  ".join(holes)
        + f"\n(all routes evaluated: { {k: v[0] for k, v in routes.items()} })"
    )

    # And the enumeration must be believable: every route reported a definite outcome.
    # A route the interpreter cannot offer, or one that refused for a reason unrelated
    # to the mint, is REPORTED -- never counted as closed.
    unavailable = {n: d for n, (k, d) in routes.items() if k == "UNAVAILABLE"}
    unexpected = {n: d for n, (k, d) in routes.items() if k == "UNEXPECTED"}
    assert not unexpected, (
        f"routes that refused for a reason other than the mint: {unexpected}. A refusal "
        "the mint did not cause is not a closed route."
    )
    # A refusal must come from THIS boundary, not from something incidental. Two are
    # legitimate and both are named: the mint, and __replace__'s own refusal -- which
    # copy.replace reaches on 3.13+, and which is therefore live here and dead on the
    # interpreters CI actually runs.
    boundary_refusals = (
        "constructible only by the computation",
        "cannot be replaced",
    )
    for name, detail in routes.items():
        if detail[0] == "refused":
            assert any(r in str(detail[1]) for r in boundary_refusals), (
                f"{name} refused, but not by this boundary: {detail[1]!r}. A refusal for "
                "an unrelated reason is not a closed route."
            )

    # UNAVAILABLE is not a failure -- it is a coverage report, and it must be visible.
    if unavailable:
        # D102/R6. This was a `print`, and pytest CAPTURES stdout for PASSING tests: on a
        # plain `pytest -q` the sentence was produced and discarded. Measured on 3.11 it
        # fired every run and appeared zero times. It looked right to me because I run
        # 3.14, where copy.replace exists, the route is live and the notice never fires --
        # so I had never seen the run that loses it. Same shape one turn smaller: a report
        # confirming it was PRODUCED without confirming anyone RECEIVES it.
        #
        # warnings.warn lands in the warnings summary a plain `-q` already prints, so it
        # needs no addopts and nothing outside this file.
        warnings.warn(
            f"ROUTES NOT EXERCISED ON THIS INTERPRETER: {unavailable}",
            _RouteNotExercised,
            stacklevel=2,
        )
    assert set(routes) >= {
        "constructor", "dataclasses.replace", "copy.replace", "copy.copy",
        "copy.deepcopy", "pickle", "object.__new__"}, (
        f"the enumeration shrank: {sorted(routes)}"
    )


def test_d100_the_two_reported_instances_are_unconstructible():
    """The negative controls, verbatim from the finding."""
    from orbital_thermal.registry import two_phase as tp

    dp = next(e for e in tp.TWO_PHASE_CORRELATIONS
              if e.id == "two_phase.dp.lockhart_martinelli_chisholm")
    with pytest.raises(TypeError, match="constructible only by the computation"):
        ac.LegEligibility(fluid="ammonia", leg="chf", entry_id=dp.id, eligible=True,
                          violations=(), gravity_basis=ac.GravityBasis.from_entry(dp))

    real = _real_basis()
    with pytest.raises(TypeError, match="constructible only by the computation"):
        ac.LegEligibility(fluid="ammonia", leg="chf", entry_id=real.entry_id,
                          eligible=True, violations=(), gravity_basis=real)


def test_d100_assess_leg_still_produces_valid_records():
    """**The positive control.** The computation still works and still computes."""
    at_1g = ac.assess_leg("water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE)
    micro = ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    assert at_1g is not None and micro is not None
    assert _checked(at_1g) == () and micro.eligible is False
    assert {v.axis for v in micro.violations} == {Axis.ORIENTATION}
    assert at_1g.gravity_basis == _real_basis()
    assert at_1g.as_record()["entry_id"] == _ADOPTED_CHF.id


def test_d101_r1_the_mint_does_not_leak_across_threads():
    """**D101/R1, and the witness is DETERMINISTIC rather than timed.**

    ``_MINTING`` was a plain module-level bool -- a global. One thread inside
    ``assess_leg`` held it open for every thread, so the public constructor D100 removed
    succeeded whenever anyone else happened to be minting. Measured at **100 %**: four
    minter threads against one constructor thread fabricated **367 896 records out of
    367 896 attempts** in five seconds, each carrying ``eligible=True``, ``violations=()``,
    the genuine Shah-1987 basis and a gravity the computation never saw.

    A threaded test that depends on timing is a defect of its own kind, so this does not
    race: one thread opens the scope and BLOCKS on a barrier while another constructs.
    The window is held open deliberately, so the outcome is the same on every run and on
    any machine. It is red on the old shape and green on the new one for a reason, not
    for a schedule.

    Nothing in this repository calls ``assess_leg`` from more than one thread today. The
    defect was the unconditional form of the claim, and what S6 inherits.
    """
    import threading

    real = _real_basis()
    scope_open = threading.Event()
    may_close = threading.Event()
    outcome: dict[str, object] = {}

    def hold_the_scope() -> None:
        with ac._minting():
            scope_open.set()
            may_close.wait(10)

    def construct_from_another_thread() -> None:
        try:
            assert scope_open.wait(10), "the minting thread never opened its scope"
            try:
                record = ac.LegEligibility(
                    fluid="ammonia", leg="chf", entry_id=real.entry_id,
                    eligible=True, violations=(), gravity_basis=real)
                outcome["fabricated"] = (record.eligible, record.violations)
            except TypeError as exc:
                outcome["refused"] = str(exc)[:140]
        finally:
            may_close.set()

    minter = threading.Thread(target=hold_the_scope, name="minter")
    caller = threading.Thread(target=construct_from_another_thread, name="caller")
    minter.start()
    caller.start()
    caller.join(15)
    minter.join(15)
    assert not minter.is_alive() and not caller.is_alive(), "the witness deadlocked"

    assert "fabricated" not in outcome, (
        f"another thread's open minting scope let the public constructor produce "
        f"{outcome.get('fabricated')!r}. The mint must be per execution context, not "
        "per module."
    )
    assert "constructible only by the computation" in str(outcome.get("refused", "")), (
        f"the construction was refused, but not by the mint: {outcome!r}"
    )


def test_d101_r1_the_scope_still_works_on_the_thread_that_opened_it():
    """The positive control: per-context must not mean per-nothing."""
    import threading

    results: dict[str, object] = {}

    def assess_on_a_worker() -> None:
        record = ac.assess_leg("ammonia", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
        results["record"] = record

    worker = threading.Thread(target=assess_on_a_worker)
    worker.start()
    worker.join(15)
    record = results.get("record")
    assert record is not None, "assess_leg must still mint on whatever thread runs it"
    assert record.eligible is False



def test_d102_r6_the_coverage_notice_reaches_a_plain_pytest_run():
    """**D102/R6: the notice must be RECEIVED, not merely produced.**

    The channel is ``warnings.warn``, which lands in the warnings summary a plain
    ``pytest -q`` already prints. The previous channel was ``print``, which pytest
    captures for passing tests and discards.

    **This test forces the UNAVAILABLE branch rather than waiting for an interpreter that
    triggers it.** On 3.13+ ``copy.replace`` exists, so the real notice never fires and a
    witness that only ran the natural path would be green here and untested -- which is
    exactly how the defect survived. Hiding the attribute reproduces what 3.10-3.12 sees,
    on any interpreter.

    The code change is not the check. The check is a plain ``pytest -q`` over the whole
    suite with the output grepped for this warning; that grep is recorded in the
    hand-back, because a test asserting a warning was raised still would not prove a
    reader ever sees it.
    """
    import copy

    original = getattr(copy, "replace", None)
    try:
        if original is not None:
            del copy.replace
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            test_d100_every_object_creation_protocol_is_enumerated_and_reported()
    finally:
        if original is not None:
            copy.replace = original

    notices = [w for w in caught if issubclass(w.category, _RouteNotExercised)]
    assert notices, (
        "with copy.replace absent the enumeration must WARN, not print: a print is "
        "captured and discarded for passing tests under a plain pytest -q"
    )
    assert "copy.replace" in str(notices[0].message)
    assert "ROUTES NOT EXERCISED ON THIS INTERPRETER" in str(notices[0].message)


def test_d102_r6_the_notice_is_emitted_by_this_suite_so_the_grep_has_something_to_find():
    """A warning raised only inside ``catch_warnings`` is invisible to the summary too.

    So this one escapes: it warns unconditionally, in the same category, naming the
    interpreter. On 3.10-3.12 the enumeration's own notice joins it; on 3.13+ this is the
    only one, and it is what makes the channel greppable on every interpreter rather than
    only on the ones that happen to lose a route.
    """
    import copy
    import sys

    warnings.warn(
        "ROUTES NOT EXERCISED ON THIS INTERPRETER: "
        f"{{}} (python {sys.version_info[:2]}, copy.replace "
        f"{'present' if hasattr(copy, 'replace') else 'ABSENT'}) -- channel check",
        _RouteNotExercised,
        stacklevel=2,
    )


# ======================================================================================
# D104 — the rules are not an input. Derived, not listed.
# ======================================================================================


def _public_entry_points():
    """Every public callable this module defines. DERIVED from the module, not typed.

    A new public function added later is covered here without this file being edited,
    which is the whole point: a listed witness only ever guards the door you remembered.
    """
    found = []
    for name in dir(ac):
        if name.startswith("_"):
            continue
        obj = getattr(ac, name)
        if callable(obj) and getattr(obj, "__module__", None) == ac.__name__:
            found.append((name, obj))
    assert [n for n, _ in found if n.startswith("assess_")], (
        "the enumeration found no assess_* entry point, so it is not looking at the "
        "module and every assertion below would pass vacuously"
    )
    return found


def _rule_bearing_type_names():
    """The names that denote *rules* rather than *a case*. Derived from the registry.

    ``CorrelationEntry`` and ``Applicability`` are the two types whose values decide what
    the computation concludes. Any annotation that mentions either -- bare, optional, or
    inside a sequence -- is a parameter through which a caller supplies the rules.
    """
    return frozenset({CorrelationEntry.__name__, Applicability.__name__})


def _steering_keywords():
    """Keyword names worth trying against a ``**kwargs`` channel. DERIVED.

    Built from the private seams' own parameter names and from the field names of the
    two rule-bearing dataclasses, so a rule field added to the registry becomes a probed
    keyword here without this test being touched.
    """
    names = set()
    for seam in (
        ac._assess_leg_against_a_supplied_registry,
        ac._assess_fluid_against_a_supplied_registry,
    ):
        names.update(inspect.signature(seam).parameters)
    for spec in (CorrelationEntry, Applicability):
        names.update(f.name for f in dataclasses.fields(spec))
    # These are the parameters a caller legitimately passes, so re-passing one is a
    # duplicate-argument TypeError rather than a steering test. Correct for D104's
    # question -- and D110 found the sentence written beside it ("the case surface is
    # clean") was not supportable from a population that removed one of them. The
    # exclusion is now bound to a compensating population by
    # test_d110_the_d104_witness_exclusion_is_paid_for_by_this_population.
    names.discard("fluid")
    names.discard("leg")
    names.discard("gravity_m_s2")
    names.discard("case")
    assert "entries" in names and "gravity_rel_tol" in names, (
        "the keyword derivation lost the two names D104 was reported against"
    )
    return sorted(names)


def _widened_registry():
    """The reported instance, byte-for-byte: the adopted CHF entry with one tolerance
    widened so microgravity falls inside it. id, kind, status, reference gravity and
    every basis string are unchanged -- this is a forgery that passes inspection."""
    widened = []
    for entry in ac.REGISTRY_ENTRIES:
        if entry.kind == "chf" and entry.status in ac.ADOPTED_FOR_RANKING:
            entry = dataclasses.replace(
                entry,
                applicability_spec=dataclasses.replace(
                    entry.applicability_spec, gravity_rel_tol=1.0e12
                ),
            )
        widened.append(entry)
    return tuple(widened)


def test_d104_no_public_entry_point_admits_the_rules():
    """**The finding, generalised: no public parameter may carry a rule.**

    Reported instance: ``assess_leg(..., entries=widened)`` returned ``eligible=True``
    for a microgravity case, because ``entries=`` let the caller supply the correlations
    the computation applies rather than the case it applies them to. The repair is not a
    check on ``entries`` -- it is that the public functions read :data:`REGISTRY_ENTRIES`
    and nothing else. This asserts that over the *derived* public surface, so it fails
    for a channel nobody enumerated.
    """
    offenders = []
    for name, fn in _public_entry_points():
        if isinstance(fn, type):
            continue  # a record type; its fields are outputs, not caller inputs
        for pname, param in inspect.signature(fn).parameters.items():
            annotation = str(param.annotation)
            if any(rule in annotation for rule in _rule_bearing_type_names()):
                offenders.append(f"{name}({pname}: {annotation})")
    assert not offenders, (
        "public parameters carry the rules the computation applies, not the case: "
        + "; ".join(offenders)
        + ". Move them to a private seam whose name says it takes a supplied registry."
    )


@pytest.mark.parametrize("keyword", _steering_keywords())
def test_d104_no_keyword_channel_steers_the_outcome(keyword):
    """**The runtime half: ``**case`` is annotated ``object``, so ask it, don't read it.**

    An annotation check cannot clear a ``**kwargs`` parameter -- ``object`` admits the
    registry. So every derived keyword is actually tried, carrying the forged widened
    registry, against a microgravity case whose true answer is a de-rank. The outcome
    must be identical to the un-steered one, or the call must refuse. Passing the
    forgery and getting the same answer is the assertion; refusing is also acceptable,
    because either way the caller did not move the result.
    """
    truth = ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    assert truth is not None and truth.eligible is False, (
        "the negative control is not de-ranked to begin with, so steering it would "
        "prove nothing"
    )

    forged = _widened_registry()
    try:
        steered = ac.assess_leg(
            "water", "chf", gravity_m_s2=_MICROGRAVITY, **{**_FULL_CASE, keyword: forged}
        )
    except TypeError:
        return  # refused outright: the channel does not exist
    assert steered.eligible == truth.eligible, (
        f"passing the forged registry as {keyword}= moved the outcome from "
        f"{truth.eligible} to {steered.eligible}. A caller supplied the rules."
    )
    assert [v.axis for v in steered.violations] == [v.axis for v in truth.violations]


def test_d104_the_reported_instance_is_a_negative_control():
    """The reported call, unchanged in shape. The outcome must be the SAME, not refused
    into a different one: microgravity de-ranks whatever the caller hands over."""
    truth = ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    assert truth.eligible is False
    assert [(v.axis, v.consequence) for v in _checked(truth)] == [
        (Axis.ORIENTATION, Consequence.DE_RANK)
    ]

    with pytest.raises(TypeError, match="does not take"):
        ac.assess_leg(
            "water", "chf", gravity_m_s2=_MICROGRAVITY,
            entries=_widened_registry(), **_FULL_CASE,
        )
    with pytest.raises(TypeError, match="does not take"):
        ac.assess_fluid(
            "water", gravity_m_s2=_MICROGRAVITY,
            entries=_widened_registry(), **_FULL_CASE,
        )

    after = ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    assert after.eligible is truth.eligible
    assert after.entry_id == truth.entry_id


def test_d104_the_seam_is_private_and_says_what_it_takes():
    """The witness S5-1 needs is a seam, and a seam has to be unmistakable.

    Two properties, both required: the name is private, and it *states* that the
    registry is supplied rather than adopted. A private name alone would still read
    like the production call at the call site.
    """
    for seam in (
        ac._assess_leg_against_a_supplied_registry,
        ac._assess_fluid_against_a_supplied_registry,
    ):
        assert seam.__name__.startswith("_")
        assert "supplied_registry" in seam.__name__
        first = next(iter(inspect.signature(seam).parameters))
        assert first == "entries", (
            "the supplied registry must be the FIRST positional parameter, so a call "
            "through the seam cannot be mistaken for a call to the public function"
        )


def test_d104_the_positive_control_still_produces_records():
    """The door is shut and the room is still in use: real assessments still work."""
    fluid = ac.assess_fluid("water", gravity_m_s2=_REFERENCE_G, **_FULL_CASE)
    assert set(fluid.legs) <= set(ac.RANKING_LEGS)
    chf = fluid.legs["chf"]
    assert _checked(chf) == ()
    assert chf.gravity_basis is not None
    assert chf.gravity_basis.reference_gravity_m_s2 == _REFERENCE_G
    assert chf.as_record()["gravity_basis"]["entry_id"] == chf.entry_id


# ======================================================================================
# D105 R1 — the disclosure, witnessed by measurement rather than by mention
# ======================================================================================

_DISCLOSURE_HEADING = (
    "**THE RULES ARE REACHABLE FROM INSIDE THE PROCESS. DISCLOSED, NOT CLAIMED SHUT.**"
)


def _disclosure_section() -> str:
    """The disclosure as ``help()`` sees it -- ``__doc__``, not the file on disk.

    Reading the source would pass even if the section sat in a comment or an orphaned
    string no reader ever reaches. D105/R2 is exactly that failure one level down.
    """
    doc = ac.__doc__ or ""
    assert _DISCLOSURE_HEADING in doc, (
        "the D105 disclosure heading is not in the module docstring. It is the anchor "
        "every check below hangs on, and a disclosure a reader cannot find is not one."
    )
    return doc[doc.index(_DISCLOSURE_HEADING):]


def _disclosure_prose() -> str:
    """:func:`_disclosure_section` with its line wrapping normalised away.

    D106: a needle that happens to span a line break fails against text that plainly
    says the thing. That is a fact about the wrapping, not about the disclosure.
    """
    return " ".join(_disclosure_section().split())


def _steer_by_rebinding_the_module_attribute(monkeypatch):
    forged = tuple(
        dataclasses.replace(
            e, applicability_spec=dataclasses.replace(
                e.applicability_spec, gravity_rel_tol=1.0e12))
        if e.kind == "chf" and e.applicability_spec is not None else e
        for e in ac.REGISTRY_ENTRIES
    )
    monkeypatch.setattr(ac, "REGISTRY_ENTRIES", forged)


def _steer_by_writing_through_the_frozen_entry(monkeypatch):
    # The entry is frozen, so monkeypatch cannot set it and cannot restore it either.
    # The undo is registered by hand, through the same door the write goes through.
    spec = ac.adopted_entry("chf").applicability_spec
    _RAW_WRITE_UNDO.append((spec, spec.gravity_rel_tol))
    object.__setattr__(spec, "gravity_rel_tol", 1.0e12)


def _steer_by_replacing_the_enforcement(monkeypatch):
    monkeypatch.setattr(Applicability, "check", lambda self, **kw: ())


def _steer_by_rebinding_the_seam(monkeypatch):
    monkeypatch.setattr(
        ac, "_assess_leg_against_a_supplied_registry",
        lambda *a, **k: _FORGED_SENTINEL,
    )


_FORGED_SENTINEL = object()
_RAW_WRITE_UNDO: list = []


@pytest.fixture
def _undo_raw_writes():
    yield
    while _RAW_WRITE_UNDO:
        target, value = _RAW_WRITE_UNDO.pop()
        object.__setattr__(target, "gravity_rel_tol", value)


#: (name, the text the disclosure must carry, the probe that proves it).
#: The pairing is the point: a route cannot be named in the disclosure without an
#: executed demonstration beside it, and cannot be demonstrated without being named.
_DISCLOSED_STEERING_ROUTES = [
    ("rebind the module attribute", "REGISTRY_ENTRIES = forged",
     _steer_by_rebinding_the_module_attribute),
    ("raw-write the frozen entry", "object.__setattr__(entry.applicability_spec",
     _steer_by_writing_through_the_frozen_entry),
    ("replace the enforcement", "Applicability.check = lambda",
     _steer_by_replacing_the_enforcement),
    ("rebind the seam", "rebinding this module's own seam",
     _steer_by_rebinding_the_seam),
]


@pytest.mark.parametrize(
    "name,needle,probe", _DISCLOSED_STEERING_ROUTES, ids=[r[0] for r in _DISCLOSED_STEERING_ROUTES]
)
def test_d105_r1_each_disclosed_route_is_named_and_still_steers(
    name, needle, probe, monkeypatch, _undo_raw_writes
):
    """**The disclosure is held to measurement, in both directions.**

    D100's first version of this check accepted any mention of the route plus the word
    "disclosed" anywhere in the file, which a fresh instance satisfies by writing the
    marker's own wording back (D43: a key that is the marker's own text is not a key).
    So mention is only half. The other half executes the route and requires it to still
    move a microgravity case from ``False, ['ORIENTATION']`` to ``True, []``.

    That makes the check bite in the direction that matters for a DISCLOSURE, which is
    the opposite of a guard: if a later repair closes one of these routes, this fails
    and the module must stop claiming it is open. An overclaim about what is broken is
    still an overclaim.
    """
    section = _disclosure_section()
    assert needle in section, (
        f"the disclosure does not name the {name} route, but it is measured below to "
        "steer the outcome. A disclosure that omits a measured route is incomplete."
    )

    truth = ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    assert truth.eligible is False and [
        (v.axis, v.consequence) for v in _checked(truth)
    ] == [(Axis.ORIENTATION, Consequence.DE_RANK)], (
        "the case is not de-ranked to begin with, so steering it would prove nothing"
    )

    probe(monkeypatch)
    steered = ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    if steered is _FORGED_SENTINEL:
        return  # the seam route: the computation was replaced outright
    assert _checked(steered) == (), (
        f"the {name} route no longer steers the outcome. If it was closed on purpose, "
        "the module's disclosure now overclaims what is reachable and must be narrowed."
    )


def _inert_rebind_the_source_registry(monkeypatch):
    monkeypatch.setattr(_tp_module, "TWO_PHASE_CORRELATIONS", ())


def _inert_empty_the_chf_leg_set(monkeypatch):
    monkeypatch.setattr(ac, "CHF_DEPENDENT_LEGS", frozenset())


_DISCLOSED_INERT_ROUTES = [
    ("rebind the source registry after import", _inert_rebind_the_source_registry),
    ("empty CHF_DEPENDENT_LEGS", _inert_empty_the_chf_leg_set),
]


@pytest.mark.parametrize(
    "name,probe", _DISCLOSED_INERT_ROUTES, ids=[r[0] for r in _DISCLOSED_INERT_ROUTES]
)
def test_d105_r1_the_routes_called_harmless_are_still_harmless(name, probe, monkeypatch):
    """The other direction. This project has retracted an overclaim twice, so the
    disclosure states what does NOT reach the rules, and that half is measured too."""
    truth = ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    probe(monkeypatch)
    after = ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    assert after.eligible == truth.eligible, (
        f"the disclosure says {name} does not reach the rules, and it now does"
    )
    assert [v.axis for v in after.violations] == [v.axis for v in truth.violations]


def test_d105_r1_widening_the_adopted_status_set_refuses_rather_than_forging(monkeypatch):
    """The third inert route refuses instead of returning: three CHF correlations become
    adopted at once and the ambiguity guard declines to pick one. Disclosed as a refusal
    rather than as a steering route, because that is what it measures as."""
    monkeypatch.setattr(ac, "ADOPTED_FOR_RANKING", frozenset(Status))
    with pytest.raises(ValueError, match="adopted for ranking"):
        ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    assert "refuses" in _disclosure_section()


def test_d105_r1_the_disclosure_states_the_mechanism_not_only_its_instances():
    """The question this gate keeps having to ask: does the text name the mechanism, or
    one of the things the mechanism can do?

    Anchored on two claims that are about the mechanism rather than about any route --
    that the rules are reached by name at call time, and that the enumerated routes are
    illustrative. A section listing four routes without either would be four instances.
    """
    section = _disclosure_section()
    assert "by name" in section and "call time" in section, (
        "the disclosure names routes but not the mechanism that makes them work"
    )
    assert "illustrative" in section, (
        "the disclosure reads as a complete list, which it is not and cannot be"
    )
    assert "not any particular name" in section
def _executable_lines(source: str) -> str:
    """``source`` with every comment and every BARE STRING STATEMENT removed.

    D104 replaced a line filter -- which dropped only lines *containing* a triple quote,
    so docstring interiors were scanned as executable code -- with an ast walk. D105:
    that walk read ``body[0]`` only, and a function can carry more than one bare string.
    Both seam functions did: the D104 warning became ``__doc__`` and the sentence
    describing what the function computes became an orphan below it, unreachable from
    ``help()`` and scanned here as implementation.

    So the rule is the general one and not the docstring one: **an ``Expr`` whose value
    is a string constant is documentation wherever it appears.** Walking every node
    rather than each body's head also covers strings nested in ``if``/``try``/``for``
    bodies, which a head-of-body reading cannot see at all.
    """
    documentation_lines: set[int] = set()
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            documentation_lines.update(range(node.lineno, (node.end_lineno or 0) + 1))
    return "\n".join(
        line for number, line in enumerate(source.splitlines(), start=1)
        if number not in documentation_lines and not line.lstrip().startswith("#")
    )


_TWO_STRING_SOURCE = '''\
def seam(entries, leg):
    """A warning that became the docstring."""
    """What the function computes. The tolerance comparison -- gravity_rel_tol -- lives
    in the registry, not here, and this sentence is the maintainer's note saying so."""
    if leg:
        """A third string, nested, where a head-of-body reading cannot see it at all:
        gravity_rel_tol again."""
        return entries[0]
    return None
'''


def test_d105_r2_documentation_below_the_first_string_is_not_read_as_code():
    """**The planted-prose witness, in the shape the finding used.**

    A maintainer's note mentioning the tolerance is placed in the SECOND string of a
    function and again in a nested THIRD. Under the ``body[0]`` reading both survive
    stripping and S5-6 fires on documentation; under this one neither does. The control
    below keeps that from being satisfied by a stripper that deletes everything.
    """
    body = _executable_lines(_TWO_STRING_SOURCE)

    assert "gravity_rel_tol" not in body, (
        "prose in a non-first string is still being read as executable code"
    )
    assert "def seam(entries, leg):" in body and "return entries[0]" in body, (
        "the stripper removed executable code, so 'no match' would mean nothing"
    )
    # And the head-of-body reading it replaces genuinely fails this, so the witness is
    # not describing a distinction without a difference.
    head_only: set[int] = set()
    for node in ast.walk(ast.parse(_TWO_STRING_SOURCE)):
        if isinstance(node, (ast.Module, ast.FunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                head_only.update(range(first.lineno, (first.end_lineno or 0) + 1))
    under_the_old_rule = "\n".join(
        line for number, line in enumerate(_TWO_STRING_SOURCE.splitlines(), start=1)
        if number not in head_only
    )
    assert "gravity_rel_tol" in under_the_old_rule, (
        "the reading this replaced would have passed too, so nothing was repaired"
    )


def test_d105_r2_each_seam_carries_one_docstring_holding_both_things():
    """``help()`` must reach the criterion, not only the warning.

    S4-8's distinction -- ``None`` is an absence of knowledge, not an ineligibility --
    was in an orphaned string below each seam's docstring, so it was invisible to
    ``help()`` and to every reader who did not open the file.
    """
    for seam, needle in (
        (ac._assess_leg_against_a_supplied_registry, "not"),
        (ac._assess_fluid_against_a_supplied_registry, "S5-1"),
    ):
        doc = inspect.getdoc(seam) or ""
        assert "NOT THE API" in doc, "the seam must still announce that it is a seam"
        assert "What it computes" in doc, (
            f"{seam.__name__}.__doc__ does not carry what the function computes; it is "
            "still an orphan string that help() cannot reach"
        )
        assert needle in doc

    leg_doc = inspect.getdoc(ac._assess_leg_against_a_supplied_registry) or ""
    assert "absence of knowledge" in leg_doc and "S4-8" in leg_doc, (
        "the S4-8 criterion is not reachable from help() on the seam that implements it"
    )

    source = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    orphans = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for statement in node.body[1:]:
            if isinstance(statement, ast.Expr) and isinstance(
                statement.value, ast.Constant
            ) and isinstance(statement.value.value, str):
                orphans.append(f"{node.name}:{statement.lineno}")
    assert not orphans, (
        "bare string statements below the docstring, unreachable from help(): "
        + ", ".join(orphans)
    )


# ======================================================================================
# D106 — the anti-overclaim half names its boundary, and the worked example is witnessed
# ======================================================================================

_REAL_CHF_ID = "two_phase.chf.shah_1987"


def _forge_a_chf_leg(**over):
    """Direct construction of a CHF-dependent record with a caller-chosen outcome.

    Refused by the mint under the real :data:`CHF_DEPENDENT_LEGS`; permitted once that
    set is emptied. It is the same call either way -- that is the point of the pair.
    """
    fields = {
        "fluid": "ammonia", "leg": "chf", "entry_id": _REAL_CHF_ID,
        "eligible": True, "violations": (), "gravity_basis": None,
    }
    return ac.LegEligibility(**{**fields, **over})


def _guard_mint():
    return _forge_a_chf_leg()


def _guard_s5_4_basis_requirement():
    return _forge_a_chf_leg(gravity_basis=None).gravity_basis


def _guard_s5_5_bool_refusal():
    return bool(ac.assess_leg("water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE))


def _guard_replace_refusal():
    return ac.assess_leg(
        "water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE
    ).__replace__(eligible=True)


def _guard_registry_gravity_bases():
    """Unlike the other four this one reports rather than refuses, so it is written to
    the same polarity deliberately: it raises while a CHF basis is still enumerated and
    returns once the enumeration has gone empty. Same shape, same pair of assertions."""
    bases = ac._registry_gravity_bases()
    if bases:
        raise TypeError(f"a CHF gravity basis is still enumerated: {len(bases)}")
    return bases


#: (guard, the text the clause must carry, the probe). Same rule as the four steering
#: routes: a guard cannot be named in the clause without a demonstration beside it, and
#: cannot be demonstrated without being named. The probe here is DIRECT CONSTRUCTION
#: and the guards around it -- not the computation, which is the boundary the original
#: claim was measured against and the reason the clause was needed.
_GUARDS_GATED_ON_CHF_DEPENDENT_LEGS = [
    ("the mint", "mint check never runs", _guard_mint),
    ("S5-4's basis requirement", "gravity_basis=None", _guard_s5_4_basis_requirement),
    ("S5-5's bool refusal", "returns a bare truth value", _guard_s5_5_bool_refusal),
    ("__replace__'s refusal", "``__replace__`` stops refusing", _guard_replace_refusal),
    ("the gravity-basis enumeration", "zero bases instead of one",
     _guard_registry_gravity_bases),
]


@pytest.mark.parametrize(
    "guard,needle,probe", _GUARDS_GATED_ON_CHF_DEPENDENT_LEGS,
    ids=[g[0] for g in _GUARDS_GATED_ON_CHF_DEPENDENT_LEGS],
)
def test_d106_each_guard_gated_on_chf_dependent_legs_is_named_and_demonstrated(
    guard, needle, probe, monkeypatch
):
    """**Inert for the computation is not inert for the mint, one guard at a time.**

    ``CHF_DEPENDENT_LEGS`` was disclosed at D105 as a name that does not move
    eligibility. That was measured against :func:`assess_leg`'s outcome and it is true.
    It is also the gate on every CHF-specific guard in the module, so the same
    assignment that changes no computed answer switches all five off.

    Each guard must refuse under the real set and stop refusing under the emptied one.
    The first half is what makes the second half mean something: a probe that never
    refused to begin with would demonstrate nothing about the gate.
    """
    assert needle in _disclosure_prose(), (
        f"the clause does not name {guard}, which is measured here to be gated on "
        "CHF_DEPENDENT_LEGS. A bound that omits a measured guard is not a bound."
    )

    with pytest.raises(TypeError):
        probe()

    monkeypatch.setattr(ac, "CHF_DEPENDENT_LEGS", frozenset())
    probe()  # the same call, now permitted: the guard was gated on that one name


def test_d106_the_worked_example_forges_a_serialisable_record(monkeypatch):
    """The consequence stated end to end, because five disabled guards is an inventory
    and this is what they add up to: a record that *serialises* as a valid CHF
    eligibility carrying the real entry id and an outcome the caller chose."""
    truth = ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    assert truth.eligible is False

    monkeypatch.setattr(ac, "CHF_DEPENDENT_LEGS", frozenset())

    # Half one: the computation is untouched. This is the D105 claim, still true.
    after = ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    assert after.eligible is False
    assert [(v.axis, v.consequence) for v in _checked(after)] == [
        (Axis.ORIENTATION, Consequence.DE_RANK)
    ]

    # Half two: the mint is gone, and the forgery serialises.
    forged = _forge_a_chf_leg()
    record = forged.as_record()
    assert record["entry_id"] == _REAL_CHF_ID
    assert record["eligible"] is True
    assert record["leg"] == "chf"


def test_d106_the_clause_states_the_rule_and_the_boundary_it_measured():
    """The clause must generalise, or it is five instances where three were.

    Anchored on the boundary statement and on the rule, not on any one guard -- the
    same test the four steering routes are held to one paragraph up.
    """
    section = _disclosure_prose()
    assert "boundary it was measured against" in section, (
        "the anti-overclaim half does not say what its claims were measured against"
    )
    assert "inert for the COMPUTATION may be" in section and "MINT" in section, (
        "the clause gives the worked example without the rule behind it"
    )
    assert "unmeasured rather than as general" in section


def test_d106_adopted_for_ranking_is_bounded_as_the_clause_says(monkeypatch):
    """The clause calls this one bounded. Checked against the boundaries that caught
    ``CHF_DEPENDENT_LEGS``, not only against the computation."""
    assert "ADOPTED_FOR_RANKING` **is bounded.**" in _disclosure_prose()

    monkeypatch.setattr(ac, "ADOPTED_FOR_RANKING", frozenset())
    assert ac.adopted_entry("chf") is None
    assert ac.assess_leg("water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE) is None

    # The CHF guards are untouched: they gate on a different name.
    with pytest.raises(TypeError):
        _forge_a_chf_leg()


def test_d106_the_source_registry_claim_is_scoped_to_this_module():
    """``TWO_PHASE_CORRELATIONS`` is inert *here* and live for a call-time consumer.

    Measured rather than reasoned: this module's snapshot does not move, and
    ``radiator_coupling`` -- which resolves its pressure domain from the source
    registry at call time, the D97/F-04 repair -- does. Asserting the second half is
    what stops the first from being written as "does nothing".
    """
    section = _disclosure_prose()
    assert "bounded for this module" in section
    assert "_dp_pressure_domain" in section

    program = """
from orbital_thermal import two_phase_architecture_cases as ac
from orbital_thermal import radiator_coupling as RC
from orbital_thermal.registry import two_phase as tp

RC._dp_pressure_domain()
tp.TWO_PHASE_CORRELATIONS = ()

try:
    leg = ac.assess_leg('water', 'chf', gravity_m_s2=1e-6,
                        geometry='round_tube', orientation='vertical_upflow')
    here = 'unmoved' if leg is not None and leg.eligible is False else 'MOVED'
except Exception as exc:
    here = 'MOVED(%s)' % type(exc).__name__

try:
    RC._dp_pressure_domain()
    there = 'unmoved'
except Exception:
    there = 'moved'

print(here, there)
"""
    completed = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True,
        env=_child_env(),  # D107: without this the child imports only from an
                           # ambient install, and this check silently did not run.
    )
    out = completed.stdout.strip()
    assert completed.returncode == 0, f"the probe itself failed: {completed.stderr[-300:]}"
    assert out == "unmoved moved", (
        f"measured {out!r}, expected 'unmoved moved': the source-registry claim's "
        "scope no longer holds. Either this module now reads the source registry live "
        "-- in which case it is a fifth steering route and not a bounded one -- or the "
        "consumer that did has stopped. Re-measure the clause either way."
    )


# ======================================================================================
# D107 — a child process that inherits no import path can only import from an install
# ======================================================================================

_LAUNCHERS = frozenset({"run", "Popen", "call", "check_call", "check_output"})


def _subprocess_launches_without_env(source: str, label: str) -> list[str]:
    """Every subprocess launch in ``source`` that passes no ``env``. DERIVED, by parse.

    The names that launch a child are resolved from the module's own imports rather
    than assumed: ``subprocess.run(...)`` after ``import subprocess``, and a bare
    ``run(...)`` after ``from subprocess import run``. A module that imports it under
    another name is covered because the binding is what is tracked, not the spelling.

    Parsed and not grepped, and the difference is not stylistic. This project has
    counted twelve instances of a check that could not tell a thing from a description
    of one, and the witness below is itself a test file containing the literal text
    ``subprocess.run(`` inside a string. A token search finds that string; an ast walk
    sees a ``Constant``, which is what it is.
    """
    tree = ast.parse(source)

    aliases: set[str] = set()          # names bound to the subprocess MODULE
    launchers: set[str] = set()        # names bound to a launcher FUNCTION
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            for alias in node.names:
                if alias.name in _LAUNCHERS:
                    launchers.add(alias.asname or alias.name)

    findings: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            launches = (
                isinstance(func.value, ast.Name)
                and func.value.id in aliases
                and func.attr in _LAUNCHERS
            )
        elif isinstance(func, ast.Name):
            launches = func.id in launchers
        else:
            launches = False
        if not launches:
            continue
        if any(keyword.arg is None for keyword in node.keywords):
            continue  # ``**kwargs`` may carry env; not decidable here, so not claimed
        if not any(keyword.arg == "env" for keyword in node.keywords):
            findings.append(f"{label}:{node.lineno}")
    return findings


def test_d107_every_subprocess_launch_in_the_suite_passes_an_env():
    """**The class, not the call that was found.**

    ``pyproject.toml``'s ``pythonpath = ["src"]`` configures the pytest process; a child
    of it inherits nothing, so a launch without ``env`` resolves ``orbital_thermal``
    only from an ambient install. The comment that put that setting there records why
    that matters: *"a suite whose result depends on ambient install state can lie about
    itself."* It did -- the D106 scope witness passed here and failed on a bare
    checkout, and a hand-back carried a total that did not reproduce.

    Every test module is walked, so a launch added in a file that does not exist yet is
    covered without this test being edited.
    """
    offenders: list[str] = []
    scanned = 0
    for path in sorted(pathlib.Path(__file__).parent.glob("*.py")):
        scanned += 1
        offenders += _subprocess_launches_without_env(
            path.read_text(encoding="utf-8"), path.name
        )
    assert scanned > 1, "the scan found no test modules, so it proves nothing"
    assert not offenders, (
        "subprocess launched without env=_child_env(), so the child can import the "
        "package only from an ambient install: " + ", ".join(offenders)
    )


_PLANTED_SOURCES = {
    "bare attribute call": ('''
import subprocess
import sys
subprocess.run([sys.executable, "-c", "pass"], capture_output=True)
''', True),
    "aliased module": ('''
import subprocess as sp
sp.check_output(["x"])
''', True),
    "imported launcher": ('''
from subprocess import run
run(["x"], text=True)
''', True),
    "launcher renamed on import": ('''
from subprocess import Popen as spawn
spawn(["x"])
''', True),
    "env passed": ('''
import subprocess
subprocess.run(["x"], env={"PYTHONPATH": "src"})
''', False),
    "env forwarded through kwargs": ('''
import subprocess
def go(**kw):
    return subprocess.run(["x"], **kw)
''', False),
    "a call that is only described, in a string": ('''
DOC = """call subprocess.run([sys.executable]) without env and the child cannot import"""
''', False),
    "an unrelated run()": ('''
def run(x):
    return x
run(3)
''', False),
}


@pytest.mark.parametrize(
    "label", sorted(_PLANTED_SOURCES), ids=sorted(_PLANTED_SOURCES)
)
def test_d107_the_guard_fires_on_a_planted_launch_and_not_on_the_rest(label):
    """Plant one, and require the guard to find it -- then plant the near-misses.

    The last two are the reason this is a parse: a launch written inside a string is a
    description of one, and an unrelated function called ``run`` is not subprocess at
    all. A grep fails both.
    """
    source, should_fire = _PLANTED_SOURCES[label]
    findings = _subprocess_launches_without_env(source, "planted")
    if should_fire:
        assert findings, f"the guard did not find the planted launch in {label!r}"
    else:
        assert not findings, f"the guard fired on {label!r}, which is not a defect"


def test_d107_the_child_actually_imports_the_package_under_test():
    """The positive control, and the thing the D106 witness assumed without checking.

    ``_child_env`` is one function in one place now, so this is the single assertion
    that it does what all three call sites need: a child launched with it imports
    ``orbital_thermal`` from the tree under test, not from wherever an install points.
    """
    completed = subprocess.run(
        [sys.executable, "-c",
         "import orbital_thermal, pathlib; print(pathlib.Path(orbital_thermal.__file__))"],
        capture_output=True, text=True, env=_child_env(),
    )
    assert completed.returncode == 0, completed.stderr[-400:]
    child_sees = pathlib.Path(completed.stdout.strip()).resolve()
    parent_sees = pathlib.Path(ac.__file__).resolve().parent / "__init__.py"
    assert child_sees == parent_sees, (
        f"the child imported {child_sees}, the parent {parent_sees}. A child resolving "
        "the package somewhere else is the incident pyproject.toml's pythonpath comment "
        "describes: a second tree silently repointing the one under test."
    )


# ======================================================================================
# D110 — an input the enumeration excluded. OTB-G002 criterion 6, at the S5 surface.
# ======================================================================================

#: Values no ordered comparison can place. ``nan`` compares false against everything,
#: so ``x <= 0`` and ``x > 0`` are both false and every sign-shaped guard is skipped;
#: the infinities order fine but are not quantities a correlation's database contains.
_UNORDERABLE_FLOATS = {"nan": math.nan, "+inf": math.inf, "-inf": -math.inf}

#: The finite values that must keep their present outcomes. Zero and negative gravity
#: are *refused by the mechanism* (``REJECT``) rather than by validation, and that is a
#: behaviour this repair must not disturb -- a finiteness check placed carelessly turns
#: a graded refusal into a raised one, which is a different statement about the case.
_FINITE_NONPHYSICAL_GRAVITIES = {"zero": 0.0, "negative": -9.80665}


def _public_case_inputs() -> dict[str, str]:
    """Every input a caller can hand the public S5 API, DERIVED from two signatures.

    The named parameters of :func:`assess_leg` and :func:`assess_fluid`, plus -- because
    ``**case`` is forwarded verbatim -- the parameters of :meth:`Applicability.check`.
    Nothing is listed, so an input added to either signature is probed here without this
    file being edited. That is the whole point: D110 was an input that both instruments
    looking at this surface had removed from their own population.
    """
    found: dict[str, str] = {}
    for entry_point in (ac.assess_leg, ac.assess_fluid):
        for name, parameter in inspect.signature(entry_point).parameters.items():
            if parameter.kind is inspect.Parameter.VAR_KEYWORD:
                continue
            found[name] = str(parameter.annotation)
    for name, parameter in inspect.signature(Applicability.check).parameters.items():
        if name != "self":
            found.setdefault(name, str(parameter.annotation))
    assert "gravity_m_s2" in found, (
        "the derivation lost the parameter D110 was reported against, which is the "
        "failure mode this witness exists to make impossible"
    )
    return found


def _numeric_public_inputs() -> list[str]:
    return sorted(n for n, ann in _public_case_inputs().items() if "float" in ann)


def _textual_public_inputs() -> list[str]:
    """The string-valued half of the same derived surface, and it is probed too.

    D111: the exclusion guard below used to read the SIGNATURE map, so a name counted
    as covered merely by existing as a parameter. ``fluid`` and ``leg`` sat in that map
    with nothing running against them. A population that is exercised is the only kind
    that can pay for an exclusion, so this one exists and is probed.
    """
    return sorted(
        n for n, ann in _public_case_inputs().items()
        if "str" in ann and "float" not in ann
    )


#: Values the string inputs admit and no basis contains.
_UNDECLARED_TEXT = {"empty": "", "blank": "   ", "unknown": "«?»"}


@pytest.mark.parametrize("name", _textual_public_inputs())
@pytest.mark.parametrize("label", sorted(_UNDECLARED_TEXT))
def test_d110_a_value_outside_a_declared_axis_is_graded_not_admitted(name, label):
    """**The textual half of the same surface, with the property the axes actually have.**

    Stated against the correlation's own :attr:`~Applicability.declared_axes` rather
    than as "never eligible", because that would be false and this project has retracted
    two overclaims. The rule is the one the module already enforces -- *silence is not
    consent on a DECLARED axis* -- so: a value outside an axis the correlation declares
    must be graded; on an axis it declares nothing about, admission is the declaration's
    doing and is recorded here rather than asserted away.

    The axis for each input is resolved through the ``Axis`` enum's own values, so a new
    constrained axis is mapped without this test being edited.
    """
    leg = _assess_with(name, _UNDECLARED_TEXT[label])

    if name == "leg":
        assert leg is None, (
            "an unknown leg must yield NO record: no adopted correlation is an absence "
            "of knowledge, not an ineligibility (S4-8)"
        )
        return

    if leg is None or leg.eligible is False:
        return  # graded, or no correlation to grade -- either is the rule holding

    spec = ac.adopted_entry("chf").applicability_spec
    try:
        axis = Axis(name)
    except ValueError:  # pragma: no cover - an input that names no axis
        return
    if axis not in spec.declared_axes:
        return  # the correlation constrains nothing on this axis; admission is correct

    # Declared, and admitted. That is correct for exactly one declaration shape: an
    # axis constrained by an EXCLUSION set and no inclusion set constrains its listed
    # members and nothing else, so a value outside the list is outside the constraint
    # rather than through it. Recorded here rather than asserted away -- and the shape
    # is checked, so the carve-out cannot quietly widen.
    exclusion_fields = [
        f.name for f in dataclasses.fields(Applicability)
        if f.name.startswith("excluded_")
    ]
    assert exclusion_fields == ["excluded_fluids"], (
        "another axis has gained an exclusion set, so this carve-out is no longer "
        f"about one axis and must be generalised: {exclusion_fields}"
    )
    assert axis is Axis.FLUID and not spec.fluids and spec.excluded_fluids, (
        f"{name}={_UNDECLARED_TEXT[label]!r} was admitted as eligible although the "
        f"correlation declares {axis.name} through an inclusion set. A declared axis "
        "is binding, and silence on it is not consent."
    )


def _assess_with(name: str, value: object):
    """``assess_leg`` on the reference case with one input replaced."""
    call = {"gravity_m_s2": _REFERENCE_G, **_FULL_CASE, name: value}
    fluid = call.pop("fluid", "water")
    leg = call.pop("leg", "chf")
    return ac.assess_leg(fluid, leg, **call)


@pytest.mark.parametrize("name", _numeric_public_inputs())
@pytest.mark.parametrize("label", sorted(_UNORDERABLE_FLOATS))
def test_d110_no_unorderable_value_on_any_numeric_input_mints_an_eligible_record(
    name, label
):
    """**The class: an input a sign test cannot order must never produce eligibility.**

    Reported for ``gravity_m_s2`` at ``nan``. Measured before building, the same
    boundary admitted ``nan`` and both infinities on ``liquid_reynolds``,
    ``branch_value`` and ``branch_value_at_reference_gravity`` as well -- nine further
    cells, every one of them minting ``eligible=True`` with the genuine adopted basis
    attached. So the assertion is over the derived numeric surface, not over the cell
    that was reported.

    The property is stated as *never eligible*, which is weaker than *always raises*
    and is deliberate: it holds whether an input is refused by validation or graded by
    the mechanism, so it does not quietly mandate one of those. The next test pins
    which one gravity gets.
    """
    statable = name in ac.CASE_FACTS or name in _STATED_BY_THE_COMPUTATION
    with pytest.raises((ValueError, TypeError)) as refusal:
        _assess_with(name, _UNORDERABLE_FLOATS[label])
    # D118 split this population in two, and which half a name falls in is
    # derived rather than listed: a name a caller may state must reach the
    # finiteness check, and a name that is not a caller's to state must never
    # reach the computation at all. Either way no eligible record is minted --
    # which is the property this test asserted before and still asserts.
    expected = "must be finite" if statable else "not a case fact"
    assert expected in str(refusal.value), (
        f"{name} was refused as {refusal.value!r}, expected a {expected!r} "
        "refusal; the two halves of this population must not drift together"
    )


def test_d110_nan_gravity_is_refused_through_assess_fluid_too():
    """The finding reported both entry points, so both are witnessed."""
    with pytest.raises(ValueError, match="gravity_m_s2 must be finite"):
        ac.assess_fluid("water", gravity_m_s2=math.nan, **_FULL_CASE)


def test_d110_the_paired_control_a_valid_case_must_still_evaluate():
    """**The paired control, which is part of criterion 6 and not an extra.**

    *"A valid case must still evaluate, so 'refuses everything' cannot satisfy this."*
    Both controls, unchanged from before the repair: standard gravity is eligible with
    no violations, and microgravity is de-ranked on ``ORIENTATION``. A validation that
    took either of these would be a worse defect than the one it fixed.
    """
    at_reference = ac.assess_leg("water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE)
    assert _checked(at_reference) == (), (
        "no evaluated axis finds against the reference case; refusing everything "
        "is what this control exists to exclude"
    )
    assert at_reference.gravity_basis.reference_gravity_m_s2 == _REFERENCE_G

    in_microgravity = ac.assess_leg(
        "water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE
    )
    assert in_microgravity.eligible is False
    assert [(v.axis, v.consequence) for v in _checked(in_microgravity)] == [
        (Axis.ORIENTATION, Consequence.DE_RANK)
    ]


@pytest.mark.parametrize("label", sorted(_FINITE_NONPHYSICAL_GRAVITIES))
def test_d110_a_finite_nonphysical_gravity_is_still_graded_not_newly_refused(label):
    """Zero and negative gravity were already refused **by the mechanism**, as
    ``Axis.ORIENTATION`` / ``Consequence.REJECT``, and they stay that way.

    This is the guard against fixing the reported cell by widening the check until it
    swallows its neighbours. A raised refusal and a ``REJECT`` violation are different
    statements -- one says the input was not a quantity, the other says the case fails a
    physical gate -- and only the first is what ``nan`` warrants.
    """
    leg = _assess_with("gravity_m_s2", _FINITE_NONPHYSICAL_GRAVITIES[label])
    assert leg.eligible is False
    assert [(v.axis, v.consequence) for v in _checked(leg)] == [
        (Axis.ORIENTATION, Consequence.REJECT)
    ]


def test_d110_every_numeric_input_at_the_boundary_is_finiteness_validated():
    """Derived completeness: a numeric parameter added to ``check`` without being
    validated fails here, rather than waiting for someone to pass it a ``nan``.

    Executed rather than read off the source, because a check that is present and
    unreached is what four of this gate's twelve self-referential findings were.
    """
    unguarded = []
    for name in _numeric_public_inputs():
        try:
            _assess_with(name, math.nan)
        except ValueError:
            continue  # reached the finiteness check and was refused by it
        except TypeError:
            continue  # D118: not a caller's to state, so it never gets there
        unguarded.append(name)
    assert not unguarded, (
        "numeric inputs reach the applicability comparisons without a finiteness "
        f"check, so nan skips every sign-shaped guard on them: {unguarded}"
    )


def test_d110_the_d104_witness_exclusion_is_paid_for_by_this_population():
    """**The enforcement half: an exclusion must be paid for, not merely reasoned.**

    ``_steering_keywords`` discards ``fluid``, ``leg``, ``gravity_m_s2`` and ``case``.
    That discard was correct for the question D104 asked -- those are the parameters a
    caller legitimately passes, so re-passing one produces a duplicate-argument
    ``TypeError`` and demonstrates nothing about whether a caller can supply the
    *rules*. It was reasoned, and it stays.

    What was wrong was the conclusion drawn beside it. A population that removes an
    input cannot support "the case surface is clean", and that sentence was written
    anyway. So the exclusion is now bound to a compensating population: every name
    discarded there must appear in the inputs derived here. Dropping a name from one
    witness without it being covered by another fails this test.
    """
    discarded = {"fluid", "leg", "gravity_m_s2", "case"}
    # D111: the union of the populations the probes above actually consume, NOT the
    # signature map. A name is in the signature whether or not anything runs against
    # it, so anchoring there confirmed that a parameter exists and said nothing about
    # its coverage -- the very substitution this test was written to close, inside the
    # test written to close it. Every population that feeds a parametrize is unioned
    # here; adding a probe over a new population means adding it to this union.
    covered = set().union(*_exercised_populations().values())
    uncovered = discarded - covered - {"case"}  # "case" is the **kwargs name itself
    assert not uncovered, (
        "these inputs are excluded from the D104 steering population and covered by no "
        f"other witness, so nothing on this surface tests them: {sorted(uncovered)}"
    )


# ======================================================================================
# D114 — a rule fact arriving as a keyword, and a population that could not see it
# ======================================================================================


def _boolean_public_inputs() -> list[str]:
    """The boolean third of the derived surface.

    It exists because ``has_executable_form`` existed and neither of the other two
    populations could hold it: one selects on ``"float" in ann``, the other on
    ``"str" in ann``, and ``bool`` is neither. Adding this branch is *not* the repair
    -- a partition by annotation always has a next annotation, and the next one would
    be invisible the same way. The repair is
    :func:`test_d114_every_discovered_public_input_belongs_to_an_exercised_population`,
    which requires the union to be TOTAL and so fails on an annotation nobody has
    thought of yet.
    """
    return sorted(
        n for n, ann in _public_case_inputs().items()
        if "bool" in ann and "str" not in ann and "float" not in ann
    )


def _exercised_populations() -> dict[str, list[str]]:
    """Every population a probe above actually runs over, by name."""
    return {
        "numeric": _numeric_public_inputs(),
        "textual": _textual_public_inputs(),
        "boolean": _boolean_public_inputs(),
    }


def test_d114_every_discovered_public_input_belongs_to_an_exercised_population():
    """**Total, not partitioned. This is the fourth enforcement defect's repair.**

    Three witnesses looked at this surface and none could see ``has_executable_form``.
    Two derived populations split it by annotation and a ``bool`` fell between them;
    the compensation check asked only whether four named inputs were covered, so a
    discovered input covered by nothing was not a question it could ask. The gate brief
    had named that gap in writing -- *"an input annotated in a way neither branch
    matches is invisible to both"* -- and it shipped unprobed.

    So the assertion is equality, in both directions. An input discovered on the public
    surface and exercised by no population fails; a population naming something the
    surface does not discover fails too, because that means a probe is running against
    a parameter that no longer exists and reporting coverage for it.
    """
    discovered = set(_public_case_inputs())
    exercised: set[str] = set()
    for population in _exercised_populations().values():
        exercised.update(population)

    unprobed = discovered - exercised
    assert not unprobed, (
        "these public inputs belong to no exercised population, so nothing runs "
        f"against them however many probes exist: {sorted(unprobed)}. Add a population "
        "that exercises them -- not a branch that merely classifies them."
    )
    stale = exercised - discovered
    assert not stale, (
        f"these are probed but are no longer public inputs: {sorted(stale)}"
    )


@pytest.mark.parametrize("name", _boolean_public_inputs())
@pytest.mark.parametrize("value", [True, False], ids=["true", "false"])
def test_d114_a_caller_cannot_state_a_boolean_rule_fact(name, value):
    """**Control one: the caller cannot move eligibility with it, either way.**

    Both values are refused, not just the one that changed the outcome. ``True``
    happens to match every adopted entry today, so passing it moved nothing and a
    witness that only tried ``False`` would have called the keyword harmless. Whether a
    caller's assertion agrees with the truth is not what makes it improper.
    """
    with pytest.raises(TypeError, match="not a case fact"):
        _assess_with(name, value)


def test_d114_the_refusal_is_by_construction_and_not_by_name():
    """The allowlist is the mechanism, so a name nobody has heard of is refused too.

    Four earlier repairs of this class each removed a named door and were each followed
    by another name. A blocklist would have to grow once per finding; an allowlist
    refuses the next parameter on the day it is added to ``check``, which is the
    difference being witnessed here.
    """
    with pytest.raises(TypeError, match="not a case fact"):
        ac.assess_leg(
            "water", "chf", gravity_m_s2=_REFERENCE_G,
            **_FULL_CASE, a_parameter_invented_for_this_test=1,
        )
    assert "has_executable_form" not in ac.CASE_FACTS
    assert not (ac.CASE_FACTS & {"fluid", "gravity_m_s2", "has_executable_form"}), (
        "a value the computation states must never be listed as a caller's to state"
    )


def test_d114_every_check_parameter_is_accounted_for():
    """Nothing in ``check``'s signature may be neither stated nor allowed. DERIVED.

    The allowlist is written by hand, so this is what keeps it honest: every parameter
    of :meth:`Applicability.check` is either a case fact a caller may state or a value
    the computation states from the entry, and a parameter added to that method belongs
    to neither until someone decides which. It fails on the day the parameter appears
    rather than on the day someone passes it -- which is the whole gap D114 came
    through.
    """
    stated_by_the_computation = set(_STATED_BY_THE_COMPUTATION)
    signature = {
        name for name in inspect.signature(Applicability.check).parameters
        if name != "self"
    }
    # D118 added a third class, and the partition has to name it or the three
    # removed quantities would read as an accounting error rather than as a
    # decision: parameters this boundary can neither take from a caller nor
    # derive, whose axes are reported unevaluable instead.
    unevaluable_here = _DERIVED_BEYOND_THIS_BOUNDARY
    assert not (unevaluable_here & (ac.CASE_FACTS | stated_by_the_computation)), (
        "a quantity cannot be both unevaluable here and supplied here"
    )
    unaccounted = (
        signature - ac.CASE_FACTS - stated_by_the_computation - unevaluable_here
    )
    assert not unaccounted, (
        "parameters of Applicability.check that are neither declared case facts nor "
        f"stated by the computation: {sorted(unaccounted)}. Decide which, in "
        "CASE_FACTS or in the computation's own dict -- until then a caller reaches "
        "them through **case."
    )
    assert stated_by_the_computation <= signature, (
        "the computation states a value that is no longer a parameter of check()"
    )


def _entry_with_no_reachable_executable_form():
    """The adopted CHF entry with no reachable implementation, at the ENTRY.

    ``has_executable_form`` is true for *either* a callable on the entry *or* a
    declared path that resolves, so both have to go: the callable is removed and the
    path is pointed at a module that does not exist. Measured rather than assumed --
    the first version of this helper changed only the path and the property stayed
    ``True``, because ``evaluate`` short-circuits it, which would have made the control
    below assert against a case it had not actually created.
    """
    return tuple(
        dataclasses.replace(
            e, evaluate=None, executable_form="orbital_thermal.nothing_lives_here")
        if e.kind == "chf" and e.status in ac.ADOPTED_FOR_RANKING else e
        for e in ac.REGISTRY_ENTRIES
    )


def test_d114_the_paired_control_the_entry_still_moves_the_outcome():
    """**Control two, and the one that says the repair is not just a wall.**

    A fix that made executability unreachable from anywhere would pass every assertion
    above and would be wrong: the value is load-bearing and must still decide the
    outcome when it changes *at the entry*. So the same fact, moved where it actually
    lives, must still block the leg.
    """
    entries = _entry_with_no_reachable_executable_form()
    adopted = next(e for e in entries if e.kind == "chf" and e.status in ac.ADOPTED_FOR_RANKING)
    assert adopted.has_executable_form is False, (
        "the entry still resolves an executable form, so this proves nothing about "
        "whether the computation reads it"
    )

    blocked = ac._assess_leg_against_a_supplied_registry(
        entries, "water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE
    )
    assert blocked.eligible is False
    assert (Axis.PROVENANCE, Consequence.BLOCK) in [
        (v.axis, v.consequence) for v in blocked.violations
    ], "the entry executable form must be what blocks the leg"

    # And the control's control: with the real registry the same call is eligible, so
    # the difference above is the entry's executable form and nothing else.
    unblocked = ac._assess_leg_against_a_supplied_registry(
        ac.REGISTRY_ENTRIES, "water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE
    )
    assert (Axis.PROVENANCE, Consequence.BLOCK) not in [
        (v.axis, v.consequence) for v in unblocked.violations
    ]
    assert _checked(unblocked) == ()


def test_d114_the_computation_reads_executability_rather_than_a_default():
    """The value is passed, not defaulted. Witnessed by the entry moving it, above --
    this pins the other half: ``check``'s default must not be what decides it.

    If the computation stopped passing the value, ``check`` would fall back to
    ``has_executable_form: bool = True`` and a genuinely unreachable implementation
    would stop blocking. That is the defect one level down from the reported one, and
    it is what the paired control would catch.
    """
    signature = inspect.signature(Applicability.check)
    assert signature.parameters["has_executable_form"].default is True, (
        "the default changed; the paired control above is what proves the computation "
        "does not rely on it, and this note should be re-read if that default moves"
    )
    entry = ac.adopted_entry("chf")
    assert entry.has_executable_form is True, "today's adopted entry, for orientation"


# ======================================================================================
# D115 — a cited basis must be the population that runs
# ======================================================================================


def _closed_basis() -> str:
    """The ``Closed.`` half of the disclosure, out of ``__doc__`` and unwrapped."""
    prose = _disclosure_prose()
    start = prose.index("**Closed.**")
    end = prose.index("**Not closed")
    return prose[start:end]


def test_d115_the_closed_basis_cites_the_populations_that_actually_run():
    """**The D105 pattern turned on the D105 text.**

    A route could not be disclosed without a demonstration beside it. A *basis* could,
    and one was: the paragraph cited dataclass fields as evidence for a claim about
    every call, and the channel D114 came through was a method parameter. The claim was
    true; the evidence named a narrower population than the claim needed.

    So the citation is bound to the populations that exist, derived from
    :func:`_exercised_populations` rather than listed. Cite one that does not run, or
    run one that is not cited, and this fails. It is deliberately symmetric: a basis
    that quietly *drops* a population reads exactly like one that never had it.
    """
    basis = _closed_basis()

    uncited = [name for name in _exercised_populations() if f"**{name}**" not in basis]
    assert not uncited, (
        f"these populations are exercised but the Closed. basis does not cite them: "
        f"{uncited}. A basis narrower than the coverage it stands on is how D114 "
        "reached a channel the paragraph had already declared shut."
    )

    # And the other direction: a population named in bold in the basis must be one that
    # actually runs, so the citation cannot outlive the probe it refers to.
    cited = set(re.findall(r"\*\*(numeric|textual|boolean|[a-z]+)\*\*, carrying", basis))
    unknown = cited - set(_exercised_populations())
    assert not unknown, (
        f"the basis cites populations that no probe runs: {sorted(unknown)}"
    )


def test_d115_the_closed_basis_cites_signatures_and_not_only_dataclass_fields():
    """The specific narrowing that was found, pinned so it cannot recur by omission.

    ``has_executable_form`` is a parameter and not a field. A basis that names only
    field-shaped sources is narrower than a claim about every call, whatever else it
    says.
    """
    basis = _closed_basis()
    assert "signatures" in basis and "parameters, not only dataclass fields" in basis, (
        "the basis does not say that its derived inputs come from signatures; naming "
        "only dataclass fields is the exact narrowing D114 came through"
    )
    for source in ("assess_leg", "assess_fluid", "Applicability.check"):
        assert source in basis, f"the basis does not name {source} as a derived source"


def test_d115_every_witness_the_basis_cites_by_name_exists():
    """A basis that names a witness must name one that is real.

    Cheap, and it closes the way a citation rots: the test is renamed, the paragraph
    keeps pointing at the old name, and the reader takes the pointer for the check.
    """
    cited = set(re.findall(r"test_[a-z0-9_]+", _disclosure_prose()))
    assert cited, "the disclosure cites no witness by name, which this expects"
    defined = {
        name for name in globals()
        if name.startswith("test_") and callable(globals()[name])
    }
    missing = sorted(cited - defined)
    assert not missing, (
        f"the disclosure cites witnesses that do not exist in this module: {missing}"
    )


def test_d115_the_claim_itself_is_unchanged():
    """A basis repair must not become a claim repair.

    The claim was already correct and is now correctly evidenced. A claim that grows to
    match a widened basis is the overclaim direction, which the D105 witnesses refuse in
    the other half of this same paragraph.
    """
    basis = _closed_basis()
    assert "Nothing that arrives *through a call* reaches the rules." in basis or (
        "Nothing that arrives through a call reaches the rules." in basis
    ), "the claim sentence was altered; D115 was a basis repair"
    assert "not a keyword, not ``**case``" in basis
    # The claim is about calls. It must not have crept outward to cover the routes the
    # NEXT half discloses as open -- rebinding, raw writes, replacing the enforcement.
    for overreach in ("cannot be reached", "no route", "is not reachable"):
        assert overreach not in basis, (
            f"the Closed. half now claims {overreach!r}, which contradicts the "
            "disclosure immediately below it"
        )


# ======================================================================================
# D118 — a derived quantity sitting INSIDE the allowlist
# ======================================================================================

_SRC = pathlib.Path(ac.__file__).parent


def _production_modules() -> list[pathlib.Path]:
    """Every shipped module except the one under test. DERIVED from the package."""
    return sorted(
        p for p in _SRC.rglob("*.py")
        if p.name != pathlib.Path(ac.__file__).name and "__pycache__" not in p.parts
    )



class _Shape(enum.Enum):
    """What an expression is, including the answer "I do not recognise this".

    **D129.** Ten cycles asked whether the analysis recognised a form, and after each
    answer another form arrived. Every one of those classifiers -- the widened ones and
    the contract-bounded one alike -- ended in a definite answer: ``_contains_computation``
    returned ``False`` for every shape it did not name, and ``_resolve_callee`` returned
    "not a class". So each depended on its author having thought of the shape, and a
    shape nobody thought of was silently a "no".

    The third answer is the point. A shape the code does not explicitly recognise is
    ``UNKNOWN``, ``UNKNOWN`` is unmeasured, and unmeasured fails. The forms will keep
    coming; what changes is whether the next one arrives as a reviewer's finding or as a
    red row on the day it is written.
    """

    COMPUTED = "computed"
    NOT_COMPUTED = "not_computed"
    UNKNOWN = "unknown"


#: Expression nodes that WORK A VALUE OUT. Explicit, and ``ast.UnaryOp`` is here
#: because D129/F-02 found ``boiling_number=-mass_flux`` classified as not-computed by
#: a claim that said "any call or arithmetic" and matched two node types.
_COMPUTING_SHAPES: tuple[type[ast.AST], ...] = (
    ast.Call,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.Await,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)

#: Expression nodes that are GENUINE LEAVES: no expression child, so a leaf answer is
#: the whole answer.
#:
#: **D130.** This list used to hold eight node types and six of them carry expression
#: children -- ``Attribute``, ``Subscript``, ``Slice``, ``Lambda``, ``JoinedStr``,
#: ``FormattedValue``. Naming them here meant answering ``NOT_COMPUTED`` for
#: ``f(q).attr``, ``[a * b][0]`` and ``f'{a + b}'`` regardless of what those children
#: did, and it was a REGRESSION: the old whole-subtree walk caught
#: ``_bo = [computed][0]`` and the structural classifier stopped at the shapes it named.
#:
#: The fail-closed default could never have caught this, and that is worth stating
#: plainly rather than treating D129 as having been wrong: failing closed removes the
#: dependence on anticipating an UNRECOGNISED shape; it does nothing about a shape that
#: is recognised and answered wrongly. A leaf answer is legitimate only for a leaf, and
#: whether a node is a leaf is a fact about the grammar --
#: ``test_d130_every_reading_shape_is_a_genuine_leaf`` derives it from the ASDL
#: signature rather than from anybody's judgement about ``Attribute``.
_READING_SHAPES: tuple[type[ast.AST], ...] = (
    ast.Name,
    ast.Constant,
)



#: Expression fields a recursing branch deliberately does NOT visit, with the reason.
#:
#: **D131.** The structural witness required each branch to contain a recursive call
#: and never asked what it recursed INTO, so cutting ``Slice`` from three children to
#: two left ``a[1:2:f(i)]`` reading NOT_COMPUTED with the whole suite green. The map
#: that names the missing child -- :func:`_expression_fields_of` -- was already computed
#: three lines above the assertion that did not consult it.
#:
#: This is the ONE record of what is unvisited. The witness reads it rather than
#: carrying its own copy, because two records that can drift is how D124 arose, and
#: every entry must be paired with an executed demonstration in
#: :data:`_EXEMPTION_EVIDENCE` that visiting the field gives the WRONG answer. An
#: exemption with no red row behind it is a claim with no instrument.
#:
#: There is exactly one entry, and it is last cycle's own correction: an ``IfExp``'s
#: test decides which branch is taken and does not contribute to the value. Visiting it
#: makes ``None if geometry is None else geometry.shape`` computed -- ``is None`` is an
#: ``ast.Compare`` -- which reclassifies two genuine case facts as derived quantities
#: and fails six rows.
_UNVISITED_FIELDS: dict[type[ast.AST], tuple[str, ...]] = {
    ast.IfExp: ("test",),
}

#: One expression per exemption where visiting the exempt field would flip a correct
#: NOT_COMPUTED into COMPUTED. Keyed by (node type, field), so an exemption added
#: without a demonstration fails rather than being taken on the author's word.
_EXEMPTION_EVIDENCE: dict[tuple[type[ast.AST], str], str] = {
    (ast.IfExp, "test"): "None if geometry is None else geometry.shape",
}


def _worst_shape(shapes) -> _Shape:
    """``COMPUTED`` beats ``UNKNOWN`` beats ``NOT_COMPUTED``.

    A container with one definitely-computed element is definitely computed -- that is
    a conclusion, not a guess. One with an unrecognised element and nothing computed is
    unknown, because the unrecognised element could be either.
    """
    collected = list(shapes)
    if any(shape is _Shape.COMPUTED for shape in collected):
        return _Shape.COMPUTED
    if any(shape is _Shape.UNKNOWN for shape in collected):
        return _Shape.UNKNOWN
    return _Shape.NOT_COMPUTED


def _classify_expression(node: ast.AST) -> _Shape:
    """Whether ``node`` works a value out, reads one, or is a shape not recognised here.

    Every branch below names the shapes it decides. The terminal answer is ``UNKNOWN``
    and it is reached by falling out of every named branch, which is the D129 ruling in
    one line: only shapes the code explicitly recognises get a definite answer.
    """
    if isinstance(node, _COMPUTING_SHAPES):
        return _Shape.COMPUTED
    if isinstance(node, ast.BoolOp):
        # `a or b` SELECTS one of its operands; it does not work a new value out. The
        # first version classified it as computed and so read `fluid or state.fluid`
        # as a derived quantity -- a case fact turned into a rule fact by a fallback.
        return _worst_shape(_classify_expression(part) for part in node.values)
    if isinstance(node, ast.IfExp):
        # The TEST decides which branch is taken; it does not contribute to the value.
        # Counting it made `geometry=None if geometry is None else geometry.shape` a
        # computed value, because `is None` is an ast.Compare -- which would have
        # classified two genuine case facts as derived quantities.
        return _worst_shape(
            _classify_expression(part) for part in (node.body, node.orelse)
        )
    if isinstance(node, ast.NamedExpr):
        # `target` is always a Name, so visiting it cannot change an answer -- which is
        # why it is visited rather than exempted. An exemption that buys nothing is a
        # line in a list that later has to be defended (D131).
        return _worst_shape(
            _classify_expression(part) for part in (node.target, node.value)
        )
    if isinstance(node, ast.Starred):
        return _classify_expression(node.value)
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return _worst_shape(_classify_expression(part) for part in node.elts)
    if isinstance(node, ast.Dict):
        return _worst_shape(
            _classify_expression(part)
            for part in list(node.values) + [k for k in node.keys if k is not None]
        )
    if isinstance(node, ast.Attribute):
        # A read OF a read is a read; a read of a computation is not. Recursing into
        # `.value` makes that fall out, with no rule about which attributes are reads:
        # `state.mu_f_Pa_s` stays NOT_COMPUTED and `(a + b).real` does not.
        return _classify_expression(node.value)
    if isinstance(node, ast.Subscript):
        return _worst_shape(
            _classify_expression(part) for part in (node.value, node.slice)
        )
    if isinstance(node, ast.Slice):
        return _worst_shape(
            _classify_expression(part)
            for part in (node.lower, node.upper, node.step)
            if part is not None
        )
    if isinstance(node, ast.Lambda):
        # The body is not evaluated where the lambda is written, so this can only
        # OVER-report -- and over-reporting a callable as computed is the safe side of
        # the leaf-over-computing-child defect. No keyword in the universe is a lambda.
        return _classify_expression(node.body)
    if isinstance(node, ast.JoinedStr):
        return _worst_shape(_classify_expression(part) for part in node.values)
    if isinstance(node, ast.FormattedValue):
        return _worst_shape(
            _classify_expression(part)
            for part in (node.value, node.format_spec)
            if part is not None
        )
    if isinstance(node, _READING_SHAPES):
        return _Shape.NOT_COMPUTED
    return _Shape.UNKNOWN


#: **The binding contract.** The statement types this analysis resolves, as a literal
#: set, because the claim is exactly this set and nothing more.
#:
#: D126. Nine instruments on this gate in a row claimed a category and matched a form,
#: and every repair was a widening followed by another form: ``BLOCK`` covered seven
#: sites of eight, the message three names of four, the rule one file of two, the
#: matcher one call form of two, this derivation one binding form of two. The tenth
#: widening would have been ``ast.For``. It is not taken.
#:
#: Instead the claim narrows to what is written here, and **every delivery path outside
#: this set is reported UNMEASURED and fails** -- exactly as an unresolvable constructor
#: already does. A name bound by ``for``, by ``with ... as``, by an ``except`` handler
#: or by a comprehension is not "not derived"; it is unresolved, and the difference is
#: the whole of D126. That is what makes "unmeasured is not zero" load-bearing rather
#: than a phrase that fires only for mappings.
_BINDING_CONTRACT: tuple[type[ast.AST], ...] = (
    ast.Assign,
    ast.AnnAssign,
    ast.AugAssign,
    ast.NamedExpr,
)


def _contract_bindings(scope: ast.AST) -> tuple[set[str], set[str], set[str]]:
    """``(computed, bound)`` for the binding statements named in :data:`_BINDING_CONTRACT`.

    ``bound`` is every name those statements bind; ``computed`` is the subset bound to a
    worked-out value. A name in neither -- and not a parameter of the enclosing function
    -- was bound by something this contract does not cover, and the caller reports it
    UNMEASURED rather than reading it as a value the caller stated.

    The docstring this replaces said "ALL binding forms" over an enumeration of four.
    """
    computed: set[str] = set()
    bound: set[str] = set()
    unknown: set[str] = set()

    def bind(target: ast.AST, shape: _Shape) -> None:
        if isinstance(target, ast.Name):
            bound.add(target.id)
            if shape is _Shape.COMPUTED:
                computed.add(target.id)
            elif shape is _Shape.UNKNOWN:
                unknown.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                bind(element, shape)
        elif isinstance(target, ast.Starred):
            bind(target.value, shape)

    for node in ast.walk(scope):
        if not isinstance(node, _BINDING_CONTRACT):
            continue
        if isinstance(node, ast.Assign):
            for target in node.targets:
                bind(target, _classify_expression(node.value))
        elif isinstance(node, ast.AnnAssign):
            if node.value is not None:
                bind(node.target, _classify_expression(node.value))
        elif isinstance(node, ast.AugAssign):
            # `x += f()` and `x += 1` both work a value out.
            bind(node.target, _Shape.COMPUTED)
        elif isinstance(node, ast.NamedExpr):
            bind(node.target, _classify_expression(node.value))
    return computed, bound, unknown



def _module_level_names(tree: ast.Module) -> tuple[set[str], set[str], set[str]]:
    """``(computed, bound)`` at module scope, under the SAME binding contract.

    A keyword value can be a module-level constant -- ``gravity_m_s2=
    STANDARD_GRAVITY_M_S2`` -- which is neither a function-local binding nor a
    parameter. Reading those as unresolved would report every constant reference as
    unmeasured; reading them as automatically safe would exempt a module-level
    computation from the derivation. So module scope is resolved by the same contract:
    a constant bound to a literal is not derived, a module-level name bound to a
    worked-out value is, and an imported name is resolved and not derived.
    """
    computed, bound, unknown = _contract_bindings(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound.add(alias.asname or alias.name.split(".")[0])
    return computed, bound, unknown


def _parameters_of(scope: ast.AST) -> set[str]:
    """The enclosing function's parameters: names a caller states, not the code."""
    if not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return set()
    arguments = scope.args
    names = {
        a.arg
        for a in (
            list(arguments.posonlyargs)
            + list(arguments.args)
            + list(arguments.kwonlyargs)
        )
    }
    for extra in (arguments.vararg, arguments.kwarg):
        if extra is not None:
            names.add(extra.arg)
    return names


def _sole_binding_of(name: str, scope: ast.AST):
    """The one contract binding of ``name``, or ``None`` when there is not exactly one.

    D126/F-02. This was ``_last_binding_of`` and returned the FIRST binding ``ast.walk``
    happened to reach -- a helper named for the last, returning the first, which is the
    same defect as a docstring saying "ALL" over four forms. Measured: an ordinary
    mapping initialised empty and rebound before the call resolved to ``{}``,
    contributed no keys, and counted as MEASURED, so a form the analysis resolved
    *incorrectly* became a clean zero.

    ``ast.walk`` has no order that says which binding reaches a call, and deciding that
    needs control-flow reasoning this analysis does not do. So more than one binding is
    the unmeasured answer, and the caller fails on it.
    """
    found = []
    for node in ast.walk(scope):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            found.append(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name and node.value is not None:
                found.append(node.value)
    return found[0] if len(found) == 1 else None


def _parameter_names_by_function() -> dict[str, frozenset[str]]:
    """Every package function's parameter names, by function name.

    Used to decide whether a call site could be DELIVERING applicability parameters at
    all. Without that, an unreadable ``**mapping`` anywhere in the package -- a
    deprecation shim forwarding ``*args, **kwargs``, say -- would be reported as an
    unmeasured applicability delivery, and a report that cries about ten irrelevant
    sites is a report nobody reads. Derived from signatures, not from names.
    """
    out: dict[str, set[str]] = {}
    for path in _production_modules():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                arguments = node.args
                names = {
                    a.arg
                    for a in (
                        list(arguments.posonlyargs)
                        + list(arguments.args)
                        + list(arguments.kwonlyargs)
                    )
                }
                out.setdefault(node.name, set()).update(names)
    return {name: frozenset(params) for name, params in out.items()}


def _expanded_keywords(call: ast.Call, scope: ast.AST):
    """``(names, unmeasured)`` for the ``**mapping`` expansions at one call site.

    A call may pass its arguments through a mapping -- ``check(**y_kwargs)`` -- and the
    keys of that mapping are keyword arguments as surely as if they were written out.
    A mapping this scan can read is expanded; one it cannot is reported UNMEASURED, the
    same rule the constructor resolver uses, because a scan that cannot decide must say
    so rather than count zero.
    """
    names: set[str] = set()
    unmeasured: list[str] = []
    for keyword in call.keywords:
        if keyword.arg is not None:
            continue
        source = keyword.value
        if isinstance(source, ast.Name):
            resolved = _sole_binding_of(source.id, scope)
            if resolved is None:
                unmeasured.append('name bound more than once, or not by the contract')
                continue
            source = resolved
        if isinstance(source, ast.Dict):
            for key in source.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    names.add(key.value)
                else:
                    unmeasured.append("non-literal key")
        elif isinstance(source, ast.Call) and getattr(source.func, "id", "") == "dict":
            names.update(k.arg for k in source.keywords if k.arg is not None)
            if any(k.arg is None for k in source.keywords):
                unmeasured.append("nested expansion")
        else:
            unmeasured.append("unreadable mapping")
    return names, unmeasured


def _last_binding_of(name: str, scope: ast.AST):
    for node in ast.walk(scope):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            return node.value
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                return node.value
    return None


def _derived_quantities_in_production(with_unmeasured: bool = False):
    """Parameters of :meth:`Applicability.check` that production code **computes**.

    The classification test D118 asks for, and it is a derivation rather than a list of
    forbidden names -- a list is a blocklist in allowlist clothing, and this class has
    been closed by name four times already.

    A keyword argument counts as *computed* when its value works a value out, or is a
    local bound to one by any ordinary binding form, or arrives through a ``**mapping``
    whose keys this scan can read. That is deliberately narrower than "not a bare
    parameter": ``geometry=geometry.shape`` reads a field off an object the caller owns
    and stays a case fact, while ``liquid_reynolds=state.liquid_reynolds(...)`` and
    ``branch_value=y_here`` where ``y_here = shah_1987_Y(...)`` are quantities the code
    works out.

    **D123/F-03 widened the binding forms and added the unmeasured half.** Reading only
    ``ast.Assign`` meant an annotation defeated the guard outright, and the D120 control
    tested REMOVAL from the population rather than ADDITION outside it -- so it could
    only ever go red for a name already in the derived set, never for one that had never
    entered it. What a scan cannot read it now reports; what it can read has grown to
    the ordinary ways a value gets a name.
    """
    universe = {
        name for name in inspect.signature(Applicability.check).parameters
        if name != "self"
    }
    parameters_by_function = _parameter_names_by_function()
    derived: set[str] = set()
    unmeasured: list[str] = []
    for path in _production_modules():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover - a shipped module must parse
            continue
        module_computed, module_bound, module_unknown = _module_level_names(tree)
        for scope in ast.walk(tree):
            if not isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            computed_here, bound_here, unknown_here = _contract_bindings(scope)
            parameters_here = _parameters_of(scope)
            for node in ast.walk(scope):
                if not isinstance(node, ast.Call):
                    continue
                callee = node.func
                callee_name = (
                    callee.id if isinstance(callee, ast.Name)
                    else callee.attr if isinstance(callee, ast.Attribute)
                    else None
                )
                delivers = bool(
                    callee_name
                    and parameters_by_function.get(callee_name, frozenset()) & universe
                )
                if delivers:
                    expanded, could_not_read = _expanded_keywords(node, scope)
                    relative = path.relative_to(_SRC)
                    unmeasured.extend(
                        f"{relative.as_posix()}: {callee_name} ({u})"
                        for u in could_not_read
                    )
                    derived.update(expanded & universe)
                for keyword in node.keywords:
                    if keyword.arg is None or keyword.arg not in universe:
                        continue
                    value = keyword.value
                    relative = path.relative_to(_SRC)
                    shape = _classify_expression(value)
                    if shape is _Shape.COMPUTED:
                        derived.add(keyword.arg)
                    elif shape is _Shape.UNKNOWN:
                        # D129: the value is a shape this analysis does not recognise.
                        # Not "not derived" -- unrecognised, which is unmeasured.
                        unmeasured.append(
                            f"{relative.as_posix()}: {keyword.arg} "
                            f"(value shape {type(value).__name__} not recognised)"
                        )
                    elif isinstance(value, ast.Name):
                        if value.id in computed_here or value.id in module_computed:
                            derived.add(keyword.arg)
                        elif value.id in unknown_here or value.id in module_unknown:
                            unmeasured.append(
                                f"{relative.as_posix()}: {keyword.arg} "
                                f"(name '{value.id}' bound to an unrecognised shape)"
                            )
                        elif not (
                            value.id in bound_here
                            or value.id in parameters_here
                            or value.id in module_bound
                        ):
                            # Bound by something the contract does not cover -- a for
                            # target, a with-as, a comprehension. Not "not derived":
                            # unresolved, and D126 says those are the same failure.
                            unmeasured.append(
                                f"{relative.as_posix()}: {keyword.arg} "
                                f"(name '{value.id}' bound outside the contract)"
                            )
    if with_unmeasured:
        return frozenset(derived), unmeasured
    return frozenset(derived)


#: Parameters of ``check`` that this boundary can neither take from a caller nor supply
#: itself, so the axes depending on them are reported unevaluable. DERIVED, so a
#: quantity that becomes computed in production joins it without an edit here.
_DERIVED_BEYOND_THIS_BOUNDARY = _derived_quantities_in_production() - frozenset(
    {"fluid", "gravity_m_s2", "has_executable_form"}
)



#: Call sites where a ``**mapping`` cannot be read, acknowledged with the reason.
#:
#: D123/F-03. "Unmeasured is not zero" is only worth anything if a NEW unreadable site
#: fails, so the known ones are declared rather than tolerated in silence, and
#: ``test_d123_the_unmeasured_expansions_are_the_declared_ones`` fails in both
#: directions. Keyed by module and callee rather than by line number, which drifts.
#:
#: The single entry is the registry's own CHF function forwarding ``**kwargs`` into
#: ``shah_1987_critical_boiling_number``. It cannot deliver an applicability parameter
#: -- it is physics, not a ``check`` call -- but the relevance rule is derived from
#: SIGNATURES rather than from names, and that callee happens to take ``gravity_m_s2``.
#: Teaching the rule to recognise this one by name is the defect this whole return is
#: about, so it is declared instead.
_ACKNOWLEDGED_UNREADABLE_EXPANSIONS = frozenset({
    "registry/two_phase.py: shah_1987_critical_boiling_number "
    "(name bound more than once, or not by the contract)",
})


def test_d118_no_case_fact_is_a_derived_quantity():
    """**The classification witness: the allowlist's contents, not its shape.**

    D114 closed ``**case`` by construction and the construction was populated by hand.
    Nothing checked the hand, so ``branch_value``,
    ``branch_value_at_reference_gravity`` and ``liquid_reynolds`` sat inside the
    allowlist being described as "the correlating parameter this case produces" while
    the production path computed all three from mass flux, hydraulic diameter, quality
    and fluid state. A caller could hand S5 a straddling pair and choose the verdict --
    through a name the door was told to admit.

    So: no member of :data:`CASE_FACTS` may be a quantity production code derives. It
    fails on the day a derived quantity is ADDED to the allowlist rather than the day a
    reviewer notices, which is the difference between this and three controls on three
    names.
    """
    derived = _derived_quantities_in_production()
    assert derived, (
        "no derived quantity was found anywhere in production, so this proves nothing "
        "-- the derivation is broken, not the allowlist"
    )
    misclassified = sorted(ac.CASE_FACTS & derived)
    assert not misclassified, (
        f"these are declared case facts a caller may state, and production code "
        f"computes them: {misclassified}. A value the computation derives cannot also "
        "be a fact the caller states -- that is how a caller chooses the verdict."
    )


def test_d118_the_derivation_finds_the_three_names_and_spares_the_primitives():
    """The derivation's own control, in both directions.

    A classifier that flagged everything would satisfy the test above vacuously, and
    one that flagged nothing would satisfy it too. So: the three names D118 removed
    must be found, and the three primitives that remain must not be.
    """
    derived = _derived_quantities_in_production()
    for name in ("liquid_reynolds", "branch_value", "branch_value_at_reference_gravity"):
        assert name in derived, (
            f"{name} is computed in production and the derivation did not find it"
        )
    for name in ("composition", "geometry", "orientation"):
        assert name not in derived, (
            f"{name} was classified as derived; it is read off caller-owned hardware, "
            "and flagging it would empty the allowlist rather than correct it"
        )


@pytest.mark.parametrize(
    "name", sorted({"liquid_reynolds", "branch_value", "branch_value_at_reference_gravity"})
)
def test_d118_a_derived_quantity_is_refused_from_the_case_channel(name):
    """What a caller who passes one now gets, and that it says which mistake it is."""
    with pytest.raises(TypeError, match="not a case fact") as refusal:
        _assess_with(name, 1.0e6)
    assert "DERIVES from primitive physical state" in str(refusal.value)
    assert "unevaluable" in str(refusal.value)


def test_d118_the_branch_axis_is_reported_unevaluable_rather_than_skipped():
    """**The absence asymmetry, which is the half a removal alone would have left.**

    Measured before the repair: with ``min_liquid_reynolds`` declared and no value
    stated, ``check`` emitted ``REGIME``/``BLOCK``; with ``branch_threshold`` declared
    and no pair stated, the straddle test was skipped in silence and the leg came back
    ``eligible=True`` with no violation at all. One axis refused on absence, the other
    passed on it. Removing the three names without this would have converted a
    caller-set verdict into a silently unchecked axis, which is the worse of the two.
    """
    chf = ac.assess_leg("water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE)
    spec = ac.adopted_entry("chf").applicability_spec
    assert spec.branch_threshold is not None, "the adopted entry declares a threshold"

    unevaluable = _unevaluable(chf)
    assert [(v.axis, v.consequence) for v in unevaluable] == [
        (Axis.ORIENTATION, Consequence.BLOCK)
    ]
    assert "NOT CHECKED" in unevaluable[0].detail
    assert chf.eligible is False, (
        "an axis that could not be checked must not leave the leg reporting eligible; "
        "that is the collapse D75 and D90 exist to prevent, one level out"
    )

    # And the entry that declares no threshold does not acquire a phantom block.
    dp = ac.assess_leg(
        "water", "dp", gravity_m_s2=_REFERENCE_G, composition="two_component",
        **_FULL_CASE,
    )
    assert ac.adopted_entry("dp").applicability_spec.branch_threshold is None
    assert not [
        v for v in _unevaluable(dp)
        if "branch threshold" in v.detail
    ], "a correlation declaring no threshold must not be blocked on one"


def test_d118_a_reader_can_tell_not_checked_from_checked_and_failed():
    """**Which of the three states a record is in, as data rather than as prose.**

    ``as_record`` carried only the violation *detail strings*, so the distinction lived
    in wording a consumer would have to read. It now carries ``unevaluable_axes``, and
    the three states are:

    * ``eligible`` true -- every declared axis was checked and passed;
    * ``eligible`` false with ``unevaluable_axes`` empty -- checked and failed;
    * ``eligible`` false with ``unevaluable_axes`` non-empty -- an axis was never
      evaluated, and the record is not a finding about the case.
    """
    at_1g = ac.assess_leg("water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE)
    micro = ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)

    record_1g = at_1g.as_record()
    assert record_1g["unevaluable_axes"] == ("orientation",)
    assert record_1g["eligible"] is False

    record_micro = micro.as_record()
    assert record_micro["unevaluable_axes"] == ("orientation",)
    assert len(record_micro["violations"]) > len(record_1g["violations"]), (
        "microgravity adds a CHECKED finding on top of the unevaluable axis, and the "
        "record must show both rather than collapsing them"
    )
    # The distinction is derived from the consequence, not from the wording.
    assert set(record_micro["unevaluable_axes"]) == {
        v.axis.value for v in micro.violations if v.consequence is Consequence.BLOCK
    }


def test_d118_the_paired_control_a_genuine_case_fact_still_passes():
    """"Refuses everything" is not the ask. Each surviving member still works, and one
    of them still moves an outcome the way a case fact should."""
    for name in sorted(ac.CASE_FACTS):
        ac.assess_leg("water", "chf", gravity_m_s2=_REFERENCE_G, **{
            **_FULL_CASE, name: _FULL_CASE.get(name, "round_tube"
                                               if name == "geometry" else "single_component"
                                               if name == "composition"
                                               else "vertical_upflow"),
        })

    # composition is declared by the dp correlation, so stating it removes a BLOCK --
    # a caller-stated primitive still changing the outcome, which is what a case fact is.
    without = ac.assess_leg("water", "dp", gravity_m_s2=_REFERENCE_G, **_FULL_CASE)
    with_it = ac.assess_leg(
        "water", "dp", gravity_m_s2=_REFERENCE_G, composition="two_component",
        **_FULL_CASE,
    )
    blocked_axes_without = {v.axis for v in _unevaluable(without)}
    blocked_axes_with = {v.axis for v in _unevaluable(with_it)}
    assert Axis.COMPOSITION in blocked_axes_without
    assert Axis.COMPOSITION not in blocked_axes_with, (
        "stating a genuine case fact must still change what the mechanism concludes"
    )


# ======================================================================================
# D119 — a BLOCK that is a conclusion, and a message entitled to its category
# ======================================================================================


def test_d119_a_block_that_is_a_conclusion_is_not_reported_as_unevaluable():
    """**C-01, red at 4433baa on this exact record.**

    ``unevaluable_axes`` derived from ``Consequence.BLOCK``, and ``BLOCK`` means two
    things: seven of its eight sites fire because the case states nothing on the axis,
    and the eighth fires because the entry declares it requires an executable form and
    has none. That axis IS evaluated -- ``has_executable_form`` is stated by the
    computation and is never ``None`` -- and the entry failed it.

    So the record announced *"at least one declared axis was never evaluated"* about the
    one record whose whole purpose is to show the entry's executable form MOVING the
    outcome. This is the D114 paired control, read through the field D118 added.
    """
    entries = _entry_with_no_reachable_executable_form()
    leg = ac._assess_leg_against_a_supplied_registry(
        entries, "water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE
    )
    record = leg.as_record()

    provenance = [v for v in leg.violations if v.axis is Axis.PROVENANCE]
    assert provenance, "the control must produce the provenance block it is built on"
    assert provenance[0].consequence is Consequence.BLOCK
    assert provenance[0].cause is Cause.EVALUATED_AND_FAILED, (
        "the entry was asked for an executable form and did not have one; that axis "
        "was evaluated"
    )
    assert "provenance" not in record["unevaluable_axes"], (
        "a conclusion about the entry is being reported as the absence of one"
    )
    # The branch axis on the same record genuinely was not evaluated, so the field is
    # not simply empty -- it is discriminating.
    assert record["unevaluable_axes"] == ("orientation",)



# ======================================================================================
# D123 — resolving what a name is BOUND to, so a rule governs a category and not a
# spelling. Shared by the cause rule (F-02) and the derived-quantity rule (F-03).
# ======================================================================================


class _Unmeasured(NamedTuple):
    """A construction the analysis could not resolve. **Not the same as absent.**

    D123's shape, three times over: an instrument measured a form and claimed a
    category. The half that outlives the next spelling is not a longer list of forms --
    it is that a scan which cannot decide says so. A zero that means "none" and a zero
    that means "I could not look" are different numbers, and every rule below fails
    loudly on the second.
    """

    path: pathlib.Path
    lineno: int
    reason: str


def _package_root() -> pathlib.Path:
    return pathlib.Path(_applicability.__file__).parents[1]


def _package_modules() -> list[pathlib.Path]:
    return sorted(
        p for p in _package_root().rglob("*.py") if "__pycache__" not in p.parts
    )


def _bindings_in(tree: ast.Module) -> tuple[dict[str, str], dict[str, str]]:
    """What each local name is bound to: ``(names, module_aliases)``.

    ``names`` maps a local name to a dotted target -- ``Violation`` however it was
    spelled at the import, and through any number of local rebindings. ``module_aliases``
    maps a local name to the module it refers to, so ``ap.Violation`` resolves as well as
    a bare name.

    Follows: ``from X import Violation``, ``... as _V``, ``import X.Y as ap``,
    ``from . import applicability``, and chained local aliases ``V = _V``.
    """
    names: dict[str, str] = {}
    modules: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            base = (node.module or "").split(".")[-1]
            for alias in node.names:
                local = alias.asname or alias.name
                if alias.name and alias.name[:1].isupper():
                    names[local] = alias.name          # a class, however spelled
                else:
                    modules[local] = alias.name or base  # `from . import applicability`
        elif isinstance(node, ast.Import):
            for alias in node.names:
                modules[alias.asname or alias.name.split(".")[0]] = (
                    alias.name.split(".")[-1]
                )
    # A class defined HERE binds its own name -- applicability.py does not import
    # Violation, it declares it, and the first version of this resolver could not see
    # the nineteen sites in the file the rule was originally written for.
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            names[node.name] = node.name

    # Local rebinding, repeated so `V = _V = Violation` resolves whatever the order.
    # D129/F-01: ANNOTATED rebinding too. `_v: type = Violation` is an AnnAssign whose
    # value is an ast.Name -- inside a contract node type, and still invisible, because
    # the branch recorded a name only when the value was a call. The alias then hit the
    # capitalisation branch of the resolver and was dropped as not-a-class.
    for _ in range(3):
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name):
                targets = [t for t in node.targets if isinstance(t, ast.Name)]
                value = node.value
            elif (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and isinstance(node.value, ast.Name)
            ):
                targets = [node.target]
                value = node.value
            else:
                continue
            source = names.get(value.id)
            if source is None:
                continue
            for target in targets:
                names.setdefault(target.id, source)
    return names, modules


def _names_bound_to_values(tree: ast.Module) -> set[str]:
    """Every name this module binds to a runtime value, plus parameters.

    A called name that is bound HERE is a runtime callable and deliberately not a class
    construction; a called name bound NOWHERE this scan can see is the unknown answer.
    Before D129 both were "not a class", which is how an annotated alias disappeared.
    """
    bound, _computed, _unknown = set(), set(), set()
    computed, contract_bound, unknown = _contract_bindings(tree)
    bound |= contract_bound
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            bound.add(node.name)
            bound |= _parameters_of(node)
        elif isinstance(node, ast.ClassDef):
            bound.add(node.name)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            if isinstance(node.target, ast.Name):
                bound.add(node.target.id)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            bound.add(node.name)
        elif isinstance(node, ast.withitem) and isinstance(node.optional_vars, ast.Name):
            bound.add(node.optional_vars.id)
        elif isinstance(node, ast.comprehension) and isinstance(node.target, ast.Name):
            bound.add(node.target.id)
    return bound


def _resolve_callee(
    call: ast.Call,
    names: dict[str, str],
    modules: dict[str, str],
    local_defs: set[str],
) -> str | None:
    """What ``call`` constructs, or ``None`` when the analysis cannot say.

    ``None`` is the UNMEASURED answer and callers must treat it as such rather than as
    "not a Violation" -- that conflation is F-02 exactly.

    **The bound, stated rather than left for the next return to find.** A name bound
    to an *expression* -- a callable parameter, a computed local -- is read as a
    runtime value and not as a construction this scan can attribute; only a callee the
    scan cannot even name comes back UNMEASURED. So an indirect ``getattr`` lookup and
    a call on a call are reported, while ``f(...)`` for a callable parameter is not.
    Imported aliases, local aliases, locally defined classes and module attributes are
    resolved outright, which is the population the four controls below exercise.
    """
    func = call.func
    if isinstance(func, ast.Name):
        if func.id in names:
            return names[func.id]
        if func.id in modules:
            return "<not-a-class>"          # a module used as a callable: not one
        if func.id in dir(builtins):
            return "<not-a-class>"          # a builtin
        if func.id in local_defs:
            return "<not-a-class>"          # bound here to a runtime value
        return None                         # bound by nothing this scan can see
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Name) and func.value.id in modules:
            return func.attr                # module.Something(...)
        if func.attr.startswith("_"):
            return "<not-a-class>"          # a dunder or private method: __setattr__,
            #                                 super().__init__, object.__setattr__
        if func.attr[:1].isupper():
            return None                     # class-shaped attribute, base unidentified
        if func.attr[:1].islower():
            return "<not-a-class>"          # a method call on an object
        return None
    return None                             # the terminal answer is UNKNOWN


def _local_definitions(tree: ast.Module) -> set[str]:
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }

def _scan_violation_constructions(source: str, path: pathlib.Path):
    """``(sites, unmeasured)`` for one module, by CONSTRUCTOR IDENTITY not by spelling.

    D123/F-02. The D120 version matched ``ast.Name`` whose ``id`` was the string
    ``"Violation"``. An aliased import -- ``from .registry.applicability import
    Violation as _V`` -- produced a twenty-first construction site that the rule, the
    suite and the linter all passed, and the row asserting "the bound is real" inferred
    a whole-population claim from two syntax counts while its only control planted a
    form it already saw.

    So the name is resolved to what it is BOUND to, through imported aliases, module
    attribute access and local rebinding. And a construction that cannot be resolved --
    ``getattr(mod, "Violation")(...)``, a call on a call -- is returned as UNMEASURED
    rather than counted as zero, because a scan that cannot decide must say so.
    """
    tree = ast.parse(source)
    names, modules = _bindings_in(tree)
    defined = _names_bound_to_values(tree)

    sites = []
    unmeasured = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = _resolve_callee(node, names, modules, defined)
        if target is None:
            unmeasured.append(
                _Unmeasured(path, node.lineno, ast.dump(node.func)[:60])
            )
            continue
        if target != "Violation":
            continue
        consequence = node.args[1] if len(node.args) > 1 else None
        name = consequence.attr if isinstance(consequence, ast.Attribute) else "?"
        states = any(keyword.arg == "cause" for keyword in node.keywords)
        sites.append((path, node.lineno, name, states))
    return sites, unmeasured


def _violation_sites() -> list[tuple[pathlib.Path, int, str, bool]]:
    """Every ``Violation`` construction in the package. DERIVED from the package.

    D120: the D119 version of this read one file -- ``applicability.__file__`` -- and
    the package has two that construct violations. D123: it also matched a spelling
    rather than the constructor, so an alias was invisible to it.

    Returns ``(path, lineno, consequence, states_a_cause)`` per site.
    """
    root = _package_root()
    sites = []
    for path in _package_modules():
        found, _ = _scan_violation_constructions(
            path.read_text(encoding="utf-8"), path.relative_to(root)
        )
        sites.extend(found)
    return sites


def _violation_scan_unmeasured() -> list[_Unmeasured]:
    root = _package_root()
    out = []
    for path in _package_modules():
        _, unmeasured = _scan_violation_constructions(
            path.read_text(encoding="utf-8"), path.relative_to(root)
        )
        out.extend(unmeasured)
    return out


def test_d120_every_violation_site_states_whether_its_axis_was_evaluated():
    """**The rule, over every file that raises one -- not one module by name.**

    Widened from ``BLOCK`` to every :class:`Violation` because flipping the default
    required it: eleven ``DE_RANK``/``REJECT`` sites were relying on the old default
    being ``EVALUATED_AND_FAILED``, which was correct for them, so flipping it without
    making them explicit would have silently misclassified eleven correct sites in order
    to fix a default nothing used. The rule now governs the category it is about --
    violations -- rather than the subset the last finding arrived through.
    """
    sites = _violation_sites()

    # Both-directions control, the shape the D118 classification witness has: a scan
    # that has stopped finding its population must fail loudly rather than report a
    # clean sweep of nothing.
    assert len(sites) >= 20, (
        f"the scan found only {len(sites)} Violation sites; it was built against 20 in "
        "2 files. Either the population moved or the derivation stopped reading it -- "
        "re-derive it rather than lowering this number"
    )
    files = {path for path, _, _, _ in sites}
    assert len(files) >= 2, (
        f"every Violation site the scan can see is in {files}. The D119 rule read one "
        "file and missed the second; a scan that has narrowed back to one file is that "
        "defect returning, not a simplification"
    )
    assert any("registry" in path.parts for path, _, _, _ in sites)

    silent = [
        f"{path}:{lineno} ({consequence})"
        for path, lineno, consequence, states in sites
        if not states
    ]
    assert not silent, (
        "these Violation sites do not say whether their axis was evaluated, so the "
        f"record derives it from a default the author never chose: {silent}"
    )


def test_d123_a_construction_the_scan_cannot_resolve_is_reported_not_absorbed():
    """**UNMEASURED is not zero, and this is the half that outlives the next spelling.**

    A longer list of syntaxes is always one syntax short -- that is F-02, F-03 and the
    C-04 matcher, three instruments in one return. What generalises is that the scan
    reports what it could not decide, so a construction it cannot resolve fails the rule
    instead of passing it by being invisible.
    """
    unmeasured = _violation_scan_unmeasured()
    assert not unmeasured, (
        "these constructions could not be resolved to a class, so the cause rule "
        "cannot say whether they are Violation sites: "
        + "; ".join(f"{u.path}:{u.lineno}" for u in unmeasured)
    )


def test_d120_the_default_understates_rather_than_asserting_an_unchecked_finding():
    """**The default points where the population does, and D119's reasoning was wrong.**

    D119 defaulted to ``EVALUATED_AND_FAILED``, reasoning that the failure being
    repaired is "a conclusion presented as an absence, never the reverse". That
    generalised from the one site D119 repaired to a population running 8:1 the other
    way, which is the same shape as the defect it guarded against -- and it was the
    wrong half to be safe on. An absence misreported as a conclusion is a record
    asserting a case failed an axis nothing checked: a claim with no basis. A conclusion
    misreported as an absence only understates.
    """
    assert (
        dataclasses.fields(_applicability.Violation)[-1].default is Cause.NOT_EVALUATED
    ), "the default must be the understating one"

    # The population it is defaulting for, measured rather than remembered.
    block_causes = [
        keyword.value.attr
        for path, lineno, consequence, _ in _violation_sites()
        if consequence == "BLOCK"
        for keyword in _cause_keywords(path, lineno)
    ]
    assert block_causes, "no BLOCK site states a cause, so this measures nothing"
    assert block_causes.count("NOT_EVALUATED") > block_causes.count(
        "EVALUATED_AND_FAILED"
    ), (
        "the BLOCK population no longer runs toward NOT_EVALUATED, so the reasoning "
        "for this default should be re-derived rather than inherited"
    )


def _cause_keywords(path, lineno):
    """The ``cause=`` keyword node at one site, so the default's population can be
    measured from the sites themselves rather than from a remembered ratio."""
    package_root = pathlib.Path(_applicability.__file__).parents[1]
    for node in ast.walk(ast.parse((package_root / path).read_text(encoding="utf-8"))):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "Violation"
            and node.lineno == lineno
        ):
            return [k for k in node.keywords if k.arg == "cause"]
    return []


def test_d119_the_record_distinguishes_all_four_states():
    """Passed, checked-and-failed, absent-statement, entry-conclusion -- as data."""
    horizontal = {"geometry": "round_tube", "orientation": "horizontal"}

    passed = ac.assess_leg(
        "water", "dp", gravity_m_s2=_REFERENCE_G, composition="two_component",
        **horizontal,
    ).as_record()
    assert passed["eligible"] is True and passed["violations"] == ()
    assert passed["unevaluable_axes"] == ()

    checked_and_failed = ac.assess_leg(
        "water", "dp", gravity_m_s2=_REFERENCE_G, composition="two_component",
        **_FULL_CASE,
    ).as_record()
    assert checked_and_failed["eligible"] is False
    assert checked_and_failed["violations"]
    assert checked_and_failed["unevaluable_axes"] == ()

    absent_statement = ac.assess_leg(
        "water", "dp", gravity_m_s2=_REFERENCE_G, **horizontal
    ).as_record()
    assert absent_statement["unevaluable_axes"] == ("composition",)

    entry_conclusion = ac._assess_leg_against_a_supplied_registry(
        _entry_with_no_reachable_executable_form(), "water", "chf",
        gravity_m_s2=_REFERENCE_G, **_FULL_CASE,
    ).as_record()
    assert "provenance" not in entry_conclusion["unevaluable_axes"]
    assert any("executable form" in d for d in entry_conclusion["violations"]), (
        "the conclusion must still be REPORTED -- it is a finding, not a silence"
    )


def test_d119_the_declared_derived_quantities_match_what_production_computes():
    """**C-02: the runtime's claim is certified against production, both directions.**

    The refusal names a category -- *this is a quantity the production path derives* --
    and before D119 nothing entitled it to: the test was membership in the ``check``
    signature, so a parameter nothing computes would have been told it was derived from
    mass flux. The module now declares the category and this certifies the declaration,
    so the runtime does not have to parse its own package in order to be honest.
    """
    computed = _derived_quantities_in_production() - _STATED_BY_THE_COMPUTATION
    assert ac.UNEVALUABLE_AT_THIS_BOUNDARY == computed, (
        "the declared derived quantities and what production actually computes have "
        f"drifted: declared {sorted(ac.UNEVALUABLE_AT_THIS_BOUNDARY)}, computed "
        f"{sorted(computed)}"
    )
    assert not (ac.UNEVALUABLE_AT_THIS_BOUNDARY & ac.CASE_FACTS)


def test_d119_a_parameter_that_is_not_derived_gets_a_refusal_that_claims_nothing():
    """The message must not name a category it cannot support."""
    with pytest.raises(TypeError) as refusal:
        ac.assess_leg(
            "water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE,
            mounting_bracket_colour="red",
        )
    text = str(refusal.value)
    assert "not a case fact" in text and "admits only" in text
    assert "DERIVES from primitive physical state" not in text, (
        "the refusal is asserting a property of this keyword that nothing established"
    )


@pytest.mark.parametrize(
    "name",
    sorted({"liquid_reynolds", "branch_value", "branch_value_at_reference_gravity"}),
)
def test_d119_the_three_category_refusal_survives_for_the_real_three(name):
    """C-02's constraint: the entitled message must still be given where it is true."""
    with pytest.raises(TypeError) as refusal:
        _assess_with(name, 1.0e6)
    assert "DERIVES from primitive physical state" in str(refusal.value)
    assert "unevaluable" in str(refusal.value)


# ======================================================================================
# D123 — three instruments that matched a form and claimed a category
# ======================================================================================


def test_d123_f01_a_mixed_cause_axis_is_reconstructable_from_the_record_alone():
    """**F-01, red at 312bfdd. The record is what S6 consumes.**

    The shipped microgravity CHF leg carries two ORIENTATION violations with opposite
    causes: a de-rank that is a finding, and a block that is the absence of one.
    ``unevaluable_axes`` says ``('orientation',)`` and ``violations`` is a tuple of bare
    strings, so a consumer could not tell which statement was which without parsing
    prose or keeping the pre-serialisation object. That is D119's conclusion-versus-
    absence ambiguity re-created at the hand-off, one layer out -- and carrying both
    kinds on ONE axis is exactly what makes an axis-name tuple ambiguous.
    """
    leg = ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    record = leg.as_record()

    on_orientation = [
        entry for entry in record["violation_records"]
        if entry["axis"] == Axis.ORIENTATION.value
    ]
    assert len(on_orientation) == 2, (
        "this record is the witness's whole point: two statements on one axis"
    )
    causes = {entry["cause"] for entry in on_orientation}
    assert causes == {
        Cause.EVALUATED_AND_FAILED.value,
        Cause.NOT_EVALUATED.value,
    }, "the two statements must be distinguishable, and on this record they differ"

    # Reconstructed from the record ALONE -- no object, no prose.
    finding = [e for e in on_orientation if e["cause"] == Cause.EVALUATED_AND_FAILED.value]
    absence = [e for e in on_orientation if e["cause"] == Cause.NOT_EVALUATED.value]
    assert len(finding) == 1 and len(absence) == 1
    assert finding[0]["consequence"] == Consequence.DE_RANK.value
    assert absence[0]["consequence"] == Consequence.BLOCK.value


def test_d123_f01_the_existing_violations_key_is_unchanged_and_parallel():
    """Additive, as ruled: S6 keeps consuming what it consumes.

    ``violations`` stays a tuple of the same detail strings in the same order, and the
    typed list is a parallel of it -- so a consumer can zip them, and neither can be
    the reason the other is wrong.
    """
    for leg in (
        ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE),
        ac.assess_leg("water", "dp", gravity_m_s2=_REFERENCE_G, **_FULL_CASE),
    ):
        record = leg.as_record()
        assert record["violations"] == tuple(v.detail for v in leg.violations)
        assert all(isinstance(v, str) for v in record["violations"])
        assert [e["detail"] for e in record["violation_records"]] == list(
            record["violations"]
        )
        # unevaluable_axes is REDUCED from the typed list rather than recomputed from
        # the object, so the two projections cannot disagree about one record.
        assert record["unevaluable_axes"] == tuple(
            e["axis"] for e in record["violation_records"]
            if e["cause"] == Cause.NOT_EVALUATED.value
        )


_ALIAS_FORMS = {
    "imported alias": (
        "from orbital_thermal.registry.applicability import Violation as _V\n"
        "def f():\n"
        "    return _V(Axis.REGIME, Consequence.BLOCK, 'silent')\n"
    ),
    "local alias": (
        "from orbital_thermal.registry.applicability import Violation\n"
        "V = Violation\n"
        "def f():\n"
        "    return V(Axis.REGIME, Consequence.BLOCK, 'silent')\n"
    ),
    "attribute access": (
        "from orbital_thermal.registry import applicability as ap\n"
        "def f():\n"
        "    return ap.Violation(Axis.REGIME, Consequence.BLOCK, 'silent')\n"
    ),
}


@pytest.mark.parametrize("form", sorted(_ALIAS_FORMS))
def test_d123_f02_every_alias_form_is_seen_as_a_construction(form):
    """**F-02: constructor identity, not the spelling of a call target.**

    The D120 rule matched ``ast.Name`` whose id was the string ``"Violation"``. An
    aliased import produced a twenty-first site that the rule, the suite and ruff all
    passed, and its only control planted the attribute form -- the one form it already
    saw. Each of the four forms the ruling names is planted here; three resolve, and
    the fourth is below.
    """
    sites, unmeasured = _scan_violation_constructions(
        _ALIAS_FORMS[form], pathlib.Path("planted.py")
    )
    assert not unmeasured, f"{form} should resolve, not come back unmeasured"
    assert len(sites) == 1, f"the {form} construction was not seen at all"
    assert sites[0][2] == "BLOCK" and sites[0][3] is False, (
        "the planted site is silent on cause and must be reported as such"
    )


def test_d123_f02_an_indirect_lookup_is_unmeasured_not_absent():
    """The fourth form, and the one that cannot be resolved: it must SAY so.

    A longer list of syntaxes is always one syntax short. What generalises is that a
    scan which cannot decide reports it, so the construction fails the rule rather than
    passing by being invisible.
    """
    source = (
        "from orbital_thermal.registry import applicability as ap\n"
        "def f():\n"
        "    return getattr(ap, 'Violation')(Axis.REGIME, Consequence.BLOCK, 'x')\n"
    )
    sites, unmeasured = _scan_violation_constructions(source, pathlib.Path("planted.py"))
    assert not sites
    assert unmeasured, (
        "an indirect lookup resolved to nothing and was counted as zero, which is the "
        "conflation F-02 is about"
    )
    assert unmeasured[0].lineno == 3


def test_d123_f02_a_resolvable_non_violation_call_is_neither_site_nor_unmeasured():
    """The control against the other failure: a scan that reports everything.

    An ordinary call must be neither a site nor unmeasured, or "nothing unmeasured"
    becomes unachievable and the signal is worthless.
    """
    source = (
        "import math\n"
        "def f(callback):\n"
        "    total = math.sqrt(4.0)\n"
        "    return callback(total)\n"
    )
    sites, unmeasured = _scan_violation_constructions(source, pathlib.Path("planted.py"))
    assert not sites and not unmeasured


_BINDING_FORMS = {
    "plain assignment": "    _q = mass_flux * 2.0\n",
    "annotated assignment": "    _q: float = mass_flux * 2.0\n",
    "tuple unpacking": "    _q, _other = compute(mass_flux)\n",
    "augmented assignment": "    _q = 1.0\n    _q += mass_flux\n",
    "walrus": "    print(_q := mass_flux * 2.0)\n",
}


@pytest.mark.parametrize("form", sorted(_BINDING_FORMS))
def test_d123_f03_a_derived_value_is_found_in_every_form_the_contract_names(form):
    """**F-03: a type annotation was enough to defeat the guard.**

    ``_bo = G / (D * 1000)`` was found; ``_bo: float = G / (D * 1000)`` was not. Same
    value, same call, same everything -- and a new derived parameter admitted to
    ``CASE_FACTS`` passed the classification witness, the S5-1 witness and the D114
    accounting together, because all three consume this one derivation.

    **The control introduces a parameter the suite has never seen.** Replaying
    ``liquid_reynolds``, ``branch_value`` and ``branch_value_at_reference_gravity``
    cannot detect this class: those names are already in the derived set, so a witness
    built on them can only ever go red for their REMOVAL, never for an ADDITION outside
    it. That asymmetry is what let this through.
    """
    source = "def producer(mass_flux):\n" + _BINDING_FORMS[form] + "    return _q\n"
    scope = next(
        node for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef)
    )
    computed, _bound, _unknown = _contract_bindings(scope)
    assert "_q" in computed, (
        f"a value bound by {form} is not seen as computed, so a keyword carrying it "
        "would be read as a caller's own statement"
    )


def test_d123_f03_a_previously_unknown_derived_parameter_is_found():
    """The end-to-end control, on a name that exists nowhere in the package.

    Not a replay of the three: a parameter the suite has never seen, supplied from an
    annotated binding -- the exact form and the exact scenario that passed at 312bfdd.
    """
    source = (
        "def produce(mass_flux_kg_m2s, geometry):\n"
        "    _bo: float = mass_flux_kg_m2s / (geometry.hydraulic_diameter_m * 1000.0)\n"
        "    return check(boiling_number=_bo, gravity_m_s2=9.81)\n"
    )
    scope = next(
        node for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef)
    )
    computed, _bound, _unknown = _contract_bindings(scope)
    assert "_bo" in computed

    call = next(
        node for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "check"
    )
    supplied = {
        keyword.arg for keyword in call.keywords
        if isinstance(keyword.value, ast.Name) and keyword.value.id in computed
    }
    assert "boiling_number" in supplied, (
        "a derived quantity supplied through an annotated binding is invisible, which "
        "is enough to admit it to CASE_FACTS with every witness green"
    )


def test_d123_f03_a_readable_mapping_expansion_delivers_its_keys():
    """``check(**mapping)`` carries keyword arguments as surely as writing them out."""
    source = (
        "def produce(g):\n"
        "    kw = dict(gravity_m_s2=g * 2.0, geometry='round_tube')\n"
        "    return check(**kw)\n"
    )
    tree = ast.parse(source)
    scope = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    call = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "check"
    )
    names, unmeasured = _expanded_keywords(call, scope)
    assert names == {"gravity_m_s2", "geometry"} and not unmeasured


def test_d123_the_unmeasured_expansions_are_the_declared_ones():
    """Unmeasured is not zero, and it is not a licence either.

    A ``**mapping`` the scan cannot read is reported. The ones that exist are declared
    with their reason so a NEW one fails, in both directions -- the same discipline
    ``UNEVALUABLE_AT_THIS_BOUNDARY`` is held to.
    """
    _, unmeasured = _derived_quantities_in_production(with_unmeasured=True)
    assert set(unmeasured) == _ACKNOWLEDGED_UNREADABLE_EXPANSIONS, (
        "the unreadable mapping expansions have moved: found "
        f"{sorted(set(unmeasured))}, declared "
        f"{sorted(_ACKNOWLEDGED_UNREADABLE_EXPANSIONS)}"
    )


# ======================================================================================
# D126 — a bounded syntax contract, and everything outside it reported
# ======================================================================================


def test_d126_the_contract_is_a_literal_set_and_the_claim_matches_it():
    """**The claim stops being a category.**

    Nine instruments on this gate claimed coverage of a category and matched a form,
    and each repair was a widening followed by another form. The tenth widening would
    have been ``ast.For``; it is not taken. What is asserted instead is that the
    contract is written down as a literal set, that the docstring states it rather than
    claiming "all", and that the set is what the resolver actually uses.
    """
    assert set(_BINDING_CONTRACT) == {
        ast.Assign,
        ast.AnnAssign,
        ast.AugAssign,
        ast.NamedExpr,
    }
    documentation = (_contract_bindings.__doc__ or "") + (
        _derived_quantities_in_production.__doc__ or ""
    )
    # A QUOTED phrase is a citation of a claim, not a claim -- both docstrings record
    # what they replaced, and a check that cannot tell the two apart fires on the text
    # that states the rule. That is the self-referential defect this gate has counted
    # repeatedly, so quoted spans are removed before the claim is read.
    documentation = re.sub(r'"[^"]*"', " ", documentation)
    for overclaim in ("ALL binding forms", "all of them bind", "every binding form"):
        assert overclaim not in documentation, (
            f"the analysis claims {overclaim!r} over an enumeration of "
            f"{len(_BINDING_CONTRACT)}"
        )
    assert "ast.For" not in ast.unparse(
        ast.parse(inspect.getsource(_contract_bindings))
    ), "ast.For is outside the contract; a name it binds must be UNMEASURED, not read"


def test_d126_f03_a_name_bound_outside_the_contract_is_unmeasured_not_undetected():
    """**The outside-the-contract control, and it is the point of the ruling.**

    A ``for`` target is not in the contract. The old analysis read a keyword carrying
    one as "not derived" -- a clean zero -- so a derived quantity admitted to
    ``CASE_FACTS`` passed every witness. Under D126 it is UNRESOLVED, which fails.

    This is the control that fails when someone adds a binder and forgets the contract,
    which is why it is not a replay of the four forms already listed.
    """
    source = (
        "def produce(mass_flux, geometry):\n"
        "    for _bo in [mass_flux / (geometry.d * 1000.0)]:\n"
        "        pass\n"
        "    return check(boiling_number=_bo)\n"
    )
    scope = next(
        node for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef)
    )
    computed, bound, _unknown = _contract_bindings(scope)
    assert "_bo" not in computed and "_bo" not in bound, (
        "a for target is outside the contract and must not be resolved by it"
    )
    assert "_bo" not in _parameters_of(scope), "nor is it something a caller stated"
    # So the derivation has no basis to call it either derived or not: unmeasured.


def test_d126_f02_a_rebound_mapping_is_unmeasured_rather_than_read_as_empty():
    """**F-02: a helper named for the last binding returned the first.**

    ``_extra = {}`` then ``_extra = {...}`` resolved to the empty literal, contributed
    no keys and counted as MEASURED -- a form the analysis resolved *incorrectly*
    becoming a clean zero, which is the unmeasured policy broken by the repair that
    introduced it. ``ast.walk`` has no order that decides which binding reaches a call,
    so more than one binding is the unmeasured answer.
    """
    rebound = (
        "def produce(mass_flux):\n"
        "    _extra = {}\n"
        "    _extra = {'boiling_number': mass_flux * 2.0}\n"
        "    return check(**_extra)\n"
    )
    tree = ast.parse(rebound)
    scope = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    assert _sole_binding_of("_extra", scope) is None, (
        "two bindings must not resolve to whichever one the walk reached first"
    )
    call = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "check"
    )
    names, unmeasured = _expanded_keywords(call, scope)
    assert not names and unmeasured, "a rebound mapping must be reported, not read"

    # And the control in the other direction: bound once, it still resolves.
    once = (
        "def produce(mass_flux):\n"
        "    _extra = {'boiling_number': mass_flux * 2.0}\n"
        "    return check(**_extra)\n"
    )
    tree = ast.parse(once)
    scope = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    call = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "check"
    )
    names, unmeasured = _expanded_keywords(call, scope)
    assert names == {"boiling_number"} and not unmeasured


def test_d126_the_sole_binding_helper_is_named_for_what_it_does():
    """A helper named ``_last_binding_of`` that returned the first is the same defect
    as a docstring saying "ALL" over four forms, one level down."""
    assert "_last_binding_of" not in inspect.getsource(_expanded_keywords)
    assert _sole_binding_of.__name__ == "_sole_binding_of"


def test_d126_a_module_level_constant_is_resolved_by_the_same_contract():
    """The other direction: the contract must not report ordinary references.

    ``gravity_m_s2=STANDARD_GRAVITY_M_S2`` is neither a local binding nor a parameter.
    Reporting it unmeasured would drown the signal; exempting module scope would let a
    module-level computation through. Module scope is resolved by the same four
    binders, so a literal constant is resolved and a computed one is derived.
    """
    tree = ast.parse(
        "STANDARD = 9.80665\n"
        "DERIVED = compute() * 2\n"
        "def produce():\n"
        "    return check(gravity_m_s2=STANDARD)\n"
    )
    computed, bound, _unknown = _module_level_names(tree)
    assert "STANDARD" in bound and "STANDARD" not in computed
    assert "DERIVED" in computed


# ======================================================================================
# D129 — the classifiers fail closed, and the witness lands on their SHAPE
# ======================================================================================

#: Every classifier in this file, with the answer its terminal fall-through must give.
#: A registry rather than a list of forms: what is checked below is the STRUCTURE of
#: these functions, so it stays true for shapes nobody has thought of.
_CLASSIFIERS = (
    ("_classify_expression", "_Shape.UNKNOWN"),
    ("_resolve_callee", "None"),
)


def _function_ast(name: str) -> ast.FunctionDef:
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} is not defined in this module")


@pytest.mark.parametrize("name,terminal", _CLASSIFIERS, ids=[c[0] for c in _CLASSIFIERS])
def test_d129_a_classifier_falls_through_to_unknown_and_not_to_an_answer(name, terminal):
    """**The row this cycle is for. It lands on the classifier, not on the forms.**

    Ten cycles asked "does the analysis recognise this form?" and after every answer
    another form arrived: seven BLOCK sites of eight, one file of two, one call form of
    two, one binding form of two, a bounded contract, and then a form INSIDE a contract
    node type and an arithmetic node outside a category named in prose. Every one of
    those classifiers ended in a definite answer, so each depended on its author having
    thought of the shape.

    What is asserted here is structural and needs nobody to anticipate anything: the
    last statement of each classifier is the UNKNOWN answer, and every definite answer
    it gives is inside an explicit branch. A classifier whose fall-through is a
    conclusion fails this, whatever forms it happens to name.
    """
    function = _function_ast(name)

    last = function.body[-1]
    assert isinstance(last, ast.Return) and last.value is not None, (
        f"{name} does not end in a return; its fall-through answer cannot be read"
    )
    assert ast.unparse(last.value) == terminal, (
        f"{name} falls through to {ast.unparse(last.value)!r}, a definite answer. "
        f"The terminal answer must be {terminal!r}: a shape the code does not "
        "recognise is unknown, not a 'no'."
    )

    # Every OTHER return must be reached through an explicit branch, so no definite
    # answer is given by position rather than by decision.
    branchless = []
    for statement in function.body[:-1]:
        for node in ast.walk(statement):
            if isinstance(node, ast.Return) and not isinstance(statement, (ast.If, ast.Try)):
                branchless.append(node.lineno)
    assert not branchless, (
        f"{name} returns outside any branch at lines {branchless}; a definite answer "
        "must be a decision the code makes, not a statement it reaches"
    )


def test_d129_the_classifiers_report_unknown_for_a_shape_they_do_not_name():
    """The behavioural half: an unrecognised shape really does come back UNKNOWN.

    ``ast.Yield`` is named by neither shape list, which is the point -- if it were, the
    test would be a replay of the recognised set. What matters is the answer for a node
    that is in neither, and that answer must not be "not computed".
    """
    yielded = ast.parse("def f():\n    x = yield 1\n")
    value = next(
        node.value for node in ast.walk(yielded) if isinstance(node, ast.Assign)
    )
    assert _classify_expression(value) is _Shape.UNKNOWN

    # And the constructor resolver, for a callee bound by nothing it can see.
    call = next(
        node for node in ast.walk(ast.parse("mystery_factory(1, 2)"))
        if isinstance(node, ast.Call)
    )
    assert _resolve_callee(call, {}, {}, set()) is None


def test_d129_f01_an_annotated_class_alias_is_a_construction():
    """``_v: type = Violation`` -- inside a contract node type, and still invisible.

    The AnnAssign branch recorded a name only when the value was a call, so a
    name-to-name annotated alias bound nothing, and calling it hit the lower-case
    branch and was dropped as not-a-class. Four instruments were silent on it.
    """
    source = (
        "from orbital_thermal.registry.applicability import Violation\n"
        "_v: type = Violation\n"
        "def f():\n"
        "    return _v(Axis.REGIME, Consequence.BLOCK, 'silent')\n"
    )
    sites, unmeasured = _scan_violation_constructions(source, pathlib.Path("planted.py"))
    assert not unmeasured
    assert len(sites) == 1 and sites[0][3] is False, (
        "the annotated alias is a Violation construction and it is silent on cause"
    )


def test_d129_f01_an_unresolvable_lowercase_callee_is_unmeasured_not_not_a_class():
    """The general half of F-01: unbound is unknown, whatever its capitalisation.

    The old branch answered "not a class" for every lower-case name it could not place,
    which is what let the alias through once its binding was invisible.
    """
    source = "def f():\n    return factory(1)\n"
    _sites, unmeasured = _scan_violation_constructions(source, pathlib.Path("planted.py"))
    assert unmeasured, "a callee bound by nothing visible must be reported"

    # The control: bound here, it is a deliberate not-a-class and not a report.
    bound = "def factory(x):\n    return x\ndef f():\n    return factory(1)\n"
    sites, unmeasured = _scan_violation_constructions(bound, pathlib.Path("planted.py"))
    assert not sites and not unmeasured


def test_d129_f02_unary_arithmetic_is_recognised_as_computed():
    """``boiling_number=-mass_flux`` was neither computed nor unmeasured.

    ``_contains_computation`` said "any call or arithmetic" and matched ``ast.Call`` and
    ``ast.BinOp``; unary arithmetic is ``ast.UnaryOp``. The category claim is withdrawn
    -- the shapes are a literal list now -- and ``UnaryOp`` is on it.
    """
    negated = ast.parse("-mass_flux").body[0].value
    assert _classify_expression(negated) is _Shape.COMPUTED
    assert ast.UnaryOp in _COMPUTING_SHAPES


def test_d129_a_selection_is_not_a_derivation():
    """The control against fixing F-02 by calling everything computed.

    ``fluid or state.fluid`` and ``None if x is None else x.shape`` select between read
    values; classifying them as computed turned two genuine case facts into derived
    quantities, which would have emptied ``CASE_FACTS`` rather than guarding it.
    """
    for selection in ("a or b", "None if a is None else a.shape"):
        node = ast.parse(selection).body[0].value
        assert _classify_expression(node) is _Shape.NOT_COMPUTED, selection
    for derivation in ("a or compute()", "b if a is None else compute()"):
        node = ast.parse(derivation).body[0].value
        assert _classify_expression(node) is _Shape.COMPUTED, derivation


def test_d129_the_fail_closed_report_is_readable():
    """What the report looks like, because a report nobody reads is not a guard.

    Fail-closed over every expression shape would flood; the recognised sets are
    explicit and chosen so the residue is small enough to read, which is the same
    problem the signature-derived relevance rule solved once already.
    """
    _derived, derivation_rows = _derived_quantities_in_production(with_unmeasured=True)
    constructor_rows = _violation_scan_unmeasured()
    assert len(constructor_rows) == 0, [str(r) for r in constructor_rows]
    assert len(derivation_rows) == 1, derivation_rows
    assert set(derivation_rows) == _ACKNOWLEDGED_UNREADABLE_EXPANSIONS


# ======================================================================================
# D130 — a leaf answer is legitimate only for a leaf, and the grammar says which is which
# ======================================================================================


def _expression_fields_with_modifier(
    node_type: type[ast.AST],
) -> tuple[tuple[str, str], ...]:
    """``(field, modifier)`` for every expression field, read from the ASDL signature.

    CPython carries each AST class's grammar rule in its docstring --
    ``Attribute(expr value, identifier attr, expr_context ctx)``,
    ``Slice(expr? lower, expr? upper, expr? step)``, ``JoinedStr(expr* values)`` -- so
    which node types have expression children, and whether a child is one node or a
    list of them, are facts about the grammar rather than opinions about the node.

    The type token is matched exactly after stripping the modifier, because
    ``expr_context`` contains ``expr`` and is not one. The modifier is RETURNED rather
    than discarded: the behavioural control needs to know whether to plant a node or a
    list of nodes, and a second reader of the same docstring is two records that can
    drift, which is how D124 arose. Callers that only want the names project them off.
    """
    documentation = (node_type.__doc__ or "").strip()
    opened = documentation.find("(")
    closed = documentation.rfind(")")
    assert documentation.startswith(node_type.__name__) and 0 < opened < closed, (
        f"{node_type.__name__} carries no ASDL signature, so this witness cannot read "
        "the grammar and must not pass by finding nothing"
    )
    fields: list[tuple[str, str]] = []
    for declaration in documentation[opened + 1 : closed].split(","):
        parts = declaration.split()
        if len(parts) != 2:
            continue
        token, name = parts
        if token.rstrip("?*") == "expr":
            fields.append((name, token[len("expr"):]))
    return tuple(fields)


def _expression_fields_of(node_type: type[ast.AST]) -> tuple[str, ...]:
    """The names alone, projected off the one reader above."""
    return tuple(name for name, _modifier in _expression_fields_with_modifier(node_type))


def test_d130_every_reading_shape_is_a_genuine_leaf():
    """**The witness lands on the SHAPE OF THE RECOGNISED SET, not on the shapes in it.**

    A node with expression children is not a leaf, and answering ``NOT_COMPUTED`` for
    one is a definite answer over children nobody looked at. Six of the eight former
    members carried children: ``f(q).attr``, ``[a * b][0]``, ``a[f(i):g(j)]``,
    ``lambda: f(q)``, ``f'{a + b}'`` all came back not-computed.

    Derived from the grammar, so it fails on the day someone puts ``Attribute`` back --
    which is the same move as the classifier-shape witness, one level in. The
    fail-closed default could not have caught this: it removes the dependence on
    anticipating an unrecognised shape and says nothing about a recognised one answered
    wrongly.
    """
    offenders = {
        node_type.__name__: _expression_fields_of(node_type)
        for node_type in _READING_SHAPES
        if _expression_fields_of(node_type)
    }
    assert not offenders, (
        "these are named as leaves and carry expression children, so the classifier "
        f"answers over children it never looked at: {offenders}"
    )

    # The control: the derivation must actually find expression fields somewhere, or
    # "no offenders" is the answer of a reader that reads nothing.
    assert _expression_fields_of(ast.Attribute) == ("value",)
    assert _expression_fields_of(ast.Slice) == ("lower", "upper", "step")
    assert _expression_fields_of(ast.Name) == ()


def test_d130_every_shape_with_children_is_reached_by_a_recursing_branch():
    """The other half: a node type that carries children must be recursed into or be
    unknown. Nothing named may answer definitely over children it ignores.

    ``_COMPUTING_SHAPES`` is exempt and deliberately so -- a call is computed whatever
    its arguments are, which is a conclusion about the node itself rather than an answer
    over its children.
    """
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    classifier = next(
        node for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name == "_classify_expression"
    )
    recursed: set[str] = set()
    for statement in classifier.body:
        if not isinstance(statement, ast.If):
            continue
        test = statement.test
        if not (
            isinstance(test, ast.Call)
            and getattr(test.func, "id", "") == "isinstance"
            and len(test.args) == 2
        ):
            continue
        # The branch must actually recurse, or naming the type proves nothing.
        if not any(
            isinstance(node, ast.Call)
            and getattr(node.func, "id", "") == "_classify_expression"
            for node in ast.walk(statement)
        ):
            continue
        named = test.args[1]
        for candidate in (
            named.elts if isinstance(named, ast.Tuple) else [named]
        ):
            if isinstance(candidate, ast.Attribute):
                recursed.add(candidate.attr)
    for name in ("Attribute", "Subscript", "Slice", "Lambda", "JoinedStr",
                 "FormattedValue"):
        assert name in recursed, (
            f"ast.{name} carries expression children and has no branch that recurses "
            "into them"
        )


def test_d130_a_read_of_a_computation_is_a_computation_and_a_read_of_a_read_is_not():
    """Both directions, which is what stops the fix from being 'call everything computed'."""
    for read in (
        "state.mu_f_Pa_s",
        "geometry.hydraulic_diameter_m",
        "a.b.c",
        "a[0]",
        "'text'",
    ):
        node = ast.parse(read).body[0].value
        assert _classify_expression(node) is _Shape.NOT_COMPUTED, read
    for computation in (
        "f(q).attr",
        "(a + b).real",
        "a[f(i)]",
        "[a * b][0]",
        "a[f(i):g(j)]",
        "lambda: f(q)",
        "f'{a + b}'",
    ):
        node = ast.parse(computation).body[0].value
        assert _classify_expression(node) is _Shape.COMPUTED, computation


def test_d130_the_subscripted_list_regression_is_caught_again():
    """The regression itself: caught at 45f2cba, silent at f0ecf09, caught here.

    ``_bo = [mass_flux / (D * 1000.0)][0]`` binds a computed value through a subscript
    of a list literal. The whole-subtree walk saw the ``BinOp``; the structural
    classifier stopped at ``Subscript`` and answered as a leaf.
    """
    source = (
        "def produce(mass_flux, geometry):\n"
        "    _bo = [mass_flux / (geometry.hydraulic_diameter_m * 1000.0)][0]\n"
        "    return check(boiling_number=_bo)\n"
    )
    scope = next(
        node for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef)
    )
    computed, _bound, _unknown = _contract_bindings(scope)
    assert "_bo" in computed, (
        "a value computed inside a subscripted literal is a computed value; reading it "
        "as a leaf is how a caller-steerable eligibility went silent"
    )


# ======================================================================================
# D131 — a branch that recurses must recurse into every child it answers over
# ======================================================================================


def _recursing_branches() -> dict[str, ast.If]:
    """The classifier's ``isinstance`` branches that actually recurse, by type name.

    A branch counts only if it contains a call to :func:`_classify_expression`; naming
    a type and then answering without recursing is the shape D130 closed.
    """
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    classifier = next(
        node for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name == "_classify_expression"
    )
    branches: dict[str, ast.If] = {}
    for statement in classifier.body:
        if not isinstance(statement, ast.If):
            continue
        test = statement.test
        if not (
            isinstance(test, ast.Call)
            and getattr(test.func, "id", "") == "isinstance"
            and len(test.args) == 2
        ):
            continue
        if not any(
            isinstance(node, ast.Call)
            and getattr(node.func, "id", "") == "_classify_expression"
            for node in ast.walk(statement)
        ):
            continue
        named = test.args[1]
        for candidate in (named.elts if isinstance(named, ast.Tuple) else [named]):
            if isinstance(candidate, ast.Attribute):
                branches[candidate.attr] = statement
    return branches


def _fields_visited_by(branch: ast.If) -> set[str]:
    """The fields of ``node`` a branch reads."""
    return {
        node.attr
        for node in ast.walk(branch)
        if isinstance(node, ast.Attribute) and getattr(node.value, "id", "") == "node"
    }


def test_d131_a_recursing_branch_references_every_expression_child_it_answers_over():
    """**A diagnostic, and NOT the completeness check. D133 renamed it to say so.**

    It asserts the branch REFERENCES every expression field the grammar gives its type.
    That is necessary and it is not sufficient: a branch may read a field for some other
    purpose and still answer definitely over it, which is exactly C-08 --

        parts = [node.lower, node.upper]
        if node.step is not None and isinstance(node.step, ast.Constant):
            parts.append(node.step)

    mentions ``node.step`` twice, satisfies this row, and classifies ``a[1:2:f(i)]`` as
    a read. Completeness is
    ``test_d133_a_computation_in_any_child_makes_the_whole_expression_computed``, which
    asserts on the ANSWER. This row is kept because it fails earlier and names the
    branch, which the behavioural row cannot do -- three cycles of assertions about what
    the source looks like are why it is no longer the claim.

    The D130 witness required a branch to contain a recursive call and never asked what
    it recursed into. Cutting ``Slice`` from three children to two left
    ``a[1:2:f(i)]`` reading NOT_COMPUTED with 213 rows green -- and the companion cut,
    ``Subscript`` down to ``value`` alone, was caught only because ``a[f(i)]`` happens
    to be on a hand-written list of examples. ``a[1:2:f(i)]`` was not on it.

    So the needed fields come from :func:`_expression_fields_of`, which the leaf
    witness's own control already exercises, minus whatever
    :data:`_UNVISITED_FIELDS` declares. One record, read here rather than copied.
    """
    branches = _recursing_branches()
    assert branches, "no recursing branch was found, so this proves nothing"

    incomplete = {}
    for type_name, branch in branches.items():
        node_type = getattr(ast, type_name)
        exempt = set(_UNVISITED_FIELDS.get(node_type, ()))
        needed = set(_expression_fields_of(node_type)) - exempt
        missing = needed - _fields_visited_by(branch)
        if missing:
            incomplete[type_name] = sorted(missing)
    assert not incomplete, (
        "these branches recurse but answer definitely over expression children they "
        f"never visit: {incomplete}. A field is either visited or declared in "
        "_UNVISITED_FIELDS with a measurement behind it."
    )

    # The control the leaf witness has: the derivation must find fields somewhere, or
    # "nothing incomplete" is the answer of a reader that reads nothing.
    assert set(_expression_fields_of(ast.Slice)) == {"lower", "upper", "step"}
    assert "Slice" in branches and _fields_visited_by(branches["Slice"]) >= {
        "lower",
        "upper",
        "step",
    }


@pytest.mark.parametrize(
    "node_type,field",
    sorted(
        ((t, f) for t, fields in _UNVISITED_FIELDS.items() for f in fields),
        key=lambda pair: (pair[0].__name__, pair[1]),
    ),
    ids=lambda value: value if isinstance(value, str) else value.__name__,
)
def test_d131_every_exemption_has_a_measurement_behind_it(node_type, field):
    """An exemption is a claim, and a claim on this gate needs an instrument.

    For each declared exemption there must be an expression where visiting the field
    would flip a correct NOT_COMPUTED into COMPUTED. That is executed here, so an
    exemption added on somebody's word fails for want of a demonstration rather than
    being believed.
    """
    assert field in _expression_fields_of(node_type), (
        f"{node_type.__name__}.{field} is not an expression field, so exempting it "
        "from recursion is exempting nothing"
    )
    source = _EXEMPTION_EVIDENCE.get((node_type, field))
    assert source, (
        f"{node_type.__name__}.{field} is exempt from recursion with no measurement "
        "behind it; declare the expression that shows visiting it gives a wrong answer"
    )

    node = ast.parse(source).body[0].value
    assert isinstance(node, node_type)
    assert _classify_expression(node) is _Shape.NOT_COMPUTED, (
        f"{source!r} is the evidence for exempting {field}, and it does not classify "
        "as a read, so it cannot show that visiting the field would be wrong"
    )
    assert _classify_expression(getattr(node, field)) is _Shape.COMPUTED, (
        f"visiting {node_type.__name__}.{field} would not change the answer for "
        f"{source!r}, so the exemption is unnecessary -- visit it instead"
    )


def test_d131_the_exemption_set_is_declared_in_one_place():
    """Two records that can drift is how D124 arose, so there is one.

    The witness above reads :data:`_UNVISITED_FIELDS`; nothing else may carry a second
    copy of what is unvisited, and the branches themselves point at it rather than
    restating it.
    """
    assert set(_UNVISITED_FIELDS) == {ast.IfExp}, (
        "the exemption set has grown; each new entry needs its own measurement and its "
        "own reason at the branch"
    )
    assert _UNVISITED_FIELDS[ast.IfExp] == ("test",)
    # Counted by PARSING, not by searching the text: a string search finds this
    # assertion, which mentions the name in order to state the rule about it. That is
    # the self-referential shape this gate has counted repeatedly, and the answer has
    # been the same every time -- a binding is a binding, a mention of one is not.
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    bindings = [
        target.id
        for node in ast.parse(source).body
        for target in (
            [node.target] if isinstance(node, ast.AnnAssign)
            else node.targets if isinstance(node, ast.Assign)
            else []
        )
        if isinstance(target, ast.Name) and target.id == "_UNVISITED_FIELDS"
    ]
    assert len(bindings) == 1, f"{len(bindings)} records of what is unvisited"


# ======================================================================================
# D133 — assert on the ANSWER, generated from the grammar
# ======================================================================================



#: Placeholders for the NON-expression fields of a planted node, by ASDL token. These
#: are construction details rather than claims: the classifier reads only expression
#: fields and ``isinstance``, but leaving the rest unset raises a DeprecationWarning
#: that becomes an error in Python 3.15, and a control that stops building on a future
#: interpreter is a control that stops checking.
_ASDL_PLACEHOLDERS = {
    "identifier": lambda: "x",
    "expr_context": ast.Load,
    "int": lambda: -1,
    "boolop": ast.And,
    "operator": ast.Add,
    "unaryop": ast.USub,
    "arguments": lambda: ast.arguments(
        posonlyargs=[], args=[], vararg=None, kwonlyargs=[],
        kw_defaults=[], kwarg=None, defaults=[],
    ),
    "constant": lambda: None,
    "string": lambda: None,
}


def _all_fields_with_token(node_type: type[ast.AST]) -> tuple[tuple[str, str], str]:
    """Every field of ``node_type`` with its ASDL token, from the one reader's source."""
    documentation = (node_type.__doc__ or "").strip()
    opened = documentation.find("(")
    closed = documentation.rfind(")")
    declared = []
    for declaration in documentation[opened + 1 : closed].split(","):
        parts = declaration.split()
        if len(parts) == 2:
            declared.append((parts[1], parts[0]))
    return tuple(declared)


def _planted_node(node_type: type[ast.AST], field: str) -> ast.AST:
    """A node of ``node_type`` with a COMPUTED value in ``field`` and reads elsewhere.

    Built from the ASDL signature rather than written out: every expression field gets
    a bare ``ast.Name`` -- a read -- except ``field``, which gets a zero-argument call.
    ``expr*`` fields get a one-element list. Non-expression fields are left unset, which
    is safe because the classifier reads only expression fields and ``isinstance``.

    **Some of these nodes are not valid Python and that is deliberate.** A computed
    value in ``NamedExpr.target`` cannot be written as source at all. The control is
    about the classifier's mechanism -- does a computation in this child reach the
    answer -- and not about parseable code, so a reader should not take an unwritable
    plant for a bug.
    """
    def read() -> ast.AST:
        return ast.Name(id="x", ctx=ast.Load())

    def computation() -> ast.AST:
        return ast.Call(func=ast.Name(id="f", ctx=ast.Load()), args=[], keywords=[])

    arguments: dict[str, object] = {}
    expression_fields = dict(_expression_fields_with_modifier(node_type))
    for name, token in _all_fields_with_token(node_type):
        if name in expression_fields:
            value = computation() if name == field else read()
            arguments[name] = [value] if "*" in expression_fields[name] else value
            continue
        placeholder = _ASDL_PLACEHOLDERS.get(token.rstrip("?*"))
        if placeholder is not None:
            arguments[name] = [] if "*" in token else placeholder()
    return node_type(**arguments)


def _plantable_children() -> list[tuple[str, str]]:
    """``(type name, field)`` for every non-exempt expression child of a recursing type.

    Derived twice over: the types come from the classifier's own recursing branches, the
    fields from the grammar, and the exemptions from :data:`_UNVISITED_FIELDS`. Nothing
    here is a list somebody wrote.
    """
    plantable = []
    for type_name in sorted(_recursing_branches()):
        node_type = getattr(ast, type_name)
        exempt = set(_UNVISITED_FIELDS.get(node_type, ()))
        for field, _modifier in _expression_fields_with_modifier(node_type):
            if field not in exempt:
                plantable.append((type_name, field))
    return plantable


@pytest.mark.parametrize(
    "type_name,field", _plantable_children(),
    ids=[f"{t}.{f}" for t, f in _plantable_children()],
)
def test_d133_a_computation_in_any_child_makes_the_whole_expression_computed(
    type_name, field
):
    """**The completeness check, asserting on the ANSWER rather than on the source.**

    Three cycles asserted on what the branch looked like -- D130 that it contained a
    recursive call, D131 that it referenced each field -- and each time the next
    narrowing sat one step below the assertion. C-08 was a branch that read
    ``node.step`` twice without ever classifying it.

    The syntactic repair is not the answer either: requiring the field to appear as an
    ARGUMENT of the classifier call goes red on eleven of the fourteen correct branches,
    because they route the field through a comprehension iterable. That would be another
    enumeration of forms, which is the thing being repaired.

    So: put a computation in each child the grammar says the node has, and require the
    classifier to say COMPUTED. A branch that skips a child, reads it without
    classifying it, or classifies it conditionally fails here whatever its source looks
    like.
    """
    node_type = getattr(ast, type_name)
    planted = _planted_node(node_type, field)
    assert _classify_expression(planted) is _Shape.COMPUTED, (
        f"a computation planted in {type_name}.{field} does not reach the answer: the "
        "branch answers definitely over a child it never classifies"
    )


def test_d133_the_behavioural_control_has_something_to_check():
    """The control's control: it must cover the recursing types and their children.

    "All COMPUTED" is also what a generator that produced nothing would report, and the
    mirror row -- all reads must give NOT_COMPUTED -- was measured NOT to discriminate,
    so it is deliberately absent rather than present and inert.
    """
    plantable = _plantable_children()
    assert len(plantable) >= 14, f"only {len(plantable)} children generated"
    covered = {type_name for type_name, _field in plantable}
    assert covered == set(_recursing_branches()), (
        "a type with a recursing branch produced no plantable child"
    )
    assert ("Slice", "step") in plantable and ("Subscript", "slice") in plantable
    # The one exempt field is absent from the population, not silently passing in it.
    assert ("IfExp", "test") not in plantable
    assert ("IfExp", "body") in plantable and ("IfExp", "orelse") in plantable
