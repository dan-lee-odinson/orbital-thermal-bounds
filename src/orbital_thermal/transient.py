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
from . import _validate as _v


def steady_state_temperature(q_load: float, t_sink: float, emissivity: float = 0.91) -> float:
    """Closed-form steady radiator temperature, K, for a constant sink.

    Solves eps*sigma*(T^4 - t_sink^4) = q_load:  T = (q_load/(eps*sigma) + t_sink^4)^(1/4).
    """
    _v.nonneg("q_load", q_load)
    _v.nonneg("t_sink", t_sink)
    if not 0.0 < emissivity <= 1.0:
        raise ValueError(f"emissivity must be in (0, 1], got {emissivity}")
    return float((q_load / (emissivity * SIGMA_SB) + t_sink**4) ** 0.25)


def thermal_time_constant(
    areal_heat_capacity: float, temperature: float, emissivity: float = 0.91
) -> float:
    """Linearized radiative time constant, s:  C / (4*eps*sigma*T^3)."""
    _v.positive("areal_heat_capacity", areal_heat_capacity)
    _v.positive("temperature", temperature)
    if not 0.0 < emissivity <= 1.0:
        raise ValueError(f"emissivity must be in (0, 1], got {emissivity}")
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
    time_safety_factor: float = 2.0,
    max_orbits: int | None = None,
    return_diagnostics: bool = False,
    raise_on_nonconvergence: bool = False,
):
    """Integrate to a periodic steady state; return (t, T, T_sink) for the final orbit.

    The panel is marched orbit by orbit (capped at ``max_orbits``, default
    ``n_orbits``) until it reaches periodic steady state under TWO criteria, both
    of which must hold (audit r4 P1):

    * periodic closure: the start-to-end temperature change over an orbit is below
      ``convergence_tol_K``; and
    * energy balance: the orbit-mean net flux, expressed as an equivalent
      temperature error ``dT_eq = |<q_net>| / (4 eps sigma T_ref^3)``, is below
      ``energy_tol_K``.

    Closure alone is insufficient when tau/period >> 1: the orbit-to-orbit change
    vanishes while the panel is still far from steady state, so the scale-aware
    energy residual is required as well.

    Temporal resolution (``check_time_resolution``, default False): periodic
    closure + energy balance do not certify that ``steps_per_orbit`` resolves the
    intra-orbit forcing. When enabled, the N-, 2N-, and 4N-step solutions are each
    converged to their OWN periodic fixed points and ``time_residual_K`` is formed
    from (all in K):

    * a grid-free forcing-quadrature certificate (the subpoint albedo has the exact
      orbit mean cos(beta)/pi, giving a closed form for <T_sink^4>);
    * POINTWISE errors of the returned N orbit and of 2N, each interpolated onto
      the 4N phase grid (this bounds the temperature WAVEFORM in L-infinity; it does
      NOT bound the time/phase of the peak -- see ``peak_phase_residual_deg``); and
    * the direct N->4N (and 2N->4N, N->2N) peak/mean/swing summaries.

    ``time_residual_K`` is a refinement-based error ESTIMATE of the returned N-grid
    profile, not a guaranteed upper bound on the continuum error: the 4N reference
    is itself approximate, and the terminator kinks in the forcing break a clean
    fourth-order Richardson assumption. The gate is therefore made CONSERVATIVE by
    requiring ``time_safety_factor * time_residual_K < time_tol_K`` (default factor
    2.0; audit r8 P2-a). One N->2N doubling alone is insufficient -- it can be
    exactly aliased by the orbital forcing, and adjacent summaries are not even an
    estimate of the returned profile's error.

    ``assume_sun_shielded`` is REQUIRED (no default) and is forwarded to the one
    effective-sink equation (sink.sink_temperature_series); see that function.

    ``t`` is seconds from the start of the final orbit; ``T`` and ``T_sink`` are
    the panel and effective-sink temperatures, K.

    If ``return_diagnostics`` is True, returns ``(t, T, T_sink, diagnostics)``.
    The diagnostics dict distinguishes three convergence notions:

    * ``periodic_converged`` -- periodic closure AND energy balance both met;
    * ``time_discretization_converged`` -- the temporal-resolution certificate
      passed (None when ``check_time_resolution`` is False); its components are
      exposed as ``forcing_residual_K``, ``n_to_2n_residual_K``,
      ``two_n_to_4n_residual_K``, ``n_to_4n_residual_K``, ``pointwise_n_to_4n_K``,
      ``pointwise_2n_to_4n_K``, and ``refined_orbits_used``;
    * ``converged`` -- the COMBINED flag: ``periodic_converged`` AND, when
      ``check_time_resolution`` is True, ``time_discretization_converged``.

    It also carries ``orbits_used``, ``closure_error_K`` and ``tol_K`` (periodic
    closure), ``energy_residual_W_m2`` / ``energy_residual_K`` and ``energy_tol_K``
    (energy balance), and ``time_residual_K`` / ``time_tol_K`` (temporal gate).
    On periodic non-convergence -- and, when ``check_time_resolution`` is on, on
    temporal under-resolution -- it warns (or raises if ``raise_on_nonconvergence``),
    so the bare three-tuple caller is signalled too.
    """
    C = areal_heat_capacity
    eps = emissivity
    _v.positive("areal_heat_capacity", C)
    _v.positive_int("steps_per_orbit", steps_per_orbit)
    _v.positive_int("n_orbits", n_orbits)
    if max_orbits is not None:
        _v.positive_int("max_orbits", max_orbits)
    _v.boolean("assume_sun_shielded", assume_sun_shielded)
    _v.boolean("check_time_resolution", check_time_resolution)
    _v.boolean("return_diagnostics", return_diagnostics)
    _v.boolean("raise_on_nonconvergence", raise_on_nonconvergence)
    _v.positive("q_load", q_load)
    if not 0.0 < emissivity <= 1.0:
        raise ValueError(f"emissivity must be in (0, 1], got {emissivity}")
    _v.positive("convergence_tol_K", convergence_tol_K)
    _v.positive("energy_tol_K", energy_tol_K)
    _v.positive("time_tol_K", time_tol_K)
    _v.positive("time_safety_factor", time_safety_factor)
    if t0_guess is not None:
        _v.positive("t0_guess", t0_guess)
    period = env.orbital_period(altitude_km)
    dt = period / steps_per_orbit
    deg_per_s = 360.0 / period
    cap = n_orbits if max_orbits is None else max_orbits
    # Per-orbit closure alone is insufficient when tau/P >> 1: the orbit-to-orbit
    # change vanishes while the panel is still far from periodic steady state
    # (audit re-review P1-1). _converge() therefore ALSO requires the orbit-mean
    # net flux -- as a scale-aware equivalent temperature error dT_eq, not a fixed
    # W/m^2 floor (4 eps sigma T^3 -> 0 at low T) -- to fall below energy_tol_K.
    vf = env.sphere_view_factor(altitude_km, tilt_deg)

    # Validate the sink parameters ONCE at the public boundary (full checks +
    # shielding assert), then evaluate the prevalidated inner expression in the RK4
    # inner loop -- which runs at every stage across the N/2N/4N grids -- to avoid
    # re-validating every call (audit r8 P3).
    sink_mod.sink_temperature_series(
        vf, beta_deg, 0.0, assume_sun_shielded=assume_sun_shielded, emissivity=eps,
        solar_absorptivity=solar_absorptivity, earth_ir=earth_ir, albedo=albedo,
        solar_constant=solar_constant, t_space=t_space)

    def sink_at(t):
        return sink_mod._sink_series_compute(
            vf, beta_deg, deg_per_s * t, emissivity=eps,
            solar_absorptivity=solar_absorptivity, earth_ir=earth_ir,
            albedo=albedo, solar_constant=solar_constant, t_space=t_space)

    def deriv(t, T):
        # RK4-stage positivity guard (audit r8 P2-c): every RK stage state -- not
        # just the accepted step -- is evaluated through T**4, so an intermediate
        # stage that crosses below absolute zero would silently corrupt the step
        # yet can still yield a positive endpoint. Reject any non-finite or
        # non-positive stage here so the raw simulate() API cannot return a
        # numerically corrupted trajectory.
        if not (np.isfinite(T) and T > 0.0):
            raise RuntimeError(
                f"RK4 stage temperature {float(T):.6g} K is non-finite or <= 0 K; "
                f"the timestep is too large for this heat capacity at this state -- "
                f"increase steps_per_orbit or areal_heat_capacity (see the "
                f"stability warning)")
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
    # Evaluate stability at the HOTTEST plausible state (the zero-sink equilibrium),
    # where tau = C/(4 eps sigma T^3) is smallest and the explicit scheme is least
    # stable. Using t0_guess alone misses a cold start that heats into an unstable
    # regime (audit r8 P2-c).
    T_stab = max(float(T), steady_state_temperature(q_load, 0.0, eps))
    tau0 = thermal_time_constant(C, T_stab, eps)
    if dt > tau0:
        warnings.warn(
            f"RK4 timestep dt={dt:.3g} s exceeds the radiative time constant "
            f"tau={tau0:.3g} s at the zero-sink equilibrium ({T_stab:.1f} K); "
            f"explicit integration may be unstable -- increase steps_per_orbit or "
            f"areal_heat_capacity",
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

    # Temporal-accuracy gate (audit r5/r6/r7 P1): periodic closure + energy balance
    # do not certify that the timestep resolves the intra-orbit forcing, and ADJACENT
    # summary differences (N~2N, 2N~4N) are not a bound on the returned N-grid
    # solution -- two adjacent changes can each be < tol while the cumulative N->4N
    # drift, and the pointwise waveform error, exceed it (audit r7 P1). The
    # certificate therefore bounds the RETURNED profile directly with, all < time_tol_K:
    #   * a grid-free forcing-quadrature certificate (subpoint albedo has the exact
    #     orbit mean cos(beta)/pi, giving a closed form for <T_sink^4>);
    #   * POINTWISE errors of the returned N orbit and of 2N, each interpolated onto
    #     the converged 4N phase grid -- this bounds the temperature waveform in
    #     L-infinity (it does NOT bound the peak TIME; see peak_phase_residual_deg); and
    #   * the DIRECT N->4N (and 2N->4N, N->2N) peak/mean/swing summaries.
    # Each refined grid must itself reach periodic steady state, else uncertified.
    forcing_residual_K = n_to_2n_residual_K = two_n_to_4n_residual_K = None
    n_to_4n_residual_K = pointwise_n_to_4n_K = pointwise_2n_to_4n_K = None
    peak_time_residual_s = peak_phase_residual_deg = None
    refined_orbits_used = None
    if check_time_resolution:
        g2 = _converge(2 * steps_per_orbit)
        g4 = _converge(4 * steps_per_orbit)
        refined_orbits_used = (g2["orbits_used"], g4["orbits_used"])
        exact4 = sink_mod.sink_fourth_power_mean(
            vf, beta_deg, assume_sun_shielded=assume_sun_shielded,
            emissivity=eps, solar_absorptivity=solar_absorptivity,
            earth_ir=earth_ir, albedo=albedo, solar_constant=solar_constant,
            t_space=t_space)
        disc4 = float(np.mean(Ts_sink[:-1] ** 4))
        T_ref = float(np.mean(Ts_panel[:-1]))
        forcing_residual_K = abs(disc4 - exact4) / (4.0 * T_ref ** 3)
        if not (g2["converged"] and g4["converged"]):
            time_residual_K = float("inf")
            time_discretization_converged = False
        else:
            def _pms(Tp):
                return (float(Tp.max()), float(np.mean(Tp[:-1])),
                        float(Tp.max() - Tp.min()))
            p1, m1, s1 = _pms(Ts_panel)
            p2, m2, s2 = _pms(g2["Tp"])
            p4, m4, s4 = _pms(g4["Tp"])
            n_to_2n_residual_K = max(abs(p1 - p2), abs(m1 - m2), abs(s1 - s2))
            two_n_to_4n_residual_K = max(abs(p2 - p4), abs(m2 - m4), abs(s2 - s4))
            n_to_4n_residual_K = max(abs(p1 - p4), abs(m1 - m4), abs(s1 - s4))
            # Pointwise: interpolate N and 2N onto the 4N orbit phase grid (both
            # share the orbital period, so the time axis is the phase axis).
            t4 = g4["ts"]
            pointwise_n_to_4n_K = float(np.max(np.abs(
                np.interp(t4, ts, Ts_panel) - g4["Tp"])))
            pointwise_2n_to_4n_K = float(np.max(np.abs(
                np.interp(t4, g2["ts"], g2["Tp"]) - g4["Tp"])))
            # Peak-timing residual (audit r8 P2-b): an L-infinity TEMPERATURE bound
            # does not bound the time/phase of the argmax (a flat peak can drift).
            # Report it from the N vs 4N peak times; it is NOT gated by time_tol_K.
            peak_time_residual_s = abs(
                float(ts[int(np.argmax(Ts_panel))])
                - float(t4[int(np.argmax(g4["Tp"]))]))
            peak_phase_residual_deg = 360.0 * peak_time_residual_s / period
            time_residual_K = max(
                forcing_residual_K, n_to_2n_residual_K, two_n_to_4n_residual_K,
                n_to_4n_residual_K, pointwise_n_to_4n_K, pointwise_2n_to_4n_K)
            time_discretization_converged = bool(
                periodic_converged
                and time_safety_factor * time_residual_K < time_tol_K)
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
        msg = (f"transient did not resolve the intra-orbit forcing: "
               f"temporal-resolution residual {time_residual_K} K (x safety "
               f"{time_safety_factor:g}) vs tol {time_tol_K:.1e} K at "
               f"{steps_per_orbit} steps/orbit; increase steps_per_orbit (and "
               f"n_orbits/max_orbits so the 2N and 4N grids also reach periodic "
               f"steady state)")
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
            "forcing_residual_K": forcing_residual_K,
            "n_to_2n_residual_K": n_to_2n_residual_K,
            "two_n_to_4n_residual_K": two_n_to_4n_residual_K,
            "n_to_4n_residual_K": n_to_4n_residual_K,
            "pointwise_n_to_4n_K": pointwise_n_to_4n_K,
            "pointwise_2n_to_4n_K": pointwise_2n_to_4n_K,
            "peak_time_residual_s": peak_time_residual_s,
            "peak_phase_residual_deg": peak_phase_residual_deg,
            "refined_orbits_used": refined_orbits_used,
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
        "source": "ASM Aerospace Specification Metals, Aluminum 6061-T6 datasheet "
                  "(rho 2.70 g/cm^3; specific heat 896 J/kg/K at 20 C)",
        "source_class": "alloy datasheet (single nominal value)",
        "rel_uncertainty": 0.02,
    },
    "cover_glass": {
        "rho_kg_m3": 2500.0, "cp_J_kgK": 800.0,
        "state": "solid, 298 K",
        "source": "space PV cover glass, cerium-doped borosilicate class (e.g. Qioptiq "
                  "CMG/CMX); nominal rho ~2.5 g/cm^3, c_p ~800 J/kg/K at 25 C. A single "
                  "page citation is not meaningful: value is grade-dependent in-class.",
        "source_class": "representative grade (range; not single-source)",
        "rel_uncertainty": 0.05,
    },
    "silicon": {
        "rho_kg_m3": 2330.0, "cp_J_kgK": 700.0,
        "state": "crystalline solid, 298 K",
        "source": "CRC Handbook of Chemistry and Physics, 97th ed. (2016), "
                  "'Heat Capacity of the Elements at 25 C' + element density table; "
                  "crystalline Si (rho 2329 kg/m^3; c_p 705 J/kg/K at 298 K)",
        "source_class": "handbook (single tabulated value)",
        "rel_uncertainty": 0.02,
    },
    "cfrp_substrate": {
        "rho_kg_m3": 1600.0, "cp_J_kgK": 800.0,
        "state": "solid, 298 K",
        "source": "CMH-17 (Composite Materials Handbook, Vol. 2) carbon/epoxy laminate, "
                  "quasi-isotropic; rho ~1550-1600 kg/m^3, c_p ~800-1000 J/kg/K. Layup / "
                  "resin / fiber-volume dependent, so no single page applies.",
        "source_class": "representative grade (range; not single-source)",
        "rel_uncertainty": 0.15,
    },
    "ammonia_liquid": {
        "rho_kg_m3": 600.17, "cp_J_kgK": 4796.38,
        "state": "saturated liquid, 300 K (Q=0)",
        "source": "CoolProp HEOS at T=300 K, Q=0; strongly state-dependent "
                  "(280 K: 629/4649; 320 K: 568/5023). See coolant_rho_cp().",
        "source_class": "EOS backend (recomputed from the pinned CoolProp version)",
        "coolprop_version": "7.2.0",            # pinned in the [fluids] extra
        "eos_bibtex_key": "Gao-JPCRD-2020",     # from get_BibTeXKey at that version
        "rel_uncertainty": 0.01,                # PHYSICAL property uncertainty (cross-check)
        "stored_decimals": 2,                   # values rounded to 2 decimals
        "regression_rtol": 1e-4,                # CODE-regression tol vs the pinned backend
    },
    "copper": {
        "rho_kg_m3": 8960.0, "cp_J_kgK": 385.0,
        "state": "solid, 298 K",
        "source": "CRC Handbook of Chemistry and Physics, 97th ed. (2016), "
                  "'Heat Capacity of the Elements at 25 C' + element density table; "
                  "Cu (rho 8960 kg/m^3; c_p 385 J/kg/K at 298 K)",
        "source_class": "handbook (single tabulated value)",
        "rel_uncertainty": 0.01,
    },
    "fr4_pcb": {
        "rho_kg_m3": 1850.0, "cp_J_kgK": 1100.0,
        "state": "solid, 298 K",
        "source": "IPC-4101 FR-4 glass-reinforced epoxy laminate class; rho ~1850 kg/m^3, "
                  "c_p ~1100-1200 J/kg/K at 25 C. Resin/glass-ratio dependent within the "
                  "spec, so no single page applies.",
        "source_class": "representative grade (range; not single-source)",
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
    _v.boolean("assume_sun_shielded", assume_sun_shielded)
    _v.boolean("require_convergence", require_convergence)
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
            f"{diag['time_discretization_converged']} (temporal-resolution residual "
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
        "forcing_residual_K": diag["forcing_residual_K"],
        "n_to_2n_residual_K": diag["n_to_2n_residual_K"],
        "two_n_to_4n_residual_K": diag["two_n_to_4n_residual_K"],
        "n_to_4n_residual_K": diag["n_to_4n_residual_K"],
        "pointwise_n_to_4n_K": diag["pointwise_n_to_4n_K"],
        "pointwise_2n_to_4n_K": diag["pointwise_2n_to_4n_K"],
        "peak_time_residual_s": diag["peak_time_residual_s"],
        "peak_phase_residual_deg": diag["peak_phase_residual_deg"],
        "refined_orbits_used": diag["refined_orbits_used"],
    }
