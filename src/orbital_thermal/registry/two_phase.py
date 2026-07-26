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

from .applicability import Applicability, DomainProvenance
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
        "PROVENANCE-UNESTABLISHED (Director ruling D1). The five numeric limits "
        "(G 10-600 kg/m2s, q'' 2e3-2.4e5 W/m2, quality 0.002-0.997, P 1.9e5-1.6e6 Pa, "
        "D 1.224e-3-3.2e-2 m) appear in NONE of the twenty-one consulted sources, "
        "including Collier & Thome 3rd ed. (1994) Sec. 7.4.3 -- the canonical text by "
        "the same author whose handbook the implementation was transcribed from, which "
        "describes the database by point count, fluid list and flow orientation and "
        "prints no numeric range. Retained and ENFORCED as guards, but they are NOT "
        "the authors' declared range and must never be presented as such. DEBTS D-1."
    ),
    "two_phase.chf.shah_1987": (
        "PROVENANCE-CONFLICTED on two axes, resolved in favour of Shah describing "
        "Shah. Mass velocity: the Springer microscale text prints '3.9 to 29.051' "
        "kg/m2s, Shah's own Fluids 2023 Appendix prints '4 to 2905' -- a factor of "
        "ten; the latter is adopted. Critical quality: '-2.6 to 1' vs '-0.26 to 0.96'; "
        "the latter is adopted. Reduced pressure 0.0014-0.96 and diameter 0.315-37.5 "
        "mm are AGREED by both printings and carry no conflict. INLET QUALITY is "
        "single-source, not conflicted, and is now ENFORCED at the tighter [-2.6, "
        "0.85] per Director ruling -- see SHAH_1987_INLET_QUALITY_NOTE."
    ),
    "two_phase.chf.shah_2015": (
        "DOMAIN DETACHED, not merely provisional. The pr_reduced 0.0014-0.96 band was "
        "never this entry's: it is Shah (1987)'s database range, per Shah's own Fluids "
        "2023, 8, 90 Sec. 3.1, and has been re-attributed to two_phase.chf.shah_1987 "
        "under Director ruling D3. This entry now declares no domain at all, because a "
        "correlation whose citation resolves to no single paper has no validity range "
        "to declare."
    ),
}


# --- Sources --------------------------------------------------------------------
# CITATIONS: no fabricated DOIs. Author(s) (year), Journal strings only; DOIs/volume/
# pages are omitted where not confidently known (locator left blank -> confirm later).

_GUNGOR_WINTERTON = Source(
    citation=(
        "Gungor, K.E. & Winterton, R.H.S. (1986), 'A general correlation for flow "
        "boiling in tubes and annuli', Int. J. Heat Mass Transfer 29(3):351-358"
    ),
    locator=(
        "Executable form confirmed by THREE independent printings, which agree with "
        "each other and with the shipped code: "
        "(1) Thome, J.R., 'Engineering Data Book III', Ch. 10, Sec. 10.3.3, "
        "Eqs. [10.3.20]-[10.3.23] with supporting [10.3.4]-[10.3.6], [10.3.8], "
        "[10.3.15] (the source the code was transcribed from); "
        "(2) CFD Letters 10(2) (2018): 49-58, Eq. (3) for E, Eq. (2) for the Cooper "
        "nucleate term, Eq. (4) for the suppression factor; "
        "(3) Collier, J.G. & Thome, J.R. (1994), 'Convective Boiling and "
        "Condensation', 3rd ed., Oxford, Sec. 7.4.3, Eq. (7.36). "
        "The Cooper (1984) nucleate term is additionally cross-checked against "
        "Shah (2022), Int. J. Refrigeration 137:103-116 Eq. (25)."
    ),
    note=(
        "PROVENANCE OF THE IMPLEMENTED FORM. The 1986 primary paper was NOT obtained "
        "(paywalled; DEBTS D-2). The volume/issue/pages above are confirmed by four "
        "independent reference lists; NO DOI is asserted because none was obtained. "
        "Director ruling D2 governs: 'The primary paper was unobtainable at this time, "
        "but correlation by multiple obtainable sources that can be cited provides the "
        "evidentiary defense.' Three independent printings all give the convective "
        "coefficient as 1.37 and the shipped code uses 1.37. Taboas Touceda (2006) "
        "Anexo I Eqs. (34)/(36) print 1.23; three sources against one makes that a "
        "transcription error in Taboas, not a variant form -- worth up to 9.43% at the "
        "top of the declared box. THE FIVE NUMERIC LIMITS ARE A SEPARATE MATTER: they "
        "appear in none of the twenty-one consulted sources and are labelled "
        "PROVENANCE-UNESTABLISHED (Director ruling D1; DEBTS D-1). They remain enforced "
        "as guards but are NOT the authors' declared range."
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
    locator=(
        "Executable form read from the source pages: Collier, J.G. & Thome, J.R., "
        "'Convective Boiling and Condensation', 3rd ed., Sec. 2.4 'The separated flow "
        "model', pp. 49-55 -- Eq. (2.67) for X, Eq. (2.69) for phi_g^2, Eq. (2.68) for "
        "phi_f^2, and the regime table on p. 53 for the Chisholm C values."
    ),
    note=(
        "S3 PROVENANCE. Eqs. (2.67), (2.68), (2.69) and the Chisholm C table were READ "
        "FROM THE RENDERED PAGES and are implemented as printed. "
        "LIMITATION OF THE FILE, NOT THE SOURCE: this PDF's embedded text layer is "
        "degraded -- automated extraction drops subscripts and operators, returning "
        "'1 + _ + _2' for the perfectly clear printed Eq. (2.68) -- so anything taken "
        "from it must be read from the rendered page. An extraction is a transcription. "
        "The identity phi_g^2 = phi_f^2 X^2, which reproduces the printed (2.68) from "
        "the printed (2.69) and (2.67), is retained and asserted as a test: it is an "
        "INDEPENDENT CONFIRMATION of the printed equation, not its source. "
        "The four Chisholm C values match the repo's pinned CHISHOLM_C exactly, which "
        "independently confirms an S1 value. "
        "CHISHOLM (1967) IS NOT THE VALIDITY EXTENSION: per p. 52 it corrects the "
        "treatment 'by allowing for the interfacial shear force (S) between the "
        "phases', i.e. the annular-flow void-fraction inconsistency. Chisholm (1963) "
        "supplies C = 1.36 at critical pressure, and MARTINELLI-NELSON (1948) is the "
        "single-component / pressure extension (p. 54, Table 2.2, 1.01-221.2 bar). "
        "Neither Martinelli-Nelson nor Chisholm (1967) is in hand, so neither is "
        "implemented and no numeric pressure ceiling is attributed to the source."
    ),
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
        "horizontal channels), so the choice is not immaterial. DIR-01 CORRECTION: an "
        "earlier version of this note asserted 'the S2 evaporator geometry is "
        "channels' -- an unsourced claim about a device that does not exist. Director "
        "ruling D9 settles the family as the SMALL-BORE ROUND TUBE, which is why "
        "neither 2015 paper is a clean fit and why Shah (1987), for round tubes, is.\n"
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
    citation=(
        "Shah, M.M. (1987), 'Improved general correlation for critical heat flux "
        "during upflow in uniformly heated vertical tubes', Int. J. Heat and Fluid "
        "Flow 8(4):326-335"
    ),
    locator=(
        "Executable form reconciled across TWO printings: "
        "[S] 'Flow Boiling and Condensation in Microscale Channels' (Springer, ISBN "
        "978-3-030-68703-8), Ch. 6 Sec. 6.4, Eqs. (6.51)-(6.65); and "
        "[A] Shah, M.M. (2023), Fluids 8, 90, Appendix A 'Shah Correlation (1987) for "
        "CHF in Vertical Tubes', Eqs. (A1)-(A17). "
        "[A] is Shah printing his own correlation and is ADOPTED wherever the two "
        "differ; every divergence is recorded in the module note above."
    ),
    note=(
        "PROMOTED to the CHF reference by Director ruling D3 (OTB-G001 F-03): 'Shah "
        "1987 is the confirmable source - if the 2015 cannot be confirmed, it must be "
        "replaced.' No DOI is asserted. FIVE transcription divergences between the two "
        "printings were found and resolved in favour of [A]; two were flagged in the "
        "fix inputs (the F2 label, the mass-velocity range) and three were not (the "
        "definition of Y itself, the Bo0 third constant, and the Fx x>0 branch). The "
        "F2 exponent sign is additionally confirmed by continuity at F1 = 4, and [A]'s "
        "high-Y F1 rule is confirmed numerically against [S]'s printed 4.452. "
        "GRAVITY-EXPLICIT: Y contains g, so the correlation has no microgravity limit "
        "-- see SHAH_1987_APPLICABILITY."
    ),
)
_KATTO_OHNO = Source(
    citation="Katto & Ohno (1984), Int. J. Heat Mass Transfer (generalized CHF)",
)
_NPSH = Source(
    citation=(
        "van Es, J. et al. (2009), 'AMS02 Tracker Thermal Control System: overview and "
        "test results', NLR-TP-2009-699 / IAC-09.C2.7.1 -- flight precedent for a "
        "mechanically pumped two-phase loop; ANSI/HI 9.6.1-2012 recorded but NOT adopted"
    ),
    locator=(
        "Criterion adopted per Director ruling D8 from the AMS-02 Tracker Thermal "
        "Control System, a mechanically pumped two-phase CO2 loop operating on ISS "
        "since 2011: condenser exit state guarantees the fluid 'is sub-cooled well "
        "below the saturation point so arrives in liquid phase back at the pump'."
    ),
    note=(
        "WHY SUBCOOLING AND NOT AN NPSHR MARGIN. ANSI/HI 9.6.1-2012 defines "
        "NPSHA = h_atm + h_s - h_vp (with h_vp at the HIGHEST SUSTAINED operating "
        "temperature), NPSH margin = NPSHA - NPSH3, and margin ratio = NPSHA / NPSH3. "
        "It gives NO route to NPSH3 without a specific pump, and no pump is selected "
        "here, so the quantitative route is RECORDED AND NOT IMPLEMENTED (DEBTS D-4). "
        "ITS WARNING, WHICH ANY FUTURE NPSHR GUARD MUST CARRY: NPSH3 is the point at "
        "which 3 % of first-stage head has ALREADY been lost to cavitation, so "
        "NPSHA = NPSHR is the ONSET OF DAMAGE, not a safe operating point -- a future "
        "guard must enforce a margin over it, never equality."
    ),
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

# --- DIR-01: the geometry vocabulary, defined rather than assumed ----------------
#
# The S2 build asserted that "the S2 evaporator geometry is channels" -- an unsourced
# claim about a device that does not exist, which this project had no authority to
# write. Director ruling D9 settles the family: the modelled evaporator is the
# SMALL-BORE ROUND TUBE, which both adopted correlations' declared geometry bases
# already cover (Gungor & Winterton {round_tube, annulus}; Shah (1987) {round_tube}).
# The note was the error, not the correlations, and nothing at S2 needs re-basing.
#
# The vocabulary is defined here so that a 2.6 mm bore cannot be simultaneously inside
# one declared basis and outside another purely because two notes used different words
# for the same thing.

#: What each geometry token means. A correlation's declared ``geometries`` set draws
#: from these, and a case states exactly one of them.
GEOMETRY_VOCABULARY: dict[str, str] = {
    "round_tube": (
        "A circular-bore tube of any diameter, characterised by that bore. The modelled "
        "evaporator family (Director ruling D9). 'Small-bore' is a description of where "
        "in the range a case sits, NOT a separate geometry: a 2.6 mm round tube and a "
        "26 mm round tube are the same geometry at different bores, and the bore is "
        "checked against each correlation's declared D_m domain."
    ),
    "annulus": (
        "The gap between two concentric tubes, characterised by an equivalent diameter. "
        "Inside Gungor & Winterton's declared basis; outside Shah (1987)'s, which is "
        "round tubes only."
    ),
    "channel": (
        "A NON-circular passage -- rectangular, chevron-plate, or a parallel array of "
        "them -- characterised by a hydraulic diameter. Deliberately DISJOINT from "
        "round_tube: the term was previously used loosely for both, which is what let "
        "an unsourced claim about the evaporator's geometry pass unnoticed. No adopted "
        "correlation declares this basis, so a channel case is out of applicability on "
        "the geometry axis for every correlation in this registry."
    ),
}


def geometry_is_defined(shape: str) -> bool:
    """Whether ``shape`` is a defined geometry token (DIR-01)."""
    return shape.strip().lower() in GEOMETRY_VOCABULARY


#: Fluids in the Gungor & Winterton (1986) development database (Thome, Engineering
#: Data Book III, Section 10.3.3). A coolant absent from this list is outside the
#: correlation's *fluid* database even when every numeric input is inside the
#: declared numeric domain -- checked by :func:`fluid_in_gw86_database`.
GW86_DATABASE_FLUIDS: frozenset[str] = frozenset(
    {"water", "r-11", "r-12", "r-22", "r-113", "r-114", "ethylene glycol"}
)


#: Minimum liquid Reynolds number for the Dittus-Boelter convective base (OTB-G001
#: F-06a). Set to Stage-1's own turbulent threshold (``pumped_loop._TURBULENT_RE_NUSSELT``)
#: so the two stages classify flow regime identically rather than by two conventions.
#:
#: Provenance, stated honestly: this is an **internal project convention**, not a number
#: read out of a GW86 source. None of the twenty-one consulted sources prints a Reynolds
#: validity band for the correlation. The classical Dittus-Boelter fully-turbulent range
#: (commonly quoted as Re >= 1e4) is STRICTER than this threshold, so the guard here is
#: the permissive end of the plausible range; tightening it is a recorded option, not a
#: silent default. See DEBTS D-1 for the same treatment of the numeric box.
GW86_MIN_LIQUID_REYNOLDS = 3000.0

#: Enforceable applicability of Gungor & Winterton (1986) -- the fix for OTB-G001 F-06
#: (fluid + regime axes) and DEBTS D-9 (geometry axis).
GW86_APPLICABILITY = Applicability(
    fluids=GW86_DATABASE_FLUIDS,
    fluids_basis=(
        "Development database agreed by five independent sources -- Collier & Thome "
        "(1994) 3rd ed. Sec. 7.4.3 (verbatim: 3693 points for 'water, refrigerants "
        "(R11, R12, R22, R113 and R114) and ethylene glycol'), Thome Engineering Data "
        "Book III Sec. 10.3.3, Kandlikar (1990) Table 1, Zurcher et al. (1999), and "
        "Taboas (2006) Anexo I. Ammonia appears in none of them."
    ),
    geometries=frozenset({"round_tube", "annulus"}),
    geometries_basis=(
        "The 1986 paper is titled 'A general correlation for flow boiling in tubes and "
        "annuli' (Int. J. Heat Mass Transfer 29(3):351-358). Closes DEBTS D-9, which "
        "recorded that this geometry basis was stated in titles and docstrings and "
        "enforced nowhere."
    ),
    orientations=frozenset({"vertical_upflow", "vertical_downflow"}),
    orientations_basis=(
        "Collier & Thome Sec. 7.4.3 records the database as covering vertical upward "
        "and downward flows AND horizontal flows -- but the horizontal branch requires "
        "the Froude/stratification de-rating (Fr_L < 0.05), which this build "
        "deliberately does not implement because it models gravitational phase "
        "stratification. The implemented form is therefore the vertical / "
        "non-stratified one, and horizontal orientation is outside what is implemented."
    ),
    min_liquid_reynolds=GW86_MIN_LIQUID_REYNOLDS,
    reynolds_basis=(
        "The convective base is Dittus-Boelter on the liquid fraction G(1-x), which is "
        "a turbulent correlation. Threshold set to Stage-1's own turbulent boundary; "
        "see GW86_MIN_LIQUID_REYNOLDS for its provenance."
    ),
    numeric_domain_provenance=DomainProvenance.UNESTABLISHED,
    numeric_domain_note=(
        "The five numeric limits (G 10-600, q'' 2e3-2.4e5, quality 0.002-0.997, "
        "P 1.9e5-1.6e6, D 1.224e-3-3.2e-2) appear in NONE of the twenty-one consulted "
        "sources, including Collier & Thome Sec. 7.4.3 by the same author as the "
        "handbook the code was transcribed from -- which describes the database by "
        "point count, fluid list and flow orientation and prints no numeric range. "
        "Retained and enforced as guards under Director ruling D1, but they are NOT "
        "the authors' declared range. See DEBTS D-1."
    ),
    unenforced_axes=(
        "liquid Prandtl number: no sourced validity band was obtained for the "
        "Dittus-Boelter base, so no Pr_L limit is enforced rather than an invented one "
        "(C1). Director direction on F-06 names the Reynolds guard, the seven-fluid "
        "database and the numeric limits; Pr is outside it.",
    ),
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


# --- S2 executable form: Shah (1987) CHF in uniformly heated vertical tubes -----
#
# Promoted to the CHF reference by Director ruling D3 (OTB-G001 F-03): "Shah 1987 is
# the confirmable source - if the 2015 cannot be confirmed, it must be replaced."
#
# SOURCES CONSULTED, AND HOW THEY WERE RECONCILED.
#
#   [S] Flow Boiling and Condensation in Microscale Channels (Springer,
#       ISBN 978-3-030-68703-8), Ch. 6 Sec. 6.4, Eqs. (6.51)-(6.65) -- supplied with
#       the fix inputs, and flagged there as carrying transcription hazards.
#   [A] Shah, M.M. (2023), Fluids 8, 90, APPENDIX A "Shah Correlation (1987) for CHF
#       in Vertical Tubes", Eqs. (A1)-(A17) -- obtained from the author's own
#       publication archive and text-extracted directly.
#
# **[A] is Shah printing his own correlation and is adopted as the transcription
# source wherever the two differ.** The fix inputs themselves name Shah-2023 the
# better authority for the mass-velocity conflict; the same logic governs every term.
# Every divergence is recorded rather than silently resolved (C8: access route is not
# a provenance criterion, transcription fidelity is).
#
# THE TWO HAZARDS THE INPUTS FLAGGED -- both resolved against [A]:
#
#   1. Eq. (6.65)'s left-hand side renders self-referentially in [S]. [A](A16)/(A17)
#      confirms it is **F2**. It also shows [S] lost a MINUS SIGN: [A] prints
#      `F2 = F1^-0.42`, [S] prints `F1^0.42`. Continuity settles this independently of
#      authority -- F2 is piecewise at F1 = 4, and 4^-0.42 = 0.5588 joins smoothly to
#      the F1 > 4 value of 0.55, whereas 4^+0.42 = 1.789 would jump down by 3.25x.
#      The subcooled branch is therefore implemented, not blocked.
#   2. Mass velocity: [S] "3.9 to 29.051", [A] "4 to 2905" kg/m2s. Recorded
#      provenance-CONFLICTED; [A] adopted, per the inputs' own instruction.
#
# THREE FURTHER DIVERGENCES FOUND HERE, NOT FLAGGED IN THE INPUTS:
#
#   3. **Y itself.** [S] prints `Y = Pe * Fe^0.4 * (mu_l/mu_v)^0.6` with
#      `Fe = 1.54 - 0.032(L/d_h)` -- conflating the ENTRANCE-EFFECT factor F_E with a
#      FROUDE group. [A](A2) gives `Y = (G D cp_f/k_f)(G^2/(rho_f^2 g D))^0.4
#      (mu_f/mu_g)^0.6`. Both carry exponent 0.4, which is how the substitution went
#      unnoticed. F_E is a separate quantity, used in (A7)/(6.58). [A] adopted.
#   4. **Bo0 third candidate.** [S] `0.0024 Y^-0.105`; [A](A11) `0.00024 Y^-0.105`.
#      A factor of ten, and Bo0 is the HIGHEST of three candidates, so at large Y this
#      changes which branch wins. [A] adopted.
#   5. **Fx for x_crit > 0.** [S]'s expression is not well-formed and contains
#      "0.24157", a mangling of `F3^-0.29`. [A](A12)/(A13) adopted.
#
# CROSS-CHECK CONFIRMING [A]. For Y > 1.4e7, [S] prints `F1 = 1 + 4.452(-x)^0.88`
# while [A] says to evaluate the Y <= 1.4e7 form at Y = 1.4e7, giving
# `0.0052 * (1.4e7)^0.41 = 4.428` -- agreeing with [S]'s 4.452 to 0.5%. The two
# sources describe the same function by different routes and agree numerically. This
# is asserted as a test.
#
# ** THE FINDING NEITHER SOURCE FLAGS: Y IS GRAVITY-EXPLICIT. **
# Y contains g. As g -> 0, Y -> infinity, and both the branch selection (Y <= 1e6 vs
# Y > 1e6) and every Y-power term diverge. **Shah (1987) has no microgravity limit.**
# This is not the generic "1g-derived correlation" caveat -- it is a literal g in the
# correlating parameter. It is carried as the `gravity_explicit` applicability axis so
# that a microgravity case cannot quietly evaluate it.

#: Standard gravitational acceleration, m/s^2 (the 1g basis of Shah's Y parameter).
STANDARD_GRAVITY_M_S2 = 9.80665

#: Enforceable applicability of Shah (1987), the promoted CHF reference (Director
#: ruling D3 / OTB-G001 F-03).
SHAH_1987_APPLICABILITY = Applicability(
    # The 23 fluids are not enumerated in either consulted printing, so the inclusive
    # list cannot be stated without inventing it (C1). What IS established is the
    # exclusion, and that is what is enforced.
    excluded_fluids=frozenset({"ammonia"}),
    fluids_basis=(
        "The database covers 23 fluids from 16 studies, but neither consulted printing "
        "enumerates them, so no inclusive list is asserted. Ammonia is absent from "
        "every naming of the database in the consulted text -- recorded in the fix "
        "inputs as 'Ammonia is not among the 23 fluids named anywhere in the consulted "
        "text'. The same exclusion mechanism as Gungor & Winterton therefore applies."
    ),
    geometries=frozenset({"round_tube"}),
    geometries_basis=(
        "Shah (1987), 'Improved general correlation for critical heat flux during "
        "upflow in uniformly heated vertical TUBES', Int. J. Heat and Fluid Flow "
        "8(4):326-335. The annulus case is a different Shah correlation (2015a)."
    ),
    orientations=frozenset({"vertical_upflow"}),
    orientations_basis="Uniformly heated vertical tubes with UPFLOW, per the title.",
    gravity_explicit=True,
    gravity_basis=(
        "Y contains g explicitly: Y = (G D cp_f/k_f)(G^2/(rho_f^2 g D))^0.4 "
        "(mu_f/mu_g)^0.6 ([A] Eq. A2). As g -> 0 the Froude group diverges, taking Y "
        "and the branch selection with it. This correlation has NO microgravity limit "
        "-- a stronger statement than the standing 1g-basis caveat, and the reason the "
        "gravity axis exists. The database is 16 terrestrial studies, so standard "
        "gravity is where it exists and nowhere else (Director ruling D6)."
    ),
    reference_gravity_m_s2=STANDARD_GRAVITY_M_S2,
    branch_threshold=1.0e6,
    branch_threshold_basis=(
        "Shah's own transitional criterion: the calculation procedure switches at "
        "Y >= 10^6 ([S] Eqs. 6.55/6.57/6.58, [A] after Eq. A17). Used as a STRADDLE "
        "test against the value at standard gravity, not as an absolute bound -- Y "
        "exceeds 10^6 legitimately at 1 g under high mass flux (measured at G ~ 1400 "
        "kg/m2s for the reference case, inside the declared 4-2905 range), so an "
        "absolute test would reject ordinary terrestrial cases."
    ),
    numeric_domain_provenance=DomainProvenance.CONFLICTED,
    numeric_domain_note=(
        "Two axes disagree between the consulted printings and are resolved in favour "
        "of Shah describing Shah: mass velocity, [S] '3.9 to 29.051' vs [A] '4 to 2905' "
        "kg/m2s (adopted); critical quality, [S] '-2.6 to 1' vs [A] '-0.26 to 0.96' "
        "(adopted). Reduced pressure 0.0014-0.96 and diameter 0.315-37.5 mm are AGREED "
        "by both. INLET QUALITY is now ENFORCED at [-2.6, 0.85]; see "
        "SHAH_1987_INLET_QUALITY_NOTE, whose provenance is not what the round-2 "
        "handoff described."
    ),
    requires_executable_form=True,
)

#: Why the enforced inlet-quality bound is -2.6 and not -4.00 (OTB-G001-FIXES F-06).
#:
#: The round-2 handoff stated that the two printings conflict on the inlet-quality lower
#: bound -- "the Springer microscale text gives -2.6, Shah's own 2023 paper gives -4.00".
#: **Both attributions are reversed and the two quality axes are conflated.** What the
#: sources actually print:
#:
#:   [S] Springer microscale text: inlet vapour quality  -4.00 to 0.85
#:                                 critical vapour quality -2.6 to 1
#:   [A] Shah (2023) Fluids 8, 90 Sec. 3.1: critical quality -0.26 to 0.96;
#:                                 inlet quality NOT STATED
#:
#: So inlet quality is not source-conflicted at all -- it is single-source ([S] only,
#: the printing carrying three demonstrated transcription errors). The -2.6 figure is
#: [S]'s CRITICAL-quality bound, a different axis, already enforced separately at [A]'s
#: tighter -0.26.
#:
#: The Director's ruling is applied exactly as given regardless, because it is
#: implementable and conservative: -2.6 is TIGHTER than the only sourced inlet bound
#: (-4.00), and CHF is the DENOMINATOR of q''/CHF, so an inflated CHF makes a case look
#: safer. A tighter bound can only exclude cases, never admit one that -4.00 would have
#: excluded. The discrepancy is recorded rather than quietly reconciled (C8:
#: transcription fidelity), because a registry asserting "-2.6 is [S]'s inlet bound"
#: would state something [S] does not say.
SHAH_1987_INLET_QUALITY_NOTE = (
    "ENFORCED at [-2.6, 0.85] per the Director ruling 'Enforce the tighter one, keep "
    "the correlation usable'. PROVENANCE, which differs from the round-2 handoff's "
    "description: the only sourced inlet-quality range is [S]'s -4.00 to 0.85 "
    "(single-source; [A] states none), so the axis is single-source rather than "
    "conflicted, and -2.6 is [S]'s CRITICAL-quality lower bound. The enforced -2.6 is "
    "tighter than the sourced -4.00 and is therefore conservative for q''/CHF: it can "
    "only exclude cases, never admit one."
)


def shah_1987_Y(
    *,
    mass_flux_kg_m2s: float,
    diameter_m: float,
    cp_f: float,
    k_f: float,
    rho_f: float,
    mu_f: float,
    mu_g: float,
    gravity_m_s2: float = STANDARD_GRAVITY_M_S2,
) -> float:
    """Shah's correlating parameter ``Y`` ([A] Eq. A2)::

        Y = (G D cp_f / k_f) * (G^2 / (rho_f^2 g D))^0.4 * (mu_f / mu_g)^0.6

    **Gravity-explicit.** ``gravity_m_s2`` must be positive: the middle group divides
    by it, so the correlation has no zero-gravity limit. The default is standard
    gravity because the correlation's database is terrestrial; evaluating it for a
    microgravity case is an applicability violation, not a parameter change.
    """
    if gravity_m_s2 <= 0.0:
        raise ValueError(
            f"Shah (1987) is gravity-explicit: its correlating parameter Y divides by "
            f"g, so g = {gravity_m_s2} m/s^2 has no limit. The correlation cannot be "
            "evaluated in microgravity; treat the case as out of applicability."
        )
    peclet = mass_flux_kg_m2s * diameter_m * cp_f / k_f
    froude = mass_flux_kg_m2s**2 / (rho_f**2 * gravity_m_s2 * diameter_m)
    return peclet * froude**0.4 * (mu_f / mu_g) ** 0.6


def shah_1987_entrance_factor(length_to_diameter: float) -> float:
    """Entrance-effect factor ``F_E`` ([A] Eq. A8): ``1.54 - 0.032 (L_E/D)``, floored at 1."""
    return max(1.0, 1.54 - 0.032 * length_to_diameter)


def shah_1987_bo_zero(y: float, p_reduced: float) -> float:
    """Boiling number at ``x_c = 0`` -- the HIGHEST of [A] Eqs. (A9)-(A11)::

        Bo0 = 15 Y^-0.612
        Bo0 = 0.082 Y^-0.3   (1 + 1.45 p_r^4.03)
        Bo0 = 0.00024 Y^-0.105 (1 + 1.15 p_r^3.39)

    The third constant is ``0.00024`` per [A]; [S] prints ``0.0024``. See the module
    note -- the divergence matters at large Y, where this candidate can win.
    """
    return max(
        15.0 * y**-0.612,
        0.082 * y**-0.3 * (1.0 + 1.45 * p_reduced**4.03),
        0.00024 * y**-0.105 * (1.0 + 1.15 * p_reduced**3.39),
    )


def shah_1987_fx(y: float, p_reduced: float, critical_quality: float) -> float:
    """Quality-correction factor ``Fx`` ([A] Eqs. A12-A17).

    ``x_c > 0`` uses ``F3``; ``x_c < 0`` uses the subcooled ``F1``/``F2`` branch. The
    exponent on ``F2`` is **negative** (``F1^-0.42``) per [A](A16); see the module note
    for the continuity argument that confirms it against [S]'s positive exponent.
    """
    exponent = 1.0 if p_reduced > 0.6 else 0.0

    if critical_quality >= 0.0:
        f3 = (1.25e5 / y) ** (0.833 * critical_quality)
        return f3 * (1.0 + (f3**-0.29 - 1.0) * (p_reduced - 0.6) / 0.35) ** exponent

    # Subcooled branch. [A]: for Y > 1.4e7 use the same expression evaluated at 1.4e7.
    y_eff = min(y, 1.4e7)
    f1 = 1.0 + 0.0052 * (-critical_quality) ** 0.88 * y_eff**0.41
    f2 = f1**-0.42 if f1 <= 4.0 else 0.55
    return f1 * (1.0 - (1.0 - f2) * (p_reduced - 0.6) / 0.35) ** exponent


def shah_1987_critical_boiling_number(
    *,
    mass_flux_kg_m2s: float,
    diameter_m: float,
    length_to_chf_m: float,
    p_reduced: float,
    inlet_quality: float,
    critical_quality: float,
    cp_f: float,
    k_f: float,
    rho_f: float,
    mu_f: float,
    mu_g: float,
    gravity_m_s2: float = STANDARD_GRAVITY_M_S2,
    is_helium: bool = False,
) -> float:
    """Critical boiling number ``Bo_crit`` from Shah (1987), dimensionless.

    Combines the upstream-condition correlation (UCC, [A] A1) and the local-condition
    correlation (LCC, [A] A7) by [A]'s selection rule: helium always uses the UCC;
    otherwise the UCC is used for ``Y <= 1e6``, and for ``Y > 1e6`` whichever
    correlation gives the LOWER ``Bo`` -- except that the UCC is used when
    ``L_E/D > 160 / p_r^1.14``.

    Convert to a heat flux with :func:`shah_1987_chf`. This function performs no
    applicability checking; callers on the ranking path must go through the entry's
    ``applicability_spec`` and ``assert_in_domain`` first.
    """
    y = shah_1987_Y(
        mass_flux_kg_m2s=mass_flux_kg_m2s,
        diameter_m=diameter_m,
        cp_f=cp_f,
        k_f=k_f,
        rho_f=rho_f,
        mu_f=mu_f,
        mu_g=mu_g,
        gravity_m_s2=gravity_m_s2,
    )

    # Effective length and effective inlet quality ([A], after A5).
    if inlet_quality <= 0.0:
        length_eff, x_ie = length_to_chf_m, inlet_quality
    else:
        length_eff, x_ie = length_to_chf_m, 0.0
    ld = length_eff / diameter_m

    # --- UCC ([A] A1), with n from (A3)-(A5) ---
    if y <= 1.0e4:
        n = 0.0
    elif is_helium:
        n = (diameter_m / length_eff) ** 0.33
    elif y <= 1.0e6:
        n = (diameter_m / length_eff) ** 0.54
    else:
        n = 0.12 / (1.0 - x_ie) ** 0.5
    bo_ucc = 0.124 * (diameter_m / length_eff) ** 0.89 * (1.0e4 / y) ** n * (1.0 - x_ie)

    if is_helium:
        return bo_ucc

    # --- LCC ([A] A7) ---
    bo_lcc = (
        shah_1987_entrance_factor(ld)
        * shah_1987_fx(y, p_reduced, critical_quality)
        * shah_1987_bo_zero(y, p_reduced)
    )

    if y <= 1.0e6:
        return bo_ucc
    if ld > 160.0 / p_reduced**1.14:
        return bo_ucc
    return min(bo_ucc, bo_lcc)


def shah_1987_chf(
    *,
    mass_flux_kg_m2s: float,
    h_fg_J_kg: float,
    **kwargs: float,
) -> float:
    """Critical heat flux from Shah (1987), W/m^2.

    ``q_crit = Bo_crit * G * h_fg`` ([A] A6 / [S] 6.56). Remaining keyword arguments
    are passed to :func:`shah_1987_critical_boiling_number`.
    """
    bo = shah_1987_critical_boiling_number(
        mass_flux_kg_m2s=mass_flux_kg_m2s, **kwargs
    )
    return bo * mass_flux_kg_m2s * h_fg_J_kg


# --- S3 executable form: Lockhart-Martinelli separated-flow multiplier ----------
#
# SOURCE CONSULTED. Collier, J.G. & Thome, J.R., "Convective Boiling and Condensation",
# 3rd ed., Sec. 2.4 "The separated flow model", pp. 49-55, read from the RENDERED PAGES.
#
# ** A LIMITATION OF THE FILE, NOT OF THE SOURCE. ** The PDF's embedded text layer is
# degraded: automated extraction drops subscripts and operators, returning things like
# "1 + _ + _2" for a perfectly clear printed equation. The printed pages themselves are
# sharp. So anything taken from this source must be read from the rendered page, and an
# extraction is a transcription -- just one nobody typed.
#
# READ FROM THE PAGE and implemented as printed:
#   * Eq. (2.68), p. 53: phi_f^2 = 1 + C/X + 1/X^2
#   * Eq. (2.69), p. 53: phi_g^2 = 1 + C X + X^2
#   * Eq. (2.67), p. 52: X^2 = (dp/dz F)_f / (dp/dz F)_g, liquid-alone over gas-alone
#   * The Chisholm C table (p. 53): tt 20, vt 12, tv 10, vv 5. These MATCH the repo's
#     pinned CHISHOLM_C exactly -- an independent confirmation of an S1 value.
#
# INDEPENDENT CONFIRMATION of (2.68), retained because it is a real cross-check:
#   By definition phi_f^2 = (dp/dz)_TP/(dp/dz)_f and phi_g^2 = (dp/dz)_TP/(dp/dz)_g, so
#   with (2.67), phi_g^2 = phi_f^2 X^2. Substituting the printed (2.69):
#       phi_f^2 = (1 + C X + X^2)/X^2 = 1 + C/X + 1/X^2
#   which reproduces the printed (2.68) exactly. The identity is asserted as a test.
#   It confirms the printed equation; it is not the equation's source.
#
# ** THE VALIDITY STATEMENT, VERBATIM (p. 54) **
#   "The correlation was developed for horizontal two-phase flow of two-component
#    systems at low pressures (close to atmospheric) and its application to situations
#    outside this range of conditions is not recommended."
#
# Three axes, all explicit -- horizontal, two-component, near-atmospheric -- and no
# number is given for "close to atmospheric". They are declared on the entry and are
# what makes it a machine-visible blocker for this project's loop, which is
# single-component ammonia, not horizontal, and runs to 20 bar.
#
# ** WHAT CHISHOLM (1967) ACTUALLY DOES -- and why the entry is still blocked. **
# The S3 handoff presumed Chisholm (1967) is the extension past those conditions. The
# source does not support that. Collier & Thome attribute:
#   * Chisholm (1967), p. 52 -- "has corrected the above treatment by allowing for the
#     INTERFACIAL SHEAR FORCE (S) between the phases": it fixes the annular-flow
#     void-fraction inconsistency, not the validity range.
#   * Chisholm (1963), p. 54 -- supplies C = 1.36 at the CRITICAL pressure level, used
#     inside Martinelli-Nelson's construction.
#   * Martinelli-Nelson (1948), p. 54 -- IS the single-component / pressure extension
#     ("enable the application of the model to single component systems"), with
#     tabulated phi_lo from 1.01 to 221.2 bar (Table 2.2).
# So the route from "horizontal, two-component, atmospheric" to this project's loop is
# Martinelli-Nelson (1948) -- which is not in the registry, not in hand, and not what
# ruling A4 names. Under C1 it is not reconstructed. The gap is the deliverable.

#: Flow-regime labels for selecting the Chisholm ``C`` (Collier & Thome p. 53).
CHISHOLM_REGIMES = ("turbulent", "laminar")


def chisholm_C(liquid_regime: str, gas_regime: str) -> float:
    """The Chisholm constant ``C`` for a regime pair (Collier & Thome p. 53 table).

    The source names the regimes viscous/turbulent; the registry's pinned
    ``CHISHOLM_C`` uses laminar/turbulent for the same distinction, and the four values
    (20, 12, 10, 5) agree with the printed table exactly.
    """
    key = (liquid_regime.strip().lower(), gas_regime.strip().lower())
    if key not in CHISHOLM_C:
        raise ValueError(
            f"no Chisholm C for regime pair {key}; the source tabulates only "
            f"{sorted(CHISHOLM_C)}"
        )
    return CHISHOLM_C[key]


def martinelli_parameter_X(dp_dz_liquid: float, dp_dz_gas: float) -> float:
    """Martinelli parameter ``X`` from the two single-phase gradients (Eq. 2.67).

    ``X^2 = (dp/dz)_f / (dp/dz)_g`` -- each phase considered to flow alone in the
    channel. Both gradients must be positive.
    """
    if dp_dz_liquid <= 0.0 or dp_dz_gas <= 0.0:
        raise ValueError(
            f"both single-phase gradients must be positive to form X; got "
            f"liquid={dp_dz_liquid}, gas={dp_dz_gas}"
        )
    return math.sqrt(dp_dz_liquid / dp_dz_gas)


def lockhart_martinelli_phi_f2(X: float, C: float) -> float:
    """Liquid-based two-phase multiplier ``phi_f^2 = 1 + C/X + 1/X^2`` (Eq. 2.68).

    Multiplies the **liquid-alone** frictional gradient. Read from the printed page;
    the identity ``phi_g^2 = phi_f^2 X^2`` independently confirms it against the
    printed (2.69) and is asserted as a test.
    """
    if X <= 0.0:
        raise ValueError(f"Martinelli parameter X must be positive, got {X}")
    return 1.0 + C / X + 1.0 / X**2


def lockhart_martinelli_phi_g2(X: float, C: float) -> float:
    """Gas-based two-phase multiplier ``phi_g^2 = 1 + C X + X^2`` (Eq. 2.69, legible)."""
    if X <= 0.0:
        raise ValueError(f"Martinelli parameter X must be positive, got {X}")
    return 1.0 + C * X + X**2


def lockhart_martinelli_frictional_gradient(
    *, dp_dz_liquid: float, dp_dz_gas: float, liquid_regime: str, gas_regime: str
) -> float:
    """Two-phase frictional pressure gradient, Pa/m, by the separated-flow model.

    ``(dp/dz)_TP = phi_f^2 (dp/dz)_f``. Performs **no** applicability checking: the
    entry's declared axes -- horizontal, two-component, near-atmospheric -- are
    enforced by the caller through ``applicability_spec``, and for this project's loop
    they do not hold.
    """
    X = martinelli_parameter_X(dp_dz_liquid, dp_dz_gas)
    C = chisholm_C(liquid_regime, gas_regime)
    return lockhart_martinelli_phi_f2(X, C) * dp_dz_liquid


def accelerational_pressure_drop(
    *,
    mass_flux_kg_m2s: float,
    quality_in: float,
    quality_out: float,
    rho_f: float,
    rho_g: float,
) -> float:
    """Acceleration pressure drop across a section, Pa (S0 Sec. 3).

    The momentum change as the mixture accelerates while evaporating, in the
    homogeneous (equal-velocity) limit::

        dP_accel = G^2 [ (x/rho_g + (1-x)/rho_f)_out - (...)_in ]

    Stated in the homogeneous limit deliberately: the separated-flow acceleration term
    needs a void fraction, and the void-fraction relation in the consulted source is
    the one Collier & Thome show to be INCONSISTENT for annular flow (p. 52, the
    discrepancy Chisholm (1967) corrects and which is not in hand). Using the
    homogeneous limit is a named modelling choice with a stated direction of error,
    rather than a separated-flow void fraction the source itself disowns.
    """
    def _v(x: float) -> float:
        return x / rho_g + (1.0 - x) / rho_f

    return mass_flux_kg_m2s**2 * (_v(quality_out) - _v(quality_in))


def static_pressure_drop(
    *,
    rho_mixture_kg_m3: float,
    height_m: float,
    gravity_m_s2: float = STANDARD_GRAVITY_M_S2,
) -> float:
    """Static (gravitational) pressure drop ``rho g h``, Pa (Director ruling D12).

    **This term IS gravity**, and in orbit it is exactly zero -- not small, zero. D12
    nonetheless makes gravity an *enforced applicability axis* rather than letting the
    term be dropped: omitting it would build a microgravity model out of a 1g-derived
    frictional correlation whose error there is unvalidated and probably
    non-conservative (DEBTS D-7), leaving a model microgravity-exact in one term and
    terrestrial in the next with nothing marking the seam.

    So this computes ``rho g h`` honestly at the gravity it is given, and the
    applicability axis on the entry is what refuses a case whose gravity the
    frictional correlation cannot speak to. Omission makes it silently microgravity;
    enforcement makes it loudly terrestrial.
    """
    if gravity_m_s2 <= 0.0:
        raise ValueError(
            f"static head is evaluated at g = {gravity_m_s2} m/s^2. The term is exactly "
            "zero in free fall, but the frictional correlation it is added to is "
            "1g-derived, so the loop as a whole is not evaluable there: treat the case "
            "as out of applicability rather than summing a microgravity-exact term "
            "with a terrestrial one (Director ruling D12)."
        )
    return rho_mixture_kg_m3 * gravity_m_s2 * height_m


def pump_inlet_subcooling_margin(
    *, saturation_temperature_K: float, inlet_temperature_K: float
) -> float:
    """Pump-inlet subcooling margin ``T_sat(P_inlet) - T_inlet``, K (ruling D8).

    Positive means the inlet is subcooled liquid and the pump is fed liquid; zero or
    negative means the fluid is at or past saturation at the inlet, which is the
    cavitation condition this criterion exists to exclude.

    The criterion is the AMS-02 Tracker Thermal Control System's, a mechanically pumped
    two-phase loop flying since 2011, whose condenser exit state guarantees the fluid
    "is sub-cooled well below the saturation point so arrives in liquid phase back at
    the pump". It is a **feasibility** criterion, not a pump-selection one: see the
    entry's source note for why the quantitative NPSHA/NPSH3 route is recorded and not
    implemented, and for the NPSH3 warning any future guard must carry.
    """
    return saturation_temperature_K - inlet_temperature_K


#: Enforceable applicability of Lockhart-Martinelli/Chisholm, taken verbatim from the
#: validity statement on p. 54 of the consulted source.
LOCKHART_MARTINELLI_APPLICABILITY = Applicability(
    compositions=frozenset({"two_component"}),
    compositions_basis=(
        "Collier & Thome Sec. 2.4 p. 54, verbatim: 'The correlation was developed for "
        "horizontal two-phase flow of TWO-COMPONENT systems at low pressures (close to "
        "atmospheric) and its application to situations outside this range of "
        "conditions is not recommended.' This project's loop is SINGLE-component "
        "(ammonia boiling in its own vapour), so every case is outside it. The route to "
        "single-component systems named by the same source is Martinelli-Nelson (1948), "
        "which is not in the registry and not in hand."
    ),
    geometries=frozenset({"round_tube"}),
    geometries_basis=(
        "The Martinelli studies were of flow in horizontal TUBES (Sec. 2.4.3). Narrowed "
        "to round_tube, consistent with Director ruling D9."
    ),
    orientations=frozenset({"horizontal"}),
    orientations_basis=(
        "Collier & Thome p. 54, same sentence: developed for HORIZONTAL flow. The "
        "static-head term is identically zero for horizontal flow, which is why the "
        "correlation could ignore it -- and is exactly why applying it to a "
        "non-horizontal loop needs the static term back (Director ruling D12)."
    ),
    gravity_explicit=False,
    gravity_basis=(
        "The frictional multiplier itself carries no g -- unlike Shah (1987), whose Y "
        "divides by it. But the correlation's database is terrestrial and the loop it "
        "is used in has a static head, so gravity is declared and enforced here too "
        "(D12): consistency between the two legs is the point of the ruling."
    ),
    reference_gravity_m_s2=STANDARD_GRAVITY_M_S2,
    numeric_domain_provenance=DomainProvenance.UNESTABLISHED,
    numeric_domain_note=(
        "The declared P_Pa ceiling of 2e6 Pa is NOT traceable to the source. Collier & "
        "Thome say only 'close to atmospheric' and give no number, so no numeric "
        "ceiling can be attributed to them -- and none is invented to replace it. The "
        "range is retained as an enforced guard under Director ruling D1 and labelled "
        "provenance-unestablished. The composition and orientation axes above are the "
        "constraints that actually bite for this project, and those ARE verbatim."
    ),
    unenforced_axes=(
        "the pressure ceiling: 'close to atmospheric' is qualitative in the source, so "
        "the numeric bound is enforced but unattributable rather than replaced by a "
        "chosen number (C1).",
    ),
)


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
        applicability_spec=GW86_APPLICABILITY,
        applicability="Reference flow-boiling HTC (executable). Applicability is "
        "ENFORCED, not annotated, via applicability_spec: seven-fluid development "
        "database (ammonia excluded), round-tube/annulus geometry, vertical "
        "orientation, and a liquid-Reynolds turbulence guard on the Dittus-Boelter "
        "base. The five numeric limits are additionally enforced by assert_in_domain "
        "but are labelled PROVENANCE-UNESTABLISHED -- they are not the authors' "
        "declared range. The horizontal Froude/stratification de-rating is "
        "deliberately not implemented (1g effect; see module note).",
        note="reference HTC for two-phase ranking; 1g basis (see limitation); executable "
        "form confirmed by three independent printings (see source locator)",
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
        formula="phi_f^2 = 1 + C/X + 1/X^2 (Eq. 2.68, as printed); phi_g^2 = 1 + C X + "
        "X^2 (Eq. 2.69); X^2 = (dp/dz)_f/(dp/dz)_g (Eq. 2.67); C from the pinned "
        "CHISHOLM_C table",
        # Retained and enforced, but NOT traceable to the source -- see the spec's
        # numeric_domain_note. The source says only "close to atmospheric".
        domain=Domain(ranges={"P_Pa": (0.1e6, 2.0e6)}),
        source=_LOCKHART_MARTINELLI,
        evaluate=lockhart_martinelli_frictional_gradient,
        applicability_spec=LOCKHART_MARTINELLI_APPLICABILITY,
        applicability="Reference two-phase frictional dP (S3 executable). The multiplier "
        "and the Chisholm C values are SOURCED. Its declared applicability is verbatim "
        "from the source -- HORIZONTAL, TWO-COMPONENT, near-atmospheric -- and this "
        "project's loop meets NONE of the three: single-component ammonia, "
        "non-horizontal, to 20 bar. So the entry is implemented as far as the sourced "
        "form allows and REFUSES outside it; every case here is a machine-visible "
        "blocker. The extension the handoff expected from Chisholm (1967) does not "
        "exist: that paper corrects the interfacial-shear/void-fraction inconsistency. "
        "The single-component route named by the same source is Martinelli-Nelson "
        "(1948), which is not in the registry and not in hand.",
        note="reference dP; Chisholm C = CHISHOLM_C keyed by (liquid_regime, gas_regime), "
        "confirmed against the source table; validity axes are the blocker, not the maths",
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
        name="Shah (2015) CHF -- ambiguous citation, superseded as the reference",
        kind="chf",
        provenance=Provenance.UNSUPPORTED,
        # OTB-G001 F-03: was RESOLVED and passed the generic rank-eligibility guard
        # despite having no evaluator, no locator, an ambiguous citation and a domain
        # belonging to a different paper. Now SOURCE_REQUIRED, so it cannot rank.
        status=Status.SOURCE_REQUIRED,
        formula="(no executable form; citation could not be resolved to a single paper)",
        # DOMAIN DETACHED (F-03b). The pr_reduced 0.0014-0.96 band was never this
        # entry's: it is Shah (1987)'s database range and has been re-attributed to
        # two_phase.chf.shah_1987. Leaving it here would keep asserting a validity
        # range this entry has no claim to.
        domain=Domain(),
        source=_SHAH_2015,
        evaluate=None,
        applicability="NOT rank-eligible and NOT the CHF reference. Superseded by "
        "two_phase.chf.shah_1987 under Director ruling D3. The citation resolves to no "
        "single paper (two distinct 2015 Shah CHF papers exist, for annuli and for "
        "horizontal channels), and the pr_reduced band formerly attached here belongs "
        "to Shah (1987) and has been re-attributed. Kept as a registered, blocked "
        "entry rather than deleted so the misattribution stays visible.",
        note="SOURCE_REQUIRED: ambiguous citation, no executable form, domain detached "
        "and re-attributed to shah_1987 (OTB-G001 F-03); locator intentionally blank",
        **_MICROGRAVITY_1G,
    ),
    CorrelationEntry(
        id="two_phase.chf.shah_1987",
        name="Shah (1987) CHF in uniformly heated vertical tubes (CHF reference)",
        kind="chf",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="Bo_crit = min(UCC, LCC) per Shah's selection rule; "
        "q_crit = Bo_crit G h_fg. UCC: Bo = 0.124 (D/L_E)^0.89 (1e4/Y)^n (1-x_IE). "
        "LCC: Bo = F_E Fx Bo0. Y = (G D cp_f/k_f)(G^2/(rho_f^2 g D))^0.4 "
        "(mu_f/mu_g)^0.6 -- GRAVITY-EXPLICIT.",
        # Re-attributed from shah_2015 (F-03b), where this band never belonged.
        # pr_reduced and diameter are AGREED by both printings; mass velocity and
        # critical quality are CONFLICTED and resolved to Shah (2023). See the entry's
        # applicability_spec for the conflict record.
        domain=Domain(
            ranges={
                "pr_reduced": (0.0014, 0.96),
                "D_m": (0.315e-3, 37.5e-3),
                "G_kg_m2s": (4.0, 2905.0),
                "critical_quality": (-0.26, 0.96),
                # F-06: unbounded inlet quality let x_in = -1000 inflate CHF ~1000x
                # and still report sourced. Enforced at the tighter bound; see
                # SHAH_1987_INLET_QUALITY_NOTE for the true provenance.
                "inlet_quality": (-2.6, 0.85),
            }
        ),
        source=_SHAH_1987,
        evaluate=shah_1987_chf,
        applicability_spec=SHAH_1987_APPLICABILITY,
        applicability="CHF reference (Director ruling D3). Applicability is ENFORCED "
        "via applicability_spec: round-tube geometry, vertical upflow, ammonia "
        "excluded, and a GRAVITY-EXPLICIT guard -- Y divides by g, so this correlation "
        "has no microgravity limit and cannot be evaluated at g <= 0. Feeds the "
        "q''/CHF <= 0.5 rank band on the LOCAL modeled wall flux (ruling A5). "
        "Evaluating it also requires sourced channel geometry (L and D); geometry is "
        "source-required per DEBTS D-5, so a case without it is blocked.",
        note="CHF reference, promoted from sensitivity by ruling D3; executable form "
        "reconciled across two printings with five divergences recorded (see source note)",
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
        name="Pump-inlet liquid feasibility (subcooling margin)",
        kind="npsh",
        provenance=Provenance.PUBLISHED,
        status=Status.RESOLVED,
        formula="dT_sub = T_sat(P_inlet) - T_inlet > 0; feasible when the margin is "
        "positive and the inlet state is liquid",
        domain=Domain(),
        source=_NPSH,
        evaluate=pump_inlet_subcooling_margin,
        applicability="Pump-inlet cavitation feasibility as a SUBCOOLING MARGIN "
        "(Director ruling D8), on the AMS-02 flight precedent. Moved off "
        "SOURCE_REQUIRED. The quantitative NPSHA/NPSH3 route is recorded in the source "
        "note and deliberately NOT implemented: it needs a specific pump, and none is "
        "selected. A future NPSHR guard must enforce a margin over NPSH3, never "
        "equality -- NPSH3 is already 3 % head loss to cavitation.",
        note="subcooling margin at the pump inlet; NPSHR route recorded, not implemented "
        "(DEBTS D-4)",
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

#: Kinds that are feasibility CRITERIA rather than fitted correlations. They are
#: exempt from the "rank-eligible entries must declare a numeric domain" rule: a
#: subcooling margin is a sign test, not a fit with a validity window, and inventing a
#: range for it to satisfy a structural checker is exactly what C1 forbids.
_CRITERION_KINDS = frozenset({"npsh", "onb"})


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

            # 3) a rank-eligible *fitted correlation* must state a validity domain.
            #    Criteria are exempt and named here rather than silently skipped: a
            #    subcooling margin is a sign test on a physical quantity, not a fit with
            #    a range of applicability, so demanding a numeric domain of it would
            #    force an invented one (C1).
            if e.rank_eligible and not e.domain.ranges and e.kind not in _CRITERION_KINDS:
                problems.append(f"{e.id}: rank-eligible correlation with empty Domain")

    return problems

