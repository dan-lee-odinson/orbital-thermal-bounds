"""Generate the Starcloud reference-architecture figures (Milestone A6).

Public-facing figures for docs/reference-architectures/starcloud-2024.md. Every
curve is computed from the package modules added in A2-A5
(reference_architectures, architecture_comparison, harmonized_comparison), so the
figures cannot drift from the tested numbers.

Usage:
    python scripts/plot_starcloud.py [output_dir]

Default output_dir: docs/reference-architectures/figures/. Requires matplotlib
(the package's optional [dev] extra). This is a report/figure script: it is
exempt from line-length/compound-statement lint (see pyproject per-file-ignores)
and is NOT imported by the package.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from orbital_thermal.architecture_comparison import AI1_DESIGN_POINT
from orbital_thermal.constants import SIGMA_SB
from orbital_thermal.harmonized_comparison import (
    HARMONIZED_TILT_DEG,
    ai1_harmonized_balance,
    harmonized_environment,
    starcloud_harmonized_balance,
)
from orbital_thermal.reference_architectures import (
    SIGMA_WHITEPAPER,
    starcloud_published_balance,
    starcloud_spectral_balance,
)
from orbital_thermal.reference_architectures import (
    STARCLOUD_2024_PUBLISHED as SC,
)

plt.switch_backend("Agg")  # headless rendering; no display required

# ----- fixed reference points from the package (tested in A2-A5) --------------
PUB = starcloud_published_balance()
SPEC = starcloud_spectral_balance()
EPS_SC = SC.emissivity_thermal          # 0.92
EPS_AI1 = AI1_DESIGN_POINT.emissivity_thermal  # 0.91
TS_AI1 = AI1_DESIGN_POINT.effective_sink_K     # 220 K
T_SUST = AI1_DESIGN_POINT.radiator_temperature_K(120e3)  # 337.10
T_PEAK = AI1_DESIGN_POINT.radiator_temperature_K(150e3)  # 353.16

COL = {"pub": "#1f77b4", "spec": "#ff7f0e", "ai1": "#2ca02c", "harm": "#d62728"}


def sc_net_published(T):
    """Starcloud as-written net per planform vs T (fixed published absorbed load)."""
    emit = 2 * EPS_SC * SIGMA_WHITEPAPER * T**4
    return emit - PUB.direct_solar_absorbed_W_m2 - PUB.earth_combined_absorbed_W_m2


def sc_net_spectral(T):
    emit = 2 * EPS_SC * SIGMA_WHITEPAPER * T**4
    return emit - SPEC.direct_solar_absorbed_W_m2 - SPEC.earth_combined_absorbed_W_m2


def ai1_net_planform(T):
    """AI1 lumped-sink net per planform (two-sided), T_s^eff = 220 K."""
    return 2 * EPS_AI1 * SIGMA_SB * (T**4 - TS_AI1**4)


def sc_net_harmonized_shielded(T, beta_deg=90.0):
    e = harmonized_environment(beta_deg, warn=False)
    emit = 2 * EPS_SC * SIGMA_SB * T**4
    return emit - EPS_SC * e.view_factor * e.earth_ir_flux_W_m2


def plot1(outdir):
    T = np.linspace(280, 370, 400)
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ax.plot(T, sc_net_published(T), color=COL["pub"], label="Starcloud published (single-band)")
    ax.plot(T, sc_net_spectral(T), color=COL["spec"], label="Starcloud spectral (alpha_IR=0.92)")
    ax.plot(T, ai1_net_planform(T), color=COL["ai1"], label="AI1 baseline (T_s^eff=220 K)")
    ax.plot(T, sc_net_harmonized_shielded(T), color=COL["harm"], ls="--",
            label="Harmonized orbital (shielded, beta=90)")
    ax.axvline(293.15, color="gray", ls=":", lw=1)
    ax.axvline(T_SUST, color="gray", ls=":", lw=1)
    ax.set_xlabel("Radiator temperature (K)")
    ax.set_ylabel("Net rejection per planform (W/m^2)")
    ax.set_title("Plot 1 - Net rejection vs radiator temperature")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    _save(fig, outdir, "plot1_net_vs_temperature.png")


def plot2(outdir):
    Q = np.linspace(50e3, 1e6, 400)
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ax.plot(Q / 1e3, Q / PUB.net_rejection_W_m2, color=COL["pub"], label="Starcloud published (293 K)")
    ax.plot(Q / 1e3, Q / SPEC.net_rejection_W_m2, color=COL["spec"], label="Starcloud spectral (293 K)")
    ax.plot(Q / 1e3, Q / ai1_net_planform(T_SUST), color=COL["ai1"], label="AI1 sustained (337 K)")
    ax.plot(Q / 1e3, Q / ai1_net_planform(T_PEAK), color=COL["ai1"], ls="--", label="AI1 peak (353 K)")
    ax.set_xlabel("Heat load (kW)")
    ax.set_ylabel("Required planform area (m^2)")
    ax.set_title("Plot 2 - Required area vs heat load")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    _save(fig, outdir, "plot2_area_vs_load.png")


def plot3(outdir):
    T = np.linspace(280, 370, 400)
    fig, ax = plt.subplots(figsize=(7, 4.6))
    net = sc_net_spectral(T)
    for Q, c in [(120e3, COL["pub"]), (150e3, COL["spec"]), (1e6, COL["ai1"])]:
        ax.plot(T, Q / net, color=c, label=f"{Q/1e3:.0f} kW")
    ax.set_xlabel("Radiator temperature (K)")
    ax.set_ylabel("Required planform area (m^2)")
    ax.set_yscale("log")
    ax.set_title("Plot 3 - Area vs radiator temperature (Starcloud spectral basis)")
    ax.legend(fontsize=8, title="Heat load")
    ax.grid(alpha=0.3, which="both")
    _save(fig, outdir, "plot3_area_vs_temperature.png")


def plot4(outdir):
    cases = ["Published", "Spectral", "Harmonized shielded\n(b90, model-limited*)",
             "Harmonized sunlit\n(b90, model-limited*)"]
    h0 = starcloud_harmonized_balance(90, sunlit_faces=0, warn=False)
    h1 = starcloud_harmonized_balance(90, sunlit_faces=1, warn=False)
    # At beta=90 the harmonized albedo is model-limited (reportable None); use the
    # raw *_model fields for display and flag them with an asterisk in the caption.
    solar = [PUB.direct_solar_absorbed_W_m2, SPEC.direct_solar_absorbed_W_m2, 0.0,
             h1.direct_solar_absorbed_W_m2]
    albedo = [PUB.earth_albedo_absorbed_W_m2, SPEC.earth_albedo_absorbed_W_m2,
              h0.earth_albedo_model_W_m2, h1.earth_albedo_model_W_m2]
    ir = [PUB.earth_ir_absorbed_W_m2, SPEC.earth_ir_absorbed_W_m2,
          h0.earth_ir_absorbed_W_m2, h1.earth_ir_absorbed_W_m2]
    net = [PUB.net_rejection_W_m2, SPEC.net_rejection_W_m2, h0.net_rejection_model_W_m2,
           h1.net_rejection_model_W_m2]
    x = np.arange(len(cases))
    w = 0.2
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.bar(x - 1.5 * w, solar, w, label="Direct solar absorbed", color="#d62728")
    ax.bar(x - 0.5 * w, albedo, w, label="Earth albedo absorbed", color="#ff7f0e")
    ax.bar(x + 0.5 * w, ir, w, label="Earth IR absorbed", color="#9467bd")
    ax.bar(x + 1.5 * w, net, w, label="Net emitted (rejection)", color="#2ca02c")
    ax.set_xticks(x)
    ax.set_xticklabels(cases, fontsize=8)
    ax.set_ylabel("Flux per planform (W/m^2)")
    ax.set_title("Plot 4 - Environmental-load decomposition (radiator at 20 C)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")
    ax.text(0.0, -0.22, "* beta=90 harmonized albedo is model-limited (sub-point model "
            "nulls); raw model values shown, not reportable as a physical load.",
            transform=ax.transAxes, fontsize=7, color="#555555")
    _save(fig, outdir, "plot4_load_decomposition.png")


def plot5(outdir):
    h0 = starcloud_harmonized_balance(90, sunlit_faces=0, warn=False)
    h1 = starcloud_harmonized_balance(90, sunlit_faces=1, warn=False)
    labels = ["Published\n633.08", "Spectral\n584.76",
              "Harmonized sunlit\n(b90, model*)", "Harmonized shielded\n(b90, model*)"]
    nets = [PUB.net_rejection_W_m2, SPEC.net_rejection_W_m2,
            h1.net_rejection_model_W_m2, h0.net_rejection_model_W_m2]
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    bars = ax.bar(labels, nets, color=[COL["pub"], COL["spec"], COL["harm"], "#8c564b"])
    for b, v in zip(bars, nets, strict=False):
        ax.text(b.get_x() + b.get_width() / 2, v + 4, f"{v:.1f}", ha="center", fontsize=8)
    ax.set_ylabel("Net rejection per planform at 20 C (W/m^2)")
    ax.set_title("Plot 5 - As-published vs harmonized (Starcloud, 293.15 K)")
    ax.grid(alpha=0.3, axis="y")
    ax.text(0.0, -0.16, "* beta=90 harmonized net uses the raw model albedo "
            "(model-limited; reportable net is None at the endpoint).",
            transform=ax.transAxes, fontsize=7, color="#555555")
    _save(fig, outdir, "plot5_published_vs_harmonized.png")


def plot6(outdir):
    """Beta sweep: Earth albedo (model) and IR vs beta, and net rejection vs beta.

    The dawn-dusk endpoint (beta=90) is marked as a model-limited point: the
    sub-point albedo model nulls there, so the reportable albedo/net are None and
    only the raw model values are shown. AI1 has no published solar absorptivity,
    so it is shown only as net-excluding-albedo (no full-net curve).
    """
    betas = np.arange(0, 91, 5)
    sc0 = [starcloud_harmonized_balance(b, sunlit_faces=0, warn=False) for b in betas]
    sc1 = [starcloud_harmonized_balance(b, sunlit_faces=1, warn=False) for b in betas]
    ai = [ai1_harmonized_balance(b, warn=False) for b in betas]

    fig, (axu, axl) = plt.subplots(2, 1, figsize=(7.2, 7.0), sharex=True)

    # Upper: Starcloud albedo (raw model) and Earth IR vs beta.
    axu.plot(betas, [x.earth_albedo_model_W_m2 for x in sc0], color=COL["spec"],
             marker="o", ms=3, label="Earth albedo (raw sub-point model)")
    axu.plot(betas, [x.earth_ir_absorbed_W_m2 for x in sc0], color="#9467bd",
             marker="s", ms=3, label="Earth IR absorbed")
    axu.axvline(90, color="gray", ls=":", lw=1)
    axu.set_ylabel("Absorbed flux per planform (W/m^2)")
    axu.set_title("Plot 6 - Starcloud environmental load and net rejection vs beta")
    axu.legend(fontsize=8)
    axu.grid(alpha=0.3)

    # Lower: net rejection vs beta (raw model net for Starcloud; AI1 net-excl-albedo).
    axl.plot(betas, [x.net_rejection_model_W_m2 for x in sc0], color=COL["harm"],
             marker="o", ms=3, label="Starcloud shielded (model net)")
    axl.plot(betas, [x.net_rejection_model_W_m2 for x in sc1], color="#8c564b",
             marker="^", ms=3, label="Starcloud one-side sunlit (model net)")
    axl.plot(betas, [x.net_excluding_albedo_W_m2 for x in ai], color=COL["ai1"],
             ls="--", marker="x", ms=3, label="AI1 net excl. albedo (alpha_s unpublished)")
    axl.axvline(90, color="gray", ls=":", lw=1)
    axl.text(0.97, 0.40, "beta=90 model-limited\n(reportable albedo/net = None)",
             transform=axl.transAxes, ha="right", va="center", fontsize=7,
             color="#555555")
    axl.set_xlabel("Beta angle (deg)")
    axl.set_ylabel("Net rejection per planform (W/m^2)")
    axl.legend(fontsize=8)
    axl.grid(alpha=0.3)
    fig.text(0.01, 0.005, "Note: the high-beta albedo decline is a property of the "
             "reduced-order sub-point model, NOT validated disk-integrated behavior.",
             fontsize=7, color="#555555")
    _save(fig, outdir, "plot6_beta_sweep.png")


def _save(fig, outdir, name):
    fig.tight_layout()
    path = Path(outdir) / name
    fig.savefig(path, dpi=130)
    plt.close(fig)
    print(f"wrote {path}")


def main():
    outdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "docs/reference-architectures/figures")
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"Harmonized geometry: tilt={HARMONIZED_TILT_DEG} deg, "
          f"F={harmonized_environment(90, warn=False).view_factor:.4f}")
    plot1(outdir)
    plot2(outdir)
    plot3(outdir)
    plot4(outdir)
    plot5(outdir)
    plot6(outdir)
    print("done.")


if __name__ == "__main__":
    main()
