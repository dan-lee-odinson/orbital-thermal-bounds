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
