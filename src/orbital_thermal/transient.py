"""One-node transient radiator model and the averaging-load bias.

The companion paper sizes the radiator at steady state with a constant sink: it
solves eps*sigma*(T^4 - T_s^4) = q_load once and reads off T = 337.1 K. But a
real panel has thermal mass, so as the effective sink swings around the orbit
(:mod:`orbital_thermal.sink`) the temperature cannot follow instantly -- it lags
and ripples. Because heat rejection goes as T^4, energy balance at periodic steady state
forces the fourth-power mean to equal the steady value exactly:
<T^4> = T_steady^4, with T_steady evaluated at the T^4-weighted average sink.
Since x^(1/4) is concave, the *arithmetic* mean then sits slightly BELOW
T_steady (a small, signed <= 0 effect) while the peak sits ABOVE it. The
engineering penalty of the steady, averaged-load assumption is therefore peak
UNDER-prediction, not a mean offset. This module integrates the transient and
quantifies both: the peak excess (the operationally important number) and the
small signed mean bias.

Model (per unit radiator area)
------------------------------
    C dT/dt = q_load - eps*sigma*(T^4 - T_s_eff(t)^4)

- ``C``        areal heat capacity, J/m^2/K (rho * c_p * thickness)
- ``q_load``   internal compute waste-heat flux, W/m^2 (constant)
- ``T_s_eff``  time-varying effective sink (orbit position u(t) = 360*t/period)

Integration is fixed-step RK4 (numpy only). The panel is marched for several
orbits until it reaches a periodic steady state; the final orbit is returned.
"""

import warnings

import numpy as np

from .constants import SIGMA_SB
from . import environment as env
from . import sink as sink_mod


def steady_state_temperature(q_load: float, t_sink: float, emissivity: float = 0.91) -> float:
    """Closed-form steady radiator temperature, K, for a constant sink.

    Solves eps*sigma*(T^4 - t_sink^4) = q_load:  T = (q_load/(eps*sigma) + t_sink^4)^(1/4).
    """
    return float((q_load / (emissivity * SIGMA_SB) + t_sink**4) ** 0.25)


def thermal_time_constant(
    areal_heat_capacity: float, temperature: float, emissivity: float = 0.91
) -> float:
    """Linearized radiative time constant, s:  C / (4*eps*sigma*T^3)."""
    return float(areal_heat_capacity / (4.0 * emissivity * SIGMA_SB * temperature**3))


def _sink_series(altitude_km, beta_deg, tilt_deg, u_deg, emissivity,
                 solar_absorptivity, earth_ir, albedo, solar_constant, t_space):
    """Vectorized T_s_eff at orbit angles ``u_deg``; VF computed once (constant
    for fixed tilt), only the cheap albedo term varies with u."""
    vf = env.sphere_view_factor(altitude_km, tilt_deg)
    cos_zeta = np.cos(np.radians(beta_deg)) * np.cos(np.radians(u_deg))
    q_ir = earth_ir * vf
    q_alb = albedo * solar_constant * vf * np.clip(cos_zeta, 0.0, None)
    t4 = (q_ir + (solar_absorptivity / emissivity) * q_alb) / SIGMA_SB + t_space**4
    return t4 ** 0.25


def simulate(
    altitude_km: float,
    beta_deg: float,
    q_load: float,
    areal_heat_capacity: float,
    tilt_deg: float = 0.0,
    emissivity: float = 0.91,
    solar_absorptivity: float = 0.20,
    earth_ir: float = sink_mod.EARTH_IR_FLUX,
    albedo: float = sink_mod.EARTH_ALBEDO,
    solar_constant: float = sink_mod.SOLAR_CONSTANT,
    t_space: float = sink_mod.T_SPACE_K,
    n_orbits: int = 30,
    steps_per_orbit: int = 2000,
    t0_guess: float | None = None,
    convergence_tol_K: float = 1e-3,
    max_orbits: int | None = None,
    return_diagnostics: bool = False,
    raise_on_nonconvergence: bool = False,
):
    """Integrate to a periodic steady state; return (t, T, T_sink) for the final orbit.

    The panel is marched orbit by orbit until the start-to-end temperature change
    over an orbit falls below ``convergence_tol_K`` (periodic closure), capped at
    ``max_orbits`` (default ``n_orbits``). High-thermal-mass panels (tau/period
    >> 1) can need many more orbits than a fixed count would allow, so a fixed
    march can silently return a not-yet-periodic profile; this loop detects that.

    ``t`` is seconds from the start of the final orbit; ``T`` and ``T_sink`` are
    the panel and effective-sink temperatures, K.

    If ``return_diagnostics`` is True, returns ``(t, T, T_sink, diagnostics)``
    where diagnostics is a dict: ``converged`` (bool), ``orbits_used`` (int),
    ``closure_error_K`` (|T_end - T_start| of the final orbit), ``tol_K``, and
    ``energy_residual_W_m2`` (orbit-mean net flux, ~0 at periodic steady state).
    On non-convergence it warns (or raises if ``raise_on_nonconvergence``).
    """
    C = areal_heat_capacity
    eps = emissivity
    period = env.orbital_period(altitude_km)
    dt = period / steps_per_orbit
    deg_per_s = 360.0 / period
    cap = n_orbits if max_orbits is None else max_orbits

    def sink_at(t):
        return _sink_series(altitude_km, beta_deg, tilt_deg, deg_per_s * t, eps,
                            solar_absorptivity, earth_ir, albedo, solar_constant, t_space)

    def deriv(t, T):
        Ts = sink_at(t)
        return (q_load - eps * SIGMA_SB * (T**4 - Ts**4)) / C

    if t0_guess is None:
        t0_guess = steady_state_temperature(q_load, 240.0, eps)
    T = float(t0_guess)

    ts = np.zeros(steps_per_orbit + 1)
    Ts_panel = np.zeros(steps_per_orbit + 1)
    Ts_sink = np.zeros(steps_per_orbit + 1)
    t = 0.0
    converged = False
    orbits_used = 0
    for orbit in range(cap):
        t_orbit0 = t
        T_start = T
        ts[0] = 0.0
        Ts_panel[0] = T
        Ts_sink[0] = sink_at(t)
        for i in range(1, steps_per_orbit + 1):
            k1 = deriv(t, T)
            k2 = deriv(t + dt / 2, T + dt / 2 * k1)
            k3 = deriv(t + dt / 2, T + dt / 2 * k2)
            k4 = deriv(t + dt, T + dt * k3)
            T += dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
            t += dt
            ts[i] = t - t_orbit0
            Ts_panel[i] = T
            Ts_sink[i] = sink_at(t)
        orbits_used = orbit + 1
        if abs(T - T_start) < convergence_tol_K:
            converged = True
            break

    closure_error_K = float(abs(Ts_panel[-1] - Ts_panel[0]))
    net = q_load - eps * SIGMA_SB * (Ts_panel[:-1] ** 4 - Ts_sink[:-1] ** 4)
    energy_residual_W_m2 = float(abs(np.mean(net)))
    if not converged:
        tau = thermal_time_constant(C, float(Ts_panel.mean()), eps)
        msg = (f"transient did not reach periodic steady state in {orbits_used} "
               f"orbits (closure {closure_error_K:.2e} K > tol "
               f"{convergence_tol_K:.1e} K; tau/period={tau / period:.2f}); "
               f"raise max_orbits/n_orbits")
        if raise_on_nonconvergence:
            raise RuntimeError(msg)
        warnings.warn(msg, RuntimeWarning)

    if return_diagnostics:
        diagnostics = {
            "converged": converged,
            "orbits_used": orbits_used,
            "closure_error_K": closure_error_K,
            "tol_K": float(convergence_tol_K),
            "energy_residual_W_m2": energy_residual_W_m2,
        }
        return ts, Ts_panel, Ts_sink, diagnostics
    return ts, Ts_panel, Ts_sink


# ---------------------------------------------------------------------------
# Areal heat-capacity provenance (audit item 10)
# ---------------------------------------------------------------------------
# The example thermal masses C used elsewhere (e.g. 2000 / 8000 / 40000 J/m^2/K)
# are ILLUSTRATIVE. Real areal heat capacity is C_A = sum_i rho_i c_p,i t_i over
# the panel's material layers. The builds below derive representative values from
# handbook room-temperature properties so transient swings can be tied to a
# concrete stack rather than a bare number.

#: Handbook material properties: name -> (density kg/m^3, specific heat J/kg/K).
MATERIALS = {
    "aluminum_6061": (2700.0, 896.0),
    "cover_glass": (2500.0, 800.0),
    "silicon": (2330.0, 700.0),
    "cfrp_substrate": (1600.0, 800.0),
    "ammonia_liquid": (600.0, 4700.0),
    "copper": (8960.0, 385.0),
    "fr4_pcb": (1850.0, 1100.0),
}

#: Representative panel builds: name -> list of (material, thickness_m) layers.
#: Thicknesses are illustrative but physically plausible.
REPRESENTATIVE_BUILDS = {
    "bare_aluminum_sheet_2mm": [("aluminum_6061", 0.002)],
    "pv_on_substrate": [
        ("cover_glass", 0.0005), ("silicon", 0.0002),
        ("cfrp_substrate", 0.001), ("aluminum_6061", 0.0005),
    ],
    "radiator_with_coolant": [("aluminum_6061", 0.002), ("ammonia_liquid", 0.005)],
    "integrated_compute_radiator": [
        ("aluminum_6061", 0.003), ("copper", 0.002), ("fr4_pcb", 0.0016),
        ("silicon", 0.0008), ("ammonia_liquid", 0.006),
    ],
}


def areal_heat_capacity(layers) -> float:
    """Areal heat capacity C_A = sum_i rho_i c_p,i t_i, J/m^2/K.

    ``layers`` is an iterable of ``(material_name, thickness_m)`` pairs; material
    names key into :data:`MATERIALS`. This is the quantity ``C`` in the one-node
    model, derived from a physical stack rather than assumed.
    """
    total = 0.0
    for material, thickness in layers:
        if material not in MATERIALS:
            raise KeyError(f"unknown material {material!r}; see MATERIALS")
        if thickness <= 0.0:
            raise ValueError(f"thickness must be positive, got {thickness}")
        rho, cp = MATERIALS[material]
        total += rho * cp * thickness
    return total


def build_areal_heat_capacity(build_name: str) -> float:
    """Areal heat capacity, J/m^2/K, of a named build in :data:`REPRESENTATIVE_BUILDS`."""
    if build_name not in REPRESENTATIVE_BUILDS:
        raise KeyError(f"unknown build {build_name!r}; see REPRESENTATIVE_BUILDS")
    return areal_heat_capacity(REPRESENTATIVE_BUILDS[build_name])

def averaging_bias(
    altitude_km: float,
    beta_deg: float,
    q_load: float,
    areal_heat_capacity: float,
    tilt_deg: float = 0.0,
    emissivity: float = 0.91,
    require_convergence: bool = True,
    **kwargs,
) -> dict:
    """Compare the transient time-mean temperature to the steady, averaged-sink
    solution. Returns a dict of temperatures (K), the bias, and timescales.

    ``bias_K`` = transient mean - steady(averaged sink). At periodic steady state
    <T^4> = T_steady^4, so by concavity of x^(1/4) the arithmetic mean is
    <= T_steady and ``bias_K`` is <= 0 up to numerical slack: the averaged-sink
    steady solution does NOT under-predict the mean. The operationally important
    quantity is ``peak_excess_over_steady_K`` (> 0), the peak the steady,
    averaged-load assumption misses.

    The Jensen/peak metrics are only meaningful at periodic steady state, so this
    helper requests convergence diagnostics from :func:`simulate`. By default
    (``require_convergence=True``) it RAISES ``RuntimeError`` if the transient did
    not converge -- a non-converged final orbit can flip the sign of the reported
    bias and peak excess (an initialization artifact, not physics). Set
    ``require_convergence=False`` to inspect the unconverged result instead; the
    returned dict always carries ``converged``, ``orbits_used``,
    ``closure_error_K``, and ``energy_residual_W_m2``.
    """
    kwargs.pop("return_diagnostics", None)
    t, T, Tsink, diag = simulate(altitude_km, beta_deg, q_load, areal_heat_capacity,
                                 tilt_deg=tilt_deg, emissivity=emissivity,
                                 return_diagnostics=True, **kwargs)
    if require_convergence and not diag["converged"]:
        raise RuntimeError(
            "averaging_bias: transient did not reach periodic steady state "
            f"({diag['orbits_used']} orbits, closure {diag['closure_error_K']:.2e} K "
            f"> tol {diag['tol_K']:.1e} K). The Jensen/peak metrics would be an "
            "initialization artifact (the bias/peak-excess sign can flip). Increase "
            "n_orbits/max_orbits, or pass require_convergence=False to inspect the "
            "unconverged diagnostics."
        )
    transient_mean = float(np.mean(T[:-1]))
    sink_avg = float(np.mean(Tsink[:-1] ** 4) ** 0.25)
    steady = steady_state_temperature(q_load, sink_avg, emissivity)
    period = env.orbital_period(altitude_km)
    tau = thermal_time_constant(areal_heat_capacity, transient_mean, emissivity)
    peak = float(T.max())
    return {
        "transient_mean_K": transient_mean,
        "steady_avg_sink_K": steady,
        "bias_K": transient_mean - steady,
        "transient_peak_K": peak,
        "peak_excess_over_steady_K": peak - steady,
        "swing_K": float(T.max() - T.min()),
        "sink_avg_K": sink_avg,
        "tau_s": tau,
        "period_s": period,
        "tau_over_period": tau / period,
        "converged": diag["converged"],
        "orbits_used": diag["orbits_used"],
        "closure_error_K": diag["closure_error_K"],
        "energy_residual_W_m2": diag["energy_residual_W_m2"],
    }
