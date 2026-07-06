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


def test_no_evaluate_callable_in_s1():
    # S1 is registry-only: no correlation may carry an executable form yet.
    for c in TWO_PHASE_CORRELATIONS:
        assert c.evaluate is None, f"{c.id} must not have an evaluate callable in S1"


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
