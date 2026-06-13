"""Time-resolved effective sink temperature around a circular orbit.

The companion paper sizes the AI1 radiator with a *constant* environmental sink,
T_s = 220 K, in A = Q / (eps*sigma*(T^4 - T_s^4)). That single number stands in
for everything the radiator's cold side actually sees: deep space, Earth's
infrared glow, and reflected sunlight (albedo). This module computes the sink
the radiator truly experiences as a function of orbit position and beta angle,
so the third paper can show how good (or conservative) the 220 K stand-in is.

Definition
----------
For a radiator of emissivity ``eps`` and solar absorptivity ``alpha_s``, the net
heat it rejects per unit area is

    q_net = eps*sigma*T^4 - q_absorbed_environment

We define the effective sink temperature T_s^eff by writing this in the paper's
form, q_net = eps*sigma*(T^4 - T_s_eff^4), so that

    sigma*T_s_eff^4 = q_IR + (alpha_s/eps)*q_albedo + sigma*T_space^4

Key point: Earth infrared is absorbed and re-emitted in the *same* band, so its
absorptivity equals ``eps`` and the emissivity cancels -- the IR part of the sink
is independent of the radiator's optical properties. Only the reflected-solar
(albedo) part carries the alpha_s/eps ratio that real radiators are designed to
keep small.

Geometry (standard first-order spacecraft-thermal model)
--------------------------------------------------------
- Earth IR irradiance on the surface: q_IR = E_ir * VF(tilt), with VF the exact
  tilted-plate-to-sphere view factor from :mod:`orbital_thermal.environment`.
- Albedo irradiance: q_alb = a * S * VF(tilt) * max(0, cos(zeta)), where the
  solar zenith angle at the sub-satellite point obeys cos(zeta) = cos(beta)*cos(u)
  and ``u`` is the in-orbit angle from orbit noon. Albedo is zero on the night
  side (cos(zeta) <= 0), which automatically includes eclipse.

NOTE (audit item 3): the albedo term is a SUBPOINT APPROXIMATION
(:func:`subpoint_albedo_factor`), not disk-integrated albedo. Its beta-90 and
eclipse albedo nulls are artifacts of sampling reflectance only beneath the
spacecraft; the true disk-integrated albedo can be nonzero there.

This deliberately omits direct solar on the radiator: a heat-rejection surface is
oriented away from the Sun, so direct flux falls on its back face. The model is
therefore the environment seen by the *cold* side.
"""

import numpy as np

from .constants import SIGMA_SB
from . import environment as env

#: Default deep-space background temperature, K (CMB).
T_SPACE_K: float = 2.7255

# Reference environmental fluxes (orbit-average values, W/m^2).
EARTH_IR_FLUX: float = 237.0       # Earth outgoing longwave radiation
SOLAR_CONSTANT: float = 1361.0     # solar irradiance at 1 AU
EARTH_ALBEDO: float = 0.30         # Bond albedo


def subpoint_albedo_factor(beta_deg: float, u_deg: float) -> float:
    """SUBPOINT albedo approximation: clamped cosine of the solar zenith angle at
    the sub-satellite point.

        cos(zeta) = cos(beta) * cos(u),   factor = max(0, cos(zeta))

    This is a first-order stand-in for the reflected-solar (albedo) drive on the
    radiator: it samples reflectance only at the point directly below the
    spacecraft. It is NOT the disk-integrated albedo. Two consequences are
    artifacts of the approximation, not physics:

    * At beta = 90 deg it returns 0 for every ``u``, so the model reports zero
      albedo around a terminator orbit -- yet the visible Earth disk is still
      partly sunlit, so the true disk-integrated albedo is nonzero.
    * It vanishes whenever the subpoint is dark, even when sunlit Earth remains
      within the radiator's field of view.

    A faithful model integrates reflected radiance over the Earth region that is
    simultaneously sunlit, above the radiator's horizon, and visible to it (see
    the package roadmap / audit item 3). Until then, treat beta-90 albedo nulls
    and eclipse-driven albedo nulls as model limitations.
    """
    return float(max(0.0, np.cos(np.radians(beta_deg)) * np.cos(np.radians(u_deg))))


def effective_sink_temperature(
    altitude_km: float,
    beta_deg: float,
    u_deg: float,
    tilt_deg: float = 0.0,
    emissivity: float = 0.91,
    solar_absorptivity: float = 0.20,
    earth_ir: float = EARTH_IR_FLUX,
    albedo: float = EARTH_ALBEDO,
    solar_constant: float = SOLAR_CONSTANT,
    t_space: float = T_SPACE_K,
    assume_sun_shielded: bool = True,
) -> float:
    """Effective radiative sink temperature, K, at one orbit position.

    ``u_deg`` is the in-orbit angle from orbit noon (sub-solar meridian); 0 deg is
    the point closest to the Sun, 180 deg the anti-solar (deep night) point.
    ``tilt_deg`` is the radiator normal's angle from nadir (0 = Earth-facing,
    180 = space-facing).

    Attitude assumption (audit item 8): this models only the *cold-side*
    environment and OMITS direct solar flux on the radiator face -- valid only for
    an anti-solar / sun-shielded attitude, where direct sunlight falls on the back
    face. ``tilt_deg`` is accepted for arbitrary Earth coupling, but the result is
    NOT a general all-attitude sink. ``assume_sun_shielded`` makes this explicit:
    it must be True (the default). Setting it False raises ``NotImplementedError``,
    since direct-solar loading from the surface normal and Sun vector is not yet
    modeled -- a guard so the omission cannot be silently misread as general.
    """
    if emissivity <= 0:
        raise ValueError("emissivity must be positive")
    if not assume_sun_shielded:
        raise NotImplementedError(
            "effective_sink_temperature models only the sun-shielded (anti-solar) "
            "cold side; direct solar flux on the radiator face is not modeled. "
            "Pass assume_sun_shielded=True (the default) to acknowledge this, or "
            "extend the model with a direct-solar term from the normal and Sun "
            "vector before treating arbitrary tilt as a general sink."
        )
    vf = env.sphere_view_factor(altitude_km, tilt_deg)
    # Reflected-solar drive uses the SUBPOINT albedo approximation (see
    # subpoint_albedo_factor): a stand-in, not disk-integrated albedo.
    albedo_factor = subpoint_albedo_factor(beta_deg, u_deg)
    q_ir = earth_ir * vf
    q_alb = albedo * solar_constant * vf * albedo_factor
    t4 = (q_ir + (solar_absorptivity / emissivity) * q_alb) / SIGMA_SB + t_space**4
    return float(t4**0.25)


def in_eclipse(altitude_km: float, beta_deg: float, u_deg: float) -> bool:
    """True if the spacecraft is in Earth's cylindrical shadow at this position."""
    r = env.orbital_radius(altitude_km)
    cos_eta = np.sqrt(1.0 - (env.EARTH_RADIUS_KM / r) ** 2)
    cos_zeta = np.cos(np.radians(beta_deg)) * np.cos(np.radians(u_deg))
    return bool(cos_zeta < -cos_eta)


def sink_profile(
    altitude_km: float,
    beta_deg: float,
    tilt_deg: float = 0.0,
    n: int = 361,
    **kwargs,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (u_deg, T_s_eff) arrays over one full orbit (0..360 deg).

    The grid includes both endpoints (0 and 360 deg are the same orbit point), so
    it closes the loop for plotting. Any radiative averaging must drop the
    duplicated endpoint (slice ``[:-1]``); :func:`orbit_averaged_sink` does this.
    """
    u = np.linspace(0.0, 360.0, n)
    T = np.array(
        [effective_sink_temperature(altitude_km, beta_deg, ui, tilt_deg, **kwargs)
         for ui in u]
    )
    return u, T


def orbit_averaged_sink(
    altitude_km: float,
    beta_deg: float,
    tilt_deg: float = 0.0,
    n: int = 720,
    **kwargs,
) -> float:
    """Radiatively-weighted orbit-average sink, K: ( <T_s_eff^4> )^(1/4).

    The fourth-power mean is the average relevant to radiator sizing, since heat
    rejection scales with T^4.
    """
    _, T = sink_profile(altitude_km, beta_deg, tilt_deg, n=n, **kwargs)
    # Drop the duplicated 360deg endpoint so it is not double-counted (consistent
    # with transient.averaging_bias, which also slices [:-1]). Audit item 7.
    return float(np.mean(T[:-1] ** 4) ** 0.25)
