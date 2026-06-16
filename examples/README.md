# Examples

Runnable, self-contained scripts that exercise the public `orbital_thermal` API.
Each prints its results next to the published anchor value so you can see the
model reproduce the papers. Run them from the repository root after installing
the package (`pip install -e .`):

```bash
python examples/01_equilibrium_and_area.py
python examples/02_edge_on_correction.py
python examples/03_transient_orbit.py
```

| Script | What it shows | Needs |
|---|---|---|
| `01_equilibrium_and_area.py` | The steady one-node radiator balance, its inverse, the exact area-ratio law, and the lumped effective sink. | numpy |
| `02_edge_on_correction.py` | The paper-three headline: the +6.35 K edge-on view-factor correction and its growth with orbit beta angle. | numpy |
| `03_transient_orbit.py` | An orbit-coupled transient marched to a periodic steady state, and the peak the steady averaged-sink assumption misses. | numpy |

These are illustrations of the model, not a substitute for the verification
suites. For the full numerical reproduction of every published number, run
`python scripts/reproduce_all.py` (see the repository README and
`docs/VERIFICATION_AND_VALIDATION.md`).
