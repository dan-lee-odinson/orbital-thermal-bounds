"""Ammonia property verification against the companion paper's NIST anchors.

The companion paper (doi:10.5281/zenodo.20670771) quotes these values from
the NIST Chemistry WebBook (SRD 69) and explicitly EXCLUDES them from its
assertion suite's verification scope. This file closes that gap: CoolProp's
HEOS backend computes the same quantities independently, and agreement
within the paper's display precision cross-validates both sources.

ORACLE-FREEZE RULE applies: the expected values below are the paper's
published NIST anchors. They are never edited to make a failing test pass.

Tolerances: the paper displays the saturation ladder to one decimal bar,
so saturation tests use abs=0.1 bar; critical point per its quoted
precision (405.5 K, "~113 bar").
"""

import pytest

pytest.importorskip("CoolProp", reason="CoolProp not installed")

from orbital_thermal import equilibrium_temperature
from orbital_thermal.fluids import (
    PA_PER_BAR,
    critical_margin,
    critical_pressure,
    critical_temperature,
    phase_state,
    provenance,
    saturated_densities,
    saturation_pressure,
)

# Paper anchors (NIST Chemistry WebBook SRD 69, as quoted in the paper)
T_CRIT_PAPER = 405.5        # K
P_CRIT_PAPER_BAR = 113.0    # bar, quoted as "~113 bar"
SAT_LADDER = {              # T (K) -> saturation pressure lower bound (bar)
    353.16: 41.4,
    358.91: 46.8,
    374.17: 63.8,
    391.47: 88.4,
}


class TestCriticalPoint:
    def test_critical_temperature_matches_nist_anchor(self):
        assert critical_temperature() == pytest.approx(T_CRIT_PAPER, abs=0.1)

    def test_critical_pressure_matches_nist_anchor(self):
        assert critical_pressure() / PA_PER_BAR == pytest.approx(
            P_CRIT_PAPER_BAR, abs=1.0
        )


class TestSaturationLadder:
    @pytest.mark.parametrize("T, P_bar", sorted(SAT_LADDER.items()))
    def test_paper_ladder_value(self, T, P_bar):
        assert saturation_pressure(T) / PA_PER_BAR == pytest.approx(
            P_bar, abs=0.1
        )

    def test_monotone_in_temperature(self):
        temps = sorted(SAT_LADDER)
        pressures = [saturation_pressure(t) for t in temps]
        assert pressures == sorted(pressures)

    def test_no_saturation_curve_above_critical(self):
        with pytest.raises(ValueError):
            saturation_pressure(410.0)


class TestCoolantScreen:
    """The companion paper's coolant-class screen, now fully computed."""

    EPS, T_S = 0.91, 220.0

    def test_two_sided_margin_over_50K(self):
        # Continuous-peak hypothetical on 220 m^2: >50 K below critical.
        T_pk = equilibrium_temperature(150e3, 220.0, self.EPS, self.T_S)
        assert critical_margin(T_pk) > 50.0

    def test_one_sided_sustained_under_14K_headroom(self):
        T = equilibrium_temperature(120e3, 110.0, self.EPS, self.T_S)
        assert 13.9 < critical_margin(T) < 14.2   # disfavored, NOT excluded

    def test_one_sided_continuous_peak_supercritical(self):
        # 411.8 K exceeds T_crit: no liquid ammonia at ANY pressure.
        T = equilibrium_temperature(150e3, 110.0, self.EPS, self.T_S)
        assert critical_margin(T) < 0.0
        assert phase_state(T, 100.0 * PA_PER_BAR).startswith("supercritical")

    def test_liquid_requires_pressure_above_saturation(self):
        # At the primary operating point (337.1 K): liquid above the
        # saturation pressure, gas below it.
        T = equilibrium_temperature(120e3, 220.0, self.EPS, self.T_S)
        P_sat = saturation_pressure(T)
        assert phase_state(T, 1.05 * P_sat) == "liquid"
        assert phase_state(T, 0.95 * P_sat) == "gas"


class TestPhysicalSanity:
    def test_saturated_liquid_denser_than_vapor(self):
        rho_liq, rho_vap = saturated_densities(337.1)
        assert rho_liq > rho_vap > 0.0

    def test_provenance_is_complete(self):
        p = provenance()
        assert p["backend"] == "HEOS"
        assert p["version"]            # non-empty
        assert p["eos_bibtex_key"]     # citable EOS reference
