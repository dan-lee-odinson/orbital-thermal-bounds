#!/usr/bin/env python3
"""Clean-room smoke test for an installed orbital-thermal wheel.

Imports the INSTALLED package (no repository src/ on the path) and checks the two
headline numbers. Used by the wheel-smoke CI job; also runnable by hand once the
package is installed:

    python scripts/smoke_test.py
"""
from importlib.metadata import version

from orbital_thermal import equilibrium_temperature
from orbital_thermal import mccalip_exact_vf as mx
from orbital_thermal import mccalip_replication as mc

v = version("orbital-thermal")
assert v == "1.1.0", f"expected orbital-thermal 1.1.0, got {v}"

# AI1 primary operating point: 120 kW / 220 m^2 / eps 0.91 / 220 K sink -> 337.1 K.
T = equilibrium_temperature(120e3, 220.0, 0.91, 220.0)
assert abs(T - 337.1) < 0.05, f"AI1 operating point off: {T}"

# Paper-three headline: exact view factor raises the coded equilibrium by +6.35 K.
delta = mx.eqtemp_exact_vf({}) - mc.calculate_thermal(dict(mc.DEFAULT_STATE))["eqTempK"]
assert abs(delta - 6.349684) < 1e-4, f"edge-on correction off: {delta}"

print(f"wheel smoke OK: version {v}, AI1 point {T:.1f} K, "
      f"edge-on correction +{delta:.6f} K")
