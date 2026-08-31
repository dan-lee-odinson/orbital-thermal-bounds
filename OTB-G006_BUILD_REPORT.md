# `OTB-G006` — S6 two-phase trade-study extension · build report

**Base** `stage-2/s5-architecture-cases @ 8e094d9` · **Rulings applied** D139, D140, D143, D144, D145
**Witnessed tree** `f9d65bc9db6bce77b801882999d69ccacfe7dd32`

---

## 1. What was built

**The result of this milestone is a bounds result.** Under the adopted correlations and
their declared applicability domains, this loop's two-phase pressure drop is not
rank-eligible on any reachable input, so a ranked two-phase comparison cannot be
supported by them. The deliverable is the machinery that shows precisely why, and shows
it on the output rather than in prose: the points are all present, de-ranked, each
carrying the axis and the source note that de-ranked it.

Two files added, one modified. No physics module was touched; no correlation was
validated or revalidated here.

**`src/orbital_thermal/two_phase_trade_study.py`** (new). The declared two-phase grid;
the eligibility seam mapping production applicability results onto `PointCategory` and
`ReasonCode`; five trades — one mixed front and four two-phase-native; two F6-tagged
exports, one per-point and one per-front.

**`tests/test_two_phase_trade_study.py`** (new). 26 tests, one or more per criterion,
each driving the criterion's falsifier where it has one.

**`src/orbital_thermal/trade_study.py`** (modified, +34/−3). Three additive changes:
`TradeDef` gains a defaulted `candidate` filter; `pareto_front` consults it, defaulting to
the Stage-1 rule unchanged; `ReasonCode` gains three members. No existing enum value
changed, nothing added to `_CSV_FIELDS`, and `TRADES` still holds exactly six — appending
to it would move `summary()['fronts']` and break S6-5.

**The mandated mixed front stays, and so does the emptiness.** Both architectures appear
in its exported table; its non-dominated set is single-phase-only, and cannot be otherwise
while the adopted correlation's declared applicability stands. The three empty
two-phase-native fronts stay, marked `degenerate` with their notes rather than omitted.

## 2. What this does not claim

**The claim is bounded to the adopted correlations and their declared applicability
domains.** It is *not* a claim that a ranked two-phase comparison is impossible. A
different correlation set, or a source establishing applicability for single-component
vertical flow, would change the result without anything here being wrong.

**Evidence category is (a) + (c)** — the declared domains recorded on the registry entries,
plus the executable sweep that evaluates them. CHARTER §4 is satisfied at a+c. **Level d
remains pending project-wide and is not claimed here.**

No new physics. No correlation validated. No harmonized comparison — that is R3. **No
"best architecture" claim**: fronts and the assumptions that drive them, never a winner.
No microgravity validation; every ranked export containing two-phase cases carries the F6
ranking-scope limitation verbatim. Mass is modeled component mass where it appears at all,
never total-system.

**No two-phase point carries `radiator_temperature_K` or `radiator_area_m2`** — the
Biswas/Suncatcher harmonization's axes. The guard is mechanical and is exercised.

Nothing is closed. `status: closed`, `disposition`, `rationale` and `classification` are
the Director's alone.

## 3. STEP ZERO and environment

Run before anything was read past the handoff and before any file was touched. All six
lines matched exactly.

```
python     : 3.14.4
CoolProp   : 7.2.0
import from: C:\Users\wolfe\.claude\sessions\orbital-thermal-bounds\src\orbital_thermal\__init__.py
summary    : {'total_points': 144, 'feasible_ranked': 110, 'gate_rejected': 14, 'nonconverged': 20, 'fronts': 6, 'degenerate_fronts': 0}
front sizes: [2, 48, 4, 3, 4, 4]
degenerate : [False, False, False, False, False, False]
export sha : 16d396823e1ca2c7da6ac51487ab78170d2d642ab2acd899d7830ae207c30ef5
```

**The hash computed is the export ROWS** — `sha256("\n".join(ts.to_csv_rows(res)))`, no
trailing newline. That is the S6-5 criterion. `CoolProp` is `7.2.0`, the pin. Python
3.14.4 is past this repo's declared support (`requires-python = ">=3.10"`, classifiers to
3.12); it passes, stated as fact rather than assumed.

**Byte-identity, tested rather than inherited (D143).** `generate_trade_study.py` writes
via `write_text` with no `newline=`, so on this platform it emits CRLF:

| artifact | bytes | CRLF | sha256 |
|---|---|---|---|
| regenerated via `write_text` | 74361 | 145 | `ec7569ab…` |
| working tree | 74361 | 145 | `ec7569ab…` |
| committed blob | 74216 | 0 | `4d9a90da…` |

`regenerated == working tree` **True**; `regenerated.replace(CRLF, LF) == blob` **True**;
`git status` on the file empty. D143's prediction holds. Regeneration went to a scratch
path — nothing was written into the repository.

## 4. The eligibility seam

**The source is the production applicability result, not `assess_leg`.** Measured at
`8e094d9`:

| | Ammonia | Water | R134a |
|---|---|---|---|
| `two_phase.critical_heat_flux` | value, `is_sourced=False`, `fluid`/DE_RANK/`evaluated_and_failed` | `is_sourced=True`, no violations | raises `SourceGatedFluidError` |
| `two_phase_loop.two_phase_pressure_drop` | `composition`+`orientation` DE_RANK | same | — |
| `two_phase_architecture_cases.assess_leg` | `eligible=False` | `eligible=False` | `eligible=False` |

`assess_leg` blocks every fluid on `geometry` and `orientation`, both
`Cause.NOT_EVALUATED` — that boundary cannot derive the branch parameter and refuses to
pretend it checked. A study built on it would report an empty front for a reason about the
boundary rather than about the case, which is a different claim entirely. Both halves are
asserted in `test_s6_1_the_seam_reads_the_production_result_not_the_s5_boundary`.

**Eligibility is per leg, because applicability is.** Each point carries `leg_status` for
`chf`, `pressure_drop` and `pump_inlet`; the point-level category is the worst of them,
and each trade admits on the leg its own axes depend on. The unevaluable set is derived
from `Cause.NOT_EVALUATED`, never from `BLOCK`, which carries both meanings.

**The de-rank vocabulary is a lookup, not an invention.** `_CONSEQUENCE_TO_STATUS` is
imported from `two_phase.py` rather than restated; `PointCategory.SENSITIVITY_ONLY`
already existed.

## 5. Criteria

| | result |
|---|---|
| **S6-1** | No point with a de-ranked leg is `FEASIBLE_RANKED` — zero offenders across 72 points. The de-rank costs front membership: no two-phase point is a member of any pressure-drop-dependent front. |
| **S6-2** | Every point with a non-empty unevaluable set carries `AXIS_NOT_EVALUATED`. Exercised both ways — a `BLOCK` whose axis *was* evaluated is not reported as unevaluable. |
| **S6-3** | F6 text verbatim, line one, on the two-phase CSV and on every front table containing two-phase cases, the mixed table included. `docs/trade-study-points.csv` contains `microgravity` zero times and is untouched. |
| **S6-4** | Exactly one mixed front, `heat_load_W × pump_power_W`. Both architectures reach it through `pump_energy(..., boundary="fluid_loop")`, asserted by equality against a direct call. The density collapse is declared for pump work in `PUMP_WORK_MODEL`, not inherited. No other front carries both architectures. |
| **S6-5** | Export-rows sha `16d39682…` unchanged; counts `144 / 110-14-20`; fronts `2·48·4·3·4·4`; zero degenerate. `TRADES` still six. The 21 existing trade-study tests pass unchanged. |
| **S6-6** | Ammonia appears in the CHF front's exported table — 24 rows, `sensitivity_only`, exclusion text on each row. Ammonia is **not** in `member_point_ids`; all members are Water. Both falsifiers driven. |

**The C11 collapse.** `two_phase_loop` declares the homogeneous `rho_mix` at `x_mean` for
the **static** term. S6 carries the same representative value into the **pump-work**
denominator — a different term doing different work — so `PUMP_WORK_MODEL` records it with
its own basis naming what is new: there it stood behind a `rho·g·h` head, here behind a
work term reported as a ranked objective.

## 6. The bounds result

**There is no reachable input under which this loop's two-phase pressure drop is
rank-eligible.** Confirmed independently by the Director at `8e094d9`, sweeping every
reachable input of `two_phase_pressure_drop` for both fluids:

| composition | orientation | outcome |
|---|---|---|
| `single_component` | horizontal | `is_applicable=False` — `composition`/`de_rank` |
| `single_component` | vertical (all) | `is_applicable=False` — `composition`, `orientation` |
| `two_component` | any | raises `NotRankEligibleError` — does not return |

`single_component` is the CHARTER's declared architecture, and it de-ranks on
**composition**: the frictional correlation is declared for two-component flow. **This is
not an artifact of the parameter choices in this build.**

Pump work is computed *through* the pressure drop and inherits the de-rank. **S6-1 then
forces the outcome** — no two-phase point may be `FEASIBLE_RANKED`, so none enters a
non-dominated set on any pressure-drop-dependent front:

| front | members | note |
|---|---|---|
| `chf_margin_vs_load` | 6, all Water | the CHF leg is clean for Water |
| `pressure_drop_vs_mass_flux` | 0 | empty: no rank-eligible point |
| `quality_vs_pump_power` | 0 | empty: no rank-eligible point |
| `subcooling_margin_vs_pressure_drop` | 0 | empty: no rank-eligible point |
| `heat_load_vs_pump_power` (mixed) | 2, both single-phase | two-phase side de-ranked on the pump-work leg |

**This was not engineered around, and the emptiness is the finding rather than a
shortfall.** Every point and its numbers appear in the exported tables, de-ranked, with
the reason on the row; `pareto_front` marks the empty fronts `degenerate` with an explicit
note rather than omitting them. Under the adopted correlations and their declared
applicability domains, the ranked two-phase comparison S6 set out to build cannot be
supported — and the machinery now says so on the output, per point, per axis, with the
source note attached.

**One correction belonging to the Director, recorded at D145, not to this build.** D144
mandated the mixed front on an analysis that checked that `pump_energy` accepts a pressure
drop and that the mixture-density collapse was declared and shipped, but did not check
whether the pressure-drop result is rank-eligible. It cannot be.

## 7. A defect this build introduced

The first working version broke S6-5, in exactly the shape D140 describes.

`pareto_front` records membership by **mutating** `point.pareto_fronts` and
`point.dominated_reasons`, and both are carried in `_CSV_FIELDS`. Ranking the caller's own
Stage-1 points in the mixed front wrote a seventh front name into their export rows.

```
summary    : 144 / 110-14-20, fronts 6, degenerate 0   <- unchanged
front sizes: [2, 48, 4, 3, 4, 4]                       <- unchanged
export sha : 716255a77a1b2dab...                       <- MOVED
```

Three of the four S6-5 fields matched the form while the rows had changed. `_detached()`
now copies the Stage-1 points with fresh membership state, and
`test_s6_5_building_the_two_phase_study_does_not_move_the_stage1_export` computes the sha
**after** building — checking it before is blind to this failure mode. The mechanism was
reproduced independently by the Director without this module: a seventh trade over the
Stage-1 points leaves counts and all six front sizes identical and moves the export sha to
`8677be01…`.

A second defect was caught by the **existing** S5 apparatus, not by anything written here:
constructing the channel geometry inside the evaluator made `geometry` — a declared case
fact — read as a quantity production derives, failing five D118/D119 tests. The apparatus
was correct and was not modified; the channel now arrives as a parameter,
`DECLARED_CHANNEL`, and all 238 of those tests pass.

## 8. Verification, and what is open

`pytest -q` **from a bare checkout with nothing installed**, via the witnessed script —
both runs in a single disable window, the export taken before the window opened:

```
tree f9d65bc9db6bce77b801882999d69ccacfe7dd32
WITNESS 1  import source: ...\otb-bare-f9d65bc-eK9zdS\src\orbital_thermal\__init__.py  PASS
plain      1371 passed, 3 xfailed     export paths 48, repo paths 0     WITNESS 2 PASS
werror     1371 passed, 3 xfailed     export paths 48, repo paths 0     WITNESS 2 PASS
.pth RESTORED; post-restore probe resolves to the repo
```

**Before** 1345 passed, 3 xfailed at `8e094d9` (bare, witnessed). **After** 1371 passed,
3 xfailed — the same 1345 plus 26 new, none removed or changed.

`python -m ruff check src/ tests/ scripts/` — **All checks passed.**

Frozen blobs re-checked after the build: `coupled_loop.py` `1e6b0db9…`,
`ACCEPTANCE_CRITERIA_OTB-G005.md` `185ca39b…` — both unchanged.

**Not touched.** `.gitattributes` and `docs/trade-study-points.csv` (D-29, apparatus,
discharge S7/S8). `docs/trade-study-data.md` (D-27). No S5 classifier apparatus rebuilt.
No existing test changed. No fan-out used — S6's scope named no job for one.

**Open.**

1. The §6 bounds result is reported, not repaired. What, if anything, follows from it is
   the Director's.
2. `afe3e64c88e85e84` remains **unverified** — the D133 grid file is not in this
   repository. Unchanged, and out of S6 scope.
3. The authoritative acceptance criteria are 193 lines, sha
   `2ef204f0fb4916ee8f4fb53fe7707c4a17bba679ef98ecd796920494be54c63a`. **That sha was not
   recomputed here** — the file is not in this tree. This build follows the D144 ruling
   text for S6-4 and S6-6.
