# OTB-G001-FIXES — Packaging Report

**Gate:** `OTB-G001-FIXES` · orbital-thermal-bounds · Phase B Stage 2, S2
**Branch:** `stage-2/s2-evaporator` · `e4e8c7d` → **`ce74fd3`** · METHOD v1.0 · Tier 2
**Date:** 2026-07-25 · **Builder:** Claude (Claude Code)

> **`main` untouched at `155b10c`. No merge, no tag, no release. Nothing in the shared folder.**

---

## 1. Result

| | before (`e4e8c7d`) | after (`ce74fd3`) |
|---|---|---|
| **Packet run** — reconstructed tree, no install | **23 errors during collection · 0 tests ran** | **697 passed · 3 xfailed · 0 failed · 0 errors** |
| Isolation line | `orbital_thermal visible in venv: False` | `orbital_thermal visible in venv: False` |
| **A. imports + runs from the packet alone** | **NO** | **YES** |
| **B. strict criterion (zero xfailed)** | NO | NO — *expected, not mine* |
| In-repo installed run | 697 passed / 3 xfailed | **697 passed / 3 xfailed** (unchanged) |

Both numbers are from `reproduce_packet_run.py --repo <checkout>`, run before the change
and again after committing. The isolation line read `False` on every run.

**The after-figure is 697, not the 695 the handoff predicted.** The handoff measured
`pythonpath` alone, which left the two install-dependent tests failing. Because both were
made to work rather than excluded, the packet run now matches the in-repo run **exactly** —
which is the stronger outcome: there is no longer any difference between what a reviewer
sees from the packet and what a developer sees in the repo.

---

## 2. What changed

Three files, nothing else. `src/`, test logic, the registry and the ledger are untouched.

### 2.1 `pyproject.toml` — one line

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]        # added
```

Takes collection from 23 errors to the full suite. The comment in the file records *why*
it is a correctness property and not packaging tidiness: a suite whose result depends on
ambient install state can lie about itself, which is exactly what happened in the 0/16
witness incident.

### 2.2 `tests/test_examples.py` — pass the import path to the child

A subprocess does not inherit pytest's `pythonpath`, so from a bare tree the child could
not import the package even though the parent session could. It now receives this
interpreter's `sys.path` via `PYTHONPATH`, **prepended** to any inherited value so a
caller's own setting still applies but cannot shadow the package under test.

### 2.3 `tests/test_smoke.py` — version single-sourcing, checked in both environments

**This differs deliberately from the approach the handoff proposed. The proposed one does
not work.** See §3.1.

The invariant (audit item 11a) is that `__version__` is never a hardcoded literal that can
drift from pyproject's. It is now checked in **both** environments rather than skipped in
one — a review packet runs with nothing installed, and a skip would leave the invariant
unguarded precisely there:

- **Distribution installed** — `__version__` equals the metadata version, **and** both
  equal the version declared in pyproject. This is **strictly stronger than before**: the
  old test compared only against the metadata, so it could not detect the two drifting
  together.
- **No distribution** — assert the documented `0.0.0+unknown` sentinel, and assert
  `__init__.py` does not contain the pyproject version as a literal, which is the drift
  the test exists to prevent.

`pyproject.toml` is parsed with a `[project]`-scoped regex rather than `tomllib`, because
the package still supports Python 3.10 (`requires-python = ">=3.10"`) where `tomllib` is
absent. The regex is scoped to the `[project]` table so a `version =` line elsewhere
cannot be picked up.

**Nothing was skipped, xfailed, deleted, or loosened.** Both tests do real work in both
environments.

---

## 3. Two things this handoff did not anticipate

The handoff asked to be checked rather than trusted. Two items:

### 3.1 The suggested fix for `test_version_is_single_sourced` would not have worked

The handoff (and `FREEZE_BLOCKER.md` §5) proposed that the test *"falls back to reading
the version from `pyproject.toml` when `importlib.metadata` finds no distribution — and
still asserts the two agree."*

That fails. `orbital_thermal/__init__.py` does **not** fall back to pyproject:

```python
try:
    __version__ = _version("orbital-thermal")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"
```

Uninstalled, `__version__` is the sentinel `0.0.0+unknown`, while pyproject declares
`1.1.0`. Asserting that the two agree would fail, not pass — the same lost build cycle the
handoff was trying to spare by correcting its own earlier "skip is acceptable" advice.

Implemented as described in §2.3 instead, which holds in both environments and is stronger
than the original in the installed one. **The alternative — making `__init__.py` read
pyproject when uninstalled — was deliberately not taken:** it would mean editing `src/`,
which is out of scope, and it would put version-parsing logic into the shipped package to
satisfy a test.

### 3.2 `ruff check .` was not clean before this change either

The definition of done asks that `ruff check .` "stay clean". It was not clean at
`e4e8c7d`. Measured by stashing this commit's three files and re-running:

```
before (e4e8c7d): Found 8 errors
after  (ce74fd3): Found 8 errors     — identical
```

All eight are in `notebooks/phase_a_visual_boundary_model.ipynb` (`I001`, three `F401`,
two `E741`, two `E501`) and none is in a file this commit touches. **They are not fixed
here**: notebooks are outside the authorised scope, and editing them would move
`artifact_sha256` for no gain.

For the record, the linting the project actually gates on is clean:
`ruff check src tests scripts` → **All checks passed!**, and the CI ruff job is
`--exit-zero` (report-only) by design.

---

## 4. Verdict B is unmet, and is not a build task

`reproduce_packet_run.py` reports **B: NO** because the strict criterion demands zero
`xfailed` and this suite has three, all in
`tests/test_sink.py::TestPhysicalAlbedoFacts`. They are deliberate, documented statements
that `disk_integrated_albedo_factor` is unimplemented, written so they convert to failures
the day it lands.

They were **not** touched. Deleting or rewriting them would destroy disclosure to make a
checker green — the same shape as F-07, which was ruled a blocker last round. Whether
METHOD's packet checker should accept an honest `xfail` is a Director question about the
tool, not something a build can resolve.

---

## 5. Verification performed

```bash
# before, from the fix-inputs bundle
python reproduce_packet_run.py --repo <checkout>     # 23 errors, 0 tests, A: NO

# after
python reproduce_packet_run.py --repo <checkout>     # 697 passed / 3 xfailed, A: YES
pytest -q                                            # 697 passed, 3 xfailed
ruff check src tests scripts                         # All checks passed!
```

The isolation check printed `orbital_thermal visible in venv: False` on every packet run,
so no result here is measuring an installed copy.

---

## 6. Definition of done

- [x] `pythonpath = ["src"]` in `[tool.pytest.ini_options]`
- [x] Both install-dependent tests made to work without an install — **not skipped, not xfailed, not deleted**
- [x] `reproduce_packet_run.py` reports **A: YES**, isolation line `False`. **B still NO** (three deliberate xfails), as expected and not mine to move
- [x] In-repo installed run unchanged: **697 passed / 3 xfailed**; `ruff check src tests scripts` clean
- [x] Small reviewable commit on `stage-2/s2-evaporator`, pushed. No merge, no tag, no release
- [x] This report, including both reproduce numbers and the two unanticipated items (§3)
- [x] Nothing deposited to `Claude_GPT_Shared_Workflow`
- [x] Pickup neither run nor simulated; no adversarial subagent launched

---

## 7. Handback

New head **`ce74fd3`** for Cowork to re-freeze against: recompute `artifact_sha256`,
regenerate the inventory and manifest, re-run `verify_packet.py`, then zip.

**The ledger's ten `commit` fields still read `e4e8c7d1b8…`** and now point at the
previous head. `commit` is a builder field, so moving it is Cowork's call as part of the
re-freeze — flagged rather than changed here, since the packet scope and hash are being
recomputed anyway and a second edit from this side would race that.

One knock-on worth noting: **`PACKET_LAYOUT.tsv`'s 82-file scope does not include this
report or `pyproject.toml`.** `pyproject.toml` *is* in scope (the packet run picked up the
new `pythonpath`, which is how it went green), but if the round-2 packet is meant to carry
this report the scope needs an 83rd row.
