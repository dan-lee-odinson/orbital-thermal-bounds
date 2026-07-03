"""B1 correlation registry: thermal (Nusselt, spreading, contact) and hydraulic
(friction, minor losses, maldistribution) correlations.

Each entry carries a source and a validity domain. Simple closed forms have an
executable ``evaluate`` callable now; correlations whose executable form belongs
in B2/B3 are registered with the source/domain fixed and ``evaluate=None``.
Correlations with no single authoritative form are blocked (no invention).

The ``evaluate`` callables are pure functions of dimensionless groups; callers in
B3 must first check the validity domain (see ``assert_in_domain``). Ranked cases
may not use a correlation outside its domain (B0 plan Sections 4.8, 6).
"""

from __future__ import annotations

import math

from .provenance import (
    CorrelationEntry,
    Domain,
    Provenance,
    Source,
    Status,
)

_INCROPERA = Source(
    citation="Incropera & DeWitt, Fundamentals of Heat and Mass Transfer (7th ed.)",
)
_WHITE = Source(citation="White, Fluid Mechanics (friction-factor correlations)")
_CRANE = Source(citation="Crane Technical Paper TP-410 (minor-loss K-factors)")
_SPREADING = Source(
    citation="Lee, Song, Au, Moran; Yovanovich constriction/spreading-resistance model",
    locator="Song et al., IEEE CPMT 1994; Lee et al. 1995",
)


# --- executable closed forms ----------------------------------------------------


def friction_laminar(Re: float) -> float:
    """Fully-developed laminar Darcy friction factor in a circular tube: 64/Re."""
    return 64.0 / Re


def friction_blasius(Re: float) -> float:
    """Blasius smooth-tube turbulent Darcy friction factor: 0.316 * Re^-0.25."""
    return 0.316 * Re**-0.25


def friction_haaland(Re: float, rel_roughness: float = 0.0) -> float:
    """Haaland explicit approximation to Colebrook (Darcy friction factor)."""
    inv_sqrt = -1.8 * math.log10((rel_roughness / 3.7) ** 1.11 + 6.9 / Re)
    return 1.0 / inv_sqrt**2


def nusselt_dittus_boelter(Re: float, Pr: float, heating: bool = True) -> float:
    """Dittus-Boelter turbulent Nusselt number, Nu = 0.023 Re^0.8 Pr^n."""
    n = 0.4 if heating else 0.3
    return 0.023 * Re**0.8 * Pr**n


def nusselt_gnielinski(Re: float, Pr: float) -> float:
    """Gnielinski turbulent Nusselt number (smooth tube)."""
    f = (0.790 * math.log(Re) - 1.64) ** -2
    num = (f / 8.0) * (Re - 1000.0) * Pr
    den = 1.0 + 12.7 * math.sqrt(f / 8.0) * (Pr ** (2 / 3) - 1.0)
    return num / den


# --- registry entries -----------------------------------------------------------

CORRELATIONS: list[CorrelationEntry] = [
    # Hydraulic: friction
    CorrelationEntry(
        id="friction.laminar",
        name="Laminar Darcy friction factor",
        kind="friction",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="f = 64 / Re",
        domain=Domain(ranges={"Re": (1.0, 2300.0)}),
        source=_WHITE,
        evaluate=friction_laminar,
        applicability="fully-developed laminar flow in a circular tube",
    ),
    CorrelationEntry(
        id="friction.blasius",
        name="Blasius turbulent friction factor",
        kind="friction",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="f = 0.316 * Re^-0.25",
        domain=Domain(ranges={"Re": (4000.0, 1.0e5)}),
        source=_WHITE,
        evaluate=friction_blasius,
        applicability="smooth tube, 4e3 <= Re <= 1e5",
    ),
    CorrelationEntry(
        id="friction.haaland",
        name="Haaland friction factor (Colebrook approx.)",
        kind="friction",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="1/sqrt(f) = -1.8 log10((eps/D/3.7)^1.11 + 6.9/Re)",
        domain=Domain(ranges={"Re": (4000.0, 1.0e8)}),
        source=_WHITE,
        evaluate=friction_haaland,
        applicability="turbulent; accepts relative roughness eps/D (default smooth)",
    ),
    # Thermal: Nusselt
    CorrelationEntry(
        id="nusselt.laminar_const_q",
        name="Laminar Nusselt, constant heat flux",
        kind="nusselt",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="Nu = 4.36",
        domain=Domain(ranges={"Re": (1.0, 2300.0)}),
        source=_INCROPERA,
        evaluate=lambda Re=None, Pr=None: 4.36,
        applicability="fully-developed laminar, uniform wall heat flux",
    ),
    CorrelationEntry(
        id="nusselt.laminar_const_Ts",
        name="Laminar Nusselt, constant wall temperature",
        kind="nusselt",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="Nu = 3.66",
        domain=Domain(ranges={"Re": (1.0, 2300.0)}),
        source=_INCROPERA,
        evaluate=lambda Re=None, Pr=None: 3.66,
        applicability="fully-developed laminar, uniform wall temperature",
    ),
    CorrelationEntry(
        id="nusselt.dittus_boelter",
        name="Dittus-Boelter turbulent Nusselt",
        kind="nusselt",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="Nu = 0.023 Re^0.8 Pr^n  (n=0.4 heating, 0.3 cooling)",
        domain=Domain(ranges={"Re": (1.0e4, 1.2e5), "Pr": (0.6, 160.0)}),
        source=_INCROPERA,
        evaluate=nusselt_dittus_boelter,
        applicability="fully-developed turbulent, L/D >= 10",
    ),
    CorrelationEntry(
        id="nusselt.gnielinski",
        name="Gnielinski turbulent Nusselt",
        kind="nusselt",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="Nu = (f/8)(Re-1000)Pr / (1 + 12.7 sqrt(f/8)(Pr^(2/3)-1))",
        domain=Domain(ranges={"Re": (3000.0, 5.0e6), "Pr": (0.5, 2000.0)}),
        source=_INCROPERA,
        evaluate=nusselt_gnielinski,
        applicability="transitional/turbulent smooth tube; wider Re/Pr than Dittus-Boelter",
    ),
    CorrelationEntry(
        id="nusselt.developing_entry_length",
        name="Developing (entry-length) Nusselt correction",
        kind="nusselt",
        provenance=Provenance.ASSUMED,
        status=Status.FUTURE,
        formula="(entry-length correlation to be selected in B3)",
        source=_INCROPERA,
        applicability="short-tube/thermal-entry correction; correlation choice deferred to B3",
        note="FUTURE: not rank-eligible until a specific correlation is selected",
    ),
    # Thermal: spreading and contact resistance
    CorrelationEntry(
        id="thermal.spreading_resistance",
        name="Spreading (constriction) resistance model",
        kind="spreading",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="dimensionless constriction/spreading-resistance closed form (Yovanovich)",
        source=_SPREADING,
        evaluate=None,  # executable form implemented in B2
        applicability="mandatory for ranked chip-to-cold-plate cases unless 1-D proven "
        "(B0 4.1a/B2); executable form lands in B2",
    ),
    CorrelationEntry(
        id="thermal.contact_resistance",
        name="Thermal contact resistance",
        kind="contact",
        provenance=Provenance.SENSITIVITY,
        status=Status.SOURCE_REQUIRED,
        formula="interface-specific (materials, pressure, interstitial, surface finish)",
        applicability="no universal value; a specific cited interface is required per case",
        note="NOT rank-eligible until a specific interface is cited",
    ),
    # Hydraulic: minor losses and maldistribution
    CorrelationEntry(
        id="hydraulic.minor_losses",
        name="Minor-loss K-factor method",
        kind="minor_loss",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="dP_minor = sum(K_i) * rho V^2 / 2",
        source=_CRANE,
        evaluate=None,
        applicability="K-factors from the cited table; the per-case fitting inventory is a "
        "B3 design variable",
    ),
    CorrelationEntry(
        id="hydraulic.maldistribution_allowance",
        name="Parallel-channel maldistribution allowance",
        kind="maldistribution",
        provenance=Provenance.ASSUMED,
        status=Status.FUTURE,
        formula="(allowance model / sensitivity to be defined in B3)",
        applicability="parallel cold-plate/manifold flow maldistribution",
        note="FUTURE: not rank-eligible until an allowance model or sensitivity bound is set",
    ),
]

CORRELATIONS_BY_ID: dict[str, CorrelationEntry] = {c.id: c for c in CORRELATIONS}
