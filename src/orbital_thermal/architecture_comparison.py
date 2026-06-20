"""As-published comparison of the AI1 and Starcloud 2024 radiator architectures.

Milestone A4. Places the two reference architectures side by side using EACH
ONE'S OWN PUBLISHED ASSUMPTIONS -- no harmonization (that is Milestone A5).

  * AI1 numbers come from the existing package implementation
    (:func:`orbital_thermal.equilibrium.equilibrium_temperature` and
    :func:`orbital_thermal.radiation.net_flux`) and the companion paper
    "The AI1 Design Point" (doi:10.5281/zenodo.20670771). The radiator
    temperature and fluxes are DERIVED from the published load/area/emissivity/
    sink, not transcribed.
  * Starcloud numbers come from the white-paper case in
    :mod:`orbital_thermal.reference_architectures`.

The two models use DIFFERENT conventions, and this module never hides that. AI1
lumps the orbital environment into one effective sink T_s^eff = 220 K and does
NOT separately publish a solar absorptivity, an Earth view factor, or a
direct-solar term; those fields are reported as "not separately published" and
are never invented. Starcloud states explicit absorbed-flux terms at a fixed
20 C radiator temperature.

Per the implementation brief, this comparison identifies a temperature-area
trade under public assumptions; it does NOT rank the architectures or claim
either is superior. A fair like-for-like ranking requires the harmonized model
(Milestone A5).
"""

from dataclasses import dataclass

from .equilibrium import equilibrium_temperature
from .radiation import net_flux
from .reference_architectures import (
    SIGMA_WHITEPAPER,
    STARCLOUD_2024_PUBLISHED,
    starcloud_published_balance,
)

#: Sentinel for a quantity the source does not separately publish. Used instead
#: of inventing a number (e.g. AI1's solar absorptivity, folded into its sink).
NOT_PUBLISHED = None


@dataclass(frozen=True)
class AI1DesignPoint:
    """Published AI1 design point (companion paper doi:10.5281/zenodo.20670771).

    Inputs below are the paper's published values (also the anchors in the
    package's verify suites). Radiator temperature and net flux are DERIVED
    through the package functions, so AI1's operating point is never hardcoded.

    AI1 models the orbital environment as a single effective sink
    ``effective_sink_K`` (T_s^eff = F^(1/4) T_s); it does not publish a separate
    solar absorptivity, Earth view factor, or direct-solar term.
    """

    name: str = "ai1_design_point"
    emissivity_thermal: float = 0.91
    effective_sink_K: float = 220.0
    planform_area_m2: float = 110.0
    emitting_area_m2: float = 220.0
    sustained_load_W: float = 120_000.0
    peak_load_W: float = 150_000.0
    coolant: str = "ammonia (screened)"
    radiator_sharing: str = "self-contained per-module"
    direct_solar_exposure: str = "edge-on / shielded (minimal direct solar)"
    architecture_type: str = "compact, higher-temperature, self-contained radiator"
    source: str = "The AI1 Design Point, doi:10.5281/zenodo.20670771"

    def radiator_temperature_K(self, load_W: float) -> float:
        """Equilibrium radiator temperature for ``load_W``, via the package."""
        return equilibrium_temperature(
            load_W, self.emitting_area_m2, self.emissivity_thermal, self.effective_sink_K
        )

    def net_flux_per_emitting_m2(self, load_W: float) -> float:
        """Net flux per emitting m^2, via the package's ``net_flux``.

        Equals ``load_W / emitting_area_m2`` by construction; computed through
        ``net_flux`` at the equilibrium temperature for traceability.
        """
        T = self.radiator_temperature_K(load_W)
        return net_flux(T, self.emissivity_thermal, self.effective_sink_K)

    def net_flux_per_planform_m2(self, load_W: float) -> float:
        """Net flux per planform m^2 (= 2x per-emitting, two-sided panel)."""
        return load_W / self.planform_area_m2


#: The canonical AI1 design point.
AI1_DESIGN_POINT = AI1DesignPoint()


@dataclass(frozen=True)
class ComparisonRow:
    """One attribute compared across the two architectures.

    ``ai1`` / ``starcloud`` may be ``NOT_PUBLISHED`` (None) when a source does
    not state the quantity. ``note`` records the convention so the two columns
    are never silently treated as like-for-like.
    """

    attribute: str
    ai1: object
    starcloud: object
    unit: str
    note: str


@dataclass(frozen=True)
class ArchitectureComparison:
    """An as-published comparison: each architecture under its own assumptions."""

    basis: str
    heat_load_W: float
    rows: tuple
    scope_note: str

    def row(self, attribute: str) -> ComparisonRow:
        """Return the row for ``attribute`` (KeyError if absent)."""
        for r in self.rows:
            if r.attribute == attribute:
                return r
        raise KeyError(attribute)

    def render_text(self) -> str:
        """Human-readable labelled table (for review and the A6 outputs)."""
        def fmt(v):
            if v is NOT_PUBLISHED:
                return "not separately published"
            if isinstance(v, float):
                return f"{v:.2f}"
            return str(v)

        header = (
            f"AS-PUBLISHED comparison (basis={self.basis}, "
            f"heat load = {self.heat_load_W/1e3:.0f} kW)\n"
            "Each architecture under its OWN published assumptions -- NOT "
            "harmonized, NOT a ranking.\n"
        )
        lines = [header, f"{'attribute':<34} {'AI1':<26} {'Starcloud':<26} unit"]
        lines.append("-" * 94)
        for r in self.rows:
            lines.append(
                f"{r.attribute:<34} {fmt(r.ai1):<26} {fmt(r.starcloud):<26} {r.unit}"
            )
        lines.append("")
        lines.append("Scope: " + self.scope_note)
        return "\n".join(lines)


#: Defensible comparison statement (implementation brief, section 5.3). States
#: the trade without ranking the architectures.
_SCOPE_NOTE = (
    "Starcloud's concept trades larger radiator area and deployable-structure "
    "scale for a cooler shared thermal network, while AI1 trades a higher "
    "operating temperature for more compact radiator area. Public information "
    "is insufficient to determine which architecture has lower total mass, "
    "lower parasitic power, or better lifecycle reliability."
)


def compare_as_published(
    load_W: float = 120_000.0,
    ai1: AI1DesignPoint = AI1_DESIGN_POINT,
    sigma: float = SIGMA_WHITEPAPER,
) -> ArchitectureComparison:
    """Build the as-published AI1-vs-Starcloud comparison at ``load_W``.

    Default load is AI1's 120 kW sustained primary point. Starcloud's planform
    area is derived from its published net flux to carry the SAME load, so the
    area rows are a like-load (not like-temperature) comparison; the temperature
    rows make the difference in operating point explicit.
    """
    sc = starcloud_published_balance(sigma=sigma)
    sc_planform = sc.required_planform_area_m2(load_W)
    sc_emitting = 2.0 * sc_planform
    scp = STARCLOUD_2024_PUBLISHED

    rows = (
        ComparisonRow(
            "radiator_temperature_K",
            ai1.radiator_temperature_K(load_W),
            sc.radiator_temperature_K,
            "K",
            "AI1 derived from load+area+sink; Starcloud is the fixed 20 C mean.",
        ),
        ComparisonRow(
            "heat_load",
            load_W,
            load_W,
            "W",
            "Same load for both (AI1 sustained primary; AI1 also runs 150 kW peak).",
        ),
        ComparisonRow(
            "planform_area",
            ai1.planform_area_m2,
            sc_planform,
            "m^2",
            "AI1 published design radiator; Starcloud derived from its W/m^2 for this load.",
        ),
        ComparisonRow(
            "emitting_area",
            ai1.emitting_area_m2,
            sc_emitting,
            "m^2",
            "Two-sided emitting area = 2x planform.",
        ),
        ComparisonRow(
            "net_rejection_per_planform",
            ai1.net_flux_per_planform_m2(load_W),
            sc.net_rejection_W_m2,
            "W/m^2",
            "AI1 at ~337 K vs Starcloud at 293 K -- different temperatures, NOT a ranking.",
        ),
        ComparisonRow(
            "net_rejection_per_emitting",
            ai1.net_flux_per_emitting_m2(load_W),
            sc.net_rejection_W_m2 / 2.0,
            "W/m^2",
            "Per emitting face.",
        ),
        ComparisonRow(
            "thermal_emissivity",
            ai1.emissivity_thermal,
            scp.emissivity_thermal,
            "-",
            "Independent published values.",
        ),
        ComparisonRow(
            "solar_absorptivity",
            NOT_PUBLISHED,
            scp.absorptivity_solar,
            "-",
            "AI1 folds optical/environment terms into its effective sink.",
        ),
        ComparisonRow(
            "earth_view_factor",
            NOT_PUBLISHED,
            scp.earth_view_factor,
            "-",
            "AI1 uses a lumped effective sink T_s^eff = 220 K instead of an explicit F.",
        ),
        ComparisonRow(
            "environment_treatment",
            "lumped effective sink T_s^eff = 220 K",
            "explicit solar + albedo + Earth-IR terms",
            "-",
            "The core modelling-convention difference.",
        ),
        ComparisonRow(
            "direct_solar_exposure",
            ai1.direct_solar_exposure,
            "one side in direct sunlight",
            "-",
            "AI1 assumes edge-on/shielded; Starcloud places the radiator in-line with arrays.",
        ),
        ComparisonRow(
            "architecture_type",
            ai1.architecture_type,
            "larger-area, lower-temperature, shared modular radiator",
            "-",
            "Qualitative characterisation, not a metric.",
        ),
        ComparisonRow(
            "radiator_sharing",
            ai1.radiator_sharing,
            "shared radiator infrastructure",
            "-",
            "Self-contained per module vs shared across modules.",
        ),
        ComparisonRow(
            "coolant",
            ai1.coolant,
            "not specified (two-phase where practical)",
            "-",
            "AI1 screens ammonia; Starcloud does not disclose a coolant identity.",
        ),
    )
    return ArchitectureComparison(
        basis="as_published",
        heat_load_W=load_W,
        rows=rows,
        scope_note=_SCOPE_NOTE,
    )
