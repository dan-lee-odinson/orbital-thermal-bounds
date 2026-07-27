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
from dataclasses import dataclass

from .registry import get

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
            f"{self.entry_id}: declared basis admits {band} of the swept "
            f"{self.swept_band}; P_R = {self.reduced_pressure:.4g} "
            f"{'inside' if self.reduced_pressure_in_basis else 'OUTSIDE'} the declared "
            f"range; {self.evidence.fluid} evidence ({self.evidence.points} of "
            f"{self.evidence.total_points} points) was measured at bores "
            f"{self.fluid_bore_hull} and is mass-flux-matched here only at "
            f"{self.fluid_flux_matched}, so it supports {self.fluid_supported}, which "
            f"does {'' if self.fluid_evidence_reaches_the_admitted_window else 'NOT '}"
            f"overlap the admitted window"
        )


def assess_declared_basis(
    *,
    entry_id: str = KIM_MUDAWAR_ID,
    mass_flow_kg_s: float,
    band_min_m: float,
    band_max_m: float,
    reduced_pressure: float,
    evidence: FluidEvidence = MAQBOOL_AMMONIA_EVIDENCE,
) -> BasisAssessment:
    """Compute what a candidate's declared basis admits of a swept bore band.

    Both axes bind at once. The bore axis is read straight off the entry's declared
    ``D_h_m`` range; the mass-flux axis is converted into a bore interval at the stated
    mass flow, because a bore band and a mass-flux band are the same constraint seen
    from two sides and applying only one of them is how a box gets over-read.
    """
    entry = get(entry_id)
    ranges = entry.domain.ranges
    for required in ("D_h_m", "G_kg_m2s", "P_R"):
        if required not in ranges:
            raise ValueError(
                f"{entry_id} declares no {required} range, so its basis cannot be "
                "assessed on that axis; assessing it anyway would invent the bound"
            )

    d_lo, d_hi = ranges["D_h_m"]
    g_lo, g_hi = ranges["G_kg_m2s"]
    p_lo, p_hi = ranges["P_R"]

    admitted = Interval(d_lo, d_hi).intersect(
        _bores_for_mass_flux(mass_flow_kg_s, g_lo, g_hi)
    )
    # Where THIS fluid was actually measured, in the same bore coordinate. Two
    # independent constraints, and the supported region is where both hold at once.
    flux_matched = _bores_for_mass_flux(
        mass_flow_kg_s,
        evidence.mass_flux_min_kg_m2s,
        evidence.mass_flux_max_kg_m2s,
    )
    bore_hull = Interval(min(evidence.diameters_m), max(evidence.diameters_m))

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
    )


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


def classify_pressure_drop_refusal(assessment: BasisAssessment) -> RefusalKind:
    """Classify the S4 pressure-drop refusal against the assessment that was computed.

    This is the D16 disclosure obligation in executable form. If the assessment finds
    the candidate's declared basis admits part of this project's space, the refusal is
    a **policy** refusal and must say so, naming A4 -- because a refusal reported
    without that distinction says no correlation exists for this corner, and one does.
    """
    if not assessment.admits_part_of_the_band:
        return RefusalKind(
            kind="knowledge",
            detail=(
                f"the assessed candidate {assessment.entry_id} does not reach this "
                f"operating space either: {assessment.summary()}. The refusal is "
                "therefore about what has been published, not about what has been "
                "adopted."
            ),
        )

    admitted = assessment.admitted.intersect(assessment.swept_band)
    caveat = (
        ""
        if assessment.fluid_evidence_reaches_the_admitted_window
        else (
            f" AND A LIMIT THAT IS NOT SMALL: the {assessment.evidence.fluid} evidence "
            f"in that database was measured at bores {assessment.fluid_bore_hull}, "
            f"while this loop reaches its measured mass fluxes only at "
            f"{assessment.fluid_flux_matched}. Those do not meet, so there is NO bore "
            f"at which this loop sits inside both -- within the admitted window the "
            f"candidate would be carried entirely by its other fluids. Its declared "
            f"basis admits this case; its {assessment.evidence.fluid} data do not "
            f"reach it."
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
