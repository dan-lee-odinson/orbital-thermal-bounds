"""One-node transient radiator model and the averaging-load bias.

The companion paper sizes the radiator at steady state with a constant sink: it
solves eps*sigma*(T^4 - T_s^4) = q_load once and reads off T = 337.1 K. But a
real panel has thermal mass, so as the effective sink swings around the orbit
(:mod:`orbital_thermal.sink`) the temperature cannot follow instantly -- it lags
and ripples. Because heat rejection goes as T^4, the time-average of that ripple
is NOT the steady solution evaluated at the average sink (Jensen's inequality).
This module integrates the transient and quantifies that gap -- the bias incurred
by the steady, averaged-load assumption.

Model (per unit radiator area)
------------------------------
    C dT/dt = q_load - eps*sigma*(T^4 - T_s_eff(t)^4)

- ``C``        areal heat capacity, J/m^2/K (rho * c_p * thickness)
- ``q_load``   internal compute waste-heat flux, W/m^2 (constant)
- ``T_s_eff``  time-varying effective sink (orbit position u(t) = 360*t/period)

Integration is fixed-step RK4 (numpy only). The panel is marched for several
orbits until it reaches a periodic steady state; the final orbit is returned.
"""

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
):
    """Integrate to a periodic steady state; return (t, T, T_sink) for the LAST orbit.

    ``t`` is seconds from the start of the final orbit; ``T`` and ``T_sink`` are
    the panel and effective-sink temperatures, K.
    """
    C = areal_heat_capacity
    eps = emissivity
    period = env.orbital_period(altitude_km)
    dt = period / steps_per_orbit
    deg_per_s = 360.0 / period

    def sink_at(t):
        return _sink_series(altitude_km, beta_deg, tilt_deg, deg_per_s * t, eps,
                            solar_absorptivity, earth_ir, albedo, solar_constant, t_space)

    def deriv(t, T):
        Ts = sink_at(t)
        return (q_load - eps * SIGMA_SB * (T**4 - Ts**4)) / C

    if t0_guess is None:
        t0_guess = steady_state_temperature(q_load, 240.0, eps)
    T = float(t0_guess)

    settle_steps = (n_orbits - 1) * steps_per_orbit
    t = 0.0
    for _ in range(settle_steps):
        k1 = deriv(t, T)
        k2 = deriv(t + dt / 2, T + dt / 2 * k1)
        k3 = deriv(t + dt / 2, T + dt / 2 * k2)
        k4 = deriv(t + dt, T + dt * k3)
        T += dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        t += dt

    ts = np.zeros(steps_per_orbit + 1)
    Ts_panel = np.zeros(steps_per_orbit + 1)
    Ts_sink = np.zeros(steps_per_orbit + 1)
    t_orbit0 = t
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
    return ts, Ts_panel, Ts_sink


def averaging_bias(
    altitude_km: float,
    beta_deg: float,
    q_load: float,
    areal_heat_capacity: float,
    tilt_deg: float = 0.0,
    emissivity: float = 0.91,
    **kwargs,
) -> dict:
    """Compare the transient time-mean temperature to the steady, averaged-sink
    solution. Returns a dict of temperatures (K), the bias, and timescales.

    ``bias_K`` = transient mean - steady(averaged sink). A positive value means
    the steady/averaged assumption UNDER-predicts the true mean temperature.
    """
    t, T, Tsink = simulate(altitude_km, beta_deg, q_load, areal_heat_capacity,
                           tilt_deg=tilt_deg, emissivity=emissivity, **kwargs)
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
    }
