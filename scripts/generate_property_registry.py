"""Generate docs/property-provenance.md from the B1 registry.

The registry (:mod:`orbital_thermal.registry`) is the single source of truth; this
script renders it to a human-readable provenance table so the docs never drift
from the code. Run from the repository root::

    python scripts/generate_property_registry.py
"""

from __future__ import annotations

from pathlib import Path

from orbital_thermal import registry

OUT = Path("docs/property-provenance.md")


def _cell(x: object) -> str:
    return "" if x is None else str(x)


def _value(e: object) -> str:
    v = getattr(e, "value", None)
    if v is None:
        return "-"
    return f"{v:g}"


def _rows(entries: list) -> str:
    lines = []
    for e in entries:
        src = e.source.citation if getattr(e, "source", None) else ""
        eligible = "yes" if e.rank_eligible else "**no**"
        lines.append(
            f"| `{e.id}` | {e.name} | {e.provenance.value} | {e.status.value} "
            f"| {_value(e)} | {_cell(getattr(e, 'units', ''))} | {_cell(src)} | {eligible} |"
        )
    return "\n".join(lines)


HEADER = "| ID | Name | Provenance | Status | Value (SI) | Units | Source | Rank-eligible |"
SEP = "|---|---|---|---|---|---|---|---|"


def render() -> str:
    s = registry.summary()
    props = registry.PROPERTIES
    corrs = registry.CORRELATIONS
    counts = ", ".join(
        f"{k}={v}" for k, v in sorted(s.items()) if k not in ("total", "rank_eligible")
    )
    n_blocked = s["total"] - s["rank_eligible"]
    summary_line = (
        f'**Summary:** {s["total"]} entries, {s["rank_eligible"]} rank-eligible, '
        f"{n_blocked} blocked ({counts})."
    )
    prov_line = (
        "`published` | `derived` | `assumed` | `corrected` | "
        "`design_variable` | `sensitivity` | `unsupported`"
    )
    return f"""# Phase B property, source, and correlation registry (B1)

> **Generated from `orbital_thermal.registry`** by `scripts/generate_property_registry.py`.
> Do not edit by hand; edit the registry and regenerate. This is a design-intent /
> data-provenance record, not a validation of any physical result.

Every load-bearing Phase B property and correlation is registered with an explicit
**provenance class** and a **resolution status**. The registry enforces one invariant:
a non-rank-eligible entry **cannot silently enter a ranked Phase B case**
(`registry.assert_rank_eligible`). Unresolved items are recorded with a machine-visible
blocker status and no value -- they are never invented (no-invention policy; B0 plan
Sections 2, 4.2, 4.5, 4.6).

{summary_line}

Resolved coolant transport values are **derived** from CoolProp 7.2.0 at the saturated-liquid
300 K reference state and re-checked in `tests/test_registry.py`.

## Provenance classes
{prov_line}

## Blocker statuses (keep an entry out of ranked cases)
`resolved` (rankable) | `sensitivity` | `future` | `source_required` | `backend_required` |
`unsupported` | `not_rank_eligible`

## Properties (coolants, solids, containment)

{HEADER}
{SEP}
{_rows(props)}

## Correlations (thermal, hydraulic)

{HEADER}
{SEP}
{_rows(corrs)}
"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render())
    s = registry.summary()
    print(f"wrote {OUT}: {s['total']} entries, {s['rank_eligible']} rank-eligible")


if __name__ == "__main__":
    main()
