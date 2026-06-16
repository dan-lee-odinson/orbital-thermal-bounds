"""Example 3: orbit-coupled transient and the averaging bias.

Marches the one-node panel to a periodic steady state under the orbit-varying
effective sink, then compares the transient peak to the steady, averaged-sink
solution -- the "peak excess" the steady, averaged-load assumption misses.
Requires only numpy.

Run from the repository root:
    python examples/03_transient_orbit.py
"""
from orbital_thermal import transient as tr

# A representative panel stack; areal heat capacity comes from a named build.
BUILD = "integrated_compute_radiator"
C_A = tr.build_areal_heat_capacity(BUILD)
print(f"Build {BUILD!r}")
print(f"  areal heat capacity          : {C_A:8,.0f} J/m^2/K")

# 550 km, beta = 30 deg, 545.5 W/m^2 load (paper-three Table 4 operating point).
res = tr.averaging_bias(550.0, 30.0, 545.5, C_A, assume_sun_shielded=True)

print(f"  transient mean temperature   : {res['transient_mean_K']:8.2f} K")
print(f"  transient peak temperature   : {res['transient_peak_K']:8.2f} K")
print(f"  steady averaged-sink temp    : {res['steady_avg_sink_K']:8.2f} K")
print(f"  peak excess over steady      : {res['peak_excess_over_steady_K']:8.2f} K")
print(f"  orbit temperature swing      : {res['swing_K']:8.2f} K")
print(f"  tau / orbital period         : {res['tau_over_period']:8.2f}")
