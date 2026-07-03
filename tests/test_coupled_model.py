"""B4 coupled steady-state tests: the R1-R5 residual system (4.1a), two-direction baseline
recovery (Modes T and A vs Phase A), energy closure, nondimensional convergence, feasibility
gates, failure states, and per-face C1/C2 contracts (C3 parametric-only). CoolProp-gated where
the coupled loop evaluates properties."""

from __future__ import annotations

import pytest

from orbital_thermal import coupled_model as cm
from orbital_thermal import radiation
from orbital_thermal.coupled_model import Contract, RadiatorFace, RadiatorSpec
from orbital_thermal.registry import NotRankEligibleError
from orbital_thermal.solid_network import build_ranked_path, build_sensitivity_path

C1 = RadiatorSpec(faces=(RadiatorFace(2.0, 250.0),), emissivity=0.9, contract=Contract.C1)
C2 = RadiatorSpec(faces=(RadiatorFace(1.0, 250.0),), emissivity=0.9, contract=Contract.C2)


def _ranked_path(**over):
    kw = dict(
        material="aluminum", length_m=0.002, area_m2=5.0e-3, source_radius_m=8.0e-3,
        plate_radius_m=0.03, thickness_m=8.0e-3, contact_conductance_W_m2K=2.0e4,
        contact_source="Madhusudana 1996 (test)",
    )
    kw.update(over)
    return build_ranked_path(**kw)


def _common(**over):
    kw = dict(
        coolant="ammonia", mass_flow_kg_s=0.05, tube_diameter_m=0.004, loop_length_m=2.0,
        coldplate_wetted_area_m2=0.05, radiator_wetted_area_m2=4.0, low_side_pressure_Pa=20.0e5,
    )
    kw.update(over)
    return kw


# --- radiator law: pure algebra, no CoolProp ------------------------------------


class TestRadiatorLaw:
    def test_temperature_matches_phase_a_single_sink(self):
        # C1 with area_fraction 2.0 => A_emit = 2*A_plan; must equal the Phase A inverse law.
        t = cm.radiator_temperature(1200.0, 2.0, C1)
        expect = cm.phase_a_baseline_temperature(1200.0, 4.0, 0.9, 250.0)
        assert t == pytest.approx(expect, rel=1e-12)

    def test_area_matches_required_area(self):
        a_emit = cm.radiator_area(1200.0, 314.0, C1) * C1.total_area_fraction
        assert a_emit == pytest.approx(radiation.required_area(1200.0, 314.0, 0.9, 250.0), rel=1e-12)

    def test_temperature_area_round_trip(self):
        a = cm.radiator_area(1500.0, 320.0, C2)
        assert cm.radiator_temperature(1500.0, a, C2) == pytest.approx(320.0, rel=1e-10)

    def test_phase_a_baseline_area_wrapper(self):
        assert cm.phase_a_baseline_area(1000.0, 310.0, 0.9, 250.0) == pytest.approx(
            radiation.required_area(1000.0, 310.0, 0.9, 250.0), rel=1e-12)

    def test_unequal_face_sinks_sum(self):
        spec = RadiatorSpec(
            faces=(RadiatorFace(1.0, 240.0), RadiatorFace(1.0, 260.0)),
            emissivity=0.9, contract=Contract.C1)
        q = cm._radiator_rejection(320.0, 3.0, spec)
        manual = 0.9 * cm.SIGMA_SB * 3.0 * ((320.0**4 - 240.0**4) + (320.0**4 - 260.0**4))
        assert q == pytest.approx(manual, rel=1e-12)

    def test_area_raises_when_radiator_below_sink(self):
        with pytest.raises(cm.FeasibilityError):
            cm.radiator_area(1000.0, 240.0, C1)  # 240 < 250 K sink


class TestContracts:
    def test_c2_requires_single_face(self):
        with pytest.raises(ValueError, match="exactly one"):
            RadiatorSpec(faces=(RadiatorFace(1.0, 250.0), RadiatorFace(1.0, 250.0)),
                         emissivity=0.9, contract=Contract.C2)

    def test_c3_without_solar_flux_blocks_ranking(self):
        with pytest.raises(NotRankEligibleError, match="alpha_s"):
            RadiatorSpec(faces=(RadiatorFace(1.0, 250.0),), emissivity=0.9, contract=Contract.C3)

    def test_shielded_contract_rejects_solar_flux(self):
        with pytest.raises(ValueError, match="C3"):
            RadiatorSpec(faces=(RadiatorFace(1.0, 250.0, parametric_solar_flux_W_m2=100.0),),
                         emissivity=0.9, contract=Contract.C1)

    def test_negative_solar_flux_rejected(self):
        with pytest.raises(ValueError):
            RadiatorFace(1.0, 250.0, parametric_solar_flux_W_m2=-5.0)

    def test_rank_eligibility_by_contract(self):
        assert C1.rank_eligible and C2.rank_eligible
        c3 = RadiatorSpec(faces=(RadiatorFace(1.0, 250.0, parametric_solar_flux_W_m2=150.0),),
                          emissivity=0.9, contract=Contract.C3)
        assert not c3.rank_eligible


class TestRankEligibilityInheritance:
    def test_ranked_case_passes(self):
        cm.assert_case_rank_eligible("ammonia", _ranked_path(), C1)  # must not raise

    def test_blocked_coolant_raises(self):
        with pytest.raises(NotRankEligibleError):
            cm.assert_case_rank_eligible("co2", _ranked_path(), C1)

    def test_sensitivity_solid_path_raises(self):
        sens = build_sensitivity_path(
            k_W_mK=1500.0, length_m=0.002, area_m2=5e-3, source_radius_m=8e-3,
            plate_radius_m=0.03, thickness_m=8e-3, contact_conductance_W_m2K=2e4)
        with pytest.raises(NotRankEligibleError):
            cm.assert_case_rank_eligible("ammonia", sens, C1)

    def test_c3_contract_not_rank_eligible(self):
        c3 = RadiatorSpec(faces=(RadiatorFace(1.0, 250.0, parametric_solar_flux_W_m2=150.0),),
                          emissivity=0.9, contract=Contract.C3)
        with pytest.raises(NotRankEligibleError):
            cm.assert_case_rank_eligible("ammonia", _ranked_path(), c3)


class TestArgumentValidation:
    # these raise before any CoolProp property evaluation
    def test_mode_t_requires_area(self):
        with pytest.raises(ValueError, match="radiator_area_m2"):
            cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(),
                             radiator=C1, ranked=False, **_common())

    def test_mode_a_requires_temperature(self):
        with pytest.raises(ValueError, match="radiator_temperature_K"):
            cm.solve_coupled(mode="A", q_compute_W=1200.0, solid_path=_ranked_path(),
                             radiator=C1, ranked=False, **_common())

    def test_unknown_coolant_raises(self):
        with pytest.raises(NotRankEligibleError):
            cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(),
                             radiator=C1, radiator_area_m2=2.0, ranked=False,
                             **_common(coolant="mercury"))

    def test_ranked_co2_rejected_before_solving(self):
        with pytest.raises(NotRankEligibleError):
            cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(),
                             radiator=C1, radiator_area_m2=2.0, ranked=True,
                             **_common(coolant="co2"))


# --- coupled solve: needs CoolProp for loop properties --------------------------

pytest.importorskip("CoolProp", reason="CoolProp not installed")


class TestBaselineRecovery:
    # two separate tests, per B0 plan Section 5.
    def test_mode_t_recovers_phase_a_temperature(self):
        r = cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(), radiator=C1,
                             radiator_area_m2=2.0, neglect_transport_losses=True, ranked=False,
                             **_common())
        expect = cm.phase_a_baseline_temperature(1200.0, 4.0, 0.9, 250.0)
        assert r.T_rad_K == pytest.approx(expect, rel=1e-9)
        # with transport off, every node collapses onto T_rad
        assert r.T_j_K == pytest.approx(r.T_rad_K, rel=1e-9)

    def test_mode_a_recovers_phase_a_area(self):
        r = cm.solve_coupled(mode="A", q_compute_W=1200.0, solid_path=_ranked_path(), radiator=C1,
                             radiator_temperature_K=314.0, neglect_transport_losses=True,
                             ranked=False, **_common())
        assert r.A_emit_m2 == pytest.approx(
            radiation.required_area(1200.0, 314.0, 0.9, 250.0), rel=1e-9)


class TestCoupledSolve:
    def test_full_transport_converges_and_closes(self):
        r = cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(), radiator=C1,
                             radiator_area_m2=2.0, ranked=True, **_common())
        assert r.converged and r.feasible
        assert r.residual_norm < 1e-10
        assert r.energy_closure_rel < 1e-10
        assert r.T_j_K >= r.T_w_K >= r.mean_fluid_K >= r.T_rad_K
        assert r.T2_K > r.T1_K

    def test_pump_heat_adds_to_rejected_load(self):
        r = cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(), radiator=C1,
                             radiator_area_m2=2.0, ranked=True, **_common())
        assert r.Q_rad_W > r.Q_chip_W
        assert r.Q_rad_W == pytest.approx(r.Q_chip_W + r.Q_pump_fluid_W, rel=1e-12)

    def test_mode_t_and_mode_a_are_consistent(self):
        rt = cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(), radiator=C1,
                              radiator_area_m2=2.0, ranked=True, **_common())
        ra = cm.solve_coupled(mode="A", q_compute_W=1200.0, solid_path=_ranked_path(), radiator=C1,
                              radiator_temperature_K=rt.T_rad_K, ranked=True, **_common())
        assert ra.A_plan_m2 == pytest.approx(2.0, rel=1e-6)

    def test_residuals_vanish_at_solution(self):
        r = cm.solve_coupled(mode="T", q_compute_W=900.0, solid_path=_ranked_path(), radiator=C2,
                             radiator_area_m2=3.0, ranked=True, **_common())
        assert r.residual_norm < 1e-10


class TestFeasibilityGates:
    def test_junction_limit_rejects_ranked_but_flags_sensitivity(self):
        base = cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(),
                                radiator=C1, radiator_area_m2=2.0, ranked=False, **_common())
        tj = base.T_j_K
        # a limit above T_j passes; below T_j rejects a ranked case
        ok = cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(), radiator=C1,
                              radiator_area_m2=2.0, ranked=True, t_junction_max_K=tj + 10.0,
                              **_common())
        assert ok.feasible
        with pytest.raises(cm.FeasibilityError):
            cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(), radiator=C1,
                             radiator_area_m2=2.0, ranked=True, t_junction_max_K=tj - 10.0,
                             **_common())
        flagged = cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(),
                                   radiator=C1, radiator_area_m2=2.0, ranked=False,
                                   t_junction_max_K=tj - 10.0, **_common())
        assert not flagged.feasible and not flagged.feasibility["junction_within_limit"]

    def test_underpressure_rejected_when_ranked(self):
        # huge required subcooling margin makes P_lo - P_sat insufficient
        flagged = cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(),
                                   radiator=C1, radiator_area_m2=2.0, ranked=False,
                                   subcooling_margin_Pa=1.0e7, **_common())
        assert not flagged.feasibility["pressure_above_saturation"]
        with pytest.raises(cm.FeasibilityError):
            cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(), radiator=C1,
                             radiator_area_m2=2.0, ranked=True, subcooling_margin_Pa=1.0e7,
                             **_common())

    def test_radiator_below_sink_fails_loudly(self):
        with pytest.raises(cm.FeasibilityError):
            cm.solve_coupled(mode="A", q_compute_W=1200.0, solid_path=_ranked_path(), radiator=C1,
                             radiator_temperature_K=240.0, ranked=False, **_common())


class TestFailureStates:
    def test_nonconvergence_raises(self):
        with pytest.raises(cm.ConvergenceError):
            cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(), radiator=C1,
                             radiator_area_m2=2.0, ranked=False, max_iter=1, multistart=False,
                             **_common())

    def test_supercritical_seed_does_not_create_a_branch(self):
        # a healthy case still solves (multi-start with the domain guard rejects the spurious
        # supercritical root instead of raising BranchError)
        r = cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(), radiator=C1,
                             radiator_area_m2=2.0, ranked=True, multistart=True, **_common())
        assert r.converged


class TestPumpBoundary:
    def test_fluid_loop_boundary_closure(self):
        r = cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(), radiator=C1,
                             radiator_area_m2=2.0, boundary="fluid_loop", ranked=True, **_common())
        assert r.pump.boundary == "fluid_loop"
        assert r.Q_rad_W == pytest.approx(r.Q_chip_W + r.pump.fluid_heat_W, rel=1e-12)

    def test_whole_spacecraft_boundary_label_carried(self):
        r = cm.solve_coupled(mode="T", q_compute_W=1200.0, solid_path=_ranked_path(), radiator=C1,
                             radiator_area_m2=2.0, boundary="whole_spacecraft", ranked=True,
                             **_common())
        assert r.pump.boundary == "whole_spacecraft"
        assert r.pump.electrical_power_W > r.pump.fluid_heat_W
