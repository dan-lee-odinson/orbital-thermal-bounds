"""S1 two-phase property/correlation registry: boiling/condensing heat-transfer
coefficient (HTC), two-phase pressure drop (dP), critical heat flux (CHF), onset
of nucleate boiling (ONB), and pump-inlet (NPSH) entries, plus the saturation
property-backend evaluation entries for the two-phase coolants.

S1 registered every entry with provenance, a resolution status, a source and (where
known) a validity domain, with **no** executable form: all ``evaluate`` callables
were ``None``. This mirrors the B1 pattern of registering a correlation on its
source/domain before wiring in the executable form.

**S2 (Stage 2) wires in the first executable form.** Exactly one correlation now
carries an ``evaluate`` callable -- ``two_phase.htc.gungor_winterton`` -- and every
other entry is still ``None``. Two entries that S2 was scoped to implement were
**not** implemented, and the blocker is the deliverable rather than a guess:

* ``two_phase.chf.shah_2015`` -- the citation is ambiguous (two distinct 2015 Shah
  CHF papers) and its declared ``pr_reduced`` domain provably belongs to Shah
  (1987). Attribution could not be established, so no maths was attached.
* ``two_phase.onb.bergles_rohsenow`` -- the 1964 criterion is graphical, and its
  usual algebraic surrogate is a dimensional water-only fit, out of fluid domain for
  the ammonia reference coolant.

Both keep a blank ``source.locator``; see each entry's source note for the evidence.
The invariant binding the two is enforced in the test suite: **an entry with a
non-None ``evaluate`` must have a non-empty ``source.locator``.**

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

import math
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


# --- Provisional (unconfirmed) validity domains ---------------------------------

#: Validity domains that could **not** be confirmed against an obtained source, kept
#: as declared but explicitly marked provisional rather than quietly promoted
#: (S0 no-invention policy). Each value states what was checked and what was found.
#:
#: A provisional domain is still **enforced** as the guard -- declaring it provisional
#: weakens the claim about the domain, not the range-checking of calls against it.
PROVISIONAL_DOMAINS: dict[str, str] = {
    "two_phase.htc.gungor_winterton": (
        "S2: the declared numeric ranges (G 10-600 kg/m2s, q'' 2e3-2.4e5 W/m2, "
        "quality 0.002-0.997, P 1.9e5-1.6e6 Pa, D 1.224e-3-3.2e-2 m) could not be "
        "matched to any obtained source. The consulted reference (Thome, Engineering "
        "Data Book III, Sec. 10.3.3) states the GW86 database as 3,693 points for "
        "water, R-11, R-12, R-22, R-113, R-114 and ethylene glycol but does not print "
        "these numeric bounds. The ranges are retained and enforced as the declared "
        "guard, but they are NOT confirmed against the source."
    ),
    "two_phase.chf.shah_2015": (
        "S2: pr_reduced 0.0014-0.96 was checked against the source and found to be "
        "the database range of Shah (1987), Int. J. Heat and Fluid Flow 8(4):326-335, "
        "not of either 2015 Shah CHF paper -- per Shah's own Fluids 2023, 8, 90 "
        "Sec. 3.1. Combined with the ambiguity of the 'Shah (2015)' citation itself "
        "(two distinct 2015 CHF papers, annuli vs horizontal channels), the domain "
        "cannot be attributed to this entry's nominal source. Declared provisional; "
        "the entry is NOT implemented. See the entry's source note."
    ),
}


# --- Sources --------------------------------------------------------------------
# CITATIONS: no fabricated DOIs. Author(s) (year), Journal strings only; DOIs/volume/
# pages are omitted where not confidently known (locator left blank -> confirm later).

_GUNGOR_WINTERTON = Source(
    citation="Gungor & Winterton (1986), Int. J. Heat Mass Transfer",
    locator=(
        "executable form transcribed from Thome, J.R., 'Engineering Data Book III', "
        "Ch. 10 'Boiling Heat Transfer Inside Plain Tubes', Sec. 10.3.3, "
        "Eqs. [10.3.20]-[10.3.23], with supporting definitions [10.3.4]-[10.3.6], "
        "[10.3.8] and [10.3.15] (chapter updated 2007)"
    ),
    note=(
        "PROVENANCE OF THE IMPLEMENTED FORM (S2). The primary 1986 IJHMT paper was "
        "NOT obtained; the equations were transcribed from the Thome reference work "
        "named in the locator, which reproduces them verbatim with equation numbers. "
        "The Cooper (1984) nucleate term was independently cross-checked against "
        "Shah (2022), Int. J. Refrigeration 137:103-116 Eq. (25) and agrees exactly. "
        "No volume, page or DOI is asserted for the 1986 paper because it was not "
        "consulted. The declared numeric domain below could NOT be confirmed against "
        "any obtained source and is provisional (see PROVISIONAL_DOMAINS)."
    ),
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
    note=(
        "S2: PROMOTION ATTEMPTED AND DECLINED -- stays SOURCE_REQUIRED, locator left "
        "blank. Two independent reasons, either sufficient on its own:\n"
        "(1) THE CRITERION IS GRAPHICAL. Liu, Lee & Garimella (2005), 'Prediction of "
        "the onset of nucleate boiling in microchannel flow', Int. J. Heat and Mass "
        "Transfer 48:5134-5149, records that Bergles and Rohsenow 'extended Hsu's "
        "model and proposed a GRAPHICAL solution to predict the incipient heat flux "
        "in flow boiling'. There is no closed form in the original to transcribe.\n"
        "(2) THE ALGEBRAIC SURROGATE IS WATER-ONLY AND DIMENSIONAL. The algebraic "
        "form commonly attributed to that graphical construction is a dimensional fit "
        "for water over roughly 1-138 bar. The S0 Sec. 9.1 reference coolant is "
        "AMMONIA, which is outside its fluid domain; applying it to ammonia would be "
        "an extrapolation across fluids, not a citation.\n"
        "CONSEQUENCE. No defensible executable ONB criterion exists for the reference "
        "coolant, so none is implemented. Per S0 Sec. 3 (F2) the ONB/saturated-regime "
        "POLICY GATE still ships unconditionally and, absent a sourced criterion, "
        "marks at-or-below-ONB cases sensitivity-only and not rank-eligible."
    ),
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
    note=(
        "S2 ATTRIBUTION BLOCKER -- executable form NOT implemented; locator "
        "deliberately left blank. Two findings, both from Shah's own publications:\n"
        "(1) AMBIGUOUS CITATION. There is no single 'Shah (2015)' general CHF "
        "correlation. Shah published TWO distinct CHF papers in 2015: 'Improved "
        "general correlation for CHF in vertical annuli with upflow', Heat Transfer "
        "Engineering 37(6):557-570; and 'A general correlation for CHF in horizontal "
        "channels', Int. J. Refrigeration 59:37-52. The citation string above "
        "identifies neither, and the two apply to different geometries (annuli vs "
        "channels). The S2 evaporator geometry is channels, so the choice is not "
        "immaterial.\n"
        "(2) THE DECLARED DOMAIN BELONGS TO A DIFFERENT PAPER. The declared "
        "pr_reduced range 0.0014-0.96 is verifiably the database range of Shah "
        "(1987), 'Improved general correlation for critical heat flux in uniformly "
        "heated vertical tubes', Int. J. Heat and Fluid Flow 8(4):326-335. Shah's own "
        "Fluids 2023, 8, 90 Sec. 3.1 states: 'Shah (1987) analyzed data for 23 fluids "
        "..., tube diameters 0.315 to 37.5 mm, mass flux 4 to 2905 kg m-2 s-1, "
        "reduced pressure 0.0014 to 0.96, and critical quality -0.26 to 0.96.' That "
        "same 2023 paper still treats Shah (1987) -- not a 2015 paper -- as the "
        "most-verified general CHF correlation for tubes.\n"
        "CONSEQUENCE. Implementing this id would require choosing which paper it "
        "means and attaching maths whose attribution cannot be established. Under the "
        "no-invention rule the entry stays unimplemented and the blocker is the "
        "deliverable. The domain is DECLARED PROVISIONAL (see PROVISIONAL_DOMAINS). "
        "Note that this finding also bears on the registry's classification of "
        "two_phase.chf.shah_1987 as a mere 'historical ancestor' sensitivity; that "
        "is a registry-level question for director disposition, not for this build."
    ),
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


# --- S2 executable form: Gungor & Winterton (1986) saturated flow-boiling HTC ----
#
# SOURCE CONSULTED (S2). The executable form below was transcribed from:
#
#   Thome, J.R., "Engineering Data Book III", Chapter 10 "Boiling Heat Transfer
#   Inside Plain Tubes", Section 10.3.3 (chapter updated 2007), Wolverine Tube Inc.
#   Equations [10.3.20]-[10.3.23], with the supporting definitions [10.3.4] (Dittus-
#   Boelter), [10.3.5] (Re_L), [10.3.6] (Pr_L), [10.3.8] (Martinelli X_tt) and
#   [10.3.15] (Boiling number Bo).
#
# INDEPENDENT CROSS-CHECK. The Cooper (1984) nucleate pool-boiling term [10.3.21]
# is reproduced identically in Shah, M.M. (2022), "New general correlation for heat
# transfer during saturated boiling in mini and macro channels", Int. J.
# Refrigeration 137:103-116, Eq. (25). Two independent sources agree term by term.
#
# NOT IMPLEMENTED, AND WHY (named modelling decision, not a silent omission).
# Gungor & Winterton (1986) also carries a Froude-number correction that de-rates
# the correlation for **stratified flow in horizontal channels** -- confirmed by
# Shah, M.M. (2006), HVAC&R Research 12(4), which records that GW86 "incorporated
# the Froude number for horizontal channels in the same way as in the Shah
# correlation". That correction models gravitational phase stratification. It is
# **deliberately not applied here**: stratification is a 1g horizontal-channel
# effect with no microgravity meaning, and applying a gravity-driven de-rating in a
# microgravity screening model would be a silent physical assumption. The
# implemented form is therefore the vertical / non-stratified form that Thome
# Section 10.3.3 presents. This mirrors the S0 Section 3 treatment of the static
# pressure head (dP_static ~ 0 in microgravity) as a *recorded* modelling decision.
#
# FLUID-DATABASE LIMITATION (machine-visible; see GW86_DATABASE_FLUIDS).
# The GW86 database is water, R-11, R-12, R-22, R-113, R-114 and ethylene glycol
# (Thome Section 10.3.3). **Ammonia is not in it** -- and ammonia is the S0 Section
# 9.1 reference coolant. This is recorded as a machine-visible applicability flag,
# not buried in prose; it is a finding for director disposition, not a defect this
# build is authorised to resolve by changing a director ruling.

#: Fluids in the Gungor & Winterton (1986) development database (Thome, Engineering
#: Data Book III, Section 10.3.3). A coolant absent from this list is outside the
#: correlation's *fluid* database even when every numeric input is inside the
#: declared numeric domain -- checked by :func:`fluid_in_gw86_database`.
GW86_DATABASE_FLUIDS: frozenset[str] = frozenset(
    {"water", "r-11", "r-12", "r-22", "r-113", "r-114", "ethylene glycol"}
)


def fluid_in_gw86_database(fluid: str) -> bool:
    """True iff ``fluid`` is in the GW86 development database (see the module note).

    ``False`` for ammonia: GW86 was not developed against ammonia data, so an
    ammonia case is outside the correlation's fluid database even when its mass
    flux, quality, pressure and diameter are all inside the declared domain.
    """
    return fluid.strip().lower() in GW86_DATABASE_FLUIDS


def martinelli_xtt(
    quality: float, rho_f: float, rho_g: float, mu_f: float, mu_g: float
) -> float:
    """Turbulent-turbulent Martinelli parameter (Thome [10.3.8])::

        X_tt = ((1-x)/x)^0.9 * (rho_g/rho_f)^0.5 * (mu_f/mu_g)^0.1
    """
    return (
        ((1.0 - quality) / quality) ** 0.9
        * (rho_g / rho_f) ** 0.5
        * (mu_f / mu_g) ** 0.1
    )


def boiling_number(q_flux_W_m2: float, mass_flux_kg_m2s: float, h_fg_J_kg: float) -> float:
    """Boiling number ``Bo = q'' / (G h_fg)`` (Thome [10.3.15])."""
    return q_flux_W_m2 / (mass_flux_kg_m2s * h_fg_J_kg)


def dittus_boelter_liquid_htc(
    *,
    mass_flux_kg_m2s: float,
    quality: float,
    diameter_m: float,
    rho_f: float,
    mu_f: float,
    k_f: float,
    cp_f: float,
) -> float:
    """Liquid-fraction Dittus-Boelter coefficient (Thome [10.3.4]-[10.3.6])::

        alpha_L = 0.023 Re_L^0.8 Pr_L^0.4 k_f / D,   Re_L = G(1-x)D/mu_f

    This is the single-phase convective base of GW86 and the value the correlation
    must recover as ``x -> 0`` with ``q'' -> 0`` (S0 Section 6 gate 1d).

    ``rho_f`` is accepted for signature symmetry with the other property groups; the
    Dittus-Boelter form is a function of the mass flux, not the density.
    """
    re_l = mass_flux_kg_m2s * (1.0 - quality) * diameter_m / mu_f
    pr_l = cp_f * mu_f / k_f
    return 0.023 * re_l**0.8 * pr_l**0.4 * k_f / diameter_m


def cooper_pool_boiling_htc(
    *, p_reduced: float, molar_mass_g_mol: float, q_flux_W_m2: float
) -> float:
    """Cooper (1984) nucleate pool-boiling coefficient (Thome [10.3.21])::

        alpha_nb = 55 p_r^0.12 (-0.4343 ln p_r)^-0.55 M^-0.5 q''^0.67

    **Dimensional.** ``q_flux_W_m2`` must be in W/m^2 and ``molar_mass_g_mol`` in
    g/mol (water = 18.02, ammonia = 17.03); the result is in W/m^2/K. The molar mass
    is taken in g/mol explicitly because a kg/mol value would silently shift the
    result by a factor of ~32.
    """
    return (
        55.0
        * p_reduced**0.12
        * (-0.4343 * math.log(p_reduced)) ** -0.55
        * molar_mass_g_mol**-0.5
        * q_flux_W_m2**0.67
    )


def gungor_winterton_1986_htc(
    *,
    mass_flux_kg_m2s: float,
    quality: float,
    q_flux_W_m2: float,
    diameter_m: float,
    rho_f: float,
    rho_g: float,
    mu_f: float,
    mu_g: float,
    k_f: float,
    cp_f: float,
    h_fg_J_kg: float,
    p_reduced: float,
    molar_mass_g_mol: float,
) -> float:
    """Gungor & Winterton (1986) saturated flow-boiling HTC, W/m^2/K.

    Vertical / non-stratified form (Thome [10.3.20]-[10.3.23])::

        alpha_tp = E alpha_L + S alpha_nb
        E = 1 + 24000 Bo^1.16 + 1.37 (1/X_tt)^0.86
        S = [1 + 1.15e-6 E^2 Re_L^1.17]^-1

    ``alpha_L`` is the liquid-fraction Dittus-Boelter coefficient and ``alpha_nb``
    the Cooper (1984) nucleate term. The horizontal-channel Froude/stratification
    de-rating is deliberately not applied -- see the module note above.

    This function performs **no domain checking**: callers on the ranking path must
    first call ``assert_in_domain`` against the registry entry
    ``two_phase.htc.gungor_winterton`` (S0 Section 6 gate 4). It is a pure function
    of already-evaluated properties, so this module stays free of CoolProp.

    At ``quality <= 0`` the Martinelli convective-enhancement term is taken at its
    ``x -> 0`` limit of zero rather than evaluated at a singular ``X_tt``.
    """
    alpha_l = dittus_boelter_liquid_htc(
        mass_flux_kg_m2s=mass_flux_kg_m2s,
        quality=max(quality, 0.0),
        diameter_m=diameter_m,
        rho_f=rho_f,
        mu_f=mu_f,
        k_f=k_f,
        cp_f=cp_f,
    )
    bo = boiling_number(q_flux_W_m2, mass_flux_kg_m2s, h_fg_J_kg)

    # Convective enhancement E. As x -> 0, X_tt -> inf and (1/X_tt)^0.86 -> 0.
    if quality <= 0.0:
        conv_term = 0.0
    else:
        x_tt = martinelli_xtt(quality, rho_f, rho_g, mu_f, mu_g)
        conv_term = 1.37 * (1.0 / x_tt) ** 0.86
    e_factor = 1.0 + 24000.0 * bo**1.16 + conv_term

    # Nucleate suppression S, with Re_L on the liquid fraction (1-x).
    re_l = mass_flux_kg_m2s * (1.0 - max(quality, 0.0)) * diameter_m / mu_f
    s_factor = 1.0 / (1.0 + 1.15e-6 * e_factor**2 * re_l**1.17)

    alpha_nb = cooper_pool_boiling_htc(
        p_reduced=p_reduced,
        molar_mass_g_mol=molar_mass_g_mol,
        q_flux_W_m2=q_flux_W_m2,
    )
    return e_factor * alpha_l + s_factor * alpha_nb


# --- Two-phase correlation registry (evaluate wired for the S2-implemented ids) --

TWO_PHASE_CORRELATIONS: list[CorrelationEntry] = [
    # ---------------- Heat-transfer coefficient (HTC) ----------------
    CorrelationEntry(
        id="two_phase.htc.gungor_winterton",
        name="Gungor & Winterton saturated flow-boiling HTC",
        kind="htc",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="alpha_tp = E alpha_L + S alpha_nb; E = 1 + 24000 Bo^1.16 + "
        "1.37 (1/X_tt)^0.86; S = [1 + 1.15e-6 E^2 Re_L^1.17]^-1 "
        "(vertical / non-stratified form; Cooper 1984 nucleate term)",
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
        evaluate=gungor_winterton_1986_htc,
        applicability="rank-eligible reference flow-boiling HTC (S2 executable). "
        "Callers on the ranking path must assert_in_domain first. The declared "
        "numeric domain is PROVISIONAL (see PROVISIONAL_DOMAINS). The horizontal "
        "Froude/stratification de-rating is deliberately not applied (1g effect; see "
        "module note). AMMONIA IS NOT IN THE GW86 FLUID DATABASE -- see "
        "GW86_DATABASE_FLUIDS / fluid_in_gw86_database.",
        note="reference HTC correlation for two-phase ranking; 1g basis (see limitation); "
        "S2 executable form transcribed from Thome EDB III Sec. 10.3.3 (see source note)",
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
        applicability="reference CHF on a local modeled wall-flux basis, feeding the "
        "q''/CHF <= 0.5 design band. S2 DID NOT IMPLEMENT IT: the citation is "
        "ambiguous and the declared domain traces to Shah (1987), not to either 2015 "
        "paper (see source note). Domain is PROVISIONAL (see PROVISIONAL_DOMAINS). "
        "The CHF BANDING POLICY ships regardless -- it is a policy gate over a CHF "
        "value, not a correlation -- but no sourced CHF evaluator backs it, so a case "
        "needing a computed CHF is blocked, never silently ranked.",
        note="reference CHF: local modeled wall-flux basis; feeds q''/CHF<=0.5 band; "
        "S2 attribution blocker -- not implemented, locator intentionally blank",
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

