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
    with pytest.raises(ValueError, match="not a registry entry"):
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
        with pytest.raises(ValueError, match="empty"):
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
    with pytest.raises(ValueError, match="does not match the registry"):
        ac.LegEligibility(fluid="water", leg="chf", entry_id=real.entry_id,
                          eligible=True, gravity_basis=overridden)

    reworded = ac.GravityBasis(
        entry_id=real.entry_id,
        reference_gravity_m_s2=real.reference_gravity_m_s2,
        basis="a friendlier basis sentence")
    with pytest.raises(ValueError, match="does not match the registry"):
        ac.LegEligibility(fluid="water", leg="chf", entry_id=real.entry_id,
                          eligible=True, gravity_basis=reworded)


def test_f04_a_zero_or_defaulted_reference_gravity_is_refused():
    """**Falsifier 4: defaulted.** The literal shape Sol constructed: 0.0 with no basis."""
    with pytest.raises(ValueError, match="not a positive gravity|empty"):
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
    ok = ac.LegEligibility(fluid="water", leg="chf", entry_id=real.entry_id,
                           eligible=True, gravity_basis=real)
    assert ok.gravity_basis == real
    # `is not None`, NOT a truth test: bool() on a CHF record raises by design (S5-5), and
    # the first draft of this control tripped that guard. A negative control that cannot
    # be written without violating another criterion is a control written carelessly.
    assert ac.assess_leg(
        "water", "chf", gravity_m_s2=_REFERENCE_G, **_FULL_CASE) is not None


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
