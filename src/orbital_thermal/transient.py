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
    energy_tol_K: float = 1e-2,
    check_time_resolution: bool = False,
    time_tol_K: float = 1e-2,
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
    for _name, _val in (("steps_per_orbit", steps_per_orbit), ("n_orbits", n_orbits)):
        if isinstance(_val, bool) or not isinstance(_val, int):
            raise TypeError(f"{_name} must be an int, got {type(_val).__name__}")
        if _val < 1:
            raise ValueError(f"{_name} must be >= 1, got {_val}")
    if max_orbits is not None:
        if isinstance(max_orbits, bool) or not isinstance(max_orbits, int):
            raise TypeError(f"max_orbits must be an int, got {type(max_orbits).__name__}")
        if max_orbits < 1:
            raise ValueError(f"max_orbits must be >= 1, got {max_orbits}")
    if not (np.isfinite(q_load) and q_load > 0.0):
        raise ValueError(f"q_load must be finite and > 0, got {q_load}")
    if not 0.0 < emissivity <= 1.0:
        raise ValueError(f"emissivity must be in (0, 1], got {emissivity}")
    if not (np.isfinite(convergence_tol_K) and convergence_tol_K > 0.0):
        raise ValueError(f"convergence_tol_K must be finite and > 0, got {convergence_tol_K}")
    if not (np.isfinite(energy_tol_K) and energy_tol_K > 0.0):
        raise ValueError(f"energy_tol_K must be finite and > 0, got {energy_tol_K}")
    if not (np.isfinite(time_tol_K) and time_tol_K > 0.0):
        raise ValueError(f"time_tol_K must be finite and > 0, got {time_tol_K}")
    if t0_guess is not None and not (np.isfinite(t0_guess) and t0_guess > 0.0):
        raise ValueError(f"t0_guess must be finite and > 0 K, got {t0_guess}")
    period = env.orbital_period(altitude_km)
    dt = period / steps_per_orbit
    deg_per_s = 360.0 / period
    cap = n_orbits if max_orbits is None else max_orbits
    # Energy-balance convergence tolerance (W/m^2): relative to the load with an
    # absolute floor. Per-orbit closure alone is insufficient when tau/P >> 1 --
    # the orbit-to-orbit change vanishes while the panel is still far from periodic
    # steady state (audit re-review P1-1). The mean net flux must also be ~0.
    vf = env.sphere_view_factor(altitude_km, tilt_deg)

    def sink_at(t):
        return sink_mod.sink_temperature_series(
            vf, beta_deg, deg_per_s * t, assume_sun_shielded=assume_sun_shielded,
            emissivity=eps, solar_absorptivity=solar_absorptivity, earth_ir=earth_ir,
            albedo=albedo, solar_constant=solar_constant, t_space=t_space)

    def deriv(t, T):
        Ts = sink_at(t)
        return (q_load - eps * SIGMA_SB * (T**4 - Ts**4)) / C

    def _converge(nsteps):
        """March orbit-by-orbit at ``nsteps`` steps/orbit from the shared initial
        guess ``t0_guess`` until periodic closure AND energy balance, capped at
        ``cap`` orbits. Returns the final-orbit arrays plus convergence
        diagnostics.

        Used for both the primary result and the 2x-resolution temporal-accuracy
        comparison. Each grid is converged to its OWN periodic fixed point, so the
        step-doubling gate compares periodic solutions -- not one-orbit transients
        from a shared coarse state, which collapse to a false pass at high thermal
        inertia because both barely move over a single orbit (audit r5 P1)."""
        dtl = period / nsteps
        Tloc = float(t0_guess)
        ts_l = np.zeros(nsteps + 1)
        Tp = np.zeros(nsteps + 1)
        Tsk = np.zeros(nsteps + 1)
        t_l = 0.0
        conv = False
        used = 0
        for orbit in range(cap):
            t_orbit0 = t_l
            T_start = Tloc
            ts_l[0] = 0.0
            Tp[0] = Tloc
            Tsk[0] = sink_at(t_l)
            for i in range(1, nsteps + 1):
                k1 = deriv(t_l, Tloc)
                k2 = deriv(t_l + dtl / 2, Tloc + dtl / 2 * k1)
                k3 = deriv(t_l + dtl / 2, Tloc + dtl / 2 * k2)
                k4 = deriv(t_l + dtl, Tloc + dtl * k3)
                Tloc += dtl / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
                t_l += dtl
                ts_l[i] = t_l - t_orbit0
                Tp[i] = Tloc
                Tsk[i] = sink_at(t_l)
            if not np.all(np.isfinite(Tp)) or float(np.min(Tp)) <= 0.0:
                raise RuntimeError(
                    "RK4 produced a non-finite or non-positive temperature "
                    f"(min {float(np.min(Tp)):.1f} K over the orbit); the timestep "
                    "is too large for this heat capacity -- increase steps_per_orbit "
                    "or areal_heat_capacity (see the stability warning)"
                )
            used = orbit + 1
            resid = float(abs(np.mean(
                q_load - eps * SIGMA_SB * (Tp[:-1] ** 4 - Tsk[:-1] ** 4))))
            T_ref = float(np.mean(Tp[:-1]))
            dT_eq = resid / (4.0 * eps * SIGMA_SB * T_ref ** 3)
            if abs(Tloc - T_start) < convergence_tol_K and dT_eq < energy_tol_K:
                conv = True
                break
        closure = float(abs(Tp[-1] - Tp[0]))
        e_w = float(abs(np.mean(
            q_load - eps * SIGMA_SB * (Tp[:-1] ** 4 - Tsk[:-1] ** 4))))
        e_K = e_w / (4.0 * eps * SIGMA_SB * float(np.mean(Tp[:-1])) ** 3)
        return {"ts": ts_l, "Tp": Tp, "Tsk": Tsk, "converged": conv,
                "orbits_used": used, "closure_K": closure,
                "energy_W": e_w, "energy_K": e_K}

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

    main = _converge(steps_per_orbit)
    ts, Ts_panel, Ts_sink = main["ts"], main["Tp"], main["Tsk"]
    periodic_converged = main["converged"]
    orbits_used = main["orbits_used"]
    closure_error_K = main["closure_K"]
    energy_residual_W_m2 = main["energy_W"]
    energy_residual_K = main["energy_K"]
    if not periodic_converged:
        tau = thermal_time_constant(C, float(Ts_panel.mean()), eps)
        msg = (f"transient did not reach periodic steady state in {orbits_used} "
               f"orbits (closure {closure_error_K:.2e} K vs tol "
               f"{convergence_tol_K:.1e} K; energy dT_eq {energy_residual_K:.2e} K vs "
               f"tol {energy_tol_K:.1e} K; tau/period={tau / period:.2f}); "
               f"raise max_orbits/n_orbits")
        if raise_on_nonconvergence:
            raise RuntimeError(msg)
        warnings.warn(msg, RuntimeWarning)

    # Temporal-accuracy gate (audit r5 P1): periodic closure + energy balance do
    # not certify that the timestep resolves the intra-orbit forcing. Converge a
    # SECOND solution at 2x resolution to ITS OWN periodic fixed point and require
    # the two periodic orbits' peak/mean/swing to agree. Comparing converged N- vs
    # 2N-step fixed points (rather than one refined orbit launched from the coarse
    # state) is what detects coarse-quadrature bias: in the high-thermal-inertia
    # limit both one-orbit transients barely move and falsely agree, but the two
    # grids' periodic equilibria still differ. The refined grid must itself reach
    # periodic steady state, else temporal accuracy is uncertified.
    if check_time_resolution:
        refined = _converge(2 * steps_per_orbit)
        if not refined["converged"]:
            time_residual_K = float("inf")
            time_discretization_converged = False
        else:
            peak_n = float(Ts_panel.max())
            mean_n = float(np.mean(Ts_panel[:-1]))
            swing_n = float(Ts_panel.max() - Ts_panel.min())
            Rp = refined["Tp"]
            time_residual_K = max(
                abs(peak_n - float(Rp.max())),
                abs(mean_n - float(np.mean(Rp[:-1]))),
                abs(swing_n - float(Rp.max() - Rp.min())),
            )
            time_discretization_converged = bool(
                periodic_converged and time_residual_K < time_tol_K)
    else:
        time_residual_K = None
        time_discretization_converged = None

    # The combined convergence flag IS gated by temporal accuracy when the caller
    # asks for it (audit r5 P2): a result that passes periodic closure + energy
    # balance but fails the step-doubling check is NOT certified. Without this the
    # bare three-tuple path could silently return a time-under-resolved profile.
    converged = periodic_converged and (
        not check_time_resolution or bool(time_discretization_converged))
    if check_time_resolution and periodic_converged and not time_discretization_converged:
        msg = (f"transient did not resolve the intra-orbit forcing: step-doubling "
               f"residual {time_residual_K} K vs tol {time_tol_K:.1e} K at "
               f"{steps_per_orbit} steps/orbit; increase steps_per_orbit (and "
               f"n_orbits/max_orbits so the 2x grid also reaches periodic steady "
               f"state)")
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
            "energy_residual_K": energy_residual_K,
            "energy_tol_K": float(energy_tol_K),
            "periodic_converged": periodic_converged,
            "time_discretization_converged": time_discretization_converged,
            "time_residual_K": time_residual_K,
            "time_tol_K": float(time_tol_K),
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
        "source": "CRC Handbook of Chemistry and Physics, 97th ed.; crystalline Si (rho 2329 kg/m^3; c_p 705 J/kg/K at 298 K)",
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
        "source": "CoolProp HEOS at T=300 K, Q=0; strongly state-dependent "
                  "(280 K: 629/4649; 320 K: 568/5023). See coolant_rho_cp().",
        "coolprop_version": "7.2.0",            # pinned in the [fluids] extra
        "eos_bibtex_key": "Gao-JPCRD-2020",     # from get_BibTeXKey at that version
        "rel_uncertainty": 0.01,                # PHYSICAL property uncertainty (cross-check)
        "stored_decimals": 2,                   # values rounded to 2 decimals
        "regression_rtol": 1e-4,                # CODE-regression tol vs the pinned backend
    },
    "copper": {
        "rho_kg_m3": 8960.0, "cp_J_kgK": 385.0,
        "state": "solid, 298 K",
        "source": "CRC Handbook of Chemistry and Physics, 97th ed.; Cu (rho 8960 kg/m^3; c_p 385 J/kg/K at 298 K)",
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
        if not (np.isfinite(thickness) and thickness > 0.0):
            raise ValueError(f"thickness must be finite and > 0, got {thickness}")
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
    kwargs.pop("check_time_resolution", None)
    t, T, Tsink, diag = simulate(altitude_km, beta_deg, q_load, areal_heat_capacity,
                                 tilt_deg=tilt_deg, assume_sun_shielded=assume_sun_shielded,
                                 emissivity=emissivity, return_diagnostics=True,
                                 check_time_resolution=True, **kwargs)
    if require_convergence and not (diag["periodic_converged"]
                                    and diag["time_discretization_converged"]):
        raise RuntimeError(
            "averaging_bias: result not certified -- "
            f"periodic_converged={diag['periodic_converged']} "
            f"(closure {diag['closure_error_K']:.2e} K vs tol {diag['tol_K']:.1e} K; "
            f"energy dT_eq {diag['energy_residual_K']:.2e} K vs tol "
            f"{diag['energy_tol_K']:.1e} K), time_discretization_converged="
            f"{diag['time_discretization_converged']} (step-doubling residual "
            f"{diag['time_residual_K']} K vs tol {diag['time_tol_K']:.1e} K). The "
            "Jensen/peak metrics would be invalid. Increase n_orbits/max_orbits and/or "
            "steps_per_orbit, or pass require_convergence=False to inspect diagnostics."
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
        "energy_residual_K": diag["energy_residual_K"],
        "energy_tol_K": diag["energy_tol_K"],
        "periodic_converged": diag["periodic_converged"],
        "time_discretization_converged": diag["time_discretization_converged"],
        "time_residual_K": diag["time_residual_K"],
        "time_tol_K": diag["time_tol_K"],
    }
