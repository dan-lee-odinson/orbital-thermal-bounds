"""Generate the third paper's opening figure: effective sink temperature around
the orbit versus the companion paper's constant 220 K assumption.

Run from the repository root:

    python scripts/plot_effective_sink.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from orbital_thermal import sink

ALT = 550.0          # km
PAPER_SINK = 220.0   # K, constant assumption in doi:10.5281/zenodo.20670771
BETAS = [0.0, 30.0, 60.0, 90.0]
OUT = Path("results/figures/effective_sink_vs_orbit.png")


def main() -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.2))

    colors = plt.cm.viridis(np.linspace(0.1, 0.85, len(BETAS)))
    for beta, c in zip(BETAS, colors):
        u, T = sink.sink_profile(ALT, beta, tilt_deg=0.0, assume_sun_shielded=True)
        ax.plot(u, T, color=c, lw=2.2, label=f"beta = {beta:.0f} deg")

    ax.axhline(PAPER_SINK, color="crimson", lw=1.8, ls="--",
               label=f"companion paper assumption ({PAPER_SINK:.0f} K)")

    floor = sink.orbital_effective_sink_temperature(ALT, 0, 180, tilt_deg=0, assume_sun_shielded=True)
    ax.annotate(f"Earth-IR floor (eclipse / terminator) ~ {floor:.0f} K",
                xy=(180, floor), xytext=(150, floor - 9),
                fontsize=8, color="0.3")
    ax.text(8, 224.5, "A space-facing (zenith) radiator instead sees ~ 3 K "
            "(CMB) - far below 220 K.", fontsize=7.5, color="0.4", style="italic")

    ax.set_xlabel("orbit position from noon, u (deg)")
    ax.set_ylabel("effective sink temperature, $T_s^{\\mathrm{eff}}$ (K)")
    ax.set_title("Nadir-facing radiator: effective sink around a 550 km orbit\n"
                 "(maximally Earth-coupled orientation vs. the constant-sink assumption)")
    ax.set_xlim(0, 360)
    ax.set_ylim(212, 270)
    ax.set_xticks(range(0, 361, 45))
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper center", ncol=2, framealpha=0.92)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=130)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
