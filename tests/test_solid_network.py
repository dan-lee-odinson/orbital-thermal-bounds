"""B2 solid thermal network tests: analytic resistances, Yovanovich spreading limits,
series assembly, and registry-governed rank-eligibility (isotropic-only)."""

from __future__ import annotations

import math

import pytest

from orbital_thermal import solid_network as sn
from orbital_thermal.registry import NotRankEligibleError

K_AL = 237.0
K_CU = 401.0


class TestConduction:
    def test_exact(self):
        assert sn.conduction_resistance(0.01, 1e-4, K_AL) == pytest.approx(0.01 / (K_AL * 1e-4))

    @pytest.mark.parametrize("args", [(-1.0, 1e-4, K_AL), (0.01, 0.0, K_AL), (0.01, 1e-4, -5.0)])
    def test_rejects_bad_inputs(self, args):
        with pytest.raises(ValueError):
            sn.conduction_resistance(*args)


class TestSpreading:
    def test_isoflux_halfspace_limit(self):
        # point source, thick plate, isothermal base -> R*k*a ~ 0.28 (cf 8/(3 pi^2)=0.270)
        r = sn.spreading_resistance(1e-3, 1.0, 10.0, K_AL)
        assert 0.25 < r * K_AL * 1e-3 < 0.30

    def test_source_fills_plate_vanishes(self):
        assert sn.spreading_resistance(0.99, 1.0, 0.01, K_AL) < 1e-6

    def test_monotonic_in_source_radius(self):
        small = sn.spreading_resistance(1e-3, 0.05, 0.005, K_AL)
        big = sn.spreading_resistance(5e-3, 0.05, 0.005, K_AL)
        assert small > big > 0.0

    def test_convective_base_not_below_isothermal(self):
        iso = sn.spreading_resistance(2e-3, 0.02, 0.003, K_AL)
        conv = sn.spreading_resistance(2e-3, 0.02, 0.003, K_AL, base_htc_W_m2K=5000.0)
        assert conv >= iso

    def test_higher_conductivity_lowers_spreading(self):
        assert sn.spreading_resistance(2e-3, 0.02, 0.003, K_CU) < sn.spreading_resistance(
            2e-3, 0.02, 0.003, K_AL
        )

    def test_source_not_smaller_than_plate_raises(self):
        with pytest.raises(ValueError):
            sn.spreading_resistance(1.0, 1.0, 0.01, K_AL)  # eps = 1


class TestContact:
    def test_exact(self):
        assert sn.contact_resistance(1e4, 1e-4) == pytest.approx(1.0)


class TestSolidPath:
    def _ranked(self):
        return sn.build_ranked_path(
            material="copper", length_m=0.003, area_m2=math.pi * 0.01**2,
            source_radius_m=0.01, plate_radius_m=0.03, thickness_m=0.003,
            contact_conductance_W_m2K=1e4, contact_source="cited interface",
        )

    def test_total_is_series_sum(self):
        p = self._ranked()
        assert p.total_K_per_W == pytest.approx(math.fsum(r.value_K_per_W for r in p.resistors))

    def test_junction_temperature(self):
        p = self._ranked()
        assert p.junction_temperature(300.0, 300.0) == pytest.approx(300.0 + 300.0 * p.total_K_per_W)

    def test_spreading_present_and_rank_eligible(self):
        p = self._ranked()
        assert p.has_spreading and p.rank_eligible

    def test_one_d_justified_allows_no_spreading(self):
        r = sn.Resistor("conduction", "conduction", 0.4, True)
        no_spread = sn.SolidPath(resistors=(r,))
        assert not no_spread.rank_eligible  # spreading missing, not justified
        justified = sn.SolidPath(resistors=(r,), one_d_justified=True, one_d_justification="thin")
        assert justified.rank_eligible


class TestRegistryEnforcement:
    def _kw(self, **over):
        base = dict(
            length_m=0.003, area_m2=math.pi * 0.01**2, source_radius_m=0.01,
            plate_radius_m=0.03, thickness_m=0.003, contact_conductance_W_m2K=1e4,
            contact_source="cited interface",
        )
        base.update(over)
        return base

    @pytest.mark.parametrize("material", ["aluminum", "copper"])
    def test_isotropic_materials_rank_eligible(self, material):
        p = sn.build_ranked_path(material=material, **self._kw())
        assert p.rank_eligible and len(p.resistors) == 3

    @pytest.mark.parametrize("material", ["apg", "diamond_composite"])
    def test_blocked_material_raises(self, material):
        with pytest.raises(NotRankEligibleError):
            sn.build_ranked_path(material=material, **self._kw())

    def test_uncited_contact_raises(self):
        with pytest.raises(NotRankEligibleError):
            sn.build_ranked_path(material="copper", **self._kw(contact_source="   "))

    def test_sensitivity_path_never_rank_eligible(self):
        p = sn.build_sensitivity_path(
            k_W_mK=1500.0, length_m=0.003, area_m2=1e-4, source_radius_m=0.01,
            plate_radius_m=0.03, thickness_m=0.003, note="APG parametric bound",
        )
        assert not p.rank_eligible

    def test_copper_beats_aluminum(self):
        cu = sn.build_ranked_path(material="copper", **self._kw())
        al = sn.build_ranked_path(material="aluminum", **self._kw())
        assert cu.total_K_per_W < al.total_K_per_W
