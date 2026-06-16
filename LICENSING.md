# Licensing

This repository is licensed by component. The packaged Python distribution
declares **MIT** and ships only the software license (`LICENSE-MIT`).

## Software -- MIT (`LICENSE-MIT`)

- `src/` (the `orbital_thermal` package)
- `tests/`
- `scripts/` (figure/table generators)
- root verification suites: `verify_suite.py`, `verify_suite.wl`
- `companion/verify_ai1.py`
- packaging: `pyproject.toml`

## Papers, documentation, figures -- CC BY 4.0 (`LICENSE-DOCS-CC-BY-4.0`)

- the manuscripts (`orbital-thermal-preprint.tex/.pdf`,
  `orbital-thermal-resolution-proof-v3.md`, `companion/ai1-design-point.tex/.pdf`,
  and the `companion/response-to-*.md` review letters)
- `docs/`
- `results/figures/`, `results/tables/`

This matches the published preprints (doi:10.5281/zenodo.20650893 and
doi:10.5281/zenodo.20670771).

## Vendored third-party -- upstream MIT

- `external_models/mccalip_thoughts/` (Andrew McCalip's "thoughts" model, vendored
  for offline oracle verification) retains its upstream MIT license. The upstream
  license statement is reproduced verbatim in
  `external_models/mccalip_thoughts/UPSTREAM-LICENSE.md`.
