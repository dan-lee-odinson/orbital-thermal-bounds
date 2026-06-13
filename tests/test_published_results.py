"""Published-results regression suite.

Encodes every central numerical claim of both preprints as a test against
the orbital_thermal package:

  Theory:    "Thermodynamic Bounds and Mass-Trade Criteria for Heat
             Rejection in Orbital Data Centers" (doi:10.5281/zenodo.20650893)
  Companion: "The AI1 Design Point" (doi:10.5281/zenodo.20670772)

Tolerance policy (documented, not incidental):
  * Exact algebraic identities -> rel=1e-12.
  * Iterative results -> the published suites' enforced tolerances
    (fixed point to 1e-10 K; dimensionless quintic residual < 1e-12).
  * Published display values -> the same absolute tolerances asserted in
    verify_suite.py / companion/verify_ai1.py, cited per test.

ORACLE-FREEZE RULE: the expected values below come from the published,
DOI-stamped papers and their verification suites. They are never edited to
make a failing test pass. A failure here means the package is wrong (or a
deliberate, documented model revision is underway) -- nothing else.
"""

from fractions import Fraction

import pytest

from orbital_thermal import (
    SIGMA_SB,
    area_ratio,
    carnot_cop_cooling,
    conversion_area_penalty,
    equilibrium_temperature,
    fixed_work_area_per_watt,
    heat_pump_area_ratio,
    heat_pump_overhead,
    heating_cop,
    net_flux,
    nonzero_sink_optimum,
    optimal_cold_fraction,
    quintic_residual,
    radiative_capacity,
    recirculation_amplification,
    required_area,
)

# ==========================================================================
# Theory paper -- Lemma 1 and Corollaries 1.1 / 1.2
# ==========================================================================


class TestAreaLaw:
    def test_corollary_1_1_zero_sink_estimate(self):
        # R0 = (600/293)^4 = 17.585
        assert (600.0 / 293.0) ** 4 == pytest.approx(17.585, abs=0.01)

    def test_corollary_1_1_exact_ratio_is_exact_rational(self):
        # (600^4 - 220^4) / (293^4 - 220^4) reduces to 6697760000/264604779.
        exact = Fraction(600**4 - 220**4, 293**4 - 220**4)
        assert exact == Fraction(6697760000, 264604779)
        assert area_ratio(293.0, 600.0, 220.0) == pytest.approx(
            float(exact), rel=1e-12
        )
        assert float(exact) == pytest.approx(25.312, abs=0.01)

    def test_corollary_1_1_direction_of_error(self):
        # Exact is 43.9% ABOVE the zero-sink estimate; the estimate is
        # 30.5% BELOW the exact. Direction matters (verify_suite B1).
        R = area_ratio(293.0, 600.0, 220.0)
        R0 = (600.0 / 293.0) ** 4
        assert (R / R0 - 1.0) == pytest.approx(0.439, abs=0.005)
        assert (1.0 - R0 / R) == pytest.approx(0.305, abs=0.005)

    def test_corollary_1_1_safe_upper_bound(self):
        # (R/R0 - 1) < (Ts/T1)^4 / (1 - (Ts/T1)^4)
        R = area_ratio(293.0, 600.0, 220.0)
        R0 = (600.0 / 293.0) ** 4
        x = (220.0 / 293.0) ** 4
        assert (R / R0 - 1.0) < x / (1.0 - x)

    def test_corollary_1_2_megawatt_radiator(self):
        # 1 MW at 293 K, emissivity 0.91, zero sink: 2,630 m^2 emitting,
        # 1,315 m^2 two-sided planform (verify_suite B7 tolerances).
        A = required_area(1e6, 293.0, 0.91)
        assert A == pytest.approx(2630.0, abs=5.0)
        assert A / 2.0 == pytest.approx(1315.0, abs=3.0)


# ==========================================================================
# Theory paper -- Theorem 1 (non-attainability of sink-temperature Carnot)
# ==========================================================================


class TestTheorem1:
    def test_99_percent_worked_example(self):
        # T_h=300, T_c=3.0, T_s=2.7 K: eta = 99%, ~10.1 kW rejected per MW
        # of work, area ~6.4e9 m^2/MW -- finite but extreme (verify_suite B8).
        eta = 1.0 - 3.0 / 300.0
        assert eta == pytest.approx(0.99, abs=1e-9)
        Qc = 1e6 * 3.0 / (300.0 - 3.0)
        assert Qc == pytest.approx(10101.0, abs=1.0)
        A_per_W = fixed_work_area_per_watt(300.0, 3.0, 2.7)
        assert 6.0e9 < A_per_W * 1e6 < 7.0e9

    def test_divergence_toward_carnot_limit(self):
        # A/W grows without bound as T_c approaches T_sink from above.
        a1 = fixed_work_area_per_watt(300.0, 3.0, 2.7)
        a2 = fixed_work_area_per_watt(300.0, 2.701, 2.7)
        assert a2 > 100.0 * a1

    def test_divergence_toward_zero_work(self):
        # ...and as T_c approaches T_h (no work output).
        a1 = fixed_work_area_per_watt(300.0, 250.0, 2.7)
        a2 = fixed_work_area_per_watt(300.0, 299.999, 2.7)
        assert a2 > 100.0 * a1


# ==========================================================================
# Theory paper -- Theorem 2 (the 3/4 rule) and Corollary 2.1
# ==========================================================================


class TestTheorem2:
    def test_reversible_optimum_is_exactly_three_quarters(self):
        assert optimal_cold_fraction(1.0) == pytest.approx(0.75, abs=1e-9)

    def test_efficiency_ceiling_25_percent(self):
        y = optimal_cold_fraction(1.0)
        assert (1.0 - y) == pytest.approx(0.25, abs=1e-9)

    @pytest.mark.parametrize(
        "a, expected",
        [(1.0, 0.7500), (0.8, 0.7645), (0.5, 0.7808)],
    )
    def test_irreversibility_shifts_optimum_up(self, a, expected):
        # Handoff/preprint values to four decimals.
        assert optimal_cold_fraction(a) == pytest.approx(expected, abs=5e-5)

    def test_stationarity_function_is_strictly_increasing(self):
        # Uniqueness of the optimum: the stationarity function g(y) (d/dy log A/W)
        # is strictly increasing on (0,1) -- its decreasing first term is dominated
        # by 4/y^2 (audit re-review P3-b). One sign change => one root.
        import numpy as np

        def g(y, a):
            return a / (1.0 - a * (1.0 - y)) + 1.0 / (1.0 - y) - 4.0 / y

        for a in (0.5, 0.8, 1.0):
            gv = g(np.linspace(0.01, 0.99, 500), a)
            assert np.all(np.diff(gv) > 0)
            assert np.sum(np.diff(np.sign(gv)) != 0) == 1

    def test_second_order_condition(self):
        # The optimum is a strict minimum of the area-per-work objective.
        y = optimal_cold_fraction(1.0)

        def objective(yy):
            eta = 1.0 - yy
            return (1.0 - eta) / (eta * yy**4)

        assert objective(y - 1e-4) > objective(y)
        assert objective(y + 1e-4) > objective(y)


class TestCorollary21:
    def test_minimum_penalty_at_optimum(self):
        # Reversible, zero sink, at T_c = (3/4) T_h: penalty = (4/3)^3.
        penalty = conversion_area_penalty(600.0, 450.0, eta=0.25)
        assert penalty == pytest.approx((4.0 / 3.0) ** 3, rel=1e-12)
        assert penalty == pytest.approx(2.370, abs=0.001)

    def test_cubic_lower_bound(self):
        # (1 - eta)(T_h/T_c)^4 >= (T_h/T_c)^3 for any reversible engine
        # (eta = 1 - T_c/T_h), spot-checked across the range.
        for Tc in (300.0, 400.0, 450.0, 500.0, 550.0):
            eta = 1.0 - Tc / 600.0
            assert conversion_area_penalty(600.0, Tc, eta) >= (
                600.0 / Tc
            ) ** 3 * (1.0 - 1e-12)

    def test_irreversible_penalty_is_larger(self):
        # a = 0.8 at T_c = 450: (1 - 0.8*0.25)(600/450)^4 = 2.5284.
        penalty = conversion_area_penalty(600.0, 450.0, eta=0.8 * 0.25)
        assert penalty == pytest.approx(2.5284, abs=0.001)
        assert penalty > conversion_area_penalty(600.0, 450.0, eta=0.25)

    def test_nonzero_sink_strictly_exceeds_cubic_bound(self):
        penalty = conversion_area_penalty(600.0, 450.0, eta=0.25, T_sink=220.0)
        assert penalty > (600.0 / 450.0) ** 3


# ==========================================================================
# Theory paper -- Theorem 3 (nonzero-sink optimum, exact quintic)
# ==========================================================================


class TestTheorem3:
    def test_canonical_optimum_full_precision(self):
        # T_h = 600, T_s = 220: T_c* = 457.98675408138325 K.
        t = nonzero_sink_optimum(600.0, 220.0)
        assert t == pytest.approx(457.98675408138325, abs=1e-6)

    def test_quintic_residual_below_published_tolerance(self):
        t = nonzero_sink_optimum(600.0, 220.0)
        assert abs(quintic_residual(t, 600.0, 220.0)) < 1e-12

    @pytest.mark.parametrize(
        "T_sink, shift_pct",
        [
            (0.0, 0.0),
            (50.0, 0.0051),
            (100.0, 0.0810),
            (150.0, 0.4049),
            (200.0, 1.2381),
            (220.0, 1.7748),
            (225.0, 1.9300),
            (250.0, 2.8390),
        ],
    )
    def test_shift_table(self, T_sink, shift_pct):
        # Published eight-sink shift table (verify_suite B4, abs 0.001).
        t = nonzero_sink_optimum(600.0, T_sink)
        shift = 100.0 * (t - 450.0) / 450.0
        assert shift == pytest.approx(shift_pct, abs=0.001)

    def test_shift_identity_q4_over_3(self):
        # Fractional shift above (3/4) T_h is EXACTLY q^4/3, q = T_s/T_c*.
        for T_sink in (50.0, 150.0, 220.0, 250.0):
            t = nonzero_sink_optimum(600.0, T_sink)
            q = T_sink / t
            shift = (t - 450.0) / 450.0
            assert shift == pytest.approx(q**4 / 3.0, abs=1e-8)

    def test_fixed_point_contraction(self):
        # |Phi'| = 4q^4/(3 + q^4) < 1 at every tabulated sink.
        for T_sink in (50.0, 150.0, 220.0, 250.0):
            t = nonzero_sink_optimum(600.0, T_sink)
            q = T_sink / t
            assert 4.0 * q**4 / (3.0 + q**4) < 1.0

    def test_sub_two_percent_bound(self):
        # Shift <= 1.9216% for q <= 0.49.
        assert 100.0 * 0.49**4 / 3.0 == pytest.approx(1.9216003, abs=1e-6)
        assert 100.0 * 0.49**4 / 3.0 < 2.0

    def test_monotone_in_sink_temperature(self):
        values = [nonzero_sink_optimum(600.0, ts) for ts in (0, 100, 200, 250)]
        assert values == sorted(values)


class TestTheorem3NearSinkLimit:
    """Robustness near T_sink -> T_h (audit item 6).

    The fixed-point solver failed to converge for r = T_sink/T_h >~ 0.97; the
    bisection solver handles the whole open domain. These are not published
    anchors -- they assert solver validity, the exact shift identity, and basic
    physical bounds at high sink fractions.
    """

    @pytest.mark.parametrize("r", [0.9, 0.99, 0.999])
    def test_converges_and_residual_below_tolerance(self, r):
        T_h = 600.0
        T_sink = r * T_h
        t = nonzero_sink_optimum(T_h, T_sink)
        assert T_sink < t < T_h                       # physical bracket
        assert abs(quintic_residual(t, T_h, T_sink)) < 1e-12

    @pytest.mark.parametrize("r", [0.9, 0.99, 0.999])
    def test_shift_identity_holds_near_limit(self, r):
        # (T_c* - 3/4 T_h)/(3/4 T_h) == q^4/3 exactly, q = T_sink/T_c*.
        T_h = 600.0
        T_sink = r * T_h
        t = nonzero_sink_optimum(T_h, T_sink)
        q = T_sink / t
        assert (t - 450.0) / 450.0 == pytest.approx(q**4 / 3.0, abs=1e-9)

    def test_raises_on_iteration_exhaustion(self):
        # Cap exhaustion must raise, not silently return an unconverged midpoint.
        with pytest.raises(RuntimeError):
            nonzero_sink_optimum(600.0, 220.0, max_iter=1)

    def test_rejects_nonpositive_tol_and_max_iter(self):
        with pytest.raises(ValueError):
            nonzero_sink_optimum(600.0, 220.0, tol=0.0)
        with pytest.raises(ValueError):
            nonzero_sink_optimum(600.0, 220.0, max_iter=0)

    def test_monotone_through_high_sink(self):
        vals = [nonzero_sink_optimum(600.0, ts) for ts in (300, 540, 594, 599.4)]
        assert vals == sorted(vals)


# ==========================================================================
# Theory paper -- Theorem 4 (heat pump) and Theorem 5 (no self-powering)
# ==========================================================================


class TestTheorem4:
    def test_carnot_cop_at_353_to_520(self):
        assert carnot_cop_cooling(353.0, 520.0) == pytest.approx(
            2.1138, abs=1e-3
        )

    def test_cop_h_equals_cop_c_plus_one(self):
        cop_c = carnot_cop_cooling(353.0, 520.0)
        assert heating_cop(cop_c) == pytest.approx(520.0 / 167.0, rel=1e-12)

    def test_minimum_overhead(self):
        cop_c = carnot_cop_cooling(353.0, 520.0)
        assert heat_pump_overhead(cop_c) == pytest.approx(0.473, abs=0.001)

    def test_area_ratio_exact_and_zero_sink(self):
        # COP_c = 1.15, 353 -> 520 K: exact 0.348 with T_s = 220 K,
        # zero-sink approximation 0.397 (verify_suite B5).
        assert heat_pump_area_ratio(1.15, 353.0, 520.0, 220.0) == pytest.approx(
            0.348, abs=0.001
        )
        assert heat_pump_area_ratio(1.15, 353.0, 520.0) == pytest.approx(
            0.397, abs=0.001
        )


class TestBoundsPhysicalContracts:
    """Public bound APIs must reject thermodynamically impossible inputs
    (audit re-review P1-c)."""

    def test_conversion_penalty_rejects_super_carnot_eta(self):
        # Carnot ceiling for 600->450 K is 1 - 450/600 = 0.25; 0.9 is impossible.
        with pytest.raises(ValueError):
            conversion_area_penalty(600.0, 450.0, eta=0.9)

    def test_conversion_penalty_allows_reversible_boundary(self):
        # eta == 1 - T_c/T_h (reversible limit) is allowed and gives (4/3)^3.
        assert conversion_area_penalty(600.0, 450.0, eta=0.25) == pytest.approx(
            (4.0 / 3.0) ** 3, rel=1e-12)

    def test_heat_pump_rejects_super_carnot_cop(self):
        # Carnot cooling ceiling for 353->520 K is 353/167 ~ 2.114; COP=100 is impossible.
        with pytest.raises(ValueError):
            heat_pump_area_ratio(100.0, 353.0, 520.0)

    def test_heat_pump_requires_upward_lift(self):
        with pytest.raises(ValueError):
            heat_pump_area_ratio(1.0, 520.0, 353.0)   # T2 < T1, not a lift

    def test_heat_pump_allows_carnot_boundary(self):
        cop = carnot_cop_cooling(353.0, 520.0)        # exactly at the ceiling
        assert heat_pump_area_ratio(cop, 353.0, 520.0) > 0.0


class TestTheorem5:
    def test_amplification_at_25_percent(self):
        assert recirculation_amplification(0.25) == pytest.approx(
            4.0 / 3.0, rel=1e-12
        )


# ==========================================================================
# Companion paper -- "The AI1 Design Point" (verify_ai1.py blocks B1-B14)
# ==========================================================================

Q_PEAK, Q_SUST = 150e3, 120e3
A_PLAN, A_EMIT = 110.0, 220.0
EPS, T_S = 0.91, 220.0


class TestAI1OperatingPoints:
    def test_b1_exact_continuous_peak_hypothetical(self):
        T_pk = equilibrium_temperature(Q_PEAK, A_EMIT, EPS, T_S)
        assert T_pk == pytest.approx(353.1623423, abs=1e-6)

    def test_b5_all_four_operating_points(self):
        cases = [
            (Q_SUST, A_EMIT, 337.1004),   # sustained, two-sided (PRIMARY)
            (Q_PEAK, A_EMIT, 353.1623),   # continuous-peak hypothetical
            (Q_SUST, A_PLAN, 391.4652),   # sustained, one-sided
            (Q_PEAK, A_PLAN, 411.8443),   # continuous-peak, one-sided
        ]
        for Q, A, expected in cases:
            assert equilibrium_temperature(Q, A, EPS, T_S) == pytest.approx(
                expected, abs=1e-3
            )


class TestAI1StressTest:
    def test_b2_capacities_at_exact_peak_temperature(self):
        T_pk = equilibrium_temperature(Q_PEAK, A_EMIT, EPS, T_S)
        cases = [
            (0.91, 220.0, 150.0),
            (0.80, 220.0, 131.8681319),
            (0.91, 260.0, 124.7166261),
            (0.80, 260.0, 109.6409900),
        ]
        for eps, ts, expected_kW in cases:
            cap = radiative_capacity(T_pk, A_EMIT, eps, ts) / 1e3
            assert cap == pytest.approx(expected_kW, abs=1e-6)

    def test_b3_table3_one_decimal_display_policy(self):
        # The paper displays ONE decimal at the exact T_pk (exact-convention
        # rounding); the rounded values are part of the published record.
        T_pk = equilibrium_temperature(Q_PEAK, A_EMIT, EPS, T_S)
        assert round(radiative_capacity(T_pk, A_EMIT, 0.91, 220.0) / 1e3, 1) == 150.0
        assert round(radiative_capacity(T_pk, A_EMIT, 0.80, 220.0) / 1e3, 1) == 131.9
        assert round(radiative_capacity(T_pk, A_EMIT, 0.91, 260.0) / 1e3, 1) == 124.7
        assert round(radiative_capacity(T_pk, A_EMIT, 0.80, 260.0) / 1e3, 1) == 109.6

    def test_b4_headroom_accounting(self):
        # Combined stress removes 40.4 kW: the full 30 kW headroom plus a
        # 10.4 kW deficit below sustained load.
        T_pk = equilibrium_temperature(Q_PEAK, A_EMIT, EPS, T_S)
        stressed = radiative_capacity(T_pk, A_EMIT, 0.80, 260.0) / 1e3
        assert (150.0 - stressed) == pytest.approx(40.36, abs=0.01)
        assert (120.0 - stressed) == pytest.approx(10.36, abs=0.01)

    def test_b7_fixed_load_equilibria(self):
        cases = [
            (Q_SUST, 0.80, 220.0, 346.21),
            (Q_SUST, 0.91, 260.0, 350.78),
            (Q_SUST, 0.80, 260.0, 358.91),   # +21.8 K over nominal
            (Q_PEAK, 0.80, 260.0, 374.17),
        ]
        for Q, eps, ts, expected in cases:
            assert equilibrium_temperature(Q, A_EMIT, eps, ts) == pytest.approx(
                expected, abs=0.01
            )

    def test_b8_overhead_parameterization(self):
        # Q_rad = (1 + f) * P_compute.
        cases = [
            (1.10, EPS, T_S, 343.80),
            (1.20, EPS, T_S, 350.12),
            (1.10, 0.80, 260.0, 365.24),
            (1.20, 0.80, 260.0, 371.26),
        ]
        for f, eps, ts, expected in cases:
            T = equilibrium_temperature(f * Q_SUST, A_EMIT, eps, ts)
            assert T == pytest.approx(expected, abs=0.01)

    def test_b9_effective_area_case(self):
        assert equilibrium_temperature(
            Q_SUST, 0.85 * A_EMIT, EPS, T_S
        ) == pytest.approx(348.67, abs=0.01)


class TestAI1CoolantScreen:
    T_CRIT_NH3 = 405.5  # K, NIST reference value (NOT computed here)

    def test_b6_one_sided_continuous_peak_supercritical(self):
        T = equilibrium_temperature(Q_PEAK, A_PLAN, EPS, T_S)
        assert T > self.T_CRIT_NH3

    def test_b6_one_sided_sustained_headroom_under_14K(self):
        gap = self.T_CRIT_NH3 - equilibrium_temperature(Q_SUST, A_PLAN, EPS, T_S)
        assert 13.9 < gap < 14.1   # strong disfavor, NOT exclusion

    def test_b6_two_sided_margin_over_50K(self):
        T_pk = equilibrium_temperature(Q_PEAK, A_EMIT, EPS, T_S)
        assert self.T_CRIT_NH3 - T_pk > 50.0


class TestAI1FluxReconciliation:
    def test_b10_planform_and_per_face_fluxes(self):
        assert Q_PEAK / A_PLAN == pytest.approx(1364.0, abs=1.0)
        assert Q_PEAK / A_EMIT == pytest.approx(682.0, abs=1.0)
        assert Q_SUST / A_EMIT == pytest.approx(545.0, abs=1.0)

    def test_b10_gross_minus_sink_decomposition(self):
        T_pk = equilibrium_temperature(Q_PEAK, A_EMIT, EPS, T_S)
        gross = EPS * SIGMA_SB * T_pk**4
        sink = EPS * SIGMA_SB * T_S**4
        assert gross == pytest.approx(802.8, abs=0.5)
        assert sink == pytest.approx(120.9, abs=0.5)
        assert (gross - sink) == pytest.approx(Q_PEAK / A_EMIT, abs=0.5)
        # net flux helper must agree with the decomposition
        assert net_flux(T_pk, EPS, T_S) == pytest.approx(gross - sink, rel=1e-12)


class TestAI1Comparisons:
    def test_b11_iss_capacity_ratios_firm(self):
        P_ISS = 70e3
        assert Q_SUST / P_ISS == pytest.approx(1.71, abs=0.01)
        assert Q_PEAK / P_ISS == pytest.approx(2.14, abs=0.01)

    def test_b11_iss_flux_ratios_provisional(self):
        # 422 m^2 is secondary reporting with UNVERIFIED area convention;
        # these ratios are PROVISIONAL in the paper and stay flagged here.
        P_ISS, A_ISS = 70e3, 422.0
        assert (Q_SUST / A_EMIT) / (P_ISS / A_ISS) == pytest.approx(3.29, abs=0.02)
        assert (Q_PEAK / A_EMIT) / (P_ISS / A_ISS) == pytest.approx(4.11, abs=0.02)

    def test_b12_constellation_scaling_both_bases(self):
        assert 1e9 / Q_PEAK == pytest.approx(6667.0, abs=1.0)
        assert 1e9 / Q_SUST == pytest.approx(8333.0, abs=1.0)
        assert 6667 * A_EMIT / 1e6 == pytest.approx(1.467, abs=0.01)
        assert 8333 * A_EMIT / 1e6 == pytest.approx(1.833, abs=0.01)

    def test_b13_specific_power_cross_check(self):
        assert 150e3 / 70e3 == pytest.approx(2.143, abs=0.005)
        assert 120e3 / 70e3 == pytest.approx(1.714, abs=0.005)

    def test_b14_hot_rejection_factor(self):
        T_pk = equilibrium_temperature(Q_PEAK, A_EMIT, EPS, T_S)
        factor = (T_pk**4 - 220.0**4) / (293.0**4 - 220.0**4)
        assert factor == pytest.approx(2.628, abs=0.005)
        # and via the package's area_ratio (same algebra, Corollary 1.1)
        assert area_ratio(293.0, T_pk, 220.0) == pytest.approx(factor, rel=1e-12)
