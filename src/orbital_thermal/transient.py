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


# (the duplicated _sink_series was removed in audit re-review P1-b;
# the one effective-sink equation now lives in sink.sink_temperature_series.)


def simulate(
    altitude_km: float,
    beta_deg: float,
    q_load: float,
    areal_heat_capacity: float,
    tilt_deg: float = 0.0,
    *,
    assume_sun_shielded: bool,
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
    energy_tol_W_m2: float | None = None,
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

    ``assume_sun_shielded`` is REQUIRED (no default) and is forwarded to the one
    effective-sink equation (sink.sink_temperature_series); see that function.

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
    if not (np.isfinite(C) and C > 0.0):
        raise ValueError(f"areal_heat_capacity must be finite and > 0, got {C}")
    if steps_per_orbit < 1:
        raise ValueError(f"steps_per_orbit must be >= 1, got {steps_per_orbit}")
    if n_orbits < 1:
        raise ValueError(f"n_orbits must be >= 1, got {n_orbits}")
    if max_orbits is not None and max_orbits < 1:
        raise ValueError(f"max_orbits must be >= 1, got {max_orbits}")
    if not np.isfinite(q_load):
        raise ValueError(f"q_load must be finite, got {q_load}")
    period = env.orbital_period(altitude_km)
    dt = period / steps_per_orbit
    deg_per_s = 360.0 / period
    cap = n_orbits if max_orbits is None else max_orbits
    # Energy-balance convergence tolerance (W/m^2): relative to the load with an
    # absolute floor. Per-orbit closure alone is insufficient when tau/P >> 1 --
    # the orbit-to-orbit change vanishes while the panel is still far from periodic
    # steady state (audit re-review P1-1). The mean net flux must also be ~0.
    e_tol = energy_tol_W_m2 if energy_tol_W_m2 is not None else max(1e-3 * abs(q_load), 1e-2)
    vf = env.sphere_view_factor(altitude_km, tilt_deg)

    def sink_at(t):
        return sink_mod.sink_temperature_series(
            vf, beta_deg, deg_per_s * t, assume_sun_shielded=assume_sun_shielded,
            emissivity=eps, solar_absorptivity=solar_absorptivity, earth_ir=earth_ir,
            albedo=albedo, solar_constant=solar_constant, t_space=t_space)

    def deriv(t, T):
        Ts = sink_at(t)
        return (q_load - eps * SIGMA_SB * (T**4 - Ts**4)) / C

    if t0_guess is None:
        t0_guess = steady_state_temperature(q_load, 240.0, eps)
    T = float(t0_guess)

    # Explicit fixed-step RK4 is conditionally stable: warn if the step exceeds the
    # radiative time constant tau = C / (4 eps sigma T^3) (audit re-review P3-a).
    tau0 = thermal_time_constant(C, T, eps)
    if dt > tau0:
        warnings.warn(
            f"RK4 timestep dt={dt:.3g} s exceeds the radiative time constant "
            f"tau={tau0:.3g} s; explicit integration may be unstable -- increase "
            f"steps_per_orbit or areal_heat_capacity",
            RuntimeWarning,
        )

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
        if not np.all(np.isfinite(Ts_panel)) or float(np.min(Ts_panel)) <= 0.0:
            raise RuntimeError(
                "RK4 produced a non-finite or non-positive temperature "
                f"(min {float(np.min(Ts_panel)):.1f} K over the orbit); the timestep "
                "is too large for this heat capacity -- increase steps_per_orbit or "
                "areal_heat_capacity (see the stability warning)"
            )
        orbits_used = orbit + 1
        orbit_energy_residual = float(abs(np.mean(
            q_load - eps * SIGMA_SB * (Ts_panel[:-1] ** 4 - Ts_sink[:-1] ** 4))))
        if abs(T - T_start) < convergence_tol_K and orbit_energy_residual < e_tol:
            converged = True
            break

    closure_error_K = float(abs(Ts_panel[-1] - Ts_panel[0]))
    net = q_load - eps * SIGMA_SB * (Ts_panel[:-1] ** 4 - Ts_sink[:-1] ** 4)
    energy_residual_W_m2 = float(abs(np.mean(net)))
    if not converged:
        tau = thermal_time_constant(C, float(Ts_panel.mean()), eps)
        msg = (f"transient did not reach periodic steady state in {orbits_used} "
               f"orbits (closure {closure_error_K:.2e} K vs tol "
               f"{convergence_tol_K:.1e} K; energy residual "
               f"{energy_residual_W_m2:.2e} vs tol {e_tol:.1e} W/m^2; "
               f"tau/period={tau / period:.2f}); raise max_orbits/n_orbits")
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
            "energy_tol_W_m2": float(e_tol),
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

#: Material properties with provenance (audit re-review P2-d). Each entry records
#: density and specific heat at a stated reference state, a source, and a relative
#: uncertainty. Values are representative grades, not a specific lot; the builds
#: below remain illustrative. The liquid-coolant entry is a single documented
#: reference state (ammonia is strongly state-dependent near these temperatures);
#: :func:`coolant_rho_cp` recomputes it from the pinned CoolProp backend.
MATERIALS = {
    "aluminum_6061": {
        "rho_kg_m3": 2700.0, "cp_J_kgK": 896.0,
        "state": "solid, 298 K, 1 atm",
        "source": "ASM aluminum 6061-T6 nominal (rho 2700 kg/m^3; c_p 896 J/kg/K at 25 C)",
        "rel_uncertainty": 0.02,
    },
    "cover_glass": {
        "rho_kg_m3": 2500.0, "cp_J_kgK": 800.0,
        "state": "solid, 298 K",
        "source": "borosilicate solar cover glass, typical (rho ~2500; c_p ~800 J/kg/K)",
        "rel_uncertainty": 0.05,
    },
    "silicon": {
        "rho_kg_m3": 2330.0, "cp_J_kgK": 700.0,
        "state": "crystalline solid, 298 K",
        "source": "CRC Handbook, crystalline Si (rho 2329 kg/m^3; c_p 705 J/kg/K at 298 K)",
        "rel_uncertainty": 0.02,
    },
    "cfrp_substrate": {
        "rho_kg_m3": 1600.0, "cp_J_kgK": 800.0,
        "state": "solid, 298 K",
        "source": "carbon-fiber/epoxy laminate, quasi-isotropic typical (rho ~1550-1600; "
                  "c_p ~800-1000 J/kg/K; strongly layup-dependent)",
        "rel_uncertainty": 0.15,
    },
    "ammonia_liquid": {
        "rho_kg_m3": 600.17, "cp_J_kgK": 4796.38,
        "state": "saturated liquid, 300 K (Q=0)",
        "source": "CoolProp HEOS (Tillner-Roth & Friend EOS) at T=300 K, Q=0; "
                  "strongly state-dependent (280 K: 629/4649; 320 K: 568/5023). "
                  "See coolant_rho_cp().",
        "rel_uncertainty": 0.01,
    },
    "copper": {
        "rho_kg_m3": 8960.0, "cp_J_kgK": 385.0,
        "state": "solid, 298 K",
        "source": "CRC Handbook, Cu (rho 8960 kg/m^3; c_p 385 J/kg/K at 298 K)",
        "rel_uncertainty": 0.01,
    },
    "fr4_pcb": {
        "rho_kg_m3": 1850.0, "cp_J_kgK": 1100.0,
        "state": "solid, 298 K",
        "source": "FR-4 glass-epoxy laminate, typical (rho ~1850; c_p ~1100-1200 J/kg/K)",
        "rel_uncertainty": 0.15,
    },
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
    layers = list(layers)
    if not layers:
        raise ValueError("layers must be a non-empty list of (material, thickness) pairs")
    total = 0.0
    for material, thickness in layers:
        if material not in MATERIALS:
            raise KeyError(f"unknown material {material!r}; see MATERIALS")
        if thickness <= 0.0:
            raise ValueError(f"thickness must be positive, got {thickness}")
        entry = MATERIALS[material]
        total += entry["rho_kg_m3"] * entry["cp_J_kgK"] * thickness
    return total


def build_areal_heat_capacity(build_name: str) -> float:
    """Areal heat capacity, J/m^2/K, of a named build in :data:`REPRESENTATIVE_BUILDS`."""
    if build_name not in REPRESENTATIVE_BUILDS:
        raise KeyError(f"unknown build {build_name!r}; see REPRESENTATIVE_BUILDS")
    return areal_heat_capacity(REPRESENTATIVE_BUILDS[build_name])


def coolant_rho_cp(fluid: str = "Ammonia", T: float = 300.0):
    """(density, specific heat) of the saturated liquid at temperature ``T`` from
    the pinned CoolProp backend, kg/m^3 and J/kg/K (audit re-review P2-d).

    This is the source/validator for the strongly state-dependent liquid-coolant
    entry in :data:`MATERIALS`, which is pinned to one documented reference state
    (300 K saturated liquid). Requires CoolProp (the [fluids] extra)."""
    from CoolProp.CoolProp import PropsSI
    rho = PropsSI("D", "T", T, "Q", 0, fluid)
    cp = PropsSI("C", "T", T, "Q", 0, fluid)
    return float(rho), float(cp)

def averaging_bias(
    altitude_km: float,
    beta_deg: float,
    q_load: float,
    areal_heat_capacity: float,
    tilt_deg: float = 0.0,
    *,
    assume_sun_shielded: bool,
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
                                 tilt_deg=tilt_deg, assume_sun_shielded=assume_sun_shielded,
                                 emissivity=emissivity, return_diagnostics=True, **kwargs)
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
