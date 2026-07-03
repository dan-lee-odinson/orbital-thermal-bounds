"""Tests for the Phase A visual boundary API (``orbital_thermal.visual_api``).

The visual API is a thin orchestration layer: its job is to call the engine and
LABEL the result. These tests therefore check three things:

1. structural contract -- every function returns the documented keys/columns and
   a ``meta`` block whose inputs are tagged with a KNOWN provenance label;
2. no-reimplementation -- selected values equal the engine functions directly, so
   the visual API cannot silently drift into a second model;
3. policy invariants -- the sun-shielded contract is carried on every
   direct-solar-omitting output, the beta = 90 deg albedo null is flagged as a
   model limitation, and no unsupported/future reference case is rank-eligible.
"""

import warnings

import pytest

from orbital_thermal import architecture_comparison as arch
from orbital_thermal import environment as env
from orbital_thermal import equilibrium as eq
from orbital_thermal import mccalip_exact_vf as mvf
from orbital_thermal import radiation as rad
from orbital_thermal import reference_architectures as refarch
from orbital_thermal import sink as sink_mod
from orbital_thermal import visual_api as v


def _assert_meta(meta):
    """Every returned meta block has the standard shape and only known labels."""
    for key in ("units", "convention", "source_functions", "inputs", "assumptions", "warnings"):
        assert key in meta, f"meta missing {key}"
    assert meta["source_functions"], "source_functions must name the engine call(s)"
    for inp in meta["inputs"]:
        assert set(inp) >= {"name", "value", "unit", "provenance"}
        assert inp["provenance"] in v.INPUT_PROVENANCE_LABELS, inp


# ---------------------------------------------------------------------------
# Environment / engine self-check
# ---------------------------------------------------------------------------

class TestEngineInfo:
    def test_all_functions_available(self):
        info = v.engine_info()
        assert info["package"] == "orbital_thermal"
        assert info["all_functions_available"] is True
        assert all(info["functions"].values())

    def test_version_is_a_string(self):
        assert isinstance(v.engine_info()["version"], str)


# ---------------------------------------------------------------------------
# Scalar boundary points -- cross-checked against the engine
# ---------------------------------------------------------------------------

class TestScalarPoints:
    def test_equilibrium_point_matches_engine(self):
        r = v.equilibrium_point(120_000, 220.0, 0.91, 220.0)
        assert r["equilibrium_temperature_K"] == pytest.approx(
            eq.equilibrium_temperature(120_000, 220.0, 0.91, 220.0)
        )
        # AI1 published anchor.
        assert r["equilibrium_temperature_K"] == pytest.approx(337.1004, abs=1e-3)
        assert r["net_flux_per_emitting_m2_W_m2"] == pytest.approx(120_000 / 220.0, rel=1e-9)
        assert r["planform_area_m2"] == pytest.approx(110.0)
        _assert_meta(r["meta"])

    def test_required_area_point_matches_engine(self):
        r = v.required_area_point(1_000_000, 293.0, 0.91, 0.0)
        assert r["required_emitting_area_m2"] == pytest.approx(
            rad.required_area(1_000_000, 293.0, 0.91, 0.0)
        )
        # Corollary 1.2 megawatt anchor.
        assert r["required_emitting_area_m2"] == pytest.approx(2630.0, abs=0.5)
        assert r["required_planform_area_m2"] == pytest.approx(
            r["required_emitting_area_m2"] / 2.0
        )
        _assert_meta(r["meta"])


# ---------------------------------------------------------------------------
# Boundary curves
# ---------------------------------------------------------------------------

class TestCurves:
    def test_net_rejection_curve_keys_and_values(self):
        r = v.net_rejection_curve(emissivity=0.91, T_sink_K=220.0, t_min=230, t_max=400, num=6)
        assert set(r) >= {"x", "y", "x_label", "y_label", "x_unit", "y_unit", "title", "meta"}
        assert len(r["x"]) == len(r["y"]) == 6
        # Each y equals radiation.net_flux at that x.
        for x, y in zip(r["x"], r["y"], strict=True):
            assert y == pytest.approx(rad.net_flux(x, 0.91, 220.0))
        _assert_meta(r["meta"])

    def test_net_rejection_curve_rejects_temperature_at_or_below_sink(self):
        with pytest.raises(ValueError):
            v.net_rejection_curve(emissivity=0.91, T_sink_K=250.0, t_min=200, t_max=300, num=5)

    def test_area_temperature_curve_matches_engine(self):
        r = v.area_temperature_curve(120_000, emissivity=0.91, T_sink_K=220.0, t_min=250, t_max=360, num=5)
        assert len(r["y"]) == len(r["y_planform"]) == 5
        for x, y in zip(r["x"], r["y"], strict=True):
            assert y == pytest.approx(rad.required_area(120_000, x, 0.91, 220.0))
        assert r["y_planform"][0] == pytest.approx(r["y"][0] / 2.0)
        _assert_meta(r["meta"])

    def test_earth_view_factor_curve_anchors(self):
        r = v.earth_view_factor_curve(550.0, t_min=0, t_max=180, num=19)
        for x, y in zip(r["x"], r["y"], strict=True):
            assert y == pytest.approx(env.sphere_view_factor(550.0, x))
        assert r["nadir_view_factor"] == pytest.approx(0.847, abs=1e-3)
        assert r["edge_on_view_factor"] == pytest.approx(0.258, abs=3e-3)
        _assert_meta(r["meta"])


# ---------------------------------------------------------------------------
# Beta-angle / effective-sink sweeps
# ---------------------------------------------------------------------------

class TestEffectiveSinkSweep:
    def test_rows_have_expected_columns(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = v.effective_sink_sweep(550.0, betas_deg=(0, 45, 90))
        cols = {"beta_deg", "orbit_averaged_sink_K", "view_factor",
                "albedo_orbit_mean_factor", "albedo_model_limited", "is_beta90_endpoint"}
        for row in r["rows"]:
            assert set(row) >= cols

    def test_no_drift_from_engine(self):
        # Guards against the visual layer applying an extra transformation to the
        # engine output (it should forward it unchanged).
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = v.effective_sink_sweep(550.0, betas_deg=(0, 45, 90), tilt_deg=0.0)
        for row in r["rows"]:
            expected = sink_mod.analytic_orbit_averaged_sink(
                550.0, row["beta_deg"], 0.0, assume_sun_shielded=True,
                emissivity=0.91, solar_absorptivity=0.20)
            assert row["orbit_averaged_sink_K"] == pytest.approx(expected)

    def test_independent_anchors(self):
        # Pinned numeric anchors (NOT re-derived from the same call), so a bug in
        # parameter passing that changes the output is caught rather than hidden.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = v.effective_sink_sweep(550.0, betas_deg=(0, 45, 90), tilt_deg=0.0)
        by_beta = {row["beta_deg"]: row for row in r["rows"]}
        # beta=90, tilt=0 matches the published sink floor anchor (243.95 K).
        assert by_beta[90.0]["orbit_averaged_sink_K"] == pytest.approx(243.95, abs=0.5)
        assert by_beta[0.0]["orbit_averaged_sink_K"] == pytest.approx(250.99, abs=0.5)
        # Sink falls toward the terminator as the albedo drive drops (beta wiring).
        assert (by_beta[0.0]["orbit_averaged_sink_K"]
                > by_beta[90.0]["orbit_averaged_sink_K"])

    def test_arguments_actually_flow_through(self):
        # A parameter swap (e.g. altitude<->tilt) would not be caught by comparing
        # to a fresh engine call with the SAME args; assert instead that changing
        # tilt materially changes the result and the view factor uses the right order.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            nadir = v.effective_sink_sweep(550.0, betas_deg=(0,), tilt_deg=0.0)["rows"][0]
            edge = v.effective_sink_sweep(550.0, betas_deg=(0,), tilt_deg=90.0)["rows"][0]
        # view_factor is F(altitude, tilt) in the correct argument order.
        assert nadir["view_factor"] == pytest.approx(env.sphere_view_factor(550.0, 0.0))
        assert edge["view_factor"] == pytest.approx(env.sphere_view_factor(550.0, 90.0))
        # Edge-on couples far less to Earth, so its sink is much colder than nadir.
        assert edge["orbit_averaged_sink_K"] < nadir["orbit_averaged_sink_K"] - 20.0

    def test_beta_90_flagged_as_model_limited(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = v.effective_sink_sweep(550.0, betas_deg=(0, 30, 60, 90))
        b90 = [row for row in r["rows"] if row["beta_deg"] == 90.0][0]
        assert b90["albedo_model_limited"] is True
        assert b90["is_beta90_endpoint"] is True
        # Off-endpoint betas are NOT model-limited.
        assert all(not row["albedo_model_limited"] for row in r["rows"] if row["beta_deg"] < 90)
        # The limitation is surfaced in the metadata (assumptions and warnings).
        assert any("beta = 90" in a for a in r["meta"]["assumptions"])
        assert r["meta"]["warnings"], "beta=90 sweep must warn about the albedo null"

    def test_sun_shielded_contract_carried(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = v.effective_sink_sweep(550.0, betas_deg=(0, 45))
        assert r["meta"]["sun_shielded"] is True
        assert any("sun-shielded" in a or "direct solar" in a.lower()
                   for a in r["meta"]["assumptions"])

    def test_assume_sun_shielded_false_is_rejected_by_engine(self):
        with pytest.raises(NotImplementedError):
            v.effective_sink_sweep(550.0, betas_deg=(0,), assume_sun_shielded=False)


class TestBetaSweep:
    def test_boundary_columns_and_engine_agreement(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = v.beta_sweep(550.0, betas_deg=(0, 45, 90), Q_W=120_000, emitting_area_m2=220.0)
        for row in r["rows"]:
            s = sink_mod.analytic_orbit_averaged_sink(
                550.0, row["beta_deg"], 0.0, assume_sun_shielded=True,
                emissivity=0.91, solar_absorptivity=0.20)
            assert row["orbit_averaged_sink_K"] == pytest.approx(s)
            assert row["equilibrium_temperature_K"] == pytest.approx(
                eq.equilibrium_temperature(120_000, 220.0, 0.91, s)
            )
        # Independent pinned anchor so a parameter-passing bug is caught, not hidden.
        by_beta = {row["beta_deg"]: row for row in r["rows"]}
        assert by_beta[0.0]["equilibrium_temperature_K"] == pytest.approx(347.25, abs=0.5)
        assert by_beta[90.0]["equilibrium_temperature_K"] == pytest.approx(344.67, abs=0.5)
        assert r["meta"]["sun_shielded"] is True

    def test_includes_beta_90_with_limitation(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = v.beta_sweep(550.0, betas_deg=(0, 45, 90))
        assert any(row["beta_deg"] == 90.0 and row["albedo_model_limited"] for row in r["rows"])

    def test_required_area_none_when_sink_exceeds_target(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # 240 K target is below the tilt=0 orbit-mean sink (~244-251 K) at every
            # beta, so no finite area rejects heat there -> required area is None.
            cold = v.beta_sweep(550.0, betas_deg=(0, 45, 90), radiator_temperature_K=240.0)
            # 400 K target is above the sink everywhere -> a finite area exists.
            hot = v.beta_sweep(550.0, betas_deg=(0, 45, 90), radiator_temperature_K=400.0)
        assert all(row["required_emitting_area_m2"] is None for row in cold["rows"])
        assert all(isinstance(row["required_emitting_area_m2"], float) for row in hot["rows"])


# ---------------------------------------------------------------------------
# McCalip heuristic vs exact view factor
# ---------------------------------------------------------------------------

class TestMccalipComparison:
    def test_matches_correction_table_and_heuristic_is_much_smaller(self):
        r = v.mccalip_view_factor_comparison(betas_deg=(0.0, 90.0))
        table = mvf.correction_table_vs_beta((0.0, 90.0))
        for row, ref in zip(r["rows"], table, strict=True):
            assert row["delta_K"] == pytest.approx(ref["delta_K"])
            assert row["eqtemp_mccalip_K"] == pytest.approx(ref["eqtemp_mccalip_K"])
            assert row["eqtemp_exact_K"] == pytest.approx(ref["eqtemp_exact_K"])
        b90 = r["rows"][-1]
        # Edge-on: exact per-face view factor is an order of magnitude above the heuristic floor.
        assert b90["vf_side_a_exact"] > 10 * b90["vf_side_a_mccalip_heuristic"]
        assert b90["delta_K"] == pytest.approx(6.35, abs=0.05)

    def test_labelled_as_replication_not_validation(self):
        r = v.mccalip_view_factor_comparison(betas_deg=(90.0,))
        assert any("REPLICATION" in w or "not a validation" in w.lower()
                   for w in r["meta"]["warnings"])


# ---------------------------------------------------------------------------
# Orbital transient waveform
# ---------------------------------------------------------------------------

class TestTransient:
    def test_waveform_keys_and_shape(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = v.transient_orbit_case(
                550.0, 0.0, 545.0, areal_heat_capacity=8000.0,
                n_orbits=40, steps_per_orbit=360)
        assert len(r["t_s"]) == len(r["T_panel_K"]) == len(r["T_sink_K"]) == 361
        s = r["summary"]
        assert s["transient_peak_K"] >= s["transient_mean_K"]
        # Jensen: arithmetic mean sits at or below the steady, averaged-sink solution.
        assert s["transient_mean_K"] <= s["steady_avg_sink_K"] + 1e-6
        assert s["peak_excess_over_steady_K"] >= 0.0

    def test_sun_shielded_contract_carried(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = v.transient_orbit_case(
                550.0, 0.0, 545.0, areal_heat_capacity=8000.0,
                n_orbits=40, steps_per_orbit=360)
        assert r["meta"]["sun_shielded"] is True
        assert any("sun-shielded" in a or "direct solar" in a.lower()
                   for a in r["meta"]["assumptions"])

    def test_build_name_path(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = v.transient_orbit_case(
                550.0, 30.0, 545.0, build_name="integrated_compute_radiator",
                n_orbits=40, steps_per_orbit=360)
        from orbital_thermal import transient as tr
        assert r["areal_heat_capacity_J_m2K"] == pytest.approx(
            tr.build_areal_heat_capacity("integrated_compute_radiator")
        )

    def test_requires_a_heat_capacity(self):
        with pytest.raises(ValueError):
            v.transient_orbit_case(550.0, 0.0, 545.0)


# ---------------------------------------------------------------------------
# Reference-case table
# ---------------------------------------------------------------------------

class TestReferenceTable:
    def test_all_labels_are_known_and_ranking_not_performed(self):
        t = v.reference_case_table()
        assert t["ranking_performed"] is False
        for row in t["rows"]:
            assert row["label"] in v.REFERENCE_CASE_LABELS
        _assert_meta(t["meta"])

    def test_no_unsupported_or_future_case_is_rank_eligible(self):
        t = v.reference_case_table()
        for row in t["rows"]:
            if row["label"] in (v.CASE_UNSUPPORTED, v.CASE_FUTURE):
                assert row["rank_eligible"] is False, row["name"]

    def test_published_and_sensitivity_are_not_rank_eligible(self):
        # As-published is never a ranking basis; the spectral case is a sensitivity.
        t = v.reference_case_table()
        for row in t["rows"]:
            if row["label"] in (v.CASE_PUBLISHED, v.CASE_SENSITIVITY):
                assert row["rank_eligible"] is False, row["name"]

    def test_ai1_row_matches_engine_and_leaves_albedo_uncomputed(self):
        t = v.reference_case_table(load_W=120_000.0)
        ai1_pub = [r for r in t["rows"] if r["name"].startswith("AI1 design point")][0]
        assert ai1_pub["radiator_temperature_K"] == pytest.approx(
            arch.AI1_DESIGN_POINT.radiator_temperature_K(120_000.0)
        )
        # Harmonized AI1: solar absorptivity unpublished => full net is None (no invention).
        ai1_h = [r for r in t["rows"] if r["name"].startswith("AI1 (harmonized")][0]
        assert ai1_h["net_rejection_W_m2"] is None
        assert ai1_h["net_excluding_albedo_W_m2"] is not None

    def test_starcloud_rows_match_engine(self):
        t = v.reference_case_table()
        pub = [r for r in t["rows"] if "published, as-written" in r["name"]][0]
        spec = [r for r in t["rows"] if "spectral separation" in r["name"]][0]
        assert pub["net_rejection_W_m2"] == pytest.approx(
            refarch.starcloud_published_balance().net_rejection_W_m2
        )
        assert pub["net_rejection_W_m2"] == pytest.approx(633.08, abs=0.01)
        assert spec["net_rejection_W_m2"] == pytest.approx(584.76, abs=0.01)

    def test_biswas_is_future_and_pinned_to_v1_2(self):
        t = v.reference_case_table()
        biswas = [r for r in t["rows"] if r["name"].startswith("Biswas")][0]
        assert biswas["label"] == v.CASE_FUTURE
        assert biswas["rank_eligible"] is False
        assert biswas["radiator_temperature_K"] is None
        assert "v1.2" in biswas["source"]
        assert v.BISWAS_REFERENCE["release_tag"] == "v1.2"


# ---------------------------------------------------------------------------
# Cross-cutting: sun-shielded contract on every direct-solar-omitting output
# ---------------------------------------------------------------------------

class TestSunShieldedContractEverywhere:
    def test_all_sink_based_outputs_carry_the_contract(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            outputs = [
                v.effective_sink_sweep(550.0, betas_deg=(0, 45)),
                v.beta_sweep(550.0, betas_deg=(0, 45)),
                v.sink_profile_case(550.0, 30.0, n=37),
                v.transient_orbit_case(550.0, 0.0, 545.0, areal_heat_capacity=8000.0,
                                       n_orbits=20, steps_per_orbit=180),
            ]
        for out in outputs:
            assert out["meta"].get("sun_shielded") is True
            assert v.SUN_SHIELDED_CONTRACT in out["meta"]["assumptions"]
