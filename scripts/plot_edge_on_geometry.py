"""Schematic of the beta=90 deg edge-on geometry behind the McCalip view-factor
correction (paper three, Figure 2). Orbit-plane (face-on) view: the Sun-tracking
panel's normal points to the Sun, which at beta=90 deg is normal to the orbit
plane (out of the page), so the panel face is presented to the reader while Earth
(nadir) lies in the panel plane, 90 deg from the normal -- the panel is edge-on to
Earth. The three per-face Earth view factors in the callout are COMPUTED from the
version-pinned package, not hard-coded.

Run from the repository root:  python scripts/plot_edge_on_geometry.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

from orbital_thermal import environment as env, mccalip_replication as mc

ALT = 550.0
OUT = Path("results/figures/edge_on_geometry.png")


def _view_factors():
    """(coded orbit-average, nominal 5% floor, exact edge-on) per face at beta=90."""
    f_nadir = mc.nadir_view_factor(ALT)
    f_floor = 0.05 * f_nadir
    f_coded = mc.sun_tracking_view_factors(ALT, 90.0)["vfSideA"]
    f_exact = env.sphere_view_factor(ALT, 90.0)
    return f_coded, f_floor, f_exact


def main() -> None:
    f_coded, f_floor, f_exact = _view_factors()
    NAVY = "#19326e"; GRAY = "#555555"; RED = "#b22222"; PANEL = "#2b2b2b"

    fig, ax = plt.subplots(figsize=(7.8, 4.5))
    ax.add_patch(Circle((0, 0), 1.0, facecolor="#cfe0f5", edgecolor=NAVY, lw=1.5, zorder=1))
    ax.text(0, 0, "Earth", ha="center", va="center", color=NAVY, fontsize=11, zorder=2)

    sc = (3.7, 0.0)
    # face-on bifacial panel: a broad plate whose face points out of the page (at the Sun)
    pw, ph = 0.62, 1.7
    ax.add_patch(Rectangle((sc[0]-pw/2, sc[1]-ph/2), pw, ph, facecolor="#d9d9d9",
                           edgecolor="black", lw=1.4, hatch="////", zorder=3))
    ax.text(sc[0], sc[1]+ph/2+0.12, "bifacial panel\n(face toward Sun / reader)",
            fontsize=9, color=PANEL, ha="center", va="bottom")

    ax.add_patch(FancyArrowPatch(sc, (1.05, 0.0), arrowstyle="-|>", mutation_scale=16,
                                 color=NAVY, lw=2, zorder=4))
    ax.text(2.35, 0.13, "nadir (in panel plane)", color=NAVY, fontsize=10, ha="center")

    # panel normal -> Sun, out of the page: circled dot at the panel centre
    ax.plot(*sc, "o", color="white", ms=20, mec=RED, mew=2.2, zorder=6)
    ax.plot(*sc, "o", color=RED, ms=5, zorder=7)
    ax.text(sc[0]+0.45, sc[1]-0.30, r"panel normal $\to$ Sun"+"\n(out of page, "+r"$\beta=90^\circ$)",
            fontsize=9.5, color=RED, va="top")

    ax.text(0.5, 0.95,
            r"$\beta=90^\circ$: Sun $\perp$ orbit plane, so the panel normal is out of the page"
            "\n"
            r"while Earth lies in the panel plane $\Rightarrow$ the panel normal is $90^\circ$ from nadir (edge-on)",
            transform=ax.transAxes, fontsize=10, color=GRAY, ha="center", va="top")

    ax.text(0.5, 0.045,
            "per-face Earth view factor at edge-on (550 km):   "
            f"coded orbit avg $= {f_coded:.5f}$   |   nominal 5%% floor $= {f_floor:.5f}$   |   "
            f"exact $= {f_exact:.5f}$",
            transform=ax.transAxes, fontsize=9, color="black", ha="center",
            bbox=dict(boxstyle="round,pad=0.4", fc="#fbf3d0", ec=GRAY, lw=1))

    ax.set_xlim(-1.3, 6.0); ax.set_ylim(-1.7, 1.95)
    ax.set_aspect("equal"); ax.axis("off")
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=300, bbox_inches="tight")
    print(f"wrote {OUT}  (coded={f_coded:.5f}, floor={f_floor:.5f}, exact={f_exact:.5f})")


if __name__ == "__main__":
    main()
