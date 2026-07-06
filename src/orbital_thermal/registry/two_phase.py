"""S1 two-phase property/correlation registry: boiling/condensing heat-transfer
coefficient (HTC), two-phase pressure drop (dP), critical heat flux (CHF), onset
of nucleate boiling (ONB), and pump-inlet (NPSH) entries, plus the saturation
property-backend evaluation entries for the two-phase coolants.

This milestone is **registry-only**: every entry carries provenance, a resolution
status, a source, and (where known) a validity domain -- but **no correlation
math/physics is implemented here**. All ``evaluate`` callables are ``None``; the
executable forms are deferred to S2/S3. This mirrors the B1 pattern of registering
a correlation on its source/domain before wiring in the executable form.

Two extra invariants specific to two-phase work are recorded as machine-visible
metadata (never invented):

* **Gravity basis.** Every HTC/dP/CHF entry is tagged as a *1g reference correlation*
  (``microgravity_validated=False``, ``gravity_basis="1g"``): ISS/microgravity
  literature shows gravity-dependent HTC/CHF behavior, so rankings built on these
  correlations are explicitly **not** microgravity-validated.
* **Backend pin.** Saturation properties come from CoolProp's HEOS backend pinned to
  7.2.0 (ammonia EOS Gao et al. JPCRD 2020; water IAPWS-95 Wagner & Pruss 2002).

This module is stdlib-only and imports without CoolProp or numpy.
"""

from __future__ import annotations

from dataclasses import dataclass

from .provenance import (
    CorrelationEntry,
    Domain,
    PropertyEntry,
    PropertyKind,
    Provenance,
    Source,
    Status,
)

# --- Backend pin ----------------------------------------------------------------


@dataclass(frozen=True)
class BackendPin:
    """A pinned property-backend version, with the known-latest version and the
    migration gate that must be cleared before the pin is advanced.

    Registry-only: this records *which* backend/version the saturation properties
    are pinned to. Advancing the pin is a deliberate, verified step (property-drift
    check), never an implicit upgrade.
    """

    backend: str
    pinned_version: str
    latest_known_version: str = ""
    migration_requires: str = ""


#: Pinned saturation-property backend for the two-phase coolants. 8.0.0 is known but
#: not adopted: advancing the pin requires a property-drift re-verification first.
COOLPROP_PIN = BackendPin(
    backend="CoolProp HEOS",
    pinned_version="7.2.0",
    latest_known_version="8.0.0",
    migration_requires=(
        "property-drift check: re-verify saturation properties (T_sat, h_fg, rho_v, "
        "sigma) against the pinned reference before advancing the pin; 8.0.0 adds "
        "mass-basis vapor quality (Qmass) + new tabular backend."
    ),
)


# --- Gravity-basis metadata (applied to every HTC/dP/CHF entry) -----------------

#: Microgravity/gravity-basis tag applied (via ``**_MICROGRAVITY_1G``) to EVERY
#: HTC/dP/CHF correlation. The correlations are 1g-derived reference forms; rankings
#: built on them are reference-only and NOT microgravity-validated.
_MICROGRAVITY_1G = dict(
    microgravity_validated=False,
    gravity_basis="1g",
    rank_scope="reference_correlation_only",
    limitation=(
        "ISS/microgravity literature shows gravity-dependent HTC/CHF behavior; "
        "rankings are not microgravity-validated."
    ),
)


# --- Chisholm separated-flow parameter (pinned rule, no physics evaluated) -------

#: Pinned Chisholm ``C`` for the Lockhart-Martinelli two-phase multiplier, keyed by
#: ``(liquid_regime, gas_regime)``. Recorded as data only; the multiplier itself is
#: NOT evaluated in S1 (deferred to S2/S3).
CHISHOLM_C: dict[tuple[str, str], float] = {
    ("turbulent", "turbulent"): 20.0,
    ("laminar", "turbulent"): 12.0,
    ("turbulent", "laminar"): 10.0,
    ("laminar", "laminar"): 5.0,
}

#: Regime thresholds used to select the Chisholm ``C`` key (data only, not evaluated).
CHISHOLM_RE_LAMINAR_MAX = 1000.0
CHISHOLM_RE_TURBULENT_MIN = 2000.0


# --- Sources --------------------------------------------------------------------
# CITATIONS: no fabricated DOIs. Author(s) (year), Journal strings only; DOIs/volume/
# pages are omitted where not confidently known (locator left blank -> confirm later).

_GUNGOR_WINTERTON = Source(
    citation="Gungor & Winterton (1986), Int. J. Heat Mass Transfer",
)
_CHEN = Source(
    citation="Chen (1966), Ind. Eng. Chem. Process Design and Development",
)
_SHAH_2022 = Source(
    citation="Shah (2022), a general correlation for saturated-boiling heat transfer "
    "in channels (updated formulation)",
)
_BERGLES_ROHSENOW = Source(
    citation="Bergles & Rohsenow (1964), J. Heat Transfer (onset of nucleate boiling)",
)
_LOCKHART_MARTINELLI = Source(
    citation="Lockhart & Martinelli (1949), Chem. Eng. Progress; Chisholm (1967), "
    "Int. J. Heat Mass Transfer",
)
_FRIEDEL = Source(
    citation="Friedel (1979), European Two-Phase Flow Group Meeting (Paper E2)",
)
_MULLER_STEINHAGEN_HECK = Source(
    citation="Muller-Steinhagen & Heck (1986), Chemical Engineering and Processing",
)
_SHAH_2015 = Source(
    citation="Shah (2015), a general correlation for critical heat flux in "
    "saturated-flow boiling",
)
_SHAH_1987 = Source(
    citation="Shah (1987), Int. J. Heat and Fluid Flow (critical heat flux, historical)",
)
_KATTO_OHNO = Source(
    citation="Katto & Ohno (1984), Int. J. Heat Mass Transfer (generalized CHF)",
)
_NPSH = Source(
    citation="Hydraulic Institute / pump-cavitation NPSH practice (NPSH_avail vs NPSH_req)",
)

# Saturation-backend sources (NIST via CoolProp HEOS; per-fluid reference EOS cited).
_NIST_AMMONIA = Source(
    citation="NIST REFPROP/CoolProp HEOS ammonia EOS (Gao et al. JPCRD 2020)",
)
_NIST_WATER = Source(
    citation="NIST/IAPWS-95 water EOS via CoolProp HEOS (Wagner & Pruss 2002, JPCRD)",
)


# --- Two-phase correlation registry (registry-only; evaluate=None everywhere) ----

TWO_PHASE_CORRELATIONS: list[CorrelationEntry] = [
    # ---------------- Heat-transfer coefficient (HTC) ----------------
    CorrelationEntry(
        id="two_phase.htc.gungor_winterton",
        name="Gungor & Winterton saturated flow-boiling HTC",
        kind="htc",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="(reference flow-boiling HTC correlation; executable form deferred to S2)",
        domain=Domain(
            ranges={
                "G_kg_m2s": (10.0, 600.0),
                "q_flux_W_m2": (2000.0, 240000.0),
                "quality": (0.002, 0.997),
                "P_Pa": (0.19e6, 1.6e6),
                "D_m": (1.224e-3, 32e-3),
            }
        ),
        source=_GUNGOR_WINTERTON,
        evaluate=None,
        applicability="rank-eligible reference flow-boiling HTC; formula deferred to S2",
        note="reference HTC correlation for two-phase ranking; 1g basis (see limitation)",
        **_MICROGRAVITY_1G,
    ),
    CorrelationEntry(
        id="two_phase.htc.chen",
        name="Chen flow-boiling HTC (superposition)",
        kind="htc",
        provenance=Provenance.SENSITIVITY,
        status=Status.SENSITIVITY,
        formula="(superposition nucleate+convective HTC; sensitivity only)",
        source=_CHEN,
        evaluate=None,
        applicability="sensitivity comparison against the reference HTC; NOT rank-eligible",
        note="SENSITIVITY: alternative HTC for spread, not a ranked value",
        **_MICROGRAVITY_1G,
    ),
    CorrelationEntry(
        id="two_phase.htc.shah_2022",
        name="Shah (2022) flow-boiling HTC (current-literature update)",
        kind="htc",
        provenance=Provenance.SENSITIVITY,
        status=Status.SENSITIVITY,
        formula="(updated general saturated-boiling HTC; sensitivity only)",
        source=_SHAH_2022,
        evaluate=None,
        applicability="current-literature sensitivity against the reference HTC; NOT rank-eligible",
        note="SENSITIVITY: current-literature HTC for spread, not a ranked value",
        **_MICROGRAVITY_1G,
    ),
    # ---------------- Onset of nucleate boiling (ONB) ----------------
    CorrelationEntry(
        id="two_phase.onb.bergles_rohsenow",
        name="Bergles & Rohsenow onset of nucleate boiling",
        kind="onb",
        provenance=Provenance.PUBLISHED,
        status=Status.SOURCE_REQUIRED,
        formula="(ONB incipience criterion; applicability/range guards required)",
        source=_BERGLES_ROHSENOW,
        evaluate=None,
        applicability="applicability/range guards required; ammonia/regime applicability "
        "source-gated",
        note="applicability/range guards required; ammonia/regime applicability "
        "source-gated => ONB-dependent cases sensitivity/source-gated, not rank-eligible",
        **_MICROGRAVITY_1G,
    ),
    # ---------------- Two-phase pressure drop (dP) ----------------
    CorrelationEntry(
        id="two_phase.dp.lockhart_martinelli_chisholm",
        name="Lockhart-Martinelli two-phase dP with Chisholm C",
        kind="dp",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="phi^2 separated-flow multiplier with Chisholm C (see CHISHOLM_C); "
        "executable form deferred to S2",
        domain=Domain(ranges={"P_Pa": (0.1e6, 2.0e6)}),  # low/moderate pressure
        source=_LOCKHART_MARTINELLI,
        evaluate=None,
        applicability="rank-eligible reference two-phase dP at low/moderate P; uses the "
        "pinned CHISHOLM_C regime rule; formula deferred to S2",
        note="reference dP; pinned Chisholm C = CHISHOLM_C keyed by (liquid_regime, gas_regime)",
        **_MICROGRAVITY_1G,
    ),
    CorrelationEntry(
        id="two_phase.dp.friedel",
        name="Friedel two-phase pressure-drop multiplier",
        kind="dp",
        provenance=Provenance.SENSITIVITY,
        status=Status.SENSITIVITY,
        formula="(Friedel two-phase friction multiplier; sensitivity only)",
        source=_FRIEDEL,
        evaluate=None,
        applicability="sensitivity comparison against the reference dP; NOT rank-eligible",
        note="SENSITIVITY: alternative dP for spread, not a ranked value",
        **_MICROGRAVITY_1G,
    ),
    CorrelationEntry(
        id="two_phase.dp.muller_steinhagen_heck",
        name="Muller-Steinhagen & Heck two-phase pressure drop",
        kind="dp",
        provenance=Provenance.SENSITIVITY,
        status=Status.SENSITIVITY,
        formula="(Muller-Steinhagen-Heck two-phase dP; sensitivity only)",
        source=_MULLER_STEINHAGEN_HECK,
        evaluate=None,
        applicability="sensitivity comparison against the reference dP; NOT rank-eligible",
        note="SENSITIVITY: alternative dP for spread, not a ranked value",
        **_MICROGRAVITY_1G,
    ),
    # ---------------- Critical heat flux (CHF) ----------------
    CorrelationEntry(
        id="two_phase.chf.shah_2015",
        name="Shah (2015) saturated-flow-boiling CHF",
        kind="chf",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="(general saturated-flow-boiling CHF; executable form deferred to S2)",
        # Shah's general CHF correlation is stated over a wide reduced-pressure band;
        # a rank-eligible reference must declare a validity domain (see missing_metadata).
        domain=Domain(ranges={"pr_reduced": (0.0014, 0.96)}),
        source=_SHAH_2015,
        evaluate=None,
        applicability="rank-eligible reference CHF; local modeled wall-flux basis; feeds "
        "the q''/CHF <= 0.5 design band; formula deferred to S2",
        note="reference CHF: local modeled wall-flux basis; feeds q''/CHF<=0.5 band",
        **_MICROGRAVITY_1G,
    ),
    CorrelationEntry(
        id="two_phase.chf.shah_1987",
        name="Shah (1987) CHF (historical ancestor)",
        kind="chf",
        provenance=Provenance.SENSITIVITY,
        status=Status.SENSITIVITY,
        formula="(historical Shah CHF; sensitivity only)",
        source=_SHAH_1987,
        evaluate=None,
        applicability="historical-ancestor CHF sensitivity; NOT rank-eligible",
        note="SENSITIVITY: historical ancestor of the reference CHF, not a ranked value",
        **_MICROGRAVITY_1G,
    ),
    CorrelationEntry(
        id="two_phase.chf.katto_ohno",
        name="Katto & Ohno generalized CHF",
        kind="chf",
        provenance=Provenance.SENSITIVITY,
        status=Status.SENSITIVITY,
        formula="(Katto-Ohno generalized CHF; sensitivity only)",
        source=_KATTO_OHNO,
        evaluate=None,
        applicability="sensitivity comparison against the reference CHF; NOT rank-eligible",
        note="SENSITIVITY: alternative CHF for spread, not a ranked value",
        **_MICROGRAVITY_1G,
    ),
    # ---------------- Pump inlet (NPSH) ----------------
    CorrelationEntry(
        id="two_phase.pump.npsh",
        name="Pump-inlet NPSH margin (cavitation feasibility)",
        kind="npsh",
        provenance=Provenance.ASSUMED,
        status=Status.SOURCE_REQUIRED,
        formula="NPSH_avail > NPSH_req + margin",
        source=_NPSH,
        evaluate=None,
        applicability="pump-class NPSH_req source-gated; NOT rank-eligible until sourced",
        note="NPSH_avail>NPSH_req+margin; pump-class NPSH_req source-gated; if unsourced, "
        "idealized pump-inlet boundary (cavitation feasibility not modeled)",
    ),
]


# --- Saturation property-backend evaluation entries (per two-phase fluid) --------
# Registry-only: name the backend + required inputs + validity domain; the actual
# per-(T,P)/quality saturation call happens in S2/S3 via orbital_thermal.fluids.

_SAT_APPLICABILITY = (
    "per-(T,P)/quality saturation properties (T_sat, h_fg, rho_v, sigma) via "
    "orbital_thermal.fluids (S2/S3); formulas NOT in S1"
)

TWO_PHASE_PROPERTIES: list[PropertyEntry] = [
    PropertyEntry(
        id="coolant.ammonia.saturation_backend",
        name="Ammonia saturation property evaluation",
        material="ammonia",
        quantity="saturation_properties(T,P,quality)",
        provenance=Provenance.DERIVED,
        status=Status.RESOLVED,
        kind=PropertyKind.BACKEND_EVALUATION,
        value=None,
        units="SI",
        domain=Domain(ranges={"T_K": (195.5, 405.4)}),  # triple -> critical (ammonia)
        source=_NIST_AMMONIA,
        backend="CoolProp HEOS",
        version="7.2.0",
        applicability=_SAT_APPLICABILITY,
    ),
    PropertyEntry(
        id="coolant.water.saturation_backend",
        name="Water saturation property evaluation",
        material="water",
        quantity="saturation_properties(T,P,quality)",
        provenance=Provenance.DERIVED,
        status=Status.RESOLVED,
        kind=PropertyKind.BACKEND_EVALUATION,
        value=None,
        units="SI",
        domain=Domain(ranges={"T_K": (273.16, 647.1)}),  # triple -> critical (water)
        source=_NIST_WATER,
        backend="CoolProp HEOS",
        version="7.2.0",
        applicability=_SAT_APPLICABILITY,
    ),
]


# --- Lookup + completeness/structural checker -----------------------------------

TWO_PHASE_BY_ID: dict[str, PropertyEntry | CorrelationEntry] = {
    e.id: e for e in (*TWO_PHASE_CORRELATIONS, *TWO_PHASE_PROPERTIES)
}

#: Correlation kinds that must carry the gravity-basis metadata when RESOLVED.
_GRAVITY_KINDS = frozenset({"htc", "dp", "chf"})


def missing_metadata(
    entries: list[PropertyEntry | CorrelationEntry],
) -> list[str]:
    """Structural/completeness checker (metadata only -- no physics).

    Flags any entry that:

    * is missing a source (no ``source`` or empty ``source.citation``);
    * is a **RESOLVED** HTC/dP/CHF correlation missing the microgravity fields
      (``microgravity_validated``/``gravity_basis``/``rank_scope``/``limitation``);
    * is a rank-eligible correlation with an empty validity ``Domain``.

    Returns a list of human-readable ``"<id>: <reason>"`` strings (empty == complete).
    """
    problems: list[str] = []
    for e in entries:
        # 1) every entry must be sourced.
        if e.source is None or not e.source.citation:
            problems.append(f"{e.id}: missing source citation")

        if isinstance(e, CorrelationEntry):
            # 2) RESOLVED HTC/dP/CHF must carry the gravity-basis metadata.
            if e.status is Status.RESOLVED and e.kind in _GRAVITY_KINDS:
                if e.microgravity_validated is None:
                    problems.append(f"{e.id}: missing microgravity_validated flag")
                if not e.gravity_basis:
                    problems.append(f"{e.id}: missing gravity_basis")
                if not e.rank_scope:
                    problems.append(f"{e.id}: missing rank_scope")
                if not e.limitation:
                    problems.append(f"{e.id}: missing limitation")

            # 3) a rank-eligible correlation must state a validity domain.
            if e.rank_eligible and not e.domain.ranges:
                problems.append(f"{e.id}: rank-eligible correlation with empty Domain")

    return problems

