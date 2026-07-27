"""Assess whether a candidate pressure-drop correlation's declared basis reaches this
loop -- and, separately, whether its evidence *for this project's fluid* reaches it.

**This module assesses. It adopts nothing.** Director ruling, S4 scope decision 7, is
*"Assess Kim & Mudawar first"*; decision 11 (settled decision **A4**) leaves
Lockhart-Martinelli/Chisholm as the reference pressure-drop correlation and Friedel as
the named sensitivity. Registering a candidate as a **sensitivity** needs no amendment;
rank-eligibility would, and there is none. Nothing here makes anything rank-eligible.

Why it is a module and not a paragraph in a report
--------------------------------------------------
Two claims about a correlation look alike and are not:

* *"ammonia is in its fluid list"* -- a fact about a list, and
* *"its ammonia data lie where this loop operates"* -- a fact about a database.

The first is cheap and is what a validity box reports. The second is what actually
licenses use, and it can only be had by computing the overlap. The project has a
recorded failure of exactly this shape (**DEBTS D-1**: a validity bound taken from a
single secondary tabulation and then found in none of twenty-one consulted sources),
and the S4 scope proposal names the same hazard against an unobtained source -- *"a
fluid list is not a coverage map"*. So the distinction is computed here, executably,
rather than asserted in prose that nothing can falsify.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from .registry import get

#: Saturated liquid and vapour ammonia viscosity at 20 bar, from the pinned CoolProp
#: backend. Defaults so an assessment cannot quietly proceed without the properties
#: the Reynolds axes need -- omitting them is what let those axes go unapplied.
_AMMONIA_MU_F_20BAR = 1.044729e-4
_AMMONIA_MU_G_20BAR = 1.0e-5

#: The assessed candidate. Named once so the rest of the module is about the question
#: rather than about one paper.
KIM_MUDAWAR_ID = "two_phase.dp.kim_mudawar_2013"

#: The A4 reference, for the comparison that gives the assessment its point.
REFERENCE_DP_ID = "two_phase.dp.lockhart_martinelli_chisholm"


@dataclass(frozen=True)
class FluidEvidence:
    """Where one fluid's data actually sit inside a consolidated database.

    Read from the source's per-source breakdown, not from its summary box.
    """

    fluid: str
    #: Bores at which that fluid was measured, m.
    diameters_m: tuple[float, ...]
    #: Mass-flux range of that fluid's rows, kg/m^2s.
    mass_flux_min_kg_m2s: float
    mass_flux_max_kg_m2s: float
    #: How many of the consolidated points are this fluid's, and out of how many.
    points: int
    total_points: int
    orientation: str
    geometry: str
    locator: str

    @property
    def share_of_database(self) -> float:
        return self.points / self.total_points


#: Kim & Mudawar (2013) Table 3, p. 723, the Maqbool et al. [33] row -- the ONLY
#: ammonia row in the consolidated database. Read from the rendered page.
MAQBOOL_AMMONIA_EVIDENCE = FluidEvidence(
    fluid="ammonia",
    diameters_m=(1.224e-3, 1.70e-3),
    mass_flux_min_kg_m2s=100.0,
    mass_flux_max_kg_m2s=500.0,
    points=235,
    total_points=2378,
    orientation="vertical_upflow",
    geometry="round_tube",
    locator="Kim & Mudawar (2013), Table 3, p. 723, row 'Maqbool et al. [33]'",
)


@dataclass(frozen=True)
class Interval:
    """A closed bore interval, or the empty interval."""

    lo_m: float
    hi_m: float

    @property
    def is_empty(self) -> bool:
        return not (self.lo_m <= self.hi_m)

    def intersect(self, other: Interval) -> Interval:
        return Interval(max(self.lo_m, other.lo_m), min(self.hi_m, other.hi_m))

    def __str__(self) -> str:
        if self.is_empty:
            return "(empty)"
        return f"{self.lo_m * 1e3:.4g}-{self.hi_m * 1e3:.4g} mm"


@dataclass(frozen=True)
class OperatingContext:
    """The loop state an assessment is made against.

    Every declared axis of a mini/micro-channel pressure-drop correlation is a
    function of bore *and* of this state, so an assessment that does not carry the
    state can only apply the axes that happen not to need it -- which is precisely how
    an axis gets silently dropped.
    """

    mass_flow_kg_s: float
    reduced_pressure: float
    mu_f: float
    mu_g: float
    quality: float


#: How to evaluate each declared axis at a bore. Keyed by the range names a registry
#: entry may declare.
#:
#: **Every declared range must have an entry here.** A declared axis with no evaluator
#: raises rather than being skipped: the first version of this module applied ``D_h_m``,
#: ``G_kg_m2s`` and ``P_R`` and silently ignored ``Re_fo``, ``Re_f``, ``Re_g`` and
#: ``x`` -- all four of which the entry declares. ``Re_fo`` binds at SMALL bore, so
#: ignoring it reported an admitted window 2.2 mm too wide at the low end, in the
#: direction of over-claiming applicability. Hand-picking axes is the defect; requiring
#: an evaluator for each is the fix.
_AXIS_EVALUATORS: dict[str, Callable[[float, OperatingContext], float]] = {
    "D_h_m": lambda d, ctx: d,
    "G_kg_m2s": lambda d, ctx: _mass_flux(d, ctx),
    "Re_fo": lambda d, ctx: _mass_flux(d, ctx) * d / ctx.mu_f,
    "Re_f": lambda d, ctx: _mass_flux(d, ctx) * (1.0 - ctx.quality) * d / ctx.mu_f,
    "Re_g": lambda d, ctx: _mass_flux(d, ctx) * ctx.quality * d / ctx.mu_g,
    "x": lambda d, ctx: ctx.quality,
    "P_R": lambda d, ctx: ctx.reduced_pressure,
}


def _mass_flux(diameter_m: float, ctx: OperatingContext) -> float:
    return 4.0 * ctx.mass_flow_kg_s / (math.pi * diameter_m * diameter_m)


def _admits(
    diameter_m: float,
    ranges: dict[str, tuple[float, float]],
    ctx: OperatingContext,
    *,
    applied: set[str] | None = None,
) -> bool:
    """Whether every declared range admits this bore. All axes, or it raises.

    ``applied`` collects the axes actually evaluated, so that what an assessment
    reports having applied is a **fact about this loop** rather than a copy of the
    declared range keys. Reporting the declaration would be the same shape of defect
    as the one this module was corrected for -- an assessment that says it used seven
    axes while using three would be indistinguishable from one that used seven.

    Deliberately no early return: a short-circuit would record only the axes checked
    before the first refusal, which would make ``applied`` depend on dict order.
    """
    ok = True
    for name, (lo, hi) in ranges.items():
        evaluator = _AXIS_EVALUATORS.get(name)
        if evaluator is None:
            raise ValueError(
                f"the entry declares a validity range on {name!r} and this module has "
                "no evaluator for it, so the axis would be silently ignored and the "
                "admitted window reported too wide. Add an evaluator or remove the "
                "declared range; do not assess around it."
            )
        if applied is not None:
            applied.add(name)
        if not lo <= evaluator(diameter_m, ctx) <= hi:
            ok = False
    return ok


def _admitted_interval(
    ranges: dict[str, tuple[float, float]],
    ctx: OperatingContext,
    *,
    applied: set[str] | None = None,
    search_lo_m: float = 1.0e-5,
    search_hi_m: float = 1.0,
    samples: int = 2001,
) -> Interval:
    """The bores every declared range admits, found by scan and refined by bisection.

    Deliberately **not** inverted analytically. Each axis is monotone in bore, but in
    different directions -- ``G`` and the three Reynolds numbers fall as bore rises
    while ``D_h`` rises with it -- and reasoning about which way each one binds is
    exactly the step that went wrong. Scanning cannot get the direction backwards.
    """
    # Log-spaced: the search spans five decades of bore and the admitted window can be
    # a fraction of a millimetre, so uniform spacing would either miss it or be
    # enormous. The scan only has to LAND in the window; bisection supplies the
    # precision, so the grid is sized for detection rather than for accuracy.
    ratio = (search_hi_m / search_lo_m) ** (1.0 / (samples - 1))
    grid = [search_lo_m * ratio**i for i in range(samples)]
    ok = [d for d in grid if _admits(d, ranges, ctx, applied=applied)]
    if not ok:
        return Interval(1.0, 0.0)  # empty

    def refine(inside: float, outside: float) -> float:
        for _ in range(80):
            mid = 0.5 * (inside + outside)
            if _admits(mid, ranges, ctx):
                inside = mid
            else:
                outside = mid
        return inside

    lo, hi = ok[0], ok[-1]
    below = [d for d in grid if d < lo]
    above = [d for d in grid if d > hi]
    if below:
        lo = refine(lo, below[-1])
    if above:
        hi = refine(hi, above[0])
    return Interval(lo, hi)


def _bores_for_mass_flux(mass_flow_kg_s: float, g_lo: float, g_hi: float) -> Interval:
    """Bores whose mass flux falls in ``[g_lo, g_hi]`` at a fixed mass flow.

    ``G = m_dot/(pi D^2/4)`` falls as ``D`` rises, so the mass-flux ceiling sets the
    **lower** bore bound and the floor sets the upper one. Getting that inversion
    backwards silently widens the window, which is why it is written once here.
    """
    if not (mass_flow_kg_s > 0.0 and 0.0 < g_lo <= g_hi):
        raise ValueError("mass flow and both mass-flux bounds must be positive")
    d_lo = math.sqrt(4.0 * mass_flow_kg_s / (math.pi * g_hi))
    d_hi = math.sqrt(4.0 * mass_flow_kg_s / (math.pi * g_lo))
    return Interval(d_lo, d_hi)


@dataclass(frozen=True)
class BasisAssessment:
    """What a candidate's declared basis admits, and what its fluid evidence supports."""

    entry_id: str
    swept_band: Interval
    #: Bores admitted by the declared box (bore axis AND mass-flux axis together).
    admitted: Interval
    #: Bores at which this loop's mass flux would match the fluid's measured fluxes.
    fluid_flux_matched: Interval
    #: The hull of the bores the fluid was actually measured at.
    fluid_bore_hull: Interval
    #: Both at once: a bore at which this loop is inside the fluid's measured bore
    #: range **and** its measured mass-flux range.
    fluid_supported: Interval
    evidence: FluidEvidence
    reduced_pressure: float
    reduced_pressure_in_basis: bool
    mass_flow_kg_s: float
    #: The vapour quality the assessment was made at. Load-bearing: two declared axes
    #: depend on it and the admitted window can be empty on either side.
    quality: float = 0.0
    #: Every declared range that was applied. Reported so a reader can see that the
    #: assessment used the whole declared box rather than the part of it that was
    #: convenient.
    applied_axes: tuple[str, ...] = ()

    @property
    def flux_matched_within_admitted(self) -> Interval:
        """Admitted bores where this loop's mass flux also matches the fluid's.

        A weaker condition than :attr:`fluid_supported` and a different one, reported
        separately because the two are easy to confuse and only one of them is
        evidence. This asks whether the loop's mass flux lands in the range the fluid
        was measured over, *ignoring the bores it was measured at*.
        """
        return self.admitted.intersect(self.fluid_flux_matched)

    @property
    def admits_part_of_the_band(self) -> bool:
        """Whether the declared basis reaches this project's band at all."""
        return (
            not self.admitted.is_empty
            and not self.admitted.intersect(self.swept_band).is_empty
            and self.reduced_pressure_in_basis
        )

    @property
    def fluid_evidence_reaches_the_admitted_window(self) -> bool:
        """Whether the assessed fluid's data overlap the region the box admits.

        The distinction criterion S4-9 exists for. ``admits_part_of_the_band`` can be
        true while this is false, and when it is, the correlation would be applied to
        this fluid outside where this fluid was measured -- on the strength of the
        other fluids in the database.

        **Both axes must hold at the same bore.** Matching the fluid's mass-flux range
        at some bore is not enough if that bore is nowhere near the bores the fluid was
        measured at: mass flux and diameter are independent coordinates of the
        database, and satisfying them at different bores satisfies neither anywhere.
        """
        return not self.fluid_supported.intersect(self.admitted).is_empty

    def summary(self) -> str:
        band = self.admitted.intersect(self.swept_band)
        return (
            f"{self.entry_id}: at x = {self.quality:.4g}, declared basis admits {band} "
            f"of the swept {self.swept_band}; P_R = {self.reduced_pressure:.4g} "
            f"{'inside' if self.reduced_pressure_in_basis else 'OUTSIDE'} the declared "
            f"range; axes applied: {', '.join(self.applied_axes)}. "
            f"{self.evidence.fluid} evidence ({self.evidence.points} of "
            f"{self.evidence.total_points} points) was measured at bores "
            f"{self.fluid_bore_hull} and G {self.evidence.mass_flux_min_kg_m2s:g}-"
            f"{self.evidence.mass_flux_max_kg_m2s:g} kg/m2s. Of the admitted window, "
            f"{self.flux_matched_within_admitted} matches that MASS-FLUX range; the "
            f"region matching BOTH its mass-flux range and its measured bores is "
            f"{self.fluid_supported}"
        )


def assess_declared_basis(
    *,
    entry_id: str = KIM_MUDAWAR_ID,
    mass_flow_kg_s: float,
    band_min_m: float,
    band_max_m: float,
    reduced_pressure: float,
    quality: float,
    mu_f: float = _AMMONIA_MU_F_20BAR,
    mu_g: float = _AMMONIA_MU_G_20BAR,
    evidence: FluidEvidence = MAQBOOL_AMMONIA_EVIDENCE,
) -> BasisAssessment:
    """Compute what a candidate's declared basis admits of a swept bore band.

    **Every** declared range binds, not a chosen subset. A bore band, a mass-flux
    band and a Reynolds band are the same constraint seen from three sides, and they
    bind from opposite ends -- ``D_h`` from above, ``G`` and the Reynolds numbers from
    below -- so applying some of them is how a validity box gets over-read.

    ``quality`` has **no default**, and that is deliberate. Two of the declared axes,
    ``Re_f = G(1-x)D/mu_f`` and ``Re_g = GxD/mu_g``, are functions of it, and the
    admitted window moves from empty to several millimetres wide and back again across
    ``0 < x < 1``. There is no neutral value to assume: assuming one would make the
    reported window an artifact of the assumption, which is the shape of defect this
    module exists to prevent.
    """
    entry = get(entry_id)
    ranges = dict(entry.domain.ranges)
    if not ranges:
        raise ValueError(
            f"{entry_id} declares no validity ranges, so there is no basis to assess; "
            "assessing it anyway would invent the bounds"
        )

    ctx = OperatingContext(
        mass_flow_kg_s=mass_flow_kg_s,
        reduced_pressure=reduced_pressure,
        mu_f=mu_f,
        mu_g=mu_g,
        quality=quality,
    )
    applied: set[str] = set()
    admitted = _admitted_interval(ranges, ctx, applied=applied)

    # Where THIS fluid was actually measured, in the same bore coordinate. Two
    # independent constraints, and the supported region is where both hold at once.
    flux_matched = _bores_for_mass_flux(
        mass_flow_kg_s,
        evidence.mass_flux_min_kg_m2s,
        evidence.mass_flux_max_kg_m2s,
    )
    bore_hull = Interval(min(evidence.diameters_m), max(evidence.diameters_m))
    p_lo, p_hi = ranges.get("P_R", (float("-inf"), float("inf")))

    return BasisAssessment(
        entry_id=entry_id,
        swept_band=Interval(band_min_m, band_max_m),
        admitted=admitted,
        fluid_flux_matched=flux_matched,
        fluid_bore_hull=bore_hull,
        fluid_supported=flux_matched.intersect(bore_hull),
        evidence=evidence,
        reduced_pressure=reduced_pressure,
        reduced_pressure_in_basis=p_lo <= reduced_pressure <= p_hi,
        mass_flow_kg_s=mass_flow_kg_s,
        quality=quality,
        applied_axes=tuple(sorted(applied)),
    )


def qualities_admitting_any_bore(
    *,
    entry_id: str = KIM_MUDAWAR_ID,
    mass_flow_kg_s: float,
    band_min_m: float,
    band_max_m: float,
    reduced_pressure: float,
    mu_f: float = _AMMONIA_MU_F_20BAR,
    mu_g: float = _AMMONIA_MU_G_20BAR,
    samples: int = 201,
) -> tuple[float, float] | None:
    """The vapour qualities at which the declared basis admits **some** bore in the band.

    Reported because "this correlation does not reach this loop" and "this correlation
    does not reach anything" are different statements, and the first is only worth
    saying with the second ruled out.

    Returns a **quality** pair, not an :class:`Interval` -- ``Interval`` renders itself
    in millimetres, and a quality printed as "0.31 mm" would be a small trap left for
    whoever reads the output next.
    """
    ranges = dict(get(entry_id).domain.ranges)
    # Only non-emptiness is needed here, so the endpoints are not refined: bisecting
    # two boundaries per quality would be most of the work and none of the answer.
    ratio = (band_max_m / band_min_m) ** (1.0 / 400)
    bores = [band_min_m * ratio**i for i in range(401)]
    admitting = [
        i / (samples - 1)
        for i in range(samples)
        if any(
            _admits(
                d,
                ranges,
                OperatingContext(
                    mass_flow_kg_s, reduced_pressure, mu_f, mu_g, i / (samples - 1)
                ),
            )
            for d in bores
        )
    ]
    return (min(admitting), max(admitting)) if admitting else None


@dataclass(frozen=True)
class RefusalKind:
    """Whether a leg refuses because nothing covers it, or because nothing adopted it.

    Criterion **S4-8**. These are materially different claims about the world and only
    one of them can be true at a time; reporting the wrong one tells a reader that the
    literature is empty where it is not.
    """

    #: ``"policy"`` or ``"knowledge"``.
    kind: str
    detail: str
    #: The settled decision standing in the way, for a policy refusal.
    settled_decision: str = ""

    @property
    def is_policy(self) -> bool:
        return self.kind == "policy"


def classify_pressure_drop_refusal(
    assessment: BasisAssessment,
    *,
    admitting_qualities: tuple[float, float] | None = None,
) -> RefusalKind:
    """Classify the S4 pressure-drop refusal against the assessment that was computed.

    This is the D16 disclosure obligation in executable form. If the assessment finds
    the candidate's declared basis admits part of this project's space, the refusal is
    a **policy** refusal and must say so, naming A4 -- because a refusal reported
    without that distinction says no correlation exists for this corner, and one does.

    ``admitting_qualities`` is the quality range at which the candidate would admit
    some bore. It changes nothing about the classification and is reported inside a
    knowledge refusal, so that "does not reach THIS loop" is not read as "does not
    reach anything".
    """
    if not assessment.admits_part_of_the_band:
        elsewhere = (
            ""
            if admitting_qualities is None
            else (
                f" It is not empty everywhere: the same declared basis admits part of "
                f"the band at vapour qualities {admitting_qualities[0]:.2f}-"
                f"{admitting_qualities[1]:.2f}, which this loop does not reach at this "
                f"duty and flow. So the refusal is about THIS operating point, not "
                f"about the correlation."
            )
        )
        return RefusalKind(
            kind="knowledge",
            detail=(
                f"the assessed candidate {assessment.entry_id} does not reach this "
                f"operating space either, once its WHOLE declared basis is applied: "
                f"{assessment.summary()}. The refusal is therefore about what has been "
                f"published, not about what has been adopted.{elsewhere}"
            ),
        )

    admitted = assessment.admitted.intersect(assessment.swept_band)
    caveat = (
        ""
        if assessment.fluid_evidence_reaches_the_admitted_window
        else (
            f" AND A LIMIT THAT IS NOT SMALL. Two different overlaps, and they must "
            f"not be confused. (a) MASS FLUX ONLY: of the admitted window, "
            f"{assessment.flux_matched_within_admitted} carries a mass flux inside the "
            f"{assessment.evidence.mass_flux_min_kg_m2s:g}-"
            f"{assessment.evidence.mass_flux_max_kg_m2s:g} kg/m2s range the "
            f"{assessment.evidence.fluid} data were taken over -- a real but narrow "
            f"strip. (b) MASS FLUX AND BORE TOGETHER: those data were measured at "
            f"bores {assessment.fluid_bore_hull}, and this loop reaches their mass "
            f"fluxes only at {assessment.fluid_flux_matched}; the two do not meet, so "
            f"the region satisfying both is {assessment.fluid_supported}. A bore in "
            f"strip (a) matches the mass flux of the {assessment.evidence.fluid} rows "
            f"while sitting three times wider than any bore they were measured at, so "
            f"strip (a) is not {assessment.evidence.fluid} evidence for this loop. "
            f"Within the admitted window the candidate would be carried by its other "
            f"fluids."
        )
    )
    return RefusalKind(
        kind="policy",
        settled_decision="A4",
        detail=(
            f"THIS IS A POLICY REFUSAL, NOT AN ABSENCE OF KNOWLEDGE. The reference "
            f"correlation {REFERENCE_DP_ID} refuses on its own declared axes, but the "
            f"assessed candidate {assessment.entry_id} declares a basis that ADMITS "
            f"{admitted} of the swept {assessment.swept_band} at P_R = "
            f"{assessment.reduced_pressure:.4g}, on the same fluid and orientation. It "
            f"is registered as a SENSITIVITY and is not rank-eligible, because settled "
            f"decision A4 makes {REFERENCE_DP_ID} the reference and adopting another "
            f"would require amending it. Saying only 'no correlation applies' would be "
            f"false.{caveat}"
        ),
    )
