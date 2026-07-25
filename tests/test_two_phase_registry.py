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

_REFERENCE_IDS = [
    "two_phase.htc.gungor_winterton",
    "two_phase.dp.lockhart_martinelli_chisholm",
    "two_phase.chf.shah_2015",
]
_NON_RANKABLE_IDS = [
    "two_phase.htc.chen",
    "two_phase.htc.shah_2022",
    "two_phase.onb.bergles_rohsenow",
    "two_phase.dp.friedel",
    "two_phase.dp.muller_steinhagen_heck",
    "two_phase.chf.shah_1987",
    "two_phase.chf.katto_ohno",
    "two_phase.pump.npsh",
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
S2_IMPLEMENTED_IDS = frozenset({"two_phase.htc.gungor_winterton"})


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


def test_s3_pressure_drop_entries_are_not_implemented_early():
    """The S3 / OTB-G002 pressure-drop work must not leak into this build."""
    for c in TWO_PHASE_CORRELATIONS:
        if c.kind == "dp":
            assert c.evaluate is None, (
                f"{c.id} is pressure drop, which belongs to S3 / OTB-G002; "
                "it must not carry an executable form in S2"
            )


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
    """The converse: nothing unconsulted acquires a locator (T8 is bounded)."""
    for c in TWO_PHASE_CORRELATIONS:
        if c.evaluate is None:
            assert not c.source.locator.strip(), (
                f"{c.id} has no executable form, so no paper was consulted for a "
                "formula from it; its locator must stay blank rather than be filled "
                "in speculatively"
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


def test_assert_rank_eligible_raises_on_npsh():
    npsh = get("two_phase.pump.npsh")
    with pytest.raises(NotRankEligibleError):
        assert_rank_eligible(npsh)


def test_assert_rank_eligible_passes_on_reference():
    # A rank-eligible reference must not raise.
    assert_rank_eligible(get("two_phase.chf.shah_2015"))


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
