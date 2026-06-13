"""Transient radiator temperature over one orbit vs the steady, averaged-sink
prediction -- showing the ripple and peak excess thermal mass introduces.

Run from the repository root:

    python scripts/plot_transient.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from orbital_thermal import transient as tr
from orbital_thermal.constants import SIGMA_SB

ALT, BETA, EPS = 550.0, 0.0, 0.91
Q_LOAD = EPS * SIGMA_SB * (337.1**4 - 220.0**4)
CAPACITIES = [2000.0, 8000.0, 40000.0]
OUT = Path("results/figures/transient_temperature.png")


def main() -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    colors = plt.cm.plasma(np.linspace(0.15, 0.8, len(CAPACITIES)))

    steady = None
    for C, c in zip(CAPACITIES, colors):
        t, T, Ts = tr.simulate(ALT, BETA, Q_LOAD, C, tilt_deg=0.0, assume_sun_shielded=True,
                               n_orbits=40, steps_per_orbit=1440)
        b = tr.averaging_bias(ALT, BETA, Q_LOAD, C, tilt_deg=0.0, assume_sun_shielded=True,
                              n_orbits=40, steps_per_orbit=1440)
        steady = b["steady_avg_sink_K"]
        tau_min = b["tau_s"] / 60.0
        ax.plot(t / 60.0, T, color=c, lw=2.0,
                label=f"C = {C/1000:.0f} kJ/m^2/K  (tau ~ {tau_min:.0f} min, "
                      f"swing {b['swing_K']:.1f} K)")

    ax.axhline(steady, color="black", lw=1.5, ls="--",
               label=f"steady, averaged sink ({steady:.1f} K)")

    ax.set_xlabel("time from orbit start (min)")
    ax.set_ylabel("radiator temperature (K)")
    ax.set_title("Transient radiator temperature over one 550 km orbit (beta = 0)\n"
                 "thermal mass damps the ripple but leaves a peak the steady sizing misses")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper right", framealpha=0.92)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=130)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
