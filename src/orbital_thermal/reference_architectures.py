"""Reference radiator architectures as data + reproducible heat balances.

Currently provides the Starcloud (formerly Lumen Orbit) 2024 white-paper case
as the second public architecture alongside AI1. The published inputs are
transcribed from the page-cited provenance record
``data/reference_architectures/starcloud_2024.yaml`` (Milestone A1); the
expected results are the white paper's own printed values (Thermal Management,
p. 9 of "Why we should train AI in space", v1.03, September 2024).

Two cases are exposed:

  * ``starcloud_published_balance`` (Milestone A2) -- the AS-WRITTEN balance,
    reproducing the paper's 633.08 W/m^2 net rejection. A single absorptivity
    (0.09) is applied to both the solar/albedo and Earth-IR bands.
  * ``starcloud_spectral_balance`` (Milestone A3) -- a SPECTRALLY-SEPARATED
    sensitivity case: the long-wave (Earth-IR) absorptivity is set equal to the
    thermal emissivity per Kirchhoff's law (0.92), giving ~584.76 W/m^2. This
    is an alternative radiative-property treatment, NOT a claim that the
    published design is wrong.

The published input constants below mirror the YAML record. Per the
repository's oracle-freeze policy, these published values are never edited to
make a test pass; a mismatch means the code is wrong, not the paper.

This module is pure-Python (no numpy / CoolProp) and is imported explicitly,
following the ``orbital_thermal.fluids`` convention -- it is not yet part of the
top-level package API.
"""

import math
from dataclasses import dataclass, replace

from . import spectral_radiation as sr

#: Stefan-Boltzmann constant AS PRINTED in the white paper (rounded to 5.67e-8).
#: Required to reproduce its displayed 770.48 / 633.08 W/m^2. The package's
#: SI-derived value (:data:`orbital_thermal.constants.SIGMA_SB`) differs by
#: ~3e-11 relative and shifts the net result by ~0.05 W/m^2 -- documented in the
#: A1 record's verification block and asserted in the published-balance test.
SIGMA_WHITEPAPER: float = 5.67e-8


@dataclass(frozen=True)
class RadiatorCaseInputs:
    """Published radiator inputs for a flat-panel orbital case.

    Per-field provenance status tags live in the YAML record; here every value
    is the source's published number unless a comment says otherwise. Earth
    albedo and Earth IR carry separate absorptivities so the same dataclass can
    express both the as-written case (both 0.09) and the spectral case (A3).
    """

    name: str
    radiator_temperature_K: float
    emissivity_thermal: float
    absorptivity_solar: float
    absorptivity_earth_ir: float
    earth_view_factor: float
    earth_albedo: float
    solar_irradiance_W_m2: float
    earth_temperature_K: float
    emitting_faces: int = 2
    sunlit_faces: int = 1
    source: str = ""


#: Starcloud 2024 white paper, Thermal Management (pp. 8-9). A single
#: absorptivity 0.09 is applied to BOTH the solar/albedo (short-wave) and the
#: Earth-IR (long-wave) bands, exactly as written.
STARCLOUD_2024_PUBLISHED = RadiatorCaseInputs(
    name="starcloud_2024_published",
    radiator_temperature_K=293.15,     # 20 C mean (inlet 35 C / outlet 5 C)
    emissivity_thermal=0.92,
    absorptivity_solar=0.09,
    absorptivity_earth_ir=0.09,        # paper reuses 0.09 for the IR band
    earth_view_factor=0.25,
    earth_albedo=0.30,
    solar_irradiance_W_m2=1366.0,
    earth_temperature_K=253.15,        # -20 C
    emitting_faces=2,
    sunlit_faces=1,
    source="Lumen Orbit/Starcloud 2024 white paper v1.03, p.9",
)


def kirchhoff_spectral_case(
    case: RadiatorCaseInputs, name: str | None = None, source: str | None = None
) -> RadiatorCaseInputs:
    """Return a copy of ``case`` with the long-wave absorptivity Kirchhoff-set.

    For a gray surface, the absorptivity in a band equals the emissivity in that
    band. The published case forces the Earth-IR (long-wave) absorptivity to the
    SOLAR (short-wave) value; this helper instead sets it equal to the panel's
    thermal emissivity -- the spectrally-separated screening interpretation. The
    short-wave absorptivity (direct sun + Earth albedo) is unchanged.
    """
    return replace(
        case,
        absorptivity_earth_ir=case.emissivity_thermal,
        name=name or f"{case.name}_spectral_separation",
        source=source or (
            "Spectral-separation interpretation (Kirchhoff: alpha_IR = "
            "emissivity); alternative treatment, not the white paper's claim. "
            f"Short-wave inputs from: {case.source}"
        ),
    )


#: Spectrally-separated alternative to the published Starcloud case: identical
#: to STARCLOUD_2024_PUBLISHED except the Earth-IR absorptivity is 0.92
#: (= emissivity), not 0.09. Tagged ``corrected`` in the YAML record.
STARCLOUD_2024_SPECTRAL = kirchhoff_spectral_case(
    STARCLOUD_2024_PUBLISHED,
    name="starcloud_2024_spectral_separation",
)


@dataclass(frozen=True)
class HeatBalanceResult:
    """Per-m^2-of-planform radiator heat balance. All fluxes in W/m^2."""

    case_name: str
    radiator_temperature_K: float
    emitted_W_m2: float
    direct_solar_absorbed_W_m2: float
    earth_albedo_absorbed_W_m2: float
    earth_ir_absorbed_W_m2: float
    earth_combined_absorbed_W_m2: float
    net_rejection_W_m2: float
    sigma_used_W_m2_K4: float
    source: str

    def required_planform_area_m2(self, heat_load_W: float) -> float:
        """Panel planform area (m^2) to reject ``heat_load_W`` at this flux.

        A = Q / q_net. Planform (one-sided geometric) area, not emitting area;
        the two-sided emission is already inside ``net_rejection_W_m2``.
        """
        if not (math.isfinite(heat_load_W) and heat_load_W > 0.0):
            raise ValueError(f"heat_load_W must be finite and > 0, got {heat_load_W}")
        if self.net_rejection_W_m2 <= 0.0:
            raise ValueError(
                "net rejection is non-positive; the panel cannot reject heat "
                "at this temperature/environment, so no finite area suffices"
            )
        return heat_load_W / self.net_rejection_W_m2


def radiator_heat_balance(
    case: RadiatorCaseInputs, sigma: float = SIGMA_WHITEPAPER
) -> HeatBalanceResult:
    """Evaluate the per-m^2 heat balance for ``case``.

    Earth albedo (short-wave, uses ``absorptivity_solar``) and Earth IR
    (long-wave, uses ``absorptivity_earth_ir``) are computed separately, then
    summed into ``earth_combined_absorbed_W_m2`` for comparison with sources
    that report a single combined Earth term.
    """
    emitted = sr.emitted_flux(
        case.radiator_temperature_K, case.emissivity_thermal, sigma, case.emitting_faces
    )
    solar = sr.solar_absorbed_flux(
        case.absorptivity_solar, case.solar_irradiance_W_m2, case.sunlit_faces
    )
    albedo = sr.earth_albedo_absorbed_flux(
        case.absorptivity_solar, case.earth_view_factor, case.earth_albedo,
        case.solar_irradiance_W_m2,
    )
    earth_ir = sr.earth_ir_absorbed_flux(
        case.absorptivity_earth_ir, case.earth_view_factor, sigma, case.earth_temperature_K
    )
    net = sr.net_rejection_flux(
        emitted=emitted,
        solar_absorbed=solar,
        earth_albedo_absorbed=albedo,
        earth_ir_absorbed=earth_ir,
    )
    return HeatBalanceResult(
        case_name=case.name,
        radiator_temperature_K=case.radiator_temperature_K,
        emitted_W_m2=emitted,
        direct_solar_absorbed_W_m2=solar,
        earth_albedo_absorbed_W_m2=albedo,
        earth_ir_absorbed_W_m2=earth_ir,
        earth_combined_absorbed_W_m2=albedo + earth_ir,
        net_rejection_W_m2=net,
        sigma_used_W_m2_K4=sigma,
        source=case.source,
    )


def starcloud_published_balance(sigma: float = SIGMA_WHITEPAPER) -> HeatBalanceResult:
    """Reproduce the white paper's as-written balance: 633.08 W/m^2 net.

    Milestone A2. Earth albedo and Earth IR are reported separately but BOTH use
    the published absorptivity of 0.09, matching the paper's single-absorptivity
    treatment. Pass ``sigma=orbital_thermal.constants.SIGMA_SB`` to see the
    ~0.05 W/m^2 shift from the SI-derived constant.
    """
    return radiator_heat_balance(STARCLOUD_2024_PUBLISHED, sigma=sigma)


def starcloud_spectral_balance(sigma: float = SIGMA_WHITEPAPER) -> HeatBalanceResult:
    """Spectrally-separated alternative: alpha_IR = emissivity = 0.92.

    Milestone A3. Reproduces ~584.76 W/m^2 net. Only the Earth-IR absorptivity
    changes from the published case (0.09 -> 0.92); the solar/albedo absorptivity
    and every other input are the white paper's published values. This is a
    SENSITIVITY case showing that wavelength-dependent coating properties
    materially change the result -- NOT a claim that the published design is
    invalid.
    """
    return radiator_heat_balance(STARCLOUD_2024_SPECTRAL, sigma=sigma)
