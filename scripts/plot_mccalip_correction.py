"""Figure: McCalip equilibrium-temperature correction vs orbit beta angle.

Recomputes McCalip's default-case equilibrium temperature with the exact per-face
Earth view factor across beta and plots his value, the corrected value, and the
+K correction. This is the paper-three headline figure for the edge-on finding.

Run from the repo root:
    python scripts/plot_mccalip_correction.py
Writes results/figures/mccalip_beta_correction.png.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from orbital_thermal import mccalip_exact_vf as ev

OUT = "results/figures/mccalip_beta_correction.png"


def main():
    rows = ev.correction_table_vs_beta(betas=range(0, 91, 5))
    beta = [r["beta_deg"] for r in rows]
    mccalip = [r["eqtemp_mccalip_K"] for r in rows]
    exact = [r["eqtemp_exact_K"] for r in rows]
    delta = [r["delta_K"] for r in rows]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 2]})
    ax1.plot(beta, mccalip, "o-", label="McCalip (cos-tilt floor)", color="#c44")
    ax1.plot(beta, exact, "s-", label="exact per-face view factor", color="#268")
    ax1.axvline(90, ls=":", color="gray", lw=1)
    ax1.annotate("default\n(edge-on)", xy=(90, exact[-1]), xytext=(70, exact[-1] + 2),
                 fontsize=9, color="gray")
    ax1.set_ylabel("equilibrium temperature (K)")
    ax1.set_title("McCalip default radiator: exact-view-factor correction vs beta")
    ax1.legend(loc="upper right")
    ax1.grid(alpha=0.3)

    ax2.plot(beta, delta, "^-", color="#373")
    ax2.set_xlabel("orbit beta angle (deg)")
    ax2.set_ylabel("correction (K)")
    ax2.set_xlim(0, 90)
    ax2.grid(alpha=0.3)
    ax2.annotate(f"+{delta[-1]:.2f} K at beta=90", xy=(90, delta[-1]),
                 xytext=(45, delta[-1] - 1.2), fontsize=9, color="#373",
                 arrowprops=dict(arrowstyle="->", color="#373"))

    fig.tight_layout()
    fig.savefig(OUT, dpi=130)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
