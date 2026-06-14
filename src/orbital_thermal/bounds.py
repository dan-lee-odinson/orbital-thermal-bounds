"""Reversible thermodynamic bounds (Level B results of the theory preprint).

Implements Theorems 1-5 and Corollary 2.1 of "Thermodynamic Bounds and
Mass-Trade Criteria for Heat Rejection in Orbital Data Centers"
(doi:10.5281/zenodo.20650893). Pure stdlib; no dependencies.

Conventions: temperatures in kelvin, ``eta`` is heat-engine efficiency in
(0, 1), areas are emitting areas. The zero-sink case is ``T_sink = 0``.
"""

import math

from .constants import SIGMA_SB
from . import _validate as _v


# --------------------------------------------------------------------------
# Theorem 1 -- sink-temperature Carnot is unattainable at finite area
# --------------------------------------------------------------------------

def fixed_work_area_per_watt(
    T_h: float, T_c: float, T_sink: float, emissivity: float = 1.0
) -> float:
    """Radiator area per watt of work output for a reversible engine, m^2/W.

    A/W >= T_c / (emissivity * sigma * (T_h - T_c) * (T_c^4 - T_sink^4))

    Diverges as T_c -> T_sink (Carnot limit) and as T_c -> T_h (zero work):
    the basis of Theorem 1's non-attainability result. Worked anchor:
    T_h = 300 K, T_c = 3.0 K, T_sink = 2.7 K gives eta = 99% at about
    6.4e9 m^2 per MW -- legal, but extreme-area.
    """
    if not 0.0 < emissivity <= 1.0:
        raise ValueError(f"emissivity must be in (0, 1], got {emissivity}")
    _v.finite("T_h", T_h)
    _v.finite("T_c", T_c)
    _v.nonneg("T_sink", T_sink)
    if not 0.0 <= T_sink < T_c < T_h:
        raise ValueError(
            f"need 0 <= T_sink < T_c < T_h, got T_sink={T_sink}, "
            f"T_c={T_c}, T_h={T_h}"
        )
    return T_c / (
        emissivity * SIGMA_SB * (T_h - T_c) * (T_c**4 - T_sink**4)
    )


# --------------------------------------------------------------------------
# Theorem 2 -- the 3/4 rule (zero-sink reversible lower envelope)
# --------------------------------------------------------------------------

def optimal_cold_fraction(a: float = 1.0, tol: float = 1e-12, max_iter: int = 1000) -> float:
    """Area-per-work-optimal T_c/T_h for an engine with eta = a*(1 - T_c/T_h).

    Minimizes A/W proportional to (1 - eta) / (eta * y^4) over y = T_c/T_h.

    Implementation: bisection on the stationarity condition

        g(y) = a/(1 - a*(1 - y)) + 1/(1 - y) - 4/y = 0

    (the derivative of log A/W). g is strictly increasing on (0, 1): although its
    first term a/(1 - a(1 - y)) is *decreasing*, the full derivative
    g'(y) = -a^2/(1 - a(1 - y))^2 + 1/(1 - y)^2 + 4/y^2 is positive there, because
    1 - a(1 - y) >= y (their difference is (1 - y)(1 - a) >= 0 for a <= 1) gives
    a^2/(1 - a(1 - y))^2 <= 1/y^2 < 4/y^2. So g has exactly one root and bisection
    converges to full precision -- a direct search on the objective itself stalls
    near the minimum, where objective differences fall below float resolution.

    Theorem 2: a = 1 (reversible) gives exactly 3/4 (g reduces to
    1/(1 - y) - 3/y), with a 25% efficiency ceiling. Irreversibility
    shifts the optimum up: a = 0.8 -> 0.7645, a = 0.5 -> 0.7808.
    """
    if not 0.0 < a <= 1.0:
        raise ValueError(f"irreversibility factor a must be in (0, 1], got {a}")
    if not (tol > 0.0 and tol < float("inf")):
        raise ValueError(f"tol must be finite and positive, got {tol}")
    if max_iter <= 0:
        raise ValueError(f"max_iter must be positive, got {max_iter}")

    def g(y: float) -> float:
        return a / (1.0 - a * (1.0 - y)) + 1.0 / (1.0 - y) - 4.0 / y

    lo, hi = 1e-12, 1.0 - 1e-12
    for _ in range(max_iter):
        if hi - lo <= tol:
            return 0.5 * (lo + hi)
        mid = 0.5 * (lo + hi)
        if mid <= lo or mid >= hi:        # bracket collapsed to float resolution
            return mid
        if g(mid) < 0.0:
            lo = mid
        else:
            hi = mid
    raise RuntimeError(
        f"optimal_cold_fraction bisection did not converge to tol={tol} in "
        f"{max_iter} steps (bracket width {hi - lo:.3g}); increase max_iter"
    )


# --------------------------------------------------------------------------
# Theorem 3 -- nonzero-sink optimum (exact implicit quintic)
# --------------------------------------------------------------------------

def nonzero_sink_optimum(
    T_h: float, T_sink: float, tol: float = 1e-10, max_iter: int = 1000
) -> float:
    """Optimal cold-side temperature T_c* for sink temperature T_sink > 0.

    Solves the quintic 4*T_c^5 - 3*T_h*T_c^4 - T_h*T_sink^4 = 0 by bisection on
    its dimensionless form f(y) = 4y^5 - 3y^4 - r^4 (y = T_c/T_h, r = T_sink/T_h),
    bracketed on (max(3/4, r), 1) and iterated to ``tol`` kelvin (the published
    suites enforce 1e-10 K). Bisection is globally convergent; the earlier
    fixed-point map Phi(T) = (T_h/4)(3 + (T_sink/T)^4) has |Phi'| = 4q^4/(3 + q^4)
    -> 1 as T_sink -> T_h and fails to converge for r >~ 0.97 (audit item 6).

    Equivalent exact form: T_c*/T_h = (3 + q^4)/4 with q = T_sink/T_c*;
    the fractional shift above (3/4)T_h is exactly q^4/3. Worked anchor:
    T_h = 600 K, T_sink = 220 K gives T_c* = 457.98675408138325 K
    (+1.7748% above 450 K).
    """
    if T_h <= 0.0:
        raise ValueError(f"T_h must be positive, got {T_h}")
    if not 0.0 <= T_sink < T_h:
        raise ValueError(f"need 0 <= T_sink < T_h, got {T_sink}")
    if not (math.isfinite(tol) and tol > 0.0):
        raise ValueError(f"tol must be finite and > 0, got {tol}")
    if max_iter <= 0:
        raise ValueError(f"max_iter must be positive, got {max_iter}")
    if T_sink == 0.0:
        return 0.75 * T_h
    # Bisection on the dimensionless quintic f(y) = 4y^5 - 3y^4 - r^4, y = T_c/T_h,
    # r = T_sink/T_h. The optimum satisfies y* >= 3/4 (Theorem 2) and y* > r, and
    # f is strictly increasing on (max(3/4, r), 1) with f(max(3/4, r)) < 0 and
    # f(1) = 1 - r^4 > 0, so a unique root is bracketed there. Bisection is
    # globally convergent, unlike the fixed-point map Phi(T) whose contraction
    # |Phi'| = 4q^4/(3 + q^4) -> 1 as T_sink -> T_h (it fails to converge for
    # r >~ 0.97). This is the same quintic the Theorem-2 optimizer brackets.
    r = T_sink / T_h

    def f(y: float) -> float:
        return 4.0 * y**5 - 3.0 * y**4 - r**4

    lo, hi = max(0.75, r), 1.0
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        if f(mid) < 0.0:
            lo = mid
        else:
            hi = mid
        if (hi - lo) * T_h < tol:
            return 0.5 * (lo + hi) * T_h
    raise RuntimeError(
        f"nonzero_sink_optimum did not converge to tol={tol} K in {max_iter} "
        f"bisection steps (bracket width {(hi - lo) * T_h:.3g} K for T_h={T_h}, "
        f"T_sink={T_sink}); increase max_iter"
    )


def quintic_residual(T_c: float, T_h: float, T_sink: float) -> float:
    """Dimensionless residual of the Theorem 3 quintic at T_c.

    With y = T_c/T_h and r = T_sink/T_h: residual = 4y^5 - 3y^4 - r^4,
    which is zero at the optimum (published tolerance: |residual| < 1e-12).
    """
    _v.nonneg("T_c", T_c)
    _v.positive("T_h", T_h)
    _v.nonneg("T_sink", T_sink)
    y = T_c / T_h
    r = T_sink / T_h
    return 4.0 * y**5 - 3.0 * y**4 - r**4


# --------------------------------------------------------------------------
# Corollary 2.1 -- conversion area penalty
# --------------------------------------------------------------------------

def conversion_area_penalty(
    T_h: float, T_c: float, eta: float, T_sink: float = 0.0
) -> float:
    """Area ratio A_engine / A_direct for converting heat to work first.

    A_engine/A_direct = (1 - eta) * (T_h^4 - T_sink^4) / (T_c^4 - T_sink^4)

    Zero-sink reversible bound: >= (T_h/T_c)^3, with minimum (4/3)^3 ~ 2.370
    at the Theorem 2 optimum; strictly larger for T_sink > 0.
    """
    if not 0.0 < eta < 1.0:
        raise ValueError(f"eta must be in (0, 1), got {eta}")
    if not 0.0 <= T_sink < T_c < T_h:
        raise ValueError(
            f"need 0 <= T_sink < T_c < T_h, got T_sink={T_sink}, "
            f"T_c={T_c}, T_h={T_h}"
        )
    eta_carnot = 1.0 - T_c / T_h
    if eta > eta_carnot + 1e-9:
        raise ValueError(
            f"eta={eta} exceeds the Carnot ceiling 1 - T_c/T_h = {eta_carnot:.6g} "
            f"for an engine between T_h={T_h} K and T_c={T_c} K; the area-penalty "
            "bound assumes a realizable (sub-Carnot) engine"
        )
    return (1.0 - eta) * (T_h**4 - T_sink**4) / (T_c**4 - T_sink**4)


# --------------------------------------------------------------------------
# Theorem 4 -- heat-pump identities
# --------------------------------------------------------------------------

def carnot_cop_cooling(T_c: float, T_h: float) -> float:
    """Carnot ceiling on the cooling COP: COP_c <= T_c / (T_h - T_c).

    Worked anchor: lifting 353 K -> 520 K gives COP_c <= 2.114.
    """
    _v.positive("T_c", T_c)
    _v.finite("T_h", T_h)
    if not 0.0 < T_c < T_h:
        raise ValueError(f"need 0 < T_c < T_h, got T_c={T_c}, T_h={T_h}")
    return T_c / (T_h - T_c)


def heating_cop(cop_cooling: float) -> float:
    """First-law identity COP_h = COP_c + 1 (Theorem 4)."""
    if not (math.isfinite(cop_cooling) and cop_cooling > 0.0):
        raise ValueError(f"COP_c must be finite and > 0, got {cop_cooling}")
    return cop_cooling + 1.0


def heat_pump_overhead(cop_cooling: float) -> float:
    """Electrical overhead per watt of heat lifted: W/Q_c = 1/COP_c.

    Worked anchor: the 353/520 K Carnot ceiling gives minimum overhead
    0.473 W per W.
    """
    if not (math.isfinite(cop_cooling) and cop_cooling > 0.0):
        raise ValueError(f"COP_c must be finite and > 0, got {cop_cooling}")
    return 1.0 / cop_cooling


def heat_pump_area_ratio(
    cop_cooling: float, T1: float, T2: float, T_sink: float = 0.0
) -> float:
    """Area ratio A_pumped / A_direct for rejecting at T2 instead of T1.

    (1 + 1/COP_c) * (T1^4 - T_sink^4) / (T2^4 - T_sink^4)

    The pump adds its own work as extra heat (numerator factor) but buys a
    hotter, smaller radiator (denominator). Worked anchor: COP_c = 1.15,
    353 -> 520 K, T_sink = 220 K gives exactly 0.348 (zero-sink
    approximation 0.397).
    """
    if not (cop_cooling > 0.0):          # also rejects NaN
        raise ValueError(f"COP_c must be a positive number, got {cop_cooling}")
    if T_sink < 0.0:
        raise ValueError(f"T_sink must be >= 0 K, got {T_sink}")
    if not (T_sink < T1 and T_sink < T2):
        raise ValueError("both temperatures must exceed the sink")
    if not T2 > T1:
        raise ValueError(
            f"need a genuine upward lift T2 > T1, got T1={T1} K, T2={T2} K"
        )
    cop_carnot = T1 / (T2 - T1)
    if cop_cooling > cop_carnot * (1.0 + 1e-9):
        raise ValueError(
            f"cop_cooling={cop_cooling} exceeds the Carnot cooling ceiling "
            f"T1/(T2 - T1) = {cop_carnot:.6g} for the {T1} -> {T2} K lift"
        )
    return (1.0 + 1.0 / cop_cooling) * (T1**4 - T_sink**4) / (
        T2**4 - T_sink**4
    )


# --------------------------------------------------------------------------
# Theorem 5 -- no self-powering
# --------------------------------------------------------------------------

def recirculation_amplification(eta: float) -> float:
    """Steady-state amplification 1/(1 - eta) of waste-heat recirculation.

    Theorem 5: external power P_ext = P*(1 - eta) > 0 always (Kelvin-Planck);
    recirculation amplifies delivered power by at most 1/(1 - eta).
    Worked anchor: eta = 0.25 -> 1.333.
    """
    if not 0.0 < eta < 1.0:
        raise ValueError(f"eta must be in (0, 1), got {eta}")
    return 1.0 / (1.0 - eta)
