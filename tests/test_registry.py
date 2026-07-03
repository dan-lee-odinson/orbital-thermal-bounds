"""B1 registry tests: framework rules, no-invention integrity, rank-eligibility
enforcement, executable correlations, and CoolProp re-derivation of the pinned
coolant values.

ORACLE-FREEZE RULE applies to the DERIVED coolant values: the registry literals
are the CoolProp 7.2.0 reference-state outputs and are never edited to make a
failing test pass -- if CoolProp disagrees, the registry (or the pin) is wrong.
"""

from __future__ import annotations

import pytest

from orbital_thermal import registry
from orbital_thermal.registry import (
    NotRankEligibleError,
    Provenance,
    Status,
    assert_in_domain,
    assert_rank_eligible,
)
from orbital_thermal.registry.correlations import (
    friction_blasius,
    friction_haaland,
    friction_laminar,
    nusselt_dittus_boelter,
    nusselt_gnielinski,
)


class TestFrameworkRules:
    def test_resolved_published_with_value_is_rank_eligible(self):
        e = registry.get("solid.copper.thermal_conductivity")
        assert e.provenance is Provenance.PUBLISHED
        assert e.status is Status.RESOLVED
        assert e.rank_eligible

    def test_sensitivity_is_not_rank_eligible(self):
        assert not registry.get("coolant.co2.loop_use").rank_eligible

    def test_source_required_is_not_rank_eligible(self):
        assert not registry.get("containment.al6061t6.allowable_stress").rank_eligible

    def test_missing_value_is_not_rank_eligible(self):
        # even PUBLISHED would fail with no value; PGW is ASSUMED + SOURCE_REQUIRED
        assert registry.get("coolant.pgw.concentration").value is None
        assert not registry.get("coolant.pgw.concentration").rank_eligible

    def test_domain_contains_and_out_of_domain(self):
        c = registry.get("friction.laminar")
        assert c.domain.contains(Re=1500.0)
        assert not c.domain.contains(Re=5000.0)
        assert c.domain.out_of_domain(Re=5000.0)  # non-empty reason list


class TestNoInventionIntegrity:
    def test_ids_are_unique(self):
        ids = [e.id for e in registry.ALL_ENTRIES]
        assert len(ids) == len(set(ids))

    def test_every_entry_has_provenance_and_status(self):
        for e in registry.ALL_ENTRIES:
            assert isinstance(e.provenance, Provenance)
            assert isinstance(e.status, Status)

    def test_resolved_property_has_a_value(self):
        # a RESOLVED *property* must carry a value (no silent None passing as resolved)
        for e in registry.PROPERTIES:
            if e.status is Status.RESOLVED:
                assert e.value is not None, e.id

    def test_non_resolved_is_never_rank_eligible(self):
        for e in registry.ALL_ENTRIES:
            if e.status is not Status.RESOLVED:
                assert not e.rank_eligible, e.id

    def test_unsupported_provenance_never_rank_eligible(self):
        for e in registry.ALL_ENTRIES:
            if e.provenance in (Provenance.SENSITIVITY, Provenance.UNSUPPORTED):
                assert not e.rank_eligible, e.id


class TestRankEligibilityEnforcement:
    def test_co2_loop_use_blocks_ranking(self):
        with pytest.raises(NotRankEligibleError):
            assert_rank_eligible(registry.get("coolant.co2.loop_use"), context="B5")

    @pytest.mark.parametrize(
        "entry_id",
        [
            "coolant.pgw.concentration",
            "solid.apg.in_plane_conductivity",
            "solid.diamond_composite.thermal_conductivity",
            "containment.al6061t6.allowable_stress",
            "thermal.contact_resistance",
            "hydraulic.maldistribution_allowance",
            "nusselt.developing_entry_length",
        ],
    )
    def test_blocked_entries_raise(self, entry_id):
        with pytest.raises(NotRankEligibleError):
            assert_rank_eligible(registry.get(entry_id))

    @pytest.mark.parametrize(
        "entry_id",
        [
            "coolant.ammonia.density",
            "coolant.water.density",
            "solid.aluminum.thermal_conductivity",
            "solid.copper.thermal_conductivity",
            "friction.laminar",
            "nusselt.gnielinski",
        ],
    )
    def test_rank_eligible_entries_pass(self, entry_id):
        assert_rank_eligible(registry.get(entry_id))  # must not raise

    def test_out_of_domain_raises(self):
        c = registry.get("friction.laminar")
        assert_in_domain(c, Re=1500.0)  # ok
        with pytest.raises(NotRankEligibleError):
            assert_in_domain(c, Re=5000.0)  # laminar corr used in turbulent range


class TestExecutableCorrelations:
    def test_friction_laminar_exact(self):
        assert friction_laminar(2000.0) == pytest.approx(0.032, rel=1e-9)

    def test_blasius_positive_and_decreasing(self):
        assert friction_blasius(1.0e4) > friction_blasius(1.0e5) > 0.0

    def test_haaland_smooth_matches_order_of_magnitude(self):
        f = friction_haaland(1.0e5, 0.0)
        assert 0.01 < f < 0.03

    def test_dittus_boelter_known_value(self):
        # 0.023 * 1e4^0.8 * 5^0.4
        assert nusselt_dittus_boelter(1.0e4, 5.0, heating=True) == pytest.approx(69.0, rel=0.02)

    def test_gnielinski_exceeds_laminar_floor(self):
        assert nusselt_gnielinski(1.0e4, 5.0) > 4.36

    def test_laminar_nusselt_constants(self):
        assert registry.get("nusselt.laminar_const_q").evaluate() == pytest.approx(4.36)
        assert registry.get("nusselt.laminar_const_Ts").evaluate() == pytest.approx(3.66)


class TestSummary:
    def test_summary_totals(self):
        s = registry.summary()
        assert s["total"] == len(registry.ALL_ENTRIES)
        assert s["rank_eligible"] == len(registry.rank_eligible_entries())
        assert s["rank_eligible"] < s["total"]  # honest gaps exist


# --- CoolProp re-derivation of the pinned DERIVED coolant values ----------------

CoolProp = pytest.importorskip("CoolProp", reason="CoolProp not installed")
from CoolProp.CoolProp import PropsSI  # noqa: E402

_TREF = 300.0
_DERIVED = {
    "coolant.ammonia.density": ("D", "Ammonia"),
    "coolant.ammonia.specific_heat": ("C", "Ammonia"),
    "coolant.ammonia.thermal_conductivity": ("L", "Ammonia"),
    "coolant.ammonia.viscosity": ("V", "Ammonia"),
    "coolant.water.density": ("D", "Water"),
    "coolant.water.specific_heat": ("C", "Water"),
    "coolant.water.thermal_conductivity": ("L", "Water"),
    "coolant.water.viscosity": ("V", "Water"),
}


class TestCoolPropReDerivation:
    @pytest.mark.parametrize("entry_id, spec", sorted(_DERIVED.items()))
    def test_registry_value_matches_coolprop(self, entry_id, spec):
        prop, fluid = spec
        expected = PropsSI(prop, "T", _TREF, "Q", 0, fluid)  # saturated liquid
        assert registry.get(entry_id).value == pytest.approx(expected, rel=1e-4)

    def test_co2_critical_point_matches(self):
        assert registry.get("coolant.co2.critical_temperature").value == pytest.approx(
            PropsSI("Tcrit", "CO2"), rel=1e-4
        )
        assert registry.get("coolant.co2.critical_pressure").value == pytest.approx(
            PropsSI("pcrit", "CO2"), rel=1e-4
        )
