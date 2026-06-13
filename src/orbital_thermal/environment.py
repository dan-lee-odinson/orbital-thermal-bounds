"""Analytic orbital thermal environment: orbit geometry, eclipse, view factors.

This module supplies the *geometry* the third paper needs to turn the static
radiator bounds into an orbit-resolved picture: where the spacecraft is, when it
is in Earth's shadow, and how strongly a tilted radiator couples to the planet.

Everything here is closed-form or evaluated to machine precision -- no empirical
fits and no small-angle or cosine view-factor approximations. The functions are
validated in ``tests/test_environment.py`` against analytic special cases and an
independent numerical integrator.

Conventions
-----------
- Circular orbit, spherical Earth.
- ``altitude_km`` is height above mean Earth radius (``EARTH_RADIUS_KM``).
- ``beta_deg`` (orbit beta angle) is the angle between the Sun direction and the
  orbit plane: 0 deg = Sun in the orbit plane (deepest eclipse), 90 deg =
  Sun normal to the orbit plane (terminator orbit, no eclipse).
- ``tilt_deg`` (radiator) is the angle between a surface normal and the nadir
  (planet-center) direction: 0 deg = facing straight down, 180 deg = zenith.

Units: SI unless a name says otherwise (km for distances, seconds for time).
"""

import numpy as np

#: Mean Earth radius, km (matches the McCalip model's EARTH_RADIUS_KM).
EARTH_RADIUS_KM: float = 6371.0

#: Earth standard gravitational parameter, km^3/s^2 (WGS-84 / EGM).
MU_EARTH_KM3_S2: float = 398600.4418

# Gauss-Legendre nodes for the radial view-factor integral (module-level so the
# weights are built once). 48 nodes drive the per-panel error below 1e-9.
_GL_X, _GL_W = np.polynomial.legendre.leggauss(48)


def _check_altitude(altitude_km: float) -> None:
    if not (np.isfinite(altitude_km) and altitude_km > 0):
        raise ValueError(f"altitude_km must be finite and > 0, got {altitude_km}")


# ---------------------------------------------------------------------------
# Circular orbit geometry
# ---------------------------------------------------------------------------

def orbital_radius(altitude_km: float) -> float:
    """Orbital radius (Earth center to spacecraft), km."""
    _check_altitude(altitude_km)
    return EARTH_RADIUS_KM + altitude_km


def orbital_period(altitude_km: float) -> float:
    """Circular orbital period, seconds.  T = 2*pi*sqrt(r^3 / mu)."""
    r = orbital_radius(altitude_km)
    return 2.0 * np.pi * np.sqrt(r**3 / MU_EARTH_KM3_S2)


def orbital_velocity(altitude_km: float) -> float:
    """Circular orbital speed, km/s.  v = sqrt(mu / r)."""
    r = orbital_radius(altitude_km)
    return np.sqrt(MU_EARTH_KM3_S2 / r)


def earth_angular_radius(altitude_km: float) -> float:
    """Angular radius of Earth seen from orbit, radians.  arcsin(R_e / r)."""
    r = orbital_radius(altitude_km)
    return np.arcsin(EARTH_RADIUS_KM / r)


def beta_critical(altitude_km: float) -> float:
    """Beta angle above which a circular orbit never enters eclipse, degrees.

    Equal to the Earth angular radius: when the Sun sits farther from the orbit
    plane than Earth's angular size, the cylindrical shadow is never crossed.
    """
    return np.degrees(earth_angular_radius(altitude_km))


# ---------------------------------------------------------------------------
# Eclipse (cylindrical shadow model)
# ---------------------------------------------------------------------------

def eclipse_fraction(altitude_km: float, beta_deg: float) -> float:
    """Fraction of a circular orbit spent in Earth's shadow (0..1).

    Cylindrical-shadow model (Earth casts an infinite cylinder of its own
    radius; ignores penumbra and the Sun's finite size). Exact closed form:

        f_E = (1/pi) * arccos( sqrt(1 - (R_e/r)^2) / cos(beta) )

    valid while the argument <= 1; for |beta| >= beta_critical the orbit is in
    continuous sunlight and the fraction is 0. At beta = 0, low Earth orbit
    spends ~0.37 of each period in eclipse.
    """
    if not (0.0 <= beta_deg <= 90.0):
        raise ValueError(f"beta_deg must be in [0, 90], got {beta_deg}")
    r = orbital_radius(altitude_km)
    cos_eta = np.sqrt(1.0 - (EARTH_RADIUS_KM / r) ** 2)   # = cos(earth ang. radius)
    beta = np.radians(beta_deg)
    arg = cos_eta / np.cos(beta)
    if arg >= 1.0:
        return 0.0
    return float(np.arccos(arg) / np.pi)


def eclipse_duration(altitude_km: float, beta_deg: float) -> float:
    """Eclipse duration per orbit, seconds (= eclipse_fraction * period)."""
    return eclipse_fraction(altitude_km, beta_deg) * orbital_period(altitude_km)


# ---------------------------------------------------------------------------
# View factors (planar radiator element to spherical Earth)
# ---------------------------------------------------------------------------

def nadir_view_factor(altitude_km: float) -> float:
    """View factor from a nadir-facing flat plate to Earth (maximum possible).

    Closed form: VF_nadir = sin^2(theta) = (R_e / r)^2.  At 550 km: 0.8474.
    """
    return float(np.sin(earth_angular_radius(altitude_km)) ** 2)


def _vf_ring(psi: float, cg: float, sg: float) -> float:
    """Azimuth-integrated, horizon-clipped projected-solid-angle density at
    polar offset ``psi`` within Earth's disk. Analytic in azimuth."""
    a = np.sin(psi) * sg
    b = np.cos(psi) * cg
    if b >= abs(a):              # whole azimuth ring above the radiator horizon
        ring = 2.0 * np.pi * b
    elif b <= -abs(a):           # whole ring below the horizon
        ring = 0.0
    else:                        # ring straddles the horizon
        phi0 = np.arccos(np.clip(-b / a, -1.0, 1.0))
        ring = 2.0 * (a * np.sin(phi0) + b * phi0)
    return ring * np.sin(psi)


def sphere_view_factor(altitude_km: float, tilt_deg: float) -> float:
    """Exact view factor from a tilted flat plate to spherical Earth.

    ``tilt_deg`` is the angle between the plate normal and nadir. This treats
    Earth as a uniform disk of angular radius ``theta = arcsin(R_e/r)`` centered
    on nadir and integrates the cosine-weighted solid angle over the part of
    that disk above the plate's horizon -- the exact radiative view factor, with
    no cosine approximation. The azimuthal integral is closed-form; the radial
    integral is evaluated by piecewise Gauss-Legendre quadrature split at the
    horizon crossings, accurate to ~1e-9.

    Limiting cases (returned in closed form):
      - tilt <= 90deg - theta:   F = cos(tilt) * sin^2(theta)   (Earth fully up)
      - tilt >= 90deg + theta:   F = 0                          (Earth fully set)
    """
    if not (0.0 <= tilt_deg <= 180.0):
        raise ValueError(f"tilt_deg must be in [0, 180], got {tilt_deg}")
    theta = earth_angular_radius(altitude_km)
    g = np.radians(tilt_deg)
    sin2 = np.sin(theta) ** 2
    if g <= (np.pi / 2 - theta):
        return float(np.cos(g) * sin2)
    if g >= (np.pi / 2 + theta):
        return 0.0
    cg, sg = np.cos(g), np.sin(g)
    # Kinks where the azimuth ring transitions (b = +/- a): split the panel there.
    cand = {abs(np.pi / 2 - g), np.pi / 2 + g}
    knots = sorted({0.0, theta} | {k for k in cand if 0.0 < k < theta})
    total = 0.0
    for lo, hi in zip(knots[:-1], knots[1:]):
        mid, half = 0.5 * (hi + lo), 0.5 * (hi - lo)
        nodes = mid + half * _GL_X
        vals = np.array([_vf_ring(p, cg, sg) for p in nodes])
        total += half * float(np.dot(_GL_W, vals))
    return total / np.pi
