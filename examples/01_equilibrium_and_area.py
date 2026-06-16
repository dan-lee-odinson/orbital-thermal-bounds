"""Example 1: equilibrium temperature and required radiator area.

The most basic use of orbital_thermal: the steady one-node radiator balance,
its inverse, and the exact area-ratio law. Requires only numpy.

Run from the repository root:
    python examples/01_equilibrium_and_area.py
"""
from orbital_thermal import (
    area_ratio,
    effective_sink_temperature,
    equilibrium_temperature,
    radiative_capacity,
    required_area,
)

EPS = 0.91  # radiator emissivity used throughout the papers

# AI1 primary operating point: 120 kW rejected through 220 m^2 of emitting
# area against a 220 K effective sink.
Q = 120e3
A = 220.0
T_SINK = 220.0

T_eq = equilibrium_temperature(Q, A, EPS, T_SINK)
print(f"Equilibrium temperature        : {T_eq:7.1f} K   (paper anchor 337.1 K)")

# Inverse check: capacity at that temperature returns the original load.
Q_back = radiative_capacity(T_eq, A, EPS, T_SINK)
print(f"Capacity back-check            : {Q_back/1e3:7.1f} kW  (input load {Q/1e3:.0f} kW)")

# Area law (Lemma 1): area to reject 1 MW at 293 K against a cold sky.
A_1MW = required_area(1e6, 293.0, EPS, T_sink=0.0)
print(f"Area for 1 MW at 293 K, no sink: {A_1MW:7,.0f} m^2  (anchor 2,630 m^2 emitting)")

# Exact area-ratio law (Corollary 1.1): 293 K -> 600 K against a 220 K sink,
# compared with the naive zero-sink estimate.
R = area_ratio(293.0, 600.0, T_sink=220.0)
R0 = area_ratio(293.0, 600.0, T_sink=0.0)
print(f"Area ratio 293->600 K (220 K)  : {R:7.3f}     "
      f"(zero-sink estimate {R0:.3f}, exact is {(R/R0-1)*100:.1f}% higher)")

# Lumped effective sink: a panel seeing the warm environment over view factor F.
T_s_eff = effective_sink_temperature(0.257772825, 255.0)
print(f"Lumped sink at F=0.2578, 255 K : {T_s_eff:7.1f} K")
