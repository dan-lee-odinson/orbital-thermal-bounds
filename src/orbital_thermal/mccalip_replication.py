"""Independent Python replication of the McCalip orbital thermal/cost model.

This is a faithful port of ``static/js/math.js`` from
https://github.com/andrewmccalip/thoughts at the pinned commit
d1e4238d3d3f4924e5ca65bafbd4ba5b39af2eb8 (see
``external_models/mccalip_thoughts/provenance.md``). It exists to *replicate* his
result in a second language and check our understanding of his model against the
frozen Node oracle (``expected_outputs.json``).

Three distinct claims must not be conflated (see the replication report):

* Replication -- does this Python reproduce his JavaScript's numbers? This module
  uses his exact constants (including the truncated sigma = 5.67e-8 and the
  rounded deep-space temperature T_space = 3 K) and matches the oracle to ~1e-9.
* Verification -- is the underlying physics internally correct? That is the job
  of :mod:`orbital_thermal` and its published-results suite, which use the exact
  CODATA sigma and the exact view-factor integral.
* Validation -- does the model match reality? Neither this module nor the core
  package claims that; it is the open question the third paper frames.

Because the goal is faithful replication, this module deliberately keeps
McCalip's approximations (the 72-point orbit average, the cos-tilt view-factor
heuristic, the 5% edge-on floor) rather than the exact forms in
:mod:`orbital_thermal.environment`.
"""

import math

# McCalip's truncated Stefan-Boltzmann constant (his math.js value).
SIGMA = 5.67e-8
T_SPACE_K = 3.0

# Constants block from math.js (defaults).
CONST = {
    "HOURS_PER_YEAR": 8760,
    "STARLINK_POWER_KW": 27,
    "STARLINK_ARRAY_M2": 116,
    "STARSHIP_PAYLOAD_KG": 100000,
    "ORBITAL_OPS_FRAC": 0.01,
    "SOLAR_IRRADIANCE_W_M2": 1361,
    "EARTH_IR_FLUX_W_M2": 237,
    "EARTH_ALBEDO_FACTOR": 0.30,
    "EARTH_RADIUS_KM": 6371.0,
}

# State block from math.js (defaults).
DEFAULT_STATE = {
    "years": 5,
    "targetGW": 1,
    "solarAbsorptivity": 0.92,
    "emissivityPV": 0.85,
    "emissivityRad": 0.90,
    "pvEfficiency": 0.22,
    "betaAngle": 90,
    "orbitalAltitudeKm": 550,
    "maxDieTempC": 85,
    "tempDropC": 10,
    "launchCostPerKg": 500,
    "satelliteCostPerW": 22,
    "specificPowerWPerKg": 36.5,
    "satellitePowerKW": 27,
    "sunFraction": 0.98,
    "cellDegradation": 2.5,
    "gpuFailureRate": 9,
    "nreCost": 1000,
    "gasTurbineCapexPerKW": 1800,
    "electricalCostPerW": 5.25,
    "mechanicalCostPerW": 3.0,
    "civilCostPerW": 2.5,
    "networkCostPerW": 1.75,
    "pue": 1.2,
    "gasPricePerMMBtu": 4.30,
    "heatRateBtuKwh": 6200,
    "capacityFactor": 0.85,
}


def _state(overrides=None):
    s = dict(DEFAULT_STATE)
    if overrides:
        s.update(overrides)
    return s


def _derived(s):
    target_power_mw = s["targetGW"] * 1000
    return {
        "TARGET_POWER_MW": target_power_mw,
        "TARGET_POWER_W": target_power_mw * 1e6,
    }


# --- View factors (ported verbatim, including approximations) ---

def earth_angular_radius(alt_km):
    r = CONST["EARTH_RADIUS_KM"] + alt_km
    return math.asin(CONST["EARTH_RADIUS_KM"] / r)


def nadir_view_factor(alt_km):
    return math.sin(earth_angular_radius(alt_km)) ** 2


def _tilted_vf_from_cos(alt_km, cos_tilt):
    theta = earth_angular_radius(alt_km)
    vf_nadir = math.sin(theta) ** 2
    if cos_tilt <= 0:
        return vf_nadir * 0.05
    return vf_nadir * cos_tilt


def sun_tracking_view_factors(alt_km, beta_deg):
    beta = math.radians(beta_deg)
    n = 72
    a_sum = b_sum = 0.0
    for i in range(n):
        nu = 2 * math.pi * i / n
        cos_gamma = math.cos(beta) * math.cos(nu)
        a_sum += _tilted_vf_from_cos(alt_km, cos_gamma)
        b_sum += _tilted_vf_from_cos(alt_km, -cos_gamma)
    return {"vfSideA": a_sum / n, "vfSideB": b_sum / n, "vfTotal": (a_sum + b_sum) / n}


# --- Orbital cost model ---

def calculate_orbital(s):
    d = _derived(s)
    total_hours = s["years"] * CONST["HOURS_PER_YEAR"]
    annual_retention = 1 - s["cellDegradation"] / 100
    capacity_sum = sum(annual_retention**y for y in range(s["years"]))
    avg_capacity_factor = capacity_sum / s["years"]
    sunlight_adjusted = avg_capacity_factor * s["sunFraction"]
    required_initial_w = d["TARGET_POWER_W"] / sunlight_adjusted
    mass_per_sat = (s["satellitePowerKW"] * 1000) / s["specificPowerWPerKg"]
    sat_count = math.ceil(required_initial_w / (s["satellitePowerKW"] * 1000))
    total_mass = sat_count * mass_per_sat
    actual_initial_w = sat_count * s["satellitePowerKW"] * 1000
    hardware = s["satelliteCostPerW"] * actual_initial_w
    launch = s["launchCostPerKg"] * total_mass
    base = hardware + launch
    ops = hardware * CONST["ORBITAL_OPS_FRAC"] * s["years"]
    gpu = hardware * (s["gpuFailureRate"] / 100) * s["years"]
    nre = s["nreCost"] * 1e6
    total = base + ops + gpu + nre
    energy_mwh = d["TARGET_POWER_MW"] * total_hours
    array_per_sat = CONST["STARLINK_ARRAY_M2"] * (s["satellitePowerKW"] / CONST["STARLINK_POWER_KW"])
    array_area_m2 = sat_count * array_per_sat
    return {
        "satelliteCount": sat_count,
        "totalMassKg": total_mass,
        "starshipLaunches": math.ceil(total_mass / CONST["STARSHIP_PAYLOAD_KG"]),
        "totalCost": total,
        "costPerW": total / d["TARGET_POWER_W"],
        "lcoe": total / energy_mwh,
        "energyMWh": energy_mwh,
        "avgCapacityFactor": avg_capacity_factor,
        "arrayAreaKm2": array_area_m2 / 1e6,
        "_arrayAreaM2": array_area_m2,
    }


# --- Thermal model ---

def calculate_thermal(s):
    orbital = calculate_orbital(s)
    area = orbital["_arrayAreaM2"]
    alpha_pv = s["solarAbsorptivity"]
    eps_pv = s["emissivityPV"]
    eps_rad = s["emissivityRad"]
    pv_eff = s["pvEfficiency"]
    beta = s["betaAngle"]
    alt = s["orbitalAltitudeKm"]
    vf = sun_tracking_view_factors(alt, beta)
    vf_a, vf_b = vf["vfSideA"], vf["vfSideB"]
    S = CONST["SOLAR_IRRADIANCE_W_M2"]
    power_generated = S * pv_eff * area
    q_abs_total = S * alpha_pv * area
    q_solar_waste = q_abs_total - power_generated
    q_ir_a = CONST["EARTH_IR_FLUX_W_M2"] * vf_a * eps_pv * area
    q_ir_b = CONST["EARTH_IR_FLUX_W_M2"] * vf_b * eps_rad * area
    q_earth_ir = q_ir_a + q_ir_b
    albedo_scaling = math.cos(math.radians(beta))
    q_albedo = S * CONST["EARTH_ALBEDO_FACTOR"] * vf_a * albedo_scaling * alpha_pv * area
    q_heat_loop = power_generated
    total_heat_in = q_solar_waste + q_earth_ir + q_albedo + q_heat_loop
    total_eps = eps_pv + eps_rad
    eq_tk = (total_heat_in / (SIGMA * area * total_eps) + T_SPACE_K**4) ** 0.25
    eq_tc = eq_tk - 273.15
    dt4_eq = eq_tk**4 - T_SPACE_K**4
    rad_cap = SIGMA * area * eps_pv * dt4_eq + SIGMA * area * eps_rad * dt4_eq
    radiator_tc = s["maxDieTempC"] - s["tempDropC"]
    temp_margin = radiator_tc - eq_tc
    target_tk = radiator_tc + 273.15
    dt4 = target_tk**4 - T_SPACE_K**4
    area_required = total_heat_in / (SIGMA * total_eps * dt4)
    return {
        "eqTempK": eq_tk,
        "eqTempC": eq_tc,
        "totalHeatInW": total_heat_in,
        "qSolarW": q_solar_waste,
        "qEarthIRW": q_earth_ir,
        "qAlbedoW": q_albedo,
        "qHeatLoopW": q_heat_loop,
        "radiativeCapacityW": rad_cap,
        "areaSufficient": eq_tc <= radiator_tc,
        "tempMarginC": temp_margin,
        "areaRequiredM2": area_required,
        "availableAreaM2": area,
        "vfNadirMax": nadir_view_factor(alt),
        "earthAngularRadiusDeg": math.degrees(earth_angular_radius(alt)),
        "vfSideA": vf_a,
        "vfSideB": vf_b,
        "vfTotal": vf["vfTotal"],
    }


def calculate_breakeven(s):
    d = _derived(s)
    total_hours = s["years"] * CONST["HOURS_PER_YEAR"]
    energy_mwh = d["TARGET_POWER_MW"] * total_hours * s["capacityFactor"]
    generation_mwh = energy_mwh * s["pue"]
    power_gen_per_w = s["gasTurbineCapexPerKW"] * s["pue"] / 1000
    infra = (power_gen_per_w + s["electricalCostPerW"] + s["mechanicalCostPerW"]
             + s["civilCostPerW"] + s["networkCostPerW"]) * d["TARGET_POWER_W"]
    fuel_per_mwh = s["heatRateBtuKwh"] * s["gasPricePerMMBtu"] / 1000
    fuel = fuel_per_mwh * generation_mwh
    terrestrial = infra + fuel
    annual_retention = 1 - s["cellDegradation"] / 100
    capacity_sum = sum(annual_retention**y for y in range(s["years"]))
    avg_cf = capacity_sum / s["years"]
    required_initial_w = d["TARGET_POWER_W"] / (avg_cf * s["sunFraction"])
    hardware = s["satelliteCostPerW"] * required_initial_w
    mass = required_initial_w / s["specificPowerWPerKg"]
    return (terrestrial - hardware) / mass


def run_case(overrides=None):
    """Return the same nested structure as one oracle case."""
    s = _state(overrides)
    orbital = calculate_orbital(s)
    thermal = calculate_thermal(s)
    return {
        "geometry": {
            "vfNadirMax": thermal["vfNadirMax"],
            "earthAngularRadiusDeg": thermal["earthAngularRadiusDeg"],
            "vfSideA": thermal["vfSideA"],
            "vfSideB": thermal["vfSideB"],
            "vfTotal": thermal["vfTotal"],
        },
        "thermal": {k: thermal[k] for k in (
            "eqTempK", "eqTempC", "totalHeatInW", "qSolarW", "qEarthIRW",
            "qAlbedoW", "qHeatLoopW", "radiativeCapacityW", "areaSufficient",
            "tempMarginC", "areaRequiredM2", "availableAreaM2")},
        "orbital": {k: orbital[k] for k in (
            "satelliteCount", "totalMassKg", "starshipLaunches", "totalCost",
            "costPerW", "lcoe", "energyMWh", "avgCapacityFactor", "arrayAreaKm2")},
        "breakeven_launch_cost_per_kg": calculate_breakeven(s),
    }
