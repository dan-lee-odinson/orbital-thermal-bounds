"""Example 2: the edge-on +6.35 K correction (paper-three headline).

Reproduces the headline of the third preprint. McCalip's public model, at its
default edge-on geometry (beta = 90 deg, 550 km), uses an approximate Earth view
factor. Recomputing the SAME heat balance with the exact tilted-plate-to-sphere
view factor raises the coded equilibrium temperature by +6.35 K. The correction
is positive at every orbit beta angle and grows toward edge-on. Requires only numpy.

Run from the repository root:
    python examples/02_edge_on_correction.py
"""
from orbital_thermal import mccalip_exact_vf as mx
from orbital_thermal import mccalip_replication as mc

# McCalip's own replicated equilibrium temperature at the default state.
T_coded = mc.calculate_thermal(dict(mc.DEFAULT_STATE))["eqTempK"]

# The same heat balance evaluated with exact per-face Earth view factors.
T_exact = mx.eqtemp_exact_vf({})

print(f"McCalip coded equilibrium      : {T_coded:.6f} K")
print(f"Exact view-factor equilibrium  : {T_exact:.6f} K")
print(f"Correction                     : +{T_exact - T_coded:.6f} K   (headline +6.35 K)")
print()
print("Correction vs orbit beta angle:")
print(f"{'beta(deg)':>9} {'McCalip(K)':>12} {'exact(K)':>11} {'delta(K)':>9}")
for r in mx.correction_table_vs_beta([0, 15, 30, 45, 60, 75, 90]):
    print(f"{r['beta_deg']:>9.0f} {r['eqtemp_mccalip_K']:>12.3f} "
          f"{r['eqtemp_exact_K']:>11.3f} {r['delta_K']:>9.2f}")
