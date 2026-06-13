"""The McCalip edge-on geometry correction (audit finding #1).

At McCalip's default geometry the sun-tracking panel is edge-on to Earth, where
his view-factor floor underestimates the exact tilted-plate-to-sphere view factor
by ~12x. Correcting only the view factor in his own heat balance raises his
default equilibrium temperature by ~6.35 K. These tests lock that quantified
result; they do not edit the frozen replication oracle.
"""

import pytest

from orbital_thermal import environment as env
from orbital_thermal import mccalip_exact_vf as ev
from orbital_thermal import mccalip_replication as mc


class TestEdgeOnDefault:
    def test_default_geometry_is_edge_on(self):
        # beta = 90 deg: every orbit position is edge-on (tilt = 90 deg), so the
        # exact per-face VF equals the single edge-on view factor and the two
        # faces are symmetric.
        s = mc._state({})
        assert s["betaAngle"] == 90
        vf_a, vf_b = ev.exact_per_face_view_factors(s["orbitalAltitudeKm"], 90.0)
        assert vf_a == pytest.approx(env.sphere_view_factor(550.0, 90.0), rel=1e-9)
        assert vf_a == pytest.approx(vf_b, rel=1e-12)

    def test_floor_underestimates_exact_by_about_12x(self):
        heur = mc.sun_tracking_view_factors(550.0, 90.0)["vfSideA"]
        exact, _ = ev.exact_per_face_view_factors(550.0, 90.0)
        assert heur == pytest.approx(0.021, abs=0.001)
        assert exact == pytest.approx(0.258, abs=0.001)
        assert exact / heur > 10.0

    def test_heat_balance_reproduces_replication_with_his_view_factors(self):
        # Only the view factor is allowed to differ: with McCalip's own VFs the
        # recomputation reproduces his replicated equilibrium temperature exactly.
        s = mc._state({})
        vf = mc.sun_tracking_view_factors(s["orbitalAltitudeKm"], s["betaAngle"])
        got = ev.equilibrium_temperature_with_view_factors({}, vf["vfSideA"], vf["vfSideB"])
        assert got == pytest.approx(mc.calculate_thermal(s)["eqTempK"], rel=1e-12)

    def test_exact_vf_raises_default_eqtemp_by_about_6_3K(self):
        mcc = mc.calculate_thermal(mc._state({}))["eqTempK"]
        exact = ev.eqtemp_exact_vf({})
        assert mcc == pytest.approx(335.75, abs=0.05)
        assert exact == pytest.approx(342.10, abs=0.10)
        assert (exact - mcc) == pytest.approx(6.35, abs=0.10)
