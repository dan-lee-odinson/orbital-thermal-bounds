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
import dataclasses
import inspect
import pathlib
import re
import subprocess
import sys
import warnings

import pytest
from conftest import _child_env

from orbital_thermal import two_phase_architecture_cases as ac
from orbital_thermal.registry import two_phase as _tp_module
from orbital_thermal.registry.applicability import Applicability, Axis, Consequence
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
    assert at_1g.eligible is True and micro.eligible is False
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
    assert [v.axis for v in truth.violations] == [Axis.ORIENTATION]

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
    assert chf.eligible is True
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
    assert truth.eligible is False and [v.axis for v in truth.violations] == [
        Axis.ORIENTATION
    ], "the case is not de-ranked to begin with, so steering it would prove nothing"

    probe(monkeypatch)
    steered = ac.assess_leg("water", "chf", gravity_m_s2=_MICROGRAVITY, **_FULL_CASE)
    if steered is _FORGED_SENTINEL:
        return  # the seam route: the computation was replaced outright
    assert steered.eligible is True and steered.violations == (), (
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
    assert [v.axis for v in after.violations] == [Axis.ORIENTATION]

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
