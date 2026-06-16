# Ammonia property model

## What this is

Executable thermophysical-property calculations supporting the coolant
screen in "The AI1 Design Point" (doi:10.5281/zenodo.20670771). The paper
quotes ammonia properties as NIST Chemistry WebBook (SRD 69) reference
values and excludes them from its assertion suite's verification scope.
The `orbital_thermal.fluids` module computes the same quantities with
CoolProp's HEOS backend, and `tests/test_ammonia.py` asserts agreement
with the paper's quoted values at display precision:

| Quantity | Paper (NIST) | Computed (CoolProp) |
|---|---|---|
| Critical temperature | 405.5 K | 405.56 K |
| Critical pressure | ~113 bar | 113.63 bar |
| P_sat at 353.16 K | 41.4 bar | 41.42 bar |
| P_sat at 358.91 K | 46.8 bar | 46.84 bar |
| P_sat at 374.17 K | 63.8 bar | 63.81 bar |
| P_sat at 391.47 K | 88.4 bar | 88.36 bar |

Two independent property sources agreeing at display precision
cross-validates both. `results/tables/ammonia_properties.csv` tabulates
the full set of paper temperatures; regenerate it with
`python scripts/generate_ammonia_table.py`.

## Provenance and reproducibility

Property values are reproducible only against a pinned CoolProp version
and equation of state. Every generated table embeds
`orbital_thermal.fluids.provenance()`: CoolProp version, HEOS backend,
and the BibTeX key of the underlying ammonia EOS. If CoolProp is
upgraded, regenerate the table and diff it; any change beyond the last
displayed digit requires investigation before adoption (oracle-freeze
discipline).

## Scope limits

Property calculations verify thermodynamic consistency only. They
establish nothing about:

- component pressure ratings or loop design margins;
- pump cavitation or two-phase flow behavior;
- seal and material compatibility with ammonia;
- long-duration corrosion or reliability;
- whether SpaceX's AI1 actually uses ammonia (unconfirmed in reporting;
  the paper screens the coolant *class*, not the design).

## Publication-scope note (decision pending)

With these calculations in place, the repository now supports the
stronger claim that all displayed values *including* fluid properties are
machine-verified. The published companion PDF's verification-scope
sentence (Option B wording) remains accurate for that archived version;
claiming the stronger scope on the record would require a new Zenodo
version of the paper. Until that decision is made, this upgrade is
repository-only.
