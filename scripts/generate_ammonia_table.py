"""Generate results/tables/ammonia_properties.csv.

Tabulates ammonia properties at every radiator-surface temperature that
appears in the companion paper (operating points, stress branches, and
overhead cases), with full provenance in the header.

Run from the repository root:

    python scripts/generate_ammonia_table.py
"""

import csv
from pathlib import Path

from orbital_thermal.fluids import (
    PA_PER_BAR,
    critical_margin,
    provenance,
    saturated_densities,
    saturation_pressure,
)

# Radiator-surface temperatures from the companion paper (K), labeled.
PAPER_TEMPERATURES = [
    (337.10, "sustained, two-sided (primary)"),
    (343.80, "f=0.10 overhead, nominal"),
    (346.21, "sustained, eps=0.80"),
    (348.67, "85% effective area"),
    (350.12, "f=0.20 overhead, nominal"),
    (350.78, "sustained, T_s=260"),
    (353.16, "continuous-peak hypothetical"),
    (358.91, "sustained, combined stress"),
    (365.24, "f=0.10 overhead, stressed"),
    (371.26, "f=0.20 overhead, stressed"),
    (374.17, "continuous-peak, combined stress"),
    (391.47, "sustained, one-sided"),
]

OUT = Path("results/tables/ammonia_properties.csv")


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prov = provenance()
    with OUT.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [f"# {k}={v}" for k, v in prov.items()][:1]
            + [f"{k}={v}" for k, v in list(prov.items())[1:]]
        )
        writer.writerow(
            [
                "T_K",
                "case",
                "P_sat_bar",
                "rho_liq_kg_m3",
                "rho_vap_kg_m3",
                "T_crit_margin_K",
            ]
        )
        for T, label in PAPER_TEMPERATURES:
            p_bar = saturation_pressure(T) / PA_PER_BAR
            rho_l, rho_v = saturated_densities(T)
            writer.writerow(
                [
                    f"{T:.2f}",
                    label,
                    f"{p_bar:.2f}",
                    f"{rho_l:.1f}",
                    f"{rho_v:.2f}",
                    f"{critical_margin(T):.2f}",
                ]
            )
    print(f"wrote {OUT} ({len(PAPER_TEMPERATURES)} rows)")
    print("provenance:", prov)


if __name__ == "__main__":
    main()
