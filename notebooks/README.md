# Notebooks

Interactive, engine-driven visualizations of the `orbital_thermal` model. These
are **verification / explanation** artifacts, not flight-validation or design
tools (see each notebook's scope-and-warning header and
`docs/VERIFICATION_AND_VALIDATION.md`).

## `phase_a_visual_boundary_model.ipynb` — B0.5 Phase A Visual Boundary Model

An interactive tour of the **existing** Phase A radiator-*boundary* model:
radiator equilibrium temperature, required area, net rejection, the exact Earth
view factor, effective sink vs beta angle, the McCalip edge-on view-factor
correction, and the one-node orbital transient waveform.

Every value and curve is produced by an `orbital_thermal` engine function through
the thin `orbital_thermal.visual_api` orchestration layer — **no physics is
reimplemented in the notebook**. Inputs are labelled by provenance
(`published` / `derived` / `assumed` / `corrected` / `design-variable` /
`sensitivity` / `unsupported/future`); plots carry units; model limitations
(sun-shielded contract, beta-90 albedo null) are surfaced next to the relevant
plots. The reference-case table is labelled and **does not rank** architectures.

### Install

The notebook stack is an optional extra so the core library stays numpy-only:

```bash
pip install -e ".[visual]"
```

(`[visual]` = jupyter, ipywidgets, plotly, nbformat, nbclient.)

### Run interactively

```bash
jupyter lab notebooks/phase_a_visual_boundary_model.ipynb
# or:  jupyter notebook notebooks/phase_a_visual_boundary_model.ipynb
```

Run all cells. The sliders (ipywidgets) drive Plotly figures; section 3 asserts
the baseline reproductions and will stop the run if the local package does not
match the verified anchors.

### Execute headlessly (verification / CI)

Execute end-to-end without a browser to confirm every cell runs (this is how the
notebook is validated; it does not replace the pytest suite):

```bash
jupyter execute notebooks/phase_a_visual_boundary_model.ipynb
# or, equivalently, via nbclient:
python -m nbclient notebooks/phase_a_visual_boundary_model.ipynb --timeout=300
```

A non-zero exit means a cell raised (including a failed baseline-reproduction
assertion in section 3).

### Conventions for committed notebooks

Commit notebooks **without execution outputs or widget state** (clear all outputs
before committing). Any reproducible data outputs belong under a clearly named
location such as `results/visual_model/`; this notebook writes none by default.

## `phase_b_stage1_chip_to_radiator_model.ipynb` — Phase B Stage 1 Chip-to-Radiator Model & Trade Study

An engine-driven tour of the **completed v1.1.0** Phase B **Stage 1** (single-phase)
reduced-order chip-to-radiator model — `orbital_thermal.coupled_model` (B4),
`architecture_cases` (B5), `trade_study` (B6) — and its six named trade-study Pareto
fronts (B7). It walks a representative rank-eligible case through the coupled Mode T /
Mode A solve (junction temperature, radiator temperature/area, pump power, pressure
drop, Reynolds/regime, single-phase margins, feasibility + reason codes), loads the
committed B6/B7 trade-study data, recreates the six Pareto fronts, and surfaces the
mass-accounting, Suncatcher/Track-R, and verification-status limitations.

Every number and figure is produced by an `orbital_thermal` engine function or read
from the committed B6/B7 artifacts (`docs/trade-study-points.csv`) — **no physics is
reimplemented in the notebook**. Inputs are labelled by provenance
(`design-variable`, plus registry `resolved`/`source_required`/… status); infeasible
and non-converged trade points are **reported, not dropped**; the reference-case table
**does not rank** architectures. Like the Phase A notebook, section 3 asserts baseline
reproductions (including the B4 Mode T/A collapse to the Phase A radiator law) and
stops the run if the local package does not match the anchors.

### Install

This notebook needs the interactive stack **and** the coolant-property backend, because
the coupled solve pulls in pinned CoolProp internally:

```bash
pip install -e ".[visual,fluids]"
```

(`[visual]` = jupyter, ipywidgets, plotly, nbformat, nbclient; `[fluids]` = the pinned
CoolProp backend the coupled loop evaluates.)

### Run interactively

```bash
jupyter lab notebooks/phase_b_stage1_chip_to_radiator_model.ipynb
```

Run all cells (from the repository root, so the committed trade-study CSV is found; the
notebook also auto-locates it from the installed package). The section-6 explorer
(ipywidgets) drives the coupled solve; the six Pareto figures are Plotly.

### Execute headlessly (verification / CI)

```bash
python -m nbclient notebooks/phase_b_stage1_chip_to_radiator_model.ipynb --timeout=600
# or:  jupyter execute notebooks/phase_b_stage1_chip_to_radiator_model.ipynb
```

A non-zero exit means a cell raised (including a failed baseline reproduction in
section 3). On Windows, `pyzmq` emits a benign `Proactor event loop` `RuntimeWarning`
during headless execution; the run still completes successfully, so no fallback is
required. The same committed-outputs conventions above apply (clear all outputs before
committing; the notebook writes no data outputs).
