"""B3 single-phase pumped-loop tests: hydraulics (Poiseuille + regime selection), pump-energy
accounting, thermics (Nusselt/film), registry rank-eligibility, and the N-segment march with
per-segment phase margins (CoolProp-gated)."""

from __future__ import annotations

import math

import pytest

from orbital_thermal import pumped_loop as pl
from orbital_thermal.registry import NotRankEligibleError


class TestHydraulics:
    def test_reynolds_mass_flow_form(self):
        # Re = 4 m_dot / (pi D mu)
        mdot, d, mu = 0.003, 0.004, 8.9e-4
        assert pl.reynolds(mdot, d, mu) == pytest.approx(4 * mdot / (math.pi * d * mu))

    def test_laminar_friction_is_64_over_Re(self):
        assert pl.friction_factor(1000.0) == pytest.approx(64.0 / 1000.0)

    def test_poiseuille_exact(self):
        rho, mu, d, ln, mdot = 997.0, 8.9e-4, 0.004, 1.0, 0.003  # Re ~ 1073 laminar
        a = pl.flow_area(d)
        v = pl.velocity(mdot, rho, a)
        re = pl.reynolds(mdot, d, mu, a)
        dp = pl.pressure_drop(pl.friction_factor(re), ln, d, rho, v)
        assert dp == pytest.approx(32 * mu * ln * v / d**2, rel=1e-12)

    def test_turbulent_uses_haaland_band(self):
        f = pl.friction_factor(1.0e5)
        assert 0.01 < f < 0.03  # smooth-turbulent range

    def test_transition_warns(self):
        with pytest.warns(RuntimeWarning):
            pl.friction_factor(3000.0)

    def test_minor_losses_add(self):
        base = pl.pressure_drop(0.02, 1.0, 0.004, 997.0, 1.0, 0.0)
        with_k = pl.pressure_drop(0.02, 1.0, 0.004, 997.0, 1.0, 5.0)
        assert with_k > base


class TestPumpEnergy:
    def test_hydraulic_into_fluid_accounting(self):
        pe = pl.pump_energy(0.2, 5.0e4, 997.0, eta_pump=0.7, eta_motor=0.9)
        assert pe.hydraulic_power_W == pytest.approx(0.2 * 5.0e4 / 997.0)
        assert pe.electrical_power_W == pytest.approx(pe.hydraulic_power_W / (0.7 * 0.9))
        assert pe.fluid_heat_W == pytest.approx(pe.hydraulic_power_W)
        assert pe.deposition_fraction == pytest.approx(0.63, rel=1e-6)
        assert pe.other_heat_W == pytest.approx(pe.electrical_power_W - pe.hydraulic_power_W)

    def test_bad_efficiency_and_boundary_raise(self):
        with pytest.raises(ValueError):
            pl.pump_energy(0.2, 5e4, 997.0, eta_pump=1.5)
        with pytest.raises(ValueError):
            pl.pump_energy(0.2, 5e4, 997.0, boundary="nope")


class TestThermics:
    def test_laminar_nusselt_constants(self):
        assert pl.nusselt(1000.0, 5.0, uniform_flux=True) == pytest.approx(4.36)
        assert pl.nusselt(1000.0, 5.0, uniform_flux=False) == pytest.approx(3.66)

    def test_turbulent_nusselt_positive_large(self):
        assert pl.nusselt(5.0e4, 6.0) > 4.36

    def test_htc_and_film_resistance(self):
        h = pl.heat_transfer_coefficient(100.0, 0.6, 0.004)
        assert h == pytest.approx(100.0 * 0.6 / 0.004)
        assert pl.film_resistance(h, 0.01) == pytest.approx(1.0 / (h * 0.01))


class TestRegistryEnforcement:
    @pytest.mark.parametrize("coolant", ["ammonia", "water"])
    def test_rankable_coolants(self, coolant):
        pl.assert_loop_coolant_rankable(coolant)  # must not raise

    @pytest.mark.parametrize("coolant", ["co2", "propylene_glycol_water", "mercury"])
    def test_blocked_coolants_raise(self, coolant):
        with pytest.raises(NotRankEligibleError):
            pl.assert_loop_coolant_rankable(coolant)


# --- CoolProp-gated: per-state properties + the loop march ----------------------

pytest.importorskip("CoolProp", reason="CoolProp not installed")


class TestLoopMarch:
    def _ammonia(self, **over):
        kw = dict(
            coolant="ammonia", mass_flow_kg_s=0.05, inlet_temperature_K=290.0,
            inlet_pressure_Pa=20.0e5, loop_length_m=2.0, diameter_m=0.004,
            heat_into_loop_W=1200.0, segments=10,
        )
        kw.update(over)
        return pl.march_single_phase_loop(**kw)

    def test_healthy_loop_rank_eligible(self):
        r = self._ammonia()
        assert r.rank_eligible and r.total_pressure_drop_Pa > 0 and r.mean_htc_W_m2K > 0

    def test_energy_balance_outlet_temperature(self):
        # T_out - T_in ~ Q / (m_dot * cp); cp ~ 4.8 kJ/kgK for ammonia
        r = self._ammonia(segments=20)
        dT = r.outlet_temperature_K - 290.0
        assert dT == pytest.approx(1200.0 / (0.05 * 4800.0), rel=0.05)

    def test_segment_count_converges(self):
        assert self._ammonia(segments=5).outlet_temperature_K == pytest.approx(
            self._ammonia(segments=40).outlet_temperature_K, rel=1e-3
        )

    def test_underpressured_loop_boils_and_raises(self):
        # inlet pressure below ammonia saturation at ~290 K -> subcooling violated
        with pytest.raises(pl.LoopPhaseError):
            self._ammonia(inlet_pressure_Pa=5.0e5)

    def test_unknown_coolant_raises_even_unranked(self):
        with pytest.raises(NotRankEligibleError):
            self._ammonia(coolant="mercury", ranked=False)


class TestFluidsPerState:
    def test_transport_properties_match_coolprop(self):
        from CoolProp.CoolProp import PropsSI

        from orbital_thermal import fluids
        p = fluids.transport_properties(300.0, 5.0e5, "Water")
        assert p["density"] == pytest.approx(PropsSI("D", "T", 300.0, "P", 5.0e5, "Water"), rel=1e-9)
        assert p["prandtl"] == pytest.approx(
            PropsSI("C", "T", 300, "P", 5e5, "Water")
            * PropsSI("V", "T", 300, "P", 5e5, "Water")
            / PropsSI("L", "T", 300, "P", 5e5, "Water"),
            rel=1e-9,
        )

    def test_freeze_margin_detects_cold_water(self):
        from orbital_thermal import fluids
        m = fluids.single_phase_liquid_margins(274.0, 3.0e5, "Water")
        assert m["freeze_margin_K"] < 5.0 and m["critical_margin_K"] > 0
