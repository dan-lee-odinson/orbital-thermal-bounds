"""Paper-specific verification for "Edge-On Geometry ... 6.35 K."

Recomputes the headline view-factor decomposition, the three equilibrium balances,
the sampled beta-correction table (Table 3), the periodic fourth-power identity,
and the displayed transient-bias rows (Table 4) from orbital-thermal==1.0.0. The
McCalip Node-oracle freeze and the broader package claims are verified separately
by the package test suite.

Run from the repository root:  python verify_paper3.py
Expected final line: "All paper-3 assertions pass."
"""
from importlib.metadata import version
import math
import numpy as np

# Pinned for archival reproduction. orbital-thermal v1.0.0 corresponds to repo
# commit 322fc44db8dc175450ac2e9eb918fe3a1758b2b1 (tag v1.0.0).
REQUIRED_VERSION = "1.0.0"
_installed = version("orbital-thermal")
assert _installed == REQUIRED_VERSION, (
    f"verify_paper3.py is pinned to orbital-thermal=={REQUIRED_VERSION}; "
    f"found {_installed}. Install the pinned release to reproduce.")

from orbital_thermal import (mccalip_replication as mc, mccalip_exact_vf as mx,
                             environment as env, transient as tr)
from orbital_thermal.constants import SIGMA_SB

ALT, EPS = 550.0, 0.91
ATOL_K = 5e-4          # temperature fingerprint tolerance (K)

def approx(a, b, tol=ATOL_K):
    assert abs(a - b) <= tol, f"{a} != {b} (tol {tol})"

# --- Claim A: exact edge-on view factor (closed form vs package) ---
theta = math.asin(6371.0 / (6371.0 + ALT))
F_edge_closed = (theta - math.sin(theta) * math.cos(theta)) / math.pi
F_edge_pkg = env.sphere_view_factor(ALT, 90.0)
approx(F_edge_closed, F_edge_pkg, 1e-6)
approx(F_edge_pkg, 0.257772825310, 1e-9)

# --- View-factor decomposition (Claims B/C/D) ---
F_nadir = mc.nadir_view_factor(ALT)
F_floor = 0.05 * F_nadir
F_coded = mc.sun_tracking_view_factors(ALT, 90.0)["vfSideA"]
approx(F_nadir, 0.84737863845, 1e-9)
approx(F_floor, 0.04236893192, 1e-9)
approx(F_coded, 0.02118446596, 1e-9)
assert abs(F_coded / F_floor - 0.5) < 1e-6, "coded != half the nominal floor"

# --- Three equilibrium balances through McCalip's own heat balance ---
T_coded = mc.calculate_thermal(dict(mc.DEFAULT_STATE))["eqTempK"]
T_floor = mx.equilibrium_temperature_with_view_factors({}, F_floor, F_floor)
T_exact = mx.eqtemp_exact_vf({})
approx(T_coded, 335.749538); approx(T_floor, 336.332909); approx(T_exact, 342.099222)
approx(T_exact - T_coded, 6.349684)   # actual coded -> exact
approx(T_exact - T_floor, 5.766313)   # intended floor -> exact (geometry)
approx(T_floor - T_coded, 0.583371)   # branch artifact

# --- beta-correction table (Table 3): positive + monotone on dense grid ---
table = {int(r["beta_deg"]): round(r["delta_K"], 2)
         for r in mx.correction_table_vs_beta([0,15,30,45,60,75,90])}
assert table == {0:1.94,15:2.04,30:2.41,45:3.22,60:4.38,75:5.55,90:6.35}, table
dense = [r["delta_K"] for r in mx.correction_table_vs_beta(np.linspace(0,90,181).tolist())]
min_inc = float(min(np.diff(dense)))
assert all(x > 0 for x in dense) and min_inc > 0, "not positive+monotone on dense grid"
approx(min_inc, 1.061e-4, 1e-5)   # reported minimum 0.5deg-grid increment

# --- Jensen identity + Table 4 (550 km, beta=30, q_load=545.5) ---
Q = EPS * SIGMA_SB * (337.1**4 - 220.0**4)
approx(Q, 545.5, 0.1)
#                  C        bias    peak   swing  tau/P   (Table 4 of the paper)
TABLE4 = [(2000.0,  -0.028,  4.45,  6.69,  0.04),
          (8000.0,  -0.014,  3.01,  5.07,  0.16),
          (40000.0, -0.001,  0.77,  1.47,  0.81)]
for C, bias_ref, peak_ref, swing_ref, tp_ref in TABLE4:
    t, T, Ts = tr.simulate(ALT, 30.0, Q, C, tilt_deg=0.0, assume_sun_shielded=True,
                           n_orbits=80, steps_per_orbit=720)
    b = tr.averaging_bias(ALT, 30.0, Q, C, tilt_deg=0.0, assume_sun_shielded=True,
                          n_orbits=80, steps_per_orbit=720)
    lhs = float(np.mean(T[:-1]**4))               # <T^4>
    rhs = Q/(EPS*SIGMA_SB) + float(np.mean(Ts[:-1]**4))
    approx(lhs**0.25, rhs**0.25, 1e-3)            # periodic energy identity
    assert b["bias_K"] <= 1e-6, "mean bias must be <= 0 (Jensen)"
    approx(b["bias_K"], bias_ref, 0.01)
    approx(b["peak_excess_over_steady_K"], peak_ref, 0.05)
    approx(b["swing_K"], swing_ref, 0.05)
    approx(b["tau_over_period"], tp_ref, 0.01)

print(f"orbital-thermal version: {version('orbital-thermal')}")
print(f"F_nadir={F_nadir:.11f}  F_floor={F_floor:.11f}  F_coded={F_coded:.11f}  F_edge={F_edge_pkg:.11f}")
print(f"T_coded={T_coded:.6f}  T_floor={T_floor:.6f}  T_exact={T_exact:.6f}")
print(f"decomposition: coded->exact +{T_exact-T_coded:.6f} = floor->exact +{T_exact-T_floor:.6f} "
      f"+ branch +{T_floor-T_coded:.6f} K")
print("All paper-3 assertions pass.")
