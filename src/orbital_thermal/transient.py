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

    ``bias_K`` = transient mean - steady(averaged sink). At periodic steady state
    <T^4> = T_steady^4, so by concavity of x^(1/4) the arithmetic mean is
    <= T_steady and ``bias_K`` is <= 0 up to numerical slack: the averaged-sink
    steady solution does NOT under-predict the mean. The operationally important
    quantity is ``peak_excess_over_steady_K`` (> 0), the peak the steady,
    averaged-load assumption misses.
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
