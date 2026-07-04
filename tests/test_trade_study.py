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
        assert s["feasible_ranked"] + s["infeasible_ranked"] == s["total_points"]
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
        assert rows[0].startswith("case_id,coolant,material")
        assert "modeled_mass_kg" in rows[0] and "pareto_fronts" in rows[0]

    def test_trade_offs_exist_no_single_case_wins_everything(self, study):
        res = study
        # union of front members spans more than one case => genuine trade-offs
        members = set()
        for f in res.fronts:
            members.update(f.member_case_ids)
        assert len(members) >= 2
