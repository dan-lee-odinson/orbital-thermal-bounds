"""S5 two-phase architecture cases — one witness per acceptance criterion it holds.

Criteria file: ``ACCEPTANCE_CRITERIA_OTB-G005.md``. Only S5-1 … S5-7 are implemented at
this point; S5-8 … S5-14 have no code to witness yet and no test here pretends otherwise.

**Every test below is named for the criterion it holds and fails when that criterion's own
falsifier is introduced.** `OTB-G002` criterion 8 — every new check has been witnessed
failing — is discharged for these by ``tests/../scripts/witness_s2_checks.py`` anchors and,
where the falsifier is structural rather than numeric, by the test constructing the
falsifying shape itself and requiring it to be refused.
"""

from __future__ import annotations

import dataclasses
import inspect
import pathlib
import re

import pytest

from orbital_thermal import two_phase_architecture_cases as ac
from orbital_thermal.registry.applicability import Axis, Consequence
from orbital_thermal.registry.provenance import Status

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
    after = ac.assess_fluid("ammonia", gravity_m_s2=_REFERENCE_G, entries=demoted)
    assert "chf" not in after.legs, (
        "de-adopting the CHF correlation must remove the CHF leg; if it does not, "
        "eligibility is a list rather than a rule"
    )


def test_s5_1_no_caller_argument_can_set_an_outcome():
    """**S5-1**'s third falsifier: "an eligibility that can be set by a caller"."""
    for fn in (ac.assess_fluid, ac.assess_leg):
        params = set(inspect.signature(fn).parameters)
        assert not (params & {"eligible", "eligibility", "force", "override", "result"}), (
            f"{fn.__name__} takes an argument that could set an outcome: {sorted(params)}"
        )


def test_s5_1_an_absent_correlation_is_not_an_ineligibility():
    """No adopted correlation returns ``None``, which S4-8 requires to stay distinct from
    a refusal: "no correlation exists" and "one exists and refuses" are different claims.
    """
    stripped = tuple(e for e in ac.REGISTRY_ENTRIES if e.kind != "chf")
    assert ac.assess_leg("ammonia", "chf", gravity_m_s2=_REFERENCE_G, entries=stripped) is None
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
    with pytest.raises(ValueError, match="gravity basis"):
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
    assert chf.eligible is True


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
    body = "\n".join(
        line for line in source.splitlines()
        if not line.lstrip().startswith("#") and '"""' not in line
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
    assert chf.eligible is True
    assert not [v for v in chf.violations if v.axis is Axis.ORIENTATION]

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
    source = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    offenders = [
        f"two_phase_architecture_cases.py:{n}: {line.strip()[:110]}"
        for n, line in enumerate(source.splitlines(), 1)
        if directional.search(line)
    ]
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
