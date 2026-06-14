"""Recompute McCalip's orbital-datacenter equilibrium temperature with the EXACT
tilted-plate-to-sphere Earth view factor in place of his cos-tilt heuristic.

Headline result (paper three). At McCalip's default geometry (beta = 90 deg,
550 km) a sun-tracking bifacial panel is EDGE-ON to Earth: the panel normal
tracks the Sun, which at beta = 90 deg is normal to the orbit plane, while nadir
lies in the plane -- 90 deg away. His per-face view-factor floor averages ~0.021
per face around the orbit there; the exact tilted-plate-to-sphere view factor is
~0.258, a ~12x underestimate. Substituting the exact per-face view factor into
his own heat balance raises his default equilibrium temperature

    335.75 K  (McCalip, replicated)  ->  342.10 K  (exact edge-on VF)   +6.35 K

This is a quantified new result, not a defect in the replication.
:mod:`orbital_thermal.mccalip_replication` remains a faithful port of his model;
this module isolates the single geometric approximation in that model and shows
what his own heat balance gives once it is replaced by the exact integral. Only
the view factor changes -- his truncated sigma, rounded deep-space temperature,
constants, and orbit sampling are all retained, so the temperature shift is
attributable to geometry alone (see :func:`equilibrium_temperature_with_view_factors`,
which reproduces his number exactly when fed his own view factors).
"""

import math

from . import environment as env
from . import mccalip_replication as mc
from . import _validate as _v


def exact_per_face_view_factors(altitude_km, beta_deg, n=72):
    """Orbit-averaged exact Earth view factor for each face of a sun-tracking
    bifacial panel, returned as ``(vf_side_a, vf_side_b)``.

    Mirrors McCalip's orbit sampling (``n``-point average, his default 72) and
    his per-face tilt cosines -- side A's normal makes cos(tilt) = cos(beta)*
    cos(nu) with nadir, side B is the opposite face -- but evaluates the EXACT
    tilted-plate-to-sphere view factor (:func:`environment.sphere_view_factor`)
    at each orbit step instead of his cos-tilt heuristic with a 5% edge-on floor.
    """
    _v.positive("altitude_km", altitude_km)
    _v.in_range("beta_deg", beta_deg, 0.0, 90.0)
    _v.positive_int("n", n)
    beta = math.radians(beta_deg)
    a = b = 0.0
    for i in range(n):
        nu = 2.0 * math.pi * i / n
        c = max(-1.0, min(1.0, math.cos(beta) * math.cos(nu)))
        a += env.sphere_view_factor(altitude_km, math.degrees(math.acos(c)))
        b += env.sphere_view_factor(altitude_km, math.degrees(math.acos(-c)))
    return a / n, b / n


def equilibrium_temperature_with_view_factors(overrides, vf_side_a, vf_side_b):
    """McCalip's ``calculate_thermal`` heat balance with arbitrary per-face Earth
    view factors. Fed his own (heuristic) view factors, this reproduces
    ``calculate_thermal(...)['eqTempK']`` to floating-point roundoff -- so any
    temperature change comes from the view factors alone.
    """
    _v.in_range("vf_side_a", vf_side_a, 0.0, 1.0)
    _v.in_range("vf_side_b", vf_side_b, 0.0, 1.0)
    s = mc._state(overrides)
    area = mc.calculate_orbital(s)["_arrayAreaM2"]
    S = mc.CONST["SOLAR_IRRADIANCE_W_M2"]
    e_ir = mc.CONST["EARTH_IR_FLUX_W_M2"]
    alb = mc.CONST["EARTH_ALBEDO_FACTOR"]
    alpha_pv, eps_pv, eps_rad = s["solarAbsorptivity"], s["emissivityPV"], s["emissivityRad"]
    pv_eff, beta = s["pvEfficiency"], s["betaAngle"]
    power_generated = S * pv_eff * area
    q_solar_waste = S * alpha_pv * area - power_generated
    q_earth_ir = e_ir * vf_side_a * eps_pv * area + e_ir * vf_side_b * eps_rad * area
    q_albedo = S * alb * vf_side_a * math.cos(math.radians(beta)) * alpha_pv * area
    q_heat_loop = power_generated
    total_heat_in = q_solar_waste + q_earth_ir + q_albedo + q_heat_loop
    total_eps = eps_pv + eps_rad
    return float((total_heat_in / (mc.SIGMA * area * total_eps) + mc.T_SPACE_K**4) ** 0.25)


def eqtemp_exact_vf(overrides=None, n=72):
    """McCalip equilibrium temperature (K) recomputed with exact per-face Earth
    view factors at the given state (defaults: beta = 90 deg, 550 km)."""
    s = mc._state(overrides)
    vf_a, vf_b = exact_per_face_view_factors(s["orbitalAltitudeKm"], s["betaAngle"], n=n)
    return equilibrium_temperature_with_view_factors(overrides, vf_a, vf_b)


# Default beta grid for the correction table (the oracle grid plus midpoints).
DEFAULT_BETAS = (0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0)


def correction_table_vs_beta(betas=DEFAULT_BETAS, overrides=None, n=72):
    """Tabulate the equilibrium-temperature correction vs orbit beta angle.

    For each beta this compares McCalip's own replicated equilibrium temperature
    (his cos-tilt view-factor heuristic) with the same heat balance evaluated
    using the exact per-face Earth view factor. Returns a list of dicts with keys
    ``beta_deg``, ``eqtemp_mccalip_K``, ``eqtemp_exact_K``, ``delta_K``
    (= exact - McCalip). The correction is positive at every beta and grows
    monotonically toward the edge-on default (beta = 90 deg), where it is +6.35 K.
    """
    _v.positive_int("n", n)
    for _b in betas:
        _v.in_range("beta_deg", _b, 0.0, 90.0)
    base = dict(overrides or {})
    rows = []
    for beta in betas:
        ov = dict(base, betaAngle=beta)
        mccalip = mc.calculate_thermal(mc._state(ov))["eqTempK"]
        exact = eqtemp_exact_vf(ov, n=n)
        rows.append({
            "beta_deg": float(beta),
            "eqtemp_mccalip_K": float(mccalip),
            "eqtemp_exact_K": float(exact),
            "delta_K": float(exact - mccalip),
        })
    return rows
