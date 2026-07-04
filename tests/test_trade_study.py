"""B6 trade-study engine tests. The engine's *executable verification* (level c) is here:
Pareto-dominance construction, front assembly, degenerate/empty handling, category + reason
metadata, reproducibility, and machine-readable export. Physics is inherited from B1-B5, not
re-validated. Pure Pareto logic is CoolProp-free; the real sweep is gated."""

from __future__ import annotations

import warnings

import pytest

from orbital_thermal import trade_study as ts
from orbital_thermal.trade_study import PointCategory, ReasonCode


def _pt(case, **metrics):
    return ts.EvaluatedPoint(
        case_id=case, coolant="ammonia", material="aluminum", grid_heat_load_W=0.0,
        grid_mass_flow_kg_s=0.0, grid_radiator_area_m2=0.0, grid_low_side_pressure_Pa=0.0,
        feasible=True, category=PointCategory.FEASIBLE_RANKED, reason_codes=(ReasonCode.FEASIBLE,),
        metrics=metrics)


_MINMIN = ts.TradeDef("t", "x", False, "y", False, "test assumption")


def _cmp(av, bv, maximize, strict=False):
    if strict:
        return av > bv if maximize else av < bv
    return av >= bv if maximize else av <= bv


# --- pure Pareto logic: no CoolProp ----------------------------------------------


class TestDominance:
    def test_min_min_dominance(self):
        a, b = _pt("c", x=1.0, y=1.0), _pt("c", x=2.0, y=2.0)
        assert ts._dominates(a, b, _MINMIN)
        assert not ts._dominates(b, a, _MINMIN)

    def test_non_dominated_tradeoff(self):
        a, b = _pt("c", x=1.0, y=3.0), _pt("c", x=3.0, y=1.0)
        assert not ts._dominates(a, b, _MINMIN)
        assert not ts._dominates(b, a, _MINMIN)

    def test_maximize_axis(self):
        trade = ts.TradeDef("t", "x", True, "y", False, "a")  # max x, min y
        a, b = _pt("c", x=3.0, y=1.0), _pt("c", x=2.0, y=2.0)
        assert ts._dominates(a, b, trade)


class TestParetoFront:
    def test_front_membership(self):
        pts = [_pt("c", x=1.0, y=3.0), _pt("c", x=2.0, y=2.0), _pt("c", x=3.0, y=1.0),
               _pt("c", x=3.0, y=3.0)]  # last is dominated by all
        front = ts.pareto_front(pts, _MINMIN)
        assert not front.degenerate
        assert len(front.member_case_ids) == 3
        assert pts[3].dominated_reasons.get("t", "").startswith("dominated_on_")
        assert "t" in pts[0].pareto_fronts

    def test_single_point_is_degenerate(self):
        front = ts.pareto_front([_pt("c", x=1.0, y=1.0)], _MINMIN)
        assert front.degenerate and "degenerate" in front.note

    def test_empty_front_recorded_not_omitted(self):
        infeasible = ts.EvaluatedPoint(
            "c", "ammonia", "aluminum", 0, 0, 0, 0, False, PointCategory.INFEASIBLE_RANKED,
            (ReasonCode.JUNCTION_LIMIT_FAILURE,), {})
        front = ts.pareto_front([infeasible], _MINMIN)
        assert front.degenerate and "empty" in front.note and front.n_feasible == 0


class TestDesignGridAndTrades:
    def test_grid_size_and_metadata(self):
        g = ts.DesignGrid(heat_load_W=(800.0, 1200.0), mass_flow_kg_s=(0.05,),
                          radiator_area_m2=(2.0,), low_side_pressure_Pa=(20e5,))
        assert g.size() == 2 and len(list(g.points())) == 2
        assert g.metadata()["grid_points_per_case"] == 2

    def test_all_six_named_trades_present(self):
        names = {t.name for t in ts.TRADES}
        assert len(ts.TRADES) == 6
        for expected in ("modeled_mass_vs_load", "pump_power_vs_delta_T", "radiator_area_vs_temp",
                         "junction_margin_vs_load", "inventory_containment_mass_vs_pressure",
                         "modeled_mass_vs_parasitic_power"):
            assert expected in names


# --- real sweep: CoolProp-gated --------------------------------------------------

pytest.importorskip("CoolProp", reason="CoolProp not installed")

_SMALL = ts.DesignGrid(heat_load_W=(1000.0, 1400.0), mass_flow_kg_s=(0.05, 0.08),
                       radiator_area_m2=(2.0, 2.5), low_side_pressure_Pa=(20e5,))


def _build():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ts.build_trade_study(grid=_SMALL)


@pytest.fixture(scope="module")
def study():
    return _build()


class TestSweep:
    def test_summary_and_counts(self, study):
        res = study
        s = res.summary()
        assert s["total_points"] == _SMALL.size() * 4  # 4 rank-eligible cases
        assert (s["feasible_ranked"] + s["gate_rejected"] + s["nonconverged"]
                == s["total_points"])  # every point is classified (F5)
        assert s["fronts"] == 6

    def test_only_rank_eligible_cases_are_swept(self, study):
        res = study
        cases = {p.case_id for p in res.points}
        assert cases == {"ammonia-aluminum", "ammonia-copper", "water-aluminum", "water-copper"}

    def test_all_six_fronts_built_or_marked_degenerate(self, study):
        res = study
        assert len(res.fronts) == 6
        for f in res.fronts:
            assert f.member_case_ids or f.degenerate  # never silently empty

    def test_feasible_points_carry_incomplete_mass_flag(self, study):
        res = study
        feas = [p for p in res.points if p.feasible]
        assert feas
        for p in feas:
            assert ReasonCode.MASS_ACCOUNTING_INCOMPLETE in p.reason_codes
            assert "modeled_mass_kg" in p.metrics

    def test_infeasible_points_carry_a_reason(self, study):
        res = study
        for p in res.points:
            if not p.feasible:
                assert p.reason_codes and p.reason_codes[0] is not ReasonCode.FEASIBLE

    def test_reproducible(self):
        a, b = _build().summary(), _build().summary()
        assert a == b

    def test_csv_export_shape(self, study):
        res = study
        rows = ts.to_csv_rows(res)
        assert len(rows) == len(res.points) + 1  # header + points
        assert rows[0].startswith("point_id,case_id,coolant,material")
        assert "modeled_mass_kg" in rows[0] and "min_subcooling_Pa" in rows[0]
        assert "pareto_front_membership" in rows[0] and "dominated_reasons" in rows[0]

    def test_no_single_case_is_optimal_on_every_front(self, study):
        # F4: the supportable claim -- no case is a member of ALL six fronts, and membership
        # spans more than one case (genuine trade-offs).
        res = study
        from collections import Counter
        counts = Counter()
        for f in res.fronts:
            for cid in set(f.member_case_ids):
                counts[cid] += 1
        assert counts and max(counts.values()) < len(ts.TRADES)  # no universal winner
        assert len(counts) >= 2  # membership distributed across cases

    def test_dominance_reasons_exported(self, study):
        # F3: the CSV must expose per-front dominance so dominance is auditable from data
        res = study
        rows = ts.to_csv_rows(res)
        hdr = rows[0].split(",")
        assert "dominated_reasons" in hdr and "pareto_front_membership" in hdr
        dominated = [p for p in res.points if p.feasible and p.dominated_reasons]
        assert dominated  # some feasible points are dominated on some front
        p = dominated[0]
        front, why = next(iter(p.dominated_reasons.items()))
        assert why.startswith("dominated_on_")

    def test_point_ids_unique(self, study):
        res = study  # F6
        ids = [p.point_id for p in res.points]
        assert len(ids) == len(set(ids))

    def test_exact_failed_gates_exported(self, study):
        # N2: gate-rejected points carry exact gate names (not just categorized reasons)
        res = study
        rows = ts.to_csv_rows(res)
        assert "failed_gates" in rows[0].split(",")
        rejected = [p for p in res.points
                    if p.category is ts.PointCategory.INFEASIBLE_RANKED]
        assert rejected  # the small grid contains gate-rejected points
        assert all(p.failed_gates for p in rejected)

    def test_nonconverged_category_is_distinct_from_gate_rejection(self, study):
        # F5: category is NONCONVERGED iff a nonconvergence reason is present
        res = study
        for p in res.points:
            has_nc = ReasonCode.RESIDUAL_NONCONVERGENCE in p.reason_codes
            assert (p.category is ts.PointCategory.NONCONVERGED) == has_nc

    def test_pareto_fronts_match_independent_oracle(self, study):
        # F8: recompute each front with a naive local dominance and compare membership
        res = study
        feasible = [p for p in res.points if p.feasible]
        for t in ts.TRADES:
            oracle = set()
            for pt in feasible:
                dom = False
                for q in feasible:
                    if q is pt:
                        continue
                    xge = _cmp(q.metrics[t.x_key], pt.metrics[t.x_key], t.x_maximize)
                    yge = _cmp(q.metrics[t.y_key], pt.metrics[t.y_key], t.y_maximize)
                    xs = _cmp(q.metrics[t.x_key], pt.metrics[t.x_key], t.x_maximize, True)
                    ys = _cmp(q.metrics[t.y_key], pt.metrics[t.y_key], t.y_maximize, True)
                    if xge and yge and (xs or ys):
                        dom = True
                        break
                if not dom:
                    oracle.add(pt.point_id)
            engine = {pt.point_id for pt in feasible if t.name in pt.pareto_fronts}
            assert engine == oracle, f"front {t.name}: engine != oracle"
