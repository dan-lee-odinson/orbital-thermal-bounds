"""Thin, source-labelled orchestration layer for the Phase A visual boundary model.

This module is the single API the ``notebooks/phase_a_visual_boundary_model.ipynb``
notebook calls. It **orchestrates existing package functions** -- it does not
reimplement any physics. Every value it returns is produced by a function in
``orbital_thermal`` (``radiation``, ``equilibrium``, ``environment``, ``sink``,
``transient``, ``mccalip_exact_vf``, ``reference_architectures``,
``architecture_comparison``, ``harmonized_comparison``) and is wrapped with
provenance/convention/unit/source metadata so a reviewer can see *where each
number comes from* without reading the codebase.

Design rules (mirroring the repository's no-invention and V&V policy)
--------------------------------------------------------------------
* **No second model.** Each function is a labelled call into the engine. If you
  find yourself writing a heat balance here, it belongs in the engine instead.
* **Source labels, not claims.** Every returned structure carries a ``meta``
  dict with: ``units``, ``convention``, ``source_functions``, ``inputs`` (each
  input tagged with a provenance label), ``assumptions``, and ``warnings``.
* **The sun-shielded contract is explicit.** Any output built on the
  direct-solar-*omitting* effective-sink model (``sink``/``transient``) records
  ``meta['sun_shielded']`` and states the contract in ``meta['assumptions']``.
  The engine itself hard-rejects ``assume_sun_shielded`` that is not the boolean
  ``True``/``False`` (see :func:`orbital_thermal.sink._require_shielding`).
* **beta = 90 deg is model-limited, not physical.** Sweeps flag the subpoint
  albedo null at the dawn-dusk endpoint as a *model limitation*
  (``albedo_model_limited``), never as "the radiator sees no reflected sun".
* **As-published is not a ranking.** :func:`reference_case_table` labels each row
  by provenance/convention (``published`` / ``harmonized`` / ``sensitivity`` /
  ``unsupported`` / ``future``), marks ``rank_eligible`` conservatively, and sets
  ``ranking_performed=False``. Unpublished optical properties (AI1 solar
  absorptivity) are left ``None`` -- never invented into a ranked value.

Returned structures are plain Python (dicts / lists of dicts / lists of floats)
so they are trivially testable and need neither pandas nor plotly at import
time. pandas/plotly/ipywidgets are notebook-only (the ``[visual]`` extra).

Units are SI unless a key says otherwise: kelvin, watts, W/m^2, m^2, degrees,
seconds.
"""

import numpy as np

from . import architecture_comparison as arch
from . import environment as env
from . import equilibrium as eq
from . import harmonized_comparison as harm
from . import mccalip_exact_vf as mvf
from . import mccalip_replication as mc
from . import radiation as rad
from . import reference_architectures as refarch
from . import sink as sink_mod
from . import transient as tr

# ---------------------------------------------------------------------------
# Provenance / label vocabularies (from docs/development/chip_to_radiator_phase_b_plan.md
# Section 2 and the mastery-ledger entries).
# ---------------------------------------------------------------------------

#: Input-provenance labels for the no-invention policy. Every input surfaced in
#: the notebook must be one of these.
PUBLISHED = "published"          # stated by a primary source
DERIVED = "derived"              # computed from published quantities by a stated relation
ASSUMED = "assumed"              # a stated modelling assumption, never presented as published
CORRECTED = "corrected"          # a published value re-derived, with the correction documented
DESIGN_VARIABLE = "design-variable"  # a swept/optimised independent variable of the study
SENSITIVITY = "sensitivity"      # an explicit parametric sensitivity, not a ranked case
UNSUPPORTED_FUTURE = "unsupported/future"  # not modelled by the current package

INPUT_PROVENANCE_LABELS = frozenset({
    PUBLISHED, DERIVED, ASSUMED, CORRECTED, DESIGN_VARIABLE, SENSITIVITY, UNSUPPORTED_FUTURE,
})

#: Reference-case classes for :func:`reference_case_table` rows.
CASE_PUBLISHED = "published"
CASE_HARMONIZED = "harmonized"
CASE_SENSITIVITY = "sensitivity"
CASE_UNSUPPORTED = "unsupported"
CASE_FUTURE = "future"

REFERENCE_CASE_LABELS = frozenset({
    CASE_PUBLISHED, CASE_HARMONIZED, CASE_SENSITIVITY, CASE_UNSUPPORTED, CASE_FUTURE,
})

#: Provenance tag for harmonized-model outputs (shared-environment package machinery
#: applied to published optical properties: a value derived under stated conventions).
HARMONIZED_PROVENANCE = DERIVED

#: The sun-shielding contract, surfaced verbatim wherever the effective-sink
#: (direct-solar-omitting) model is used.
SUN_SHIELDED_CONTRACT = (
    "Effective-sink model OMITS direct solar flux on the radiator face; it is "
    "valid only when that face is sun-shielded (anti-solar attitude or external "
    "shade). The engine requires assume_sun_shielded=True (sink._require_shielding); "
    "a sun-facing/tilted face that sees direct sun violates this contract."
)

#: The beta -> 90 deg subpoint-albedo limitation, surfaced on every beta sweep.
BETA90_ALBEDO_LIMITATION = (
    "The subpoint albedo factor cos(beta)/pi nulls at beta = 90 deg: a MODEL "
    "limitation (sink.subpoint_albedo_factor), not a physical claim that albedo "
    "is zero. True disk-integrated albedo is nonzero at a terminator orbit "
    "(sink.disk_integrated_albedo_factor is intentionally NotImplemented)."
)

_ALBEDO_LIMIT_EPS = 1e-6


def _input(name, value, provenance, unit=""):
    """Build one labelled input record; ``provenance`` must be a known label."""
    if provenance not in INPUT_PROVENANCE_LABELS:
        raise ValueError(
            f"unknown input provenance {provenance!r}; use one of {sorted(INPUT_PROVENANCE_LABELS)}"
        )
    return {"name": name, "value": value, "unit": unit, "provenance": provenance}


def _meta(units, convention, source_functions, inputs, *, assumptions=None,
          warnings=None, sun_shielded=None):
    """Assemble the standard ``meta`` block attached to every returned structure."""
    m = {
        "units": units,
        "convention": convention,
        "source_functions": list(source_functions),
        "inputs": list(inputs),
        "assumptions": list(assumptions or []),
        "warnings": list(warnings or []),
    }
    if sun_shielded is not None:
        m["sun_shielded"] = bool(sun_shielded)
        m["assumptions"].append(SUN_SHIELDED_CONTRACT)
    return m


def _temperature_grid(temperatures_K, t_min, t_max, num):
    """Return a validated 1-D temperature grid (K) from an explicit sequence or a
    (t_min, t_max, num) span."""
    if temperatures_K is not None:
        grid = np.asarray(temperatures_K, dtype=float)
        if grid.ndim != 1 or grid.size == 0:
            raise ValueError("temperatures_K must be a non-empty 1-D sequence")
        return grid
    if t_min is None or t_max is None:
        raise ValueError("provide temperatures_K, or both t_min and t_max")
    if not (num and num >= 2):
        raise ValueError(f"num must be an integer >= 2, got {num}")
    if not (t_max > t_min):
        raise ValueError(f"t_max ({t_max}) must exceed t_min ({t_min})")
    return np.linspace(float(t_min), float(t_max), int(num))


# ---------------------------------------------------------------------------
# Environment / engine self-check (notebook section 2)
# ---------------------------------------------------------------------------

#: (label, module, attribute) triples for the engine functions the notebook needs.
_ENGINE_ENTRY_POINTS = (
    ("radiation.net_flux", rad, "net_flux"),
    ("radiation.required_area", rad, "required_area"),
    ("equilibrium.equilibrium_temperature", eq, "equilibrium_temperature"),
    ("environment.sphere_view_factor", env, "sphere_view_factor"),
    ("environment.nadir_view_factor", env, "nadir_view_factor"),
    ("sink.analytic_orbit_averaged_sink", sink_mod, "analytic_orbit_averaged_sink"),
    ("sink.sink_profile", sink_mod, "sink_profile"),
    ("transient.simulate", tr, "simulate"),
    ("mccalip_exact_vf.correction_table_vs_beta", mvf, "correction_table_vs_beta"),
    ("reference_architectures.starcloud_published_balance", refarch, "starcloud_published_balance"),
    ("harmonized_comparison.ai1_harmonized_balance", harm, "ai1_harmonized_balance"),
)


def engine_info():
    """Package version and a presence check of every engine entry point the
    notebook depends on. Pure metadata; imports nothing beyond the package."""
    checks = {
        label: callable(getattr(module, attr, None))
        for label, module, attr in _ENGINE_ENTRY_POINTS
    }
    from . import __version__ as version
    return {
        "package": "orbital_thermal",
        "version": version,
        "all_functions_available": all(checks.values()),
        "functions": checks,
    }


# ---------------------------------------------------------------------------
# Scalar boundary points (notebook section 3/4)
# ---------------------------------------------------------------------------

def equilibrium_point(
    Q_W,
    emitting_area_m2,
    emissivity,
    T_sink_K=0.0,
    *,
    load_provenance=DESIGN_VARIABLE,
    area_provenance=DESIGN_VARIABLE,
    emissivity_provenance=DESIGN_VARIABLE,
    sink_provenance=DESIGN_VARIABLE,
):
    """Steady radiator temperature (K) that rejects ``Q_W`` through ``emitting_area_m2``.

    Wraps :func:`orbital_thermal.equilibrium.equilibrium_temperature` and reports
    the net flux per emitting face via :func:`orbital_thermal.radiation.net_flux`.
    ``emitting_area_m2`` is the TWO-SIDED emitting area (= 2 x planform for a
    bifacial panel with equal per-face sinks); ``T_sink_K`` is the lumped
    effective sink T_s^eff.
    """
    T = eq.equilibrium_temperature(Q_W, emitting_area_m2, emissivity, T_sink_K)
    net = rad.net_flux(T, emissivity, T_sink_K)
    return {
        "equilibrium_temperature_K": float(T),
        "equilibrium_temperature_C": float(T - 273.15),
        "net_flux_per_emitting_m2_W_m2": float(net),
        "planform_area_m2": float(emitting_area_m2 / 2.0),
        "meta": _meta(
            units={"temperature": "K", "flux": "W/m^2", "area": "m^2"},
            convention=(
                "Gray-body two-sided panel; T_s^eff lumped effective sink; "
                "emitting area = 2 x planform (valid for equal per-face sinks)."
            ),
            source_functions=["equilibrium.equilibrium_temperature", "radiation.net_flux"],
            inputs=[
                _input("Q", Q_W, load_provenance, "W"),
                _input("emitting_area", emitting_area_m2, area_provenance, "m^2"),
                _input("emissivity", emissivity, emissivity_provenance, "-"),
                _input("T_sink_eff", T_sink_K, sink_provenance, "K"),
            ],
        ),
    }


def required_area_point(
    Q_W,
    radiator_temperature_K,
    emissivity,
    T_sink_K=0.0,
    *,
    load_provenance=DESIGN_VARIABLE,
    temperature_provenance=DESIGN_VARIABLE,
    emissivity_provenance=DESIGN_VARIABLE,
    sink_provenance=DESIGN_VARIABLE,
):
    """Emitting area (m^2) required to reject ``Q_W`` at ``radiator_temperature_K``.

    Wraps :func:`orbital_thermal.radiation.required_area` (Lemma 1 area law). The
    planform area is the emitting area halved (two-sided panel, equal per-face
    sinks).
    """
    a_emit = rad.required_area(Q_W, radiator_temperature_K, emissivity, T_sink_K)
    return {
        "required_emitting_area_m2": float(a_emit),
        "required_planform_area_m2": float(a_emit / 2.0),
        "meta": _meta(
            units={"area": "m^2", "temperature": "K"},
            convention=(
                "Lemma 1 area law A = Q / (eps*sigma*(T^4 - T_sink^4)); emitting "
                "area, planform = emitting / 2 (equal per-face sinks)."
            ),
            source_functions=["radiation.required_area"],
            inputs=[
                _input("Q", Q_W, load_provenance, "W"),
                _input("radiator_temperature", radiator_temperature_K, temperature_provenance, "K"),
                _input("emissivity", emissivity, emissivity_provenance, "-"),
                _input("T_sink_eff", T_sink_K, sink_provenance, "K"),
            ],
        ),
    }


# ---------------------------------------------------------------------------
# Boundary curves (notebook section 5 plots)
# ---------------------------------------------------------------------------

def net_rejection_curve(
    temperatures_K=None,
    *,
    emissivity,
    T_sink_K=0.0,
    t_min=None,
    t_max=None,
    num=200,
    emissivity_provenance=DESIGN_VARIABLE,
    sink_provenance=DESIGN_VARIABLE,
):
    """Net rejected flux (W/m^2) vs radiator temperature (K).

    y = :func:`orbital_thermal.radiation.net_flux` at each T. All temperatures
    must exceed ``T_sink_K`` (the engine requires T > T_sink for net rejection).
    """
    grid = _temperature_grid(temperatures_K, t_min, t_max, num)
    if not np.all(grid > T_sink_K):
        raise ValueError(
            f"every radiator temperature must exceed the sink ({T_sink_K} K) for net "
            "rejection; trim the grid so min(T) > T_sink"
        )
    y = [float(rad.net_flux(float(t), emissivity, T_sink_K)) for t in grid]
    return {
        "x": grid.tolist(),
        "y": y,
        "x_label": "Radiator temperature",
        "y_label": "Net rejected flux (per emitting m^2)",
        "x_unit": "K",
        "y_unit": "W/m^2",
        "title": f"Net rejection vs radiator temperature (eps={emissivity}, T_sink={T_sink_K} K)",
        "meta": _meta(
            units={"x": "K", "y": "W/m^2"},
            convention="Gray-body net flux per emitting face; q = eps*sigma*(T^4 - T_sink^4).",
            source_functions=["radiation.net_flux"],
            inputs=[
                _input("emissivity", emissivity, emissivity_provenance, "-"),
                _input("T_sink_eff", T_sink_K, sink_provenance, "K"),
            ],
        ),
    }


def area_temperature_curve(
    Q_W,
    temperatures_K=None,
    *,
    emissivity,
    T_sink_K=0.0,
    t_min=None,
    t_max=None,
    num=200,
    load_provenance=DESIGN_VARIABLE,
    emissivity_provenance=DESIGN_VARIABLE,
    sink_provenance=DESIGN_VARIABLE,
):
    """Required emitting area (m^2) vs radiator temperature (K), for a fixed load.

    y = :func:`orbital_thermal.radiation.required_area` at each T.
    """
    grid = _temperature_grid(temperatures_K, t_min, t_max, num)
    if not np.all(grid > T_sink_K):
        raise ValueError(
            f"every radiator temperature must exceed the sink ({T_sink_K} K); "
            "trim the grid so min(T) > T_sink"
        )
    emitting = [float(rad.required_area(Q_W, float(t), emissivity, T_sink_K)) for t in grid]
    return {
        "x": grid.tolist(),
        "y": emitting,
        "y_planform": [a / 2.0 for a in emitting],
        "x_label": "Radiator temperature",
        "y_label": "Required emitting area",
        "x_unit": "K",
        "y_unit": "m^2",
        "title": (
            f"Required area vs radiator temperature "
            f"(Q={Q_W/1e3:.0f} kW, eps={emissivity}, T_sink={T_sink_K} K)"
        ),
        "meta": _meta(
            units={"x": "K", "y": "m^2"},
            convention=(
                "Lemma 1 area law; y is emitting area, y_planform = y/2 (equal per-face sinks)."
            ),
            source_functions=["radiation.required_area"],
            inputs=[
                _input("Q", Q_W, load_provenance, "W"),
                _input("emissivity", emissivity, emissivity_provenance, "-"),
                _input("T_sink_eff", T_sink_K, sink_provenance, "K"),
            ],
        ),
    }


def earth_view_factor_curve(
    altitude_km=550.0,
    tilts_deg=None,
    *,
    t_min=0.0,
    t_max=180.0,
    num=181,
    altitude_provenance=DESIGN_VARIABLE,
):
    """Exact tilted-plate-to-sphere Earth view factor vs radiator tilt (deg).

    y = :func:`orbital_thermal.environment.sphere_view_factor` at each tilt.
    ``tilt = 0`` is nadir-facing (maximum coupling), ``90`` is edge-on,
    ``180`` is space-facing. Nadir and edge-on anchors are included in ``meta``.
    """
    if tilts_deg is not None:
        grid = np.asarray(tilts_deg, dtype=float)
    else:
        grid = np.linspace(float(t_min), float(t_max), int(num))
    y = [float(env.sphere_view_factor(altitude_km, float(g))) for g in grid]
    nadir = float(env.nadir_view_factor(altitude_km))
    edge_on = float(env.sphere_view_factor(altitude_km, 90.0))
    return {
        "x": grid.tolist(),
        "y": y,
        "x_label": "Radiator tilt from nadir",
        "y_label": "Earth view factor (exact)",
        "x_unit": "deg",
        "y_unit": "-",
        "title": f"Exact Earth view factor vs tilt ({altitude_km:.0f} km)",
        "nadir_view_factor": nadir,
        "edge_on_view_factor": edge_on,
        "meta": _meta(
            units={"x": "deg", "y": "-"},
            convention=(
                "Exact tilted-plate-to-sphere view factor (Gauss-Legendre, no cosine "
                "approximation); differential-element idealization (no finite-panel self-view)."
            ),
            source_functions=["environment.sphere_view_factor", "environment.nadir_view_factor"],
            inputs=[_input("altitude", altitude_km, altitude_provenance, "km")],
            warnings=[
                "Differential-element idealization: neglects finite-panel self-view and "
                "across-panel gradients (adequate for screening, not detailed panel design)."
            ],
        ),
    }


# ---------------------------------------------------------------------------
# Beta-angle / effective-sink sweeps (notebook section 5)
# ---------------------------------------------------------------------------

def effective_sink_sweep(
    altitude_km=550.0,
    betas_deg=(0, 15, 30, 45, 60, 75, 90),
    tilt_deg=0.0,
    *,
    assume_sun_shielded=True,
    emissivity=0.91,
    solar_absorptivity=0.20,
    altitude_provenance=DESIGN_VARIABLE,
    tilt_provenance=DESIGN_VARIABLE,
    emissivity_provenance=DESIGN_VARIABLE,
    solar_absorptivity_provenance=ASSUMED,
):
    """Radiatively-weighted orbit-mean effective sink (K) vs beta angle.

    y = :func:`orbital_thermal.sink.analytic_orbit_averaged_sink` (the grid-free
    ``(<T_s_eff^4>)^(1/4)``, immune to the coarse-quadrature alias). Each row
    flags ``albedo_model_limited`` where the subpoint-albedo factor nulls
    (beta -> 90 deg). Direct solar is omitted -- the sun-shielded contract applies.
    """
    rows = []
    for b in betas_deg:
        b = float(b)
        alb_mean = sink_mod.analytic_albedo_orbit_mean(b)
        limited = alb_mean < _ALBEDO_LIMIT_EPS
        s = sink_mod.analytic_orbit_averaged_sink(
            altitude_km, b, tilt_deg, assume_sun_shielded=assume_sun_shielded,
            emissivity=emissivity, solar_absorptivity=solar_absorptivity)
        rows.append({
            "beta_deg": b,
            "orbit_averaged_sink_K": float(s),
            "view_factor": float(env.sphere_view_factor(altitude_km, tilt_deg)),
            "albedo_orbit_mean_factor": float(alb_mean),
            "albedo_model_limited": bool(limited),
            "is_beta90_endpoint": bool(b >= 90.0 - 1e-9),
        })
    return {
        "rows": rows,
        "x_label": "Orbit beta angle",
        "y_label": "Radiatively-weighted orbit-mean effective sink",
        "x_unit": "deg",
        "y_unit": "K",
        "title": f"Effective sink vs beta ({altitude_km:.0f} km, tilt={tilt_deg:.0f} deg)",
        "meta": _meta(
            units={"beta": "deg", "sink": "K"},
            convention=(
                "T_s^eff = ((q_IR + (alpha_s/eps)*q_albedo + sigma*T_space^4)/sigma)^(1/4); "
                "radiatively-weighted (T^4) orbit mean; grid-free closed form."
            ),
            source_functions=[
                "sink.analytic_orbit_averaged_sink",
                "sink.analytic_albedo_orbit_mean",
                "environment.sphere_view_factor",
            ],
            inputs=[
                _input("altitude", altitude_km, altitude_provenance, "km"),
                _input("tilt", tilt_deg, tilt_provenance, "deg"),
                _input("emissivity", emissivity, emissivity_provenance, "-"),
                _input("solar_absorptivity", solar_absorptivity,
                       solar_absorptivity_provenance, "-"),
            ],
            assumptions=[BETA90_ALBEDO_LIMITATION],
            warnings=(
                [BETA90_ALBEDO_LIMITATION]
                if any(r["albedo_model_limited"] for r in rows) else []
            ),
            sun_shielded=assume_sun_shielded,
        ),
    }


def beta_sweep(
    altitude_km=550.0,
    betas_deg=(0, 15, 30, 45, 60, 75, 90),
    tilt_deg=0.0,
    *,
    Q_W=120_000.0,
    emitting_area_m2=220.0,
    emissivity=0.91,
    radiator_temperature_K=293.15,
    solar_absorptivity=0.20,
    assume_sun_shielded=True,
    load_provenance=DESIGN_VARIABLE,
    area_provenance=DESIGN_VARIABLE,
    emissivity_provenance=DESIGN_VARIABLE,
    temperature_provenance=DESIGN_VARIABLE,
    solar_absorptivity_provenance=ASSUMED,
    altitude_provenance=DESIGN_VARIABLE,
    tilt_provenance=DESIGN_VARIABLE,
):
    """Beta-angle sensitivity of the radiator BOUNDARY, driven by the orbit-mean sink.

    For each beta this computes the orbit-mean effective sink
    (:func:`orbital_thermal.sink.analytic_orbit_averaged_sink`) and feeds it into
    the boundary model:

    * ``equilibrium_temperature_K`` -- :func:`orbital_thermal.equilibrium.equilibrium_temperature`
      for the fixed load/area (always defined);
    * ``required_emitting_area_m2`` -- :func:`orbital_thermal.radiation.required_area`
      to hold ``radiator_temperature_K`` (``None`` when the sink meets/exceeds
      that temperature, i.e. no finite area rejects heat there).

    Shows how sensitive the boundary is to beta. The sun-shielded contract and the
    beta-90 albedo limitation apply.
    """
    rows = []
    for b in betas_deg:
        b = float(b)
        alb_mean = sink_mod.analytic_albedo_orbit_mean(b)
        limited = alb_mean < _ALBEDO_LIMIT_EPS
        s = sink_mod.analytic_orbit_averaged_sink(
            altitude_km, b, tilt_deg, assume_sun_shielded=assume_sun_shielded,
            emissivity=emissivity, solar_absorptivity=solar_absorptivity)
        T_eq = eq.equilibrium_temperature(Q_W, emitting_area_m2, emissivity, s)
        # Explicit domain guard (rather than swallowing the engine's ValueError, which
        # would also mask unrelated bad-input errors): net rejection needs T > sink.
        if radiator_temperature_K > s:
            a_req = float(rad.required_area(Q_W, radiator_temperature_K, emissivity, s))
        else:
            a_req = None  # sink meets/exceeds the target temperature: no finite area
        rows.append({
            "beta_deg": b,
            "orbit_averaged_sink_K": float(s),
            "equilibrium_temperature_K": float(T_eq),
            "required_emitting_area_m2": a_req,
            "albedo_model_limited": bool(limited),
            "is_beta90_endpoint": bool(b >= 90.0 - 1e-9),
        })
    return {
        "rows": rows,
        "x_label": "Orbit beta angle",
        "x_unit": "deg",
        "title": f"Boundary sensitivity to beta ({altitude_km:.0f} km, tilt={tilt_deg:.0f} deg)",
        "meta": _meta(
            units={"beta": "deg", "sink": "K", "temperature": "K", "area": "m^2"},
            convention=(
                "Orbit-mean effective sink drives equilibrium_temperature (fixed Q/area) "
                "and required_area (fixed radiator T). Emitting area; equal per-face sinks."
            ),
            source_functions=[
                "sink.analytic_orbit_averaged_sink",
                "equilibrium.equilibrium_temperature",
                "radiation.required_area",
            ],
            inputs=[
                _input("altitude", altitude_km, altitude_provenance, "km"),
                _input("tilt", tilt_deg, tilt_provenance, "deg"),
                _input("Q", Q_W, load_provenance, "W"),
                _input("emitting_area", emitting_area_m2, area_provenance, "m^2"),
                _input("emissivity", emissivity, emissivity_provenance, "-"),
                _input("radiator_temperature", radiator_temperature_K, temperature_provenance, "K"),
                _input("solar_absorptivity", solar_absorptivity,
                       solar_absorptivity_provenance, "-"),
            ],
            assumptions=[BETA90_ALBEDO_LIMITATION],
            warnings=(
                [BETA90_ALBEDO_LIMITATION]
                if any(r["albedo_model_limited"] for r in rows) else []
            ),
            sun_shielded=assume_sun_shielded,
        ),
    }


def sink_profile_case(
    altitude_km=550.0,
    beta_deg=30.0,
    tilt_deg=0.0,
    n=361,
    *,
    assume_sun_shielded=True,
    emissivity=0.91,
    solar_absorptivity=0.20,
):
    """Effective sink (K) vs in-orbit angle u (deg) over one full orbit.

    x, y = :func:`orbital_thermal.sink.sink_profile`. Useful for showing the sink
    swing that drives the transient. Direct solar omitted (sun-shielded contract).
    """
    u, T = sink_mod.sink_profile(
        altitude_km, beta_deg, tilt_deg, n=n, assume_sun_shielded=assume_sun_shielded,
        emissivity=emissivity, solar_absorptivity=solar_absorptivity)
    return {
        "x": np.asarray(u, dtype=float).tolist(),
        "y": np.asarray(T, dtype=float).tolist(),
        "x_label": "In-orbit angle from orbit noon (u)",
        "y_label": "Effective sink temperature",
        "x_unit": "deg",
        "y_unit": "K",
        "title": (
            f"Effective sink over one orbit "
            f"(beta={beta_deg:.0f} deg, {altitude_km:.0f} km, tilt={tilt_deg:.0f} deg)"
        ),
        "meta": _meta(
            units={"x": "deg", "y": "K"},
            convention=(
                "Instantaneous subpoint-model effective sink around the orbit; "
                "endpoint duplicated (0 == 360 deg)."
            ),
            source_functions=["sink.sink_profile"],
            inputs=[
                _input("altitude", altitude_km, DESIGN_VARIABLE, "km"),
                _input("beta", beta_deg, DESIGN_VARIABLE, "deg"),
                _input("tilt", tilt_deg, DESIGN_VARIABLE, "deg"),
                _input("emissivity", emissivity, DESIGN_VARIABLE, "-"),
                _input("solar_absorptivity", solar_absorptivity, ASSUMED, "-"),
            ],
            assumptions=[BETA90_ALBEDO_LIMITATION],
            sun_shielded=assume_sun_shielded,
        ),
    }


# ---------------------------------------------------------------------------
# McCalip heuristic vs exact view factor (notebook section 5)
# ---------------------------------------------------------------------------

def mccalip_view_factor_comparison(
    betas_deg=mvf.DEFAULT_BETAS,
    altitude_km=None,
    n=72,
):
    """McCalip cos-tilt heuristic vs exact per-face Earth view factor, and the
    resulting equilibrium-temperature correction, vs beta.

    Per beta this returns the McCalip heuristic side-A view factor
    (:func:`orbital_thermal.mccalip_replication.sun_tracking_view_factors`), the
    exact per-face view factors
    (:func:`orbital_thermal.mccalip_exact_vf.exact_per_face_view_factors`), and
    the replicated vs exact-VF equilibrium temperatures with their delta
    (:func:`orbital_thermal.mccalip_exact_vf.correction_table_vs_beta`).

    ``altitude_km=None`` uses McCalip's default state altitude (550 km).
    """
    overrides = None if altitude_km is None else {"orbitalAltitudeKm": float(altitude_km)}
    alt = mc._state(overrides)["orbitalAltitudeKm"]
    table = mvf.correction_table_vs_beta(tuple(betas_deg), overrides=overrides, n=n)
    rows = []
    for entry in table:
        b = float(entry["beta_deg"])
        heur = mc.sun_tracking_view_factors(alt, b)
        vf_a_exact, vf_b_exact = mvf.exact_per_face_view_factors(alt, b, n=n)
        rows.append({
            "beta_deg": b,
            "vf_side_a_mccalip_heuristic": float(heur["vfSideA"]),
            "vf_side_b_mccalip_heuristic": float(heur["vfSideB"]),
            "vf_side_a_exact": float(vf_a_exact),
            "vf_side_b_exact": float(vf_b_exact),
            "eqtemp_mccalip_K": float(entry["eqtemp_mccalip_K"]),
            "eqtemp_exact_K": float(entry["eqtemp_exact_K"]),
            "delta_K": float(entry["delta_K"]),
        })
    return {
        "rows": rows,
        "altitude_km": float(alt),
        "x_label": "Orbit beta angle",
        "x_unit": "deg",
        "title": (
            f"McCalip heuristic vs exact view factor + eq-temperature correction ({alt:.0f} km)"
        ),
        "meta": _meta(
            units={"beta": "deg", "view_factor": "-", "temperature": "K"},
            convention=(
                "McCalip's own heat balance held fixed; only the per-face Earth view "
                "factor is swapped (cos-tilt heuristic + 5% edge-on floor vs exact "
                "tilted-plate-to-sphere). Replication uses his truncated sigma=5.67e-8, "
                "T_space=3 K, and 72-point orbit average."
            ),
            source_functions=[
                "mccalip_exact_vf.correction_table_vs_beta",
                "mccalip_exact_vf.exact_per_face_view_factors",
                "mccalip_replication.sun_tracking_view_factors",
            ],
            inputs=[
                _input("altitude", alt, DESIGN_VARIABLE, "km"),
                _input("mccalip_default_state", "DEFAULT_STATE", PUBLISHED, "-"),
            ],
            warnings=[
                "This is a REPLICATION + geometry correction of an external model, not a "
                "validation of McCalip's model against reality.",
                "Coarse-quadrature/subpoint aliasing: 72-point orbit average and cos-tilt "
                "heuristic alias finer orbital geometry.",
            ],
        ),
    }


# ---------------------------------------------------------------------------
# Orbital transient waveform (notebook section 5)
# ---------------------------------------------------------------------------

def transient_orbit_case(
    altitude_km=550.0,
    beta_deg=0.0,
    q_load_W_m2=545.0,
    areal_heat_capacity=None,
    build_name=None,
    tilt_deg=0.0,
    *,
    assume_sun_shielded=True,
    emissivity=0.91,
    solar_absorptivity=0.20,
    n_orbits=40,
    steps_per_orbit=1440,
    q_load_provenance=DESIGN_VARIABLE,
    capacity_provenance=DESIGN_VARIABLE,
):
    """One-node orbital transient waveform for the final (periodic) orbit.

    Wraps :func:`orbital_thermal.transient.simulate` (RK4, marched to a periodic
    steady state) and returns the panel and effective-sink waveforms plus a
    summary (peak, mean, swing, steady-at-averaged-sink, thermal time constant,
    tau/period) and the engine's convergence diagnostics.

    Provide the areal heat capacity either directly (``areal_heat_capacity``,
    J/m^2/K) or by naming a representative build
    (``build_name`` in :data:`orbital_thermal.transient.REPRESENTATIVE_BUILDS`,
    resolved via :func:`orbital_thermal.transient.build_areal_heat_capacity`).
    Direct solar is omitted -- the sun-shielded contract applies.
    """
    if areal_heat_capacity is None and build_name is None:
        raise ValueError("provide areal_heat_capacity (J/m^2/K) or build_name")
    if build_name is not None:
        C = tr.build_areal_heat_capacity(build_name)
        capacity_provenance = DERIVED  # derived from a documented material stack
    else:
        C = float(areal_heat_capacity)

    t, T, T_sink, diag = tr.simulate(
        altitude_km, beta_deg, q_load_W_m2, C, tilt_deg=tilt_deg,
        assume_sun_shielded=assume_sun_shielded, emissivity=emissivity,
        solar_absorptivity=solar_absorptivity, n_orbits=n_orbits,
        steps_per_orbit=steps_per_orbit, return_diagnostics=True)

    T = np.asarray(T, dtype=float)
    T_sink = np.asarray(T_sink, dtype=float)
    t = np.asarray(t, dtype=float)
    # Radiatively-weighted average sink over the orbit (drop duplicated endpoint).
    sink_avg = float(np.mean(T_sink[:-1] ** 4) ** 0.25)
    steady = tr.steady_state_temperature(q_load_W_m2, sink_avg, emissivity)
    mean_T = float(np.mean(T[:-1]))
    peak_T = float(T.max())
    tau = tr.thermal_time_constant(C, mean_T, emissivity)
    period = env.orbital_period(altitude_km)
    warnings = []
    if not diag["converged"]:
        warnings.append(
            "Transient did NOT reach a certified periodic steady state at these "
            "settings; peak/mean/swing are not certified. Increase n_orbits and/or "
            "steps_per_orbit (see diagnostics)."
        )
    return {
        "t_s": t.tolist(),
        "t_min": (t / 60.0).tolist(),
        "T_panel_K": T.tolist(),
        "T_sink_K": T_sink.tolist(),
        "areal_heat_capacity_J_m2K": float(C),
        "summary": {
            "transient_peak_K": peak_T,
            "transient_mean_K": mean_T,
            "swing_K": float(T.max() - T.min()),
            "steady_avg_sink_K": float(steady),
            "peak_excess_over_steady_K": float(peak_T - steady),
            "avg_sink_K": sink_avg,
            "tau_s": float(tau),
            "period_s": float(period),
            "tau_over_period": float(tau / period),
            "converged": bool(diag["converged"]),
            "periodic_converged": bool(diag["periodic_converged"]),
            "orbits_used": int(diag["orbits_used"]),
        },
        "x_label": "Time into final orbit",
        "y_label": "Temperature",
        "x_unit": "min",
        "y_unit": "K",
        "title": (
            f"Transient over one orbit (beta={beta_deg:.0f} deg, {altitude_km:.0f} km, "
            f"q={q_load_W_m2:.0f} W/m^2, C={C:.0f} J/m^2/K)"
        ),
        "meta": _meta(
            units={"time": "s/min", "temperature": "K", "capacity": "J/m^2/K"},
            convention=(
                "One-node areal model C dT/dt = q_load - eps*sigma*(T^4 - T_s_eff(t)^4); "
                "final periodic orbit; radiatively-weighted average sink for the steady comparison."
            ),
            source_functions=[
                "transient.simulate",
                "transient.steady_state_temperature",
                "transient.thermal_time_constant",
                ("transient.build_areal_heat_capacity"
                 if build_name is not None else "transient.simulate"),
            ],
            inputs=[
                _input("altitude", altitude_km, DESIGN_VARIABLE, "km"),
                _input("beta", beta_deg, DESIGN_VARIABLE, "deg"),
                _input("tilt", tilt_deg, DESIGN_VARIABLE, "deg"),
                _input("q_load", q_load_W_m2, q_load_provenance, "W/m^2"),
                _input("areal_heat_capacity", C, capacity_provenance, "J/m^2/K"),
                _input("emissivity", emissivity, DESIGN_VARIABLE, "-"),
                _input("solar_absorptivity", solar_absorptivity, ASSUMED, "-"),
            ],
            assumptions=[BETA90_ALBEDO_LIMITATION],
            warnings=warnings,
            sun_shielded=assume_sun_shielded,
        ),
    }


# ---------------------------------------------------------------------------
# Reference-case table (notebook section 6)
# ---------------------------------------------------------------------------

#: Biswas / Suncatcher reference: RECORDED as a pinned future case, never ranked.
BISWAS_REFERENCE = {
    "release_tag": "v1.2",
    "short_commit_sha": "23053beeff53",
    "full_commit_sha": None,  # to be resolved and recorded (integrated-program-roadmap R0 intake)
    "repository": "https://github.com/Samarjithbiswas/space-based-ai-datacenter",
    "status": (
        "Future Stage-2 (two-phase) benchmark; NOT in the current package and NOT a "
        "ranked Phase B Stage-1 case. Author cross-check is source-author review, not "
        "independent external validation. Public documentation requires project-director approval."
    ),
}


def reference_case_table(load_W=120_000.0, harmonized_beta_deg=45.0):
    """Labelled reference-case table for cases the CURRENT package supports, plus
    recorded future/unsupported entries.

    Each row carries a ``label`` in {published, harmonized, sensitivity,
    unsupported, future}, a conservative ``rank_eligible`` flag, and the source.
    ``ranking_performed`` is always ``False``: this is a labelled inventory, not a
    ranking (as-published cases are never a ranking basis, and AI1's unpublished
    solar absorptivity leaves its harmonized albedo unresolved).

    Values are produced by the engine:
    :class:`orbital_thermal.architecture_comparison.AI1_DESIGN_POINT` (AI1),
    :func:`orbital_thermal.reference_architectures.starcloud_published_balance` /
    ``starcloud_spectral_balance`` (Starcloud),
    :func:`orbital_thermal.harmonized_comparison.ai1_harmonized_balance` /
    ``starcloud_harmonized_balance`` (harmonized),
    :func:`orbital_thermal.mccalip_exact_vf.correction_table_vs_beta` (McCalip).
    """
    ai1 = arch.AI1_DESIGN_POINT
    sc_pub = refarch.starcloud_published_balance()
    sc_spec = refarch.starcloud_spectral_balance()
    ai1_h = harm.ai1_harmonized_balance(harmonized_beta_deg, warn=False)
    sc_h = harm.starcloud_harmonized_balance(harmonized_beta_deg, sunlit_faces=0, warn=False)
    mc_row = mvf.correction_table_vs_beta((90.0,))[0]

    rows = [
        {
            "name": "AI1 design point (sustained)",
            "label": CASE_PUBLISHED,
            "rank_eligible": False,
            "radiator_temperature_K": float(ai1.radiator_temperature_K(load_W)),
            "net_rejection_W_m2": None,
            "net_flux_per_emitting_m2_W_m2": float(ai1.net_flux_per_emitting_m2(load_W)),
            "convention": (
                "Lumped effective sink T_s^eff = 220 K; T derived from published "
                "load/area/eps/sink."
            ),
            "value_provenance": {
                "radiator_temperature_K": DERIVED, "effective_sink_K": PUBLISHED,
            },
            "source": ai1.source,
            "notes": (
                "AI1 does NOT separately publish solar absorptivity / Earth view factor / "
                "direct-solar term (folded into its sink). As-published => not a ranking basis."
            ),
        },
        {
            "name": "Starcloud 2024 (published, as-written)",
            "label": CASE_PUBLISHED,
            "rank_eligible": False,
            "radiator_temperature_K": float(sc_pub.radiator_temperature_K),
            "net_rejection_W_m2": float(sc_pub.net_rejection_W_m2),
            "net_flux_per_emitting_m2_W_m2": float(sc_pub.net_rejection_W_m2 / 2.0),
            "convention": (
                "White-paper single-absorptivity (0.09) balance; rounded sigma=5.67e-8."
            ),
            "value_provenance": {
                "net_rejection_W_m2": PUBLISHED, "radiator_temperature_K": PUBLISHED,
            },
            "source": sc_pub.source,
            "notes": "Reproduces the white paper's printed 633.08 W/m^2 net.",
        },
        {
            "name": "Starcloud 2024 (spectral separation)",
            "label": CASE_SENSITIVITY,
            "rank_eligible": False,
            "radiator_temperature_K": float(sc_spec.radiator_temperature_K),
            "net_rejection_W_m2": float(sc_spec.net_rejection_W_m2),
            "net_flux_per_emitting_m2_W_m2": float(sc_spec.net_rejection_W_m2 / 2.0),
            "convention": (
                "Kirchhoff: long-wave absorptivity = emissivity (0.92); short-wave unchanged."
            ),
            "value_provenance": {"net_rejection_W_m2": CORRECTED},
            "source": sc_spec.source,
            "notes": (
                "Alternative radiative-property treatment (sensitivity), NOT a claim the "
                "design is wrong."
            ),
        },
        {
            "name": f"AI1 (harmonized, beta={harmonized_beta_deg:.0f} deg)",
            "label": CASE_HARMONIZED,
            # albedo unresolved (alpha_s unpublished) -> not fully comparable
            "rank_eligible": False,
            "radiator_temperature_K": float(ai1_h.radiator_temperature_K),
            "net_rejection_W_m2": (
                None if ai1_h.net_rejection_W_m2 is None else float(ai1_h.net_rejection_W_m2)
            ),
            "net_excluding_albedo_W_m2": (
                None if ai1_h.net_excluding_albedo_W_m2 is None
                else float(ai1_h.net_excluding_albedo_W_m2)
            ),
            "convention": (
                "Shared orbit environment (F, IR, albedo, SI sigma, Kirchhoff); shielded/edge-on."
            ),
            "value_provenance": {
                "net_excluding_albedo_W_m2": HARMONIZED_PROVENANCE,
                "solar_absorptivity": UNSUPPORTED_FUTURE,
            },
            "source": ai1.source,
            "notes": (
                "Full net is None: AI1 publishes no solar absorptivity, so albedo is left "
                "uncomputed (no-invention). Only net_excluding_albedo is reportable."
            ),
        },
        {
            "name": f"Starcloud (harmonized, beta={harmonized_beta_deg:.0f} deg)",
            "label": CASE_HARMONIZED,
            "rank_eligible": (sc_h.net_rejection_W_m2 is not None),
            "radiator_temperature_K": float(sc_h.radiator_temperature_K),
            "net_rejection_W_m2": (
                None if sc_h.net_rejection_W_m2 is None else float(sc_h.net_rejection_W_m2)
            ),
            "net_excluding_albedo_W_m2": (
                None if sc_h.net_excluding_albedo_W_m2 is None
                else float(sc_h.net_excluding_albedo_W_m2)
            ),
            "convention": (
                "Shared orbit environment; shielded (sunlit_faces=0); published "
                "eps=0.92, alpha_s=0.09."
            ),
            "value_provenance": {"net_rejection_W_m2": HARMONIZED_PROVENANCE},
            "source": sc_pub.source,
            "notes": (
                "rank_eligible only reflects a fully-resolved reportable net at this beta; "
                "ranking is still NOT performed here (B0.5 scope)."
            ),
        },
        {
            "name": "McCalip (edge-on, exact-VF correction, beta=90 deg)",
            "label": CASE_PUBLISHED,
            "rank_eligible": False,
            "radiator_temperature_K": float(mc_row["eqtemp_mccalip_K"]),
            "eqtemp_exact_vf_K": float(mc_row["eqtemp_exact_K"]),
            "delta_K": float(mc_row["delta_K"]),
            "net_rejection_W_m2": None,
            "convention": (
                "McCalip's own heat balance; his replicated eqtemp is published, "
                "exact-VF is corrected."
            ),
            "value_provenance": {
                "radiator_temperature_K": PUBLISHED, "eqtemp_exact_vf_K": CORRECTED,
            },
            "source": (
                "andrewmccalip/thoughts (replicated); exact-VF correction: "
                "doi:10.5281/zenodo.20695720"
            ),
            "notes": (
                "Replication + geometry correction of an external model; not a validation "
                "against reality."
            ),
        },
        {
            "name": "Biswas / Suncatcher (v1.2)",
            "label": CASE_FUTURE,
            "rank_eligible": False,
            "radiator_temperature_K": None,
            "net_rejection_W_m2": None,
            "convention": (
                "Two-phase heat-pipe architecture; not modelled by the current single-node package."
            ),
            "value_provenance": {},
            "source": (
                f"{BISWAS_REFERENCE['repository']} @ {BISWAS_REFERENCE['release_tag']} "
                f"(short SHA {BISWAS_REFERENCE['short_commit_sha']}; full SHA to be resolved)"
            ),
            "notes": BISWAS_REFERENCE["status"],
        },
        {
            "name": "Disk-integrated albedo model",
            "label": CASE_UNSUPPORTED,
            "rank_eligible": False,
            "radiator_temperature_K": None,
            "net_rejection_W_m2": None,
            "convention": (
                "Physically-faithful replacement for the subpoint albedo approximation."
            ),
            "value_provenance": {},
            "source": (
                "sink.disk_integrated_albedo_factor (raises NotImplementedError; "
                "strict-xfail tests)"
            ),
            "notes": (
                "Not implemented: the package uses the subpoint albedo approximation, whose "
                "beta-90 null is a model limitation. Recorded here so the gap is visible."
            ),
        },
    ]

    for r in rows:
        if r["label"] not in REFERENCE_CASE_LABELS:
            raise ValueError(f"row {r['name']!r} has unknown label {r['label']!r}")
        # Safety invariant: future/unsupported cases can never be rank-eligible.
        if r["label"] in (CASE_FUTURE, CASE_UNSUPPORTED) and r["rank_eligible"]:
            raise AssertionError(f"{r['name']!r} is {r['label']} and must not be rank_eligible")

    return {
        "rows": rows,
        "ranking_performed": False,
        "columns": [
            "name", "label", "rank_eligible", "radiator_temperature_K",
            "net_rejection_W_m2", "source", "notes",
        ],
        "meta": _meta(
            units={"temperature": "K", "flux": "W/m^2"},
            convention=(
                "Labelled inventory of package-supported reference cases plus recorded "
                "future/unsupported entries. As-published is NOT a ranking; harmonized is "
                "like-for-like only when fully resolved; no invention on missing alpha_s."
            ),
            source_functions=[
                "architecture_comparison.AI1_DESIGN_POINT",
                "reference_architectures.starcloud_published_balance",
                "reference_architectures.starcloud_spectral_balance",
                "harmonized_comparison.ai1_harmonized_balance",
                "harmonized_comparison.starcloud_harmonized_balance",
                "mccalip_exact_vf.correction_table_vs_beta",
            ],
            inputs=[
                _input("load", load_W, DESIGN_VARIABLE, "W"),
                _input("harmonized_beta", harmonized_beta_deg, DESIGN_VARIABLE, "deg"),
            ],
            warnings=[
                "ranking_performed=False: this table labels provenance/convention; it does "
                "not rank architectures (requires harmonized, fully-resolved, gated cases).",
                BETA90_ALBEDO_LIMITATION,
            ],
        ),
    }
