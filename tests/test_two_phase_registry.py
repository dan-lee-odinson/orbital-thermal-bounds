"""S1 two-phase registry tests (metadata / flags / guards only -- NOT physics).

These tests assert the *registry contract*: every two-phase correlation is sourced,
the reference correlations are rank-eligible while sensitivities/ONB/NPSH are not,
every HTC/dP/CHF entry carries the 1g gravity-basis metadata, the CoolProp pin and
Chisholm rule are recorded as pinned, the saturation-backend property entries are
rank-eligible per-state evaluators, and the rank/domain guards reject bad use.

No correlation math is evaluated here (S1 is registry-only); ``evaluate`` is ``None``
throughout and physical correctness is intentionally out of scope.
"""

import pytest

from orbital_thermal.registry import (
    NotRankEligibleError,
    PropertyKind,
    Status,
    assert_in_domain,
    assert_rank_eligible,
    get,
    two_phase,
)
from orbital_thermal.registry.two_phase import (
    CHISHOLM_C,
    COOLPROP_PIN,
    TWO_PHASE_CORRELATIONS,
    TWO_PHASE_PROPERTIES,
    missing_metadata,
)

# OTB-G001 F-03 / Director ruling D3 swapped the CHF reference: shah_2015's citation
# resolves to no single paper and its declared band was Shah (1987)'s all along, so
# shah_1987 is the reference and shah_2015 is blocked.
_REFERENCE_IDS = [
    "two_phase.htc.gungor_winterton",
    "two_phase.dp.lockhart_martinelli_chisholm",
    "two_phase.chf.shah_1987",
]
_NON_RANKABLE_IDS = [
    "two_phase.htc.chen",
    "two_phase.htc.shah_2022",
    "two_phase.onb.bergles_rohsenow",
    "two_phase.dp.friedel",
    "two_phase.dp.muller_steinhagen_heck",
    "two_phase.chf.shah_2015",
    "two_phase.chf.katto_ohno",
]
_GRAVITY_KINDS = {"htc", "dp", "chf"}


# --- sourcing -------------------------------------------------------------------


def test_every_correlation_has_a_nonempty_citation():
    for c in TWO_PHASE_CORRELATIONS:
        assert c.source is not None, f"{c.id} has no source"
        assert c.source.citation.strip(), f"{c.id} has an empty citation"


#: The two-phase ids S2 implemented an executable form for. This is the successor to
#: the S1 ``test_no_evaluate_callable_in_s1`` guard, which asserted that NO entry
#: carried an ``evaluate``. S2 exists to add executable forms, so that test had to
#: fail the moment S2 succeeded -- that was the S1 gate working, not a defect. The
#: successor below is strictly stronger: it pins the EXACT set, so it still catches
#: an accidental early implementation of an S3 correlation (e.g. the pressure-drop
#: entries) and any un-scoped promotion, in both directions.
#:
#: ``two_phase.chf.shah_2015`` and ``two_phase.onb.bergles_rohsenow`` are absent on
#: purpose: S2 was scoped to implement the CHF entry and to attempt the ONB one, and
#: both were left unimplemented because their sources could not be established. See
#: their registry source notes.
S2_IMPLEMENTED_IDS = frozenset(
    {
        "two_phase.htc.gungor_winterton",
        "two_phase.chf.shah_1987",
        # S3 (OTB-G002) adds the reference pressure drop and the pump-inlet criterion.
        "two_phase.dp.lockhart_martinelli_chisholm",
        "two_phase.pump.npsh",
        # S4 (OTB-G003) adds the static Ledinegg guard, adopted by Director ruling D15
        # against DEBTS D-12. It is the only implementation this milestone adds: the
        # assessed pressure-drop candidate stays at evaluate=None, because assessing a
        # correlation and adopting one are different acts and only the first was ruled.
        "two_phase.stability.ledinegg_static",
    }
)


def test_exactly_the_s2_implemented_ids_carry_an_evaluate_callable():
    """Exactly the S2-implemented ids have an executable form; all others are None."""
    with_evaluate = {c.id for c in TWO_PHASE_CORRELATIONS if c.evaluate is not None}
    assert with_evaluate == set(S2_IMPLEMENTED_IDS), (
        "the set of two-phase correlations carrying an evaluate callable must be "
        f"exactly {sorted(S2_IMPLEMENTED_IDS)}; found {sorted(with_evaluate)}. "
        "Adding one means an out-of-scope correlation was implemented; removing one "
        "means an S2 deliverable regressed."
    )


def test_s2_unimplemented_entries_are_still_none():
    """The two entries S2 deliberately did not implement carry no executable form."""
    for cid in ("two_phase.chf.shah_2015", "two_phase.onb.bergles_rohsenow"):
        entry = get(cid)
        assert entry.evaluate is None, (
            f"{cid} must not carry an evaluate callable: its source could not be "
            "established, and the blocker is the deliverable (no-invention policy)"
        )
        assert entry.source is not None and entry.source.note.strip(), (
            f"{cid} must record WHY it was not implemented in its source note"
        )


#: The one pressure-drop correlation S3 implements. A4 makes Lockhart-Martinelli/
#: Chisholm the REFERENCE and Friedel and Mueller-Steinhagen-Heck named SENSITIVITIES;
#: this milestone implements the reference only.
S3_IMPLEMENTED_DP_IDS = frozenset({"two_phase.dp.lockhart_martinelli_chisholm"})


def test_only_the_reference_pressure_drop_is_implemented():
    """Successor to the S2 guard that no dp entry carried an executable form.

    That guard had to fail the moment S3 succeeded -- which is the gate working, not a
    defect. The successor is strictly stronger: it pins the EXACT dp set, so it still
    catches an out-of-scope sensitivity being implemented, in both directions.
    """
    implemented = {c.id for c in TWO_PHASE_CORRELATIONS if c.kind == "dp" and c.evaluate}
    assert implemented == set(S3_IMPLEMENTED_DP_IDS), (
        "A4 names Friedel and Mueller-Steinhagen-Heck as sensitivities, not references; "
        f"expected exactly {sorted(S3_IMPLEMENTED_DP_IDS)}, found {sorted(implemented)}"
    )


def test_the_named_dp_sensitivities_stay_unimplemented():
    """Friedel and Mueller-Steinhagen-Heck are untouched by S3 (ruling A4)."""
    for cid in ("two_phase.dp.friedel", "two_phase.dp.muller_steinhagen_heck"):
        entry = get(cid)
        assert entry.evaluate is None, f"{cid} is a named sensitivity, not a reference"
        assert entry.rank_eligible is False


def test_implemented_correlations_have_a_nonempty_locator():
    """Binding invariant: an executable form requires a read source (Sec. 3.2b).

    Implemented without a locator recording what was actually consulted -> the suite
    fails. This is what turns the sourcing rule into a mechanism instead of a promise.

    Scope note: this invariant is deliberately applied to the **two-phase** registry
    only. Stage-1's B1 correlations carry seven ``evaluate`` callables with blank
    locators; retro-fitting locators onto them is Stage-1 work and out of scope for
    OTB-G001, so widening this test is a deliberate future decision, not an oversight.
    """
    for c in TWO_PHASE_CORRELATIONS:
        if c.evaluate is not None:
            assert c.source is not None, f"{c.id} has an evaluate but no source"
            assert c.source.locator.strip(), (
                f"{c.id} carries an executable form but its source.locator is blank: "
                "a correlation may only be implemented from a source that was "
                "actually consulted, and the locator must record which one"
            )


def test_unimplemented_correlations_keep_a_blank_locator():
    """The converse: nothing **unconsulted** acquires a locator (T8 is bounded).

    The invariant is about whether a paper was *read*, and it used "carries an
    ``evaluate``" as the proxy for that. S4 breaks the proxy in both directions it can
    break: a source can be read in full and still be unimplementable (Shah 1974's
    correlating curve is hand-drawn and disclaimed by its own author) or read in full
    and deliberately not implemented (Kim & Mudawar 2013, which A4 has not adopted).
    So the test now asks the question it always meant to ask, and ``Source.consulted``
    is the answer -- see the field's own note.
    """
    for c in TWO_PHASE_CORRELATIONS:
        if c.evaluate is None and not c.source.consulted:
            assert not c.source.locator.strip(), (
                f"{c.id} has no executable form and is not declared consulted, so no "
                "paper was read for a formula from it; its locator must stay blank "
                "rather than be filled in speculatively"
            )


def test_a_source_declared_consulted_must_say_what_was_read():
    """``consulted`` cannot be used to wave a locator through without one."""
    for c in TWO_PHASE_CORRELATIONS:
        if c.source is not None and c.source.consulted:
            assert c.source.locator.strip(), (
                f"{c.id} declares its source consulted but records no locator: the "
                "flag exists to admit a locator that names what was read, so a blank "
                "one is the defect it was introduced to prevent"
            )


def test_the_deliberately_unimplemented_s4_sources_are_declared_consulted():
    """The two S4 entries that were read but must not be implemented say so."""
    for cid in ("two_phase.htc.shah_1974_ammonia", "two_phase.dp.kim_mudawar_2013"):
        entry = get(cid)
        assert entry.evaluate is None, f"{cid} must carry no executable form"
        assert entry.source is not None and entry.source.consulted, (
            f"{cid} was read from the rendered pages and must declare it, so its "
            "locator is admissible on the fact rather than on a proxy"
        )


def test_provisional_domains_are_declared_not_promoted():
    """A domain that could not be confirmed is declared provisional, not promoted."""
    from orbital_thermal.registry.two_phase import PROVISIONAL_DOMAINS

    # The CHF entry's domain was checked against the source and found to belong to a
    # different paper; the HTC entry's numeric ranges could not be matched at all.
    for cid in ("two_phase.chf.shah_2015", "two_phase.htc.gungor_winterton"):
        assert cid in PROVISIONAL_DOMAINS, (
            f"{cid} has an unconfirmed validity domain and must be declared "
            "provisional rather than quietly treated as confirmed"
        )
        assert PROVISIONAL_DOMAINS[cid].strip(), f"{cid}: empty provisional reason"

    # A provisional domain is still enforced as the guard.
    assert get("two_phase.htc.gungor_winterton").domain.ranges, (
        "declaring a domain provisional must not remove it: the ranges are still "
        "the enforced guard"
    )


def test_ammonia_is_not_in_the_gw86_fluid_database():
    """The reference coolant sits outside the reference HTC's fluid database.

    Machine-visible because it is load-bearing: S0 Sec. 9.1 makes ammonia the
    reference coolant, while the Gungor & Winterton (1986) database is water, five
    refrigerants and ethylene glycol. Both are director-level facts; reconciling them
    is a disposition decision, so this build surfaces the conflict rather than
    silently de-ranking ammonia or silently ranking it.
    """
    from orbital_thermal.registry.two_phase import (
        GW86_DATABASE_FLUIDS,
        fluid_in_gw86_database,
    )

    assert fluid_in_gw86_database("water") is True
    assert fluid_in_gw86_database("Ammonia") is False
    assert "ammonia" not in GW86_DATABASE_FLUIDS


# --- rank eligibility -----------------------------------------------------------


@pytest.mark.parametrize("cid", _REFERENCE_IDS)
def test_reference_correlations_are_rank_eligible(cid):
    assert get(cid).rank_eligible is True


@pytest.mark.parametrize("cid", _NON_RANKABLE_IDS)
def test_sensitivities_onb_npsh_are_not_rank_eligible(cid):
    assert get(cid).rank_eligible is False


# --- gravity-basis metadata on every HTC/dP/CHF entry ---------------------------


def test_htc_dp_chf_entries_carry_1g_microgravity_metadata():
    checked = 0
    for c in TWO_PHASE_CORRELATIONS:
        if c.kind in _GRAVITY_KINDS:
            checked += 1
            assert c.microgravity_validated is False, f"{c.id} microgravity_validated"
            assert c.gravity_basis == "1g", f"{c.id} gravity_basis"
            assert c.rank_scope == "reference_correlation_only", f"{c.id} rank_scope"
            assert c.limitation.strip(), f"{c.id} limitation empty"
    assert checked > 0, "expected at least one HTC/dP/CHF entry"


# --- backend pin ----------------------------------------------------------------


def test_coolprop_pin_recorded():
    assert COOLPROP_PIN.pinned_version == "7.2.0"
    assert COOLPROP_PIN.latest_known_version == "8.0.0"
    assert COOLPROP_PIN.migration_requires.strip(), "migration_requires must be non-empty"


# --- Chisholm rule --------------------------------------------------------------


def test_chisholm_c_regime_keys_and_values():
    assert CHISHOLM_C[("turbulent", "turbulent")] == 20.0
    assert CHISHOLM_C[("laminar", "turbulent")] == 12.0
    assert CHISHOLM_C[("turbulent", "laminar")] == 10.0
    assert CHISHOLM_C[("laminar", "laminar")] == 5.0
    assert set(CHISHOLM_C) == {
        ("turbulent", "turbulent"),
        ("laminar", "turbulent"),
        ("turbulent", "laminar"),
        ("laminar", "laminar"),
    }


def test_chisholm_regime_thresholds_present():
    assert two_phase.CHISHOLM_RE_LAMINAR_MAX == 1000.0
    assert two_phase.CHISHOLM_RE_TURBULENT_MIN == 2000.0


# --- saturation-backend property entries ----------------------------------------


@pytest.mark.parametrize(
    "pid", ["coolant.ammonia.saturation_backend", "coolant.water.saturation_backend"]
)
def test_saturation_backend_entries(pid):
    e = get(pid)
    assert e.kind is PropertyKind.BACKEND_EVALUATION
    assert e.rank_eligible is True
    assert e.version == "7.2.0"
    assert e.status is Status.RESOLVED


def test_ammonia_saturation_backend_cites_gao_2020():
    e = get("coolant.ammonia.saturation_backend")
    assert e.source is not None
    assert "Gao" in e.source.citation
    assert "2020" in e.source.citation


def test_water_saturation_backend_cites_iapws95():
    e = get("coolant.water.saturation_backend")
    assert e.source is not None
    # IAPWS-95 water reference (Wagner & Pruss 2002).
    assert "IAPWS" in e.source.citation or "Wagner" in e.source.citation


# --- guard behavior -------------------------------------------------------------


def test_assert_in_domain_raises_out_of_domain_mass_flux():
    gw = get("two_phase.htc.gungor_winterton")
    with pytest.raises(NotRankEligibleError):
        assert_in_domain(gw, G_kg_m2s=5000)


def test_assert_in_domain_passes_inside_domain():
    gw = get("two_phase.htc.gungor_winterton")
    # In-domain value must NOT raise (metadata guard, no physics).
    assert_in_domain(gw, G_kg_m2s=100)


def test_assert_rank_eligible_raises_on_sensitivity():
    chen = get("two_phase.htc.chen")
    with pytest.raises(NotRankEligibleError):
        assert_rank_eligible(chen)


def test_npsh_moved_off_source_required_by_ruling_d8():
    """Successor to the S2 guard that the NPSH entry was blocked.

    Director ruling D8 adopts a SUBCOOLING-margin criterion on the AMS-02 flight
    precedent, so the entry is now sourced and implemented. The quantitative
    NPSHA/NPSH3 route is deliberately NOT implemented -- it needs a specific pump --
    and the entry's note must carry the warning that NPSHA = NPSHR is the onset of
    damage rather than a safe point.
    """
    npsh = get("two_phase.pump.npsh")
    assert npsh.status is Status.RESOLVED
    assert npsh.evaluate is not None
    assert npsh.rank_eligible is True
    assert_rank_eligible(npsh)  # must not raise

    note = npsh.source.note
    assert "NPSH3" in note and "onset of damage" in note.lower()
    assert "not implemented" in note.lower()


def test_assert_rank_eligible_passes_on_reference():
    # A rank-eligible reference must not raise.
    assert_rank_eligible(get("two_phase.chf.shah_1987"))


def test_f03_unimplemented_entry_cannot_pass_the_generic_eligibility_guard():
    """OTB-G001 F-03: an entry needing an evaluator is not eligible without one.

    Before the fix, ``shah_2015`` carried ``status=RESOLVED`` with ``evaluate=None``,
    a blank locator and an ambiguous citation, and still passed both
    ``rank_eligible`` and ``assert_rank_eligible`` -- the silently permissive generic
    path. Both must now refuse it.
    """
    entry = get("two_phase.chf.shah_2015")
    assert entry.status is Status.SOURCE_REQUIRED
    assert entry.rank_eligible is False
    with pytest.raises(NotRankEligibleError):
        assert_rank_eligible(entry)


def test_f03_the_reduced_pressure_band_moved_to_the_paper_it_belongs_to():
    """The 0.0014-0.96 band is Shah (1987)'s and is now attached only to it."""
    superseded = get("two_phase.chf.shah_2015")
    reference = get("two_phase.chf.shah_1987")

    assert superseded.domain.ranges == {}, (
        "the pr_reduced band was never shah_2015's; leaving it attached would keep "
        "asserting a validity range this entry has no claim to"
    )
    assert reference.domain.ranges["pr_reduced"] == (0.0014, 0.96)
    assert reference.status is Status.RESOLVED
    assert reference.evaluate is not None
    assert reference.source.locator.strip()


def test_f03_the_executable_form_rule_is_load_bearing_on_its_own():
    """The rule must bite even where status alone would not have blocked the entry.

    ``shah_2015`` is now also ``SOURCE_REQUIRED``, so its *status* already makes it
    ineligible -- which means it cannot demonstrate that the executable-form rule
    works. The mutation witness caught exactly that: disabling the rule left every
    shah_2015 test green. This test exercises the rule directly, on an entry that is
    RESOLVED and PUBLISHED and would otherwise rank.
    """
    import dataclasses

    from orbital_thermal.registry.applicability import Applicability

    would_otherwise_rank = dataclasses.replace(
        get("two_phase.chf.shah_1987"),
        evaluate=None,
        applicability_spec=Applicability(requires_executable_form=True),
    )
    assert would_otherwise_rank.status is Status.RESOLVED
    assert would_otherwise_rank.provenance.value == "published"
    assert would_otherwise_rank.rank_eligible is False, (
        "a RESOLVED, PUBLISHED entry that declares it needs an executable form must "
        "not rank while it has none -- status alone does not catch this"
    )

    # Control: the same entry WITH its evaluator ranks.
    with_evaluator = dataclasses.replace(
        would_otherwise_rank, evaluate=get("two_phase.chf.shah_1987").evaluate
    )
    assert with_evaluator.rank_eligible is True


def test_dir02_eligibility_requires_an_executable_form_generically():
    """DIR-02, closed at the boundary rather than by demoting one entry.

    OTB-G001 round 1 named this class and fixed it by moving one entry's status; the
    permissive rule stayed. DIR-02 is its third occurrence, so the rule itself changed:
    an entry that cannot supply an evaluated value is not rank-eligible, and the check
    is no longer opt-in via ``requires_executable_form``.

    "Can supply a value" spans a callable on the entry OR a named module
    implementation, which is what lets the rule be generic without demoting the B1
    entries whose executable form has always lived in a module. Those are the control:
    they were never unimplemented, only undocumented.
    """
    import dataclasses

    # Sibling 1 -- a RESOLVED, PUBLISHED entry with no executable form anywhere.
    stripped = dataclasses.replace(
        get("two_phase.chf.shah_1987"), evaluate=None, executable_form=""
    )
    assert stripped.status is Status.RESOLVED
    assert stripped.has_executable_form is False
    assert stripped.rank_eligible is False, (
        "status alone must no longer admit an entry that cannot supply a value"
    )
    with pytest.raises(NotRankEligibleError):
        assert_rank_eligible(stripped)

    # Sibling 2 -- the same entry with a module implementation named is admitted.
    elsewhere = dataclasses.replace(
        stripped, executable_form="orbital_thermal.registry.two_phase.shah_1987_chf"
    )
    assert elsewhere.has_executable_form is True
    assert elsewhere.rank_eligible is True

    # Control -- the two B1 entries evaluated by a module were never unimplemented,
    # and the generic rule must not sweep them up.
    for cid in ("thermal.spreading_resistance", "hydraulic.minor_losses"):
        entry = get(cid)
        assert entry.evaluate is None
        assert entry.executable_form, f"{cid} must record where its form lives"
        assert entry.rank_eligible is True, (
            f"{cid} is implemented in a module; the DIR-02 rule must not demote it"
        )


def test_dir02_no_entry_is_rank_eligible_without_an_executable_form():
    """The class-level statement: the property holds across the whole registry."""
    from orbital_thermal.registry import CORRELATIONS

    offenders = [
        c.id
        for c in list(CORRELATIONS) + list(TWO_PHASE_CORRELATIONS)
        if c.rank_eligible and not c.has_executable_form
    ]
    assert offenders == [], (
        f"these entries claim rank-eligibility but can supply no value: {offenders}"
    )


#: V-01 R1 regression. The class is *"the boundary admits a DECLARATION where the rule
#: needs a FACT"* -- DIR-02's own fix, one level down. Five sibling instances of a
#: declaration that cannot be honoured, plus the control that must survive.
@pytest.mark.parametrize(
    "declared,why",
    [
        ("x", "not a dotted path at all -- the single character the probe used"),
        ("orbital_thermal.no_such_module.no_such_fn", "well-formed, module absent"),
        ("orbital_thermal.solid_network.no_such_fn", "module exists, attribute absent"),
        (
            "orbital_thermal.registry.two_phase.CHISHOLM_C",
            "attribute exists but is a dict, not callable",
        ),
        ("os.path.join", "resolvable and callable, but outside the package"),
    ],
)
def test_v01_a_declaration_that_cannot_be_honoured_is_not_eligible(declared, why):
    """An entry may rank only if an executable form can actually be REACHED.

    Before this fix ``has_executable_form`` was ``bool(self.executable_form.strip())``,
    so any non-empty string admitted the entry. Nothing shipped broken -- both real
    declarations resolved -- but "the current entries happen to be correct" was the
    standard that let round-1 F-03 come back as DIR-02, and it is not the standard now.
    """
    import dataclasses

    entry = dataclasses.replace(
        get("two_phase.chf.shah_1987"), evaluate=None, executable_form=declared
    )
    assert entry.has_executable_form is False, why
    assert entry.rank_eligible is False, why
    with pytest.raises(NotRankEligibleError):
        assert_rank_eligible(entry)


def test_v01_control_the_module_implemented_b1_entries_still_rank():
    """The control that matters: the fix must not demote what it was built around."""
    for cid in ("thermal.spreading_resistance", "hydraulic.minor_losses"):
        entry = get(cid)
        assert entry.evaluate is None
        assert entry.has_executable_form is True, f"{cid} declaration must resolve"
        assert entry.rank_eligible is True


def test_v01_a_declaration_that_does_resolve_is_accepted():
    """The other control: a real module implementation is honoured."""
    import dataclasses

    entry = dataclasses.replace(
        get("two_phase.chf.shah_1987"),
        evaluate=None,
        executable_form="orbital_thermal.registry.two_phase.shah_1987_chf",
    )
    assert entry.has_executable_form is True
    assert entry.rank_eligible is True


def test_v01_every_shipped_declaration_resolves():
    """The loud half of the fix.

    ``has_executable_form`` fails CLOSED and says nothing, which is right at a boundary
    but useless as a diagnostic: a typo would silently de-rank an entry. This names the
    offender instead. Both halves ship because they do different jobs -- see
    ``OTB-G002_FIXES_REPORT.md`` for why neither alone was judged sufficient.
    """
    from orbital_thermal.registry import ALL_ENTRIES
    from orbital_thermal.registry.provenance import unresolved_executable_forms

    assert unresolved_executable_forms(ALL_ENTRIES) == []


def test_v01_the_reporter_actually_names_a_broken_declaration():
    """The reporter needs its own test, for the same reason the sweep above does.

    ``test_v01_every_shipped_declaration_resolves`` cannot witness the reporter while
    every shipped declaration resolves -- there is nothing for it to find, so breaking
    it changes nothing. The mutation harness caught that. This drives a synthetic
    broken declaration through it, which is the only way to hold the diagnostic.
    """
    import dataclasses

    from orbital_thermal.registry.provenance import unresolved_executable_forms

    base = get("two_phase.chf.shah_1987")
    broken = [
        dataclasses.replace(
            base, evaluate=None, executable_form="orbital_thermal.nope.nope"
        ),
        dataclasses.replace(base, evaluate=None, executable_form="os.path.join"),
    ]
    problems = unresolved_executable_forms(broken)
    assert len(problems) == 2
    assert any("does not resolve" in p for p in problems)
    assert any("outside" in p for p in problems)
    # ...and a healthy entry produces nothing.
    assert unresolved_executable_forms([get("thermal.spreading_resistance")]) == []


def test_v01_resolution_is_platform_independent():
    """R3: resolution must not depend on host import semantics.

    The same path resolves to the same object on repeat calls, and case is significant
    -- a filesystem that happens to be case-insensitive must not make
    ``ORBITAL_THERMAL...`` resolve.
    """
    from orbital_thermal.registry.provenance import resolve_executable_form

    path = "orbital_thermal.solid_network.spreading_resistance"
    first = resolve_executable_form(path)
    assert first is not None and callable(first)
    assert resolve_executable_form(path) is first, "resolution must be stable/cached"
    assert resolve_executable_form(path.upper()) is None
    assert resolve_executable_form("") is None
    assert resolve_executable_form("   ") is None


def test_dir02_the_vocabulary_splits_resolved_from_implemented():
    """``RESOLVED`` stopped carrying two meanings (the vocabulary half of DIR-02)."""
    assert hasattr(Status, "IMPLEMENTATION_REQUIRED")
    assert Status.IMPLEMENTATION_REQUIRED.value == "implementation_required"

# --- completeness / structural checker ------------------------------------------


def test_missing_metadata_is_empty_for_the_registry():
    assert missing_metadata(TWO_PHASE_CORRELATIONS + TWO_PHASE_PROPERTIES) == []


def test_missing_metadata_flags_a_broken_entry():
    import dataclasses

    # Deliberately break a RESOLVED HTC entry: drop its source AND its gravity metadata.
    gw = get("two_phase.htc.gungor_winterton")
    broken = dataclasses.replace(
        gw,
        source=None,
        microgravity_validated=None,
        gravity_basis="",
        rank_scope="",
        limitation="",
    )
    problems = missing_metadata([broken])
    assert problems, "a broken entry must be structurally rejected"
    assert any(broken.id in p for p in problems)
