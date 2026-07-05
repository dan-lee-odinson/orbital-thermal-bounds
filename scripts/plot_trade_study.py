"""Generate the six B6 Pareto-front figures for the public docs (Milestone B7).

Reads the committed, machine-readable B6 data (``docs/trade-study-points.csv``) and imports the
front definitions from :data:`orbital_thermal.trade_study.TRADES`, so the figures **cannot drift**
from the tested engine output. This script performs **no** new physics, smoothing, interpolation,
or ranking -- it only renders the already-computed points.

Each figure shows the feasible points for one named front, coloured by case, with the
**Pareto-front members** (from the exported ``pareto_front_membership``) highlighted. Points that
are gate-rejected or nonconverged carry no feasible metric coordinates, so they cannot be placed
on a metric axis; their counts are stated in the caption and their full records remain in the CSV.

Usage::

    python scripts/plot_trade_study.py [csv_path] [output_dir]

Defaults: ``docs/trade-study-points.csv`` -> ``docs/trade-study-figures/``. Requires matplotlib
(the package's optional [dev] extra). Report/figure script: lint-exempt, not imported by the
package.
"""

import csv
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from orbital_thermal.trade_study import TRADES  # noqa: E402

_AXIS_LABEL = {
    "heat_load_W": "heat load Q [W]",
    "modeled_mass_kg": "modeled component mass (incomplete) [kg]",
    "fluid_delta_T_K": "fluid delta_T [K]",
    "pump_power_W": "pump power [W]",
    "radiator_temperature_K": "radiator temperature [K]",
    "radiator_area_m2": "radiator emitting area [m^2]",
    "junction_margin_K": "junction margin [K]",
    "inventory_plus_containment_kg": "inventory + containment mass (incomplete) [kg]",
    "operating_pressure_Pa": "operating pressure [Pa]",
    "parasitic_power_W": "parasitic power [W]",
}
_CASE_COLOR = {
    "ammonia-aluminum": "#1f77b4", "ammonia-copper": "#ff7f0e",
    "water-aluminum": "#2ca02c", "water-copper": "#d62728",
}


def _load(csv_path):
    with open(csv_path, newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/trade-study-points.csv")
    outdir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("docs/trade-study-figures")
    outdir.mkdir(parents=True, exist_ok=True)
    rows = _load(csv_path)

    feasible = [r for r in rows if r["feasible"] == "True"]
    cat_counts = Counter(r["category"] for r in rows if r["feasible"] != "True")
    excluded_note = ", ".join(f"{v} {k}" for k, v in sorted(cat_counts.items())) or "none"

    for t in TRADES:
        fig, ax = plt.subplots(figsize=(6.4, 4.6))
        for r in feasible:
            member = t.name in r["pareto_front_membership"].split("|")
            x, y = float(r[t.x_key]), float(r[t.y_key])
            color = _CASE_COLOR.get(r["case_id"], "#777777")
            if member:
                ax.scatter(x, y, s=95, facecolors=color, edgecolors="black", linewidths=1.3,
                           zorder=3)
            else:
                ax.scatter(x, y, s=26, facecolors=color, alpha=0.35, zorder=2)
        # legend: cases + a "Pareto member" marker
        handles = [plt.Line2D([], [], marker="o", ls="", mfc=c, mec="none", label=case)
                   for case, c in _CASE_COLOR.items()]
        handles.append(plt.Line2D([], [], marker="o", ls="", mfc="white", mec="black",
                                  mew=1.3, ms=9, label="Pareto-front member"))
        ax.legend(handles=handles, fontsize=7, loc="best", framealpha=0.9)
        ax.set_xlabel(_AXIS_LABEL.get(t.x_key, t.x_key)
                      + f"  ({'maximize' if t.x_maximize else 'minimize'})")
        ax.set_ylabel(_AXIS_LABEL.get(t.y_key, t.y_key)
                      + f"  ({'maximize' if t.y_maximize else 'minimize'})")
        ax.set_title(t.name, fontsize=11, fontweight="bold")
        cap = (f"Stage-1 grid; feasible points only. Dominating assumption: {t.dominating_assumption}\n"
               f"Excluded (no feasible metrics): {excluded_note}. No single case is optimal on "
               f"every front (not a global ranking). Data: trade-study-points.csv.")
        fig.text(0.02, -0.02, cap, fontsize=6.2, wrap=True, va="top")
        ax.grid(True, ls=":", alpha=0.4)
        fig.tight_layout()
        out = outdir / f"{t.name}.png"
        fig.savefig(out, dpi=140, bbox_inches="tight")
        plt.close(fig)
        print(f"wrote {out}")

    print(f"\n{len(feasible)} feasible points plotted; excluded: {excluded_note}")


if __name__ == "__main__":
    main()
