"""B5 architecture-case tests: gate-driven classification of the 16-combo case space, the
Stage-1 common-envelope ranked cases, sensitivity handling (never ranked), REJECTED-by-physics,
and the modeled component mass (4.6 / 4.8a). Classification is CoolProp-free; solving is gated."""

from __future__ import annotations

import pytest

from orbital_thermal import architecture_cases as ac
from orbital_thermal.architecture_cases import Classification as C
from orbital_thermal.architecture_cases import Reason, Stage1Envelope
from orbital_thermal.coupled_model import Contract, RadiatorFace, RadiatorSpec

ENV = Stage1Envelope()


# --- classification: pure gates, no CoolProp -------------------------------------


class TestClassification:
    def test_coolant_verdicts(self):
        assert ac._coolant_verdict("ammonia") == (None, None)
        assert ac._coolant_verdict("water") == (None, None)
        assert ac._coolant_verdict("co2")[0] is C.SENSITIVITY_ONLY
        assert ac._coolant_verdict("pgw")[0] is C.SOURCE_REQUIRED

    def test_material_verdicts(self):
        assert ac._material_verdict(ENV, "aluminum") == (None, None)
        assert ac._material_verdict(ENV, "copper") == (None, None)
        assert ac._material_verdict(ENV, "apg")[0] is C.SOURCE_REQUIRED
        assert ac._material_verdict(ENV, "diamond_composite")[0] is C.SOURCE_REQUIRED

    def test_four_combos_are_provenance_eligible(self):
        for c in ("ammonia", "water"):
            for m in ("aluminum", "copper"):
                cls, reasons = ac.classify_provenance(ENV, c, m)
                assert cls is None and reasons == ()

    def test_twelve_combos_are_blocked_with_reasons(self):
        blocked = 0
        for c in ac.COOLANTS:
            for m in ac.MATERIALS:
                cls, reasons = ac.classify_provenance(ENV, c, m)
                if cls is not None:
                    blocked += 1
                    assert reasons  # at least one reason code
        assert blocked == 12

    def test_multi_reason_cell_carries_all_codes(self):
        cls, reasons = ac.classify_provenance(ENV, "co2", "apg")
        assert cls is C.SENSITIVITY_ONLY  # coolant (permanent) precedence over source-required
        assert Reason.COOLANT_BACKEND_BLOCKED in reasons
        assert Reason.MATERIAL_ANISOTROPIC_SOURCE_REQUIRED in reasons

    def test_c3_contract_unsupported(self):
        c3 = RadiatorSpec(faces=(RadiatorFace(1.0, 250.0, parametric_solar_flux_W_m2=150.0),),
                          emissivity=0.9, contract=Contract.C3)
        assert ac._contract_verdict(c3) == (C.UNSUPPORTED, Reason.CONTRACT_C3_UNSUPPORTED)

    def test_c2_without_evidence_source_required(self):
        c2 = RadiatorSpec(faces=(RadiatorFace(1.0, 250.0),), emissivity=0.9, contract=Contract.C2)
        assert ac._contract_verdict(c2) == (C.SOURCE_REQUIRED, Reason.CONTRACT_C2_SOURCE_REQUIRED)


# --- containment mass: pure math, no CoolProp ------------------------------------


class TestContainmentMass:
    def test_thin_wall_regime_and_lower_bound_label(self):
        comp = ac.containment_ideal_shell(21.0e5, 0.002, 2.0, 2700.0, 138.0e6)
        assert comp.included and comp.mass_kg > 0
        assert comp.completeness == "lower-bound"
        assert "thin-wall" in comp.note and "ideal-shell lower bound" in comp.note

    def test_thick_wall_regime_when_r_over_t_small(self):
        # P_g between sigma/10 and sigma forces r/t < 10 -> Lame thick-wall
        comp = ac.containment_ideal_shell(50.0e6, 0.002, 2.0, 2700.0, 138.0e6)
        assert "Lame thick-wall" in comp.note


# --- solving / matrix: CoolProp-gated --------------------------------------------

pytest.importorskip("CoolProp", reason="CoolProp not installed")


class TestMatrix:
    def test_summary_counts_16_4_12(self):
        s = ac.matrix_summary(ac.build_case_matrix(ENV))
        assert s["total"] == 16
        assert s["rank_eligible"] == 4
        assert s["non_ranked"] == 12
        assert s["sensitivity_only"] == 4      # CO2 x 4
        assert s["source_required"] == 8       # PGW x 4 + anisotropic x 4
        assert s["rejected"] == 0 and s["unsupported"] == 0

    def test_rank_eligible_cases_are_feasible(self):
        ranked = ac.ranked_cases(ac.build_case_matrix(ENV))
        assert len(ranked) == 4
        for r in ranked:
            assert r.rank_eligible and r.evaluated and r.coupled.feasible
            assert r.coolant in ("ammonia", "water") and r.material in ("aluminum", "copper")

    def test_copper_gives_more_junction_margin_than_aluminum(self):
        al = ac.evaluate_case(ENV, "ammonia", "aluminum")
        cu = ac.evaluate_case(ENV, "ammonia", "copper")
        assert cu.coupled.T_j_K < al.coupled.T_j_K


class TestSensitivity:
    def test_apg_runs_only_with_parametric_k_and_is_never_ranked(self):
        classified = ac.evaluate_case(ENV, "ammonia", "apg")
        assert not classified.evaluated and not classified.rank_eligible
        run = ac.evaluate_case(ENV, "ammonia", "apg", parametric_conductivity_W_mK=1500.0,
                               parametric_note="APG in-plane bound (uncited sensitivity)")
        assert run.evaluated and not run.rank_eligible
        assert run.classification is C.SOURCE_REQUIRED

    def test_co2_and_pgw_not_evaluable_even_with_parametric_k(self):
        for c in ("co2", "pgw"):
            r = ac.evaluate_case(ENV, c, "aluminum", parametric_conductivity_W_mK=1500.0)
            assert not r.evaluated


class TestRejectedByPhysics:
    def test_tight_spreader_rejected_by_junction_limit(self):
        tight = Stage1Envelope(source_radius_m=0.008, plate_radius_m=0.03, thickness_m=0.008)
        r = ac.evaluate_case(tight, "ammonia", "aluminum")
        assert r.classification is C.REJECTED
        assert Reason.JUNCTION_LIMIT_FAILURE in r.reason_codes
        assert not r.rank_eligible


class TestModeledMass:
    def test_components_and_incomplete_label(self):
        r = ac.evaluate_case(ENV, "ammonia", "aluminum")
        m = r.mass
        assert m.total_modeled_kg > 0
        assert m.label == "modeled component mass (incomplete Stage-1 accounting)"
        names = {c.name for c in m.components}
        assert "coolant inventory (tube)" in names
        assert "tube containment shell" in names
        assert "radiator panel" in names

    def test_named_exclusions_present(self):
        r = ac.evaluate_case(ENV, "ammonia", "aluminum")
        for excluded in ("pump", "motor", "accumulator", "manifolds", "redundancy"):
            assert excluded in r.mass.excluded_components

    def test_copper_solid_mass_exceeds_aluminum(self):
        al = ac.evaluate_case(ENV, "ammonia", "aluminum").mass.total_modeled_kg
        cu = ac.evaluate_case(ENV, "ammonia", "copper").mass.total_modeled_kg
        assert cu > al  # copper is denser
