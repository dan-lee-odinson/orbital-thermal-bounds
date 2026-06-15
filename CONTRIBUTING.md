# Contributing

Thanks for your interest. This is an independently developed, reduced-order research
package; contributions — especially **scientific scrutiny** — are welcome.

## Development setup

```bash
git clone https://github.com/dan-lee-odinson/orbital-thermal-bounds.git
cd orbital-thermal-bounds
python -m venv .venv && source .venv/bin/activate
pip install -e ".[fluids]"
pytest
```

Python 3.10+ is required. The `[fluids]` extra (CoolProp 7.2.0) is only needed for the
ammonia coolant screen.

## Testing requirements

- All tests must pass (`pytest`): currently 259 passing, 3 intentional `xfail`s.
- New behavior needs new tests. New public functions need input-domain validation and a
  test that exercises it.
- Do **not** edit published or oracle expected values to make a test pass. The McCalip
  oracle is SHA-256-pinned by design.

## Style

- Match the surrounding code; keep the core dependency-light (numpy only; CoolProp stays
  behind the `[fluids]` extra).
- Validate inputs at public boundaries (see `orbital_thermal._validate`).
- Prefer small, reviewable commits with a clear message.

## Scientific changes

A change to a model, equation, constant, or published number must include:
- the derivation or source for the change;
- a reproduction of the affected result before and after;
- updated tests and, where relevant, the verification scripts;
- a note on any impact to published values or DOIs.

If you believe a published result is wrong, open a **Scientific / mathematical
discrepancy** issue (template provided) rather than silently changing it.

## Preserving reproducibility

Do not break the ability to reproduce `v1.0.0`: keep pinned inputs, hashes, DOIs, and
verification scripts intact, and call out any intentional change to public behavior.

## Public API

The import package is `orbital_thermal`. Avoid breaking public function names, signatures,
or defaults; if a break is necessary, document it in `CHANGELOG.md`.

## AI-assisted contributions

This project was developed through a documented, human-directed, multi-model AI workflow.
If you use AI assistance, that's fine — please disclose it in the pull request and take
responsibility for verifying correctness yourself.
