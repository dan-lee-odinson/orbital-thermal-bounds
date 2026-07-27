"""Harmonized orbital comparison of AI1 and Starcloud (Milestone A5).

Puts both architectures under ONE orbital environment and ONE set of conventions
using the package's own machinery, so the two are finally like-for-like (unlike
the as-published comparison in :mod:`orbital_thermal.architecture_comparison`,
which keeps each design's own assumptions and is explicitly NOT a ranking).

Shared harmonized conventions
-----------------------------
* Exact Earth view factor from :func:`orbital_thermal.environment.sphere_view_factor`.
  At the default geometry (550 km, radiator edge-on to nadir, tilt = 90 deg) this
  is F = 0.258 -- essentially the white paper's assumed 0.25, reached here from
  orbit geometry rather than assumed.
* Package environmental constants (``EARTH_IR_FLUX`` = 237 W/m^2,
  ``SOLAR_CONSTANT`` = 1361 W/m^2, ``EARTH_ALBEDO`` = 0.30) from
  :mod:`orbital_thermal.sink`, replacing each paper's fixed values.
* Orbit-mean reflected-solar drive: the subpoint albedo factor cos(beta)/pi
  (:func:`orbital_thermal.sink.analytic_albedo_orbit_mean`).
* SI Stefan-Boltzmann (:data:`orbital_thermal.constants.SIGMA_SB`), NOT the
  paper's rounded constant.
* Kirchhoff spectral convention: long-wave (Earth-IR) absorptivity = emissivity.
* Earth albedo (short-wave) and Earth IR (long-wave) are reported SEPARATELY.
* Per-planform fluxes; two-sided thermal emission; environmental absorption on
  the Earth-facing side via the single view factor F.

Each architecture keeps its OWN published optical properties: emissivity
(AI1 0.91, Starcloud 0.92) and short-wave solar absorptivity (Starcloud 0.09).
AI1 publishes NO solar absorptivity, so its reflected-solar (albedo) and any
direct-solar term are left as ``NOT_PUBLISHED`` and never invented; only an
explicit parametric value (a sensitivity, not a ranked case) fills them in.
Because the albedo term is the ONLY one that needs the short-wave absorptivity,
``net_excluding_albedo`` is always computable; the full ``net_rejection`` is
``None`` whenever a required term is unpublished.

Model limitation (surfaced, not hidden)
---------------------------------------
The subpoint albedo factor is 0 at the dawn-dusk endpoint (beta = 90 deg), so
the orbit-mean albedo vanishes there for BOTH architectures regardless of
absorptivity. That is a known limitation of the package's albedo model (true
disk-integrated albedo is nonzero at a terminator orbit), surfaced as a
``RuntimeWarning`` -- NOT a statement that the radiators see no reflected
sunlight. The published Starcloud environmental load is preserved alongside the
sweep (see :func:`published_starcloud_environment`) so the beta-90 null never
erases it.

This is a REDUCED-ORDER screening comparison and says so: flat-plate radiator,
single Earth-facing view factor, orbit-averaged albedo, no eclipse transient,
no deployable-structure or mass modelling.
"""

import warnings
from dataclasses import dataclass

from . import environment as env
from . import sink
from . import spectral_radiation as sr
from .architecture_comparison import AI1_DESIGN_POINT, NOT_PUBLISHED
from .constants import SIGMA_SB
from .reference_architectures import STARCLOUD_2024_PUBLISHED, starcloud_published_balance
from .registry.collapse import Collapse, Transcription

# --- C11(i): what this module collapses, declared on the module itself -------------
#
# DECLARATION ONLY. No number moves: every comparison below is exactly as released at
# v1.1.0. The module already SAID this in prose, which is the point -- the declaration
# quotes that prose rather than restating it, so the two cannot drift apart.
#
# The collapse is performed by sink.analytic_albedo_orbit_mean, whose closed-form orbit
# average is grid-free and exact for what it computes. It is declared HERE, not there,
# because this is the module that applies it as a screening simplification and this is
# where the prose describing it lives. A different caller could use the same exact mean
# without collapsing anything -- the collapse belongs to the use, not to the function.
COLLAPSES: tuple[Collapse, ...] = (
    Collapse(
        quantity="albedo load over the orbit",
        representative_value="the closed-form orbit mean cos(beta)/pi",
        phenomena=("temporal_profile", "eclipse_transient"),
        basis=(
            "The environmental forcing enters as an orbit-averaged albedo factor, so "
            "the comparison sees one steady load rather than a load that varies "
            "around the orbit and falls through eclipse. Peak and swing are therefore "
            "outside what this module can report; transient.py quantifies the penalty "
            "of that assumption separately, and does not feed this comparison."
        ),
        transcription=Transcription(
            module="orbital_thermal.harmonized_comparison",
            verbatim="orbit-averaged albedo, no eclipse transient",
            repo_path="src/orbital_thermal/harmonized_comparison.py",
            context_line=(
                "single Earth-facing view factor, orbit-averaged albedo, "
                "no eclipse transient,"
            ),
        ),
    ),
)

#: Default harmonized orbit / geometry. Tilt 90 deg = radiator edge-on to nadir
#: (in-plane with the arrays); F(550 km, 90 deg) = 0.258 ~ the paper's 0.25.
HARMONIZED_ALTITUDE_KM: float = 550.0
HARMONIZED_TILT_DEG: float = 90.0

#: Default beta-angle sweep (deg), dawn-dusk endpoint included.
DEFAULT_BETA_SWEEP: tuple = (0, 15, 30, 45, 60, 75, 90)

#: Default representative radiator temperatures (each design's published point).
AI1_RADIATOR_TEMPERATURE_K: float = AI1_DESIGN_POINT.radiator_temperature_K(
    AI1_DESIGN_POINT.sustained_load_W
)
STARCLOUD_RADIATOR_TEMPERATURE_K: float = STARCLOUD_2024_PUBLISHED.radiator_temperature_K


@dataclass(frozen=True)
class HarmonizedEnvironment:
    """Shared orbital environment at one beta angle (all fluxes per m^2)."""

    beta_deg: float
    altitude_km: float
    tilt_deg: float
    view_factor: float
    albedo_factor_mean: float
    earth_ir_flux_W_m2: float
    solar_constant_W_m2: float
    earth_albedo: float
    is_dawn_dusk_endpoint: bool
    albedo_model_limited: bool


def harmonized_environment(
    beta_deg: float,
    altitude_km: float = HARMONIZED_ALTITUDE_KM,
    tilt_deg: float = HARMONIZED_TILT_DEG,
    *,
    warn: bool = True,
) -> HarmonizedEnvironment:
    """Build the shared environment at ``beta_deg``.

    Emits a ``RuntimeWarning`` when the orbit-mean albedo factor collapses to ~0
    near the dawn-dusk endpoint (beta -> 90 deg): the package's subpoint albedo
    model nulls there, while the true disk-integrated albedo is nonzero.
    """
    if not (0.0 <= beta_deg <= 90.0):
        raise ValueError(f"beta_deg must be in [0, 90], got {beta_deg}")
    vf = env.sphere_view_factor(altitude_km, tilt_deg)
    alb_factor = sink.analytic_albedo_orbit_mean(beta_deg)
    is_endpoint = beta_deg >= 90.0 - 1e-9
    limited = alb_factor < 1e-6
    if warn and limited:
        warnings.warn(
            f"orbit-mean albedo factor is ~0 at beta={beta_deg:g} deg "
            "(subpoint-albedo model nulls near the dawn-dusk endpoint); the true "
            "disk-integrated albedo is nonzero there. Harmonized albedo is "
            "under-counted at high beta -- see published_starcloud_environment() "
            "for the paper's environmental load.",
            RuntimeWarning,
            stacklevel=2,
        )
    return HarmonizedEnvironment(
        beta_deg=beta_deg,
        altitude_km=altitude_km,
        tilt_deg=tilt_deg,
        view_factor=vf,
        albedo_factor_mean=alb_factor,
        earth_ir_flux_W_m2=sink.EARTH_IR_FLUX,
        solar_constant_W_m2=sink.SOLAR_CONSTANT,
        earth_albedo=sink.EARTH_ALBEDO,
        is_dawn_dusk_endpoint=is_endpoint,
        albedo_model_limited=limited,
    )


@dataclass(frozen=True)
class HarmonizedBalance:
    """Harmonized per-planform heat balance for one architecture at one beta.

    Two policies govern what is REPORTABLE:

    * **No-invention.** An unpublished short-wave absorptivity (AI1) leaves the
      albedo and any direct-solar term unresolved at EVERY beta -- including
      beta = 90 deg. ``net_excluding_albedo_W_m2`` (which needs only emissivity)
      stays available.
    * **Model-limitation precedence.** Where the absorptivity IS known, the raw
      sub-point-model albedo is still computed and exposed as
      ``earth_albedo_model_W_m2`` / ``net_rejection_model_W_m2`` (useful for
      figures), but it is NOT reportable as a validated load wherever the
      sub-point albedo model nulls (``albedo_model_limited``, e.g. beta -> 90).
      There, the reportable ``earth_albedo_absorbed_W_m2`` and
      ``net_rejection_W_m2`` are ``None`` -- a model-limited 0.0 is never
      published as a physical environmental load.
    """

    architecture: str
    beta_deg: float
    radiator_temperature_K: float
    emissivity: float
    solar_absorptivity: object           # float or NOT_PUBLISHED
    sunlit_faces: int
    emitted_W_m2: float
    direct_solar_absorbed_W_m2: object   # float or None (None if sunlit & unpublished alpha)
    earth_ir_absorbed_W_m2: float
    earth_albedo_absorbed_W_m2: object   # REPORTABLE: None if unpublished alpha OR model-limited
    earth_albedo_model_W_m2: object      # raw sub-point-model albedo (None iff unpublished alpha)
    albedo_model_limited: bool
    net_excluding_albedo_W_m2: object    # float or None (None if direct unresolved)
    net_rejection_W_m2: object           # REPORTABLE full net: None if albedo not reportable
    net_rejection_model_W_m2: object     # full net using the raw model albedo (for figures)
    notes: str


def harmonized_balance(
    architecture: str,
    emissivity: float,
    solar_absorptivity: object,
    sunlit_faces: int,
    radiator_temperature_K: float,
    environment: HarmonizedEnvironment,
    notes: str = "",
) -> HarmonizedBalance:
    """Evaluate the harmonized balance. ``solar_absorptivity`` may be NOT_PUBLISHED.

    Kirchhoff: the long-wave (Earth-IR) absorptivity is the emissivity, so the IR
    term and the emission never need the short-wave value. Only the reflected
    sunlight (albedo) and any direct-solar term do.
    """
    e = environment
    emitted = sr.emitted_flux(radiator_temperature_K, emissivity, SIGMA_SB, faces=2)
    earth_ir = emissivity * e.view_factor * e.earth_ir_flux_W_m2

    # Direct solar: zero if shielded, regardless of absorptivity; otherwise it
    # needs the (short-wave) solar absorptivity.
    if sunlit_faces == 0:
        direct = 0.0
    elif solar_absorptivity is NOT_PUBLISHED:
        direct = None
    else:
        direct = sr.solar_absorbed_flux(solar_absorptivity, e.solar_constant_W_m2, sunlit_faces)

    # Albedo (reflected sunlight). The no-invention policy comes FIRST: an
    # unpublished short-wave absorptivity leaves albedo unresolved at every beta,
    # including beta = 90 deg. Where the absorptivity is known we compute the raw
    # sub-point-model albedo (exposed for figures), but it is NOT reportable where
    # the model nulls (albedo_model_limited) -- a model artifact is never published
    # as a physical zero load.
    if solar_absorptivity is NOT_PUBLISHED:
        albedo_model = None
        albedo = None
    else:
        albedo_model = (
            sr.earth_albedo_absorbed_flux(
                solar_absorptivity, e.view_factor, e.earth_albedo, e.solar_constant_W_m2
            )
            * e.albedo_factor_mean
        )
        albedo = None if e.albedo_model_limited else albedo_model

    net_excl = None if direct is None else emitted - direct - earth_ir
    net_model = (
        None if (net_excl is None or albedo_model is None) else net_excl - albedo_model
    )
    net = None if (net_excl is None or albedo is None) else net_excl - albedo

    return HarmonizedBalance(
        architecture=architecture,
        beta_deg=e.beta_deg,
        radiator_temperature_K=radiator_temperature_K,
        emissivity=emissivity,
        solar_absorptivity=solar_absorptivity,
        sunlit_faces=sunlit_faces,
        emitted_W_m2=emitted,
        direct_solar_absorbed_W_m2=direct,
        earth_ir_absorbed_W_m2=earth_ir,
        earth_albedo_absorbed_W_m2=albedo,
        earth_albedo_model_W_m2=albedo_model,
        albedo_model_limited=e.albedo_model_limited,
        net_excluding_albedo_W_m2=net_excl,
        net_rejection_W_m2=net,
        net_rejection_model_W_m2=net_model,
        notes=notes,
    )


def starcloud_harmonized_balance(
    beta_deg: float,
    *,
    sunlit_faces: int = 0,
    radiator_temperature_K: float = STARCLOUD_RADIATOR_TEMPERATURE_K,
    altitude_km: float = HARMONIZED_ALTITUDE_KM,
    tilt_deg: float = HARMONIZED_TILT_DEG,
    warn: bool = True,
) -> HarmonizedBalance:
    """Starcloud under the harmonized environment.

    Uses the published emissivity (0.92) and short-wave absorptivity (0.09).
    ``sunlit_faces=0`` is the shielded/edge-on convention; ``sunlit_faces=1`` is
    Starcloud's architecture-specific one-side-sunlit case.
    """
    e = harmonized_environment(beta_deg, altitude_km, tilt_deg, warn=warn)
    note = "shielded/edge-on" if sunlit_faces == 0 else "Starcloud one-side sunlit (alpha_s=0.09)"
    return harmonized_balance(
        "starcloud",
        STARCLOUD_2024_PUBLISHED.emissivity_thermal,
        STARCLOUD_2024_PUBLISHED.absorptivity_solar,
        sunlit_faces,
        radiator_temperature_K,
        e,
        notes=note,
    )


def ai1_harmonized_balance(
    beta_deg: float,
    *,
    sunlit_faces: int = 0,
    solar_absorptivity: object = NOT_PUBLISHED,
    radiator_temperature_K: float = AI1_RADIATOR_TEMPERATURE_K,
    altitude_km: float = HARMONIZED_ALTITUDE_KM,
    tilt_deg: float = HARMONIZED_TILT_DEG,
    warn: bool = True,
) -> HarmonizedBalance:
    """AI1 under the harmonized environment.

    AI1 publishes no solar absorptivity, so ``solar_absorptivity`` defaults to
    ``NOT_PUBLISHED``: the albedo term (and any direct-solar term) is left
    uncomputed rather than invented, while ``net_excluding_albedo_W_m2`` stays
    available. Supplying a value is an explicit PARAMETRIC SENSITIVITY, not a
    ranked case; ``sunlit_faces=1`` is likewise sensitivity-only.
    """
    e = harmonized_environment(beta_deg, altitude_km, tilt_deg, warn=warn)
    if solar_absorptivity is NOT_PUBLISHED:
        note = "shielded/edge-on; alpha_s unpublished (albedo left uncomputed)"
    else:
        note = f"parametric sensitivity: assumed alpha_s={solar_absorptivity}"
    return harmonized_balance(
        "ai1",
        AI1_DESIGN_POINT.emissivity_thermal,
        solar_absorptivity,
        sunlit_faces,
        radiator_temperature_K,
        e,
        notes=note,
    )


def shielded_comparison(beta_deg: float, *, warn: bool = True) -> dict:
    """Harmonized shielded/edge-on comparison: ``sunlit_faces=0`` for BOTH.

    Returns ``{"ai1": HarmonizedBalance, "starcloud": HarmonizedBalance}``. AI1's
    short-wave absorptivity stays unpublished, so its albedo is ``None`` except at
    beta=90 (where the orbit-mean factor is 0 for both).
    """
    return {
        "ai1": ai1_harmonized_balance(beta_deg, sunlit_faces=0, warn=warn),
        "starcloud": starcloud_harmonized_balance(beta_deg, sunlit_faces=0, warn=False),
    }


def beta_sweep(
    architecture_balance,
    betas=DEFAULT_BETA_SWEEP,
    *,
    warn_at_endpoint: bool = True,
    **kwargs,
) -> list:
    """Evaluate ``architecture_balance`` across a beta sweep (default 0..90).

    ``architecture_balance`` is one of the wrappers above. The dawn-dusk endpoint
    (beta=90) is included; only that endpoint warns about the albedo null (so the
    sweep emits a single, intentional warning rather than one per point).
    """
    out = []
    for b in betas:
        endpoint = b >= 90.0 - 1e-9
        out.append(architecture_balance(b, warn=(warn_at_endpoint and endpoint), **kwargs))
    return out


@dataclass(frozen=True)
class PublishedEnvironmentLoad:
    """Starcloud's PUBLISHED environmental load, preserved so the harmonized
    beta-90 albedo null never erases it (separate albedo + Earth IR)."""

    earth_albedo_absorbed_W_m2: float
    earth_ir_absorbed_W_m2: float
    earth_combined_absorbed_W_m2: float
    basis: str


def published_starcloud_environment() -> PublishedEnvironmentLoad:
    """The white paper's published environmental load (albedo 9.22 + IR 5.24).

    Kept available next to the harmonized sweep as a reference, since the
    harmonized albedo collapses at the dawn-dusk endpoint by model limitation.
    """
    r = starcloud_published_balance()
    return PublishedEnvironmentLoad(
        earth_albedo_absorbed_W_m2=r.earth_albedo_absorbed_W_m2,
        earth_ir_absorbed_W_m2=r.earth_ir_absorbed_W_m2,
        earth_combined_absorbed_W_m2=r.earth_combined_absorbed_W_m2,
        basis="published (white paper p.9: F=0.25, alpha=0.09, single-band)",
    )
