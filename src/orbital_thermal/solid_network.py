"""B2: reduced-order solid thermal network (junction -> cold-plate).

The chip-side conduction path of the B0 plan's coupled model (Section 4.1a, residual
R1): a series of solid resistances -- 1-D conduction, spreading (Yovanovich / Lee et
al. isothermal-base, Biot-optional), and contact resistance -- carrying the **chip
heat only** (pump heat enters the fluid downstream, per the B0 heat-injection rule).
This module computes those resistances and the junction temperature above the
cold-plate base.

Registry-governed rank-eligibility (B1): conductivity is pulled from
:mod:`orbital_thermal.registry`. A *ranked* case may not use a blocked material
(APG/diamond conductivity is ``source_required``) or an **uncited** contact
resistance, and must include a spreading resistance unless 1-D conduction is
explicitly justified. This module is **isotropic-only**; anisotropic / direction-aware
handling is deferred to a later milestone.

Units: SI -- metres, watts, kelvin, W/m/K, W/m^2/K. Resistances are K/W.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import registry
from ._validate import in_range, positive

# --- individual resistances (pure physics) --------------------------------------


def conduction_resistance(length_m: float, area_m2: float, k_W_mK: float) -> float:
    """1-D conduction resistance ``R = L / (k A)`` [K/W]."""
    positive("length_m", length_m)
    positive("area_m2", area_m2)
    positive("k_W_mK", k_W_mK)
    return length_m / (k_W_mK * area_m2)


def spreading_resistance(
    source_radius_m: float,
    plate_radius_m: float,
    thickness_m: float,
    k_W_mK: float,
    base_htc_W_m2K: float | None = None,
) -> float:
    """Circular-source-on-disk spreading resistance [K/W] (Lee, Song, Au, Moran 1995).

    Isothermal base by default (``base_htc_W_m2K=None`` => Bi -> infinity); pass a
    finite base heat-transfer coefficient for a convective base. Requires a circular
    source of radius ``a`` on a coaxial disk of radius ``b`` (with ``a < b``) and
    thickness ``t``::

        eps = a/b,  tau = t/b,  lam = pi + 1/(sqrt(pi) eps)
        phi = (tanh(lam tau) + lam/Bi) / (1 + (lam/Bi) tanh(lam tau))
        psi = 0.5 (1 - eps)^{3/2} phi,  R = psi / (sqrt(pi) k a)
        (phi = tanh(lam tau) in the isothermal-base limit, Bi -> infinity)

    In the point-source, thick, isothermal-base limit R -> ~0.282/(k a), consistent
    with the isoflux half-space constriction value 8/(3 pi^2 k a) ~ 0.270/(k a).
    """
    positive("source_radius_m", source_radius_m)
    positive("plate_radius_m", plate_radius_m)
    positive("thickness_m", thickness_m)
    positive("k_W_mK", k_W_mK)
    eps = source_radius_m / plate_radius_m
    in_range("epsilon (a/b)", eps, 1e-6, 0.999999)  # source strictly smaller than plate
    tau = thickness_m / plate_radius_m
    lam = math.pi + 1.0 / (math.sqrt(math.pi) * eps)
    th = math.tanh(lam * tau)
    if base_htc_W_m2K is None:
        phi = th  # isothermal base (Bi -> infinity)
    else:
        positive("base_htc_W_m2K", base_htc_W_m2K)
        bi = base_htc_W_m2K * plate_radius_m / k_W_mK
        phi = (th + lam / bi) / (1.0 + (lam / bi) * th)
    psi = 0.5 * (1.0 - eps) ** 1.5 * phi
    return psi / (math.sqrt(math.pi) * k_W_mK * source_radius_m)


def contact_resistance(conductance_W_m2K: float, area_m2: float) -> float:
    """Contact resistance ``R = 1 / (h_c A)`` [K/W] from a contact conductance ``h_c``."""
    positive("conductance_W_m2K", conductance_W_m2K)
    positive("area_m2", area_m2)
    return 1.0 / (conductance_W_m2K * area_m2)


# --- series network -------------------------------------------------------------


@dataclass(frozen=True)
class Resistor:
    """One element of the solid path, with its rank-eligibility and provenance note."""

    name: str
    kind: str  # "conduction" | "spreading" | "contact"
    value_K_per_W: float
    rank_eligible: bool
    note: str = ""


@dataclass(frozen=True)
class SolidPath:
    """A junction-to-cold-plate series solid path. Carries the chip heat only."""

    resistors: tuple[Resistor, ...]
    one_d_justified: bool = False
    one_d_justification: str = ""

    @property
    def total_K_per_W(self) -> float:
        return math.fsum(r.value_K_per_W for r in self.resistors)

    @property
    def has_spreading(self) -> bool:
        return any(r.kind == "spreading" for r in self.resistors)

    @property
    def rank_eligible(self) -> bool:
        # every resistor must be rank-eligible, AND a spreading resistance must be
        # present unless 1-D conduction is explicitly justified (B0 plan B2).
        if not all(r.rank_eligible for r in self.resistors):
            return False
        return self.has_spreading or self.one_d_justified

    def junction_temperature(self, base_temp_K: float, q_chip_W: float) -> float:
        """``T_j = T_base + Q_chip * R_total`` (chip heat only; B0 4.1a rule)."""
        positive("base_temp_K", base_temp_K)
        positive("q_chip_W", q_chip_W)
        return base_temp_K + q_chip_W * self.total_K_per_W


# --- registry-aware builders (enforce rank-eligibility) -------------------------


def _registry_conductivity(material: str, *, ranked: bool) -> float:
    entry_id = f"solid.{material}.thermal_conductivity"
    try:
        entry = registry.get(entry_id)
    except KeyError as exc:
        # e.g. APG exposes only directional (in_plane/through_plane) entries -> anisotropic,
        # which is deferred in B2 (isotropic-only).
        raise registry.NotRankEligibleError(
            f"no isotropic conductivity entry '{entry_id}' in the registry; '{material}' is "
            "anisotropic or unregistered. B2 is isotropic-only; anisotropic handling is deferred."
        ) from exc
    if ranked:
        registry.assert_rank_eligible(entry, context="B2 solid conduction")
    if entry.value is None:
        raise registry.NotRankEligibleError(
            f"material '{material}' has no registry conductivity value (status="
            f"{entry.status.value}); supply a cited parametric k and run as a sensitivity "
            "(anisotropic handling is deferred)."
        )
    return float(entry.value)


def build_ranked_path(
    *,
    material: str,
    length_m: float,
    area_m2: float,
    source_radius_m: float,
    plate_radius_m: float,
    thickness_m: float,
    contact_conductance_W_m2K: float,
    contact_source: str,
    base_htc_W_m2K: float | None = None,
) -> SolidPath:
    """Assemble a **rank-eligible** junction->cold-plate solid path.

    Conductivity comes from the registry and must be rank-eligible (isotropic Al/Cu);
    a blocked material (APG/diamond) raises ``NotRankEligibleError``. Contact resistance
    is ``source_required`` in the registry, so a ranked case must pass a non-empty
    ``contact_source`` citation, else it raises. Spreading is always included.
    """
    k = _registry_conductivity(material, ranked=True)
    if not str(contact_source).strip():
        raise registry.NotRankEligibleError(
            "contact resistance is source_required (B1 registry): a ranked case must cite a "
            "specific interface source; got none. Run the case as a sensitivity instead."
        )
    r_cond = conduction_resistance(length_m, area_m2, k)
    r_spread = spreading_resistance(source_radius_m, plate_radius_m, thickness_m, k, base_htc_W_m2K)
    r_contact = contact_resistance(contact_conductance_W_m2K, area_m2)
    note_k = f"registry solid.{material}"
    return SolidPath(
        resistors=(
            Resistor("conduction", "conduction", r_cond, True, note_k),
            Resistor("spreading", "spreading", r_spread, True, "Yovanovich isothermal-base"),
            Resistor("contact", "contact", r_contact, True, f"cited: {contact_source}"),
        )
    )


def build_sensitivity_path(
    *,
    k_W_mK: float,
    length_m: float,
    area_m2: float,
    source_radius_m: float,
    plate_radius_m: float,
    thickness_m: float,
    contact_conductance_W_m2K: float | None = None,
    base_htc_W_m2K: float | None = None,
    note: str = "parametric",
) -> SolidPath:
    """Assemble a **parametric / sensitivity** path from explicit values (e.g. an
    anisotropic material bound or an uncited contact). Never rank-eligible."""
    r_cond = conduction_resistance(length_m, area_m2, k_W_mK)
    r_spread = spreading_resistance(
        source_radius_m, plate_radius_m, thickness_m, k_W_mK, base_htc_W_m2K
    )
    resistors = [
        Resistor("conduction", "conduction", r_cond, False, note),
        Resistor("spreading", "spreading", r_spread, False, note),
    ]
    if contact_conductance_W_m2K is not None:
        r_contact = contact_resistance(contact_conductance_W_m2K, area_m2)
        resistors.append(Resistor("contact", "contact", r_contact, False, note))
    return SolidPath(resistors=tuple(resistors))
