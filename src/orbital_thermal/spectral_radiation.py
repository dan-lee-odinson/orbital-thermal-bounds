"""Spectrally-resolved radiator heat-balance terms (flat-panel orbital case).

These are the building blocks for a flat-panel orbital radiator that

  * emits thermal IR from two faces (gray body, emissivity ``emissivity``),
  * absorbs direct sunlight on its sunlit face(s),
  * absorbs Earth's reflected sunlight (albedo, short-wave), and
  * absorbs Earth's own thermal-IR emission (long-wave).

Unlike :mod:`orbital_thermal.radiation`, which lumps the environment into a
single effective sink T_s^eff, this module keeps each absorbed-flux term
explicit and lets the SHORT-WAVE absorptivity (to sunlight and Earth albedo)
differ from the LONG-WAVE absorptivity (to Earth's thermal IR). That spectral
separation is what the Starcloud 2024 white-paper comparison exercises (see
``data/reference_architectures/starcloud_2024.yaml``): the paper applies one
absorptivity to both bands; a Kirchhoff-consistent coating generally does not.

All fluxes are per square metre of panel PLANFORM area (one geometric side),
in W/m^2; temperatures in kelvin. ``sigma`` is passed explicitly so a caller
can reproduce a source that used a rounded Stefan-Boltzmann constant; the
package's SI-derived value lives in :data:`orbital_thermal.constants.SIGMA_SB`.

Scope: gray, diffuse, isothermal panel; far-field radiation only. No
conduction, coolant, or view-factor geometry beyond the scalar ``F`` the caller
supplies. The orbit-resolved view factor lives in
:mod:`orbital_thermal.environment`; harmonized cases (Milestone A5) feed it in.
"""

import math


def _check_unit_interval(name: str, x: float) -> None:
    if not (math.isfinite(x) and 0.0 <= x <= 1.0):
        raise ValueError(f"{name} must be finite in [0, 1], got {x}")


def _check_positive(name: str, x: float) -> None:
    if not (math.isfinite(x) and x > 0.0):
        raise ValueError(f"{name} must be finite and > 0, got {x}")


def _check_nonneg(name: str, x: float) -> None:
    if not (math.isfinite(x) and x >= 0.0):
        raise ValueError(f"{name} must be finite and >= 0, got {x}")


def emitted_flux(
    T: float, emissivity: float, sigma: float, faces: int = 2
) -> float:
    """Thermal IR emitted per m^2 of planform, summed over ``faces`` sides.

    q_emit = faces * emissivity * sigma * T^4
    """
    _check_unit_interval("emissivity", emissivity)
    _check_nonneg("radiator temperature", T)
    _check_positive("sigma", sigma)
    if faces < 1:
        raise ValueError(f"faces must be an integer >= 1, got {faces}")
    return faces * emissivity * sigma * T**4


def solar_absorbed_flux(
    alpha_solar: float, solar_irradiance: float, sunlit_faces: int = 1
) -> float:
    """Direct-sunlight absorption per m^2 of planform.

    q_sun = sunlit_faces * alpha_solar * S
    """
    _check_unit_interval("alpha_solar", alpha_solar)
    _check_nonneg("solar_irradiance", solar_irradiance)
    if sunlit_faces < 0:
        raise ValueError(f"sunlit_faces must be an integer >= 0, got {sunlit_faces}")
    return sunlit_faces * alpha_solar * solar_irradiance


def earth_albedo_absorbed_flux(
    alpha_solar: float, view_factor: float, albedo: float, solar_irradiance: float
) -> float:
    """Earth-reflected sunlight (short-wave) absorbed per m^2 of planform.

    q_albedo = alpha_solar * F * albedo * S

    Uses the SOLAR (short-wave) absorptivity, because Earth's albedo is
    reflected sunlight.
    """
    _check_unit_interval("alpha_solar", alpha_solar)
    _check_unit_interval("view_factor", view_factor)
    _check_unit_interval("albedo", albedo)
    _check_nonneg("solar_irradiance", solar_irradiance)
    return alpha_solar * view_factor * albedo * solar_irradiance


def earth_ir_absorbed_flux(
    alpha_ir: float, view_factor: float, sigma: float, T_earth: float
) -> float:
    """Earth's thermal-IR (long-wave) absorbed per m^2 of planform.

    q_earth_ir = alpha_ir * F * sigma * T_earth^4

    Uses the LONG-WAVE absorptivity. The white paper sets this equal to the
    solar value (0.09); a Kirchhoff-consistent screening sets it equal to the
    thermal emissivity instead (Milestone A3).
    """
    _check_unit_interval("alpha_ir", alpha_ir)
    _check_unit_interval("view_factor", view_factor)
    _check_positive("sigma", sigma)
    _check_nonneg("earth temperature", T_earth)
    return alpha_ir * view_factor * sigma * T_earth**4


def net_rejection_flux(
    *,
    emitted: float,
    solar_absorbed: float,
    earth_albedo_absorbed: float,
    earth_ir_absorbed: float,
) -> float:
    """Net heat rejected per m^2 of planform.

    q_net = q_emit - q_sun - q_albedo - q_earth_ir

    Keyword-only so the four terms can never be transposed by accident.
    """
    return emitted - solar_absorbed - earth_albedo_absorbed - earth_ir_absorbed
