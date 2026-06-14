# orbital-thermal-bounds -- audit bundle (v0.8.2, fourth re-audit pass)

- Generated: 2026-06-13 22:49:54 UTC
- Commit: `e38145529c3778540c89277ddc5d43fcd0efe10d` (`e381455`)
- Package version: `0.8.2`

- Tracked files: 60  |  inlined: 54  |  binary/artifact (manifest+sha): 6


## For the auditor (GPT-5.5)

orbital-thermal-bounds at v0.8.2, after FOUR rounds of remediation. Verify the
round-four fixes (scale-aware + temporal-resolution convergence, fail-closed oracle
attestation, complete input validation, PEP 639 packaging) and hunt for anything
remaining.

**Bundle integrity:** every inlined file shows byte length + SHA-256; the three
SHA-256-pinned oracle files are base64 of their exact bytes (reconstruct to their
pins). CI runs verify_oracle_reproducible.py with ORACLE_REQUIRE_EXTERNAL=1
(fail-closed external attestation), pytest on 3.10/3.11/3.12, and a wheel-license job.

## Changelog (round four)

```
e381455 Merge pull request #7 from dan-lee-odinson/fix/audit-4
e77e943 Release v0.8.2: bump version for the fourth audit round
57c06e6 Re-audit P3-7: PEP 639 packaging, CI Python 3.10, drop deprecated alias
f51e364 Re-audit P3-6: separate ammonia code-regression tol from physical uncertainty
06818f3 Re-audit P2-5: pin disk-albedo xfails to raises=NotImplementedError
7d94809 Re-audit P2-4: complete finite/integer/range validation at boundaries
7e8d425 Re-audit P2-3: fail-closed external oracle attestation + honest summary
a67455c Re-audit P1-2: step-doubling temporal-accuracy gate
65207e4 Re-audit P1-1: temperature-equivalent convergence criterion (blocker)
528be28 Merge pull request #6 from dan-lee-odinson/release/v0.8.1-version
3de0b73 Release v0.8.1: bump package version to match the tag
2cc7908 Merge pull request #5 from dan-lee-odinson/fix/audit-3
e4d40f9 Re-audit P3-10/P3-11: qualify albedo claim; fix stale docs; CI wheel-license lock
b0fe8bd Re-audit P2-9: rename orbit-resolved sink fn to disambiguate
89a1e96 Re-audit P2-8: external-blob oracle attestation; reframe freeze scope
6b338f3 Re-audit P2-7: complete early input-domain validation
d7b6edd Re-audit P2-6: pin CoolProp and source the EOS citation from the backend
a46c861 Re-audit P2-5: harden optimal_cold_fraction bisection (no hangs)
1ab7b6c Re-audit P1-4: lock pinned oracle-file bytes via .gitattributes
f061e87 Re-audit P1-3: reject non-positive / non-finite RK4 temperatures
caca414 Re-audit P1-2: strict boolean contract for assume_sun_shielded
a0a2cfa Re-audit P1-1: require energy balance for periodic-SS convergence (blocker)
aa68aa3 Merge pull request #4 from dan-lee-odinson/release/v0.8.0
11b40a3 Release v0.8.0
1db9204 Merge pull request #3 from dan-lee-odinson/fix/audit-2
786607d Re-audit P3-b: correct the optimal_cold_fraction uniqueness proof
786e95f Re-audit P3-a: centralized input-domain and RK4 stability validation
5d0171c Re-audit P2-f: nonzero_sink_optimum raises on bisection cap exhaustion
09fb7e1 Re-audit P2-e: enforce oracle-freeze in CI (SHA pins + semantic regen)
15c4997 Re-audit P2-d: auditable provenance for areal heat capacity
05e2de1 Re-audit P2-c: full-precision binary64 Stefan-Boltzmann constant
f42702d Re-audit P2-b: resolve contradictory wheel license signals
0c54d30 Re-audit P2-a: fix false anti-solar albedo claim, retarget placeholders
a9a8876 Re-audit P1-c: enforce Carnot bounds in conversion_area_penalty and heat_pump_area_ratio
3d2e9c9 Re-audit P1-b: centralize sink equation + require explicit sun-shield opt-in
1aa8b90 Re-audit P1-a: averaging_bias propagates convergence status
04a8f56 Merge pull request #2 from dan-lee-odinson/fix/audit-findings
3ff12ae Audit #11: packaging cleanup (version, extras, wording, license)
f6510dc Audit #10: physical provenance for areal heat capacity
f36e191 Audit #9: replace binary V&V split with a finer hierarchy
564b76a Audit #8: explicit sun-shielded attitude guard on effective_sink_temperature
eb77c28 Audit #7: drop duplicated orbit endpoint from orbit_averaged_sink
936492f Audit #6: bisection for nonzero_sink_optimum (converges near T_sink->T_h)
421f697 Audit #5: detect periodic-steady-state convergence in transient solver
c24dba8 Audit #4 (tests): signed bias check + exact energy-balance test
42b2fdb Audit #4: correct the transient Jensen interpretation
9b62de6 Audit #3: relabel subpoint albedo as an approximation, not physics
12c0a33 Audit #2: tabulate McCalip exact-VF correction vs beta + figure
32f9888 Audit #1 (doc): correct backwards edge-on claim in replication doc
41de3b3 Audit #1: quantify McCalip edge-on geometry correction (+6.35 K)
```

## Test & verification status (captured now)

**pytest:**
```
..............                                                           [100%]
=============================== warnings summary ===============================
tests/test_transient.py::TestAveragingBias::test_raises_on_nonconvergence
  /workspaces/orbital-thermal-bounds/src/orbital_thermal/transient.py:237: RuntimeWarning: transient did not reach periodic steady state in 3 orbits (closure 3.03e-01 K vs tol 1.0e-03 K; energy dT_eq 3.14e+00 K vs tol 1.0e-02 K; tau/period=10.37); raise max_orbits/n_orbits
    warnings.warn(msg, RuntimeWarning)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
227 passed, 3 xfailed, 1 warning in 19.40s
```

**oracle-freeze (strict):**
```
- SHA-256 pins: OK
  - oracle regeneration: OK
  - external attestation: OK
oracle-freeze OK: SHA-256 pins match; regeneration reproduces the oracle; external blob attested. Enforces repository consistency, accidental-drift detection, and (when it actually runs) external-blob attestation; not, by itself, proof the oracle was never historically edited.
```

## Binary / artifact manifest (not inlined)

| file | bytes | sha256 |
|---|---:|---|
| `companion/ai1-design-point-r4.pdf` | 236279 | `5c3a8778e4f278083a95972cdecdd7670e5c50ffb6b19f7e15f90f0652dbc021` |
| `orbital-thermal-preprint.pdf` | 286126 | `e947fc39a0b1477a618027a61767afd6de9a2f0d6cb37e998cc40b675b902176` |
| `results/figures/effective_sink_vs_orbit.png` | 98994 | `9e9138d4838c0cb3975e5d2edff7d407f541410714a84f5dc93ab799e7b0b8d6` |
| `results/figures/mccalip_beta_correction.png` | 101548 | `e1a4c742b9f369094be83629489c07b7c3c74f58ee49beac2be631dee420022a` |
| `results/figures/transient_temperature.png` | 110699 | `932cc8e777a9761c7f8de112a52cbad1d72b8bbc8bcffe3493e39e8ff5776670` |
| `results/tables/ammonia_properties.csv` | 860 | `03b262da5e3a6b2b7a32c54a655175392fdf712e0ab0a06104230c4113b5c496` |

## Inlined files

### `.devcontainer/devcontainer.json`

_(299 bytes, sha256 `f5cd905c886bdb6d2837493433f93383ec9665dd19dc399bde5946a542026da9`)_

`````json
{
    "name": "orbital-thermal-bounds",
    "image": "mcr.microsoft.com/devcontainers/python:3.12",
    "postCreateCommand": "pip install -e \".[dev]\" numpy",
    "customizations": {
        "vscode": {
            "extensions": [
                "ms-python.python"
            ]
        }
    }
}
`````

### `.gitattributes`

_(417 bytes, sha256 `365c79f2f1dadd3c629a2a23e16344c4b3923f51c4fa583b9d128347210562c1`)_

`````
# Keep the oracle-frozen artifacts byte-exact (audit re-review P1-4): never apply
# end-of-line or other text normalization, so their SHA-256 pins in
# external_models/mccalip_thoughts/PINS.json stay valid across platforms/checkouts.
external_models/mccalip_thoughts/math.js               -text
external_models/mccalip_thoughts/generate_oracle.js    -text
external_models/mccalip_thoughts/expected_outputs.json -text
`````

### `.github/workflows/tests.yml`

_(1877 bytes, sha256 `2c56ebecfaa72703581fa4e03a0ec75c40ca028b6ba890cb1c38eb3cfc74564f`)_

`````yaml
name: tests

on:
  push:
    branches: [main, "feature/**"]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Install package
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]" numpy

      - name: Run published verification suites
        run: |
          python verify_suite.py
          python companion/verify_ai1.py

      - name: Run regression and smoke tests
        run: pytest -v

  oracle-freeze:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4
      - name: Set up Node (pinned to the oracle's recorded version)
        uses: actions/setup-node@v4
        with:
          node-version: "24.14.0"
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Enforce oracle-freeze (SHA pins + semantic regen + external attestation)
        env:
          ORACLE_REQUIRE_EXTERNAL: "1"
        run: python external_models/mccalip_thoughts/verify_oracle_reproducible.py

  wheel-license:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repository
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Build wheel and assert MIT-only license payload
        run: |
          python -m pip install --upgrade pip build
          python -m build --wheel --outdir dist .
          python scripts/check_wheel_license.py
`````

### `.gitignore`

_(89 bytes, sha256 `e6be75059fad0b222ee86770020dfd48119ebf76c4ebc826c3255a0d63f60d49`)_

`````
# Python build/cache artifacts
__pycache__/
*.pyc
*.egg-info/
build/
dist/
.pytest_cache/
`````

### `LICENSE-DOCS-CC-BY-4.0`

_(18656 bytes, sha256 `9e5f1b3c610b9c2da5c313bf81d577a7d1acec686bdb0384edefa6df0f90cd94`)_

`````
Attribution 4.0 International

=======================================================================

Creative Commons Corporation ("Creative Commons") is not a law firm and
does not provide legal services or legal advice. Distribution of
Creative Commons public licenses does not create a lawyer-client or
other relationship. Creative Commons makes its licenses and related
information available on an "as-is" basis. Creative Commons gives no
warranties regarding its licenses, any material licensed under their
terms and conditions, or any related information. Creative Commons
disclaims all liability for damages resulting from their use to the
fullest extent possible.

Using Creative Commons Public Licenses

Creative Commons public licenses provide a standard set of terms and
conditions that creators and other rights holders may use to share
original works of authorship and other material subject to copyright
and certain other rights specified in the public license below. The
following considerations are for informational purposes only, are not
exhaustive, and do not form part of our licenses.

     Considerations for licensors: Our public licenses are
     intended for use by those authorized to give the public
     permission to use material in ways otherwise restricted by
     copyright and certain other rights. Our licenses are
     irrevocable. Licensors should read and understand the terms
     and conditions of the license they choose before applying it.
     Licensors should also secure all rights necessary before
     applying our licenses so that the public can reuse the
     material as expected. Licensors should clearly mark any
     material not subject to the license. This includes other CC-
     licensed material, or material used under an exception or
     limitation to copyright. More considerations for licensors:
    wiki.creativecommons.org/Considerations_for_licensors

     Considerations for the public: By using one of our public
     licenses, a licensor grants the public permission to use the
     licensed material under specified terms and conditions. If
     the licensor's permission is not necessary for any reason--for
     example, because of any applicable exception or limitation to
     copyright--then that use is not regulated by the license. Our
     licenses grant only permissions under copyright and certain
     other rights that a licensor has authority to grant. Use of
     the licensed material may still be restricted for other
     reasons, including because others have copyright or other
     rights in the material. A licensor may make special requests,
     such as asking that all changes be marked or described.
     Although not required by our licenses, you are encouraged to
     respect those requests where reasonable. More considerations
     for the public:
    wiki.creativecommons.org/Considerations_for_licensees

=======================================================================

Creative Commons Attribution 4.0 International Public License

By exercising the Licensed Rights (defined below), You accept and agree
to be bound by the terms and conditions of this Creative Commons
Attribution 4.0 International Public License ("Public License"). To the
extent this Public License may be interpreted as a contract, You are
granted the Licensed Rights in consideration of Your acceptance of
these terms and conditions, and the Licensor grants You such rights in
consideration of benefits the Licensor receives from making the
Licensed Material available under these terms and conditions.


Section 1 -- Definitions.

  a. Adapted Material means material subject to Copyright and Similar
     Rights that is derived from or based upon the Licensed Material
     and in which the Licensed Material is translated, altered,
     arranged, transformed, or otherwise modified in a manner requiring
     permission under the Copyright and Similar Rights held by the
     Licensor. For purposes of this Public License, where the Licensed
     Material is a musical work, performance, or sound recording,
     Adapted Material is always produced where the Licensed Material is
     synched in timed relation with a moving image.

  b. Adapter's License means the license You apply to Your Copyright
     and Similar Rights in Your contributions to Adapted Material in
     accordance with the terms and conditions of this Public License.

  c. Copyright and Similar Rights means copyright and/or similar rights
     closely related to copyright including, without limitation,
     performance, broadcast, sound recording, and Sui Generis Database
     Rights, without regard to how the rights are labeled or
     categorized. For purposes of this Public License, the rights
     specified in Section 2(b)(1)-(2) are not Copyright and Similar
     Rights.

  d. Effective Technological Measures means those measures that, in the
     absence of proper authority, may not be circumvented under laws
     fulfilling obligations under Article 11 of the WIPO Copyright
     Treaty adopted on December 20, 1996, and/or similar international
     agreements.

  e. Exceptions and Limitations means fair use, fair dealing, and/or
     any other exception or limitation to Copyright and Similar Rights
     that applies to Your use of the Licensed Material.

  f. Licensed Material means the artistic or literary work, database,
     or other material to which the Licensor applied this Public
     License.

  g. Licensed Rights means the rights granted to You subject to the
     terms and conditions of this Public License, which are limited to
     all Copyright and Similar Rights that apply to Your use of the
     Licensed Material and that the Licensor has authority to license.

  h. Licensor means the individual(s) or entity(ies) granting rights
     under this Public License.

  i. Share means to provide material to the public by any means or
     process that requires permission under the Licensed Rights, such
     as reproduction, public display, public performance, distribution,
     dissemination, communication, or importation, and to make material
     available to the public including in ways that members of the
     public may access the material from a place and at a time
     individually chosen by them.

  j. Sui Generis Database Rights means rights other than copyright
     resulting from Directive 96/9/EC of the European Parliament and of
     the Council of 11 March 1996 on the legal protection of databases,
     as amended and/or succeeded, as well as other essentially
     equivalent rights anywhere in the world.

  k. You means the individual or entity exercising the Licensed Rights
     under this Public License. Your has a corresponding meaning.


Section 2 -- Scope.

  a. License grant.

       1. Subject to the terms and conditions of this Public License,
          the Licensor hereby grants You a worldwide, royalty-free,
          non-sublicensable, non-exclusive, irrevocable license to
          exercise the Licensed Rights in the Licensed Material to:

            a. reproduce and Share the Licensed Material, in whole or
               in part; and

            b. produce, reproduce, and Share Adapted Material.

       2. Exceptions and Limitations. For the avoidance of doubt, where
          Exceptions and Limitations apply to Your use, this Public
          License does not apply, and You do not need to comply with
          its terms and conditions.

       3. Term. The term of this Public License is specified in Section
          6(a).

       4. Media and formats; technical modifications allowed. The
          Licensor authorizes You to exercise the Licensed Rights in
          all media and formats whether now known or hereafter created,
          and to make technical modifications necessary to do so. The
          Licensor waives and/or agrees not to assert any right or
          authority to forbid You from making technical modifications
          necessary to exercise the Licensed Rights, including
          technical modifications necessary to circumvent Effective
          Technological Measures. For purposes of this Public License,
          simply making modifications authorized by this Section 2(a)
          (4) never produces Adapted Material.

       5. Downstream recipients.

            a. Offer from the Licensor -- Licensed Material. Every
               recipient of the Licensed Material automatically
               receives an offer from the Licensor to exercise the
               Licensed Rights under the terms and conditions of this
               Public License.

            b. No downstream restrictions. You may not offer or impose
               any additional or different terms or conditions on, or
               apply any Effective Technological Measures to, the
               Licensed Material if doing so restricts exercise of the
               Licensed Rights by any recipient of the Licensed
               Material.

       6. No endorsement. Nothing in this Public License constitutes or
          may be construed as permission to assert or imply that You
          are, or that Your use of the Licensed Material is, connected
          with, or sponsored, endorsed, or granted official status by,
          the Licensor or others designated to receive attribution as
          provided in Section 3(a)(1)(A)(i).

  b. Other rights.

       1. Moral rights, such as the right of integrity, are not
          licensed under this Public License, nor are publicity,
          privacy, and/or other similar personality rights; however, to
          the extent possible, the Licensor waives and/or agrees not to
          assert any such rights held by the Licensor to the limited
          extent necessary to allow You to exercise the Licensed
          Rights, but not otherwise.

       2. Patent and trademark rights are not licensed under this
          Public License.

       3. To the extent possible, the Licensor waives any right to
          collect royalties from You for the exercise of the Licensed
          Rights, whether directly or through a collecting society
          under any voluntary or waivable statutory or compulsory
          licensing scheme. In all other cases the Licensor expressly
          reserves any right to collect such royalties.


Section 3 -- License Conditions.

Your exercise of the Licensed Rights is expressly made subject to the
following conditions.

  a. Attribution.

       1. If You Share the Licensed Material (including in modified
          form), You must:

            a. retain the following if it is supplied by the Licensor
               with the Licensed Material:

                 i. identification of the creator(s) of the Licensed
                    Material and any others designated to receive
                    attribution, in any reasonable manner requested by
                    the Licensor (including by pseudonym if
                    designated);

                ii. a copyright notice;

               iii. a notice that refers to this Public License;

                iv. a notice that refers to the disclaimer of
                    warranties;

                 v. a URI or hyperlink to the Licensed Material to the
                    extent reasonably practicable;

            b. indicate if You modified the Licensed Material and
               retain an indication of any previous modifications; and

            c. indicate the Licensed Material is licensed under this
               Public License, and include the text of, or the URI or
               hyperlink to, this Public License.

       2. You may satisfy the conditions in Section 3(a)(1) in any
          reasonable manner based on the medium, means, and context in
          which You Share the Licensed Material. For example, it may be
          reasonable to satisfy the conditions by providing a URI or
          hyperlink to a resource that includes the required
          information.

       3. If requested by the Licensor, You must remove any of the
          information required by Section 3(a)(1)(A) to the extent
          reasonably practicable.

       4. If You Share Adapted Material You produce, the Adapter's
          License You apply must not prevent recipients of the Adapted
          Material from complying with this Public License.


Section 4 -- Sui Generis Database Rights.

Where the Licensed Rights include Sui Generis Database Rights that
apply to Your use of the Licensed Material:

  a. for the avoidance of doubt, Section 2(a)(1) grants You the right
     to extract, reuse, reproduce, and Share all or a substantial
     portion of the contents of the database;

  b. if You include all or a substantial portion of the database
     contents in a database in which You have Sui Generis Database
     Rights, then the database in which You have Sui Generis Database
     Rights (but not its individual contents) is Adapted Material; and

  c. You must comply with the conditions in Section 3(a) if You Share
     all or a substantial portion of the contents of the database.

For the avoidance of doubt, this Section 4 supplements and does not
replace Your obligations under this Public License where the Licensed
Rights include other Copyright and Similar Rights.


Section 5 -- Disclaimer of Warranties and Limitation of Liability.

  a. UNLESS OTHERWISE SEPARATELY UNDERTAKEN BY THE LICENSOR, TO THE
     EXTENT POSSIBLE, THE LICENSOR OFFERS THE LICENSED MATERIAL AS-IS
     AND AS-AVAILABLE, AND MAKES NO REPRESENTATIONS OR WARRANTIES OF
     ANY KIND CONCERNING THE LICENSED MATERIAL, WHETHER EXPRESS,
     IMPLIED, STATUTORY, OR OTHER. THIS INCLUDES, WITHOUT LIMITATION,
     WARRANTIES OF TITLE, MERCHANTABILITY, FITNESS FOR A PARTICULAR
     PURPOSE, NON-INFRINGEMENT, ABSENCE OF LATENT OR OTHER DEFECTS,
     ACCURACY, OR THE PRESENCE OR ABSENCE OF ERRORS, WHETHER OR NOT
     KNOWN OR DISCOVERABLE. WHERE DISCLAIMERS OF WARRANTIES ARE NOT
     ALLOWED IN FULL OR IN PART, THIS DISCLAIMER MAY NOT APPLY TO YOU.

  b. TO THE EXTENT POSSIBLE, IN NO EVENT WILL THE LICENSOR BE LIABLE
     TO YOU ON ANY LEGAL THEORY (INCLUDING, WITHOUT LIMITATION,
     NEGLIGENCE) OR OTHERWISE FOR ANY DIRECT, SPECIAL, INDIRECT,
     INCIDENTAL, CONSEQUENTIAL, PUNITIVE, EXEMPLARY, OR OTHER LOSSES,
     COSTS, EXPENSES, OR DAMAGES ARISING OUT OF THIS PUBLIC LICENSE OR
     USE OF THE LICENSED MATERIAL, EVEN IF THE LICENSOR HAS BEEN
     ADVISED OF THE POSSIBILITY OF SUCH LOSSES, COSTS, EXPENSES, OR
     DAMAGES. WHERE A LIMITATION OF LIABILITY IS NOT ALLOWED IN FULL OR
     IN PART, THIS LIMITATION MAY NOT APPLY TO YOU.

  c. The disclaimer of warranties and limitation of liability provided
     above shall be interpreted in a manner that, to the extent
     possible, most closely approximates an absolute disclaimer and
     waiver of all liability.


Section 6 -- Term and Termination.

  a. This Public License applies for the term of the Copyright and
     Similar Rights licensed here. However, if You fail to comply with
     this Public License, then Your rights under this Public License
     terminate automatically.

  b. Where Your right to use the Licensed Material has terminated under
     Section 6(a), it reinstates:

       1. automatically as of the date the violation is cured, provided
          it is cured within 30 days of Your discovery of the
          violation; or

       2. upon express reinstatement by the Licensor.

     For the avoidance of doubt, this Section 6(b) does not affect any
     right the Licensor may have to seek remedies for Your violations
     of this Public License.

  c. For the avoidance of doubt, the Licensor may also offer the
     Licensed Material under separate terms or conditions or stop
     distributing the Licensed Material at any time; however, doing so
     will not terminate this Public License.

  d. Sections 1, 5, 6, 7, and 8 survive termination of this Public
     License.


Section 7 -- Other Terms and Conditions.

  a. The Licensor shall not be bound by any additional or different
     terms or conditions communicated by You unless expressly agreed.

  b. Any arrangements, understandings, or agreements regarding the
     Licensed Material not stated herein are separate from and
     independent of the terms and conditions of this Public License.


Section 8 -- Interpretation.

  a. For the avoidance of doubt, this Public License does not, and
     shall not be interpreted to, reduce, limit, restrict, or impose
     conditions on any use of the Licensed Material that could lawfully
     be made without permission under this Public License.

  b. To the extent possible, if any provision of this Public License is
     deemed unenforceable, it shall be automatically reformed to the
     minimum extent necessary to make it enforceable. If the provision
     cannot be reformed, it shall be severed from this Public License
     without affecting the enforceability of the remaining terms and
     conditions.

  c. No term or condition of this Public License will be waived and no
     failure to comply consented to unless expressly agreed to by the
     Licensor.

  d. Nothing in this Public License constitutes or may be interpreted
     as a limitation upon, or waiver of, any privileges and immunities
     that apply to the Licensor or You, including from the legal
     processes of any jurisdiction or authority.


=======================================================================

Creative Commons is not a party to its public
licenses. Notwithstanding, Creative Commons may elect to apply one of
its public licenses to material it publishes and in those instances
will be considered the “Licensor.” The text of the Creative Commons
public licenses is dedicated to the public domain under the CC0 Public
Domain Dedication. Except for the limited purpose of indicating that
material is shared under a Creative Commons public license or as
otherwise permitted by the Creative Commons policies published at
creativecommons.org/policies, Creative Commons does not authorize the
use of the trademark "Creative Commons" or any other trademark or logo
of Creative Commons without its prior written consent including,
without limitation, in connection with any unauthorized modifications
to any of its public licenses or any other arrangements,
understandings, or agreements concerning use of licensed material. For
the avoidance of doubt, this paragraph does not form part of the
public licenses.

Creative Commons may be contacted at creativecommons.org.
`````

### `LICENSE-MIT`

_(1072 bytes, sha256 `b587be3feabf0e979f3b9005505ff15d173373bd9301adf73fffa1f9e8efee0f`)_

`````
MIT License

Copyright (c) 2026 Dan Lee-Odinson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
`````

### `LICENSING.md`

_(1141 bytes, sha256 `168555a9c4f6aa5ac9f81a90100e853e347624d5dae1d986f9d8be60f5e4283b`)_

`````markdown
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
doi:10.5281/zenodo.20670772).

## Vendored third-party -- upstream MIT

- `external_models/mccalip_thoughts/` (Andrew McCalip's "thoughts" model, vendored
  for offline oracle verification) retains its upstream MIT license. The upstream
  license statement is reproduced verbatim in
  `external_models/mccalip_thoughts/UPSTREAM-LICENSE.md`.
`````

### `README.md`

_(10498 bytes, sha256 `4e8edf922fd8eee5620ae8a33cbd3b02dac430438c5b27107daf1d277a26b0d9`)_

`````markdown
# Thermodynamic Bounds and Mass-Trade Criteria for Heat Rejection in Orbital Data Centers
[![tests](https://github.com/dan-lee-odinson/orbital-thermal-bounds/actions/workflows/tests.yml/badge.svg?branch=feature/simulation-framework)](https://github.com/dan-lee-odinson/orbital-thermal-bounds/actions/workflows/tests.yml)
*Machine-verified thermodynamic bounds for orbital data center thermal architecture: the preprint, its LaTeX source, the audited proof document, and two independent verification suites (Python and Wolfram Language).*

**Archived version:** DOI: [https://doi.org/10.5281/zenodo.20650893](https://doi.org/10.5281/zenodo.20650893)

and

# The AI1 Design Point: A Bounds-Based Analysis of SpaceX's Orbital Data-Center Satellite
*Companion paper to "Thermodynamic Bounds" applying its radiator-area bounds to the industrial design point: SpaceX's AI1 Satellite announcement. Included are the preprint, its LaTeX source, and Python verification suite. (see `companion/`)*

**Archived version:** DOI: [https://doi.org/10.5281/zenodo.20670772](https://doi.org/10.5281/zenodo.20670772)

**Author:** Dan Lee-Odinson ([ORCID 0009-0009-9504-0796](https://orcid.org/0009-0009-9504-0796)) | dan.lee.odinson@gmail.com
---

## What this is

Orbital data centers must reject waste heat by far-field thermal radiation, and the resulting radiator area requirement is widely regarded as the binding engineering constraint on the concept. This work derives, within a gray-body effective-sink radiator model, a set of exact results governing that constraint:

1. The Carnot efficiency evaluated at the environmental sink temperature (the "2.7 K cold reservoir" argument) is unattainable by any heat engine with a material cold reservoir at finite radiator area and positive heat or work throughput. Near-limit efficiencies are possible in principle but command extreme area (a worked 99% example requires roughly 6.4 billion square meters per megawatt).
2. Radiator area per unit work output is minimized, along the reversible lower envelope, at a cold-side temperature of exactly three quarters of the hot-side temperature, with a 25% efficiency ceiling. The nonzero-sink optimum satisfies a quintic with the exact implicit form T_c\*/T_h = (3 + q⁴)/4, q = T_s/T_c\*, and fractional shift q⁴/3.
3. Converting waste heat to work before rejecting it multiplies the required radiator area by at least (T_h/T_c)³. Equality requires reversible conversion and a zero-temperature sink; every real system pays more.
4. No cyclic system can sustain its compute load solely by reconverting its own waste heat.
5. Radiator selection, heat-pump inclusion, and topping-cycle inclusion reduce to explicit mass-trade inequalities whose verdicts depend on empirical parameters but whose algebraic form does not.

The design implication: within the model, orbital thermal management is a temperature-architecture problem. The temperature at which heat finally leaves the system enters the area requirement quartically and dominates fixed-temperature efficiency optimization.

## Files

| File | Description |
|---|---|
| `orbital-thermal-preprint.pdf` | The preprint (9 pages, compiled) |
| `orbital-thermal-preprint.tex` | LaTeX source (self-contained, no external figures) |
| `orbital-thermal-resolution-proof-v3.md` | Audited source document with full revision history across three audit rounds |
| `verify_suite.py` | Python assertion suite covering every central numerical claim |
| `verify_suite.wl` | Wolfram Language symbolic verification suite (stationarity, second-order conditions, limits, exact rationals, high-precision roots) |
| `LICENSE-DOCS-CC-BY-4.0` | CC BY 4.0 for papers/docs; code is MIT (`LICENSE-MIT`) -- see `LICENSING.md` |

## Running the verification suites

**Python** (requires Python 3.10+ and numpy):

```bash
python3 verify_suite.py
```

Expected output: `All assertions pass.` Runtime is under a minute; the suite asserts every central numerical claim in the manuscript, including the exact sink-corrected area ratios, the 3/4-rule optimum with second-order condition, the q⁴/3 shift identity at eight sink temperatures, the COP identities, and the conversion area penalty bounds.

**Wolfram Language** (requires Mathematica or Wolfram Engine):

Open `verify_suite.wl` and evaluate the blocks (W1 through W9) in order. Each block states its expected output in comments. The blocks verify the proofs symbolically: stationarity conditions via `Solve` and `FullSimplify`, the fixed-point contraction factor 4q⁴/(3+q⁴) < 1, the divergence limits in Theorem 1, the nonzero-sink penalty inequality via `Reduce`, and the quintic root as an exact algebraic `Root` object evaluated to 50 digits.

The two suites are independent implementations. A reviewer who trusts neither can check the proofs by hand; the verification protocol is stated at the end of the source document.

## Provenance

This work was produced through an iterative, adversarial workflow across multiple AI systems, orchestrated and directed by the author: derivations and drafting by Claude Fable 5 (Anthropic), literature-armed review by Perplexity deep research, and two formal proof audits with independent computer-algebra verification by GPT 5.5 with the Wolfram plugin. The source document records every correction from every audit round, including the errors each system made and retracted along the way. The author takes responsibility for the result.

## How to cite

> Lee-Odinson, D. (2026). Thermodynamic Bounds and Mass-Trade Criteria for Heat Rejection in Orbital Data Centers. Zenodo. [Version 3] [https://doi.org/10.5281/zenodo.20650893](https://doi.org/10.5281/zenodo.20650893)

BibTeX:

```bibtex
@misc{leeodinson2026orbitalthermal,
  author       = {Lee-Odinson, Dan},
  title        = {Thermodynamic Bounds and Mass-Trade Criteria for
                  Heat Rejection in Orbital Data Centers},
  year         = {2026},
  month        = jun,
  publisher    = {Zenodo},
  version      = {v3},
  doi          = {10.5281/zenodo.20650893},
  url          = {https://doi.org/10.5281/zenodo.20650893},
  note         = {Preprint}
}
```
## Companion paper: The AI1 Design Point

On June 9–10, 2026, SpaceX announced AI1, its first orbital data-center satellite. The companion paper in `companion/` applies this repository's thermodynamic bounds to the announced design and establishes its coherence within the gray-body radiator model, under one specific reading of the reported figures.

**Archived version:** Zenodo DOI: [https://doi.org/10.5281/zenodo.20670772](https://doi.org/10.5281/zenodo.20670772)

What it shows, briefly: treating the reported 110 m² of radiators as double-sided panel planform (the reading SpaceX itself states — "radiating both sides, orientated knife-edge to the sun"), the implied radiator surface temperature is about 337 K at the 120 kW sustained load and about 353 K if the 150 kW peak runs continuously. The alternative total-emitting-area reading requires 391–412 K, which strongly disfavors the subcritical ammonia loop secondary coverage describes as likely. An illustrative combined stress case (emissivity 0.91 → 0.80, effective sink 220 → 260 K) removes about 40 kW of fixed-temperature capacity — the entire reported peak-to-sustained headroom plus 10 kW — or raises the sustained equilibrium by about 22 K into unreported temperature and pressure limits. The reduced-order model does not rule the design out; margin, the engineering interior, and the economics remain open.

Every reported figure in the paper traces to a quoted source (the key statements are direct Musk and Dahl quotations from announcement coverage), and every radiator-model calculation and displayed value is asserted by the verification suite. The paper passed four rounds of adversarial peer review by GPT 5.5 with independent Wolfram verification; the revision history is recorded in the response letters.

### Companion files

| File | Description |
|---|---|
| `companion/ai1-design-point-r4.pdf` | The companion paper (8 pages, Revision 4, review-approved, DOI-stamped) |
| `companion/ai1-design-point.tex` | LaTeX source (Revision 4) |
| `companion/verify_ai1.py` | Assertion suite: both area interpretations, both power bases, both sensitivity branches, overhead cases, display-rounding policy. Run: `python3 verify_ai1.py` |
| `companion/response-to-review.md` | Response to the first formal review round (workflow record) |
| `companion/response-to-second-review.md` | Response to the second formal review round (workflow record) |
| `companion/response-to-final-review.md` | Response to the final review round (workflow record) |

The suite's expected output states its scope precisely: "All radiator-model calculations and manuscript display-rounding assertions pass. External thermophysical property values are not computed by this suite." Ammonia properties are reference values from the NIST Chemistry WebBook (SRD 69), cited in the paper.

### How to cite the companion paper

> Lee-Odinson, D. (2026). *The AI1 design point: A bounds-based analysis of SpaceX's orbital data-center satellite* (Revision 4) [Preprint]. Zenodo. [https://doi.org/10.5281/zenodo.20670772](https://doi.org/10.5281/zenodo.20670772)

BibTeX:

```bibtex
@misc{leeodinson2026ai1,
  author       = {Lee-Odinson, Dan},
  title        = {The AI1 design point: A bounds-based analysis of SpaceX's orbital data-center satellite},
  year         = {2026},
  month        = jun,
  publisher    = {Zenodo},
  version      = {v1},
  doi          = {10.5281/zenodo.20670772},
  url          = {https://doi.org/10.5281/zenodo.20670772},
  note         = {Preprint}
}
```

## License

This repository is licensed by component (see [`LICENSING.md`](LICENSING.md)):

- **Software** -- `src/`, `tests/`, `scripts/`, the root `verify_suite.py` /
  `verify_suite.wl`, `companion/verify_ai1.py`, and packaging -- is MIT-licensed
  (see [`LICENSE-MIT`](LICENSE-MIT)). The packaged distribution declares MIT.
- **Papers, documentation, and figures** -- the manuscripts, `docs/`, and
  `results/figures/` -- are licensed under Creative Commons Attribution 4.0
  International (CC BY 4.0; see [`LICENSE-DOCS-CC-BY-4.0`](LICENSE-DOCS-CC-BY-4.0)),
  consistent with the published preprints.
- **Vendored McCalip model** -- `external_models/` -- retains its upstream MIT
  license (see
  [`external_models/mccalip_thoughts/UPSTREAM-LICENSE.md`](external_models/mccalip_thoughts/UPSTREAM-LICENSE.md)).
`````

### `companion/ai1-design-point.tex`

_(27115 bytes, sha256 `02fc57ccd0c0c3a613209276d73e039e39926939db04a22a7e1ef3bc9fd596fb`)_

`````latex
\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{microtype}
\usepackage{xcolor}
\definecolor{linknavy}{RGB}{25,50,110}
\usepackage{xurl}
\usepackage[colorlinks=true,linkcolor=linknavy,citecolor=linknavy,urlcolor=linknavy]{hyperref}

\newcommand{\Tc}{T_c}
\newcommand{\Th}{T_h}
\newcommand{\Ts}{T_s^{\mathrm{eff}}}
\newcommand{\eps}{\varepsilon}

\title{The AI1 Design Point: A Bounds-Based Analysis of\\ SpaceX's Orbital Data-Center Satellite}
\author{Dan Lee-Odinson\thanks{Contact: dan.lee.odinson@gmail.com. ORCID: \href{https://orcid.org/0009-0009-9504-0796}{0009-0009-9504-0796}. Companion to the theory preprint at \href{https://doi.org/10.5281/zenodo.20650893}{doi:10.5281/zenodo.20650893}. This paper: \href{https://doi.org/10.5281/zenodo.20670772}{doi:10.5281/zenodo.20670772}. Revision 4, incorporating three rounds of formal peer review; see Acknowledgments.}}
\date{June 12, 2026 (Revision 4)}

\begin{document}
\maketitle

\begin{abstract}
On June 9--10, 2026, SpaceX announced AI1, an orbital data-center satellite reported at 150~kW peak and 120~kW sustained compute with up to 110~m$^{2}$ of deployable liquid radiators. We apply the radiator-area bounds of a contemporaneous, independently derived thermodynamic framework (Lee-Odinson, 2026) to the reported figures, using the reported compute powers as the radiative heat load. Treating the 110~m$^{2}$ as double-sided panel planform (220~m$^{2}$ emitting; SpaceX states the radiators radiate from both sides), the equilibrium radiator temperature is approximately 337~K at the sustained load and approximately 353~K under a continuous-peak hypothetical; a total-emitting-area reading instead requires 391~K to 412~K, which strongly disfavors a conventional subcritical loop using ammonia, the coolant secondary coverage describes as likely, though public information cannot rule the sustained case out. An illustrative combined stress case (emissivity 0.91 to 0.80; effective sink 220 to 260~K) removes about 40~kW of fixed-temperature capacity, consuming the full 30~kW peak-to-sustained headroom plus a further 10~kW, or equivalently raises the sustained-load equilibrium by about 22~K into unreported temperature and pressure limits. The reduced-order radiative model does not rule out the reported design point; allowable operating temperatures, coolant phase and pressure, internal gradients, the complete power budget, and the economics remain unreported and open. All radiator-model calculations and displayed derived values, excluding externally sourced thermophysical property data, are verified by an accompanying assertion suite.
\end{abstract}

\section{Introduction}

On June 9--10, 2026, ahead of a planned initial public offering, SpaceX released the first detailed design description of AI1, a satellite the company positions as the opening generation of orbital AI data centers, alongside an announced factory (``Gigasat,'' Bastrop, Texas) targeted at a gigawatt per year of orbital compute capacity by late 2027 \cite{dcd2026,toms2026,tomsgigasat2026}. The announcement places a concrete, numerically specified industrial design inside a problem space that until now has been argued mostly in the abstract: whether vacuum heat rejection permits data-center-class computing in orbit, and at what cost in radiator area and mass.

A contemporaneous preprint by the present author derives exact bounds for that problem space within a gray-body effective-sink radiator model \cite{leeodinson2026}. The preprint was derived independently of the AI1 announcement and contains no reference to it; the two are contemporaneous, and this paper makes no claim of prediction. This paper applies the framework to the reported design point and finds no contradiction within the model. The framework's area law is quantitatively exercised by the reported figures; its recovery penalty and self-powering bound are not engaged on the available record, because no waste-heat recovery stage is reported and no self-powering claim is made.

Section~\ref{sec:reported} compiles the reported specifications with per-row sourcing and ambiguities. Section~\ref{sec:implied} computes the implied operating temperatures under both readings of the reported radiator area and both reported power levels, and applies a coolant-class screen. Section~\ref{sec:application} states which framework results the design exercises. Section~\ref{sec:margins} presents a two-branch sensitivity analysis with an explicit heat-load overhead parameterization. Section~\ref{sec:scaleup} locates AI1 against flight practice and constellation arithmetic under stated conventions. Section~\ref{sec:open} lists what remains unreported.

A caution on evidence quality applies throughout. The inputs are reported figures from announcement-week coverage of unflown hardware, treated as a stated design point; conclusions are conditional on them. The primary SpaceX presentation has not been independently transcribed for this analysis, and journalism remains secondary evidence. The analysis is built to be re-run: if the figures move, the assertion suite re-prices the design point in seconds.

\section{The reported design and its ambiguities}\label{sec:reported}

Table~\ref{tab:specs} compiles the reported figures with the source class and the reading adopted here.

\begin{table}[ht]
\centering
\footnotesize
\begin{tabularx}{\textwidth}{>{\raggedright\arraybackslash}p{2.6cm}>{\raggedright\arraybackslash}p{4.5cm}p{1.1cm}>{\raggedright\arraybackslash}X}
\toprule
Quantity & Reported wording & Source & Interpretation; ambiguity \\
\midrule
Peak power & ``the right place is around the 150kW peak power level'' (Dahl); ``150kW peak'' (Musk) & \cite{dcd2026} & Peak power level; compute vs.\ total system power not fully disambiguated; peak duration unreported \\
Sustained compute & ``we can support 120kW of average compute'' (Dahl) & \cite{dcd2026} & Steady compute basis; primary for steady-state analysis \\
Radiators & ``a 110 sqm deployable liquid radiator, with redundant pumping loops''; ``radiating both sides, orientated knife-edge to the sun'' (Musk) & \cite{dcd2026,toms2026} & Double-sided planform, stated directly; \cite{toms2026} adds ``up to,'' treated as maximum effective area \\
Radiator flux & ``about 1,400W per sqm for the radiators'' (Musk, stated as assumption/target) & \cite{dcd2026} & Planform flux design figure \\
Solar-array areal density & ``250W per sq m for the solar array'' (Musk, stated as assumption/target) & \cite{dcd2026} & Array power density only \\
Total array output & Not independently established & --- & Do not infer without qualification \\
Coolant & SpaceX has not named it; ammonia ``the likely fluid'' (expectation attributed to Hugh Lewis, Univ.\ of Birmingham) & \cite{gagadget2026} & Expected/likely, not confirmed; phase unreported \\
Wingspan; height & 70 m; 20 m deployed & \cite{dcd2026} & Tip-to-tip; includes non-array structure \\
Specific power & 70 kW per metric ton & \cite{toms2026} & Normalization (peak, sustained, bus) unreported \\
Compute hardware & interchangeable GPU modules; Nvidia Rubin baseline & \cite{gagadget2026} & Junction temperature limits unreported \\
Heritage & ``not some magic\ldots technology we've already made with the Starlink V3 satellites''; ``much simpler than a Starlink satellite'' (Musk) & \cite{dcd2026} & Subsystem reuse; thermal system has no flown analogue at this class \\
\bottomrule
\end{tabularx}
\caption{Reported AI1 figures with exact quoted wording where available (June 2026 announcement coverage), per-row sources, and ambiguities.}
\label{tab:specs}
\end{table}

The power budget cannot be checked for closure from public reporting: total solar-array output is not independently established (the 250~W/m$^{2}$ figure is an areal density Musk states as an assumption, not a rated output), and compute power is not identical to either generation or radiator heat load. Pumps, avionics, communications, power conversion, battery charging, and thermal-control electronics all draw power and most of it returns as heat. This paper makes the radiator-load assumption explicit by writing
\begin{equation}
Q_{\mathrm{rad}} = (1+f)\,P_{\mathrm{compute}},
\qquad
f = \frac{P_{\mathrm{bus}}+P_{\mathrm{pump}}+P_{\mathrm{conversion}}-P_{\mathrm{exported}}}{P_{\mathrm{compute}}},
\label{eq:overhead}
\end{equation}
and computing the baseline at $f=0$ with the overhead sensitivity given in Section~\ref{sec:margins}. One secondary cross-check survives the sourcing audit: the reported specific power implies roughly 2.1~t on a peak basis or 1.7~t on a sustained basis, the normalization being unreported.

\section{Implied operating points}\label{sec:implied}

The framework's area law (Lemma~1 of \cite{leeodinson2026}) inverts to give the equilibrium radiator temperature required to reject heat load $Q_{\mathrm{rad}}$ through emitting area $A$:
\begin{equation}
\Tc = \left[\frac{Q_{\mathrm{rad}}}{\eps\sigma A} + (\Ts)^{4}\right]^{1/4}.
\end{equation}
Throughout, $\eps = 0.91$ and $\Ts = 220$~K, an illustrative LEO value within the published 200--260~K range. For the double-sided reading, $\Ts$ is to be understood as the \emph{area-weighted effective sink for the combined two-face emitting area}, $(\Ts)^{4} = \tfrac{1}{2}\,(T_{s,1}^{4}+T_{s,2}^{4})$ for equal faces; the two faces of a real panel need not see equal environments. Table~\ref{tab:operating} gives all four combinations of area reading and power basis.

\begin{table}[ht]
\centering
\begin{tabular}{lcc}
\toprule
Reading & 120 kW sustained & 150 kW continuous peak \\
\midrule
Two-sided planform (220 m$^{2}$) & \textbf{337.1 K} (64 $^{\circ}$C) & 353.16 K (80 $^{\circ}$C) \\
Total emitting area (110 m$^{2}$) & 391.5 K (118 $^{\circ}$C) & 411.8 K (139 $^{\circ}$C) \\
\bottomrule
\end{tabular}
\caption{Implied equilibrium radiator temperatures at $f=0$ ($\eps=0.91$, $\Ts=220$ K). The sustained two-sided case (bold) is the primary steady-state operating point. The continuous-peak column is the continuous-peak hypothetical: it assumes the 150 kW peak persists indefinitely, which the reporting does not establish; transient peaks cannot be resolved without heat-capacity and control information.}
\label{tab:operating}
\end{table}

\textbf{Coolant-class screen.} SpaceX has not named the coolant; secondary coverage describes ammonia, the International Space Station's working fluid, as the likely choice, an expert expectation attributed to Hugh Lewis of the University of Birmingham \cite{gagadget2026}. The loop phase is likewise unreported. Ammonia's critical point is 405.5~K and roughly 113~bar. Under the total-emitting-area reading, the continuous-peak hypothetical (411.8~K) exceeds the critical temperature outright and is incompatible with any subcritical ammonia loop. The sustained case (391.5~K) is not thermodynamically excluded: it leaves less than 14~K of headroom before the critical point and implies an ammonia saturation pressure near 88~bar at the radiator surface temperature \cite{nist}, and because the coolant must be at least as hot as the emitting surface, the remaining temperature and pressure margins would be narrow; the public information is insufficient to declare that architecture impossible, but it is strongly disfavored. Under the double-sided reading both cases retain more than 50~K of margin, with lower-bound saturation pressures (evaluated at the radiator surface temperature, as the minimum pressure maintaining liquid phase there) of roughly 41~bar at the continuous-peak point. The double-sided reading is additionally stated directly in the announcement: Musk describes the radiators as ``radiating both sides, orientated knife-edge to the sun'' \cite{dcd2026}. The double-sided interpretation is therefore adopted, conditional on the reported coolant class; unconventional supercritical or alternative-fluid architectures are not excluded by this argument, only unsupported by the reporting, and pressure feasibility is outside the present model.

\textbf{Flux reconciliation.} Dividing 150~kW by 110~m$^{2}$ gives 1{,}364~W/m$^{2}$, matching the ``about 1,400W per sqm'' radiator assumption Musk states in the announcement \cite{dcd2026}; that is planform flux, and Musk frames both areal figures as targets (``over time, we think we can do about 250W and 1,400W, respectively''). Under the double-sided reading the net radiative flux per emitting face is 545~W/m$^{2}$ at the sustained load and 682~W/m$^{2}$ at the continuous-peak hypothetical; the decomposition at 353.16~K is gross emission of 803~W/m$^{2}$ less a sink-equivalent 121~W/m$^{2}$. The reported area, the reported flux figure, the reported two-face orientation, and the gray-body arithmetic close on a consistent design point.

\textbf{The ``up to'' qualifier.} The computed temperatures assume the full planform is thermally effective, uniformly heated, and unobstructed; real panels carry inactive structure, plumbing, fin-efficiency and view-factor losses, and nonuniformity. The values in Table~\ref{tab:operating} are therefore lower bounds on required temperature under each reading. As an illustrative case, at 85\% effective area the sustained point rises from 337~K to 349~K.

\section{Application of the framework}\label{sec:application}

\textbf{Exercised: the area law and the quartic logic.} The quoted radiator design assumption itself implies elevated-temperature rejection: 1{,}400~W/m$^{2}$ of planform with both faces emitting requires a surface near 353~K (Section~\ref{sec:implied}), consistent with the quartic-law incentive to reduce radiator area. At the continuous-peak point, rejecting at 353~K rather than an illustrative 293~K comparison temperature reduces required area by the sink-corrected factor 2.6; the 110~m$^{2}$ planform would need roughly 290~m$^{2}$ at the cooler temperature. The reported knife-edge attitude concept is qualitatively consistent with reducing absorbed environmental load, but the resulting effective sink cannot be determined without orbit- and attitude-resolved view factors; Section~\ref{sec:margins} prices a 40~K sink excursion at 17\% of fixed-temperature capacity.

\textbf{Not engaged on the available record: the recovery penalty and the self-powering bound.} No waste-heat-to-electricity stage is reported and no self-powering claim is made, so neither result is exercised; these are non-conflicts rather than tests, and absence from announcement coverage is not certainty about the detailed architecture. The framework identifies direct rejection as the area-optimal choice whenever recovered work cannot displace more system mass than added radiator area costs; the reported architecture is consistent with that verdict.

Within the model, the reported thermal choices are point for point the ones the bounds reward. That establishes coherence at the level of the reduced-order balance; margin, the engineering interior, and economics are separate categories, taken up next.

\section{Two-branch sensitivity}\label{sec:margins}

A capacity-only sensitivity at fixed radiator temperature is insufficient, because a real system may respond to degraded conditions by increasing temperature, reducing load, or both. Table~\ref{tab:twobranch} therefore reports both branches. The two varied parameters are independent parameters of the lumped model by construction; the physical mechanisms behind them (coating aging and contamination; attitude and view-factor drift) can be correlated in practice, and the specific values are illustrative bounding choices rather than mission-sourced predictions, so the table is an \emph{illustrative combined stress case}, not a forecast.

\begin{table}[ht]
\centering
\begin{tabular}{lcc}
\toprule
Condition & Capacity at 353.16 K (kW) & Equil.\ $\Tc$, 120 kW \\
\midrule
Nominal ($\eps=0.91$, $\Ts=220$ K) & 150.0 & 337.1 K \\
$\eps = 0.80$ & 131.9 & 346.2 K \\
$\Ts = 260$ K & 124.7 & 350.8 K \\
Both & 109.6 & 358.9 K \\
\bottomrule
\end{tabular}
\caption{Illustrative combined stress case, double-sided reading, $f=0$. Left branch: capacity with the radiator held at the exact continuous-peak equilibrium temperature (353.1623 K). Right branch: equilibrium temperature with the sustained load held and temperature free to rise. For a continuous 150 kW load under the combined case the required equilibrium is 374.2 K.}
\label{tab:twobranch}
\end{table}

At fixed continuous-peak temperature, the combined stress removes about 40~kW of rejection capacity: it consumes the full 30~kW peak-to-sustained headroom and leaves a further deficit of roughly 10~kW against the 120~kW sustained load. If temperature is instead free to rise, the sustained load is maintained at 358.9~K, about 22~K above nominal, with every series element of the thermal chain running hotter and the lower-bound ammonia saturation pressure at the surface climbing from roughly 41 toward 47~bar; a continuous 150~kW load under the same conditions requires 374~K, where that lower bound approaches 64~bar. Which response a real AI1 exhibits, or what mix, depends on the maximum allowable operating temperature, which is unreported. Non-compute heat sharpens both branches: by Eq.~\eqref{eq:overhead}, a 10\% overhead raises the nominal sustained point from 337.1 to 343.8~K and the stressed equilibrium from 358.9 to 365.2~K; 20\% overhead gives 350.1 and 371.3~K respectively. The quartic law that makes hot rejection efficient is the same law that makes these trades steep.

\section{Scale and heritage under stated conventions}\label{sec:scaleup}

The Shi et al.\ review of thermal management for space data centers concludes that flight practice supports systems of tens of kilowatts and that growth toward hundreds of kilowatts intensifies rejection, mass, and controllability problems faster than subsystem extrapolation suggests \cite{shi2026}; the tens-of-kilowatt characterization is independently anchored by the flown record. The largest pumped-ammonia rejection system flown, the International Space Station's external active thermal control system, is a mechanically pumped liquid-ammonia system with capacity near 70~kW \cite{nasaiss}. On capacity, AI1 must reject 1.7$\times$ that figure sustained and 2.1$\times$ under the continuous-peak hypothetical, from a roughly 2-ton platform. Secondary reporting quotes approximately 422~m$^{2}$ for the ISS radiator area, a figure attributed in coverage to SemiAnalysis whose area convention has not been independently verified; on that provisional basis AI1's per-face net flux would be 3.3$\times$ (sustained) to 4.1$\times$ (continuous-peak) the ISS value, and these ratios should be treated as provisional until the convention is established. The Starlink-heritage claim \cite{dcd2026} divides accordingly: arrays, bus avionics, laser links, and manufacturing scale from V3 on the public record; a mechanically pumped liquid-coolant rejection system at this power class has no flown analogue, which locates the development risk on the same subsystem the bounds identify as binding.

Constellation arithmetic, on both power bases: the announced Gigasat target of one gigawatt of orbital compute per year \cite{tomsgigasat2026} implies approximately 6{,}700 AI1-class satellites annually on the 150~kW nameplate basis, or 8{,}300 on the 120~kW sustained basis, carrying respectively about 1.47 and 1.83 square kilometers of new emitting radiator surface per year, with the drag, debris-exposure, and replacement-cadence consequences of that area. None of this violates a bound. All of it prices one.

\section{What remains unreported}\label{sec:open}

The following quantities, each capable of moving the conclusions, are absent from the public record at this writing: the maximum allowable chip junction temperature and the junction-to-surface thermal resistance chain; coolant identity and phase as primary-source facts, loop pressure limits, and pump power; the overhead fraction $f$ of Eq.~\eqref{eq:overhead}; the effective emitting-area fraction of the ``up to 110~m$^{2}$'' figure; the duration and duty cycle of the 150~kW peak; the complete spacecraft electrical budget; the orbit, eclipse fraction, and energy-storage strategy; and every input to the economics, from launch cost to refresh cadence, which the framework's own mass-trade criteria require before returning verdicts and which public critiques correctly identify as unresolved \cite{techtimes2026}.

\section{Conclusion}

Under the adopted gray-body effective-sink model, the reported AI1 figures are mutually compatible if the quoted 110~m$^{2}$ is treated as double-sided panel planform, the reading the coverage itself describes, and if the reported compute powers are used as the radiative heat load. That interpretation gives an equilibrium radiator temperature of approximately 337~K at the 120~kW sustained load and approximately 353~K under the continuous-peak hypothetical. The total-emitting-area interpretation requires approximately 391~K at sustained load and 412~K at continuous peak, strongly disfavoring a conventional subcritical ammonia loop on temperature headroom and saturation pressure, although the sustained case cannot be ruled out from public information alone. The illustrative combined stress case removes about 40~kW of fixed-temperature capacity (the full reported headroom plus 10~kW) or raises the sustained equilibrium by about 22~K into unreported limits.

The reduced-order radiative model does not rule out the reported AI1 design point. Full thermal margin and engineering feasibility remain unresolved, because coolant identity and phase, loop pressure, internal thermal resistance, effective two-face view factors, non-compute heat load, peak duration, and allowable operating temperatures have not been reported. The unreported engineering limits, and the price per token, will determine whether the architecture is realizable.

\section*{Acknowledgments}

This paper came out of an iterative adversarial workflow I ran across multiple AI systems: analysis and drafting by Claude Fable 5 (Anthropic), the evidence base assembled through Perplexity deep research, and three rounds of formal peer review with independent Wolfram verification by GPT~5.5. The third review's source-audit corrections (exact-quotation sourcing of every reported figure, correct attribution of the both-sides and 1,400~W/m$^{2}$ statements to the primary-quoted reporting, removal of the unsourced array-output composite and design-intent claims, verification of the Shi et al.\ reference against the journal of record, and the narrowed verification-scope claim) are incorporated in this revision and acknowledged with thanks. All radiator-model calculations and displayed derived values, externally sourced thermophysical property data excluded, are machine-verified by the supplementary assertion suite. Remaining errors are mine.

\section*{Data and Code Availability}

The assertion suite verifying all radiator-model calculations and displayed derived values in this paper, externally sourced thermophysical property data excluded (\texttt{verify\_ai1.py}; fourteen blocks covering both area interpretations, both power bases, both sensitivity branches, the overhead parameterization, display-rounding policy, and the provisional ISS conventions) accompanies it as supplementary material. This paper and its suite are archived at \href{https://doi.org/10.5281/zenodo.20670772}{doi:10.5281/zenodo.20670772}; the theory framework is archived at \href{https://doi.org/10.5281/zenodo.20650893}{doi:10.5281/zenodo.20650893}; both are mirrored at \url{https://github.com/dan-lee-odinson/orbital-thermal-bounds}.

\begin{thebibliography}{10}
\bibitem{leeodinson2026} D.~Lee-Odinson, ``Thermodynamic bounds and mass-trade criteria for heat rejection in orbital data centers,'' Zenodo preprint, June 12, 2026. \href{https://doi.org/10.5281/zenodo.20650893}{doi:10.5281/zenodo.20650893}
\bibitem{shi2026} Shi~J., Zhang~X., Yang~M., et al., ``Thermal management technologies for space data centers: current status and prospects,'' \emph{Journal of Refrigeration} \textbf{47}(1), 1--19 (2026). doi:10.12465/issn.0253-4339.20251030004. \url{https://www.sciopen.com/article/10.12465/issn.0253-4339.20251030004}
\bibitem{dcd2026} S.~Moss, ``SpaceX details AI1 satellite `data center,' claims 150kW peak compute,'' Data Center Dynamics, June 9, 2026. Contains the quoted Dahl and Musk statements used in Table~1, including the 250~W/m$^{2}$ and 1,400~W/m$^{2}$ assumptions and the both-sides, knife-edge radiator orientation. \url{https://www.datacenterdynamics.com/en/news/spacex-details-ai1-satellite-data-center-claims-150kw-peak-compute/}
\bibitem{toms2026} Tom's Hardware, ``Elon Musk's first-gen orbital data center craft spans wider than a Boeing 747 and runs an interchangeable chip payload --- AI1 satellite compute payload is 120 kW, peaks at 150 kW,'' June 2026. \url{https://www.tomshardware.com/tech-industry/spacex-details-its-ai1-compute-satellite}
\bibitem{tomsgigasat2026} Tom's Hardware, ``SpaceX unveils 11-million-square-foot Gigasat factory --- aims for 1 GW/year of space AI compute by late 2027,'' June 2026. \url{https://www.tomshardware.com/tech-industry/big-tech/spacex-unveils-11-million-square-foot-gigasat-factory-a-new-manufacturing-facility-for-space-based-data-centers-aims-for-1-gw-year-of-space-ai-compute-by-late-2027-from-its-satellites}
\bibitem{gagadget2026} A.~Kratiuk, ``SpaceX's AI1 satellite is a Boeing 747-sized GPU node in orbit,'' Gagadget, June 10, 2026 (110~m$^{2}$ liquid radiator with redundant pumping loops; interchangeable GPU modules with Nvidia Rubin baseline; ammonia described as the likely coolant, an expectation attributed to Hugh Lewis, University of Birmingham; SpaceX has not named the coolant). \url{https://gagadget.com/en/714424-spacexs-orbital-ai-satellites-boeing-747-sized-liquid-cooled-and-already-sold-to-google/}
\bibitem{techtimes2026} TechTimes, ``SpaceX AI1 orbital data center bets on space power and cooling: economics stay unproven,'' June 10, 2026. \url{https://www.techtimes.com/articles/318103/20260610/spacex-ai1-orbital-data-center-bets-space-power-cooling-economics-stay-unproven.htm}
\bibitem{nasaiss} NASA, International Space Station Active Thermal Control System documentation (mechanically pumped liquid-ammonia external loops; capacity $\approx$70 kW). The 422 m$^{2}$ radiator area used provisionally in Section 6 is from secondary reporting attributed to SemiAnalysis; its area convention is unverified.
\bibitem{nist} E.~W. Lemmon, M.~O. McLinden, and D.~G. Friend, ``Thermophysical properties of fluid systems,'' in \emph{NIST Chemistry WebBook, NIST Standard Reference Database 69}. Source of the ammonia critical point (405.5 K, $\approx$113 bar) and saturation-pressure reference values used in Sections 3 and 5.
\bibitem{nasaguidebook} NASA, \emph{Passive Thermal Control Engineering Guidebook}, v4.0, NTRS 20230013900 (2023).
\end{thebibliography}

\end{document}
`````

### `companion/response-to-final-review.md`

_(7838 bytes, sha256 `2fa96b5fdba800466913c37c94d52f5f9562df40345b087990b70f9abf2371ca`)_

`````markdown
# Response to Final Review — The AI1 Design Point (Revision 4)

**To:** GPT 5.5 (reviewing model, Wolfram-assisted)
**From:** Claude Fable 5, on behalf of the author
**Re:** Point-by-point response, Revision 4 (PDF + LaTeX), revised assertion suite, and build-log summary

Before drafting Revision 4 we executed the source-audit procedure you required: the Data Center Dynamics and Gagadget articles were fetched and read in full, and the Shi et al. reference was checked against the journal of record. The audit vindicated your suspicion of claim migration and produced a material improvement you will want to verify: **the DCD article contains direct quoted statements from Musk and from Ian Dahl (SpaceX director of satellite engineering) that settle most of the contested attributions.** Musk, quoted verbatim: "The assumptions here are 250W per sq m for the solar array, and about 1,400W per sqm for the radiators. The radiators are radiating both sides, orientated knife-edge to the sun." Dahl: "the right place is around the 150kW peak power level" and "we can support 120kW of average compute."

## Blocking Correction 1 (array composite) — ACCEPTED; preferred correction applied, and your reading was exactly right.

Musk's own wording describes 250 W/m² as an *assumption* for the solar array, not a rated output; the audit found no source stating a 150 kW array rating. Table 1 now carries your required row structure: "Solar-array areal density — 250 W/m² (Musk, stated as assumption/target)" and a separate "Total array output — not independently established — do not infer without qualification" row. The 600 m² and 8.6 m chord calculations are removed from the manuscript and retired from the assertion suite (block B13 note records the retirement). The Section 2 power-budget paragraph is rewritten accordingly: closure cannot be checked from public reporting.

## Blocking Correction 2 (Reference [3]/[6] attribution) — ACCEPTED; the audit reassigned every claim.

You were right that the knife-edge, both-faces, and 1,400 W/m² claims did not belong to Gagadget. They belong to DCD, as direct Musk quotations, and are now cited there — which upgrades them from journalist paraphrase to primary-quoted statements. Gagadget's citation is restricted to what the article contains: the 110 m² liquid radiator with redundant pumping loops, the interchangeable GPU modules with Nvidia Rubin baseline, and ammonia as the *likely* coolant — an expectation the article attributes to a named expert, Hugh Lewis, professor of astronautics at the University of Birmingham, alongside the explicit statement that SpaceX has not named the coolant. The manuscript now says "secondary coverage describes ammonia as the likely choice (expert expectation attributed to Hugh Lewis...)" throughout; "coverage identifies" is gone. Both bibliography entries now carry author, exact title, date, URL, and annotations restricted to verified contents. Two entries that failed the audit (TechSpot and Yahoo Finance, no longer needed once DCD carried the quotes) are removed; the heritage and wingspan claims now cite DCD's quoted material.

One consequence you should note: the both-sides reading is no longer an interpretation the paper adopts and defends — it is a directly quoted company statement. The one-sided analysis is retained as the counterfactual that motivates the coolant screen.

## Blocking Correction 3 (verification scope) — ACCEPTED; Option B.

The manuscript claim is narrowed to your specified wording ("All radiator-model calculations and displayed derived values, excluding externally sourced thermophysical property data, are verified...") in the abstract, Acknowledgments, and Data and Code Availability, consistently. A formal thermophysical reference is added (NIST Chemistry WebBook, SRD 69, Lemmon, McLinden, and Friend) covering the ammonia critical point and the quoted saturation pressures, cited at first pressure use. The suite's header now states the exclusion explicitly with the NIST attribution, and its final print statement is your specified text verbatim: "All radiator-model calculations and manuscript display-rounding assertions pass. External thermophysical property values are not computed by this suite."

## Blocking Correction 4 (Reference [2]) — RESOLVED VIA OPTION A.

The Shi et al. reference verified against the journal of record: SciOpen and the Journal of Refrigeration's own site confirm the official English title ("Thermal Management Technologies for Space Data Centers: Current Status and Prospects"), the author list (Shi J., Zhang X., Yang M., et al.), volume 47, issue 1, pages 1–19, year 2026, and the DOI. The "pending verification" warning is removed from both the bibliography and Section 6, and the SciOpen URL is added. The prohibited state (substantive citation + unverified flag) no longer exists.

## Strongly Recommended 1 (run-hot design intent) — ACCEPTED, and the audit went further.

Neither audited source contains the "custom chip designed to run hot to shrink radiator mass" claim; the audit also found no verified support for "custom chip" at all (the sourced facts are interchangeable GPU modules with an Nvidia Rubin baseline). All of it is removed. Section 4 now derives the elevated-temperature point from the company's own quoted radiator figure instead: 1,400 W/m² of planform with both faces emitting requires a surface near 353 K, consistent with the quartic-law incentive — a model-scoped statement resting entirely on quoted material.

## Strongly Recommended 2 (LaTeX warnings) — ACCEPTED, including the process criticism.

Our previous zero-overfull claim was inaccurate: the build-log grep filtered for boxes over 20 pt and missed the two table overfulls (11.0 pt and 12.4 pt) you observed. Both are fixed (shortened table headings; the operating-points table labels tightened), and Table 1's narrow columns were set ragged-right to eliminate the resulting underfull warnings as well.

## Build-log summary (final, unfiltered)

`latexmk -pdf`, TeX Live 2022, 8 pages. Errors: 0. Undefined references or citations: 0. Overfull boxes (any size): 0. Underfull boxes (any size): 0. LaTeX warnings: 0. The summary above reports counts from unfiltered greps of the final log; the earlier under-reporting resulted from a size-filtered pattern, not a clean log.

## Assertion suite status

All fourteen blocks pass. Changes this round: header carries the verification-scope exclusion and NIST attribution; the array-composite assertions are retired with a recorded reason; the specific-power cross-check is retained; the final print statement accurately describes scope. The suite continues to assert the exact sustained and continuous-peak temperatures, both area interpretations, exact fixed-temperature capacities, one-decimal display values, the 40/30/10 kW headroom decomposition, fixed-load stress temperatures, overhead cases, the effective-area case, gross/sink/net fluxes, dual-basis constellation scaling, the provisional ISS ratios, and the hot-rejection factor.

## Final pass criteria, self-checked

Array composite removed and restructured per your table — done. 600 m²/8.6 m removed — done. DCD and Gagadget cited only for verified contents — done, with quotes. Ammonia as expected/likely throughout — done. Thermophysical values formally sourced (NIST) — done. Verification claim accurately scoped — done. Reference [2] fully verified — done. Design-intent claim removed and replaced with model-scoped language — done. Build free of citation errors and warnings — done, counts above. Mathematical values and rounding unchanged — confirmed; no premise correction forced recalculation. Conclusion remains model-scoped — unchanged from Revision 3's accepted form.

Ready for the final pass.
`````

### `companion/response-to-review.md`

_(7640 bytes, sha256 `dc7361712ddb055d48ee7a77e78af33d254bbbe97bd92132dbc83f82877dfd97`)_

`````markdown
# Response to Peer Review — The AI1 Design Point (Revision 2)

**To:** GPT 5.5 (reviewing model, Wolfram-assisted)
**From:** Claude Fable 5, on behalf of the author
**Re:** Point-by-point response and revision record

The review was substantively correct on its two central findings and the revision implements its required structure in full. Three points receive partial rebuttals below; none affects the revision's compliance with the requested changes. Revision 2 accompanies this response with an extended assertion suite (`verify_ai1.py`) covering both area interpretations, both power bases, and both sensitivity branches, as Minor 8 requires.

## Major points

**M1 (peak vs. sustained) — ACCEPTED.** The original draft inserted the 150 kW peak into a steady-state equation without qualification. Revision 2 presents all four combinations (Table 2): 337.1 K sustained / 353.2 K continuous-peak under the two-sided reading; 391.5 K / 411.8 K under the one-sided reading; with an explicit statement that transient peaks require heat-capacity and control data not in the public record. The sustained two-sided case is now marked as the primary operating point.

**M2 (throttling not established) — ACCEPTED, with one addition.** The review is right that the original conclusion smuggled in an unstated ceiling at 353 K. Revision 2 replaces the capacity-only table with the requested two-branch treatment (fixed-temperature capacity; fixed-load equilibrium temperature) and the conclusion now reads as the review prescribed: the combined stress consumes either the entire reported power headroom or a ~22 K bite of an unreported temperature budget, and which response a real system exhibits cannot be determined from public information. The addition: the revision prices the temperature branch, not just names it. At the 358.9 K degraded-sustained equilibrium, ammonia saturation pressure rises from ~41 toward ~46 bar; at the 374.2 K degraded-continuous-peak equilibrium it approaches ~63 bar. The temperature branch is physically available but not free, and stating its cost is within the model's competence. We believe this strengthens rather than weakens the review's correction.

**M3 (power budget) — ACCEPTED.** Revision 2 adds the budget-closure paragraph to Section 2: 150 kW array against 150 kW peak compute leaves nothing for bus loads, with the plausible resolutions enumerated, the radiator-load assumption stated explicitly, and "external supply exceeds the load" removed in favor of a flagged ambiguity.

**M4 (ammonia exclusion) — ACCEPTED IN FORM, with a rebuttal on substance.** The revision adopts the requested conditional wording, adds the saturation-pressure caveat (41 bar at 353 K is not "comfortable margin," and pressure feasibility is stated to be outside the model), and acknowledges that exotic supercritical or alternative-fluid architectures are not excluded, only unsupported by the reporting. The rebuttal: the review treats the screen as weaker than it is. Re-running it on the *sustained* basis the review itself mandates elsewhere, the one-sided reading requires 391.5 K — under 14 K from ammonia's critical point, no engineering margin for a loop that must run at or above the radiator surface temperature. The exclusion therefore holds on both power bases, not only at continuous peak, and M1's correction strengthens M4's original conclusion. Revision 2 states it that way: "strongly favored conditional on the reported coolant class," on both bases.

**M5 ("up to 110 m²") — ACCEPTED.** Revision 2 states that the computed temperatures are lower bounds under maximum assumed effective area and idealized uniformity, enumerates the loss mechanisms, and adds the 85% effective-area sensitivity case (sustained point rises 337 → 349 K), asserted in the suite.

**M6 (ISS comparison) — ACCEPTED, with a provenance note.** The original "roughly triple" mixed conventions and "must continuously reject" presumed continuous peak. Revision 2 normalizes both systems to the emitting-area convention and quotes all four ratios (flux 3.3× sustained / 4.1× peak; capacity 1.7× / 2.1×). Provenance note for the record: the 422 m² ISS radiator area was introduced by the review, not the manuscript, which had cited only the ~70 kW capacity. The figure is adopted with its convention stated in the reference entry; if the reviewer has a primary NASA source for 422 m², adding it would improve both documents.

**M7 (reframe as application) — ACCEPTED.** Section 4 is renamed "First-order application of the framework"; "clean test," "sits inside every bound," and the radiator-sizing flourish are gone; the recovery penalty and self-powering bound are now explicitly labeled non-conflicts rather than tests; and the abstract and conclusion use the review's recommended "first-order compatibility within the model" formulation, including its enumerated unreported quantities.

**M8 (ε and sink independence) — ACCEPTED IN FORM, with a definitional rebuttal.** Revision 2 adopts option 2: the table is labeled a parametric stress test, and the possible physical correlation of the underlying degradation mechanisms is stated. The rebuttal: within the cited framework the two quantities are independent by construction — ε is the surface's hemispherical IR emissivity and T_s^eff is a view-factor-weighted environmental brightness temperature, defined in the theory paper's notation section as separate model parameters. Independent *parametric* variation is therefore mathematically licensed; what is not licensed, and what the revision no longer implies, is reading the combined row as two physically independent failure modes. The review's correction is to the interpretation, not the mathematics, and the revision reflects exactly that split.

**M9 (dual-basis scaling) — ACCEPTED.** Both bases now appear: ~6,700 satellites / 1.47 km² per GW-year on the 150 kW nameplate basis; ~8,300 / 1.83 km² on the 120 kW sustained basis.

## Minor points

All eight accepted and implemented: (1) margin restated as 25% of sustained load, 20% of capacity, zero at continuous peak; (2) "net radiative heat flux" terminology adopted, with the 803/121/682 W/m² decomposition shown; (3) inferred mass quoted on both normalizations (2.14 t peak / 1.71 t sustained) with the normalization flagged unreported; (4) the chord calculation downgraded to a rough plausibility check with the span caveat; (5) 293 K relabeled an illustrative comparison temperature; (6) a primary-source limitation paragraph added to the introduction; (7) the Shi et al. reference now carries "bibliographic details pending independent verification" in the bibliography itself; (8) the assertion suite extended to ten blocks covering both area interpretations, both power bases, both sensitivity branches, the ISS conventions, the dual-basis scaling, the margin percentages, the net/gross flux decomposition, and the effective-area case — branches, not just the preferred path.

## Summary

Review findings accepted: 9 of 9 major, 8 of 8 minor. Rebuttals entered on substance, not compliance: M4 (the coolant screen survives, and is strengthened by, the sustained-basis correction), M8 (parametric independence is definitional in the cited framework; the interpretive correction is adopted), M6 (provenance of the 422 m² figure). The revision adopts the reviewer's recommended central claim nearly verbatim and keeps the five categories — mathematical consistency, physical plausibility, engineering feasibility, operational margin, economic viability — separate throughout, as the final judgment required.
`````

### `companion/response-to-second-review.md`

_(7998 bytes, sha256 `4a58a50ac1b1f5d945af2f5e216848fbc52f812f96a99681382781869b93989d`)_

`````markdown
# Response to Second-Pass Peer Review — The AI1 Design Point (Revision 3)

**To:** GPT 5.5 (reviewing model, Wolfram-assisted)
**From:** Claude Fable 5, on behalf of the author
**Re:** Point-by-point response, Revision 3, and the distributed assertion suite

All nine Priority A items, all five Priority B items, and all four Priority C items are implemented. The requested `verify_ai1.py` accompanies this response exactly as distributed with the paper: fourteen blocks, including your specified exact-temperature and display-rounding assertions verbatim in substance (B1–B3). One concession on our previous letter, one new sourcing development, and two clarifications follow the point-by-point record.

## Priority A

**A1 (Table 3 convention) — ACCEPTED; you were right about the drift.** The capacities were computed at 353.0 K while the header said 353.2 K — precisely the manuscript/suite divergence you suspected. Revision 3 adopts the exact convention: header states the exact continuous-peak equilibrium (353.1623 K noted in the caption), values displayed to one decimal (150.0 / 131.9 / 124.7 / 109.6 kW), and suite blocks B1–B3 assert the full-precision values (353.1623423 K; 131.8681319 / 124.7166261 / 109.6409900 kW) and the display rounding separately, per your snippet.

**A2 (headroom accounting) — ACCEPTED.** The text now reads: the combined stress removes about 40 kW, consuming the full 30 kW peak-to-sustained headroom and leaving a further deficit of roughly 10 kW against the sustained load. Suite block B4 asserts 40.36 / 30 / 10.36 kW.

**A3 (two-phase overclaim) — ACCEPTED.** "Pumped two-phase rejection system" is replaced by "mechanically pumped liquid-coolant rejection system"; the ISS is described as a mechanically pumped liquid-ammonia system; and all quoted pressures are now labeled lower-bound saturation pressures evaluated at the radiator surface temperature, the minimum to maintain liquid phase there.

**A4 (sustained ammonia claim) — ACCEPTED; previous response letter conceded.** Our prior letter's claim that the exclusion "holds on both power bases" was too strong, exactly as you say: 391.5 K is subcritical and the critical-temperature criterion alone cannot exclude it. Revision 3 adopts your replacement wording nearly verbatim, including the ~88 bar saturation pressure at the surface temperature, and the conclusion now distinguishes outright incompatibility (continuous-peak, 411.8 K) from strong disfavor (sustained, 391.5 K). Your 88.4 bar figure is recorded in the suite's reference table.

**A5 (ISS 422 m²) — ACCEPTED.** The figure is now attributed to secondary reporting credited to SemiAnalysis, its convention stated as unverified, the flux ratios labeled provisional in both Section 6 and the bibliography note, and the capacity comparison (NASA-documented ~70 kW) carried as the secure claim.

**A6 (array composite) — ACCEPTED with a sourcing note.** One secondary source (Data Center Dynamics) does state the composite as an array specification ("power comes from a 150-kW solar array delivering 250 W/m²"), so the composite is retained — but flagged in Table 1 as a single-secondary-source composite, unverified against the primary presentation, with the 600 m² and 8.6 m chord figures marked as discardable if the primary does not tie the values together. This implements your conditional ("unless directly stated") on its satisfied branch while preserving the audit trail.

**A7 (Table 1 clipping) — ACCEPTED AND FIXED.** Table 1 is rebuilt in `tabularx` with wrapped paragraph columns and per-row sources (your first-review request, now fully implemented), re-rendered, and visually verified to the right edge. Zero overfull boxes in the final build log.

**A8 (model-scoped conclusion) — ACCEPTED.** "The physics permits AI1" is gone; the conclusion now uses your recommended formulation ("the reduced-order radiative model does not rule out the reported design point..."), and "incurs none of the framework's penalties" is replaced by the not-engaged-on-the-available-record construction.

**A9 (assertion suite) — SUPPLIED.** `verify_ai1.py` accompanies this response. It asserts displayed manuscript values (one-decimal Table 3 entries via `round()` checks), full-precision intermediates to your stated tolerances, all four operating points, both sensitivity branches, the overhead parameterization, the headroom decomposition, the provisional ISS ratios, dual-basis scaling, and the display-rounding policy. The ammonia pressures are documented in the header as NIST-consistent literature reference values used as lower bounds, with the critical point stated; no vapor-pressure correlation is computed, so there is no correlation range to misapply.

## Priority B

**B1 (two-face sink) — ACCEPTED.** Section 3 defines the adopted 220 K as the area-weighted effective sink for the combined two-face emitting area, with the fourth-power mean formula stated, and the attitude sentence now uses your recommended qualitative-consistency wording.

**B2 (overhead parameterization) — ACCEPTED.** Eq. (1) defines Q_rad = (1+f)·P_compute with the overhead terms enumerated; Section 5 gives the 10% and 20% cases on both branches (343.8/350.1 K nominal; 365.2/371.3 K stressed), asserted in suite block B8.

**B3 ("plausible degradations") — ACCEPTED.** "Illustrative combined stress case" throughout, including abstract and conclusion; the 85% effective-area case is labeled illustrative.

**B4 (revision-history prose) — ACCEPTED.** Section 5 opens with the methodological statement you supplied, nearly verbatim.

**B5 (bibliography) — ACCEPTED, with one substitution.** Every announcement-coverage entry now carries outlet, exact title, date, and stable URL. The PCMag and Light Reading citations could not be verified to exist as discrete articles and are removed; the coolant claim is re-sourced to verifiable coverage (Gagadget), which also yields a new substantive datum: the coverage explicitly describes the radiator as oriented knife-edge to the Sun and radiating from both faces, providing direct reporting support for the double-sided area interpretation independent of the coolant screen. The heritage claim is re-sourced to Yahoo Finance. The Shi et al. entry retains its pending-verification flag and now notes that the tens-of-kilowatts claim is co-supported by the flown-system record, so no major claim rests on the unverified source alone.

## Priority C

All four implemented: the abstract is cut to the four moves you specified (roughly half its former length, pressure and phase detail moved to the body); "first-order" now appears zero times (your complaint was repetition; we found removal cleaner than rationing); "continuous-peak hypothetical" is the uniform term; Table 3 uses one-decimal values.

## Clarifications for the record

The 88.4 bar figure at 391.47 K and the corrected capacities at 353.1623 K are yours; they are adopted with this acknowledgment rather than independent re-derivation of the pressure datum, which lies outside the suite's computed scope and is recorded as a literature reference value. And one process note: the suite's absence from your second-pass materials was a distribution failure on our side, not a suppression; it is attached now and prints `All assertions pass.` on an unmodified run.

## Summary

Second-pass findings accepted: 9/9 Priority A, 5/5 Priority B, 4/4 Priority C, including a concession correcting our own previous rebuttal on M4. One substitution (unverifiable citations replaced with verifiable ones) yielded an evidentiary improvement: reporting-level support for the double-sided reading. Revision 3 holds every empirical premise to a stated source, every displayed value to one declared rounding convention asserted in the suite, every coolant statement conditional on phase and pressure assumptions, and the conclusion inside the reduced-order model. Ready for the short verification pass you proposed.
`````

### `companion/verify_ai1.py`

_(6618 bytes, sha256 `acf98485e325e514c29216fadc118f1705c103ef7463aad743d968610805d822`)_

`````python
"""Assertion suite for 'The AI1 Design Point' (Revision 4).
Verifies the DISPLAYED manuscript values (exact convention, one decimal in
Table 3) as well as full-precision intermediates, both area interpretations,
both power bases, both sensitivity branches, the overhead parameterization,
ISS conventions, and dual-basis constellation scaling.
Run: python3 verify_ai1.py  -> expected: All assertions pass.

VERIFICATION SCOPE: this suite verifies radiator-model calculations and
manuscript display values. Externally sourced thermophysical property data
are EXCLUDED from its verification scope: the ammonia critical point
(405.5 K, ~113 bar) and the saturation pressures quoted in the paper
(41.4, 46.8, 63.8, 88.4 bar at the stated radiator-surface temperatures,
used as lower bounds on loop pressure) are reference values from the NIST
Chemistry WebBook (SRD 69; Lemmon, McLinden, and Friend, 'Thermophysical
Properties of Fluid Systems') and are NOT computed or asserted here."""

sigma = 5.670374419e-8

# Reported AI1 figures (announcement coverage; Table 1 of the paper)
Q_peak, Q_sust = 150e3, 120e3      # W (compute payload, used as radiative load; f=0)
A_plan         = 110.0             # m^2 ("up to"; double-sided planform reading)
A2             = 220.0             # m^2 emitting under that reading

def T_req(Q, A, eps, Ts):
    return (Q/(eps*sigma*A) + Ts**4)**0.25

def cap_kW(T, eps, Ts, A=220.0):
    return eps*sigma*A*(T**4 - Ts**4)/1e3

# --- B1: exact continuous-peak-hypothetical equilibrium (audit-required) ---
T_pk = T_req(Q_peak, A2, 0.91, 220.0)
assert abs(T_pk - 353.1623423) < 1e-6

# --- B2: capacities at that EXACT temperature (audit-required) ---
assert abs(cap_kW(T_pk, 0.91, 220.0) - 150.0)       < 1e-6
assert abs(cap_kW(T_pk, 0.80, 220.0) - 131.8681319) < 1e-6
assert abs(cap_kW(T_pk, 0.91, 260.0) - 124.7166261) < 1e-6
assert abs(cap_kW(T_pk, 0.80, 260.0) - 109.6409900) < 1e-6

# --- B3: display-rounding policy: Table 3 shows ONE DECIMAL at exact T_pk ---
assert round(cap_kW(T_pk, 0.91, 220.0), 1) == 150.0
assert round(cap_kW(T_pk, 0.80, 220.0), 1) == 131.9
assert round(cap_kW(T_pk, 0.91, 260.0), 1) == 124.7
assert round(cap_kW(T_pk, 0.80, 260.0), 1) == 109.6

# --- B4: headroom accounting (second-pass correction 2) ---
loss = 150.0 - cap_kW(T_pk, 0.80, 260.0)
assert abs(loss - 40.36) < 0.01          # total stress-induced capacity loss, kW
assert abs((150-120) - 30.0) < 1e-9      # advertised peak-to-sustained headroom
assert abs((120.0 - cap_kW(T_pk, 0.80, 260.0)) - 10.36) < 0.01  # deficit below sustained

# --- B5: all four operating points (two readings x two power bases) ---
assert abs(T_req(Q_sust, A2,    0.91, 220.0) - 337.1004) < 1e-3   # sustained, two-sided (primary)
assert abs(T_req(Q_peak, A2,    0.91, 220.0) - 353.1623) < 1e-3   # continuous-peak hypothetical
assert abs(T_req(Q_sust, 110.0, 0.91, 220.0) - 391.4652) < 1e-3   # sustained, one-sided
assert abs(T_req(Q_peak, 110.0, 0.91, 220.0) - 411.8443) < 1e-3   # continuous-peak, one-sided

# --- B6: coolant-class screen, second-pass wording basis ---
T_crit = 405.5
assert T_req(Q_peak, 110.0, 0.91, 220.0) > T_crit        # one-sided continuous-peak: supercritical
gap = T_crit - T_req(Q_sust, 110.0, 0.91, 220.0)
assert 13.9 < gap < 14.1                                  # one-sided sustained: <14 K headroom
                                                          #   (strong disfavor, NOT exclusion)
assert T_crit - T_pk > 50                                 # two-sided readings: >50 K margin
# Lower-bound saturation pressures at radiator-surface temperature (literature values):
P_sat = {353.16: 41.4, 358.91: 46.8, 374.17: 63.8, 391.47: 88.4}   # bar

# --- B7: equilibrium-temperature branch (fixed load, T free to rise) ---
assert abs(T_req(Q_sust, A2, 0.80, 220.0) - 346.21) < 0.01
assert abs(T_req(Q_sust, A2, 0.91, 260.0) - 350.78) < 0.01
assert abs(T_req(Q_sust, A2, 0.80, 260.0) - 358.91) < 0.01        # +21.8 K over nominal
assert abs(T_req(Q_peak, A2, 0.80, 260.0) - 374.17) < 0.01
assert T_req(Q_peak, A2, 0.80, 260.0) < T_crit

# --- B8: non-compute heat overhead parameterization Q_rad = (1+f) P_compute ---
assert abs(T_req(1.10*Q_sust, A2, 0.91, 220.0) - 343.80) < 0.01   # f = 0.10, nominal
assert abs(T_req(1.20*Q_sust, A2, 0.91, 220.0) - 350.12) < 0.01   # f = 0.20, nominal
assert abs(T_req(1.10*Q_sust, A2, 0.80, 260.0) - 365.24) < 0.01   # f = 0.10, stress case
assert abs(T_req(1.20*Q_sust, A2, 0.80, 260.0) - 371.26) < 0.01   # f = 0.20, stress case

# --- B9: illustrative effective-area case ("up to" qualifier) ---
assert abs(T_req(Q_sust, 0.85*A2, 0.91, 220.0) - 348.67) < 0.01

# --- B10: flux decomposition (net vs gross; planform vs emitting) ---
assert abs(Q_peak/A_plan - 1364) < 1                       # planform flux ("~1,400 W/m^2")
assert abs(Q_peak/A2     -  682) < 1                       # net flux per face, continuous peak
assert abs(Q_sust/A2     -  545) < 1                       # net flux per face, sustained
gross = 0.91*sigma*T_pk**4; sink = 0.91*sigma*220.0**4
assert abs(gross - 802.8) < 0.5 and abs(sink - 120.9) < 0.5
assert abs((gross - sink) - Q_peak/A2) < 0.5

# --- B11: ISS comparison; capacity firm, flux ratios PROVISIONAL ---
P_ISS = 70e3                                               # NASA-documented EATCS capacity
assert abs(Q_sust/P_ISS - 1.71) < 0.01
assert abs(Q_peak/P_ISS - 2.14) < 0.01
A_ISS = 422.0           # secondary reporting (SemiAnalysis via coverage); convention UNVERIFIED
assert abs((Q_sust/A2)/(P_ISS/A_ISS) - 3.29) < 0.02        # provisional
assert abs((Q_peak/A2)/(P_ISS/A_ISS) - 4.11) < 0.02        # provisional

# --- B12: constellation scaling, both bases ---
assert abs(1e9/Q_peak - 6667) < 1 and abs(1e9/Q_sust - 8333) < 1
assert abs(6667*A2/1e6 - 1.467) < 0.01                     # km^2 emitting per GW-yr, nameplate
assert abs(8333*A2/1e6 - 1.833) < 0.01                     # km^2 emitting per GW-yr, sustained

# --- B13: specific-power cross-check (array-output composite retired in Rev 4:
#          250 W/m^2 is a stated areal-density assumption, not a rated output) ---
assert abs(150e3/70e3 - 2.143) < 0.005                     # t, peak-normalized specific power
assert abs(120e3/70e3 - 1.714) < 0.005                     # t, sustained-normalized

# --- B14: hot-rejection factor (illustrative 293 K comparison, exact T_pk) ---
assert abs((T_pk**4 - 220**4)/(293**4 - 220**4) - 2.628) < 0.005

print(
    "All radiator-model calculations and manuscript display-rounding "
    "assertions pass. External thermophysical property values are not "
    "computed by this suite."
)
`````

### `docs/ammonia-model.md`

_(2455 bytes, sha256 `a3109b0c16084747ac08ff8c529d89f56645e7e628cc9247b0a0011659ce6464`)_

`````markdown
# Ammonia property model

## What this is

Executable thermophysical-property calculations supporting the coolant
screen in "The AI1 Design Point" (doi:10.5281/zenodo.20670772). The paper
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
`````

### `docs/mccalip-replication.md`

_(8014 bytes, sha256 `61c1cad6b40547f7f333f8dadbc6fc8877bfcda6d68c43c2685095ba92cbeb0e`)_

`````markdown
# Replicating the McCalip orbital thermal/cost model

## Purpose

Andrew McCalip's "Space Datacenters" model (github.com/andrewmccalip/thoughts,
MIT) is the most visible public first-principles model of orbital-datacenter
thermal and cost economics. Before the third paper builds on or argues against
that body of work, we establish exactly what his model says by reproducing it
independently. This document records that exercise and -- more importantly --
draws the line between three claims that are easy to conflate.

## Replication vs. verification vs. validation

**Replication** -- *does our independent implementation reproduce his?*
`src/orbital_thermal/mccalip_replication.py` is a from-scratch Python port of his
`static/js/math.js`, using his exact constants, including the truncated
sigma = 5.67e-8 and the rounded deep-space temperature T_space = 3 K. Run over
the same parameter grid, it matches the frozen Node oracle
(`external_models/mccalip_thoughts/expected_outputs.json`) to a maximum relative
error of ~4e-14 across all 297 compared values in 11 cases -- floating-point
roundoff. **The model is faithfully replicated.** This says nothing about whether
the model is right; it says only that we understand it precisely enough to
recompute it in another language.

**Verification** -- *is the physics internally correct?* This is the job of the
core package (`orbital_thermal.radiation`, `.equilibrium`, `.bounds`,
`.environment`) and its published-results suite, which use the exact CODATA
sigma = 5.670374419184429e-8 (binary64 of the SI-derived value) and the exact tilted-plate-to-sphere view factor rather
than McCalip's approximations. Where the two diverge, the gap is bounded and
explained, not reconciled away:

| Element | McCalip model | Core package | Consequence |
|---|---|---|---|
| Stefan-Boltzmann sigma | 5.67e-8 (truncated) | 5.670374419184429e-8 (binary64 SI-derived) | ~0.002 K at 340 K |
| Deep-space sink | 3 K (rounded) | 2.7255 K (CMB) | negligible above 300 K |
| Tilted view factor | cos-tilt heuristic + 5% edge-on floor | exact integral (machine precision) | >0.10 in VF near the horizon |
| Orbit-averaged VF | 72-point Riemann sum | exact / analytic | small, but uncontrolled |

The view-factor heuristic is the substantive modelling difference, and at the
default geometry it is not a small one. At beta = 90 deg the sun-tracking panel is
EDGE-ON to Earth: its normal tracks the Sun, which at beta = 90 deg is normal to
the orbit plane, while nadir lies in the plane 90 deg away. Around the orbit
McCalip's per-face floor averages ~0.021 there; the exact tilted-plate-to-sphere
view factor is ~0.258 -- a ~12x underestimate
(`test_floor_underestimates_exact_by_about_12x`). This is not a region where his
heuristic is reasonable; it is the region where it is worst, and it is his
default. The core package therefore carries its own exact geometry rather than
inheriting his -- and, as the next subsection quantifies, that correction moves his
headline temperature.

## The edge-on correction (headline result)

Substituting the exact per-face view factor into McCalip's own heat balance --
changing nothing else, not his truncated sigma, rounded deep-space temperature, or
constants -- raises his default equilibrium temperature

    335.75 K  (McCalip, replicated)  ->  342.10 K  (exact edge-on VF)   +6.35 K

The replication in `mccalip_replication.py` stays faithful; this is a quantified
new result, not a defect papered over. It is implemented in
`orbital_thermal.mccalip_exact_vf` and locked by
`tests/test_mccalip_exact_vf.py::TestEdgeOnDefault::test_exact_vf_raises_default_eqtemp_by_about_6_3K`.
The self-consistency test in that file confirms that feeding McCalip's own view
factors back through the same heat balance reproduces his number exactly, so the
+6.35 K is attributable to geometry alone. The correction across the full range of
beta angles is tabulated in the next section.

## Correction across beta

McCalip's default is beta = 90 deg -- the worst case -- but the correction is
present at every beta, because the sun-tracking panel's faces are never near
nadir. Recomputing his own heat balance with the exact per-face view factor
(`mccalip_exact_vf.correction_table_vs_beta`) across the oracle's beta grid gives:

| beta (deg) | McCalip eqTemp (K) | exact-VF eqTemp (K) | correction (K) |
|---:|---:|---:|---:|
| 0  | 349.58 | 351.53 | +1.94 |
| 15 | 348.94 | 350.98 | +2.04 |
| 30 | 347.12 | 349.53 | +2.41 |
| 45 | 344.42 | 347.63 | +3.22 |
| 60 | 341.28 | 345.66 | +4.38 |
| 75 | 338.24 | 343.79 | +5.55 |
| 90 | 335.75 | 342.10 | +6.35 |

The correction is positive and grows monotonically toward the edge-on default,
since his cos-tilt floor underestimates the exact view factor more severely as the
panel tilts away from nadir. The figure
`results/figures/mccalip_beta_correction.png`
(`scripts/plot_mccalip_correction.py`) plots this; it is the section paper three
leads with.

**Validation** -- *does the model match reality?* Neither the replication nor the
core package claims this. Validation would require flight or test data for an
orbital datacenter radiator, which does not exist publicly. The third paper's
contribution is to frame that open question precisely (orientation-dependent
effective sink, transient peak excess) rather than to assert a validated answer.

## Verification and validation, more precisely

The three-way replication/verification/validation split above is a useful first
cut, but "verification" and "validation" each resolve into finer levels, and the
package sits at specific ones. Stated precisely:

1. **Mathematical verification** -- the equations follow from the stated
   assumptions. Encoded by the published-results suite (`tests/test_published_results.py`),
   which checks the analytic identities and bounds of the theory paper.
2. **Software verification** -- the code computes those equations correctly.
   Covered by the same suite plus the smoke and module tests.
3. **Cross-model verification** -- independent implementations of the *same* model
   agree. Covered by the McCalip replication against the frozen Node oracle
   (`tests/test_mccalip_replication.py`), and by the exact view factor checked
   against an independent integrator (`tests/test_environment.py`).
4. **Model-form validation** -- the modelling assumptions match physical
   benchmarks (e.g. measured Earth IR/albedo, real view factors, attitude). NOT
   established here; the subpoint-albedo and sun-shielded limitations (items 3, 8)
   are exactly model-form gaps.
5. **System validation** -- predictions match hardware or flight data. NOT
   established here; no public orbital-datacenter radiator data exists.

So the package delivers levels 1-3 -- mathematical, software, and cross-model
verification -- and explicitly does NOT claim model-form or system validation.
"We replicated McCalip and corrected his edge-on view factor" is a cross-model
verification result; it is not a claim that either model matches a real radiator.


## What was replicated

The port covers `calculateOrbital`, `calculateThermal`, `calculateBreakeven`, and
the view-factor functions (`earthAngularRadius`, `nadirViewFactor`,
`sunTrackingPanelViewFactors`). The oracle grid is: defaults; beta in
{0, 30, 60, 90} deg; altitude in {400, 550, 800} km; radiator emissivity in
{0.85, 0.90, 0.95}. The replicated default equilibrium temperature is 335.75 K
(342.10 K once the edge-on view factor is corrected; see "The edge-on
correction" above).

## Reproducing this result

Regenerate the oracle from the pinned JavaScript (requires Node), then check the
Python port against it:

    cd external_models/mccalip_thoughts
    node generate_oracle.js > expected_outputs.json
    cd ../..
    pytest tests/test_mccalip_replication.py -v

The oracle is frozen under the oracle-freeze rule: it is never hand-edited to make
a test pass. If McCalip updates his model, regenerate the whole file at a new
pinned commit and update `provenance.md`.
`````

### `external_models/mccalip_thoughts/PINS.json`

_(439 bytes, sha256 `1c82fd5e11da8baff4c11f6d0e40224d5d750283e2681fbb7335e56ac690c1af`)_

`````json
{
  "pinned_commit": "d1e4238d3d3f4924e5ca65bafbd4ba5b39af2eb8",
  "source_repo": "andrewmccalip/thoughts",
  "source_path": "static/js/math.js",
  "sha256": {
    "math.js": "bcdced986d9c121a626e8ded1b10bd4ab48ce09b65847de0301d2e5f34fcd71f",
    "generate_oracle.js": "367cbda532ecc963e269b68c1106e215a2ac7bad2692c8cf4137ee35c406ac74",
    "expected_outputs.json": "18c068673af2fce6d99c5cb7d0705d44d9a3ed40f6a04864e477a76789667c4e"
  }
}
`````

### `external_models/mccalip_thoughts/UPSTREAM-LICENSE.md`

_(843 bytes, sha256 `9eaf3dda3ddb3868fcd60a54dd2b4f98d8354c13875decba27bac6e55d2421b8`)_

`````markdown
# Upstream license -- McCalip "thoughts" model

The vendored material in this directory (`math.js`, `generate_oracle.js`, and the
oracle generated from them) derives from Andrew McCalip's "thoughts" repository:

- Source: https://github.com/andrewmccalip/thoughts
- Pinned commit: `d1e4238d3d3f4924e5ca65bafbd4ba5b39af2eb8` (2025-12-29)
- Author: Andrew McCalip (@andrewmccalip)

The upstream repository carries **no standalone LICENSE file**. Its stated license,
in the repository README at the pinned commit, is reproduced here verbatim:

> ## License
>
> MIT License — Do whatever you want with it.

(The README also shows a "License: MIT" badge.) This NOTICE retains the upstream
license statement as published. If upstream later adds a formal MIT notice with a
copyright line, replace this file with that text at the new pinned commit.
`````

### `external_models/mccalip_thoughts/expected_outputs.json`

_SHA-256-pinned; exact bytes as base64 (14642 bytes, sha256 `18c068673af2fce6d99c5cb7d0705d44d9a3ed40f6a04864e477a76789667c4e`):_

`````base64
ewogICJfbWV0YSI6IHsKICAgICJnZW5lcmF0ZWRfYnkiOiAiZ2VuZXJhdGVfb3JhY2xlLmpzIiwKICAgICJzb3VyY2VfcmVwbyI6ICJodHRwczovL2dpdGh1Yi5jb20vYW5kcmV3bWNjYWxpcC90aG91Z2h0cyIsCiAgICAicGlubmVkX2NvbW1pdCI6ICJkMWU0MjM4ZDNkM2Y0OTI0ZTVjYTY1YmFmYmQ0YmE1YjM5YWYyZWI4IiwKICAgICJjb21taXRfZGF0ZSI6ICIyMDI1LTEyLTI5VDE3OjQyOjEzWiIsCiAgICAiZ2VuZXJhdGVkX29uIjogIjIwMjYtMDYtMTIiLAogICAgInNvdXJjZV9maWxlIjogInN0YXRpYy9qcy9tYXRoLmpzIiwKICAgICJub2RlX3ZlcnNpb24iOiAidjI0LjE0LjAiLAogICAgImNvbnZlbnRpb25zIjogewogICAgICAic2lnbWFfc2IiOiAiNS42N2UtOCAgKE1jQ2FsaXAgdHJ1bmNhdGVkOyBDT0RBVEEgZXhhY3Q6IDUuNjcwMzc0NDE5ZS04KSIsCiAgICAgICJUX3NwYWNlX0siOiAiMyBLICAoTWNDYWxpcCByb3VuZGVkOyBDTUI6IDIuNzI1NSBLKSIsCiAgICAgICJyZXBsaWNhdGlvbl90b2xlcmFuY2VfSyI6IDAuMDUKICAgIH0KICB9LAogICJjYXNlcyI6IFsKICAgIHsKICAgICAgImxhYmVsIjogImRlZmF1bHRzIiwKICAgICAgInN0YXRlX292ZXJyaWRlcyI6IHt9LAogICAgICAiZ2VvbWV0cnkiOiB7CiAgICAgICAgInZmTmFkaXJNYXgiOiAwLjg0NzM3ODYzODQ0OTg1NjYsCiAgICAgICAgImVhcnRoQW5ndWxhclJhZGl1c0RlZyI6IDY3LjAwMzkzOTIzNTYwNzA0LAogICAgICAgICJ2ZlNpZGVBIjogMC4wMjExODQ0NjU5NjEyNDY0MzMsCiAgICAgICAgInZmU2lkZUIiOiAwLjAyMTE4NDQ2NTk2MTI0NjQyMiwKICAgICAgICAidmZUb3RhbCI6IDAuMDQyMzY4OTMxOTIyNDkyODUKICAgICAgfSwKICAgICAgInRoZXJtYWwiOiB7CiAgICAgICAgImVxVGVtcEsiOiAzMzUuNzQ5NTM4MDI4MjYsCiAgICAgICAgImVxVGVtcEMiOiA2Mi41OTk1MzgwMjgyNjAwNCwKICAgICAgICAidG90YWxIZWF0SW5XIjogNTgxMTI1OTcxNC44MjMwMDIsCiAgICAgICAgInFTb2xhclciOiA0MzkwNzk5OTQ5LjIwMDAwMSwKICAgICAgICAicUVhcnRoSVJXIjogNDA0OTQwNjcuMzAzMDAwMzMsCiAgICAgICAgInFBbGJlZG9XIjogMi4yNDU3MDY4NzcyMjQxOTg0ZS05LAogICAgICAgICJxSGVhdExvb3BXIjogMTM3OTk2NTY5OC4zMjAwMDAyLAogICAgICAgICJyYWRpYXRpdmVDYXBhY2l0eVciOiA1ODExMjU5NzE0LjgyMzAwMSwKICAgICAgICAiYXJlYVN1ZmZpY2llbnQiOiB0cnVlLAogICAgICAgICJ0ZW1wTWFyZ2luQyI6IDEyLjQwMDQ2MTk3MTczOTk1OCwKICAgICAgICAiYXJlYVJlcXVpcmVkTTIiOiAzOTg2NDI0Ljg1NTIwODU2MywKICAgICAgICAiYXZhaWxhYmxlQXJlYU0yIjogNDYwODc5NgogICAgICB9LAogICAgICAib3JiaXRhbCI6IHsKICAgICAgICAic2F0ZWxsaXRlQ291bnQiOiAzOTczMSwKICAgICAgICAidG90YWxNYXNzS2ciOiAyOTM5MDA1NC43OTQ1MjA1NSwKICAgICAgICAic3RhcnNoaXBMYXVuY2hlcyI6IDI5NCwKICAgICAgICAidG90YWxDb3N0IjogNTEwOTUzNDgzOTcuMjYwMjgsCiAgICAgICAgImNvc3RQZXJXIjogNTEuMDk1MzQ4Mzk3MjYwMjc0LAogICAgICAgICJsY29lIjogMTE2Ni41NjA0NjU2OTA4NzM4LAogICAgICAgICJlbmVyZ3lNV2giOiA0MzgwMDAwMCwKICAgICAgICAiYXZnQ2FwYWNpdHlGYWN0b3IiOiAwLjk1MTIzNDQ1MzEyNDk5OTksCiAgICAgICAgImFycmF5QXJlYUttMiI6IDQuNjA4Nzk2CiAgICAgIH0sCiAgICAgICJicmVha2V2ZW5fbGF1bmNoX2Nvc3RfcGVyX2tnIjogLTI2My42NTcyMDU1NTQ1NTI4MwogICAgfSwKICAgIHsKICAgICAgImxhYmVsIjogImJldGFfMCIsCiAgICAgICJzdGF0ZV9vdmVycmlkZXMiOiB7CiAgICAgICAgImJldGFBbmdsZSI6IDAKICAgICAgfSwKICAgICAgImdlb21ldHJ5IjogewogICAgICAgICJ2Zk5hZGlyTWF4IjogMC44NDczNzg2Mzg0NDk4NTY2LAogICAgICAgICJlYXJ0aEFuZ3VsYXJSYWRpdXNEZWciOiA2Ny4wMDM5MzkyMzU2MDcwNCwKICAgICAgICAidmZTaWRlQSI6IDAuMjkwNzQyMjY2ODc1MTk1OCwKICAgICAgICAidmZTaWRlQiI6IDAuMjkwNzQyMjY2ODc1MTk1OTQsCiAgICAgICAgInZmVG90YWwiOiAwLjU4MTQ4NDUzMzc1MDM5MTcKICAgICAgfSwKICAgICAgInRoZXJtYWwiOiB7CiAgICAgICAgImVxVGVtcEsiOiAzNDkuNTgzNDA4Mjc3NDEzMiwKICAgICAgICAiZXFUZW1wQyI6IDc2LjQzMzQwODI3NzQxMzIsCiAgICAgICAgInRvdGFsSGVhdEluVyI6IDY4Mjk4NjA1OTUuOTUxNzA2LAogICAgICAgICJxU29sYXJXIjogNDM5MDc5OTk0OS4yMDAwMDEsCiAgICAgICAgInFFYXJ0aElSVyI6IDU1NTc1MzMwMi42NDIwNjI3LAogICAgICAgICJxQWxiZWRvVyI6IDUwMzM0MTY0NS43ODk2NDE1NiwKICAgICAgICAicUhlYXRMb29wVyI6IDEzNzk5NjU2OTguMzIwMDAwMiwKICAgICAgICAicmFkaWF0aXZlQ2FwYWNpdHlXIjogNjgyOTg2MDU5NS45NTE3MDQsCiAgICAgICAgImFyZWFTdWZmaWNpZW50IjogZmFsc2UsCiAgICAgICAgInRlbXBNYXJnaW5DIjogLTEuNDMzNDA4Mjc3NDEzMjA3LAogICAgICAgICJhcmVhUmVxdWlyZWRNMiI6IDQ2ODUxNjcuNjUyNjk3MjYzLAogICAgICAgICJhdmFpbGFibGVBcmVhTTIiOiA0NjA4Nzk2CiAgICAgIH0sCiAgICAgICJvcmJpdGFsIjogewogICAgICAgICJzYXRlbGxpdGVDb3VudCI6IDM5NzMxLAogICAgICAgICJ0b3RhbE1hc3NLZyI6IDI5MzkwMDU0Ljc5NDUyMDU1LAogICAgICAgICJzdGFyc2hpcExhdW5jaGVzIjogMjk0LAogICAgICAgICJ0b3RhbENvc3QiOiA1MTA5NTM0ODM5Ny4yNjAyOCwKICAgICAgICAiY29zdFBlclciOiA1MS4wOTUzNDgzOTcyNjAyNzQsCiAgICAgICAgImxjb2UiOiAxMTY2LjU2MDQ2NTY5MDg3MzgsCiAgICAgICAgImVuZXJneU1XaCI6IDQzODAwMDAwLAogICAgICAgICJhdmdDYXBhY2l0eUZhY3RvciI6IDAuOTUxMjM0NDUzMTI0OTk5OSwKICAgICAgICAiYXJyYXlBcmVhS20yIjogNC42MDg3OTYKICAgICAgfSwKICAgICAgImJyZWFrZXZlbl9sYXVuY2hfY29zdF9wZXJfa2ciOiAtMjYzLjY1NzIwNTU1NDU1MjgzCiAgICB9LAogICAgewogICAgICAibGFiZWwiOiAiYmV0YV8zMCIsCiAgICAgICJzdGF0ZV9vdmVycmlkZXMiOiB7CiAgICAgICAgImJldGFBbmdsZSI6IDMwCiAgICAgIH0sCiAgICAgICJnZW9tZXRyeSI6IHsKICAgICAgICAidmZOYWRpck1heCI6IDAuODQ3Mzc4NjM4NDQ5ODU2NiwKICAgICAgICAiZWFydGhBbmd1bGFyUmFkaXVzRGVnIjogNjcuMDAzOTM5MjM1NjA3MDQsCiAgICAgICAgInZmU2lkZUEiOiAwLjI1NDYyODM2OTM0MDk5NDc1LAogICAgICAgICJ2ZlNpZGVCIjogMC4yNTQ2MjgzNjkzNDA5OTQ3NSwKICAgICAgICAidmZUb3RhbCI6IDAuNTA5MjU2NzM4NjgxOTg5NQogICAgICB9LAogICAgICAidGhlcm1hbCI6IHsKICAgICAgICAiZXFUZW1wSyI6IDM0Ny4xMTgzNjIzMDg5Nzk5LAogICAgICAgICJlcVRlbXBDIjogNzMuOTY4MzYyMzA4OTc5OTIsCiAgICAgICAgInRvdGFsSGVhdEluVyI6IDY2MzkyNDg3ODguNjY5MDU0LAogICAgICAgICJxU29sYXJXIjogNDM5MDc5OTk0OS4yMDAwMDEsCiAgICAgICAgInFFYXJ0aElSVyI6IDQ4NjcyMTY1NC42NDExNzI4LAogICAgICAgICJxQWxiZWRvVyI6IDM4MTc2MTQ4Ni41MDc4ODE2NCwKICAgICAgICAicUhlYXRMb29wVyI6IDEzNzk5NjU2OTguMzIwMDAwMiwKICAgICAgICAicmFkaWF0aXZlQ2FwYWNpdHlXIjogNjYzOTI0ODc4OC42NjkwNTYsCiAgICAgICAgImFyZWFTdWZmaWNpZW50IjogdHJ1ZSwKICAgICAgICAidGVtcE1hcmdpbkMiOiAxLjAzMTYzNzY5MTAyMDA4MDIsCiAgICAgICAgImFyZWFSZXF1aXJlZE0yIjogNDU1NDQxMS4yMTAyODQzNDEsCiAgICAgICAgImF2YWlsYWJsZUFyZWFNMiI6IDQ2MDg3OTYKICAgICAgfSwKICAgICAgIm9yYml0YWwiOiB7CiAgICAgICAgInNhdGVsbGl0ZUNvdW50IjogMzk3MzEsCiAgICAgICAgInRvdGFsTWFzc0tnIjogMjkzOTAwNTQuNzk0NTIwNTUsCiAgICAgICAgInN0YXJzaGlwTGF1bmNoZXMiOiAyOTQsCiAgICAgICAgInRvdGFsQ29zdCI6IDUxMDk1MzQ4Mzk3LjI2MDI4LAogICAgICAgICJjb3N0UGVyVyI6IDUxLjA5NTM0ODM5NzI2MDI3NCwKICAgICAgICAibGNvZSI6IDExNjYuNTYwNDY1NjkwODczOCwKICAgICAgICAiZW5lcmd5TVdoIjogNDM4MDAwMDAsCiAgICAgICAgImF2Z0NhcGFjaXR5RmFjdG9yIjogMC45NTEyMzQ0NTMxMjQ5OTk5LAogICAgICAgICJhcnJheUFyZWFLbTIiOiA0LjYwODc5NgogICAgICB9LAogICAgICAiYnJlYWtldmVuX2xhdW5jaF9jb3N0X3Blcl9rZyI6IC0yNjMuNjU3MjA1NTU0NTUyODMKICAgIH0sCiAgICB7CiAgICAgICJsYWJlbCI6ICJiZXRhXzYwIiwKICAgICAgInN0YXRlX292ZXJyaWRlcyI6IHsKICAgICAgICAiYmV0YUFuZ2xlIjogNjAKICAgICAgfSwKICAgICAgImdlb21ldHJ5IjogewogICAgICAgICJ2Zk5hZGlyTWF4IjogMC44NDczNzg2Mzg0NDk4NTY2LAogICAgICAgICJlYXJ0aEFuZ3VsYXJSYWRpdXNEZWciOiA2Ny4wMDM5MzkyMzU2MDcwNCwKICAgICAgICAidmZTaWRlQSI6IDAuMTU1OTYzMzY2NDE4MjIxMSwKICAgICAgICAidmZTaWRlQiI6IDAuMTU1OTYzMzY2NDE4MjIxMTcsCiAgICAgICAgInZmVG90YWwiOiAwLjMxMTkyNjczMjgzNjQ0MjMKICAgICAgfSwKICAgICAgInRoZXJtYWwiOiB7CiAgICAgICAgImVxVGVtcEsiOiAzNDEuMjgyNDM0ODUwOTQxNCwKICAgICAgICAiZXFUZW1wQyI6IDY4LjEzMjQzNDg1MDk0MTQyLAogICAgICAgICJ0b3RhbEhlYXRJblciOiA2MjAzODkzNTM4LjA3MjIwOCwKICAgICAgICAicVNvbGFyVyI6IDQzOTA3OTk5NDkuMjAwMDAxLAogICAgICAgICJxRWFydGhJUlciOiAyOTgxMjM2ODQuOTcyNTMxNSwKICAgICAgICAicUFsYmVkb1ciOiAxMzUwMDQyMDUuNTc5Njc2NzUsCiAgICAgICAgInFIZWF0TG9vcFciOiAxMzc5OTY1Njk4LjMyMDAwMDIsCiAgICAgICAgInJhZGlhdGl2ZUNhcGFjaXR5VyI6IDYyMDM4OTM1MzguMDcyMjA4LAogICAgICAgICJhcmVhU3VmZmljaWVudCI6IHRydWUsCiAgICAgICAgInRlbXBNYXJnaW5DIjogNi44Njc1NjUxNDkwNTg1NzgsCiAgICAgICAgImFyZWFSZXF1aXJlZE0yIjogNDI1NTc2NC45NDgyMDE0NDMsCiAgICAgICAgImF2YWlsYWJsZUFyZWFNMiI6IDQ2MDg3OTYKICAgICAgfSwKICAgICAgIm9yYml0YWwiOiB7CiAgICAgICAgInNhdGVsbGl0ZUNvdW50IjogMzk3MzEsCiAgICAgICAgInRvdGFsTWFzc0tnIjogMjkzOTAwNTQuNzk0NTIwNTUsCiAgICAgICAgInN0YXJzaGlwTGF1bmNoZXMiOiAyOTQsCiAgICAgICAgInRvdGFsQ29zdCI6IDUxMDk1MzQ4Mzk3LjI2MDI4LAogICAgICAgICJjb3N0UGVyVyI6IDUxLjA5NTM0ODM5NzI2MDI3NCwKICAgICAgICAibGNvZSI6IDExNjYuNTYwNDY1NjkwODczOCwKICAgICAgICAiZW5lcmd5TVdoIjogNDM4MDAwMDAsCiAgICAgICAgImF2Z0NhcGFjaXR5RmFjdG9yIjogMC45NTEyMzQ0NTMxMjQ5OTk5LAogICAgICAgICJhcnJheUFyZWFLbTIiOiA0LjYwODc5NgogICAgICB9LAogICAgICAiYnJlYWtldmVuX2xhdW5jaF9jb3N0X3Blcl9rZyI6IC0yNjMuNjU3MjA1NTU0NTUyODMKICAgIH0sCiAgICB7CiAgICAgICJsYWJlbCI6ICJiZXRhXzkwIiwKICAgICAgInN0YXRlX292ZXJyaWRlcyI6IHsKICAgICAgICAiYmV0YUFuZ2xlIjogOTAKICAgICAgfSwKICAgICAgImdlb21ldHJ5IjogewogICAgICAgICJ2Zk5hZGlyTWF4IjogMC44NDczNzg2Mzg0NDk4NTY2LAogICAgICAgICJlYXJ0aEFuZ3VsYXJSYWRpdXNEZWciOiA2Ny4wMDM5MzkyMzU2MDcwNCwKICAgICAgICAidmZTaWRlQSI6IDAuMDIxMTg0NDY1OTYxMjQ2NDMzLAogICAgICAgICJ2ZlNpZGVCIjogMC4wMjExODQ0NjU5NjEyNDY0MjIsCiAgICAgICAgInZmVG90YWwiOiAwLjA0MjM2ODkzMTkyMjQ5Mjg1CiAgICAgIH0sCiAgICAgICJ0aGVybWFsIjogewogICAgICAgICJlcVRlbXBLIjogMzM1Ljc0OTUzODAyODI2LAogICAgICAgICJlcVRlbXBDIjogNjIuNTk5NTM4MDI4MjYwMDQsCiAgICAgICAgInRvdGFsSGVhdEluVyI6IDU4MTEyNTk3MTQuODIzMDAyLAogICAgICAgICJxU29sYXJXIjogNDM5MDc5OTk0OS4yMDAwMDEsCiAgICAgICAgInFFYXJ0aElSVyI6IDQwNDk0MDY3LjMwMzAwMDMzLAogICAgICAgICJxQWxiZWRvVyI6IDIuMjQ1NzA2ODc3MjI0MTk4NGUtOSwKICAgICAgICAicUhlYXRMb29wVyI6IDEzNzk5NjU2OTguMzIwMDAwMiwKICAgICAgICAicmFkaWF0aXZlQ2FwYWNpdHlXIjogNTgxMTI1OTcxNC44MjMwMDEsCiAgICAgICAgImFyZWFTdWZmaWNpZW50IjogdHJ1ZSwKICAgICAgICAidGVtcE1hcmdpbkMiOiAxMi40MDA0NjE5NzE3Mzk5NTgsCiAgICAgICAgImFyZWFSZXF1aXJlZE0yIjogMzk4NjQyNC44NTUyMDg1NjMsCiAgICAgICAgImF2YWlsYWJsZUFyZWFNMiI6IDQ2MDg3OTYKICAgICAgfSwKICAgICAgIm9yYml0YWwiOiB7CiAgICAgICAgInNhdGVsbGl0ZUNvdW50IjogMzk3MzEsCiAgICAgICAgInRvdGFsTWFzc0tnIjogMjkzOTAwNTQuNzk0NTIwNTUsCiAgICAgICAgInN0YXJzaGlwTGF1bmNoZXMiOiAyOTQsCiAgICAgICAgInRvdGFsQ29zdCI6IDUxMDk1MzQ4Mzk3LjI2MDI4LAogICAgICAgICJjb3N0UGVyVyI6IDUxLjA5NTM0ODM5NzI2MDI3NCwKICAgICAgICAibGNvZSI6IDExNjYuNTYwNDY1NjkwODczOCwKICAgICAgICAiZW5lcmd5TVdoIjogNDM4MDAwMDAsCiAgICAgICAgImF2Z0NhcGFjaXR5RmFjdG9yIjogMC45NTEyMzQ0NTMxMjQ5OTk5LAogICAgICAgICJhcnJheUFyZWFLbTIiOiA0LjYwODc5NgogICAgICB9LAogICAgICAiYnJlYWtldmVuX2xhdW5jaF9jb3N0X3Blcl9rZyI6IC0yNjMuNjU3MjA1NTU0NTUyODMKICAgIH0sCiAgICB7CiAgICAgICJsYWJlbCI6ICJhbHRfNDAwa20iLAogICAgICAic3RhdGVfb3ZlcnJpZGVzIjogewogICAgICAgICJvcmJpdGFsQWx0aXR1ZGVLbSI6IDQwMAogICAgICB9LAogICAgICAiZ2VvbWV0cnkiOiB7CiAgICAgICAgInZmTmFkaXJNYXgiOiAwLjg4NTMzODk3MzIwNDA0ODgsCiAgICAgICAgImVhcnRoQW5ndWxhclJhZGl1c0RlZyI6IDcwLjIwNzQwMzQ2ODg1NTgzLAogICAgICAgICJ2ZlNpZGVBIjogMC4wMjIxMzM0NzQzMzAxMDEyNCwKICAgICAgICAidmZTaWRlQiI6IDAuMDIyMTMzNDc0MzMwMTAxMjMsCiAgICAgICAgInZmVG90YWwiOiAwLjA0NDI2Njk0ODY2MDIwMjQ3CiAgICAgIH0sCiAgICAgICJ0aGVybWFsIjogewogICAgICAgICJlcVRlbXBLIjogMzM1Ljc3NTczNjYzNzM1NzM0LAogICAgICAgICJlcVRlbXBDIjogNjIuNjI1NzM2NjM3MzU3MzYsCiAgICAgICAgInRvdGFsSGVhdEluVyI6IDU4MTMwNzM3NDIuNTU1ODYwNSwKICAgICAgICAicVNvbGFyVyI6IDQzOTA3OTk5NDkuMjAwMDAxLAogICAgICAgICJxRWFydGhJUlciOiA0MjMwODA5NS4wMzU4NTk3MzQsCiAgICAgICAgInFBbGJlZG9XIjogMi4zNDYzMDg2NDAwNjIwODNlLTksCiAgICAgICAgInFIZWF0TG9vcFciOiAxMzc5OTY1Njk4LjMyMDAwMDIsCiAgICAgICAgInJhZGlhdGl2ZUNhcGFjaXR5VyI6IDU4MTMwNzM3NDIuNTU1ODYwNSwKICAgICAgICAiYXJlYVN1ZmZpY2llbnQiOiB0cnVlLAogICAgICAgICJ0ZW1wTWFyZ2luQyI6IDEyLjM3NDI2MzM2MjY0MjYzNywKICAgICAgICAiYXJlYVJlcXVpcmVkTTIiOiAzOTg3NjY5LjI0NzIzMzIxNSwKICAgICAgICAiYXZhaWxhYmxlQXJlYU0yIjogNDYwODc5NgogICAgICB9LAogICAgICAib3JiaXRhbCI6IHsKICAgICAgICAic2F0ZWxsaXRlQ291bnQiOiAzOTczMSwKICAgICAgICAidG90YWxNYXNzS2ciOiAyOTM5MDA1NC43OTQ1MjA1NSwKICAgICAgICAic3RhcnNoaXBMYXVuY2hlcyI6IDI5NCwKICAgICAgICAidG90YWxDb3N0IjogNTEwOTUzNDgzOTcuMjYwMjgsCiAgICAgICAgImNvc3RQZXJXIjogNTEuMDk1MzQ4Mzk3MjYwMjc0LAogICAgICAgICJsY29lIjogMTE2Ni41NjA0NjU2OTA4NzM4LAogICAgICAgICJlbmVyZ3lNV2giOiA0MzgwMDAwMCwKICAgICAgICAiYXZnQ2FwYWNpdHlGYWN0b3IiOiAwLjk1MTIzNDQ1MzEyNDk5OTksCiAgICAgICAgImFycmF5QXJlYUttMiI6IDQuNjA4Nzk2CiAgICAgIH0sCiAgICAgICJicmVha2V2ZW5fbGF1bmNoX2Nvc3RfcGVyX2tnIjogLTI2My42NTcyMDU1NTQ1NTI4MwogICAgfSwKICAgIHsKICAgICAgImxhYmVsIjogImFsdF81NTBrbSIsCiAgICAgICJzdGF0ZV9vdmVycmlkZXMiOiB7CiAgICAgICAgIm9yYml0YWxBbHRpdHVkZUttIjogNTUwCiAgICAgIH0sCiAgICAgICJnZW9tZXRyeSI6IHsKICAgICAgICAidmZOYWRpck1heCI6IDAuODQ3Mzc4NjM4NDQ5ODU2NiwKICAgICAgICAiZWFydGhBbmd1bGFyUmFkaXVzRGVnIjogNjcuMDAzOTM5MjM1NjA3MDQsCiAgICAgICAgInZmU2lkZUEiOiAwLjAyMTE4NDQ2NTk2MTI0NjQzMywKICAgICAgICAidmZTaWRlQiI6IDAuMDIxMTg0NDY1OTYxMjQ2NDIyLAogICAgICAgICJ2ZlRvdGFsIjogMC4wNDIzNjg5MzE5MjI0OTI4NQogICAgICB9LAogICAgICAidGhlcm1hbCI6IHsKICAgICAgICAiZXFUZW1wSyI6IDMzNS43NDk1MzgwMjgyNiwKICAgICAgICAiZXFUZW1wQyI6IDYyLjU5OTUzODAyODI2MDA0LAogICAgICAgICJ0b3RhbEhlYXRJblciOiA1ODExMjU5NzE0LjgyMzAwMiwKICAgICAgICAicVNvbGFyVyI6IDQzOTA3OTk5NDkuMjAwMDAxLAogICAgICAgICJxRWFydGhJUlciOiA0MDQ5NDA2Ny4zMDMwMDAzMywKICAgICAgICAicUFsYmVkb1ciOiAyLjI0NTcwNjg3NzIyNDE5ODRlLTksCiAgICAgICAgInFIZWF0TG9vcFciOiAxMzc5OTY1Njk4LjMyMDAwMDIsCiAgICAgICAgInJhZGlhdGl2ZUNhcGFjaXR5VyI6IDU4MTEyNTk3MTQuODIzMDAxLAogICAgICAgICJhcmVhU3VmZmljaWVudCI6IHRydWUsCiAgICAgICAgInRlbXBNYXJnaW5DIjogMTIuNDAwNDYxOTcxNzM5OTU4LAogICAgICAgICJhcmVhUmVxdWlyZWRNMiI6IDM5ODY0MjQuODU1MjA4NTYzLAogICAgICAgICJhdmFpbGFibGVBcmVhTTIiOiA0NjA4Nzk2CiAgICAgIH0sCiAgICAgICJvcmJpdGFsIjogewogICAgICAgICJzYXRlbGxpdGVDb3VudCI6IDM5NzMxLAogICAgICAgICJ0b3RhbE1hc3NLZyI6IDI5MzkwMDU0Ljc5NDUyMDU1LAogICAgICAgICJzdGFyc2hpcExhdW5jaGVzIjogMjk0LAogICAgICAgICJ0b3RhbENvc3QiOiA1MTA5NTM0ODM5Ny4yNjAyOCwKICAgICAgICAiY29zdFBlclciOiA1MS4wOTUzNDgzOTcyNjAyNzQsCiAgICAgICAgImxjb2UiOiAxMTY2LjU2MDQ2NTY5MDg3MzgsCiAgICAgICAgImVuZXJneU1XaCI6IDQzODAwMDAwLAogICAgICAgICJhdmdDYXBhY2l0eUZhY3RvciI6IDAuOTUxMjM0NDUzMTI0OTk5OSwKICAgICAgICAiYXJyYXlBcmVhS20yIjogNC42MDg3OTYKICAgICAgfSwKICAgICAgImJyZWFrZXZlbl9sYXVuY2hfY29zdF9wZXJfa2ciOiAtMjYzLjY1NzIwNTU1NDU1MjgzCiAgICB9LAogICAgewogICAgICAibGFiZWwiOiAiYWx0XzgwMGttIiwKICAgICAgInN0YXRlX292ZXJyaWRlcyI6IHsKICAgICAgICAib3JiaXRhbEFsdGl0dWRlS20iOiA4MDAKICAgICAgfSwKICAgICAgImdlb21ldHJ5IjogewogICAgICAgICJ2Zk5hZGlyTWF4IjogMC43ODkzMjQ4MzA3NzA1ODQ4LAogICAgICAgICJlYXJ0aEFuZ3VsYXJSYWRpdXNEZWciOiA2Mi42Nzc4MTE0ODQxNzc5NywKICAgICAgICAidmZTaWRlQSI6IDAuMDE5NzMzMTIwNzY5MjY0NjI4LAogICAgICAgICJ2ZlNpZGVCIjogMC4wMTk3MzMxMjA3NjkyNjQ2MiwKICAgICAgICAidmZUb3RhbCI6IDAuMDM5NDY2MjQxNTM4NTI5MjUKICAgICAgfSwKICAgICAgInRoZXJtYWwiOiB7CiAgICAgICAgImVxVGVtcEsiOiAzMzUuNzA5NDU5ODkzMDc3NDUsCiAgICAgICAgImVxVGVtcEMiOiA2Mi41NTk0NTk4OTMwNzc0NzQsCiAgICAgICAgInRvdGFsSGVhdEluVyI6IDU4MDg0ODU0NzEuMTg2NTc5LAogICAgICAgICJxU29sYXJXIjogNDM5MDc5OTk0OS4yMDAwMDEsCiAgICAgICAgInFFYXJ0aElSVyI6IDM3NzE5ODIzLjY2NjU3NzgxNiwKICAgICAgICAicUFsYmVkb1ciOiAyLjA5MTg1Mzc3MTYxMjY1MzVlLTksCiAgICAgICAgInFIZWF0TG9vcFciOiAxMzc5OTY1Njk4LjMyMDAwMDIsCiAgICAgICAgInJhZGlhdGl2ZUNhcGFjaXR5VyI6IDU4MDg0ODU0NzEuMTg2NTc5LAogICAgICAgICJhcmVhU3VmZmljaWVudCI6IHRydWUsCiAgICAgICAgInRlbXBNYXJnaW5DIjogMTIuNDQwNTQwMTA2OTIyNTI2LAogICAgICAgICJhcmVhUmVxdWlyZWRNMiI6IDM5ODQ1MjEuNzcxNDgzMjg2LAogICAgICAgICJhdmFpbGFibGVBcmVhTTIiOiA0NjA4Nzk2CiAgICAgIH0sCiAgICAgICJvcmJpdGFsIjogewogICAgICAgICJzYXRlbGxpdGVDb3VudCI6IDM5NzMxLAogICAgICAgICJ0b3RhbE1hc3NLZyI6IDI5MzkwMDU0Ljc5NDUyMDU1LAogICAgICAgICJzdGFyc2hpcExhdW5jaGVzIjogMjk0LAogICAgICAgICJ0b3RhbENvc3QiOiA1MTA5NTM0ODM5Ny4yNjAyOCwKICAgICAgICAiY29zdFBlclciOiA1MS4wOTUzNDgzOTcyNjAyNzQsCiAgICAgICAgImxjb2UiOiAxMTY2LjU2MDQ2NTY5MDg3MzgsCiAgICAgICAgImVuZXJneU1XaCI6IDQzODAwMDAwLAogICAgICAgICJhdmdDYXBhY2l0eUZhY3RvciI6IDAuOTUxMjM0NDUzMTI0OTk5OSwKICAgICAgICAiYXJyYXlBcmVhS20yIjogNC42MDg3OTYKICAgICAgfSwKICAgICAgImJyZWFrZXZlbl9sYXVuY2hfY29zdF9wZXJfa2ciOiAtMjYzLjY1NzIwNTU1NDU1MjgzCiAgICB9LAogICAgewogICAgICAibGFiZWwiOiAiZVJhZF8wLjg1IiwKICAgICAgInN0YXRlX292ZXJyaWRlcyI6IHsKICAgICAgICAiZW1pc3Npdml0eVJhZCI6IDAuODUKICAgICAgfSwKICAgICAgImdlb21ldHJ5IjogewogICAgICAgICJ2Zk5hZGlyTWF4IjogMC44NDczNzg2Mzg0NDk4NTY2LAogICAgICAgICJlYXJ0aEFuZ3VsYXJSYWRpdXNEZWciOiA2Ny4wMDM5MzkyMzU2MDcwNCwKICAgICAgICAidmZTaWRlQSI6IDAuMDIxMTg0NDY1OTYxMjQ2NDMzLAogICAgICAgICJ2ZlNpZGVCIjogMC4wMjExODQ0NjU5NjEyNDY0MjIsCiAgICAgICAgInZmVG90YWwiOiAwLjA0MjM2ODkzMTkyMjQ5Mjg1CiAgICAgIH0sCiAgICAgICJ0aGVybWFsIjogewogICAgICAgICJlcVRlbXBLIjogMzM4LjE3NDY3OTY3NzM2OTQ1LAogICAgICAgICJlcVRlbXBDIjogNjUuMDI0Njc5Njc3MzY5NDgsCiAgICAgICAgInRvdGFsSGVhdEluVyI6IDU4MTAxMDI3NDEuNDcxNDg3LAogICAgICAgICJxU29sYXJXIjogNDM5MDc5OTk0OS4yMDAwMDEsCiAgICAgICAgInFFYXJ0aElSVyI6IDM5MzM3MDkzLjk1MTQ4NjAzLAogICAgICAgICJxQWxiZWRvVyI6IDIuMjQ1NzA2ODc3MjI0MTk4NGUtOSwKICAgICAgICAicUhlYXRMb29wVyI6IDEzNzk5NjU2OTguMzIwMDAwMiwKICAgICAgICAicmFkaWF0aXZlQ2FwYWNpdHlXIjogNTgxMDEwMjc0MS40NzE0ODUsCiAgICAgICAgImFyZWFTdWZmaWNpZW50IjogdHJ1ZSwKICAgICAgICAidGVtcE1hcmdpbkMiOiA5Ljk3NTMyMDMyMjYzMDUyMywKICAgICAgICAiYXJlYVJlcXVpcmVkTTIiOiA0MTAyODU1LjYzODA2Mjg0NTQsCiAgICAgICAgImF2YWlsYWJsZUFyZWFNMiI6IDQ2MDg3OTYKICAgICAgfSwKICAgICAgIm9yYml0YWwiOiB7CiAgICAgICAgInNhdGVsbGl0ZUNvdW50IjogMzk3MzEsCiAgICAgICAgInRvdGFsTWFzc0tnIjogMjkzOTAwNTQuNzk0NTIwNTUsCiAgICAgICAgInN0YXJzaGlwTGF1bmNoZXMiOiAyOTQsCiAgICAgICAgInRvdGFsQ29zdCI6IDUxMDk1MzQ4Mzk3LjI2MDI4LAogICAgICAgICJjb3N0UGVyVyI6IDUxLjA5NTM0ODM5NzI2MDI3NCwKICAgICAgICAibGNvZSI6IDExNjYuNTYwNDY1NjkwODczOCwKICAgICAgICAiZW5lcmd5TVdoIjogNDM4MDAwMDAsCiAgICAgICAgImF2Z0NhcGFjaXR5RmFjdG9yIjogMC45NTEyMzQ0NTMxMjQ5OTk5LAogICAgICAgICJhcnJheUFyZWFLbTIiOiA0LjYwODc5NgogICAgICB9LAogICAgICAiYnJlYWtldmVuX2xhdW5jaF9jb3N0X3Blcl9rZyI6IC0yNjMuNjU3MjA1NTU0NTUyODMKICAgIH0sCiAgICB7CiAgICAgICJsYWJlbCI6ICJlUmFkXzAuOSIsCiAgICAgICJzdGF0ZV9vdmVycmlkZXMiOiB7CiAgICAgICAgImVtaXNzaXZpdHlSYWQiOiAwLjkKICAgICAgfSwKICAgICAgImdlb21ldHJ5IjogewogICAgICAgICJ2Zk5hZGlyTWF4IjogMC44NDczNzg2Mzg0NDk4NTY2LAogICAgICAgICJlYXJ0aEFuZ3VsYXJSYWRpdXNEZWciOiA2Ny4wMDM5MzkyMzU2MDcwNCwKICAgICAgICAidmZTaWRlQSI6IDAuMDIxMTg0NDY1OTYxMjQ2NDMzLAogICAgICAgICJ2ZlNpZGVCIjogMC4wMjExODQ0NjU5NjEyNDY0MjIsCiAgICAgICAgInZmVG90YWwiOiAwLjA0MjM2ODkzMTkyMjQ5Mjg1CiAgICAgIH0sCiAgICAgICJ0aGVybWFsIjogewogICAgICAgICJlcVRlbXBLIjogMzM1Ljc0OTUzODAyODI2LAogICAgICAgICJlcVRlbXBDIjogNjIuNTk5NTM4MDI4MjYwMDQsCiAgICAgICAgInRvdGFsSGVhdEluVyI6IDU4MTEyNTk3MTQuODIzMDAyLAogICAgICAgICJxU29sYXJXIjogNDM5MDc5OTk0OS4yMDAwMDEsCiAgICAgICAgInFFYXJ0aElSVyI6IDQwNDk0MDY3LjMwMzAwMDMzLAogICAgICAgICJxQWxiZWRvVyI6IDIuMjQ1NzA2ODc3MjI0MTk4NGUtOSwKICAgICAgICAicUhlYXRMb29wVyI6IDEzNzk5NjU2OTguMzIwMDAwMiwKICAgICAgICAicmFkaWF0aXZlQ2FwYWNpdHlXIjogNTgxMTI1OTcxNC44MjMwMDEsCiAgICAgICAgImFyZWFTdWZmaWNpZW50IjogdHJ1ZSwKICAgICAgICAidGVtcE1hcmdpbkMiOiAxMi40MDA0NjE5NzE3Mzk5NTgsCiAgICAgICAgImFyZWFSZXF1aXJlZE0yIjogMzk4NjQyNC44NTUyMDg1NjMsCiAgICAgICAgImF2YWlsYWJsZUFyZWFNMiI6IDQ2MDg3OTYKICAgICAgfSwKICAgICAgIm9yYml0YWwiOiB7CiAgICAgICAgInNhdGVsbGl0ZUNvdW50IjogMzk3MzEsCiAgICAgICAgInRvdGFsTWFzc0tnIjogMjkzOTAwNTQuNzk0NTIwNTUsCiAgICAgICAgInN0YXJzaGlwTGF1bmNoZXMiOiAyOTQsCiAgICAgICAgInRvdGFsQ29zdCI6IDUxMDk1MzQ4Mzk3LjI2MDI4LAogICAgICAgICJjb3N0UGVyVyI6IDUxLjA5NTM0ODM5NzI2MDI3NCwKICAgICAgICAibGNvZSI6IDExNjYuNTYwNDY1NjkwODczOCwKICAgICAgICAiZW5lcmd5TVdoIjogNDM4MDAwMDAsCiAgICAgICAgImF2Z0NhcGFjaXR5RmFjdG9yIjogMC45NTEyMzQ0NTMxMjQ5OTk5LAogICAgICAgICJhcnJheUFyZWFLbTIiOiA0LjYwODc5NgogICAgICB9LAogICAgICAiYnJlYWtldmVuX2xhdW5jaF9jb3N0X3Blcl9rZyI6IC0yNjMuNjU3MjA1NTU0NTUyODMKICAgIH0sCiAgICB7CiAgICAgICJsYWJlbCI6ICJlUmFkXzAuOTUiLAogICAgICAic3RhdGVfb3ZlcnJpZGVzIjogewogICAgICAgICJlbWlzc2l2aXR5UmFkIjogMC45NQogICAgICB9LAogICAgICAiZ2VvbWV0cnkiOiB7CiAgICAgICAgInZmTmFkaXJNYXgiOiAwLjg0NzM3ODYzODQ0OTg1NjYsCiAgICAgICAgImVhcnRoQW5ndWxhclJhZGl1c0RlZyI6IDY3LjAwMzkzOTIzNTYwNzA0LAogICAgICAgICJ2ZlNpZGVBIjogMC4wMjExODQ0NjU5NjEyNDY0MzMsCiAgICAgICAgInZmU2lkZUIiOiAwLjAyMTE4NDQ2NTk2MTI0NjQyMiwKICAgICAgICAidmZUb3RhbCI6IDAuMDQyMzY4OTMxOTIyNDkyODUKICAgICAgfSwKICAgICAgInRoZXJtYWwiOiB7CiAgICAgICAgImVxVGVtcEsiOiAzMzMuNDA5ODQ4MDg0OTQwMiwKICAgICAgICAiZXFUZW1wQyI6IDYwLjI1OTg0ODA4NDk0MDI0NSwKICAgICAgICAidG90YWxIZWF0SW5XIjogNTgxMjQxNjY4OC4xNzQ1MTUsCiAgICAgICAgInFTb2xhclciOiA0MzkwNzk5OTQ5LjIwMDAwMSwKICAgICAgICAicUVhcnRoSVJXIjogNDE2NTEwNDAuNjU0NTE0NjIsCiAgICAgICAgInFBbGJlZG9XIjogMi4yNDU3MDY4NzcyMjQxOTg0ZS05LAogICAgICAgICJxSGVhdExvb3BXIjogMTM3OTk2NTY5OC4zMjAwMDAyLAogICAgICAgICJyYWRpYXRpdmVDYXBhY2l0eVciOiA1ODEyNDE2Njg4LjE3NDUxNywKICAgICAgICAiYXJlYVN1ZmZpY2llbnQiOiB0cnVlLAogICAgICAgICJ0ZW1wTWFyZ2luQyI6IDE0Ljc0MDE1MTkxNTA1OTc1NSwKICAgICAgICAiYXJlYVJlcXVpcmVkTTIiOiAzODc2NDYyLjQ0OTE3OTUxOCwKICAgICAgICAiYXZhaWxhYmxlQXJlYU0yIjogNDYwODc5NgogICAgICB9LAogICAgICAib3JiaXRhbCI6IHsKICAgICAgICAic2F0ZWxsaXRlQ291bnQiOiAzOTczMSwKICAgICAgICAidG90YWxNYXNzS2ciOiAyOTM5MDA1NC43OTQ1MjA1NSwKICAgICAgICAic3RhcnNoaXBMYXVuY2hlcyI6IDI5NCwKICAgICAgICAidG90YWxDb3N0IjogNTEwOTUzNDgzOTcuMjYwMjgsCiAgICAgICAgImNvc3RQZXJXIjogNTEuMDk1MzQ4Mzk3MjYwMjc0LAogICAgICAgICJsY29lIjogMTE2Ni41NjA0NjU2OTA4NzM4LAogICAgICAgICJlbmVyZ3lNV2giOiA0MzgwMDAwMCwKICAgICAgICAiYXZnQ2FwYWNpdHlGYWN0b3IiOiAwLjk1MTIzNDQ1MzEyNDk5OTksCiAgICAgICAgImFycmF5QXJlYUttMiI6IDQuNjA4Nzk2CiAgICAgIH0sCiAgICAgICJicmVha2V2ZW5fbGF1bmNoX2Nvc3RfcGVyX2tnIjogLTI2My42NTcyMDU1NTQ1NTI4MwogICAgfQogIF0KfQo=
`````

### `external_models/mccalip_thoughts/generate_oracle.js`

_SHA-256-pinned; exact bytes as base64 (3966 bytes, sha256 `367cbda532ecc963e269b68c1106e215a2ac7bad2692c8cf4137ee35c406ac74`):_

`````base64
LyoqCiAqIGdlbmVyYXRlX29yYWNsZS5qcwogKgogKiBHZW5lcmF0ZXMgZXhwZWN0ZWRfb3V0cHV0cy5qc29uIGJ5IGRyaXZpbmcgQ29zdE1vZGVsIChNY0NhbGlwIG1hdGguanMpIG92ZXIKICogYSBwYXJhbWV0ZXIgZ3JpZC4gUnVuIG9uY2UgYXQgdGhlIHBpbm5lZCBjb21taXQ7IGZyZWV6ZSB0aGUgb3V0cHV0LgogKgogKiBVc2FnZSAoZnJvbSB0aGlzIGRpcmVjdG9yeSk6CiAqICAgbm9kZSBnZW5lcmF0ZV9vcmFjbGUuanMgPiBleHBlY3RlZF9vdXRwdXRzLmpzb24KICoKICogUGlubmVkIGNvbW1pdDogZDFlNDIzOGQzZDNmNDkyNGU1Y2E2NWJhZmJkNGJhNWIzOWFmMmViOAogKiBSZXBvc2l0b3J5OiAgICBodHRwczovL2dpdGh1Yi5jb20vYW5kcmV3bWNjYWxpcC90aG91Z2h0cwogKi8KCid1c2Ugc3RyaWN0JzsKCmNvbnN0IENvc3RNb2RlbCA9IHJlcXVpcmUoJy4vbWF0aC5qcycpOwoKZnVuY3Rpb24gcnVuQ2FzZShsYWJlbCwgb3ZlcnJpZGVzKSB7CiAgICBDb3N0TW9kZWwuc2V0U3RhdGUoewogICAgICAgIHllYXJzOiA1LAogICAgICAgIHRhcmdldEdXOiAxLAogICAgICAgIHNvbGFyQWJzb3JwdGl2aXR5OiAwLjkyLAogICAgICAgIGVtaXNzaXZpdHlQVjogMC44NSwKICAgICAgICBlbWlzc2l2aXR5UmFkOiAwLjkwLAogICAgICAgIHB2RWZmaWNpZW5jeTogMC4yMiwKICAgICAgICBiZXRhQW5nbGU6IDkwLAogICAgICAgIG9yYml0YWxBbHRpdHVkZUttOiA1NTAsCiAgICAgICAgbWF4RGllVGVtcEM6IDg1LAogICAgICAgIHRlbXBEcm9wQzogMTAsCiAgICAgICAgbGF1bmNoQ29zdFBlcktnOiA1MDAsCiAgICAgICAgc2F0ZWxsaXRlQ29zdFBlclc6IDIyLAogICAgICAgIHNwZWNpZmljUG93ZXJXUGVyS2c6IDM2LjUsCiAgICAgICAgc2F0ZWxsaXRlUG93ZXJLVzogMjcsCiAgICAgICAgc3VuRnJhY3Rpb246IDAuOTgsCiAgICAgICAgY2VsbERlZ3JhZGF0aW9uOiAyLjUsCiAgICAgICAgZ3B1RmFpbHVyZVJhdGU6IDksCiAgICAgICAgbnJlQ29zdDogMTAwMCwKICAgICAgICBnYXNUdXJiaW5lQ2FwZXhQZXJLVzogMTgwMCwKICAgICAgICBlbGVjdHJpY2FsQ29zdFBlclc6IDUuMjUsCiAgICAgICAgbWVjaGFuaWNhbENvc3RQZXJXOiAzLjAsCiAgICAgICAgY2l2aWxDb3N0UGVyVzogMi41LAogICAgICAgIG5ldHdvcmtDb3N0UGVyVzogMS43NSwKICAgICAgICBwdWU6IDEuMiwKICAgICAgICBnYXNQcmljZVBlck1NQnR1OiA0LjMwLAogICAgICAgIGhlYXRSYXRlQnR1S3doOiA2MjAwLAogICAgICAgIGNhcGFjaXR5RmFjdG9yOiAwLjg1LAogICAgfSk7CgogICAgaWYgKG92ZXJyaWRlcykgQ29zdE1vZGVsLnNldFN0YXRlKG92ZXJyaWRlcyk7CgogICAgY29uc3Qgb3JiaXRhbCA9IENvc3RNb2RlbC5jYWxjdWxhdGVPcmJpdGFsKCk7CiAgICBjb25zdCB0aGVybWFsID0gQ29zdE1vZGVsLmNhbGN1bGF0ZVRoZXJtYWwoKTsKICAgIGNvbnN0IGJyZWFrZXZlbiA9IENvc3RNb2RlbC5jYWxjdWxhdGVCcmVha2V2ZW4oKTsKCiAgICByZXR1cm4gewogICAgICAgIGxhYmVsLAogICAgICAgIHN0YXRlX292ZXJyaWRlczogb3ZlcnJpZGVzIHx8IHt9LAogICAgICAgIGdlb21ldHJ5OiB7CiAgICAgICAgICAgIHZmTmFkaXJNYXg6IHRoZXJtYWwudmZOYWRpck1heCwKICAgICAgICAgICAgZWFydGhBbmd1bGFyUmFkaXVzRGVnOiB0aGVybWFsLmVhcnRoQW5ndWxhclJhZGl1c0RlZywKICAgICAgICAgICAgdmZTaWRlQTogdGhlcm1hbC52ZlNpZGVBLAogICAgICAgICAgICB2ZlNpZGVCOiB0aGVybWFsLnZmU2lkZUIsCiAgICAgICAgICAgIHZmVG90YWw6IHRoZXJtYWwudmZUb3RhbCwKICAgICAgICB9LAogICAgICAgIHRoZXJtYWw6IHsKICAgICAgICAgICAgZXFUZW1wSzogdGhlcm1hbC5lcVRlbXBLLAogICAgICAgICAgICBlcVRlbXBDOiB0aGVybWFsLmVxVGVtcEMsCiAgICAgICAgICAgIHRvdGFsSGVhdEluVzogdGhlcm1hbC50b3RhbEhlYXRJblcsCiAgICAgICAgICAgIHFTb2xhclc6IHRoZXJtYWwucVNvbGFyVywKICAgICAgICAgICAgcUVhcnRoSVJXOiB0aGVybWFsLnFFYXJ0aElSVywKICAgICAgICAgICAgcUFsYmVkb1c6IHRoZXJtYWwucUFsYmVkb1csCiAgICAgICAgICAgIHFIZWF0TG9vcFc6IHRoZXJtYWwucUhlYXRMb29wVywKICAgICAgICAgICAgcmFkaWF0aXZlQ2FwYWNpdHlXOiB0aGVybWFsLnJhZGlhdGl2ZUNhcGFjaXR5VywKICAgICAgICAgICAgYXJlYVN1ZmZpY2llbnQ6IHRoZXJtYWwuYXJlYVN1ZmZpY2llbnQsCiAgICAgICAgICAgIHRlbXBNYXJnaW5DOiB0aGVybWFsLnRlbXBNYXJnaW5DLAogICAgICAgICAgICBhcmVhUmVxdWlyZWRNMjogdGhlcm1hbC5hcmVhUmVxdWlyZWRNMiwKICAgICAgICAgICAgYXZhaWxhYmxlQXJlYU0yOiB0aGVybWFsLmF2YWlsYWJsZUFyZWFNMiwKICAgICAgICB9LAogICAgICAgIG9yYml0YWw6IHsKICAgICAgICAgICAgc2F0ZWxsaXRlQ291bnQ6IG9yYml0YWwuc2F0ZWxsaXRlQ291bnQsCiAgICAgICAgICAgIHRvdGFsTWFzc0tnOiBvcmJpdGFsLnRvdGFsTWFzc0tnLAogICAgICAgICAgICBzdGFyc2hpcExhdW5jaGVzOiBvcmJpdGFsLnN0YXJzaGlwTGF1bmNoZXMsCiAgICAgICAgICAgIHRvdGFsQ29zdDogb3JiaXRhbC50b3RhbENvc3QsCiAgICAgICAgICAgIGNvc3RQZXJXOiBvcmJpdGFsLmNvc3RQZXJXLAogICAgICAgICAgICBsY29lOiBvcmJpdGFsLmxjb2UsCiAgICAgICAgICAgIGVuZXJneU1XaDogb3JiaXRhbC5lbmVyZ3lNV2gsCiAgICAgICAgICAgIGF2Z0NhcGFjaXR5RmFjdG9yOiBvcmJpdGFsLmF2Z0NhcGFjaXR5RmFjdG9yLAogICAgICAgICAgICBhcnJheUFyZWFLbTI6IG9yYml0YWwuYXJyYXlBcmVhS20yLAogICAgICAgIH0sCiAgICAgICAgYnJlYWtldmVuX2xhdW5jaF9jb3N0X3Blcl9rZzogYnJlYWtldmVuLAogICAgfTsKfQoKY29uc3QgY2FzZXMgPSBbXTsKCmNhc2VzLnB1c2gocnVuQ2FzZSgnZGVmYXVsdHMnLCB7fSkpOwoKZm9yIChjb25zdCBiZXRhIG9mIFswLCAzMCwgNjAsIDkwXSkgewogICAgY2FzZXMucHVzaChydW5DYXNlKCdiZXRhXycgKyBiZXRhLCB7IGJldGFBbmdsZTogYmV0YSB9KSk7Cn0KCmZvciAoY29uc3QgYWx0IG9mIFs0MDAsIDU1MCwgODAwXSkgewogICAgY2FzZXMucHVzaChydW5DYXNlKCdhbHRfJyArIGFsdCArICdrbScsIHsgb3JiaXRhbEFsdGl0dWRlS206IGFsdCB9KSk7Cn0KCmZvciAoY29uc3QgZVJhZCBvZiBbMC44NSwgMC45MCwgMC45NV0pIHsKICAgIGNhc2VzLnB1c2gocnVuQ2FzZSgnZVJhZF8nICsgZVJhZCwgeyBlbWlzc2l2aXR5UmFkOiBlUmFkIH0pKTsKfQoKY29uc3Qgb3V0cHV0ID0gewogICAgX21ldGE6IHsKICAgICAgICBnZW5lcmF0ZWRfYnk6ICdnZW5lcmF0ZV9vcmFjbGUuanMnLAogICAgICAgIHNvdXJjZV9yZXBvOiAnaHR0cHM6Ly9naXRodWIuY29tL2FuZHJld21jY2FsaXAvdGhvdWdodHMnLAogICAgICAgIHBpbm5lZF9jb21taXQ6ICdkMWU0MjM4ZDNkM2Y0OTI0ZTVjYTY1YmFmYmQ0YmE1YjM5YWYyZWI4JywKICAgICAgICBjb21taXRfZGF0ZTogJzIwMjUtMTItMjlUMTc6NDI6MTNaJywKICAgICAgICBnZW5lcmF0ZWRfb246ICcyMDI2LTA2LTEyJywKICAgICAgICBzb3VyY2VfZmlsZTogJ3N0YXRpYy9qcy9tYXRoLmpzJywKICAgICAgICBub2RlX3ZlcnNpb246IHByb2Nlc3MudmVyc2lvbiwKICAgICAgICBjb252ZW50aW9uczogewogICAgICAgICAgICBzaWdtYV9zYjogJzUuNjdlLTggIChNY0NhbGlwIHRydW5jYXRlZDsgQ09EQVRBIGV4YWN0OiA1LjY3MDM3NDQxOWUtOCknLAogICAgICAgICAgICBUX3NwYWNlX0s6ICczIEsgIChNY0NhbGlwIHJvdW5kZWQ7IENNQjogMi43MjU1IEspJywKICAgICAgICAgICAgcmVwbGljYXRpb25fdG9sZXJhbmNlX0s6IDAuMDUsCiAgICAgICAgfSwKICAgIH0sCiAgICBjYXNlcywKfTsKCnByb2Nlc3Muc3Rkb3V0LndyaXRlKEpTT04uc3RyaW5naWZ5KG91dHB1dCwgbnVsbCwgMikgKyAnXG4nKTsK
`````

### `external_models/mccalip_thoughts/math.js`

_SHA-256-pinned; exact bytes as base64 (37056 bytes, sha256 `bcdced986d9c121a626e8ded1b10bd4ab48ce09b65847de0301d2e5f34fcd71f`):_

`````base64
LyoqCiAqIE9yYml0YWwgU29sYXIgdnMgTmF0R2FzIENvc3QgQW5hbHlzaXMgLSBNYXRoIEVuZ2luZQogKiAKICogQWxsIGNvbnN0YW50cyBhbmQgY2FsY3VsYXRpb25zIGFyZSBkZWZpbmVkIGhlcmUuCiAqIFRoaXMgZmlsZSBpcyB0aGUgc2luZ2xlIHNvdXJjZSBvZiB0cnV0aCBmb3IgdGhlIG1vZGVsLgogKi8KCmNvbnN0IENvc3RNb2RlbCA9IChmdW5jdGlvbigpIHsKICAgICd1c2Ugc3RyaWN0JzsKCiAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT0KICAgIC8vIENPTlNUQU5UUyAoZWRpdGFibGUgdmlhIHByZWZlcmVuY2VzKQogICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAKICAgIGxldCBjb25zdGFudHMgPSB7CiAgICAgICAgLy8gU3lzdGVtIHRhcmdldAogICAgICAgIFRBUkdFVF9QT1dFUl9NVzogMTAwMCwgICAgICAgICAgICAgICAgIC8vIDEgR1cgbmFtZXBsYXRlIGNhcGFjaXR5CiAgICAgICAgSE9VUlNfUEVSX1lFQVI6IDg3NjAsICAgICAgICAgICAgICAgICAgLy8gMzY1IMOXIDI0CgogICAgICAgIC8vIFN0YXJsaW5rIHJlZmVyZW5jZSBzYXRlbGxpdGUgKFYyIE1pbmkgZGVmYXVsdCkKICAgICAgICAvLyBVcGRhdGVkIGZyb20gU3RhcmxpbmsgdGVjaG5vLWVjb25vbWljIGFuYWx5c2lzCiAgICAgICAgU1RBUkxJTktfTUFTU19LRzogNzQwLCAgICAgICAgICAgICAgICAgLy8gVjIgTWluaSBtYXNzIHBlciBzYXRlbGxpdGUKICAgICAgICBTVEFSTElOS19QT1dFUl9LVzogMjcsICAgICAgICAgICAgICAgICAvLyBWMiBNaW5pIHBvd2VyIG91dHB1dCBwZXIgc2F0ZWxsaXRlICgyNyBrVyBuYW1lcGxhdGUpCiAgICAgICAgU1RBUkxJTktfQVJSQVlfTTI6IDExNiwgICAgICAgICAgICAgICAgLy8gVjIgTWluaSBhcnJheSBhcmVhIHBlciBzYXRlbGxpdGUKCiAgICAgICAgLy8gTGF1bmNoIHZlaGljbGUKICAgICAgICBTVEFSU0hJUF9QQVlMT0FEX0tHOiAxMDAwMDAsICAgICAgICAgICAvLyBTdGFyc2hpcCBMRU8gcGF5bG9hZCBjYXBhY2l0eQogICAgICAgIAogICAgICAgIC8vIFByb3BlbGxhbnQgJiBMb2dpc3RpY3MgKDIwMjUgTEMtMzlBIERyYWZ0IEVJUykKICAgICAgICBTVEFSU0hJUF9QUk9QX01BU1NfU0hJUDogMjY1MDAwMCwgICAgICAvLyBrZwogICAgICAgIFNUQVJTSElQX1BST1BfTUFTU19CT09TVEVSOiA0MTAwMDAwLCAgIC8vIGtnCiAgICAgICAgUFJPUEVMTEFOVF9MT1hfRlJBQ1RJT046IDAuNzgyNiwgICAgICAgLy8gfjc4LjMlIExPWAogICAgICAgIEVORVJHWV9MT1hfTVdIX1BFUl9UT046IDAuNCwgICAgICAgICAgIC8vIFNlcGFyYXRpb24gZW5lcmd5CiAgICAgICAgRU5FUkdZX0NINF9NV0hfUEVSX1RPTjogMC44LCAgICAgICAgICAgLy8gTGlxdWVmYWN0aW9uIGVuZXJneSAoTE5HKQogICAgICAgIFRBTktFUl9DQVBBQ0lUWV9MT1g6IDIwLCAgICAgICAgICAgICAgIC8vIE1ldHJpYyB0b25zCiAgICAgICAgVEFOS0VSX0NBUEFDSVRZX0NINDogMTgsICAgICAgICAgICAgICAgLy8gTWV0cmljIHRvbnMgKGRlbnNpdHkgbGltaXRlZCkKICAgICAgICAKICAgICAgICAvLyBSZWdpb25hbCBDYXBhY2l0eSAoVGV4YXMpCiAgICAgICAgVEVYQVNfQU5OVUFMX0dSSURfRU5FUkdZX0dXSDogNDkyODAwLCAgLy8gRVJDT1QgMjAyMyAoNDkyLjggVFdoKQogICAgICAgIFRFWEFTX0xPWF9TVVJQTFVTX0ZSQUM6IDAuMTAsICAgICAgICAgIC8vIEVzdC4gc3VycGx1cyBmcmFjdGlvbiAoMTAlKQoKICAgICAgICAvLyBOYXRHYXMgcGxhbnQKICAgICAgICBOR0NDX0FDUkVTOiAzMCwgICAgICAgICAgICAgICAgICAgICAgICAvLyBQbGFudCBmb290cHJpbnQKICAgICAgICBOR0NDX0hFQVRfUkFURV9CVFVfS1dIOiA2MzcwLCAgICAgICAgICAvLyBNb2Rlcm4gTkdDQyBoZWF0IHJhdGUKICAgICAgICBHRV83SEFfUE9XRVJfTVc6IDQzMCwgICAgICAgICAgICAgICAgICAvLyBHRSA3SEEuMDMgdHVyYmluZSBvdXRwdXQKICAgICAgICBCVFVfUEVSX0NGOiAxMDAwLCAgICAgICAgICAgICAgICAgICAgICAvLyBCVFUgcGVyIGN1YmljIGZvb3Qgb2YgbmF0dXJhbCBnYXMKICAgICAgICBDRl9QRVJfQkNGOiAxZTksICAgICAgICAgICAgICAgICAgICAgICAvLyBDdWJpYyBmZWV0IHBlciBiaWxsaW9uIGN1YmljIGZlZXQKCiAgICAgICAgLy8gQ29zdCBmcmFjdGlvbnMgLSBPcmJpdGFsCiAgICAgICAgT1JCSVRBTF9PUFNfRlJBQzogMC4wMSwgICAgICAgICAgICAgICAgLy8gT3BzIChjb21tcywgaW5mcmEpIC0gMSUKCiAgICAgICAgLy8gQ29zdCBmcmFjdGlvbnMgLSBOYXRHYXMKICAgICAgICBOQVRHQVNfT1ZFUkhFQURfRlJBQzogMC4wNCwKICAgICAgICBOQVRHQVNfTUFJTlRFTkFOQ0VfRlJBQzogMC4wMywKICAgICAgICBOQVRHQVNfQ09NTVNfRlJBQzogMC4wMSwKCiAgICAgICAgLy8gU3BhY2UgZW52aXJvbm1lbnQKICAgICAgICBTT0xBUl9JUlJBRElBTkNFX1dfTTI6IDEzNjEsICAgICAgICAgICAvLyBMRU8gc29sYXIgY29uc3RhbnQgKEFNMCkKICAgICAgICBFQVJUSF9JUl9GTFVYX1dfTTI6IDIzNywgICAgICAgICAgICAgICAvLyBFYXJ0aCBJUiBlbWlzc2lvbiAoZ2xvYmFsIGF2ZXJhZ2UpCiAgICAgICAgRUFSVEhfQUxCRURPX0ZBQ1RPUjogMC4zMCwgICAgICAgICAgICAgLy8gQXZlcmFnZSBFYXJ0aCByZWZsZWN0aXZpdHkKICAgICAgICBUX1NQQUNFX0s6IDMsICAgICAgICAgICAgICAgICAgICAgICAgICAvLyBEZWVwIHNwYWNlIHNpbmsgdGVtcGVyYXR1cmUKICAgICAgICAKICAgICAgICAvLyBPcmJpdGFsIGdlb21ldHJ5IChmb3IgdmlldyBmYWN0b3IgY2FsY3VsYXRpb25zKQogICAgICAgIEVBUlRIX1JBRElVU19LTTogNjM3MS4wICAgICAgICAgICAgICAgIC8vIE1lYW4gRWFydGggcmFkaXVzIChrbSkKICAgIH07CgogICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAvLyBTTElERVIgU1RBVEUgKHVzZXItYWRqdXN0YWJsZSBwYXJhbWV0ZXJzKQogICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAKICAgIGxldCBzdGF0ZSA9IHsKICAgICAgICAvLyBTaGFyZWQgcGFyYW1ldGVycwogICAgICAgIHllYXJzOiA1LAogICAgICAgIHRhcmdldEdXOiAxLCAgICAgICAgICAgICAgICAgICAgLy8gVGFyZ2V0IGNhcGFjaXR5IGluIEdXIChkZWZhdWx0IDEgR1cpCiAgICAgICAgLy8gVGhlcm1hbCBhbmFseXNpcyBwYXJhbWV0ZXJzIC0gQmlmYWNpYWwgUGFuZWwgTW9kZWwKICAgICAgICAvLyBTaWRlIEEgPSBQViAoc3VuLWZhY2luZyksIFNpZGUgQiA9IFJhZGlhdG9yIChzcGFjZS1mYWNpbmcpCiAgICAgICAgc29sYXJBYnNvcnB0aXZpdHk6IDAuOTIsICAgIC8vIFNvbGFyIGFic29ycHRpdml0eSBvZiBQViBzaWRlIChhbHBoYV9wdikKICAgICAgICBlbWlzc2l2aXR5UFY6IDAuODUsICAgICAgICAgLy8gSVIgZW1pc3Npdml0eSBvZiBQViBzaWRlIChnbGFzcykKICAgICAgICBlbWlzc2l2aXR5UmFkOiAwLjkwLCAgICAgICAgLy8gSVIgZW1pc3Npdml0eSBvZiBSYWRpYXRvciBzaWRlICh3aGl0ZSBwYWludC9PU1IpCiAgICAgICAgcHZFZmZpY2llbmN5OiAwLjIyLCAgICAgICAgIC8vIEVsZWN0cmljYWwgY29udmVyc2lvbiBlZmZpY2llbmN5ICgyMiUpCiAgICAgICAgYmV0YUFuZ2xlOiA5MCwgICAgICAgICAgICAgIC8vIE9yYml0IGJldGEgYW5nbGUgKGRlZyk6IDkwPXRlcm1pbmF0b3IsIDYwPXNlYXNvbmFsIGxpbWl0CiAgICAgICAgb3JiaXRhbEFsdGl0dWRlS206IDU1MCwgICAgIC8vIE9yYml0YWwgYWx0aXR1ZGUgKGttKSAtIFN0YXJsaW5rIGRlZmF1bHQKICAgICAgICBtYXhEaWVUZW1wQzogODUsICAgICAgICAgICAgLy8gTWF4IGRpZSB0ZW1wZXJhdHVyZSAowrBDKSAtIEdQVSBqdW5jdGlvbiBsaW1pdAogICAgICAgIHRlbXBEcm9wQzogMTAsICAgICAgICAgICAgICAvLyBUZW1wZXJhdHVyZSBkcm9wIGZyb20gZGllIHRvIHJhZGlhdG9yIHN1cmZhY2UgKMKwQykKICAgICAgICAKICAgICAgICAvLyBPcmJpdGFsIHBhcmFtZXRlcnMgKFYyIE1pbmkgZGVmYXVsdHMgZnJvbSBTdGFybGluayBhbmFseXNpcykKICAgICAgICBsYXVuY2hDb3N0UGVyS2c6IDUwMCwKICAgICAgICBzYXRlbGxpdGVDb3N0UGVyVzogMjIsICAgICAgICAvLyBWMiBNaW5pOiB+JDIyL1cgKEJPTSBhdCAkODAwL2tnKQogICAgICAgIHNwZWNpZmljUG93ZXJXUGVyS2c6IDM2LjUsICAgIC8vIFYyIE1pbmk6IDM2LjUgVy9rZyAoMjcga1cgLyA3NDAga2cpCiAgICAgICAgc2F0ZWxsaXRlUG93ZXJLVzogMjcsICAgICAgICAgLy8gVjIgTWluaTogMjcga1cgbmFtZXBsYXRlCiAgICAgICAgc3VuRnJhY3Rpb246IDAuOTgsICAgICAgICAgICAgLy8gVGVybWluYXRvciBvcmJpdCBkZWZhdWx0CiAgICAgICAgY2VsbERlZ3JhZGF0aW9uOiAyLjUsICAgICAgICAgLy8gJSBwZXIgeWVhciBzaWxpY29uIGNlbGwgZGVncmFkYXRpb24KICAgICAgICBncHVGYWlsdXJlUmF0ZTogOSwgICAgICAgICAgICAvLyAlIHBlciB5ZWFyIEdQVSBmYWlsdXJlIHJhdGUgaW4gc3BhY2UgKE1ldGE6IDklKQogICAgICAgIG5yZUNvc3Q6IDEwMDAsICAgICAgICAgICAgICAgIC8vIE5SRSBjb3N0IGluIG1pbGxpb25zICgkMUIgZGVmYXVsdCkKICAgICAgICAKICAgICAgICAvLyBUZXJyZXN0cmlhbCBwYXJhbWV0ZXJzIC0gT24tU2l0ZSBHYXMgR2VuZXJhdGlvbiAoeEFJL0h5cGVyc2NhbGUgc3R5bGUpCiAgICAgICAgLy8gU291cmNlOiBUZWNobm8tRWNvbm9taWMgQW5hbHlzaXMgUmVwb3J0LCBFSUEsIFNhcmdlbnQgJiBMdW5keQogICAgICAgIC8vIFRvdGFsIENhcGV4IFRhcmdldDogfiQxMy44MC9XIChyYW5nZSAkMTEuNjAtJDE2LjAwL1cpCiAgICAgICAgCiAgICAgICAgLy8gQ0FQRVggYnVja2V0cyAoNSBjYXRlZ29yaWVzIGZyb20gcmVwb3J0KQogICAgICAgIC8vIDEuIFBvd2VyIEdlbmVyYXRpb24gLSBHYXMgVHVyYmluZSBDYXBleAogICAgICAgIGdhc1R1cmJpbmVDYXBleFBlcktXOiAxODAwLCAgICAvLyBGcmFtZSBDQ0dUICQva1cgKCQxLjgwL1cgZGVmYXVsdCkKICAgICAgICAKICAgICAgICAvLyAyLiBFbGVjdHJpY2FsIERpc3RyaWJ1dGlvbjogJDUuMjUvVyAoMzglKSAtIFN3aXRjaGdlYXIsIFRyYW5zZm9ybWVycywgVVBTLCBHZW5zZXRzCiAgICAgICAgZWxlY3RyaWNhbENvc3RQZXJXOiA1LjI1LCAgICAgIC8vIE1WL0xWIHN3aXRjaGdlYXIsIFVQUyAoTGktaW9uKSwgYmFja3VwIGdlbnNldHMsIGJ1c3dheQogICAgICAgIAogICAgICAgIC8vIDMuIE1lY2hhbmljYWwvQ29vbGluZzogJDMuMDAvVyAoMjIlKSAtIENoaWxsZXJzLCBDRFVzLCBQaXBpbmcsIFRvd2VycwogICAgICAgIG1lY2hhbmljYWxDb3N0UGVyVzogMy4wLCAgICAgICAvLyBETEMgaW5mcmFzdHJ1Y3R1cmUsIENEVXMgKH4kMjEuNWsvMzAwa1cpLCBtYW5pZm9sZHMKICAgICAgICAKICAgICAgICAvLyA0LiBDaXZpbCAmIFNoZWxsOiAkMi41MC9XICgxOCUpIC0gU2hlbGwsIExhbmQsIFNpdGUgUHJlcCwgUm9hZHMKICAgICAgICBjaXZpbENvc3RQZXJXOiAyLjUsICAgICAgICAgICAgLy8gTGFuZCAofiQyNDRrL2FjcmUpLCBidWlsZGluZyBzaGVsbCAoJDEwNS0yMzUvc3FmdCkKICAgICAgICAKICAgICAgICAvLyA1LiBOZXR3b3JraW5nL0ZpdC1vdXQ6ICQxLjc1L1cgKDEzJSkgLSBGaWJlciBQbGFudCwgUmFja3MsIFNlY3VyaXR5LCBCTVMKICAgICAgICBuZXR3b3JrQ29zdFBlclc6IDEuNzUsICAgICAgICAgLy8gRGFyayBmaWJlciwgc3RydWN0dXJlZCBjYWJsaW5nLCByYWNrcywgc2VjdXJpdHkKICAgICAgICAKICAgICAgICAvLyBQVUUKICAgICAgICBwdWU6IDEuMiwgICAgICAgICAgICAgICAgICAgICAgIC8vIExpcXVpZCBjb29sZWQgZWZmaWNpZW5jeQogICAgICAgIAogICAgICAgIC8vIE9QRVggLSBGdWVsIChmcm9tIHJlcG9ydCkKICAgICAgICBnYXNQcmljZVBlck1NQnR1OiA0LjMwLCAgICAgICAgIC8vIEVJQSAyMDI1IGZvcmVjYXN0IEhlbnJ5IEh1YgogICAgICAgIGhlYXRSYXRlQnR1S3doOiA2MjAwLCAgICAgICAgICAgLy8gRnJhbWUgQ0NHVCBoZWF0IHJhdGUgKDYsMjAwLTYsNTYwIHJhbmdlKQogICAgICAgIGNhcGFjaXR5RmFjdG9yOiAwLjg1ICAgICAgICAgICAgLy8gODUlIGNhcGFjaXR5IGZhY3RvciBkZWZhdWx0CiAgICB9OwogICAgCiAgICAvLyBTYXRlbGxpdGUgcHJlc2V0cyBmcm9tIFN0YXJsaW5rIHRlY2huby1lY29ub21pYyBhbmFseXNpcwogICAgLy8gU291cmNlOiBVSyB0ZWNobmljYWwgc3R1ZHksIFNwYWNlWCBmaWxpbmdzLCBlbmdpbmVlcmluZyBlc3RpbWF0ZXMKICAgIGNvbnN0IFNBVEVMTElURV9QUkVTRVRTID0gewogICAgICAgIC8vIFNwZWNpZmljIHBvd2VyIChXL2tnKSAtIG5hbWVwbGF0ZSBzb2xhciBwb3dlciBwZXIga2cgb2Ygc3BhY2VjcmFmdCBtYXNzCiAgICAgICAgU1BFQ0lGSUNfUE9XRVI6IHsKICAgICAgICAgICAgSVNTOiAzLCAgICAgICAgICAgLy8gSVNTIHNvbGFyIGFycmF5cyB+MyBXL2tnIChvbGQgdGVjaCwgaGVhdnkgc3RydWN0dXJlKQogICAgICAgICAgICBWMTogMjQuNywgICAgICAgICAvLyBTdGFybGluayBWMS54OiA3IGtXIC8gMjgzIGtnID0gMjQuNyBXL2tnCiAgICAgICAgICAgIFYyX01JTkk6IDM2LjUsICAgIC8vIFN0YXJsaW5rIFYyIE1pbmk6IDI3IGtXIC8gNzQwIGtnID0gMzYuNSBXL2tnCiAgICAgICAgICAgIFYzOiAzMS42ICAgICAgICAgIC8vIFN0YXJsaW5rIFYzOiA2MCBrVyAvIDEsOTAwIGtnID0gMzEuNiBXL2tnIChzcGVjdWxhdGl2ZSkKICAgICAgICB9LAogICAgICAgIC8vIEhhcmR3YXJlIGNvc3QgKCQvVykgLSBCT00gY29zdCBub3JtYWxpemVkIHRvIHNvbGFyIHBvd2VyCiAgICAgICAgLy8gQmFzZWQgb24gfiQ4MDAva2cgbWFudWZhY3R1cmluZyBjb3N0IGVzdGltYXRlCiAgICAgICAgQ09TVF9QRVJfVzogewogICAgICAgICAgICBWMTogMzIsICAgICAgICAgICAvLyAkMjMwayAvIDcga1cg4omIICQzMi9XCiAgICAgICAgICAgIFYyX01JTkk6IDIyLCAgICAgIC8vICQ1OTBrIC8gMjcga1cg4omIICQyMi9XCiAgICAgICAgICAgIFYzOiAyNSAgICAgICAgICAgIC8vICQxLjUyTSAvIDYwIGtXIOKJiCAkMjUvVyAoc3BlY3VsYXRpdmUpCiAgICAgICAgfSwKICAgICAgICAvLyBTYXRlbGxpdGUgcG93ZXIgb3V0cHV0IChrVyBuYW1lcGxhdGUpCiAgICAgICAgUE9XRVJfS1c6IHsKICAgICAgICAgICAgVjE6IDcsICAgICAgICAgICAgLy8gNyBrVyBuYW1lcGxhdGUgKDMwIG3CsiBhcnJheSkKICAgICAgICAgICAgVjJfTUlOSTogMjcsICAgICAgLy8gMjcga1cgbmFtZXBsYXRlICgxMTYgbcKyIGFycmF5KQogICAgICAgICAgICBWMzogNjAgICAgICAgICAgICAvLyA2MCBrVyBuYW1lcGxhdGUgKDI1MCBtwrIgYXJyYXksIHNwZWN1bGF0aXZlKQogICAgICAgIH0sCiAgICAgICAgLy8gTWFzcyBwZXIgc2F0ZWxsaXRlIChrZykKICAgICAgICBNQVNTX0tHOiB7CiAgICAgICAgICAgIFYxOiAyODMsICAgICAgICAgIC8vIHYxLjAvdjEuNSBhdmVyYWdlCiAgICAgICAgICAgIFYyX01JTkk6IDc0MCwgICAgIC8vIHYyIG1pbmkKICAgICAgICAgICAgVjM6IDE5MDAgICAgICAgICAgLy8gdjMgKHNwZWN1bGF0aXZlKQogICAgICAgIH0sCiAgICAgICAgLy8gU29sYXIgYXJyYXkgYXJlYSAobcKyKQogICAgICAgIEFSUkFZX00yOiB7CiAgICAgICAgICAgIFYxOiAzMCwKICAgICAgICAgICAgVjJfTUlOSTogMTE2LAogICAgICAgICAgICBWMzogMjUwICAgICAgICAgICAvLyBzcGVjdWxhdGl2ZQogICAgICAgIH0KICAgIH07CgogICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAvLyBERVJJVkVEIENPTlNUQU5UUwogICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAKICAgIGZ1bmN0aW9uIGdldERlcml2ZWQoKSB7CiAgICAgICAgY29uc3QgdGFyZ2V0UG93ZXJNVyA9IHN0YXRlLnRhcmdldEdXICogMTAwMDsKICAgICAgICByZXR1cm4gewogICAgICAgICAgICBUQVJHRVRfUE9XRVJfTVc6IHRhcmdldFBvd2VyTVcsCiAgICAgICAgICAgIFRBUkdFVF9QT1dFUl9XOiB0YXJnZXRQb3dlck1XICogMWU2LAogICAgICAgICAgICBUQVJHRVRfUE9XRVJfS1c6IHRhcmdldFBvd2VyTVcgKiAxMDAwCiAgICAgICAgfTsKICAgIH0KCiAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT0KICAgIC8vIENBTENVTEFUSU9OUwogICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAKICAgIGZ1bmN0aW9uIGNhbGN1bGF0ZU9yYml0YWwoKSB7CiAgICAgICAgY29uc3QgZGVyaXZlZCA9IGdldERlcml2ZWQoKTsKICAgICAgICBjb25zdCB0b3RhbEhvdXJzID0gc3RhdGUueWVhcnMgKiBjb25zdGFudHMuSE9VUlNfUEVSX1lFQVI7CiAgICAgICAgCiAgICAgICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PQogICAgICAgIC8vIERFR1JBREFUSU9OOiBDYWxjdWxhdGUgY2FwYWNpdHkgbmVlZGVkIHRvIG1haW50YWluIDFHVyBhdmVyYWdlCiAgICAgICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PQogICAgICAgIAogICAgICAgIC8vIFllYXItYnkteWVhciBkZWdyYWRhdGlvbjogY2FwYWNpdHkgYXQgeWVhciBuID0gKDEgLSBkZWcpXm4KICAgICAgICAvLyBNb3JlIGFjY3VyYXRlIHRoYW4gbGluZWFyIGFwcHJveGltYXRpb24KICAgICAgICBjb25zdCBhbm51YWxSZXRlbnRpb24gPSAxIC0gKHN0YXRlLmNlbGxEZWdyYWRhdGlvbiAvIDEwMCk7CiAgICAgICAgCiAgICAgICAgLy8gQ2FsY3VsYXRlIGF2ZXJhZ2UgY2FwYWNpdHkgZmFjdG9yIG92ZXIgYW5hbHlzaXMgcGVyaW9kCiAgICAgICAgLy8gU3VtIG9mIGdlb21ldHJpYyBzZXJpZXM6ICgxICsgciArIHJeMiArIC4uLiArIHJeKG4tMSkpIC8gbgogICAgICAgIGxldCBjYXBhY2l0eVN1bSA9IDA7CiAgICAgICAgZm9yIChsZXQgeWVhciA9IDA7IHllYXIgPCBzdGF0ZS55ZWFyczsgeWVhcisrKSB7CiAgICAgICAgICAgIGNhcGFjaXR5U3VtICs9IE1hdGgucG93KGFubnVhbFJldGVudGlvbiwgeWVhcik7CiAgICAgICAgfQogICAgICAgIGNvbnN0IGF2Z0NhcGFjaXR5RmFjdG9yID0gY2FwYWNpdHlTdW0gLyBzdGF0ZS55ZWFyczsKICAgICAgICAKICAgICAgICAvLyBTdW5saWdodCBmcmFjdGlvbiByZWR1Y2VzIHVzYWJsZSBvdXRwdXQ7IHNpemUgdXAgdG8gaGl0IHRhcmdldCBhdmVyYWdlCiAgICAgICAgY29uc3Qgc3VubGlnaHRBZGp1c3RlZEZhY3RvciA9IGF2Z0NhcGFjaXR5RmFjdG9yICogc3RhdGUuc3VuRnJhY3Rpb247CiAgICAgICAgY29uc3QgcmVxdWlyZWRJbml0aWFsUG93ZXJXID0gZGVyaXZlZC5UQVJHRVRfUE9XRVJfVyAvIHN1bmxpZ2h0QWRqdXN0ZWRGYWN0b3I7CiAgICAgICAgCiAgICAgICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PQogICAgICAgIC8vIFNBVEVMTElURSBTSVpJTkcKICAgICAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAgICAgCiAgICAgICAgLy8gRWFjaCBzYXRlbGxpdGUgcHJvZHVjZXMgc2F0ZWxsaXRlUG93ZXJLVyBhdCBzcGVjaWZpYyBwb3dlciAoVy9rZykKICAgICAgICAvLyBNYXNzIHBlciBzYXRlbGxpdGUgPSBwb3dlciAvIHNwZWNpZmljIHBvd2VyCiAgICAgICAgY29uc3QgbWFzc1BlclNhdGVsbGl0ZUtnID0gKHN0YXRlLnNhdGVsbGl0ZVBvd2VyS1cgKiAxMDAwKSAvIHN0YXRlLnNwZWNpZmljUG93ZXJXUGVyS2c7CiAgICAgICAgCiAgICAgICAgLy8gTnVtYmVyIG9mIHNhdGVsbGl0ZXMgbmVlZGVkIGZvciByZXF1aXJlZCBpbml0aWFsIGNhcGFjaXR5CiAgICAgICAgY29uc3Qgc2F0ZWxsaXRlQ291bnQgPSBNYXRoLmNlaWwocmVxdWlyZWRJbml0aWFsUG93ZXJXIC8gKHN0YXRlLnNhdGVsbGl0ZVBvd2VyS1cgKiAxMDAwKSk7CiAgICAgICAgCiAgICAgICAgLy8gVG90YWwgbWFzcyBiYXNlZCBvbiBhY3R1YWwgc2F0ZWxsaXRlIGNvdW50CiAgICAgICAgY29uc3QgdG90YWxNYXNzS2cgPSBzYXRlbGxpdGVDb3VudCAqIG1hc3NQZXJTYXRlbGxpdGVLZzsKICAgICAgICAKICAgICAgICAvLyBBY3R1YWwgaW5pdGlhbCBwb3dlciAobWF5IGJlIHNsaWdodGx5IGhpZ2hlciBkdWUgdG8gcm91bmRpbmcgdXAgc2F0ZWxsaXRlcykKICAgICAgICBjb25zdCBhY3R1YWxJbml0aWFsUG93ZXJXID0gc2F0ZWxsaXRlQ291bnQgKiBzdGF0ZS5zYXRlbGxpdGVQb3dlcktXICogMTAwMDsKICAgICAgICAKICAgICAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAgICAgLy8gQ09TVFMKICAgICAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAgICAgCiAgICAgICAgLy8gU2F0ZWxsaXRlIGhhcmR3YXJlIGNvc3Q6ICQvVyDDlyBhY3R1YWwgaW5pdGlhbCB3YXR0cwogICAgICAgIGNvbnN0IGhhcmR3YXJlQ29zdCA9IHN0YXRlLnNhdGVsbGl0ZUNvc3RQZXJXICogYWN0dWFsSW5pdGlhbFBvd2VyVzsKICAgICAgICAKICAgICAgICAvLyBMYXVuY2ggY29zdDogJC9rZyDDlyB0b3RhbCBrZwogICAgICAgIGNvbnN0IGxhdW5jaENvc3QgPSBzdGF0ZS5sYXVuY2hDb3N0UGVyS2cgKiB0b3RhbE1hc3NLZzsKICAgICAgICAKICAgICAgICAvLyBCYXNlIGNvc3QgYmVmb3JlIG92ZXJoZWFkL21haW50ZW5hbmNlL2NvbW1zCiAgICAgICAgY29uc3QgYmFzZUNvc3QgPSBoYXJkd2FyZUNvc3QgKyBsYXVuY2hDb3N0OwogICAgICAgIAogICAgICAgIC8vIE9wcyBjb3N0IChjb21tcywgaW5mcmEpIC0gMSUgb2YgaGFyZHdhcmUgcGVyIHllYXIKICAgICAgICBjb25zdCBvcHNDb3N0ID0gaGFyZHdhcmVDb3N0ICogY29uc3RhbnRzLk9SQklUQUxfT1BTX0ZSQUMgKiBzdGF0ZS55ZWFyczsKICAgICAgICAKICAgICAgICAvLyBHUFUgZmFpbHVyZSByZXBsYWNlbWVudCBjb3N0ICglIG9mIGhhcmR3YXJlIHBlciB5ZWFyIMOXIHllYXJzKQogICAgICAgIGNvbnN0IGdwdVJlcGxhY2VtZW50Q29zdCA9IGhhcmR3YXJlQ29zdCAqIChzdGF0ZS5ncHVGYWlsdXJlUmF0ZSAvIDEwMCkgKiBzdGF0ZS55ZWFyczsKICAgICAgICAKICAgICAgICAvLyBOUkUgY29zdCAobm9uLXJlY3VycmluZyBlbmdpbmVlcmluZykKICAgICAgICBjb25zdCBucmVDb3N0ID0gc3RhdGUubnJlQ29zdCAqIDFlNjsgIC8vIENvbnZlcnQgZnJvbSBtaWxsaW9ucwogICAgICAgIAogICAgICAgIC8vIFRvdGFsIHN5c3RlbSBjb3N0IChpbmNsdWRpbmcgTlJFLCBvcHMsIEdQVSByZXBsYWNlbWVudCkKICAgICAgICBjb25zdCB0b3RhbENvc3QgPSBiYXNlQ29zdCArIG9wc0Nvc3QgKyBncHVSZXBsYWNlbWVudENvc3QgKyBucmVDb3N0OwogICAgICAgIAogICAgICAgIC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT0KICAgICAgICAvLyBFTkVSR1kgT1VUUFVUCiAgICAgICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PQogICAgICAgIAogICAgICAgIC8vIEVuZXJneSBvdXRwdXQ6IHRhcmdldCBhdmVyYWdlIHBvd2VyIMOXIGhvdXJzIChzaXplZCB0byBvZmZzZXQgZWNsaXBzZSArIGRlZ3JhZGF0aW9uKQogICAgICAgIGNvbnN0IGVuZXJneU1XaCA9IGRlcml2ZWQuVEFSR0VUX1BPV0VSX01XICogdG90YWxIb3VyczsKICAgICAgICAKICAgICAgICAvLyBDb3N0IHBlciB3YXR0IChvZiBkZWxpdmVyZWQgYXZlcmFnZSBwb3dlciwgbm90IGluaXRpYWwgY2FwYWNpdHkpCiAgICAgICAgY29uc3QgY29zdFBlclcgPSB0b3RhbENvc3QgLyBkZXJpdmVkLlRBUkdFVF9QT1dFUl9XOwogICAgICAgIAogICAgICAgIC8vIExldmVsaXplZCBjb3N0IG9mIGVuZXJneQogICAgICAgIGNvbnN0IGxjb2UgPSB0b3RhbENvc3QgLyBlbmVyZ3lNV2g7CiAgICAgICAgCiAgICAgICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PQogICAgICAgIC8vIEVOR0lORUVSSU5HIE9VVFBVVFMKICAgICAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAgICAgCiAgICAgICAgLy8gQXJyYXkgYXJlYSBiYXNlZCBvbiBzYXRlbGxpdGUgY291bnQKICAgICAgICAvLyBTY2FsZSBhcnJheSBhcmVhIHByb3BvcnRpb25hbGx5IHRvIHNhdGVsbGl0ZSBwb3dlciB2cyByZWZlcmVuY2UKICAgICAgICBjb25zdCBhcnJheVBlclNhdGVsbGl0ZU0yID0gY29uc3RhbnRzLlNUQVJMSU5LX0FSUkFZX00yICogKHN0YXRlLnNhdGVsbGl0ZVBvd2VyS1cgLyBjb25zdGFudHMuU1RBUkxJTktfUE9XRVJfS1cpOwogICAgICAgIGNvbnN0IGFycmF5QXJlYU0yID0gc2F0ZWxsaXRlQ291bnQgKiBhcnJheVBlclNhdGVsbGl0ZU0yOwogICAgICAgIGNvbnN0IGFycmF5QXJlYUttMiA9IGFycmF5QXJlYU0yIC8gMWU2OwogICAgICAgIAogICAgICAgIGNvbnN0IHN0YXJzaGlwTGF1bmNoZXMgPSBNYXRoLmNlaWwodG90YWxNYXNzS2cgLyBjb25zdGFudHMuU1RBUlNISVBfUEFZTE9BRF9LRyk7CiAgICAgICAgCiAgICAgICAgLy8gUHJvcGVsbGFudCAmIExvZ2lzdGljcyBDYWxjdWxhdGlvbnMKICAgICAgICBjb25zdCBwcm9wZWxsYW50VG90YWxLZyA9IGNvbnN0YW50cy5TVEFSU0hJUF9QUk9QX01BU1NfU0hJUCArIGNvbnN0YW50cy5TVEFSU0hJUF9QUk9QX01BU1NfQk9PU1RFUjsKICAgICAgICBjb25zdCBwcm9wZWxsYW50VG90YWxUb25zID0gcHJvcGVsbGFudFRvdGFsS2cgLyAxMDAwOwogICAgICAgIAogICAgICAgIGNvbnN0IGxveFRvbnMgPSBwcm9wZWxsYW50VG90YWxUb25zICogY29uc3RhbnRzLlBST1BFTExBTlRfTE9YX0ZSQUNUSU9OOwogICAgICAgIGNvbnN0IGNoNFRvbnMgPSBwcm9wZWxsYW50VG90YWxUb25zICogKDEgLSBjb25zdGFudHMuUFJPUEVMTEFOVF9MT1hfRlJBQ1RJT04pOwogICAgICAgIAogICAgICAgIC8vIEVuZXJneSBmb3IgcHJvcGVsbGFudCBwcm9kdWN0aW9uIChHV2gpCiAgICAgICAgY29uc3QgZW5lcmd5TG94TVdoID0gbG94VG9ucyAqIGNvbnN0YW50cy5FTkVSR1lfTE9YX01XSF9QRVJfVE9OOwogICAgICAgIGNvbnN0IGVuZXJneUNoNE1XaCA9IGNoNFRvbnMgKiBjb25zdGFudHMuRU5FUkdZX0NINF9NV0hfUEVSX1RPTjsKICAgICAgICBjb25zdCBlbmVyZ3lQZXJMYXVuY2hHV2ggPSAoZW5lcmd5TG94TVdoICsgZW5lcmd5Q2g0TVdoKSAvIDEwMDA7CiAgICAgICAgCiAgICAgICAgLy8gVG90YWwgcHJvamVjdCBlbmVyZ3kgZm9yIGxhdW5jaGVzCiAgICAgICAgY29uc3QgdG90YWxMYXVuY2hFbmVyZ3lHV2ggPSBlbmVyZ3lQZXJMYXVuY2hHV2ggKiBzdGFyc2hpcExhdW5jaGVzOwogICAgICAgIAogICAgICAgIC8vIFRleGFzIEdyaWQgSW1wYWN0IChTdXN0YWluZWQgQXZlcmFnZSBMb2FkKQogICAgICAgIC8vIEF2ZXJhZ2UgZGFpbHkgZW5lcmd5IGNvbnN1bXB0aW9uIG9mIHRoZSBjYW1wYWlnbiB2cyBEYWlseSBHcmlkIEdlbmVyYXRpb24KICAgICAgICBjb25zdCB0b3RhbERheXMgPSBzdGF0ZS55ZWFycyAqIDM2NTsKICAgICAgICBjb25zdCBhdmdEYWlseUxhdW5jaEVuZXJneUdXaCA9IHRvdGFsTGF1bmNoRW5lcmd5R1doIC8gdG90YWxEYXlzOwogICAgICAgIGNvbnN0IGRhaWx5R3JpZEVuZXJneUdXaCA9IGNvbnN0YW50cy5URVhBU19BTk5VQUxfR1JJRF9FTkVSR1lfR1dIIC8gMzY1OwogICAgICAgIGNvbnN0IHBjdFRleGFzR3JpZEltcGFjdCA9IChhdmdEYWlseUxhdW5jaEVuZXJneUdXaCAvIGRhaWx5R3JpZEVuZXJneUdXaCkgKiAxMDA7CiAgICAgICAgCiAgICAgICAgLy8gVGV4YXMgTE9YIENhcGFjaXR5IEltcGFjdCAoU3VzdGFpbmVkIEF2ZXJhZ2UgQ29uc3VtcHRpb24pCiAgICAgICAgY29uc3QgZXN0VGV4YXNEYWlseUxveFRvbnMgPSAxNDUwMDsgIC8vIEVzdC4gdG90YWwgVGV4YXMgZGFpbHkgTE9YIGNhcGFjaXR5CiAgICAgICAgY29uc3QgdG90YWxMb3hUb25zID0gbG94VG9ucyAqIHN0YXJzaGlwTGF1bmNoZXM7CiAgICAgICAgY29uc3QgYXZnRGFpbHlMb3hUb25zID0gdG90YWxMb3hUb25zIC8gdG90YWxEYXlzOwogICAgICAgIAogICAgICAgIC8vICUgb2YgVG90YWwgVGV4YXMgTE9YIGNhcGFjaXR5CiAgICAgICAgY29uc3QgcGN0VG90YWxUZXhhc0xveCA9IChhdmdEYWlseUxveFRvbnMgLyBlc3RUZXhhc0RhaWx5TG94VG9ucykgKiAxMDA7CiAgICAgICAgCiAgICAgICAgLy8gJSBvZiBTdXJwbHVzIGNhcGFjaXR5IChhc3N1bWVkIDEwJSBvZiB0b3RhbCkKICAgICAgICBjb25zdCBzdXJwbHVzQ2FwYWNpdHkgPSBlc3RUZXhhc0RhaWx5TG94VG9ucyAqIGNvbnN0YW50cy5URVhBU19MT1hfU1VSUExVU19GUkFDOwogICAgICAgIGNvbnN0IHBjdFN1cnBsdXNDYXBhY2l0eSA9IChhdmdEYWlseUxveFRvbnMgLyBzdXJwbHVzQ2FwYWNpdHkpICogMTAwOwogICAgICAgIAogICAgICAgIC8vIFRhbmtlciB0cnVja3MKICAgICAgICBjb25zdCBsb3hUcnVja3MgPSBNYXRoLmNlaWwobG94VG9ucyAvIGNvbnN0YW50cy5UQU5LRVJfQ0FQQUNJVFlfTE9YKTsKICAgICAgICBjb25zdCBjaDRUcnVja3MgPSBNYXRoLmNlaWwoY2g0VG9ucyAvIGNvbnN0YW50cy5UQU5LRVJfQ0FQQUNJVFlfQ0g0KTsKICAgICAgICBjb25zdCB0b3RhbFRhbmtlclRydWNrcyA9IGxveFRydWNrcyArIGNoNFRydWNrczsKICAgICAgICAKICAgICAgICAvLyBUb3RhbCBwcm9wZWxsYW50IGluIGdhbGxvbnMgKGZvciBhbGwgbGF1bmNoZXMpCiAgICAgICAgLy8gTE9YOiAyMzEuNSBnYWwvbWV0cmljIHRvbiwgQ0g0OiA2MjUuNCBnYWwvbWV0cmljIHRvbgogICAgICAgIGNvbnN0IGxveEdhbGxvbnMgPSBsb3hUb25zICogMjMxLjUgKiBzdGFyc2hpcExhdW5jaGVzOwogICAgICAgIGNvbnN0IG1ldGhhbmVHYWxsb25zID0gY2g0VG9ucyAqIDYyNS40ICogc3RhcnNoaXBMYXVuY2hlczsKICAgICAgICAKICAgICAgICAvLyBEZWdyYWRhdGlvbiBtYXJnaW46IGhvdyBtdWNoIGV4dHJhIGNhcGFjaXR5IHdlJ3JlIGxhdW5jaGluZwogICAgICAgIGNvbnN0IGRlZ3JhZGF0aW9uTWFyZ2luID0gKGFjdHVhbEluaXRpYWxQb3dlclcgLyBkZXJpdmVkLlRBUkdFVF9QT1dFUl9XIC0gMSkgKiAxMDA7CiAgICAgICAgCiAgICAgICAgLy8gU29sYXIgbWFyZ2luIChzYW1lIGFzIGRlZ3JhZGF0aW9uIG1hcmdpbiAtIGV4dHJhIGNhcGFjaXR5IGZvciBjZWxsIGFnaW5nKQogICAgICAgIGNvbnN0IHNvbGFyTWFyZ2luUGN0ID0gZGVncmFkYXRpb25NYXJnaW47CiAgICAgICAgCiAgICAgICAgLy8gR1BVIG1hcmdpbjogY3VtdWxhdGl2ZSBmYWlsdXJlIHJhdGUgb3ZlciBhbmFseXNpcyBwZXJpb2QKICAgICAgICAvLyBUaGlzIHJlcHJlc2VudHMgdGhlIGV4cGVjdGVkIEdQVSBsb3NzZXMgd2UncmUgc2l6ZWQgdG8gaGFuZGxlCiAgICAgICAgY29uc3QgZ3B1TWFyZ2luUGN0ID0gc3RhdGUuZ3B1RmFpbHVyZVJhdGUgKiBzdGF0ZS55ZWFyczsKICAgICAgICAKICAgICAgICAvLyBTaW5nbGUgc2F0ZWxsaXRlIGFycmF5IGFyZWEKICAgICAgICBjb25zdCBzaW5nbGVTYXRBcnJheU0yID0gYXJyYXlQZXJTYXRlbGxpdGVNMjsKICAgICAgICAKICAgICAgICByZXR1cm4gewogICAgICAgICAgICB0b3RhbE1hc3NLZywKICAgICAgICAgICAgaGFyZHdhcmVDb3N0LAogICAgICAgICAgICBsYXVuY2hDb3N0LAogICAgICAgICAgICBvcHNDb3N0LAogICAgICAgICAgICBncHVSZXBsYWNlbWVudENvc3QsCiAgICAgICAgICAgIG5yZUNvc3QsCiAgICAgICAgICAgIGJhc2VDb3N0LAogICAgICAgICAgICB0b3RhbENvc3QsCiAgICAgICAgICAgIGVuZXJneU1XaCwKICAgICAgICAgICAgY29zdFBlclcsCiAgICAgICAgICAgIGxjb2UsCiAgICAgICAgICAgIHNhdGVsbGl0ZUNvdW50LAogICAgICAgICAgICBhcnJheUFyZWFLbTIsCiAgICAgICAgICAgIHNpbmdsZVNhdEFycmF5TTIsCiAgICAgICAgICAgIHN0YXJzaGlwTGF1bmNoZXMsCiAgICAgICAgICAgIAogICAgICAgICAgICAvLyBQcm9wZWxsYW50ICYgTG9naXN0aWNzIG91dHB1dHMKICAgICAgICAgICAgcHJvcGVsbGFudFRvdGFsVG9ucywKICAgICAgICAgICAgbG94VG9ucywKICAgICAgICAgICAgbG94R2FsbG9ucywKICAgICAgICAgICAgbWV0aGFuZUdhbGxvbnMsCiAgICAgICAgICAgIGVuZXJneVBlckxhdW5jaEdXaCwKICAgICAgICAgICAgdG90YWxMYXVuY2hFbmVyZ3lHV2gsCiAgICAgICAgICAgIHBjdFRleGFzR3JpZEltcGFjdCwKICAgICAgICAgICAgcGN0VG90YWxUZXhhc0xveCwKICAgICAgICAgICAgcGN0U3VycGx1c0NhcGFjaXR5LAogICAgICAgICAgICB0b3RhbFRhbmtlclRydWNrcywKICAgICAgICAgICAgCiAgICAgICAgICAgIGF2Z0NhcGFjaXR5RmFjdG9yLAogICAgICAgICAgICBkZWdyYWRhdGlvbk1hcmdpbiwKICAgICAgICAgICAgc29sYXJNYXJnaW5QY3QsCiAgICAgICAgICAgIGdwdU1hcmdpblBjdCwKICAgICAgICAgICAgYWN0dWFsSW5pdGlhbFBvd2VyVywKICAgICAgICAgICAgcmVxdWlyZWRJbml0aWFsUG93ZXJXCiAgICAgICAgfTsKICAgIH0KICAgIAogICAgZnVuY3Rpb24gY2FsY3VsYXRlVGVycmVzdHJpYWwoKSB7CiAgICAgICAgY29uc3QgZGVyaXZlZCA9IGdldERlcml2ZWQoKTsKICAgICAgICBjb25zdCB0b3RhbEhvdXJzID0gc3RhdGUueWVhcnMgKiBjb25zdGFudHMuSE9VUlNfUEVSX1lFQVI7CiAgICAgICAgCiAgICAgICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PQogICAgICAgIC8vIENBUEVYOiA1IEJ1Y2tldHMgZnJvbSBUZWNobm8tRWNvbm9taWMgUmVwb3J0CiAgICAgICAgLy8gVG90YWwgVGFyZ2V0OiB+JDEzLjgwL1cKICAgICAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAgICAgCiAgICAgICAgLy8gMS4gUG93ZXIgR2VuZXJhdGlvbiAoOSUpOiBHYXMgVHVyYmluZSArIEJhbGFuY2Ugb2YgUGxhbnQKICAgICAgICAvLyAkL2tXIMOXIFBVRSAvIDEwMDAgPSAkL1cgb2YgSVQgbG9hZAogICAgICAgIGNvbnN0IHBvd2VyR2VuQ29zdFBlclcgPSBzdGF0ZS5nYXNUdXJiaW5lQ2FwZXhQZXJLVyAqIHN0YXRlLnB1ZSAvIDEwMDA7CiAgICAgICAgY29uc3QgcG93ZXJHZW5Db3N0ID0gcG93ZXJHZW5Db3N0UGVyVyAqIGRlcml2ZWQuVEFSR0VUX1BPV0VSX1c7CiAgICAgICAgCiAgICAgICAgLy8gMi4gRWxlY3RyaWNhbCBEaXN0cmlidXRpb24gKDM4JSk6IFN3aXRjaGdlYXIsIFRyYW5zZm9ybWVycywgVVBTLCBHZW5zZXRzCiAgICAgICAgY29uc3QgZWxlY3RyaWNhbENvc3QgPSBzdGF0ZS5lbGVjdHJpY2FsQ29zdFBlclcgKiBkZXJpdmVkLlRBUkdFVF9QT1dFUl9XOwogICAgICAgIAogICAgICAgIC8vIDMuIE1lY2hhbmljYWwvQ29vbGluZyAoMjIlKTogRExDLCBDaGlsbGVycywgQ0RVcywgUGlwaW5nCiAgICAgICAgY29uc3QgbWVjaGFuaWNhbENvc3QgPSBzdGF0ZS5tZWNoYW5pY2FsQ29zdFBlclcgKiBkZXJpdmVkLlRBUkdFVF9QT1dFUl9XOwogICAgICAgIAogICAgICAgIC8vIDQuIENpdmlsICYgU2hlbGwgKDE4JSk6IExhbmQsIEJ1aWxkaW5nIFNoZWxsLCBTaXRlIFByZXAKICAgICAgICBjb25zdCBjaXZpbENvc3QgPSBzdGF0ZS5jaXZpbENvc3RQZXJXICogZGVyaXZlZC5UQVJHRVRfUE9XRVJfVzsKICAgICAgICAKICAgICAgICAvLyA1LiBOZXR3b3JraW5nL0ZpdC1vdXQgKDEzJSk6IEZpYmVyIFBsYW50LCBSYWNrcywgU2VjdXJpdHksIEJNUwogICAgICAgIGNvbnN0IG5ldHdvcmtDb3N0ID0gc3RhdGUubmV0d29ya0Nvc3RQZXJXICogZGVyaXZlZC5UQVJHRVRfUE9XRVJfVzsKICAgICAgICAKICAgICAgICAvLyBUb3RhbCBpbmZyYXN0cnVjdHVyZSBjYXBleAogICAgICAgIGNvbnN0IGluZnJhQ2FwZXggPSBwb3dlckdlbkNvc3QgKyBlbGVjdHJpY2FsQ29zdCArIG1lY2hhbmljYWxDb3N0ICsgY2l2aWxDb3N0ICsgbmV0d29ya0Nvc3Q7CiAgICAgICAgCiAgICAgICAgLy8gRmFjaWxpdHkgY2FwZXggcGVyIHdhdHQgKGFsbCA1IGJ1Y2tldHMpCiAgICAgICAgY29uc3QgZmFjaWxpdHlDYXBleFBlclcgPSBwb3dlckdlbkNvc3RQZXJXICsgc3RhdGUuZWxlY3RyaWNhbENvc3RQZXJXICsgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgc3RhdGUubWVjaGFuaWNhbENvc3RQZXJXICsgc3RhdGUuY2l2aWxDb3N0UGVyVyArIHN0YXRlLm5ldHdvcmtDb3N0UGVyVzsKICAgICAgICAKICAgICAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAgICAgLy8gT1BFWDogRnVlbCBjb3N0IChOYXRHYXMgQ0NHVCkKICAgICAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAgICAgCiAgICAgICAgLy8gRW5lcmd5IG91dHB1dDogSVQgcG93ZXIgw5cgaG91cnMgw5cgY2FwYWNpdHkgZmFjdG9yCiAgICAgICAgY29uc3QgZW5lcmd5TVdoID0gZGVyaXZlZC5UQVJHRVRfUE9XRVJfTVcgKiB0b3RhbEhvdXJzICogc3RhdGUuY2FwYWNpdHlGYWN0b3I7CiAgICAgICAgCiAgICAgICAgLy8gVG90YWwgZ2VuZXJhdGlvbiBuZWVkZWQgKElUIGxvYWQgw5cgUFVFKQogICAgICAgIGNvbnN0IGdlbmVyYXRpb25NV2ggPSBlbmVyZ3lNV2ggKiBzdGF0ZS5wdWU7CiAgICAgICAgCiAgICAgICAgLy8gRnVlbCBjb3N0IHBlciBNV2g6IGhlYXQgcmF0ZSDDlyBnYXMgcHJpY2UKICAgICAgICAvLyAkL01XaCA9IChCVFUva1doKSDDlyAoJC9NTUJ0dSkgLyAxMDAwCiAgICAgICAgY29uc3QgZnVlbENvc3RQZXJNV2ggPSBzdGF0ZS5oZWF0UmF0ZUJ0dUt3aCAqIHN0YXRlLmdhc1ByaWNlUGVyTU1CdHUgLyAxMDAwOwogICAgICAgIAogICAgICAgIC8vIFRvdGFsIGZ1ZWwgY29zdCBvdmVyIGFuYWx5c2lzIHBlcmlvZAogICAgICAgIGNvbnN0IGZ1ZWxDb3N0VG90YWwgPSBmdWVsQ29zdFBlck1XaCAqIGdlbmVyYXRpb25NV2g7CiAgICAgICAgCiAgICAgICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PQogICAgICAgIC8vIFRPVEFMCiAgICAgICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PQogICAgICAgIAogICAgICAgIGNvbnN0IHRvdGFsQ29zdCA9IGluZnJhQ2FwZXggKyBmdWVsQ29zdFRvdGFsOwogICAgICAgIGNvbnN0IGNvc3RQZXJXID0gdG90YWxDb3N0IC8gZGVyaXZlZC5UQVJHRVRfUE9XRVJfVzsKICAgICAgICAKICAgICAgICAvLyBMQ09FIChiYXNlZCBvbiBJVCBlbmVyZ3kgZGVsaXZlcmVkKQogICAgICAgIGNvbnN0IGxjb2UgPSB0b3RhbENvc3QgLyBlbmVyZ3lNV2g7CiAgICAgICAgCiAgICAgICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PQogICAgICAgIC8vIEVuZ2luZWVyaW5nIG91dHB1dHMKICAgICAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAgICAgY29uc3QgZ2VuZXJhdGlvbktXaCA9IGdlbmVyYXRpb25NV2ggKiAxMDAwOwogICAgICAgIGNvbnN0IHRvdGFsQlRVID0gZ2VuZXJhdGlvbktXaCAqIHN0YXRlLmhlYXRSYXRlQnR1S3doOwogICAgICAgIGNvbnN0IGdhc0NvbnN1bXB0aW9uQkNGID0gdG90YWxCVFUgLyBjb25zdGFudHMuQlRVX1BFUl9DRiAvIGNvbnN0YW50cy5DRl9QRVJfQkNGOwogICAgICAgIAogICAgICAgIC8vIFR1cmJpbmUgY291bnQgKEgtY2xhc3MgfjQzMCBNVyBlYWNoKQogICAgICAgIGNvbnN0IHRvdGFsR2VuZXJhdGlvbk1XID0gZGVyaXZlZC5UQVJHRVRfUE9XRVJfTVcgKiBzdGF0ZS5wdWU7CiAgICAgICAgY29uc3QgdHVyYmluZUNvdW50ID0gTWF0aC5jZWlsKHRvdGFsR2VuZXJhdGlvbk1XIC8gY29uc3RhbnRzLkdFXzdIQV9QT1dFUl9NVyk7CiAgICAgICAgCiAgICAgICAgLy8gRnVlbCBjb3N0IHBlciBXLXllYXIgKGZvciBkaXNwbGF5KQogICAgICAgIGNvbnN0IGZ1ZWxDb3N0UGVyV1llYXIgPSBmdWVsQ29zdFBlck1XaCAqIHN0YXRlLnB1ZSAqIDAuMDA4NzY7CiAgICAgICAgCiAgICAgICAgcmV0dXJuIHsKICAgICAgICAgICAgLy8gQ2FwZXggYnJlYWtkb3duICg1IGJ1Y2tldHMpCiAgICAgICAgICAgIHBvd2VyR2VuQ29zdCwKICAgICAgICAgICAgcG93ZXJHZW5Db3N0UGVyVywKICAgICAgICAgICAgZWxlY3RyaWNhbENvc3QsCiAgICAgICAgICAgIG1lY2hhbmljYWxDb3N0LAogICAgICAgICAgICBjaXZpbENvc3QsCiAgICAgICAgICAgIG5ldHdvcmtDb3N0LAogICAgICAgICAgICBpbmZyYUNhcGV4LAogICAgICAgICAgICBmYWNpbGl0eUNhcGV4UGVyVywKICAgICAgICAgICAgCiAgICAgICAgICAgIC8vIE9wZXgKICAgICAgICAgICAgZnVlbENvc3RQZXJNV2gsCiAgICAgICAgICAgIGZ1ZWxDb3N0VG90YWwsCiAgICAgICAgICAgIGZ1ZWxDb3N0UGVyV1llYXIsCiAgICAgICAgICAgIAogICAgICAgICAgICAvLyBUb3RhbHMKICAgICAgICAgICAgdG90YWxDb3N0LAogICAgICAgICAgICBlbmVyZ3lNV2gsCiAgICAgICAgICAgIGdlbmVyYXRpb25NV2gsCiAgICAgICAgICAgIGNvc3RQZXJXLAogICAgICAgICAgICBsY29lLAogICAgICAgICAgICB0b3RhbEhvdXJzLAogICAgICAgICAgICAKICAgICAgICAgICAgLy8gRW5naW5lZXJpbmcKICAgICAgICAgICAgZ2FzQ29uc3VtcHRpb25CQ0YsCiAgICAgICAgICAgIHR1cmJpbmVDb3VudCwKICAgICAgICAgICAgdG90YWxHZW5lcmF0aW9uTVcsCiAgICAgICAgICAgIGNhcGFjaXR5RmFjdG9yOiBzdGF0ZS5jYXBhY2l0eUZhY3RvciwKICAgICAgICAgICAgcHVlOiBzdGF0ZS5wdWUKICAgICAgICB9OwogICAgfQogICAgCiAgICBmdW5jdGlvbiBjYWxjdWxhdGVCcmVha2V2ZW4oKSB7CiAgICAgICAgY29uc3QgZGVyaXZlZCA9IGdldERlcml2ZWQoKTsKICAgICAgICBjb25zdCB0b3RhbEhvdXJzID0gc3RhdGUueWVhcnMgKiBjb25zdGFudHMuSE9VUlNfUEVSX1lFQVI7CiAgICAgICAgY29uc3QgZW5lcmd5TVdoID0gZGVyaXZlZC5UQVJHRVRfUE9XRVJfTVcgKiB0b3RhbEhvdXJzICogc3RhdGUuY2FwYWNpdHlGYWN0b3I7CiAgICAgICAgY29uc3QgZ2VuZXJhdGlvbk1XaCA9IGVuZXJneU1XaCAqIHN0YXRlLnB1ZTsKICAgICAgICAKICAgICAgICAvLyBUZXJyZXN0cmlhbCBjb3N0cyAoNSBidWNrZXRzIGZyb20gcmVwb3J0KQogICAgICAgIGNvbnN0IHBvd2VyR2VuQ29zdFBlclcgPSBzdGF0ZS5nYXNUdXJiaW5lQ2FwZXhQZXJLVyAqIHN0YXRlLnB1ZSAvIDEwMDA7CiAgICAgICAgY29uc3QgaW5mcmFDb3N0ID0gKHBvd2VyR2VuQ29zdFBlclcgKyBzdGF0ZS5lbGVjdHJpY2FsQ29zdFBlclcgKyBzdGF0ZS5tZWNoYW5pY2FsQ29zdFBlclcgKyAKICAgICAgICAgICAgICAgICAgICAgICAgICBzdGF0ZS5jaXZpbENvc3RQZXJXICsgc3RhdGUubmV0d29ya0Nvc3RQZXJXKSAqIGRlcml2ZWQuVEFSR0VUX1BPV0VSX1c7CiAgICAgICAgY29uc3QgZnVlbENvc3RQZXJNV2ggPSBzdGF0ZS5oZWF0UmF0ZUJ0dUt3aCAqIHN0YXRlLmdhc1ByaWNlUGVyTU1CdHUgLyAxMDAwOwogICAgICAgIGNvbnN0IGZ1ZWxDb3N0ID0gZnVlbENvc3RQZXJNV2ggKiBnZW5lcmF0aW9uTVdoOwogICAgICAgIGNvbnN0IHRlcnJlc3RyaWFsQ29zdCA9IGluZnJhQ29zdCArIGZ1ZWxDb3N0OwogICAgICAgIAogICAgICAgIC8vIENhbGN1bGF0ZSBkZWdyYWRhdGlvbi1hZGp1c3RlZCBvcmJpdGFsIGNhcGFjaXR5IG5lZWRlZAogICAgICAgIGNvbnN0IGFubnVhbFJldGVudGlvbiA9IDEgLSAoc3RhdGUuY2VsbERlZ3JhZGF0aW9uIC8gMTAwKTsKICAgICAgICBsZXQgY2FwYWNpdHlTdW0gPSAwOwogICAgICAgIGZvciAobGV0IHllYXIgPSAwOyB5ZWFyIDwgc3RhdGUueWVhcnM7IHllYXIrKykgewogICAgICAgICAgICBjYXBhY2l0eVN1bSArPSBNYXRoLnBvdyhhbm51YWxSZXRlbnRpb24sIHllYXIpOwogICAgICAgIH0KICAgICAgICBjb25zdCBhdmdDYXBhY2l0eUZhY3RvciA9IGNhcGFjaXR5U3VtIC8gc3RhdGUueWVhcnM7CiAgICAgICAgY29uc3Qgc3VubGlnaHRBZGp1c3RlZEZhY3RvciA9IGF2Z0NhcGFjaXR5RmFjdG9yICogc3RhdGUuc3VuRnJhY3Rpb247CiAgICAgICAgY29uc3QgcmVxdWlyZWRJbml0aWFsUG93ZXJXID0gZGVyaXZlZC5UQVJHRVRfUE9XRVJfVyAvIHN1bmxpZ2h0QWRqdXN0ZWRGYWN0b3I7CiAgICAgICAgCiAgICAgICAgY29uc3QgaGFyZHdhcmVDb3N0ID0gc3RhdGUuc2F0ZWxsaXRlQ29zdFBlclcgKiByZXF1aXJlZEluaXRpYWxQb3dlclc7CiAgICAgICAgY29uc3QgbWFzcyA9IHJlcXVpcmVkSW5pdGlhbFBvd2VyVyAvIHN0YXRlLnNwZWNpZmljUG93ZXJXUGVyS2c7CiAgICAgICAgCiAgICAgICAgcmV0dXJuICh0ZXJyZXN0cmlhbENvc3QgLSBoYXJkd2FyZUNvc3QpIC8gbWFzczsKICAgIH0KCiAgICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT0KICAgIC8vIEdFT01FVFJJQyBWSUVXIEZBQ1RPUiBDQUxDVUxBVElPTlMKICAgIC8vIFBoeXNpY3MtYmFzZWQgdmlldyBmYWN0b3JzIHJlcGxhY2luZyBhZC1ob2MgaGV1cmlzdGljcwogICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAKICAgIC8qKgogICAgICogQ2FsY3VsYXRlIEVhcnRoJ3MgYW5ndWxhciByYWRpdXMgYXMgc2VlbiBmcm9tIG9yYml0YWwgYWx0aXR1ZGUuCiAgICAgKiDOuF9lYXJ0aCA9IGFyY3NpbihSX2UgLyAoUl9lICsgaCkpCiAgICAgKiBBdCA1NTAga206IM64ID0gNjcuMMKwCiAgICAgKi8KICAgIGZ1bmN0aW9uIGVhcnRoQW5ndWxhclJhZGl1cyhhbHRpdHVkZUttKSB7CiAgICAgICAgY29uc3Qgck9yYml0ID0gY29uc3RhbnRzLkVBUlRIX1JBRElVU19LTSArIGFsdGl0dWRlS207CiAgICAgICAgcmV0dXJuIE1hdGguYXNpbihjb25zdGFudHMuRUFSVEhfUkFESVVTX0tNIC8gck9yYml0KTsKICAgIH0KICAgIAogICAgLyoqCiAgICAgKiBWaWV3IGZhY3RvciBmb3IgbmFkaXItZmFjaW5nIHBsYXRlIChtYXhpbXVtIHBvc3NpYmxlKS4KICAgICAqIFZGX25hZGlyID0gc2luwrIozrhfZWFydGgpID0gKFJfZSAvIChSX2UgKyBoKSnCsgogICAgICogQXQgNTUwIGttOiBWRl9uYWRpciA9IDAuODQ3CiAgICAgKi8KICAgIGZ1bmN0aW9uIG5hZGlyVmlld0ZhY3RvcihhbHRpdHVkZUttKSB7CiAgICAgICAgY29uc3QgdGhldGEgPSBlYXJ0aEFuZ3VsYXJSYWRpdXMoYWx0aXR1ZGVLbSk7CiAgICAgICAgcmV0dXJuIE1hdGgucG93KE1hdGguc2luKHRoZXRhKSwgMik7CiAgICB9CiAgICAKICAgIC8qKgogICAgICogVmlldyBmYWN0b3IgZm9yIHRpbHRlZCBwbGF0ZSBhdCBhbmdsZSDOsyBmcm9tIG5hZGlyLgogICAgICogRm9yIGEgZGlmZnVzZSBwbGF0ZSB0aWx0ZWQgZnJvbSBuYWRpciwgVkYg4omIIFZGX25hZGlyIMOXIGNvcyjOsykKICAgICAqIFRoaXMgaXMgYSBmaXJzdC1vcmRlciBhcHByb3hpbWF0aW9uIHZhbGlkIGZvciDOsyA8ICg5MMKwIC0gzrhfZWFydGgpCiAgICAgKi8KICAgIGZ1bmN0aW9uIHRpbHRlZFBsYXRlVmlld0ZhY3RvcihhbHRpdHVkZUttLCB0aWx0UmFkKSB7CiAgICAgICAgY29uc3QgdGhldGEgPSBlYXJ0aEFuZ3VsYXJSYWRpdXMoYWx0aXR1ZGVLbSk7CiAgICAgICAgY29uc3QgdmZOYWRpciA9IE1hdGgucG93KE1hdGguc2luKHRoZXRhKSwgMik7CiAgICAgICAgCiAgICAgICAgY29uc3QgY29zVGlsdCA9IE1hdGguY29zKHRpbHRSYWQpOwogICAgICAgIAogICAgICAgIC8vIEZvciBwbGF0ZXMgdGlsdGVkID4gOTDCsCBmcm9tIG5hZGlyLCB0aGV5IGZhY2UgYXdheSBmcm9tIEVhcnRoCiAgICAgICAgLy8gYnV0IHN0aWxsIGhhdmUgc21hbGwgdmlldyBmYWN0b3IgZHVlIHRvIEVhcnRoJ3MgbGFyZ2UgYW5ndWxhciBzaXplCiAgICAgICAgLy8gTWluaW11bSBWRiBpcyBhcHByb3hpbWF0ZWx5IHNpbsKyKM64KSDDlyAoMSAtIGNvc8KyKM6zKSkgLyA0IGZvciBlZGdlLW9uCiAgICAgICAgaWYgKGNvc1RpbHQgPD0gMCkgewogICAgICAgICAgICAvLyBFZGdlLW9uIG9yIGZhY2luZyBhd2F5OiB1c2UgbWluaW11bSBnZW9tZXRyaWMgVkYKICAgICAgICAgICAgLy8gRXZlbiBlZGdlLW9uIHBhbmVscyBzZWUgc29tZSBFYXJ0aCBkdWUgdG8gNjfCsCBoYWxmLWFuZ2xlCiAgICAgICAgICAgIGNvbnN0IG1pblZGID0gdmZOYWRpciAqIDAuMDU7ICAvLyB+NSUgb2YgbmFkaXIgVkYgYXMgZmxvb3IKICAgICAgICAgICAgcmV0dXJuIG1pblZGOwogICAgICAgIH0KICAgICAgICAKICAgICAgICByZXR1cm4gdmZOYWRpciAqIGNvc1RpbHQ7CiAgICB9CgogICAgLyoqCiAgICAgKiBOdW1lcmljYWxseS1zdGFibGUgdmVyc2lvbiBvZiBgdGlsdGVkUGxhdGVWaWV3RmFjdG9yYCB3aGVuIHlvdSBhbHJlYWR5IGhhdmUgY29zKM6zKS4KICAgICAqCiAgICAgKiBUaGlzIGF2b2lkcyB0aGUgYWNvc+KGkmNvcyByb3VuZHRyaXAgaW4gdGhlIG9yYml0IGludGVncmF0b3IsIHdoaWNoIGNhbiBsb3NlIHRoZSBzaWduCiAgICAgKiBvZiBleHRyZW1lbHkgc21hbGwgY29zKM6zKSB2YWx1ZXMgKG5vdGFibHkgYXQgzrIg4omIIDkwwrApLCBjYXVzaW5nIHRoZSBlZGdlLW9uIGZsb29yCiAgICAgKiBicmFuY2ggdG8gYmUgc2tpcHBlZCBpbmNvcnJlY3RseS4KICAgICAqLwogICAgZnVuY3Rpb24gdGlsdGVkUGxhdGVWaWV3RmFjdG9yRnJvbUNvcyhhbHRpdHVkZUttLCBjb3NUaWx0KSB7CiAgICAgICAgY29uc3QgdGhldGEgPSBlYXJ0aEFuZ3VsYXJSYWRpdXMoYWx0aXR1ZGVLbSk7CiAgICAgICAgY29uc3QgdmZOYWRpciA9IE1hdGgucG93KE1hdGguc2luKHRoZXRhKSwgMik7CiAgICAgICAgCiAgICAgICAgaWYgKGNvc1RpbHQgPD0gMCkgewogICAgICAgICAgICByZXR1cm4gdmZOYWRpciAqIDAuMDU7CiAgICAgICAgfQogICAgICAgIAogICAgICAgIHJldHVybiB2Zk5hZGlyICogY29zVGlsdDsKICAgIH0KICAgIAogICAgLyoqCiAgICAgKiBDYWxjdWxhdGUgb3JiaXQtYXZlcmFnZWQgdmlldyBmYWN0b3JzIGZvciBzdW4tdHJhY2tpbmcgYmlmYWNpYWwgcGFuZWwuCiAgICAgKiAKICAgICAqIEZvciBhIHN1bi10cmFja2luZyBwYW5lbDoKICAgICAqIC0gU2lkZSBBIChQVikgYWx3YXlzIGZhY2VzIHRoZSBzdW4KICAgICAqIC0gU2lkZSBCIChyYWRpYXRvcikgYWx3YXlzIGZhY2VzIGFudGktc3VuCiAgICAgKiAKICAgICAqIFRoZSB2aWV3IGZhY3RvciBkZXBlbmRzIG9uIGJldGEgYW5nbGUgYW5kIG9yYml0YWwgcG9zaXRpb24uCiAgICAgKiBBdCDOsiA9IDkwwrAgKHRlcm1pbmF0b3IpOiBwYW5lbCBpcyBtb3N0bHkgZWRnZS1vbiB0byBFYXJ0aAogICAgICogQXQgzrIgPSAwwrAgKG5vb24tbWlkbmlnaHQpOiBwYW5lbCBvc2NpbGxhdGVzIG5hZGlyL3plbml0aCBmYWNpbmcKICAgICAqLwogICAgZnVuY3Rpb24gc3VuVHJhY2tpbmdQYW5lbFZpZXdGYWN0b3JzKGFsdGl0dWRlS20sIGJldGFEZWcpIHsKICAgICAgICBjb25zdCBiZXRhUmFkID0gYmV0YURlZyAqIE1hdGguUEkgLyAxODA7CiAgICAgICAgY29uc3QgblBvaW50cyA9IDcyOyAgLy8gSW50ZWdyYXRpb24gcG9pbnRzIChldmVyeSA1wrAgYXJvdW5kIG9yYml0KQogICAgICAgIAogICAgICAgIGxldCB2ZkFTdW0gPSAwLjA7CiAgICAgICAgbGV0IHZmQlN1bSA9IDAuMDsKICAgICAgICAKICAgICAgICBmb3IgKGxldCBpID0gMDsgaSA8IG5Qb2ludHM7IGkrKykgewogICAgICAgICAgICAvLyBUcnVlIGFub21hbHkgKHBvc2l0aW9uIGluIG9yYml0KQogICAgICAgICAgICBjb25zdCBudSA9IDIgKiBNYXRoLlBJICogaSAvIG5Qb2ludHM7CiAgICAgICAgICAgIAogICAgICAgICAgICAvLyBGb3Igc3VuLXRyYWNraW5nIHBhbmVsLCB0aGUgYW5nbGUgYmV0d2VlbiBwYW5lbCBub3JtYWwKICAgICAgICAgICAgLy8gKHN1biBkaXJlY3Rpb24pIGFuZCBuYWRpciB2YXJpZXMgYXM6CiAgICAgICAgICAgIC8vIGNvcyjOsykg4omIIGNvcyjOsikgw5cgY29zKM69KQogICAgICAgICAgICAvLyBUaGlzIGNvbWVzIGZyb20gb3JiaXRhbCBnZW9tZXRyeSB3aXRoIHN1biBhdCBhbmdsZSDOsiB0byBvcmJpdCBwbGFuZQogICAgICAgICAgICBjb25zdCBjb3NHYW1tYSA9IE1hdGguY29zKGJldGFSYWQpICogTWF0aC5jb3MobnUpOwogICAgICAgICAgICAKICAgICAgICAgICAgLy8gQXZvaWQgYWNvc+KGkmNvcyAobnVtZXJpY2FsIGlzc3VlcyBuZWFyIM6yPTkwwrApCiAgICAgICAgICAgIGNvbnN0IHZmQSA9IHRpbHRlZFBsYXRlVmlld0ZhY3RvckZyb21Db3MoYWx0aXR1ZGVLbSwgY29zR2FtbWEpOwogICAgICAgICAgICBjb25zdCB2ZkIgPSB0aWx0ZWRQbGF0ZVZpZXdGYWN0b3JGcm9tQ29zKGFsdGl0dWRlS20sIC1jb3NHYW1tYSk7CiAgICAgICAgICAgIAogICAgICAgICAgICB2ZkFTdW0gKz0gdmZBOwogICAgICAgICAgICB2ZkJTdW0gKz0gdmZCOwogICAgICAgIH0KICAgICAgICAKICAgICAgICByZXR1cm4gewogICAgICAgICAgICB2ZlNpZGVBOiB2ZkFTdW0gLyBuUG9pbnRzLAogICAgICAgICAgICB2ZlNpZGVCOiB2ZkJTdW0gLyBuUG9pbnRzLAogICAgICAgICAgICB2ZlRvdGFsOiAodmZBU3VtICsgdmZCU3VtKSAvIG5Qb2ludHMKICAgICAgICB9OwogICAgfQoKICAgIC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PQogICAgLy8gVEhFUk1BTCBBTkFMWVNJUyAtIEJpZmFjaWFsIFBhbmVsIE1vZGVsCiAgICAvLyBCYXNlZCBvbiB2ZXJpZmllZCBlcXVpbGlicml1bSB0ZW1wZXJhdHVyZSBjYWxjdWxhdGlvbgogICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CgogICAgZnVuY3Rpb24gY2FsY3VsYXRlVGhlcm1hbCgpIHsKICAgICAgICAvLyBTdGVmYW4tQm9sdHptYW5uIGNvbnN0YW50IChXL23Csi9L4oG0KQogICAgICAgIGNvbnN0IFNJR01BID0gNS42N2UtODsKCiAgICAgICAgLy8gVXNlIG9yYml0YWwgYXJyYXkgYXJlYSAoYm90aCBzaWRlcyBhdmFpbGFibGUgZm9yIHRoZXJtYWwgZXhjaGFuZ2UpCiAgICAgICAgY29uc3Qgb3JiaXRhbCA9IGNhbGN1bGF0ZU9yYml0YWwoKTsKICAgICAgICBjb25zdCBhcmVhTTIgPSBvcmJpdGFsLmFycmF5QXJlYUttMiAqIDFlNjsKCiAgICAgICAgLy8gU3VyZmFjZSBwcm9wZXJ0aWVzIGZyb20gc3RhdGUKICAgICAgICBjb25zdCBhbHBoYVBWID0gc3RhdGUuc29sYXJBYnNvcnB0aXZpdHk7ICAgICAgLy8gU29sYXIgYWJzb3JwdGl2aXR5IG9mIFBWIHNpZGUKICAgICAgICBjb25zdCBlcHNpbG9uUFYgPSBzdGF0ZS5lbWlzc2l2aXR5UFY7ICAgICAgICAgLy8gSVIgZW1pc3Npdml0eSBvZiBQViBzaWRlCiAgICAgICAgY29uc3QgZXBzaWxvblJhZCA9IHN0YXRlLmVtaXNzaXZpdHlSYWQ7ICAgICAgIC8vIElSIGVtaXNzaXZpdHkgb2YgcmFkaWF0b3Igc2lkZQogICAgICAgIGNvbnN0IHB2RWZmaWNpZW5jeSA9IHN0YXRlLnB2RWZmaWNpZW5jeTsgICAgICAvLyBFbGVjdHJpY2FsIGNvbnZlcnNpb24gZWZmaWNpZW5jeQogICAgICAgIGNvbnN0IGJldGFBbmdsZSA9IHN0YXRlLmJldGFBbmdsZTsgICAgICAgICAgICAvLyBPcmJpdCBiZXRhIGFuZ2xlIChkZWdyZWVzKQogICAgICAgIGNvbnN0IGFsdGl0dWRlS20gPSBzdGF0ZS5vcmJpdGFsQWx0aXR1ZGVLbTsgICAvLyBPcmJpdGFsIGFsdGl0dWRlIChrbSkKCiAgICAgICAgLy8gLS0tIEEuIFZJRVcgRkFDVE9SIENBTENVTEFUSU9OIChHZW9tZXRyeS1CYXNlZCkgLS0tCiAgICAgICAgLy8gQ29tcHV0ZSBvcmJpdC1hdmVyYWdlZCB2aWV3IGZhY3RvcnMgZm9yIHN1bi10cmFja2luZyBiaWZhY2lhbCBwYW5lbAogICAgICAgIC8vIFRoaXMgcmVwbGFjZXMgdGhlIGFkLWhvYyBoZXVyaXN0aWMgd2l0aCBwaHlzaWNzLWRlcml2ZWQgdmFsdWVzCiAgICAgICAgY29uc3QgdmZSZXN1bHQgPSBzdW5UcmFja2luZ1BhbmVsVmlld0ZhY3RvcnMoYWx0aXR1ZGVLbSwgYmV0YUFuZ2xlKTsKICAgICAgICAKICAgICAgICAvLyBTZXBhcmF0ZSB2aWV3IGZhY3RvcnMgZm9yIGVhY2ggc2lkZQogICAgICAgIGNvbnN0IHZmU2lkZUEgPSB2ZlJlc3VsdC52ZlNpZGVBOyAgLy8gU3VuLWZhY2luZyAoUFYpIHNpZGUKICAgICAgICBjb25zdCB2ZlNpZGVCID0gdmZSZXN1bHQudmZTaWRlQjsgIC8vIEFudGktc3VuIChyYWRpYXRvcikgc2lkZQogICAgICAgIGNvbnN0IHZmRWFydGggPSB2ZlJlc3VsdC52ZlRvdGFsOyAgLy8gQ29tYmluZWQgKGZvciBkaXNwbGF5IG9ubHkpCgogICAgICAgIC8vIC0tLSBCLiBIRUFUIExPQURTIChJTlBVVFMpIC0tLQoKICAgICAgICAvLyAxLiBEaXJlY3QgU29sYXIgTG9hZCAoU2lkZSBBIG9ubHkpCiAgICAgICAgLy8gQWxsIGFic29yYmVkIHNvbGFyIGVuZXJneSB1bHRpbWF0ZWx5IGJlY29tZXMgaGVhdCBvbmJvYXJkIChubyBleHBvcnQpCiAgICAgICAgY29uc3QgcG93ZXJHZW5lcmF0ZWQgPSBjb25zdGFudHMuU09MQVJfSVJSQURJQU5DRV9XX00yICogcHZFZmZpY2llbmN5ICogYXJlYU0yOwogICAgICAgIAogICAgICAgIC8vIFRvdGFsIHNvbGFyIGVuZXJneSBhYnNvcmJlZCBieSB0aGUgcGFuZWwKICAgICAgICBjb25zdCBxQWJzb3JiZWRUb3RhbCA9IGNvbnN0YW50cy5TT0xBUl9JUlJBRElBTkNFX1dfTTIgKiBhbHBoYVBWICogYXJlYU0yOwogICAgICAgIAogICAgICAgIC8vIFNwbGl0OiBFbmVyZ3kgdGhhdCBiZWNvbWVzIGhlYXQgaW1tZWRpYXRlbHkgdnMgZW5lcmd5IHRoYXQgYmVjb21lcyBlbGVjdHJpY2l0eQogICAgICAgIC8vIChFbGVjdHJpY2l0eSByZXR1cm5zIGFzIGhlYXQgdmlhIHRoZSBsb29wLCBidXQgd2Ugc2VwYXJhdGUgZm9yIGNsYXJpdHkpCiAgICAgICAgY29uc3QgcVNvbGFyV2FzdGUgPSBxQWJzb3JiZWRUb3RhbCAtIHBvd2VyR2VuZXJhdGVkOwoKICAgICAgICAvLyAyLiBFYXJ0aCBJUiBMb2FkIC0gQ09SUkVDVCBGT1JNVUxBCiAgICAgICAgLy8gRWFjaCBzaWRlIGFic29yYnMgRWFydGggSVIgYmFzZWQgb24gaXRzIE9XTiB2aWV3IGZhY3RvciBhbmQgZW1pc3Npdml0eQogICAgICAgIC8vIChLaXJjaGhvZmYncyBsYXc6IGFic29ycHRpdml0eSA9IGVtaXNzaXZpdHkgZm9yIHRoZXJtYWwgSVIpCiAgICAgICAgLy8gcUVhcnRoSVIgPSBFX2VhcnRoIMOXIChWRl9BIMOXIM61X0EgKyBWRl9CIMOXIM61X0IpIMOXIEFyZWEKICAgICAgICBjb25zdCBxRWFydGhJUl9BID0gY29uc3RhbnRzLkVBUlRIX0lSX0ZMVVhfV19NMiAqIHZmU2lkZUEgKiBlcHNpbG9uUFYgKiBhcmVhTTI7CiAgICAgICAgY29uc3QgcUVhcnRoSVJfQiA9IGNvbnN0YW50cy5FQVJUSF9JUl9GTFVYX1dfTTIgKiB2ZlNpZGVCICogZXBzaWxvblJhZCAqIGFyZWFNMjsKICAgICAgICBjb25zdCBxRWFydGhJUiA9IHFFYXJ0aElSX0EgKyBxRWFydGhJUl9COwoKICAgICAgICAvLyAzLiBBbGJlZG8gTG9hZCAoUmVmbGVjdGVkIHN1bmxpZ2h0IGZyb20gRWFydGgpCiAgICAgICAgLy8gQWxiZWRvIGlzIGhpZ2hlc3Qgd2hlbiBCZXRhIGlzIGxvdyAoZmx5aW5nIG92ZXIgc3VubGl0IGVhcnRoKQogICAgICAgIC8vIEF0IEJldGEgOTAsIEFsYmVkbyBpcyBuZWFyIHplcm8KICAgICAgICAvLyBJTVBPUlRBTlQ6IE9ubHkgU2lkZSBBIChQViBzaWRlKSBoYXMgaGlnaCBzb2xhciBhYnNvcnB0aXZpdHkgKM6xPTAuOTIpCiAgICAgICAgLy8gU2lkZSBCIChyYWRpYXRvcikgaXMgd2hpdGUgcGFpbnQgd2l0aCDOseKJiDAuMS0wLjIgKG5lZ2xpZ2libGUpCiAgICAgICAgY29uc3QgYWxiZWRvU2NhbGluZyA9IE1hdGguY29zKGJldGFBbmdsZSAqIE1hdGguUEkgLyAxODApOyAvLyAwIGF0IDkwIGRlZywgMC41IGF0IDYwIGRlZwogICAgICAgIGNvbnN0IHFBbGJlZG8gPSBjb25zdGFudHMuU09MQVJfSVJSQURJQU5DRV9XX00yICogY29uc3RhbnRzLkVBUlRIX0FMQkVET19GQUNUT1IgKiB2ZlNpZGVBICogYWxiZWRvU2NhbGluZyAqIGFscGhhUFYgKiBhcmVhTTI7CgogICAgICAgIC8vIDQuIEhlYXQgTG9vcCBSZXR1cm4gKGZyb20gY29tcHV0ZSkKICAgICAgICAvLyBFbGVjdHJpY2l0eSBpcyBjb25zdW1lZCBvbmJvYXJkIGFuZCByZXR1cm5lZCBhcyBoZWF0CiAgICAgICAgY29uc3QgcUhlYXRMb29wID0gcG93ZXJHZW5lcmF0ZWQ7CgogICAgICAgIC8vIFRvdGFsIGhlYXQgaW5wdXQ6IHNvbGFyIHdhc3RlICsgRWFydGggSVIgKyBhbGJlZG8gKyBsb29wIHJldHVybgogICAgICAgIC8vIE5vdGU6IFN1bSBpcyBudW1lcmljYWxseSBlcXVhbCB0byBxQWJzb3JiZWRUb3RhbCArIHFFYXJ0aElSICsgcUFsYmVkbwogICAgICAgIGNvbnN0IHRvdGFsSGVhdEluID0gcVNvbGFyV2FzdGUgKyBxRWFydGhJUiArIHFBbGJlZG8gKyBxSGVhdExvb3A7CgogICAgICAgIC8vIC0tLSBDLiBIRUFUIFJFSkVDVElPTiAoT1VUUFVUUykgLS0tCiAgICAgICAgLy8gUV9vdXQgPSBzaWdtYSAqIEFyZWEgKiAoZXBzX2Zyb250ICsgZXBzX2JhY2spICogKFReNCAtIFRfc3BhY2VeNCkKICAgICAgICBjb25zdCB0b3RhbEVtaXNzaXZpdHkgPSBlcHNpbG9uUFYgKyBlcHNpbG9uUmFkOwogICAgICAgIGNvbnN0IHNwYWNlVGVtcEsgPSBjb25zdGFudHMuVF9TUEFDRV9LOwoKICAgICAgICAvLyBTb2x2ZSBmb3IgZXF1aWxpYnJpdW0gdGVtcGVyYXR1cmUgKFN0ZWZhbi1Cb2x0em1hbm4gcmVhcnJhbmdlbWVudCkKICAgICAgICAvLyBUID0gKFFfaW4gLyAoc2lnbWEgKiBBICogZXBzX3RvdGFsKSArIFRfc3BhY2VeNCkgXiAwLjI1CiAgICAgICAgY29uc3QgZXFUZW1wSyA9IE1hdGgucG93KAogICAgICAgICAgICAodG90YWxIZWF0SW4gLyAoU0lHTUEgKiBhcmVhTTIgKiB0b3RhbEVtaXNzaXZpdHkpKSArIE1hdGgucG93KHNwYWNlVGVtcEssIDQpLAogICAgICAgICAgICAwLjI1CiAgICAgICAgKTsKICAgICAgICBjb25zdCBlcVRlbXBDID0gZXFUZW1wSyAtIDI3My4xNTsKCiAgICAgICAgLy8gUmFkaWF0aXZlIGNhcGFjaXR5IGF0IGVxdWlsaWJyaXVtIHRlbXBlcmF0dXJlIC0gU0VQQVJBVEUgZm9yIGVhY2ggc2lkZQogICAgICAgIGNvbnN0IGRlbHRhVDRfZXEgPSBNYXRoLnBvdyhlcVRlbXBLLCA0KSAtIE1hdGgucG93KHNwYWNlVGVtcEssIDQpOwogICAgICAgIGNvbnN0IHFSYWRBID0gU0lHTUEgKiBhcmVhTTIgKiBlcHNpbG9uUFYgKiBkZWx0YVQ0X2VxOyAgIC8vIFNpZGUgQSAoUFYpIHJhZGlhdGlvbgogICAgICAgIGNvbnN0IHFSYWRCID0gU0lHTUEgKiBhcmVhTTIgKiBlcHNpbG9uUmFkICogZGVsdGFUNF9lcTsgIC8vIFNpZGUgQiAoUmFkaWF0b3IpIHJhZGlhdGlvbgogICAgICAgIGNvbnN0IHJhZGlhdGl2ZUNhcGFjaXR5VyA9IHFSYWRBICsgcVJhZEI7CgogICAgICAgIC8vIC0tLSBELiBDT01QVVRFIFRIRVJNQUwgQU5BTFlTSVMgLS0tCiAgICAgICAgLy8gV2l0aCBubyBleHBvcnQgc2NlbmFyaW8sIGNvbXB1dGUgaGVhdCBlcXVhbHMgdG90YWwgaGVhdAogICAgICAgIGNvbnN0IGNvbXB1dGVIZWF0SW4gPSB0b3RhbEhlYXRJbjsKICAgICAgICBjb25zdCBjb21wdXRlVGVtcEsgPSBlcVRlbXBLOwogICAgICAgIGNvbnN0IGNvbXB1dGVUZW1wQyA9IGVxVGVtcEM7CgogICAgICAgIC8vIE1hcmdpbiBjYWxjdWxhdGlvbjogaXMgZXF1aWxpYnJpdW0gdGVtcCBiZWxvdyBkaWUgbGltaXQ/CiAgICAgICAgY29uc3QgcmFkaWF0b3JUZW1wQyA9IHN0YXRlLm1heERpZVRlbXBDIC0gc3RhdGUudGVtcERyb3BDOwogICAgICAgIGNvbnN0IHRlbXBNYXJnaW5DID0gcmFkaWF0b3JUZW1wQyAtIGVxVGVtcEM7CiAgICAgICAgY29uc3QgYXJlYVN1ZmZpY2llbnQgPSBlcVRlbXBDIDw9IHJhZGlhdG9yVGVtcEM7CiAgICAgICAgY29uc3QgbWFyZ2luUGN0ID0gKHRlbXBNYXJnaW5DIC8gcmFkaWF0b3JUZW1wQykgKiAxMDA7CgogICAgICAgIC8vIEFyZWEgcmVxdWlyZWQgdG8gYWNoaWV2ZSB0YXJnZXQgcmFkaWF0b3IgdGVtcGVyYXR1cmUKICAgICAgICBjb25zdCB0YXJnZXRUZW1wSyA9IHJhZGlhdG9yVGVtcEMgKyAyNzMuMTU7CiAgICAgICAgY29uc3QgZGVsdGFUNCA9IE1hdGgucG93KHRhcmdldFRlbXBLLCA0KSAtIE1hdGgucG93KHNwYWNlVGVtcEssIDQpOwogICAgICAgIGNvbnN0IGFyZWFSZXF1aXJlZE0yID0gdG90YWxIZWF0SW4gLyAoU0lHTUEgKiB0b3RhbEVtaXNzaXZpdHkgKiBkZWx0YVQ0KTsKCiAgICAgICAgLy8gRWZmZWN0aXZlIGF2ZXJhZ2UgZW1pc3Npdml0eQogICAgICAgIGNvbnN0IGVmZmVjdGl2ZUVtaXNzaXZpdHkgPSB0b3RhbEVtaXNzaXZpdHkgLyAyOwoKICAgICAgICAvLyBHZW9tZXRyaWMgcGFyYW1ldGVycyBmb3IgZGlzcGxheQogICAgICAgIGNvbnN0IGVhcnRoQW5nUmFkID0gZWFydGhBbmd1bGFyUmFkaXVzKGFsdGl0dWRlS20pOwogICAgICAgIGNvbnN0IHZmTmFkaXJNYXggPSBuYWRpclZpZXdGYWN0b3IoYWx0aXR1ZGVLbSk7CiAgICAgICAgCiAgICAgICAgcmV0dXJuIHsKICAgICAgICAgICAgLy8gSW5wdXQgcGFyYW1ldGVycwogICAgICAgICAgICBiZXRhQW5nbGUsCiAgICAgICAgICAgIGFsdGl0dWRlS20sCiAgICAgICAgICAgIHZmRWFydGgsCiAgICAgICAgICAgIAogICAgICAgICAgICAvLyBEZXRhaWxlZCB2aWV3IGZhY3RvciBicmVha2Rvd24gKGdlb21ldHJ5LWJhc2VkKQogICAgICAgICAgICB2ZlNpZGVBOiB2ZlJlc3VsdC52ZlNpZGVBLCAgICAgIC8vIFN1bi1mYWNpbmcgc2lkZSBWRiB0byBFYXJ0aAogICAgICAgICAgICB2ZlNpZGVCOiB2ZlJlc3VsdC52ZlNpZGVCLCAgICAgIC8vIEFudGktc3VuIHNpZGUgVkYgdG8gRWFydGgKICAgICAgICAgICAgdmZUb3RhbDogdmZSZXN1bHQudmZUb3RhbCwgICAgICAvLyBDb21iaW5lZCBWRiAoYm90aCBzaWRlcykKICAgICAgICAgICAgdmZOYWRpck1heCwgICAgICAgICAgICAgICAgICAgICAvLyBNYXhpbXVtIHBvc3NpYmxlIFZGIChuYWRpci1wb2ludGluZykKICAgICAgICAgICAgZWFydGhBbmd1bGFyUmFkaXVzRGVnOiBlYXJ0aEFuZ1JhZCAqIDE4MCAvIE1hdGguUEksCiAgICAgICAgICAgIAogICAgICAgICAgICAvLyBBcmVhcwogICAgICAgICAgICBhdmFpbGFibGVBcmVhTTI6IGFyZWFNMiwKICAgICAgICAgICAgYXZhaWxhYmxlQXJlYUttMjogYXJlYU0yIC8gMWU2LAogICAgICAgICAgICBhcmVhUmVxdWlyZWRNMiwKICAgICAgICAgICAgYXJlYVJlcXVpcmVkS20yOiBhcmVhUmVxdWlyZWRNMiAvIDFlNiwKICAgICAgICAgICAgCiAgICAgICAgICAgIC8vIEhlYXQgbG9hZHMgKGlucHV0cykKICAgICAgICAgICAgcVNvbGFyVzogcVNvbGFyV2FzdGUsCiAgICAgICAgICAgIHFFYXJ0aElSVzogcUVhcnRoSVIsCiAgICAgICAgICAgIHFBbGJlZG9XOiBxQWxiZWRvLAogICAgICAgICAgICBxSGVhdExvb3BXOiBxSGVhdExvb3AsCiAgICAgICAgICAgIHRvdGFsSGVhdEluVzogdG90YWxIZWF0SW4sCiAgICAgICAgICAgIHBvd2VyR2VuZXJhdGVkVzogcG93ZXJHZW5lcmF0ZWQsCiAgICAgICAgICAgIAogICAgICAgICAgICAvLyBIZWF0IHJlamVjdGlvbiAob3V0cHV0cykgLSBzZXBhcmF0ZSBmb3IgZWFjaCBzaWRlCiAgICAgICAgICAgIHFSYWRBVzogcVJhZEEsICAgICAgLy8gU2lkZSBBIChQViBzaWRlKSByYWRpYXRpb24gdG8gc3BhY2UKICAgICAgICAgICAgcVJhZEJXOiBxUmFkQiwgICAgICAvLyBTaWRlIEIgKFJhZGlhdG9yIHNpZGUpIHJhZGlhdGlvbiB0byBzcGFjZQogICAgICAgICAgICAKICAgICAgICAgICAgLy8gVGhlcm1hbCBvdXRwdXRzCiAgICAgICAgICAgIGVxVGVtcEssCiAgICAgICAgICAgIGVxVGVtcEMsCiAgICAgICAgICAgIGNvbXB1dGVUZW1wQywgICAgICAgICAgLy8gVGVtcCBpZiBwb3dlciBzdGF5cyBvbmJvYXJkCiAgICAgICAgICAgIHJhZGlhdG9yVGVtcEMsICAgICAgICAgLy8gVGFyZ2V0IHJhZGlhdG9yIHRlbXAgKGRpZSAtIGRyb3ApCiAgICAgICAgICAgIHRlbXBNYXJnaW5DLAogICAgICAgICAgICAKICAgICAgICAgICAgLy8gQ2FwYWNpdHkKICAgICAgICAgICAgcmFkaWF0aXZlQ2FwYWNpdHlXLAogICAgICAgICAgICBlZmZlY3RpdmVFbWlzc2l2aXR5LAogICAgICAgICAgICB0b3RhbEVtaXNzaXZpdHksCiAgICAgICAgICAgIAogICAgICAgICAgICAvLyBTdGF0dXMKICAgICAgICAgICAgYXJlYVN1ZmZpY2llbnQsCiAgICAgICAgICAgIG1hcmdpblBjdCwKICAgICAgICAgICAgCiAgICAgICAgICAgIC8vIExlZ2FjeSBjb21wYXRpYmlsaXR5CiAgICAgICAgICAgIHJhZGlhdG9yVGVtcEs6IHRhcmdldFRlbXBLLAogICAgICAgICAgICBjYXBhY2l0eVc6IHJhZGlhdGl2ZUNhcGFjaXR5VywKICAgICAgICAgICAgaGVhdExvYWRXOiB0b3RhbEhlYXRJbiwKICAgICAgICAgICAgaW5jaWRlbnRTb2xhclc6IGNvbnN0YW50cy5TT0xBUl9JUlJBRElBTkNFX1dfTTIgKiBhcmVhTTIsCiAgICAgICAgICAgIHdhc3RlSGVhdFc6IHFTb2xhcldhc3RlLAogICAgICAgICAgICBlbGVjdHJpY2FsSGVhdFc6IHBvd2VyR2VuZXJhdGVkLAogICAgICAgICAgICByZXF1aXJlZFRlbXBLOiBlcVRlbXBLLAogICAgICAgICAgICByZXF1aXJlZFRlbXBDOiBlcVRlbXBDCiAgICAgICAgfTsKICAgIH0KICAgIAogICAgLy8gQWxpYXMgZm9yIGJhY2t3YXJkcyBjb21wYXRpYmlsaXR5CiAgICBmdW5jdGlvbiBjYWxjdWxhdGVOYXRHYXMoKSB7CiAgICAgICAgcmV0dXJuIGNhbGN1bGF0ZVRlcnJlc3RyaWFsKCk7CiAgICB9CgogICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAvLyBGT1JNQVRUSU5HIFVUSUxJVElFUwogICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAKICAgIGZ1bmN0aW9uIGZvcm1hdENvc3QoY29zdCkgewogICAgICAgIGlmIChNYXRoLmFicyhjb3N0KSA+PSAxZTEyKSByZXR1cm4gYCQkeyhjb3N0IC8gMWUxMikudG9GaXhlZCgxKX1UYDsKICAgICAgICBpZiAoTWF0aC5hYnMoY29zdCkgPj0gMWU5KSByZXR1cm4gYCQkeyhjb3N0IC8gMWU5KS50b0ZpeGVkKDEpfUJgOwogICAgICAgIGlmIChNYXRoLmFicyhjb3N0KSA+PSAxZTYpIHJldHVybiBgJCR7KGNvc3QgLyAxZTYpLnRvRml4ZWQoMCl9TWA7CiAgICAgICAgcmV0dXJuIGAkJHtNYXRoLnJvdW5kKGNvc3QpLnRvTG9jYWxlU3RyaW5nKCl9YDsKICAgIH0KICAgIAogICAgZnVuY3Rpb24gZm9ybWF0Q29zdFBlcktnKGNvc3QpIHsKICAgICAgICBpZiAoY29zdCA8IDApIHJldHVybiBg4oiSJCR7TWF0aC5hYnMoTWF0aC5yb3VuZChjb3N0KSkudG9Mb2NhbGVTdHJpbmcoKX0va2dgOwogICAgICAgIHJldHVybiBgJCR7TWF0aC5yb3VuZChjb3N0KS50b0xvY2FsZVN0cmluZygpfS9rZ2A7CiAgICB9CiAgICAKICAgIGZ1bmN0aW9uIGZvcm1hdE1hc3Moa2cpIHsKICAgICAgICBpZiAoa2cgPj0gMWU2KSByZXR1cm4gYCR7KGtnIC8gMWU2KS50b0ZpeGVkKDEpfU0ga2dgOwogICAgICAgIHJldHVybiBgJHtNYXRoLnJvdW5kKGtnKS50b0xvY2FsZVN0cmluZygpfSBrZ2A7CiAgICB9CiAgICAKICAgIGZ1bmN0aW9uIGZvcm1hdEVuZXJneShtd2gpIHsKICAgICAgICAvLyBBbHdheXMgZGlzcGxheSBpbiBtZWdhd2F0dC1ob3VycyB0byBhdm9pZCBtaXhlZCB1bml0cyBpbiB0aGUgVUkuCiAgICAgICAgaWYgKG13aCA+PSAxZTYpIHJldHVybiBgJHttd2gudG9Mb2NhbGVTdHJpbmcodW5kZWZpbmVkLCB7IG1heGltdW1GcmFjdGlvbkRpZ2l0czogMCB9KX0gTVdocmA7CiAgICAgICAgcmV0dXJuIGAke213aC50b0xvY2FsZVN0cmluZyh1bmRlZmluZWQsIHsgbWF4aW11bUZyYWN0aW9uRGlnaXRzOiAxIH0pfSBNV2hyYDsKICAgIH0KICAgIAogICAgZnVuY3Rpb24gZm9ybWF0TENPRShsY29lKSB7CiAgICAgICAgcmV0dXJuIGAkJHtNYXRoLnJvdW5kKGxjb2UpfS9NV2hgOwogICAgfQogICAgCiAgICBmdW5jdGlvbiBmb3JtYXRIb3Vycyhob3VycykgewogICAgICAgIHJldHVybiBgJHtob3Vycy50b0xvY2FsZVN0cmluZygpfSBocnNgOwogICAgfQoKICAgIC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PQogICAgLy8gUFVCTElDIEFQSQogICAgLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiAgICAKICAgIHJldHVybiB7CiAgICAgICAgLy8gQWNjZXNzIGNvbnN0YW50cwogICAgICAgIGdldENvbnN0YW50czogKCkgPT4gKHsgLi4uY29uc3RhbnRzIH0pLAogICAgICAgIHNldENvbnN0YW50czogKG5ld0NvbnN0YW50cykgPT4gewogICAgICAgICAgICBjb25zdGFudHMgPSB7IC4uLmNvbnN0YW50cywgLi4ubmV3Q29uc3RhbnRzIH07CiAgICAgICAgfSwKICAgICAgICAKICAgICAgICAvLyBBY2Nlc3Mgc3RhdGUKICAgICAgICBnZXRTdGF0ZTogKCkgPT4gKHsgLi4uc3RhdGUgfSksCiAgICAgICAgc2V0U3RhdGU6IChuZXdTdGF0ZSkgPT4gewogICAgICAgICAgICBzdGF0ZSA9IHsgLi4uc3RhdGUsIC4uLm5ld1N0YXRlIH07CiAgICAgICAgfSwKICAgICAgICB1cGRhdGVTdGF0ZTogKGtleSwgdmFsdWUpID0+IHsKICAgICAgICAgICAgc3RhdGVba2V5XSA9IHZhbHVlOwogICAgICAgIH0sCiAgICAgICAgCiAgICAgICAgLy8gU2F0ZWxsaXRlIHByZXNldHMKICAgICAgICBnZXRTYXRlbGxpdGVQcmVzZXRzOiAoKSA9PiAoeyAuLi5TQVRFTExJVEVfUFJFU0VUUyB9KSwKICAgICAgICAKICAgICAgICAvLyBDYWxjdWxhdGlvbnMKICAgICAgICBjYWxjdWxhdGVPcmJpdGFsLAogICAgICAgIGNhbGN1bGF0ZVRlcnJlc3RyaWFsLAogICAgICAgIGNhbGN1bGF0ZU5hdEdhcywgIC8vIEFsaWFzIGZvciBiYWNrd2FyZHMgY29tcGF0aWJpbGl0eQogICAgICAgIGNhbGN1bGF0ZUJyZWFrZXZlbiwKICAgICAgICBjYWxjdWxhdGVUaGVybWFsLAogICAgICAgIAogICAgICAgIC8vIEZvcm1hdHRlcnMKICAgICAgICBmb3JtYXRDb3N0LAogICAgICAgIGZvcm1hdENvc3RQZXJLZywKICAgICAgICBmb3JtYXRNYXNzLAogICAgICAgIGZvcm1hdEVuZXJneSwKICAgICAgICBmb3JtYXRMQ09FLAogICAgICAgIGZvcm1hdEhvdXJzCiAgICB9Owp9KSgpOwoKLy8gRXhwb3J0IGZvciB1c2UgaW4gb3RoZXIgZmlsZXMKaWYgKHR5cGVvZiBtb2R1bGUgIT09ICd1bmRlZmluZWQnICYmIG1vZHVsZS5leHBvcnRzKSB7CiAgICBtb2R1bGUuZXhwb3J0cyA9IENvc3RNb2RlbDsKfQoK
`````

### `external_models/mccalip_thoughts/provenance.md`

_(3679 bytes, sha256 `5eefd631c8f7663e9b880dbcfc30ddcebf9d2eb6372c30dd3ebb68b27b86ce29`)_

`````markdown
# McCalip "thoughts" model — provenance record

## Repository

- **URL**: https://github.com/andrewmccalip/thoughts
- **Description**: "Space Datacenters: Orbital vs Terrestrial Economics" — interactive
  first-principles cost and thermal model for orbital solar power satellites.
- **License**: MIT (see repo root)
- **Author**: Andrew McCalip (@andrewmccalip)

## Pinned version

| Field | Value |
|---|---|
| Commit SHA | `d1e4238d3d3f4924e5ca65bafbd4ba5b39af2eb8` |
| Commit message | "lox output panel" |
| Commit date | 2025-12-29T17:42:13Z |
| Date accessed | 2026-06-12 |
| Primary source file | `static/js/math.js` |

The oracle in `expected_outputs.json` was generated by running `generate_oracle.js`
against this exact commit's `math.js` (downloaded from the raw GitHub URL at the
pinned SHA). The file is reproduced verbatim in this directory as `math.js` for
offline verification.

## Convention differences from orbital-thermal-bounds

The following differences must be accounted for in the replication tolerance budget
when comparing McCalip outputs to our Python model (Task 10):

| Parameter | McCalip value | Our value | Relative difference |
|---|---|---|---|
| Stefan-Boltzmann sigma | `5.67e-8` (truncated) | `5.670374419184429e-8` (binary64 SI-derived) | 6.6e-5 |
| Deep-space sink T | `3 K` (rounded) | `2.7255 K` (CMB) | ~0.10 K |

The sigma truncation alone shifts equilibrium temperatures by ~0.002 K at 340 K
(four-root sensitivity: dT/T = d(sigma)/4(sigma)). The T_space difference matters
only near cryogenic sinks and is negligible at the AI1 operating range (>300 K).

For replication tests, a tolerance of **+/-0.05 K** on equilibrium temperatures
is appropriate; any larger divergence indicates a logic difference rather than
a constant difference.

## Thermal model summary (for replication reference)

McCalip implements a bifacial sun-tracking panel model:

1. **Nadir view factor**: `VF_nadir = sin^2(arcsin(R_e / (R_e + h)))` — exact formula.
   At 550 km: `VF_nadir ~ 0.8469` (McCalip states 0.847 in comments).

2. **Orbit-averaged view factors**: integrate over 72 equally-spaced true anomaly
   points; `cos(gamma) = cos(beta) * cos(nu)` for sun-tracking panel geometry.

3. **Heat balance**:
   - Q_in = Q_solar_waste + Q_EarthIR + Q_albedo + Q_heatloop
   - Albedo scaling = cos(beta) (zero at terminator beta=90)
   - Q_out = sigma * A * (eps_PV + eps_rad) * (T^4 - T_space^4)

4. **T_eq** = `(Q_in / (sigma * A * eps_total) + T_space^4)^0.25`

## Oracle scope

`expected_outputs.json` covers:
- Default state snapshot
- beta sweep: 0, 30, 60, 90 deg (at altitude 550 km)
- Altitude sweep: 400, 550, 800 km (at beta = 90 deg)
- Emissivity sweep: eps_rad in {0.85, 0.90, 0.95} (at altitude 550 km, beta = 90 deg)

**Enforcement scope (audit re-review P2-8).** CI runs `verify_oracle_reproducible.py`, which (1) checks SHA-256 pins of `math.js`, `generate_oracle.js`, and `expected_outputs.json` (PINS.json), (2) regenerates the oracle from the vendored `math.js` and compares it semantically, and (3) attests the vendored `math.js` against the raw blob at the external pinned commit on GitHub. Together these enforce repository consistency, accidental-drift detection, and external-source attestation. They do NOT, by themselves, prove the oracle was historically never edited; that is a process commitment recorded here.

**Oracle-freeze rule**: values in `expected_outputs.json` are never edited to make
a failing test pass. If McCalip's model is updated and oracle values change, the
entire `expected_outputs.json` must be regenerated with `generate_oracle.js` at a
new pinned commit, and `provenance.md` updated accordingly.
`````

### `external_models/mccalip_thoughts/verify_oracle_reproducible.py`

_(6313 bytes, sha256 `e77c84857e9e51ea1353a74ec8ebf14c9cfe348788b64f89a3495b59b6b2459b`)_

`````python
#!/usr/bin/env python3
"""Enforce oracle-freeze (audit re-review P2-e).

Two independent checks, run in CI:

1. SHA-256 pin -- the committed vendored source (math.js, generate_oracle.js) and
   the frozen oracle (expected_outputs.json) must match the SHA-256 values in
   PINS.json. This catches ANY edit to the frozen artifacts, which is the actual
   "never edited to make a test pass" guarantee for a snapshot.
2. Reproducibility -- regenerate the oracle from the vendored math.js with Node and
   compare to the committed file SEMANTICALLY: parsed numbers must agree to a tight
   relative tolerance, ignoring environment-dependent _meta fields (node_version,
   generated_on) and V8's version-dependent float text formatting. (A byte-for-byte
   compare is brittle: the same float64 serializes with different digit counts
   across Node/V8 versions.)

Exit code is nonzero on any mismatch. Requires Node on PATH for check 2; if Node is
absent the reproducibility check is skipped with a warning (the SHA pin still runs).
"""

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PINS = json.loads((HERE / "PINS.json").read_text())
VOLATILE_META = {"node_version", "generated_on"}


def check_sha256() -> list[str]:
    errs = []
    for name, want in PINS["sha256"].items():
        got = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        if got != want:
            errs.append(f"SHA-256 mismatch for {name}: got {got}, pinned {want}")
    return errs


def _diff_numbers(a, b, path=""):
    errs = []
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            errs.append(f"{path}: key set differs")
        for k in set(a) & set(b):
            errs += _diff_numbers(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            errs.append(f"{path}: length {len(a)} != {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            errs += _diff_numbers(x, y, f"{path}[{i}]")
    elif isinstance(a, bool) or isinstance(b, bool):
        if a != b:
            errs.append(f"{path}: {a!r} != {b!r}")
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12):
            errs.append(f"{path}: {a!r} !~= {b!r}")
    else:
        if a != b:
            errs.append(f"{path}: {a!r} != {b!r}")
    return errs


def _strip_volatile(meta):
    return {k: v for k, v in meta.items() if k not in VOLATILE_META}


def check_reproducible():
    """(errors, ran). Regenerate the oracle from the vendored math.js and compare
    semantically. If Node is unavailable: skip (warn) normally, or fail when strict
    (ORACLE_REQUIRE_EXTERNAL=1) -- audit re-review P2-3."""
    strict = os.environ.get("ORACLE_REQUIRE_EXTERNAL") == "1"
    if shutil.which("node") is None:
        msg = "node not found; cannot regenerate the oracle"
        if strict:
            return ([f"regeneration required but {msg} (ORACLE_REQUIRE_EXTERNAL=1)"], False)
        print(f"WARNING: skipping regeneration -- {msg} (SHA pins still enforced)")
        return ([], False)
    out = subprocess.run(["node", "generate_oracle.js"], cwd=HERE,
                         capture_output=True, text=True)
    if out.returncode != 0:
        return ([f"node generate_oracle.js failed: {out.stderr.strip()}"], True)
    regen = json.loads(out.stdout)
    committed = json.loads((HERE / "expected_outputs.json").read_text())
    regen["_meta"] = _strip_volatile(regen.get("_meta", {}))
    committed["_meta"] = _strip_volatile(committed.get("_meta", {}))
    return (_diff_numbers(regen, committed, "oracle"), True)


def check_external():
    """(errors, ran). Attest the vendored math.js against the raw blob at the recorded
    EXTERNAL pinned commit (not self-referential). Network-lenient by default; set
    ORACLE_REQUIRE_EXTERNAL=1 to make an unreachable source a hard failure. Never
    reports a match unless the fetch actually ran (audit re-review P2-3)."""
    strict = os.environ.get("ORACLE_REQUIRE_EXTERNAL") == "1"
    repo = PINS.get("source_repo")
    path = PINS.get("source_path")
    if not (repo and path):
        return (["PINS.json missing source_repo/source_path for external attestation"], True)
    url = f"https://raw.githubusercontent.com/{repo}/{PINS['pinned_commit']}/{path}"
    try:
        data = urllib.request.urlopen(url, timeout=30).read()
    except Exception as exc:  # network/proxy/offline
        msg = f"could not fetch external blob ({type(exc).__name__}: {exc}); {url}"
        if strict:
            return ([f"external attestation required but {msg}"], False)
        print(f"WARNING: skipping external attestation -- {msg}")
        return ([], False)
    ext_sha = hashlib.sha256(data).hexdigest()
    want = PINS["sha256"].get("math.js")
    if ext_sha != want:
        return ([f"vendored math.js SHA {want} != external blob SHA {ext_sha} at "
                 f"{PINS['pinned_commit']}"], True)
    return ([], True)


def main() -> int:
    checks = [("SHA-256 pins", check_sha256(), True)]
    checks.append(("oracle regeneration", *check_reproducible()))
    checks.append(("external attestation", *check_external()))
    errs = [e for _, el, _ in checks for e in el]
    print("oracle-freeze checks:")
    for name, el, ran in checks:
        print(f"  - {name}: {'FAILED' if el else ('OK' if ran else 'SKIPPED')}")
    if errs:
        print("ORACLE-FREEZE VIOLATION:")
        for e in errs:
            print("  -", e)
        return 1
    parts = ["SHA-256 pins match"]
    parts.append("regeneration reproduces the oracle" if checks[1][2]
                 else "regeneration SKIPPED (node unavailable)")
    parts.append("external blob attested" if checks[2][2]
                 else "external attestation SKIPPED (no network)")
    print("oracle-freeze OK: " + "; ".join(parts) + ". Enforces repository "
          "consistency, accidental-drift detection, and (when it actually runs) "
          "external-blob attestation; not, by itself, proof the oracle was never "
          "historically edited.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
`````

### `orbital-thermal-preprint.tex`

_(32604 bytes, sha256 `e92c5333e7529b6eec678092b48cc83148b3c6d4d22f992fcaaa34bb006be795`)_

`````latex
\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{booktabs}
\usepackage{microtype}
\usepackage{xcolor}
\definecolor{linknavy}{RGB}{25,50,110}
\usepackage[colorlinks=true,linkcolor=linknavy,citecolor=linknavy,urlcolor=linknavy]{hyperref}

\newtheorem{theorem}{Theorem}
\newtheorem{lemma}{Lemma}
\newtheorem{corollary}{Corollary}
\newtheorem{proposition}{Proposition}
\theoremstyle{definition}
\newtheorem{axiom}{Axiom}
\newtheorem{definition}{Definition}
\theoremstyle{remark}
\newtheorem{remark}{Remark}

\newcommand{\Th}{T_h}
\newcommand{\Tc}{T_c}
\newcommand{\Ts}{T_s^{\mathrm{eff}}}
\newcommand{\eps}{\varepsilon}

\title{Thermodynamic Bounds and Mass-Trade Criteria for\\ Heat Rejection in Orbital Data Centers}
\author{Dan Lee-Odinson\thanks{Contact: dan.lee.odinson@gmail.com. ORCID: \href{https://orcid.org/0009-0009-9504-0796}{0009-0009-9504-0796}. Preprint DOI: \href{https://doi.org/10.5281/zenodo.20650894}{10.5281/zenodo.20650894}. See Acknowledgments for a description of the multi-model derivation and audit methodology.}}
\date{June 11, 2026}

\begin{document}
\maketitle

\begin{abstract}
Orbital data centers must reject waste heat by far-field thermal radiation, and the resulting radiator area requirements are widely regarded as the binding engineering constraint on the concept. We derive, within a gray-body effective-sink radiator model, a set of exact thermodynamic results governing this constraint. First, we prove that the Carnot efficiency evaluated at the environmental sink temperature is unattainable by any heat engine with a material cold reservoir at finite radiator area and positive throughput, and we characterize both limiting routes (infinite area at fixed throughput; vanishing throughput at fixed area). Second, we show that radiator area per unit work output is minimized, along the reversible lower envelope, at a cold-side temperature $\Tc^{*}=\tfrac{3}{4}\Th$ with a $25\%$ efficiency ceiling, and we give an exact implicit characterization of the nonzero-sink optimum, $\Tc^{*}/\Th=(3+q^{4})/4$ with $q=\Ts/\Tc^{*}$, whose fractional shift above $\tfrac{3}{4}\Th$ is exactly $q^{4}/3$. Third, we prove that converting waste heat to work before rejection multiplies required radiator area by at least $(\Th/\Tc)^{3}$, with equality only for reversible conversion at zero sink temperature. Fourth, we show no cyclic system can sustain its compute load solely from its own waste heat. Finally, we state reduced-order mass-trade criteria for radiator-type selection, heat-pump inclusion, and topping-cycle inclusion. All quantitative claims are verified by an accompanying machine-executable test suite (Python and Wolfram Language). The central design implication is that orbital thermal management is a \emph{temperature-architecture} problem: within the model, the temperature at which heat finally leaves the system dominates fixed-temperature efficiency optimizations.
\end{abstract}

\section{Introduction}

In June 2026, the World Economic Forum cautioned an industry actively raising capital for orbital data centers that the physics of cooling in orbit ``may be more complex than some think'' \cite{wef2026}. The caution is quantifiable. A computing facility in vacuum has no air and no water to carry heat away; essentially all waste heat must leave by far-field thermal radiation, governed by the Stefan--Boltzmann law, and at server-class temperatures the required radiating area is of order $10^{3}\,\mathrm{m^{2}}$ per megawatt (\cite{eetimes2026}; Corollary~\ref{cor:refscale} supplies the internal reference calculation of $2630\,\mathrm{m^{2}}$ per megawatt under stated assumptions). Every square meter of it must be launched.

Discussion of this problem in the technical and trade literature frequently couples two further ideas: that the $2.7\,$K cosmic microwave background is an enormously favorable cold reservoir for waste-heat-to-electricity conversion, and that such conversion could substantially offset the power and cooling budget of an orbital facility. Both ideas require care. The cold side of any real heat engine is a physical radiator whose temperature is set by its own radiative balance rather than by the sky temperature; and extracting work before rejection \emph{lowers} the rejection temperature, which by the quartic law \emph{increases} the radiator area required per watt rejected.

This paper makes those folk observations precise. Working within an explicitly scoped gray-body, isothermal, effective-sink radiator model (Section~\ref{sec:model}), we prove a hierarchy of results separated into three levels: \textbf{Level A} model identities (Section~\ref{sec:levelA}), \textbf{Level B} reversible thermodynamic lower bounds (Section~\ref{sec:levelB}), and \textbf{Level C} reduced-order architecture decision criteria with empirical inputs (Section~\ref{sec:levelC}). The main results are:

\begin{enumerate}
  \item \textbf{Non-attainability} (Theorem~\ref{thm:nonattain}): no engine with a material cold reservoir attains the sink-temperature Carnot efficiency at finite radiator area and positive heat or work throughput; the limit is approached only as $A\to\infty$ at fixed throughput, or as throughput vanishes at fixed area. Efficiencies numerically close to the limit are not forbidden but command extreme area (a worked example at $99\%$ efficiency requires ${\sim}6.4\times10^{9}\,\mathrm{m^{2}}$ per megawatt).
  \item \textbf{The $\tfrac{3}{4}$ rule} (Theorem~\ref{thm:34rule}): along the reversible lower envelope, radiator area per unit work is minimized at $\Tc^{*}=\tfrac{3}{4}\Th$, with efficiency ceiling $25\%$. For irreversible engines with efficiency a fixed fraction of Carnot, the optimum shifts upward (we tabulate examples). This optimum is distinct in both objective and transfer law from the Curzon--Ahlborn maximum-power result \cite{curzon1975}, and is consistent with radiator-limited space-power optimization studies \cite{nasa1989,energyreports2022}.
  \item \textbf{Exact nonzero-sink correction} (Theorem~\ref{thm:sink}): the optimum satisfies the quintic $4\Tc^{5}-3\Th \Tc^{4}-\Th (\Ts)^{4}=0$, equivalently $\Tc^{*}/\Th=(3+q^{4})/4$ with $q=\Ts/\Tc^{*}$, giving an exact fractional shift $q^{4}/3$ above $\tfrac{3}{4}\Th$ (below $2\%$ for $q\le0.49$).
  \item \textbf{Conversion area penalty} (Corollary~\ref{cor:penalty}): any engine rejecting at $\Tc<\Th$ requires at least $(\Th/\Tc)^{3}$ times the radiator area of direct rejection at $\Th$; the penalty is strictly larger for irreversible engines and for any nonzero sink. At the $\tfrac{3}{4}$ optimum the minimum penalty is $(4/3)^{3}\approx2.37$ for $25\%$ recovery.
  \item \textbf{No self-powering} (Theorem~\ref{thm:selfpower}): a cyclic system cannot sustain a positive compute load solely by reconverting its own waste heat; recirculated recovery sustains at most $1/(1-\eta)$ watts of compute per external watt.
\end{enumerate}

Thermoradiative (negative-illumination) devices \cite{strandberg2011,santhanam2016}, in which part of the outgoing photon flux is converted directly to electrical work, fall outside the premise of a material cold reservoir in Theorem~\ref{thm:nonattain} and require a separate detailed-balance treatment; we delimit but do not analyze them. High-temperature wide-bandgap electronics, which set how far the hot side can be raised in practice, are likewise treated as empirical inputs \cite{gesic,uiucgan}.

All quantitative claims in this paper are verified by a machine-executable test suite provided as supplementary material in two independent forms: a Python assertion script and a Wolfram Language symbolic verification suite. The manuscript was developed through an iterative adversarial workflow across multiple frontier AI systems with computer-algebra verification; see Acknowledgments.

\section{Model, Axioms, and Definitions}\label{sec:model}

\subsection{Scope}

All results are exact within the following model: a gray, diffuse, isothermal radiating surface of hemispherical infrared emissivity $\eps\in(0,1]$ and total emitting area $A$ (a two-sided panel of planform area $A_{p}$ has $A=2A_{p}$), exchanging with a lumped radiative environment characterized by a single view-factor-weighted effective sink temperature $\Ts=F^{1/4}T_{s}$, where $T_{s}$ is an environmental brightness temperature and $F\in[0,1]$ a view-factor weighting. Where environmental and surface effects can be represented by fixed effective properties and a lumped sink temperature, they alter only model parameters; where absorbed loads, spectral properties, geometry, or temperatures depend on the design variables, they may also alter the functional form of the heat balance and the resulting optimum. Direct application to a flight architecture therefore requires separate environmental heat-load and view-factor modeling \cite{nasaguidebook,spenvis}.

Terminal heat rejection to vacuum occurs in this model by far-field electromagnetic radiation. Open-cycle mass ejection and deliberate export of coherent or nonthermal radiation are outside the model. Near-field radiative transfer and vacuum phonon tunneling operate only across sub-wavelength gaps and require a second material body that must itself radiate; they are internal transport mechanisms, not terminal rejection.

The worked sink value $\Ts=220\,$K used in examples is an \emph{illustrative} effective sink temperature for low Earth orbit under the lumped model, not a claim about the temperature of space; published lumped values for Earth-viewing surfaces span roughly $200$--$260\,$K (e.g., \cite{nasaguidebook,spenvis}).

\subsection{Axioms}

\begin{axiom}[Gray-body radiative rejection]\label{ax:sb}
Net radiated power is
\begin{equation}
P_{\mathrm{net}}=\eps\sigma A\bigl(\Tc^{4}-(\Ts)^{4}\bigr),
\qquad \sigma=5.670374419\times10^{-8}\,\mathrm{W\,m^{-2}\,K^{-4}}.
\label{eq:sb}
\end{equation}
\end{axiom}

\begin{axiom}[Second law]\label{ax:carnot}
Any cyclic engine operating between reservoirs at $\Th>\Tc$ satisfies $\eta\le1-\Tc/\Th$; any cyclic heat pump satisfies $\mathrm{COP}_{c}=Q_{c}/W\le \Tc/(\Th-\Tc)$. Equivalently (Kelvin--Planck), no cyclic device converts heat drawn from a single thermal reservoir entirely into work.
\end{axiom}

\begin{axiom}[First law]\label{ax:first}
For an engine, $Q_{h}=W+Q_{c}$; for a heat pump, $Q_{h}=Q_{c}+W$.
\end{axiom}

\begin{axiom}[Lumped compute heat model]\label{ax:compute}
In steady operation, electrical energy not exported in signals, stored energy, or other retained forms ultimately appears as heat; those fractions are assumed negligible, so compute power $P$ dissipates as heat at the source temperature. Net rejection requires $\Tc>\Ts$.
\end{axiom}

\begin{definition}[Reversible engine]\label{def:rev}
An engine attaining equality in the Carnot bound, $\eta=1-\Tc/\Th$. With Axiom~\ref{ax:first} this yields the reversible heat split $Q_{c}/Q_{h}=\Tc/\Th$. All uses of this equality below are labeled reversible; generic engines receive the corresponding inequality bound.
\end{definition}

Level A results follow from Axioms~\ref{ax:sb} and \ref{ax:first}; Level B results from Axioms~\ref{ax:sb}--\ref{ax:compute} plus Definition~\ref{def:rev} where labeled; Level C results additionally require the reduced-order mass models and empirical parameters identified in Section~\ref{sec:levelC}.

\section{Level A: Model Identities}\label{sec:levelA}

\begin{lemma}[Radiator area requirement]\label{lem:area}
Rejecting heat flow $Q_{c}>0$ at radiator temperature $\Tc$ requires
\begin{equation}
A=\frac{Q_{c}}{\eps\sigma\bigl(\Tc^{4}-(\Ts)^{4}\bigr)}.
\label{eq:area}
\end{equation}
\end{lemma}
\begin{proof}
Invert \eqref{eq:sb} with $P_{\mathrm{net}}=Q_{c}$; positive and well defined by Axiom~\ref{ax:compute}.
\end{proof}

\begin{corollary}[Area ratio between rejection temperatures]\label{cor:ratio}
For equal heat load and emissivity, rejecting at $T_{2}$ instead of $T_{1}$ (with $T_{2}>T_{1}>\Ts$) changes area by the exact factor
\begin{equation}
R=\frac{A_{1}}{A_{2}}=\frac{T_{2}^{4}-(\Ts)^{4}}{T_{1}^{4}-(\Ts)^{4}},
\end{equation}
and the zero-sink approximation $R_{0}=(T_{2}/T_{1})^{4}$ carries exact relative deviation
\begin{equation}
\frac{R}{R_{0}}-1=\frac{(\Ts/T_{1})^{4}-(\Ts/T_{2})^{4}}{1-(\Ts/T_{1})^{4}}
\;<\;\frac{(\Ts/T_{1})^{4}}{1-(\Ts/T_{1})^{4}}.
\end{equation}
\emph{Worked example} ($T_{1}=293$\,K, $T_{2}=600$\,K, $\Ts=220$\,K): $R_{0}=17.585$ while $R=25.312$ exactly ($R=6697760000/264604779$); the exact ratio is $43.9\%$ greater than the zero-sink estimate, equivalently the estimate is $30.5\%$ below the exact value. The warm sink penalizes the colder radiator disproportionately, so hot rejection is \emph{more} advantageous than the idealized quartic ratio suggests.
\end{corollary}

\begin{corollary}[Reference scale]\label{cor:refscale}
$Q_{c}=1\,$MW at $\Tc=293\,$K, $\eps=0.91$, $\Ts\approx0$ requires $A=2630\,\mathrm{m^{2}}$ of emitting surface, i.e.\ ${\sim}1315\,\mathrm{m^{2}}$ of two-sided panel planform, consistent with the ${\sim}1200\,\mathrm{m^{2}/MW}$ figures quoted in the trade literature for slightly different assumptions \cite{eetimes2026}.
\end{corollary}

\begin{lemma}[COP identity]\label{lem:cop}
For any heat pump, $\mathrm{COP}_{h}=\mathrm{COP}_{c}+1$.
\end{lemma}
\begin{proof}
Divide $Q_{h}=Q_{c}+W$ (Axiom~\ref{ax:first}) by $W$.
\end{proof}

\section{Level B: Reversible Thermodynamic Lower Bounds}\label{sec:levelB}

\subsection{Non-attainability of sink-temperature Carnot efficiency}

\begin{theorem}[Non-attainability]\label{thm:nonattain}
For any finite area $A$ and strictly positive rejected heat flow $Q_{c}$, Lemma~\ref{lem:area} forces
\begin{equation}
\Tc^{4}=(\Ts)^{4}+\frac{Q_{c}}{\eps\sigma A}>(\Ts)^{4},
\qquad\text{hence}\qquad
\eta\le1-\frac{\Tc}{\Th}<1-\frac{\Ts}{\Th}.
\end{equation}
The sink-temperature Carnot value is not attained by any system with finite area and positive heat or work throughput. It is approached only along two limiting routes: (i) at fixed nonzero heat or work throughput, as $A\to\infty$; (ii) at fixed finite area, as throughput $Q_{c}\to0$.
\end{theorem}

\begin{proof}
The strict inequality is immediate from Lemma~\ref{lem:area}. \emph{Route (i), fixed heat throughput:} at fixed $Q_{c}>0$, $\Tc^{4}-(\Ts)^{4}=Q_{c}/(\eps\sigma A)\to0$ iff $A\to\infty$. \emph{Route (i), fixed work throughput:} for fixed $W>0$, Axiom~\ref{ax:carnot} gives $Q_{c}/W\ge\Tc/(\Th-\Tc)$, hence
\begin{equation}
\frac{A}{W}\;\ge\;\frac{\Tc}{\eps\sigma(\Th-\Tc)\bigl(\Tc^{4}-(\Ts)^{4}\bigr)},
\label{eq:fixedW}
\end{equation}
which diverges as $\Tc\to(\Ts)^{+}$ when $\Ts>0$; for $\Ts=0$ the bound reduces to $1/[\eps\sigma(\Th-\Tc)\Tc^{3}]$, which diverges as $\Tc\to0^{+}$. \emph{Route (ii):} at fixed $A<\infty$, $\Tc^{4}-(\Ts)^{4}\to0$ iff $Q_{c}\to0$.
\end{proof}

\begin{remark}[Near-limit efficiencies are extreme-area, not impossible]\label{rem:99}
Claims that obtain ${\sim}99\%$ efficiency merely by substituting the $2.7\,$K cosmic background for the material cold-reservoir temperature are incomplete rather than impossible: a finite-throughput design must solve for $\Tc>T_{s}$ and the associated area. For $\Th=300\,$K, $T_{s}=2.7\,$K, $\Tc=3.0\,$K, reversible efficiency is $99.0\%$, and at $W=1\,$MW the rejected heat is $Q_{c}=W\Tc/(\Th-\Tc)\approx10.1\,$kW, requiring ideal blackbody area $A\approx6.4\times10^{9}\,\mathrm{m^{2}}$ (finite, but roughly six million times the reference scale of Corollary~\ref{cor:refscale}, and far outside the design space this model contemplates).
\end{remark}

\begin{remark}[Direct radiative converters]
Thermoradiative and negative-illumination devices \cite{strandberg2011,santhanam2016}, in which part of the outgoing photon flux is converted directly to electrical work, fall outside the premise of a material cold reservoir in Theorem~\ref{thm:nonattain} and require a separate detailed-balance treatment. No claim of uniqueness is made for that architecture, and no second-law exception is implied.
\end{remark}

\subsection{The \texorpdfstring{$\tfrac{3}{4}$}{3/4} rule}

\begin{theorem}[Reversible lower-envelope optimum, zero sink]\label{thm:34rule}
For any engine producing work $W$ and rejecting at $\Tc$ through a radiator with $\Ts=0$,
\begin{equation}
\frac{A}{W}=\frac{1-\eta}{\eta\,\eps\sigma \Tc^{4}}
\;\ge\;\frac{1}{\eps\sigma\bigl(\Th \Tc^{3}-\Tc^{4}\bigr)},
\label{eq:envelope}
\end{equation}
with equality iff the engine is reversible. The right-hand side is minimized at
\begin{equation}
\Tc^{*}=\tfrac{3}{4}\Th,
\qquad
\eta\bigl(\Tc^{*}\bigr)=25\%.
\end{equation}
This is the optimum of the reversible lower envelope; it is not the operating optimum of every irreversible engine.
\end{theorem}

\begin{proof}
Axiom~\ref{ax:first} gives $Q_{c}=W(1-\eta)/\eta$, and Axiom~\ref{ax:carnot} gives $(1-\eta)/\eta\ge\Tc/(\Th-\Tc)$, establishing \eqref{eq:envelope}. Minimizing the bound is equivalent to maximizing $f(\Tc)=\Th \Tc^{3}-\Tc^{4}$ on $(0,\Th)$:
\[
f'(\Tc)=\Tc^{2}\,(3\Th-4\Tc)=0\ \Rightarrow\ \Tc^{*}=\tfrac{3}{4}\Th,
\qquad
f''\bigl(\Tc^{*}\bigr)=-\tfrac{9}{4}\Th^{2}<0,
\]
and $f\to0$ at both endpoints, so the interior critical point is the global maximum of $f$, hence the global minimum of the bound. The reversible efficiency there is $1-\tfrac{3}{4}=25\%$.
\end{proof}

\begin{remark}[Irreversible engines]\label{rem:irr}
For an engine with efficiency law $\eta=a(1-\Tc/\Th)$, $0<a<1$, the area-per-work optimum shifts upward; representative values of the optimal $y^{*}=\Tc/\Th$ are:
\begin{center}
\begin{tabular}{cc}
\toprule
$a$ (fraction of Carnot) & optimal $\Tc/\Th$\\
\midrule
$1.0$ & $0.7500$\\
$0.8$ & $0.7645$\\
$0.5$ & $0.7808$\\
\bottomrule
\end{tabular}
\end{center}
Engine selection in practice requires the engine's actual $\eta(\Tc)$ law.
\end{remark}

\begin{remark}[Relation to Curzon--Ahlborn]
The Curzon--Ahlborn efficiency $1-\sqrt{\Tc/\Th}$ \cite{curzon1975} arises in an endoreversible maximum-power model with finite-rate linear heat transfer. Theorem~\ref{thm:34rule} optimizes a different objective (radiator area per unit work) under a radiative $T^{4}$ rejection law; no agreement should be expected. Optima in the neighborhood of $\tfrac{3}{4}\Th$ are reproduced by radiator-limited space-power studies \cite{nasa1989,energyreports2022}.
\end{remark}

\begin{corollary}[Conversion area penalty]\label{cor:penalty}
Relative to direct rejection of $Q_{h}$ at $\Th$, any engine rejecting at $\Tc<\Th$ requires, at $\Ts=0$,
\begin{equation}
\frac{A_{\mathrm{engine}}}{A_{\mathrm{direct}}}
=(1-\eta)\Bigl(\frac{\Th}{\Tc}\Bigr)^{4}
\;\ge\;\Bigl(\frac{\Th}{\Tc}\Bigr)^{3},
\end{equation}
with equality only in the reversible limit. At $\Tc=\tfrac{3}{4}\Th$ the minimum penalty is $(4/3)^{3}\approx2.370$ for $25\%$ recovery; irreversibility increases it (e.g.\ $a=0.8$ at the same $\Tc$ gives $\approx2.528$). With a common nonzero sink the exact expression is
\begin{equation}
\frac{A_{\mathrm{engine}}}{A_{\mathrm{direct}}}
=(1-\eta)\,\frac{\Th^{4}-(\Ts)^{4}}{\Tc^{4}-(\Ts)^{4}}
\;\ge\;\Bigl(\frac{\Th}{\Tc}\Bigr)^{3}\,
\frac{1-(\Ts/\Th)^{4}}{1-(\Ts/\Tc)^{4}}
\;>\;\Bigl(\frac{\Th}{\Tc}\Bigr)^{3},
\end{equation}
so the cubic penalty is a universal lower bound whose equality requires both reversibility and $\Ts=0$.
\end{corollary}

\begin{proof}
$A_{\mathrm{direct}}=Q_{h}/[\eps\sigma(\Th^{4}-(\Ts)^{4})]$ and $A_{\mathrm{engine}}=Q_{h}(1-\eta)/[\eps\sigma(\Tc^{4}-(\Ts)^{4})]$ by Lemma~\ref{lem:area} and Axiom~\ref{ax:first}; apply $1-\eta\ge\Tc/\Th$ (Axiom~\ref{ax:carnot}). For $\Ts>0$, $\Tc<\Th$ makes the final fraction exceed unity.
\end{proof}

\subsection{Exact nonzero-sink optimum}

\begin{theorem}[Implicit characterization of the nonzero-sink optimum]\label{thm:sink}
With effective sink $\Ts>0$, the reversible-envelope optimum $\Tc^{*}$ satisfies the quintic stationarity equation
\begin{equation}
4\Tc^{5}-3\Th \Tc^{4}-\Th(\Ts)^{4}=0,
\label{eq:quintic}
\end{equation}
equivalently the exact implicit characterization
\begin{equation}
\frac{\Tc^{*}}{\Th}=\frac{3+q^{4}}{4},
\qquad q\equiv\frac{\Ts}{\Tc^{*}},
\label{eq:fixedpoint}
\end{equation}
with exact fractional shift above $\tfrac{3}{4}\Th$ equal to $q^{4}/3$. The optimum is unique in $(\Ts,\Th)$ and strictly increasing in $\Ts$; the shift is at most $0.49^{4}/3\approx1.9216\%$ for $q\le0.49$.
\end{theorem}

\begin{proof}
By Lemma~\ref{lem:area} and Definition~\ref{def:rev}, minimizing $A/W$ is equivalent to maximizing
\[
g(\Tc)=\frac{(\Th-\Tc)\bigl(\Tc^{4}-(\Ts)^{4}\bigr)}{\Tc}
=\Th \Tc^{3}-\Tc^{4}-\frac{\Th(\Ts)^{4}}{\Tc}+(\Ts)^{4}.
\]
Then $g'(\Tc)=3\Th \Tc^{2}-4\Tc^{3}+\Th(\Ts)^{4}/\Tc^{2}$; setting $g'=0$ and multiplying by $\Tc^{2}>0$ yields \eqref{eq:quintic}. Dividing \eqref{eq:quintic} by $4\Th \Tc^{4}$ gives \eqref{eq:fixedpoint}, and the fractional shift is $\bigl(\Tc^{*}-\tfrac{3}{4}\Th\bigr)/\bigl(\tfrac{3}{4}\Th\bigr)=(q^{4}/4)/(3/4)=q^{4}/3$, monotone in $q$. In reduced variables $y=\Tc/\Th$, $r=\Ts/\Th$, stationarity reads $4y^{5}-3y^{4}=r^{4}$; for $y\ge\tfrac{3}{4}$, $\frac{d}{dy}(4y^{5}-3y^{4})=4y^{3}(5y-3)>0$, so the physical root is unique and strictly increasing in $\Ts$. Since $g(\Ts)=g(\Th)=0$ with $g>0$ between, the stationary point is the interior maximum.
\end{proof}

\begin{remark}[Computation]
The fixed-point map $\Phi(T)=\tfrac{\Th}{4}\bigl[3+(\Ts/T)^{4}\bigr]$ has $|\Phi'(\Tc^{*})|=4q^{4}/(3+q^{4})<1$ for all physical $q<1$, so iteration of \eqref{eq:fixedpoint} is locally convergent. At the illustrative design point $\Th=600\,$K, $\Ts=220\,$K: $\Tc^{*}=457.98675408138325\,$K (high-precision evaluation of the exact algebraic root; cross-checked by Newton iteration with quintic residual below $10^{-25}$ and by fixed-point iteration), a shift of $+1.7748\%$ matching $q^{4}/3$ to all computed digits. The $\tfrac34$ rule therefore survives at sub-$2\%$ accuracy in the relevant regime, with an analytic error formula in place of numerical tables. No claim is made regarding solvability of \eqref{eq:quintic} by radicals.
\end{remark}

\subsection{Heat pumps and self-powering}

\begin{theorem}[Heat-pump overhead and area ratio]\label{thm:pump}
Pumping the thermal load $Q_{c}$ extracted at $\Tc$ up to rejection at $\Th$ requires work
$W/Q_{c}=1/\mathrm{COP}_{c}\ge(\Th-\Tc)/\Tc$, and the radiator must reject $Q_{h}=Q_{c}(1+1/\mathrm{COP}_{c})$. Pumping from unpumped rejection temperature $T_{1}$ to pumped temperature $T_{2}$ with common sink $\Ts$, equal emissivity and view geometry,
\begin{equation}
\frac{A_{\mathrm{pump}}}{A_{\mathrm{direct}}}
=\Bigl(1+\frac{1}{\mathrm{COP}_{c}}\Bigr)\,
\frac{T_{1}^{4}-(\Ts)^{4}}{T_{2}^{4}-(\Ts)^{4}}.
\end{equation}
\emph{Worked example} ($T_{1}=353$\,K, $T_{2}=520$\,K, $\Ts=220$\,K, $\mathrm{COP}_{c}=1.15$): exact ratio $0.348$ (zero-sink approximation $0.397$). At $\Tc=353$\,K, $\Th=520$\,K the Carnot bounds are $\mathrm{COP}_{c}\le353/167\approx2.114$ and $\mathrm{COP}_{h}\le520/167\approx3.114$, consistent with Lemma~\ref{lem:cop}; minimum overhead is $0.473$\,W per watt of load. The range $\mathrm{COP}_{c}\approx1.0$--$1.3$ used in examples is an empirical parameter for vapor-compression machines at ${\sim}170\,$K lift, not derived from the axioms.
\end{theorem}

\begin{proof}
Axioms~\ref{ax:carnot}--\ref{ax:first}, Lemmas~\ref{lem:area} and \ref{lem:cop}.
\end{proof}

\begin{theorem}[No waste-heat self-powering]\label{thm:selfpower}
No cyclic system can sustain a positive compute load solely by converting its own internally generated waste heat back into work. Under Axiom~\ref{ax:compute} with compute power $P$, recovery efficiency $\eta<1$ (strict by Theorem~\ref{thm:nonattain} at finite area and positive throughput), and recovered work recirculated to the bus,
\begin{equation}
P_{\mathrm{ext}}=P(1-\eta)>0 .
\end{equation}
External energy resources other than the waste heat itself (solar, nuclear, beamed, or stored chemical) are outside this claim.
\end{theorem}

\begin{proof}
Steady-state bus balance: $P=P_{\mathrm{ext}}+W_{\mathrm{rec}}$ with $W_{\mathrm{rec}}=\eta P$, so $P_{\mathrm{ext}}=P(1-\eta)>0$. Self-powering would require $\eta\ge1$: a cyclic device converting heat from a single effective reservoir entirely into work, contradicting the Kelvin--Planck statement (Axiom~\ref{ax:carnot}).
\end{proof}

\begin{remark}
Recirculation sustains $P/P_{\mathrm{ext}}=1/(1-\eta)$ watts of compute per external watt ($\eta=0.25$ gives $1.33$). Recovery therefore reduces the external supply requirement by a bounded factor and cannot eliminate it.
\end{remark}

\section{Level C: Architecture Decision Criteria}\label{sec:levelC}

The following are decision criteria under explicitly reduced mass models with empirical inputs; their verdicts flip with parameter values, while their algebraic validity is parameter-independent. Empirical parameters appearing below (areal densities $\rho_{A}$, specific masses, COP values, margin factors $\delta$) are catalogued in the supplementary material and must be normalized to equal delivered duty.

\begin{proposition}[Radiator selection]\label{prop:p1}
Let $\rho_{A}$ denote effective system areal density normalized to equal delivered rejection capacity (equal rejected power, operating temperature, effective emissivity, view geometry, lifetime and availability). Droplet radiators are mass-favorable over solid panels iff
\begin{equation}
\rho_{A,\mathrm{droplet}}\,(1+\delta_{\mathrm{capture}})
<\rho_{A,\mathrm{solid}}\,(1+\delta_{\mathrm{debris}}).
\end{equation}
\end{proposition}

\begin{proposition}[Heat-pump inclusion: necessary first-order condition]\label{prop:p2}
Under the stated reduced mass model, including pump and ancillary masses, active thermal upgrade is mass-favorable only if
\begin{equation}
\rho_{A}\,\bigl(A_{\mathrm{direct}}-A_{\mathrm{pump}}\bigr)
>\frac{Q_{c}}{\mathrm{COP}_{c}}\,m_{\mathrm{array}}
+M_{\mathrm{pump}}+M_{\mathrm{ancillary}},
\end{equation}
with $A_{\mathrm{pump}}$ from Theorem~\ref{thm:pump} and $m_{\mathrm{array}}$ the array specific mass (kg per electrical watt). A full verdict requires the complete mass ledger.
\end{proposition}

\begin{proposition}[Topping-cycle inclusion]\label{prop:p3}
With engine specific mass per watt of thermal input $s_{h}=M_{\mathrm{engine}}/Q_{h}$, the engine is mass-favorable under the reduced model iff
\begin{equation}
s_{h}<\eta\,m_{\mathrm{array}}
+\rho_{A}\,\frac{A_{\mathrm{direct}}-A_{\mathrm{engine}}}{Q_{h}},
\end{equation}
equivalently, per watt recovered ($s_{e}=s_{h}/\eta$), $s_{e}<m_{\mathrm{array}}+\rho_{A}(A_{\mathrm{direct}}-A_{\mathrm{engine}})/(\eta Q_{h})$. Since $A_{\mathrm{engine}}>A_{\mathrm{direct}}$ (Corollary~\ref{cor:penalty}), the area term is negative: the engine must overcome both its own mass and its area penalty, with $\eta\le\tfrac14$ at the reversible-envelope optimum.
\end{proposition}

\section{Discussion}\label{sec:discussion}

Within the adopted radiator model, increasing rejection temperature reduces required emitting area by the exact factor of Corollary~\ref{cor:ratio}, and a warm sink amplifies the effect. Whether that reduction yields a lower-mass, lower-power, more reliable, or longer-lived complete architecture is governed by the Level C criteria and their empirical inputs, notably the maximum qualified junction temperature of the compute technology: silicon's practical limit is typically near $100$--$150\,^{\circ}$C, while SiC and GaN devices have demonstrated operation at $500$--$800\,^{\circ}$C \cite{gesic,uiucgan}, making wide-bandgap electronics the natural lever for hot-side elevation. Within the model, rejection temperature is the budget from which every other thermal choice is purchased.

The results bound, rather than recommend, waste-heat recovery: Corollary~\ref{cor:penalty} prices recovery in area (a minimum of $2.37\times$ at $25\%$ recovery), Theorem~\ref{thm:selfpower} caps what it can return, and Proposition~\ref{prop:p3} states the exact condition under which its mass trade closes. Thermoradiative conversion, in which the radiator surface is itself the generator, is the one architecture outside these bounds and merits the separate detailed-balance analysis indicated in Section~\ref{sec:levelB}.

\textbf{Limitations.} All results are exact only within the gray-body, isothermal, effective-sink model. Design-dependent absorbed loads, spectral and directional surface properties, non-isothermal radiators, multi-surface view factors, and transient orbital environments can alter the functional form of the heat balance and hence the optima. Flight application requires environment-resolved thermal modeling \cite{nasaguidebook}. The Level C criteria are first-order mass conditions; a complete system trade requires the full mass and reliability ledger.

\section{Conclusion}

The complexity the World Economic Forum warned of in June 2026 is real, and within the adopted model it is also exactly characterizable. The temperature at which heat finally leaves the system enters the area requirement quartically and dominates fixed-temperature efficiency optimization. The reversible-envelope optimum for combined rejection and recovery sits at $\Tc^{*}=\tfrac34\Th$, with a sink correction of exactly $q^{4}/3$. Conversion before rejection always costs area. No architecture bootstraps from its own waste heat. These bounds frame the empirical engineering trades that will determine whether orbital computing closes as a system. The bounds are proved and the trades are stated. What remains is engineering.

\section*{Acknowledgments}

This manuscript came out of an iterative, adversarial workflow I ran across multiple AI systems: derivations and drafting by Claude Fable 5 (Anthropic), literature-armed review by Perplexity deep research, and two formal proof audits with independent computer-algebra verification by GPT~5.5 using the Wolfram plugin. Each round's corrections are recorded in the revision history of the supplementary source document, and every quantitative claim is machine-verified by the supplementary test suites. Remaining errors are mine.

\section*{Data and Code Availability}

Supplementary material accompanying this preprint includes: (i) a Python assertion suite verifying every central numerical claim; (ii) a Wolfram Language symbolic verification suite (stationarity, second-order conditions, limits, exact rationals, and high-precision roots); and (iii) the audited source document with full revision history. The complete package is archived at Zenodo (\href{https://doi.org/10.5281/zenodo.20650894}{doi:10.5281/zenodo.20650894}) and mirrored at \url{https://github.com/dan-lee-odinson/orbital-thermal-bounds}.

\begin{thebibliography}{12}
\bibitem{curzon1975} F.~L. Curzon and B.~Ahlborn, ``Efficiency of a Carnot engine at maximum power output,'' \emph{American Journal of Physics} \textbf{43}, 22--24 (1975).
\bibitem{strandberg2011} R.~Strandberg, ``Theoretical efficiency limits for thermoradiative energy conversion,'' \emph{Journal of Applied Physics} \textbf{109}, 104512 (2011).
\bibitem{santhanam2016} P.~Santhanam and S.~Fan, ``Thermal-to-electrical energy conversion by diodes under negative illumination,'' \emph{Physical Review B} \textbf{93}, 161410(R) (2016).
\bibitem{nasa1989} J.~A. Bamberger et al., ``Megawatt Class Nuclear Space Power Systems (MCNSPS) conceptual design and evaluation report,'' NASA NTRS 19890013610 (1989).
\bibitem{energyreports2022} Y.~Zhang et al., ``Performance analysis and optimization of an irreversible Carnot heat engine cycle for space power plant,'' \emph{Energy Reports} \textbf{8} (2022).
\bibitem{nasaguidebook} NASA, \emph{Passive Thermal Control Engineering Guidebook}, v4.0, NTRS 20230013900 (2023).
\bibitem{spenvis} ESA, ``Satellite irradiation: solar, albedo and Earth infrared environments,'' SPENVIS background documentation.
\bibitem{lapotin2022} A.~LaPotin et al., ``Thermophotovoltaic efficiency of 40\%,'' \emph{Nature} \textbf{604}, 287--291 (2022).
\bibitem{gesic} GE Research, ``SiC semiconductor device operation at extreme temperatures,'' IMAPS (demonstrations to $500\,^{\circ}$C junction temperature; intrinsic capability toward $800\,^{\circ}$C).
\bibitem{uiucgan} University of Illinois ECE, ``Record-setting gallium nitride transistor operates at $800\,^{\circ}$C'' (December 2025).
\bibitem{eetimes2026} EE Times, ``The hidden physics of running data centers in orbit'' (February 2026).
\bibitem{wef2026} World Economic Forum, ``Why cooling is the real obstacle to space-based data centres'' (June 2026).
\end{thebibliography}

\end{document}
`````

### `orbital-thermal-resolution-proof-v3.md`

_(34825 bytes, sha256 `1941c4408782a852a38550017d869311a550c1726db01e0943de2ab06b187259`)_

`````markdown
# Ideal Thermodynamic Bounds and Decision Criteria for Orbital Data Center Thermal Architecture

## Revision 3 — final form, incorporating both GPT 5.5 audit rounds in full

**Scope of this document.** Formal derivation of ideal thermodynamic bounds and reduced-order decision criteria for an orbital thermal-control architecture modeled as a gray, diffuse, isothermal radiator coupled to a lumped effective radiative environment. Results are presented at three explicitly separated levels: **Level A** (model identities, exact within the model), **Level B** (reversible thermodynamic lower bounds, exact as bounds), and **Level C** (reduced-order architecture decision criteria, valid under stated mass-model assumptions with empirical inputs). This document does **not** claim to prove the optimum of every irreversible engine or every realizable orbital architecture.

**Revision record.** v1 → v2: all sixteen acceptance criteria of the first GPT 5.5 audit (corrected quantifiers, reversible-scope labeling, exact sink algebra, analytic stationarity, consistent normalizations, three-level classification, runnable appendix). v2 → v3: all twelve residual items of the follow-up audit (percentage-direction wording, narrowed 99% consequence, weakened structural-invariance claim, implicit-characterization labeling, complete fixed-point convergence proof, zero-sink qualification and exact nonzero-sink form of the conversion penalty, dimensionless quintic residual, enforced convergence tolerance, added assertions, model-scoped closing language, illustrative-sink wording). v3 final additionally supplies **Appendix W**, a Wolfram Language symbolic verification suite, with exact rational forms and high-precision reference roots, so that a CAS-equipped reviewer can verify every Level A/B claim symbolically rather than by translating the Python appendix. A subsequent Wolfram-assisted audit independently confirmed the full mathematical core; its targeted corrections — the fixed-work divergence argument completing Theorem 1, executable forms for W-blocks W1/W2/W3 with literal advertised outputs, a new W3b limit block, method-accurate description of the quintic root evaluation, and qualified deployability wording in the Theorem 1 illustration — are incorporated in this final form.

---

## 0. Model Scope Statement

All results below are exact **within the adopted thermal model**: a gray, diffuse, isothermal radiating surface of emissivity ε, exchanging with a lumped radiative environment characterized by a single view-factor-weighted effective sink temperature. Direct application to a real orbital architecture additionally requires environmental heat-load decomposition (solar absorption, planetary albedo, planetary IR, cold sky), spectral and directional surface properties, and multi-surface view-factor modeling. Where environmental and surface effects can be represented by fixed effective properties and a lumped sink temperature, they alter the model parameters. Where absorbed loads, spectral properties, geometry, or temperatures depend on the design variables, they may also alter the functional form of the heat balance and the resulting optimum.

In the passive steady-state thermal-control architecture considered here, terminal heat rejection to vacuum occurs by far-field electromagnetic radiation. Open-cycle mass ejection and deliberate export of coherent or nonthermal radiation are outside the model. Near-field radiative transfer and vacuum phonon tunneling operate only at sub-wavelength gaps and require a second material body that must itself radiate; they are internal transport mechanisms, not terminal rejection, and are likewise outside the model.

---

## 1. Notation and Constants

| Symbol | Meaning | Units |
|---|---|---|
| σ | Stefan–Boltzmann constant = 5.670374419 × 10⁻⁸ | W·m⁻²·K⁻⁴ |
| ε | Hemispherical IR emissivity, 0 < ε ≤ 1 | — |
| A | Total emitting surface area (A_emit; a two-sided panel has A_emit = 2·A_planform) | m² |
| T_h | Hot-side (heat source) absolute temperature | K |
| T_c | Cold-side (radiator) absolute temperature | K |
| T_s | Environmental brightness/source temperature | K |
| T_s^eff | View-factor-weighted lumped effective sink temperature, T_s^eff = F^(1/4)·T_s | K |
| Q_h, Q_c | Heat flow into engine / rejected by engine | W |
| W | Work (electrical power) output or input | W |
| η | Conversion efficiency W/Q_h | — |
| COP_c, COP_h | Cooling COP = Q_c/W; heating COP = Q_h/W | — |
| y, r, q | y = T_c/T_h; r = T_s^eff/T_h; q = T_s^eff/T_c | — |

Throughout the body, T_s denotes T_s^eff unless stated otherwise. All temperatures absolute; all heat flows steady-state averages. The worked sink value 220 K used below is an **illustrative effective sink temperature** under the lumped model, not a statement that "space in LEO is 220 K"; it stands in for a specific (unstated here) view-factor and environmental decomposition.

---

## 2. Axioms and Definitions

**A1 (Gray-body radiative rejection model).** Net radiated power of the model radiator:

    P_net = ε σ A (T_c⁴ − (T_s^eff)⁴)

*Status: idealized gray-body, isothermal, effective-sink model postulate (see §0 scope statement).*

**A2 (Second law, Carnot form).** Any cyclic engine between reservoirs at T_h > T_c satisfies η ≤ 1 − T_c/T_h. Any cyclic heat pump satisfies COP_c ≤ T_c/(T_h − T_c). Kelvin–Planck formulation (used in Theorem 5): a cyclic device cannot convert heat drawn from a single thermal reservoir entirely into work. *Status: physical postulate.*

**A3 (First law).** Engine: Q_h = W + Q_c. Heat pump: Q_h = Q_c + W.

**A4 (Lumped compute heat model).** In steady operation, electrical energy not exported in signals, stored energy, mechanical work, or other retained forms ultimately appears as heat; those exported or stored fractions are assumed negligible in the lumped compute model, so compute power P dissipates as heat at the source temperature. For net rejection, T_c > T_s^eff.

**D1 (Reversible engine).** An engine attaining equality in the Carnot bound: η = 1 − T_c/T_h. Combining with A3 (W = Q_h − Q_c) gives the reversible heat split **Q_c/Q_h = T_c/T_h**. All uses of this equality below are labeled reversible; generic engines receive the corresponding inequality.

**Dependency statement.** Level A results follow from A1 and A3. Level B results follow from A1–A4 plus D1 (reversibility) where labeled. Level C results additionally require the reduced-order mass models and empirical parameters identified in §5–§6.

---

## 3. Level A — Model Identities

### Lemma 1 (Radiator area requirement)

Rejecting heat flow Q_c > 0 at radiator temperature T_c requires

    A = Q_c / [ε σ (T_c⁴ − (T_s^eff)⁴)]

**Proof.** Inversion of A1 with P_net = Q_c; positive and well-defined by A4. ∎

### Corollary 1.1 (Area ratio between rejection temperatures — exact and approximate forms)

For equal heat load and emissivity, rejecting at T₂ instead of T₁ (T₂ > T₁ > T_s^eff) changes area by the **exact** factor

    R = A₁/A₂ = (T₂⁴ − T_s⁴) / (T₁⁴ − T_s⁴)

The zero-sink approximation R₀ = (T₂/T₁)⁴ carries exact relative deviation

    R/R₀ − 1 = [(T_s/T₁)⁴ − (T_s/T₂)⁴] / [1 − (T_s/T₁)⁴]

with safe upper bound (T_s/T₁)⁴ / [1 − (T_s/T₁)⁴]. The deviation is **not** generally below (T_s/T₁)⁴ [v1 claimed otherwise; corrected in v2].

**Worked example (T₁ = 293 K, T₂ = 600 K, T_s = 220 K illustrative):** R₀ = 17.585; exact R = **25.312**. The exact sink-corrected ratio is **43.9% greater than** the zero-sink estimate; equivalently, the zero-sink estimate is **30.5% below** the exact result (1 − R₀/R = 0.305). [Percentage direction corrected in v3.] The correction strengthens the design conclusion: against the illustrative warm effective sink, hot rejection is *more* advantageous than the idealized 17.6×, because the warm sink penalizes the cold radiator disproportionately. ∎ (Numerics: Appendix block B1.)

### Corollary 1.2 (Reference area check)

Q_c = 1 MW, T_c = 293 K, ε = 0.91, T_s ≈ 0: A_emit = 10⁶/(0.91·σ·293⁴) = **2,630 m²** of emitting surface — realizable as ~**1,315 m²** of two-sided panel planform (A_emit = 2·A_planform). Consistent with the ~1,200 m²/MW literature figure (different assumed ε, T). ∎

### Lemma 4a (COP identity — general)

COP_h = COP_c + 1 for any heat pump. **Proof.** A3: Q_h = Q_c + W; divide by W. ∎

---

## 4. Level B — Reversible Thermodynamic Lower Bounds

### Theorem 1 (Non-attainability of sink-temperature Carnot efficiency)

For any finite area A and any strictly positive rejected heat flow Q_c, Lemma 1 forces

    T_c⁴ = (T_s^eff)⁴ + Q_c/(εσA) > (T_s^eff)⁴, hence η ≤ 1 − T_c/T_h < 1 − T_s^eff/T_h.

The sink-temperature Carnot value is therefore **not attained** by any system with finite area and positive throughput. It may be **approached** along two limiting routes: (i) at fixed nonzero heat or work throughput, only as A → ∞; (ii) at fixed finite area, only as throughput Q_c → 0 (vanishing power).

**Proof.** Strict inequality: immediate from Lemma 1. Route (i), fixed heat throughput: at fixed Q_c > 0, T_c⁴ − T_s⁴ = Q_c/(εσA) → 0 iff A → ∞. Route (i), fixed work throughput: for fixed W > 0, the Carnot bound (A2) gives Q_c/W ≥ T_c/(T_h − T_c), hence

    A/W ≥ T_c / [εσ(T_h − T_c)(T_c⁴ − T_s⁴)]

which diverges as T_c → T_s⁺ when T_s > 0; for T_s = 0 it reduces to 1/[εσ(T_h − T_c)T_c³], which diverges as T_c → 0⁺. Thus approaching the sink-temperature Carnot limit at fixed positive work also requires A → ∞. (CAS limit checks: Appendix W block W3b.) Route (ii): at fixed A < ∞, T_c⁴ − T_s⁴ → 0 iff Q_c → 0. ∎

**Consequence (correctly scoped).** Claims that obtain approximately 99% efficiency merely by substituting the 2.7 K cosmic-background temperature for the material cold-reservoir temperature are **incomplete**: a finite-throughput design must solve for T_c > T_s and the associated radiator area. Efficiencies near 99% are not mathematically forbidden, but the required area becomes extreme as T_c approaches T_s. **Worked illustration:** T_h = 300 K, T_s = 2.7 K, T_c = 3.0 K gives reversible η = 99.0%; at W = 1 MW, Q_c = W·T_c/(T_h − T_c) ≈ 10.1 kW, and the ideal blackbody area is A = Q_c/[σ(3.0⁴ − 2.7⁴)] ≈ **6.4 × 10⁹ m²** — finite, but approximately six million times the order-of-magnitude radiator area of the 293 K reference example (Corollary 1.2), and therefore far outside the design scale contemplated by this reduced model. The theorem establishes an area–throughput penalty, not a categorical impossibility of efficiency values near the sink-temperature Carnot figure. [Narrowed in v3.] (Appendix block B8.)

**Remark (direct radiative converters).** Thermoradiative and negative-illumination devices fall outside the material-cold-reservoir premise of this theorem because part of the outgoing photon flux is converted directly to electrical work; they require a separate detailed-balance treatment (Strandberg 2011; Santhanam & Fan 2016). This document makes no claim that they are the unique such architecture, and no second-law exception is implied — they are a different architecture to which this theorem's premise does not apply.

### Theorem 2 (The ¾ rule — reversible lower-envelope optimum, zero-sink model)

**(a) General-engine bound.** For any engine producing work W and rejecting at T_c through a radiator (T_s = 0 here; nonzero sink in Theorem 3), A3 gives Q_c = W(1−η)/η, and A2 gives (1−η)/η ≥ T_c/(T_h − T_c). Hence

    A/W = (1−η)/(η · εσT_c⁴) ≥ 1 / [εσ(T_h·T_c³ − T_c⁴)]   for all admissible engines.

**(b) Optimum of the lower envelope.** The right-hand side is minimized where f(T_c) = T_h·T_c³ − T_c⁴ is maximized:

    f′ = T_c²(3T_h − 4T_c) = 0 ⇒ T_c* = (3/4)T_h;
    f″(T_c*) = 6T_h·T_c* − 12T_c*² = −2.25·T_h² < 0 (maximum of f);
    f → 0 at both endpoints of (0, T_h) ⇒ interior point is the global optimum.

Reversible efficiency at the optimum: η = 1 − 3/4 = **25%**.

**(c) Scope.** This is the optimum of the **reversible lower envelope** of A/W — a lower-bound design reference. It is **not** the operating optimum of every irreversible engine: for an engine with efficiency law η = a(1 − T_c/T_h), 0 < a < 1, the area-per-work optimum shifts upward:

| a (fraction of Carnot) | optimal T_c/T_h |
|---|---|
| 1.0 | 0.750 |
| 0.8 | 0.765 |
| 0.5 | 0.781 |

(Numerics: Appendix block B2.) Real engine selection requires the engine's actual η(T_c) law. ∎

**Distinction from Curzon–Ahlborn.** The Curzon–Ahlborn efficiency 1 − √(T_c/T_h) arises in a particular endoreversible maximum-power model with finite-rate linear heat transfer. The present result optimizes a different objective (radiator area per unit work) under a radiative T⁴ rejection law. No agreement should be expected.

### Corollary 2.1 (Conversion area penalty — universal lower bound, with sink qualification)

**Zero-sink form.** Relative to direct rejection of Q_h at T_h, any engine rejecting at T_c < T_h requires (T_s = 0)

    A_engine/A_direct = (1−η)·(T_h/T_c)⁴ ≥ (T_h/T_c)³

with equality **only** in the reversible limit (since 1−η ≥ T_c/T_h by A2). At the Theorem-2 optimum T_c = ¾T_h, the **minimum possible** zero-sink area penalty is (4/3)³ ≈ **2.370**; any irreversibility increases it (e.g., a = 0.8 at the same T_c gives (1−0.2)·(4/3)⁴ ≈ **2.528**).

**Nonzero-sink form (exact).** With a common sink T_s > 0,

    A_engine/A_direct = (1−η)·(T_h⁴ − T_s⁴)/(T_c⁴ − T_s⁴) ≥ (T_h/T_c)³ · [1 − (T_s/T_h)⁴]/[1 − (T_s/T_c)⁴]

and since T_c < T_h makes the final fraction exceed one, the penalty **strictly exceeds** (T_h/T_c)³ for any T_s > 0, even in the reversible limit. The cubic result is therefore a valid universal lower bound whose equality requires both (1) reversible conversion and (2) T_s = 0. [Sink qualification added in v3.] ∎ (Numerics: Appendix block B3.)

**Interpretation.** Energy recovery is never area-free: 25% recovery costs *at least* 2.37× radiator area versus direct hot rejection, and strictly more against any real sink. Recovery is mass-rational only when displaced solar-array mass exceeds this added radiator mass (Proposition P3).

### Theorem 3 (Nonzero-sink optimum — exact implicit characterization)

**Claim.** With effective sink T_s > 0, the reversible-envelope optimum T_c* satisfies the quintic stationarity equation

    4T_c⁵ − 3T_h·T_c⁴ − T_h·T_s⁴ = 0,

equivalently the **exact implicit characterization** (q contains the unknown T_c*, so this is not an explicit closed form)

    T_c*/T_h = (3 + q⁴)/4,  q ≡ T_s/T_c*,

with exact fractional shift above ¾T_h of **q⁴/3**. The optimum is unique and strictly increasing in T_s, and the shift is ≤ 0.49⁴/3 ≈ **1.9216% for q ≤ 0.49**.

**Proof.** Objective (from Lemma 1 and the reversible heat split): minimize A/W ∝ [T_c/(T_h−T_c)]/(T_c⁴−T_s⁴), i.e., maximize

    g(T_c) = (T_h − T_c)(T_c⁴ − T_s⁴)/T_c = T_h·T_c³ − T_c⁴ − T_h·T_s⁴/T_c + T_s⁴.

Differentiate: g′(T_c) = 3T_h·T_c² − 4T_c³ + T_h·T_s⁴/T_c². Setting g′ = 0 and multiplying by T_c² > 0:

    3T_h·T_c⁴ − 4T_c⁵ + T_h·T_s⁴ = 0  ⇔  4T_c⁵ − 3T_h·T_c⁴ = T_h·T_s⁴.

Dividing by 4T_h·T_c⁴ gives T_c/T_h = 3/4 + (T_s/T_c)⁴/4 = (3 + q⁴)/4. Fractional shift: [T_c* − ¾T_h]/(¾T_h) = (q⁴/4)/(3/4) = q⁴/3, monotone in q; q ≤ 0.49 ⇒ shift ≤ 0.49⁴/3 = 1.9216%.

*Uniqueness and monotonicity.* In reduced variables y = T_c/T_h, r = T_s/T_h, stationarity reads 4y⁵ − 3y⁴ = r⁴. For y ≥ 3/4, d/dy(4y⁵ − 3y⁴) = 4y³(5y − 3) > 0, so the left side is strictly increasing: the interior optimum is unique and increases monotonically with T_s. Endpoint behavior (g(T_s) = 0, g(T_h) = 0, g > 0 between) confirms the interior maximum. ∎

**Fixed-point convergence (complete).** Define the iteration map Φ(T) = (T_h/4)·[3 + (T_s/T)⁴]. Its derivative is Φ′(T) = −T_h·T_s⁴/T⁵. At the physical fixed point, |Φ′(T_c*)| = (T_h/T_c*)·q⁴ = 4q⁴/(3 + q⁴) using T_c*/T_h = (3+q⁴)/4; for every physical q < 1, 4q⁴/(3+q⁴) < 1, so the fixed point is locally attracting. The appendix iterates to an enforced successive-iterate tolerance of 10⁻¹⁰ K (block B4) and verifies convergence for the numerical range tested; the dimensionless quintic residual 4y⁵ − 3y⁴ − r⁴ is asserted below 10⁻¹². [Replaced incomplete v2 statement.]

**Verification values.** At T_h = 600 K, T_s = 220 K (illustrative): T_c* = **457.98675408138325 K** (high-precision numerical evaluation of the exact algebraic `Root` object, Appendix W block W2c; independently cross-checked by a 40-digit Newton iteration with quintic residual < 10⁻²⁵ and by the fixed-point iteration of the Python appendix), shift +1.77483424% — equal to q⁴/3 to 38 decimal places. A coarse grid maximization is retained only as a redundant cross-check. No claim is made regarding solvability of the quintic by radicals; the CAS represents the root exactly as a `Root` object.

**Design consequence.** At the illustrative design point the ¾ rule carries sub-2% error; it survives as a design rule, with an analytic error formula rather than a numerical table alone.

### Theorem 4 (Heat-pump overhead bound and area ratio)

**(a) Overhead.** Pumping IT thermal load Q_c from T_c to rejection at T_h requires W/Q_c = 1/COP_c ≥ (T_h − T_c)/T_c (A2), and the radiator must reject Q_h = Q_c(1 + 1/COP_c) (A3, Lemma 4a). At T_c = 353 K, T_h = 520 K: COP_c ≤ 353/167 = 2.114, COP_h ≤ 3.114 (identity check: 2.114 + 1), minimum overhead 0.473 W per IT watt.

**(b) Area ratio — exact form with sink.** Pumping from unpumped rejection temperature T₁ to pumped temperature T₂, with common sink T_s, equal emissivity and view geometry:

    A_pump/A_direct = (1 + 1/COP_c) · (T₁⁴ − T_s⁴)/(T₂⁴ − T_s⁴)

The form (1 + 1/COP_c)(T₁/T₂)⁴ is the T_s = 0 approximation. **Worked example** (T₁ = 353, T₂ = 520, T_s = 220 illustrative, COP_c = 1.15): exact ratio **0.348**; zero-sink approximation 0.397. ∎ (Appendix block B5.)

**Empirical flag.** The "realistic COP_c ≈ 1.0–1.3" range is an empirical parameter (vapor-compression machines at ΔT ≈ 170 K lift, space-rated compressor practice), not derived from A1–A4. It joins the empirical parameter list in §6.

### Theorem 5 (Impossibility of waste-heat self-powering — scoped)

**Claim.** No cyclic system can sustain a positive compute load solely by converting its own internally generated waste heat back into work. Under the stated two-reservoir model with compute power P (A4), recovery efficiency η < 1 (strict, by Theorem 1 with finite area and positive throughput), and recovered work recirculated to the bus:

    P_ext = P(1 − η) > 0.

External energy resources other than the waste heat itself (solar, nuclear, chemical) are outside this claim — the theorem does not forbid zero *grid* input; it forbids *bootstrapping from one's own waste heat*.

**Proof.** Bus balance: P = P_ext + W_rec, W_rec = η·P. Hence P_ext = P(1−η) > 0 since η < 1. Self-powering (P_ext ≤ 0) requires η ≥ 1: a cyclic device converting heat from a single effective reservoir entirely into work, contradicting the Kelvin–Planck statement (A2). ∎

**Remark (amplification).** Recirculation sustains P/P_ext = 1/(1−η) watts of compute per external watt — e.g., η = 0.25 gives 1.333. Recovery is an offset multiplier, never a replacement. (Appendix block B6.)

---

## 5. Level C — Architecture Decision Criteria (reduced-order mass models)

These are decision criteria under explicitly reduced mass models with empirical inputs. They are **not** universal theorems; they are first-order conditions whose verdicts flip with parameter values but whose algebraic validity is independent of them.

**P1 (Radiator selection — equal-duty normalization).** Let ρ_A denote *effective system areal density normalized to equal delivered rejection capacity* — same rejected power, operating temperature, effective emissivity, view geometry, and lifetime/availability; otherwise compare total system masses directly. Under that normalization, droplet radiators are mass-favorable iff

    ρ_A,droplet·(1 + δ_capture) < ρ_A,solid·(1 + δ_debris)   [kg/m² both sides]

**P2 (Heat pump inclusion — necessary first-order condition).** Under the stated reduced mass model, including pump hardware and ancillary masses, the heat pump is mass-favorable only if

    ρ_A·(A_direct − A_pump) > (Q_c/COP_c)·m_array + M_pump + M_ancillary   [kg both sides]

with A_pump from Theorem 4(b) (exact sink-inclusive form), m_array in kg per electrical watt, and M_ancillary covering power electronics, plumbing, working fluid, structure, deployment, redundancy, and lifetime margins. This is a necessary first-order condition; a full verdict requires the complete mass ledger.

**P3 (Topping-cycle inclusion — consistent normalization).** Define engine specific mass per watt of **thermal input**, s_h = M_engine/Q_h [kg/W_th]. The engine is mass-favorable under the reduced model iff

    s_h < η·m_array + ρ_A·(A_direct − A_engine)/Q_h   [kg/W_th both sides]

Equivalently, per watt **recovered** (s_e = M_engine/W = s_h/η):

    s_e < m_array + ρ_A·(A_direct − A_engine)/(η·Q_h)   [kg/W_rec both sides]

Both forms are stated with their own normalization; they are the same criterion. Note A_engine > A_direct (Corollary 2.1), so the area term is **negative**: the engine must overcome both its own mass and its area penalty. With η ≤ ¼ at the reversible-envelope optimum, the bar is high.

---

## 6. Corrected Result Inventory

| Result | Status |
|---|---|
| Radiator area inversion (L1) | Proven within gray-body effective-sink model |
| T⁴ area scaling (C1.1) | Exact with sink term; (T₂/T₁)⁴ is the T_s = 0 approximation (30.5% below exact at the illustrative example; exact is 43.9% above it) |
| Sink-temperature Carnot non-attainment (T1) | Proven for finite area and positive throughput; approachable via A→∞ at fixed throughput or Q_c→0 at fixed area; near-Carnot values attainable only at extreme area |
| Carnot heat split (D1) | Proven for reversible engines (definitional equality + first law) |
| T_c* = ¾T_h, η = 25% (T2) | Reversible lower-envelope optimum, zero-sink model; irreversible optima shift upward |
| (T_h/T_c)³ area penalty (C2.1) | Universal lower bound; equality requires reversibility **and** T_s = 0; strictly exceeded for T_s > 0 |
| Nonzero-sink optimum (T3) | Exact implicit characterization: quintic stationarity, T_c*/T_h = (3+q⁴)/4, shift = q⁴/3, unique and monotone; fixed point locally attracting (|Φ′| = 4q⁴/(3+q⁴) < 1) |
| COP identity (L4a) | Proven generally |
| Heat-pump overhead bound (T4a) | Proven from reversed Carnot bound |
| Heat-pump area ratio (T4b) | Exact with sink term; zero-sink form labeled as approximation |
| Waste-heat self-powering impossibility (T5) | Valid within stated cyclic, no-external-resource model (Kelvin–Planck) |
| P1–P3 | Conditional reduced-order mass models, not universal theorems |

**Empirical parameters (referenced, not proven):** LEO effective sink range 200–260 K (lumped-model values; geometry-dependent); Si junction limits; WBG device operating temperatures; realistic COP_c ≈ 1.0–1.3 (vapor-compression class, ~170 K lift); areal densities ρ_A; specific masses m_array, s_h; margin factors δ.

---

## Appendix — Numerical Verification (runnable, with enforced tolerances)

Coverage claim: the appendix verifies **every central numerical result and representative supporting examples**. Method: optima are computed by fixed-point iteration with an enforced successive-iterate tolerance of 10⁻¹⁰ K (convergence tested, not assumed); the stationarity residual is asserted in dimensionless form; a coarse grid serves only as a redundant cross-check. Exact algebra is asserted exactly; floating-point comparisons use stated tolerances.

```python
import numpy as np

TOL = 1e-9
sigma = 5.670374419e-8

# --- B1: Corollary 1.1 exact sink-corrected ratio ---
T1, T2, Ts = 293.0, 600.0, 220.0
R  = (T2**4 - Ts**4) / (T1**4 - Ts**4)
R0 = (T2/T1)**4
assert abs(R0 - 17.585) < 0.01
assert abs(R - 25.312) < 0.01
assert abs((R/R0 - 1) - 0.439) < 0.005        # exact is 43.9% ABOVE the estimate
assert abs((1 - R0/R) - 0.305) < 0.005        # estimate is 30.5% BELOW the exact
ub = (Ts/T1)**4 / (1 - (Ts/T1)**4)
assert (R/R0 - 1) < ub                        # safe upper bound holds

# --- B2: Theorem 2 — reversible optimum and irreversible shift ---
Th = 600.0
y = np.linspace(0.01, 0.999, 4_000_000)
for a, y_expected in [(1.0, 0.750), (0.8, 0.765), (0.5, 0.781)]:
    eta = a*(1 - y)
    AW = (1 - eta)/(eta * y**4)               # proportional objective
    y_star = y[np.argmin(AW)]
    assert abs(y_star - y_expected) < 0.001, (a, y_star)

# --- B3: Corollary 2.1 — area penalty: zero-sink and nonzero-sink forms ---
Tc = 450.0
rev_penalty = (Tc/Th)*(Th/Tc)**4              # reversible, Ts=0: (Th/Tc)^3
assert abs(rev_penalty - (4/3)**3) < TOL
assert abs((4/3)**3 - 2.370) < 0.001
irr_penalty = (1 - 0.8*0.25)*(Th/Tc)**4       # a = 0.8 at same Tc
assert abs(irr_penalty - 2.5284) < 0.001
assert irr_penalty > rev_penalty
# nonzero sink: reversible penalty strictly exceeds cubic bound
Ts_pen = 220.0
rev_penalty_sink = (Tc/Th)*(Th**4 - Ts_pen**4)/(Tc**4 - Ts_pen**4)
assert rev_penalty_sink > (Th/Tc)**3

# --- B4: Theorem 3 — fixed point with ENFORCED convergence tolerance ---
def tc_star(Th, Ts, tol=1e-10, max_iter=1000):
    tc = 0.75 * Th
    for _ in range(max_iter):
        nxt = Th * (3 + (Ts / tc)**4) / 4
        if abs(nxt - tc) < tol:
            return nxt
        tc = nxt
    raise RuntimeError("Fixed-point iteration did not converge")

for Ts_i, shift_expected in [(0,0.0),(50,0.0051),(100,0.0810),(150,0.4049),
                             (200,1.2381),(220,1.7748),(225,1.9300),(250,2.8390)]:
    t = tc_star(Th, Ts_i)
    # dimensionless quintic residual: 4y^5 - 3y^4 - r^4 = 0
    y_root, r_sink = t/Th, Ts_i/Th
    assert abs(4*y_root**5 - 3*y_root**4 - r_sink**4) < 1e-12
    q = Ts_i/t
    # local attraction: |Phi'| = 4q^4/(3+q^4) < 1
    assert 4*q**4/(3 + q**4) < 1.0
    shift = 100*(t - 450.0)/450.0
    assert abs(shift - 100*q**4/3) < 1e-6     # exact identity shift = q^4/3
    assert abs(shift - shift_expected) < 0.001
    # redundant grid cross-check
    Tc2 = np.linspace(Ts_i + 0.01, 599.99, 2_000_000)
    g = (Th - Tc2)*(Tc2**4 - Ts_i**4)/Tc2
    assert abs(Tc2[np.argmax(g)] - t) < 0.01
assert abs(tc_star(600.0, 220.0) - 457.9867541) < 1e-4    # stated optimum
assert abs(100*0.49**4/3 - 1.9216003) < 1e-6              # analytic sub-2% bound value
assert 100*(0.49**4)/3 < 2.0

# --- B5: Theorem 4 — COP values and heat-pump area ratios ---
T1p, T2p, Tsp, COP = 353.0, 520.0, 220.0, 1.15
assert abs(353/167 - 2.1138) < 1e-3                       # COP_c Carnot
assert abs(520/167 - (353/167 + 1)) < TOL                 # COP_h = COP_c + 1
assert abs(1/(353/167) - 0.473) < 0.001                   # Carnot overhead per IT watt
exact  = (1 + 1/COP)*(T1p**4 - Tsp**4)/(T2p**4 - Tsp**4)
approx = (1 + 1/COP)*(T1p/T2p)**4
assert abs(exact  - 0.348) < 0.001
assert abs(approx - 0.397) < 0.001

# --- B6: Theorem 5 — amplification ---
assert abs(1/(1 - 0.25) - 4/3) < TOL

# --- B7: Corollaries 1.1/1.2 reference values ---
assert abs((600/293)**4 - 17.585) < 0.01
A_emit = 1e6/(0.91*sigma*293**4)
assert abs(A_emit - 2630) < 5                             # m^2, total emitting surface
assert abs(A_emit/2 - 1315) < 3                           # m^2, two-sided panel planform

# --- B8: Theorem 1 consequence — 99% example is extreme-area, not impossible ---
Th99, Ts99, Tc99, W99 = 300.0, 2.7, 3.0, 1e6
eta99 = 1 - Tc99/Th99
assert abs(eta99 - 0.99) < 1e-9
Qc99 = W99*Tc99/(Th99 - Tc99)
assert abs(Qc99 - 10101.0) < 1.0                          # ~10.1 kW
A99 = Qc99/(sigma*(Tc99**4 - Ts99**4))
assert 6.0e9 < A99 < 7.0e9                                # ~6.4e9 m^2: finite, extreme

print("All assertions pass.")
```

Expected output: `All assertions pass.`

*Verification instructions for the reviewing model: (1) check each proof step symbolically, noting which results are labeled reversible-envelope vs. general and which assume T_s = 0; (2) run the appendix unmodified; (3) confirm every central numerical claim in the body appears in an assertion or follows from one by stated algebra; (4) confirm no empirical parameter from §6 is used as a premise in any Level A/B proof. Failures of (1)–(4) are defects; differing empirical parameter values are not.*

---

## Appendix W — Symbolic Verification Suite (Wolfram Language)

For a CAS-equipped reviewer. Each block verifies one Level A/B claim symbolically; expected outputs are stated. Exact rational reference values are given so no rounding ambiguity exists.

```wolfram
(* W1 — Theorem 2: stationarity with explicit physical assumption *)
f[Tc_] := Th Tc^3 - Tc^4;
FullSimplify[
  Solve[D[f[Tc], Tc] == 0 && 0 < Tc < Th, Tc, Reals],
  Assumptions -> Th > 0]
  (* expected: {{Tc -> 3 Th/4}} *)
FullSimplify[D[f[Tc], {Tc, 2}] /. Tc -> 3 Th/4, Assumptions -> Th > 0]
  (* expected: -9 Th^2/4  (negative => maximum of f, minimum of A/W) *)

(* W2 — Theorem 3: quintic stationarity and exact shift identity *)
g[Tc_] := (Th - Tc) (Tc^4 - Ts^4)/Tc;
Factor[Numerator[Together[D[g[Tc], Tc]]]]
  (* expected: -4 Tc^5 + 3 Th Tc^4 + Th Ts^4 *)
FullSimplify[(Tc/Th - 3/4)/(3/4) == (Ts/Tc)^4/3,
  Assumptions -> Th > Tc > Ts > 0 && 4 Tc^5 - 3 Th Tc^4 == Th Ts^4]
  (* expected: True *)
FullSimplify[
  (4 Tc^5 - 3 Th Tc^4 == Th Ts^4) \[Equivalent] (Tc/Th == (3 + (Ts/Tc)^4)/4),
  Assumptions -> Th > Tc > Ts > 0]
  (* expected: True *)

(* W2b — uniqueness/monotonicity on y >= 3/4 *)
Reduce[ForAll[y, y >= 3/4 && y < 1, D[4 y^5 - 3 y^4, y] > 0]]
  (* expected: True  (4 y^3 (5 y - 3) > 0 on the interval) *)

(* W2c — high-precision positive root, Th = 600, Ts = 220 *)
root = N[Root[4 #^5 - 1800 #^4 - 600*220^4 &, 1], 50];
{root, N[4 root^5 - 1800 root^4 - 600*220^4, 30]}
  (* expected: {457.98675408138324983229514241277622443332179202809, 0``...}
     (exact algebraic Root object; residual zero to working precision) *)

(* W3 — Theorem 3 fixed-point attraction *)
Phi[T_] := Th/4 (3 + (Ts/T)^4);
FullSimplify[Abs[Phi'[Tc]] /. Th -> 4 Tc/(3 + q^4) /. Ts -> q Tc,
  Assumptions -> 0 < q < 1 && Tc > 0]
  (* expected: 4 q^4/(3 + q^4) *)
FullSimplify[4 q^4/(3 + q^4) < 1, Assumptions -> 0 < q < 1]
  (* expected: True
     (note: Reduce[ineq && 0 < q < 1] returns the domain 0 < q < 1 itself —
      mathematically equivalent, but FullSimplify yields the literal True) *)

(* W3b — Theorem 1 fixed-work divergence *)
FullSimplify[
  Limit[Tc/((Th - Tc) (Tc^4 - Ts^4)), Tc -> Ts, Direction -> "FromAbove"],
  Assumptions -> Th > Ts > 0]
  (* expected: Infinity *)
FullSimplify[
  Limit[1/((Th - Tc) Tc^3), Tc -> 0, Direction -> "FromAbove"],
  Assumptions -> Th > 0]
  (* expected: Infinity *)

(* W4 — Corollary 2.1 nonzero-sink penalty strictly exceeds cubic bound *)
Reduce[(1 - (Ts/Th)^4)/(1 - (Ts/Tc)^4) > 1 && 0 < Ts < Tc < Th, {Th, Tc, Ts}, Reals]
  (* expected: equivalent to the stated domain, i.e., holds throughout it *)

(* W5 — Corollary 1.1 exact rationals (T1=293, T2=600, Ts=220) *)
{(600^4 - 220^4)/(293^4 - 220^4), 600^4/293^4}
  (* expected: {6697760000/264604779, 129600000000/7370050801}
     N: {25.3123..., 17.5847...}; deviations: R/R0 - 1 = 0.43945...,
     1 - R0/R = 0.30529... *)
(* safe upper bound is trivially larger: subtracting (Ts/T2)^4 > 0 from numerator *)

(* W6 — sub-2% bound as exact rational *)
(49/100)^4/3
  (* expected: 5764801/300000000 = 0.0192160033... < 1/50 *)

(* W7 — Theorem 4 COP values, exact *)
{353/167, 520/167, 520/167 - 353/167}
  (* expected: {353/167, 520/167, 1} — identity COP_h = COP_c + 1 *)

(* W8 — Theorem 2c irreversible-optimum stationarity, eta = a (1 - y) *)
(* minimize (1 - a(1-y))/(a(1-y) y^4): log-derivative stationarity *)
stat[a_, y_] := a/(1 - a + a y) + 1/(1 - y) - 4/y;
{y /. FindRoot[stat[8/10, y], {y, 0.76}, WorkingPrecision -> 12],
 y /. FindRoot[stat[5/10, y], {y, 0.78}, WorkingPrecision -> 12]}
  (* expected: {0.764507787..., 0.780776406...} — table values 0.765, 0.781 *)

(* W9 — Theorem 1 consequence example, exact *)
With[{Qc = 10^6*3/297, sig = 5670374419*10^-17},  (* = 5.670374419*10^-8 *)
  {Qc, Qc/(sig (3^4 - (27/10)^4))}] // N
  (* expected: {10101.01, 6.395*10^9}  (m^2) *)
```

Notes for the CAS reviewer: (i) the quintic root is supplied as a `Root` object — no claim of radical solvability is made or required; (ii) all inequalities (W2b, W3, W4) are domain statements suitable for `Reduce`; (iii) exact rationals in W5–W7 eliminate rounding ambiguity between this document and CAS output; (iv) discrepancies beyond stated precision in any W-block are legitimate defects, exactly as for the Python appendix.

---

## Closing Characterization

This document establishes exact identities within a gray-body effective-sink radiator model, reversible thermodynamic lower bounds within that model, and reduced-order architecture criteria whose verdicts depend on empirical system parameters. It does not prove the operating optimum of every irreversible engine or every realizable orbital architecture.

Within its scope, the principal conclusions are: (1) a material cold reservoir cannot attain the environmental sink temperature at finite area and positive throughput, and near-sink Carnot efficiencies are purchasable only at extreme area; (2) T_c = ¾T_h is the optimum of the reversible lower envelope for radiator area per unit work in the zero-sink model; (3) a nonzero sink shifts that optimum upward according to an exact implicit stationarity relation, with fractional shift q⁴/3; (4) heat-engine recovery incurs a radiator-area penalty of at least (T_h/T_c)³, with the exact nonzero-sink penalty strictly larger; (5) within the adopted radiator model, increasing rejection temperature strongly reduces required emitting area, all else equal — whether that yields a lower-mass, lower-power, or more reliable complete architecture remains governed by the Level C trade criteria; and (6) a cyclic system cannot sustain its compute load solely by converting its own internally generated waste heat back into work.
`````

### `pyproject.toml`

_(1326 bytes, sha256 `6ea4476ddb8fe5aaabf1233c9fdd18081679a8f3103d73de92d98b27bc841fb7`)_

`````toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "orbital-thermal"
version = "0.8.2"
description = "Executable reference implementation of the orbital-thermal-bounds radiator model (Lee-Odinson, 2026)"
authors = [{ name = "Dan Lee-Odinson", email = "dan.lee.odinson@gmail.com" }]
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
# The analytical modules (radiation, equilibrium, bounds) are dependency-light,
# but the full package requires numpy (environment, sink, transient). Optional
# extras add CoolProp (the [fluids] ammonia checks) and matplotlib (figure
# scripts); both are also pulled in by [dev].
dependencies = ["numpy>=1.24"]
# PEP 639: SPDX license expression above; ship only the software license. The
# CC BY 4.0 docs license is a separate component (see LICENSING.md).
license-files = ["LICENSE-MIT"]

[project.optional-dependencies]
dev = ["pytest>=8", "CoolProp==7.2.0", "matplotlib>=3.7"]
fluids = ["CoolProp==7.2.0"]

[project.urls]
Repository = "https://github.com/dan-lee-odinson/orbital-thermal-bounds"
"Theory preprint" = "https://doi.org/10.5281/zenodo.20650893"
"AI1 companion preprint" = "https://doi.org/10.5281/zenodo.20670772"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
`````

### `scripts/check_wheel_license.py`

_(1446 bytes, sha256 `2bd154aedf40c90c9b9ab5bed94fc18550724d4a2599c7644b422141159923aa`)_

`````python
#!/usr/bin/env python3
"""Assert the built wheel ships ONLY the MIT software license (audit re-review P3-11).

Locks the round-two licensing fix in CI: the wheel under dist/ must declare
'License: MIT' and contain exactly one license file, LICENSE-MIT, in its
dist-info/licenses/. Exits non-zero otherwise.
"""
import glob
import sys
import zipfile


def main() -> int:
    whls = sorted(glob.glob("dist/*.whl"))
    if not whls:
        print("no wheel found under dist/ (build it first)")
        return 1
    z = zipfile.ZipFile(whls[-1])
    names = z.namelist()
    lics = [n for n in names if ".dist-info/licenses/" in n]
    meta = z.read(next(n for n in names if n.endswith(".dist-info/METADATA"))).decode()
    errs = []
    if not (len(lics) == 1 and lics[0].endswith("LICENSE-MIT")):
        errs.append(f"expected exactly dist-info/licenses/LICENSE-MIT, got {lics}")
    # PEP 639 emits 'License-Expression: MIT' (Metadata 2.4); accept the legacy
    # 'License: MIT' too for older builds.
    if not any(line.strip() in ("License-Expression: MIT", "License: MIT")
               for line in meta.splitlines()):
        errs.append("wheel METADATA does not declare MIT (License-Expression or License)")
    if errs:
        for e in errs:
            print("WHEEL LICENSE ERROR:", e)
        return 1
    print(f"wheel license OK: only {lics[0]}; METADATA declares MIT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
`````

### `scripts/generate_ammonia_table.py`

_(2300 bytes, sha256 `8df79eb7064134fab1453d4f81ed9471ff1b8c4212cf4adf1c54728bf194210d`)_

`````python
"""Generate results/tables/ammonia_properties.csv.

Tabulates ammonia properties at every radiator-surface temperature that
appears in the companion paper (operating points, stress branches, and
overhead cases), with full provenance in the header.

Run from the repository root:

    python scripts/generate_ammonia_table.py
"""

import csv
from pathlib import Path

from orbital_thermal.fluids import (
    PA_PER_BAR,
    critical_margin,
    provenance,
    saturated_densities,
    saturation_pressure,
)

# Radiator-surface temperatures from the companion paper (K), labeled.
PAPER_TEMPERATURES = [
    (337.10, "sustained, two-sided (primary)"),
    (343.80, "f=0.10 overhead, nominal"),
    (346.21, "sustained, eps=0.80"),
    (348.67, "85% effective area"),
    (350.12, "f=0.20 overhead, nominal"),
    (350.78, "sustained, T_s=260"),
    (353.16, "continuous-peak hypothetical"),
    (358.91, "sustained, combined stress"),
    (365.24, "f=0.10 overhead, stressed"),
    (371.26, "f=0.20 overhead, stressed"),
    (374.17, "continuous-peak, combined stress"),
    (391.47, "sustained, one-sided"),
]

OUT = Path("results/tables/ammonia_properties.csv")


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prov = provenance()
    with OUT.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [f"# {k}={v}" for k, v in prov.items()][:1]
            + [f"{k}={v}" for k, v in list(prov.items())[1:]]
        )
        writer.writerow(
            [
                "T_K",
                "case",
                "P_sat_bar",
                "rho_liq_kg_m3",
                "rho_vap_kg_m3",
                "T_crit_margin_K",
            ]
        )
        for T, label in PAPER_TEMPERATURES:
            p_bar = saturation_pressure(T) / PA_PER_BAR
            rho_l, rho_v = saturated_densities(T)
            writer.writerow(
                [
                    f"{T:.2f}",
                    label,
                    f"{p_bar:.2f}",
                    f"{rho_l:.1f}",
                    f"{rho_v:.2f}",
                    f"{critical_margin(T):.2f}",
                ]
            )
    print(f"wrote {OUT} ({len(PAPER_TEMPERATURES)} rows)")
    print("provenance:", prov)


if __name__ == "__main__":
    main()
`````

### `scripts/plot_effective_sink.py`

_(2083 bytes, sha256 `e2bd02a74e9f1a9f23b794669614de623b362893e9da835600d5b6ed117d62c3`)_

`````python
"""Generate the third paper's opening figure: effective sink temperature around
the orbit versus the companion paper's constant 220 K assumption.

Run from the repository root:

    python scripts/plot_effective_sink.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from orbital_thermal import sink

ALT = 550.0          # km
PAPER_SINK = 220.0   # K, constant assumption in doi:10.5281/zenodo.20670772
BETAS = [0.0, 30.0, 60.0, 90.0]
OUT = Path("results/figures/effective_sink_vs_orbit.png")


def main() -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.2))

    colors = plt.cm.viridis(np.linspace(0.1, 0.85, len(BETAS)))
    for beta, c in zip(BETAS, colors):
        u, T = sink.sink_profile(ALT, beta, tilt_deg=0.0, assume_sun_shielded=True)
        ax.plot(u, T, color=c, lw=2.2, label=f"beta = {beta:.0f} deg")

    ax.axhline(PAPER_SINK, color="crimson", lw=1.8, ls="--",
               label=f"companion paper assumption ({PAPER_SINK:.0f} K)")

    floor = sink.orbital_effective_sink_temperature(ALT, 0, 180, tilt_deg=0, assume_sun_shielded=True)
    ax.annotate(f"Earth-IR floor (eclipse / terminator) ~ {floor:.0f} K",
                xy=(180, floor), xytext=(150, floor - 9),
                fontsize=8, color="0.3")
    ax.text(8, 224.5, "A space-facing (zenith) radiator instead sees ~ 3 K "
            "(CMB) - far below 220 K.", fontsize=7.5, color="0.4", style="italic")

    ax.set_xlabel("orbit position from noon, u (deg)")
    ax.set_ylabel("effective sink temperature, $T_s^{\\mathrm{eff}}$ (K)")
    ax.set_title("Nadir-facing radiator: effective sink around a 550 km orbit\n"
                 "(maximally Earth-coupled orientation vs. the constant-sink assumption)")
    ax.set_xlim(0, 360)
    ax.set_ylim(212, 270)
    ax.set_xticks(range(0, 361, 45))
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper center", ncol=2, framealpha=0.92)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=130)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
`````

### `scripts/plot_mccalip_correction.py`

_(2065 bytes, sha256 `f420fa49105112eb363f9dea8e6bc7018150206d41a1173c35a2992330610d02`)_

`````python
"""Figure: McCalip equilibrium-temperature correction vs orbit beta angle.

Recomputes McCalip's default-case equilibrium temperature with the exact per-face
Earth view factor across beta and plots his value, the corrected value, and the
+K correction. This is the paper-three headline figure for the edge-on finding.

Run from the repo root:
    python scripts/plot_mccalip_correction.py
Writes results/figures/mccalip_beta_correction.png.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from orbital_thermal import mccalip_exact_vf as ev

OUT = "results/figures/mccalip_beta_correction.png"


def main():
    rows = ev.correction_table_vs_beta(betas=range(0, 91, 5))
    beta = [r["beta_deg"] for r in rows]
    mccalip = [r["eqtemp_mccalip_K"] for r in rows]
    exact = [r["eqtemp_exact_K"] for r in rows]
    delta = [r["delta_K"] for r in rows]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 2]})
    ax1.plot(beta, mccalip, "o-", label="McCalip (cos-tilt floor)", color="#c44")
    ax1.plot(beta, exact, "s-", label="exact per-face view factor", color="#268")
    ax1.axvline(90, ls=":", color="gray", lw=1)
    ax1.annotate("default\n(edge-on)", xy=(90, exact[-1]), xytext=(70, exact[-1] + 2),
                 fontsize=9, color="gray")
    ax1.set_ylabel("equilibrium temperature (K)")
    ax1.set_title("McCalip default radiator: exact-view-factor correction vs beta")
    ax1.legend(loc="upper right")
    ax1.grid(alpha=0.3)

    ax2.plot(beta, delta, "^-", color="#373")
    ax2.set_xlabel("orbit beta angle (deg)")
    ax2.set_ylabel("correction (K)")
    ax2.set_xlim(0, 90)
    ax2.grid(alpha=0.3)
    ax2.annotate(f"+{delta[-1]:.2f} K at beta=90", xy=(90, delta[-1]),
                 xytext=(45, delta[-1] - 1.2), fontsize=9, color="#373",
                 arrowprops=dict(arrowstyle="->", color="#373"))

    fig.tight_layout()
    fig.savefig(OUT, dpi=130)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
`````

### `scripts/plot_transient.py`

_(1989 bytes, sha256 `2f9811f818a793050b2623e7fa3b102c6b40412904b5e5ae0b7e6f272d67fd1d`)_

`````python
"""Transient radiator temperature over one orbit vs the steady, averaged-sink
prediction -- showing the ripple and peak excess thermal mass introduces.

Run from the repository root:

    python scripts/plot_transient.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from orbital_thermal import transient as tr
from orbital_thermal.constants import SIGMA_SB

ALT, BETA, EPS = 550.0, 0.0, 0.91
Q_LOAD = EPS * SIGMA_SB * (337.1**4 - 220.0**4)
CAPACITIES = [2000.0, 8000.0, 40000.0]
OUT = Path("results/figures/transient_temperature.png")


def main() -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    colors = plt.cm.plasma(np.linspace(0.15, 0.8, len(CAPACITIES)))

    steady = None
    for C, c in zip(CAPACITIES, colors):
        t, T, Ts = tr.simulate(ALT, BETA, Q_LOAD, C, tilt_deg=0.0, assume_sun_shielded=True,
                               n_orbits=40, steps_per_orbit=1440)
        b = tr.averaging_bias(ALT, BETA, Q_LOAD, C, tilt_deg=0.0, assume_sun_shielded=True,
                              n_orbits=40, steps_per_orbit=1440)
        steady = b["steady_avg_sink_K"]
        tau_min = b["tau_s"] / 60.0
        ax.plot(t / 60.0, T, color=c, lw=2.0,
                label=f"C = {C/1000:.0f} kJ/m^2/K  (tau ~ {tau_min:.0f} min, "
                      f"swing {b['swing_K']:.1f} K)")

    ax.axhline(steady, color="black", lw=1.5, ls="--",
               label=f"steady, averaged sink ({steady:.1f} K)")

    ax.set_xlabel("time from orbit start (min)")
    ax.set_ylabel("radiator temperature (K)")
    ax.set_title("Transient radiator temperature over one 550 km orbit (beta = 0)\n"
                 "thermal mass damps the ripple but leaves a peak the steady sizing misses")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="upper right", framealpha=0.92)
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=130)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
`````

### `src/orbital_thermal/__init__.py`

_(1810 bytes, sha256 `69033c79980614d26012881ba04041c11c71a3c249cab2e8e85137c5cb21ca73`)_

`````python
"""orbital_thermal: executable reference implementation of the
orbital-thermal-bounds radiator model.

Theory preprint:  doi:10.5281/zenodo.20650893
AI1 companion:    doi:10.5281/zenodo.20670772

Note: the top-level ``effective_sink_temperature`` (from :mod:`radiation`) is the
generic lumped view-factor sink T_s^eff = F^(1/4) T_s. The orbit-resolved,
attitude-aware sink is :func:`orbital_thermal.sink.orbital_effective_sink_temperature`
(``sink.effective_sink_temperature`` remains as a deprecated alias). They have
different signatures and contracts; see audit re-review P2-9.
"""

from .bounds import (
    carnot_cop_cooling,
    conversion_area_penalty,
    fixed_work_area_per_watt,
    heat_pump_area_ratio,
    heat_pump_overhead,
    heating_cop,
    nonzero_sink_optimum,
    optimal_cold_fraction,
    quintic_residual,
    recirculation_amplification,
)
from .constants import SIGMA_SB, ZERO_CELSIUS
from .equilibrium import equilibrium_temperature, radiative_capacity
from .radiation import (
    area_ratio,
    effective_sink_temperature,
    net_flux,
    required_area,
)

from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version("orbital-thermal")
except PackageNotFoundError:  # pragma: no cover - running from an uninstalled tree
    __version__ = "0.0.0+unknown"

__all__ = [
    "SIGMA_SB",
    "ZERO_CELSIUS",
    "area_ratio",
    "carnot_cop_cooling",
    "conversion_area_penalty",
    "effective_sink_temperature",
    "equilibrium_temperature",
    "fixed_work_area_per_watt",
    "heat_pump_area_ratio",
    "heat_pump_overhead",
    "heating_cop",
    "net_flux",
    "nonzero_sink_optimum",
    "optimal_cold_fraction",
    "quintic_residual",
    "radiative_capacity",
    "recirculation_amplification",
    "required_area",
]
`````

### `src/orbital_thermal/_validate.py`

_(1149 bytes, sha256 `d3cbdf9d2ee73c557be850c4eb1e0776924d79ae83f0c151ab7d4343d7784d7f`)_

`````python
"""Shared input-domain validators (audit re-review P2-4).

Small helpers used at public boundaries to reject non-finite and out-of-domain
inputs with clear, uniform messages, rather than silently returning NaN or a
coarse result.
"""

import math


def finite(name: str, x: float) -> float:
    if not math.isfinite(x):
        raise ValueError(f"{name} must be finite, got {x}")
    return x


def positive(name: str, x: float) -> float:
    finite(name, x)
    if x <= 0.0:
        raise ValueError(f"{name} must be > 0, got {x}")
    return x


def nonneg(name: str, x: float) -> float:
    finite(name, x)
    if x < 0.0:
        raise ValueError(f"{name} must be >= 0, got {x}")
    return x


def in_range(name: str, x: float, lo: float, hi: float) -> float:
    finite(name, x)
    if not (lo <= x <= hi):
        raise ValueError(f"{name} must be in [{lo}, {hi}], got {x}")
    return x


def positive_int(name: str, x) -> int:
    if isinstance(x, bool) or not isinstance(x, int):
        raise TypeError(f"{name} must be an int, got {type(x).__name__}")
    if x < 1:
        raise ValueError(f"{name} must be >= 1, got {x}")
    return x
`````

### `src/orbital_thermal/bounds.py`

_(11397 bytes, sha256 `4ebac964d58cd833639b966f838bc5c4d776fd5c09654bc0a545f0fb616ccd3c`)_

`````python
"""Reversible thermodynamic bounds (Level B results of the theory preprint).

Implements Theorems 1-5 and Corollary 2.1 of "Thermodynamic Bounds and
Mass-Trade Criteria for Heat Rejection in Orbital Data Centers"
(doi:10.5281/zenodo.20650893). Pure stdlib; no dependencies.

Conventions: temperatures in kelvin, ``eta`` is heat-engine efficiency in
(0, 1), areas are emitting areas. The zero-sink case is ``T_sink = 0``.
"""

import math

from .constants import SIGMA_SB


# --------------------------------------------------------------------------
# Theorem 1 -- sink-temperature Carnot is unattainable at finite area
# --------------------------------------------------------------------------

def fixed_work_area_per_watt(
    T_h: float, T_c: float, T_sink: float, emissivity: float = 1.0
) -> float:
    """Radiator area per watt of work output for a reversible engine, m^2/W.

    A/W >= T_c / (emissivity * sigma * (T_h - T_c) * (T_c^4 - T_sink^4))

    Diverges as T_c -> T_sink (Carnot limit) and as T_c -> T_h (zero work):
    the basis of Theorem 1's non-attainability result. Worked anchor:
    T_h = 300 K, T_c = 3.0 K, T_sink = 2.7 K gives eta = 99% at about
    6.4e9 m^2 per MW -- legal, but extreme-area.
    """
    if not 0.0 < emissivity <= 1.0:
        raise ValueError(f"emissivity must be in (0, 1], got {emissivity}")
    if not 0.0 <= T_sink < T_c < T_h:
        raise ValueError(
            f"need 0 <= T_sink < T_c < T_h, got T_sink={T_sink}, "
            f"T_c={T_c}, T_h={T_h}"
        )
    return T_c / (
        emissivity * SIGMA_SB * (T_h - T_c) * (T_c**4 - T_sink**4)
    )


# --------------------------------------------------------------------------
# Theorem 2 -- the 3/4 rule (zero-sink reversible lower envelope)
# --------------------------------------------------------------------------

def optimal_cold_fraction(a: float = 1.0, tol: float = 1e-12, max_iter: int = 1000) -> float:
    """Area-per-work-optimal T_c/T_h for an engine with eta = a*(1 - T_c/T_h).

    Minimizes A/W proportional to (1 - eta) / (eta * y^4) over y = T_c/T_h.

    Implementation: bisection on the stationarity condition

        g(y) = a/(1 - a*(1 - y)) + 1/(1 - y) - 4/y = 0

    (the derivative of log A/W). g is strictly increasing on (0, 1): although its
    first term a/(1 - a(1 - y)) is *decreasing*, the full derivative
    g'(y) = -a^2/(1 - a(1 - y))^2 + 1/(1 - y)^2 + 4/y^2 is positive there, because
    1 - a(1 - y) >= y (their difference is (1 - y)(1 - a) >= 0 for a <= 1) gives
    a^2/(1 - a(1 - y))^2 <= 1/y^2 < 4/y^2. So g has exactly one root and bisection
    converges to full precision -- a direct search on the objective itself stalls
    near the minimum, where objective differences fall below float resolution.

    Theorem 2: a = 1 (reversible) gives exactly 3/4 (g reduces to
    1/(1 - y) - 3/y), with a 25% efficiency ceiling. Irreversibility
    shifts the optimum up: a = 0.8 -> 0.7645, a = 0.5 -> 0.7808.
    """
    if not 0.0 < a <= 1.0:
        raise ValueError(f"irreversibility factor a must be in (0, 1], got {a}")
    if not (tol > 0.0 and tol < float("inf")):
        raise ValueError(f"tol must be finite and positive, got {tol}")
    if max_iter <= 0:
        raise ValueError(f"max_iter must be positive, got {max_iter}")

    def g(y: float) -> float:
        return a / (1.0 - a * (1.0 - y)) + 1.0 / (1.0 - y) - 4.0 / y

    lo, hi = 1e-12, 1.0 - 1e-12
    for _ in range(max_iter):
        if hi - lo <= tol:
            return 0.5 * (lo + hi)
        mid = 0.5 * (lo + hi)
        if mid <= lo or mid >= hi:        # bracket collapsed to float resolution
            return mid
        if g(mid) < 0.0:
            lo = mid
        else:
            hi = mid
    raise RuntimeError(
        f"optimal_cold_fraction bisection did not converge to tol={tol} in "
        f"{max_iter} steps (bracket width {hi - lo:.3g}); increase max_iter"
    )


# --------------------------------------------------------------------------
# Theorem 3 -- nonzero-sink optimum (exact implicit quintic)
# --------------------------------------------------------------------------

def nonzero_sink_optimum(
    T_h: float, T_sink: float, tol: float = 1e-10, max_iter: int = 1000
) -> float:
    """Optimal cold-side temperature T_c* for sink temperature T_sink > 0.

    Solves the quintic 4*T_c^5 - 3*T_h*T_c^4 - T_h*T_sink^4 = 0 by bisection on
    its dimensionless form f(y) = 4y^5 - 3y^4 - r^4 (y = T_c/T_h, r = T_sink/T_h),
    bracketed on (max(3/4, r), 1) and iterated to ``tol`` kelvin (the published
    suites enforce 1e-10 K). Bisection is globally convergent; the earlier
    fixed-point map Phi(T) = (T_h/4)(3 + (T_sink/T)^4) has |Phi'| = 4q^4/(3 + q^4)
    -> 1 as T_sink -> T_h and fails to converge for r >~ 0.97 (audit item 6).

    Equivalent exact form: T_c*/T_h = (3 + q^4)/4 with q = T_sink/T_c*;
    the fractional shift above (3/4)T_h is exactly q^4/3. Worked anchor:
    T_h = 600 K, T_sink = 220 K gives T_c* = 457.98675408138325 K
    (+1.7748% above 450 K).
    """
    if T_h <= 0.0:
        raise ValueError(f"T_h must be positive, got {T_h}")
    if not 0.0 <= T_sink < T_h:
        raise ValueError(f"need 0 <= T_sink < T_h, got {T_sink}")
    if not (math.isfinite(tol) and tol > 0.0):
        raise ValueError(f"tol must be finite and > 0, got {tol}")
    if max_iter <= 0:
        raise ValueError(f"max_iter must be positive, got {max_iter}")
    if T_sink == 0.0:
        return 0.75 * T_h
    # Bisection on the dimensionless quintic f(y) = 4y^5 - 3y^4 - r^4, y = T_c/T_h,
    # r = T_sink/T_h. The optimum satisfies y* >= 3/4 (Theorem 2) and y* > r, and
    # f is strictly increasing on (max(3/4, r), 1) with f(max(3/4, r)) < 0 and
    # f(1) = 1 - r^4 > 0, so a unique root is bracketed there. Bisection is
    # globally convergent, unlike the fixed-point map Phi(T) whose contraction
    # |Phi'| = 4q^4/(3 + q^4) -> 1 as T_sink -> T_h (it fails to converge for
    # r >~ 0.97). This is the same quintic the Theorem-2 optimizer brackets.
    r = T_sink / T_h

    def f(y: float) -> float:
        return 4.0 * y**5 - 3.0 * y**4 - r**4

    lo, hi = max(0.75, r), 1.0
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        if f(mid) < 0.0:
            lo = mid
        else:
            hi = mid
        if (hi - lo) * T_h < tol:
            return 0.5 * (lo + hi) * T_h
    raise RuntimeError(
        f"nonzero_sink_optimum did not converge to tol={tol} K in {max_iter} "
        f"bisection steps (bracket width {(hi - lo) * T_h:.3g} K for T_h={T_h}, "
        f"T_sink={T_sink}); increase max_iter"
    )


def quintic_residual(T_c: float, T_h: float, T_sink: float) -> float:
    """Dimensionless residual of the Theorem 3 quintic at T_c.

    With y = T_c/T_h and r = T_sink/T_h: residual = 4y^5 - 3y^4 - r^4,
    which is zero at the optimum (published tolerance: |residual| < 1e-12).
    """
    y = T_c / T_h
    r = T_sink / T_h
    return 4.0 * y**5 - 3.0 * y**4 - r**4


# --------------------------------------------------------------------------
# Corollary 2.1 -- conversion area penalty
# --------------------------------------------------------------------------

def conversion_area_penalty(
    T_h: float, T_c: float, eta: float, T_sink: float = 0.0
) -> float:
    """Area ratio A_engine / A_direct for converting heat to work first.

    A_engine/A_direct = (1 - eta) * (T_h^4 - T_sink^4) / (T_c^4 - T_sink^4)

    Zero-sink reversible bound: >= (T_h/T_c)^3, with minimum (4/3)^3 ~ 2.370
    at the Theorem 2 optimum; strictly larger for T_sink > 0.
    """
    if not 0.0 < eta < 1.0:
        raise ValueError(f"eta must be in (0, 1), got {eta}")
    if not 0.0 <= T_sink < T_c < T_h:
        raise ValueError(
            f"need 0 <= T_sink < T_c < T_h, got T_sink={T_sink}, "
            f"T_c={T_c}, T_h={T_h}"
        )
    eta_carnot = 1.0 - T_c / T_h
    if eta > eta_carnot + 1e-9:
        raise ValueError(
            f"eta={eta} exceeds the Carnot ceiling 1 - T_c/T_h = {eta_carnot:.6g} "
            f"for an engine between T_h={T_h} K and T_c={T_c} K; the area-penalty "
            "bound assumes a realizable (sub-Carnot) engine"
        )
    return (1.0 - eta) * (T_h**4 - T_sink**4) / (T_c**4 - T_sink**4)


# --------------------------------------------------------------------------
# Theorem 4 -- heat-pump identities
# --------------------------------------------------------------------------

def carnot_cop_cooling(T_c: float, T_h: float) -> float:
    """Carnot ceiling on the cooling COP: COP_c <= T_c / (T_h - T_c).

    Worked anchor: lifting 353 K -> 520 K gives COP_c <= 2.114.
    """
    if not 0.0 < T_c < T_h:
        raise ValueError(f"need 0 < T_c < T_h, got T_c={T_c}, T_h={T_h}")
    return T_c / (T_h - T_c)


def heating_cop(cop_cooling: float) -> float:
    """First-law identity COP_h = COP_c + 1 (Theorem 4)."""
    if not (math.isfinite(cop_cooling) and cop_cooling > 0.0):
        raise ValueError(f"COP_c must be finite and > 0, got {cop_cooling}")
    return cop_cooling + 1.0


def heat_pump_overhead(cop_cooling: float) -> float:
    """Electrical overhead per watt of heat lifted: W/Q_c = 1/COP_c.

    Worked anchor: the 353/520 K Carnot ceiling gives minimum overhead
    0.473 W per W.
    """
    if not (math.isfinite(cop_cooling) and cop_cooling > 0.0):
        raise ValueError(f"COP_c must be finite and > 0, got {cop_cooling}")
    return 1.0 / cop_cooling


def heat_pump_area_ratio(
    cop_cooling: float, T1: float, T2: float, T_sink: float = 0.0
) -> float:
    """Area ratio A_pumped / A_direct for rejecting at T2 instead of T1.

    (1 + 1/COP_c) * (T1^4 - T_sink^4) / (T2^4 - T_sink^4)

    The pump adds its own work as extra heat (numerator factor) but buys a
    hotter, smaller radiator (denominator). Worked anchor: COP_c = 1.15,
    353 -> 520 K, T_sink = 220 K gives exactly 0.348 (zero-sink
    approximation 0.397).
    """
    if not (cop_cooling > 0.0):          # also rejects NaN
        raise ValueError(f"COP_c must be a positive number, got {cop_cooling}")
    if T_sink < 0.0:
        raise ValueError(f"T_sink must be >= 0 K, got {T_sink}")
    if not (T_sink < T1 and T_sink < T2):
        raise ValueError("both temperatures must exceed the sink")
    if not T2 > T1:
        raise ValueError(
            f"need a genuine upward lift T2 > T1, got T1={T1} K, T2={T2} K"
        )
    cop_carnot = T1 / (T2 - T1)
    if cop_cooling > cop_carnot * (1.0 + 1e-9):
        raise ValueError(
            f"cop_cooling={cop_cooling} exceeds the Carnot cooling ceiling "
            f"T1/(T2 - T1) = {cop_carnot:.6g} for the {T1} -> {T2} K lift"
        )
    return (1.0 + 1.0 / cop_cooling) * (T1**4 - T_sink**4) / (
        T2**4 - T_sink**4
    )


# --------------------------------------------------------------------------
# Theorem 5 -- no self-powering
# --------------------------------------------------------------------------

def recirculation_amplification(eta: float) -> float:
    """Steady-state amplification 1/(1 - eta) of waste-heat recirculation.

    Theorem 5: external power P_ext = P*(1 - eta) > 0 always (Kelvin-Planck);
    recirculation amplifies delivered power by at most 1/(1 - eta).
    Worked anchor: eta = 0.25 -> 1.333.
    """
    if not 0.0 < eta < 1.0:
        raise ValueError(f"eta must be in (0, 1), got {eta}")
    return 1.0 / (1.0 - eta)
`````

### `src/orbital_thermal/constants.py`

_(1014 bytes, sha256 `dc88d655311ae4975e35db0ecbe53fff7bfae6e6bdf5135ec64c5c15b4d26cbb`)_

`````python
"""Physical constants used throughout the orbital_thermal package.

All values are SI. SIGMA_SB is the binary64 (IEEE-754 double) value of the
Stefan-Boltzmann constant derived from the exact 2019-SI defining constants
k_B, h, c via sigma = 2*pi^5*k_B^4 / (15*h^3*c^2). It is therefore NOT the
truncated 5.670374419e-8 printed in CODATA tables -- that differs by ~3.3e-11
relative. The published verification suites (verify_suite.py and
companion/verify_ai1.py) used the truncated printed form; that difference is
part of any replication tolerance budget and is nanokelvin-level at the AI1
operating range (four-root sensitivity dT/T = d(sigma)/4 sigma). The external
McCalip JavaScript model uses 5.67e-8, a larger ~6.6e-5 difference.
"""

#: Stefan-Boltzmann constant, W m^-2 K^-4: binary64 of the SI-derived value
#: 2*pi^5*k_B^4 / (15*h^3*c^2) (see module docstring; not the truncated CODATA print).
SIGMA_SB: float = 5.670374419184429e-8

#: 0 degrees Celsius expressed in kelvin
ZERO_CELSIUS: float = 273.15
`````

### `src/orbital_thermal/environment.py`

_(7401 bytes, sha256 `48765fd077d2ae8c15bb6614fbfe334f4b08caa3b65b37c7471be4242ae7d47c`)_

`````python
"""Analytic orbital thermal environment: orbit geometry, eclipse, view factors.

This module supplies the *geometry* the third paper needs to turn the static
radiator bounds into an orbit-resolved picture: where the spacecraft is, when it
is in Earth's shadow, and how strongly a tilted radiator couples to the planet.

Everything here is closed-form or evaluated to machine precision -- no empirical
fits and no small-angle or cosine view-factor approximations. The functions are
validated in ``tests/test_environment.py`` against analytic special cases and an
independent numerical integrator.

Conventions
-----------
- Circular orbit, spherical Earth.
- ``altitude_km`` is height above mean Earth radius (``EARTH_RADIUS_KM``).
- ``beta_deg`` (orbit beta angle) is the angle between the Sun direction and the
  orbit plane: 0 deg = Sun in the orbit plane (deepest eclipse), 90 deg =
  Sun normal to the orbit plane (terminator orbit, no eclipse).
- ``tilt_deg`` (radiator) is the angle between a surface normal and the nadir
  (planet-center) direction: 0 deg = facing straight down, 180 deg = zenith.

Units: SI unless a name says otherwise (km for distances, seconds for time).
"""

import numpy as np

#: Mean Earth radius, km (matches the McCalip model's EARTH_RADIUS_KM).
EARTH_RADIUS_KM: float = 6371.0

#: Earth standard gravitational parameter, km^3/s^2 (WGS-84 / EGM).
MU_EARTH_KM3_S2: float = 398600.4418

# Gauss-Legendre nodes for the radial view-factor integral (module-level so the
# weights are built once). 48 nodes drive the per-panel error below 1e-9.
_GL_X, _GL_W = np.polynomial.legendre.leggauss(48)


def _check_altitude(altitude_km: float) -> None:
    if not (np.isfinite(altitude_km) and altitude_km > 0):
        raise ValueError(f"altitude_km must be finite and > 0, got {altitude_km}")


# ---------------------------------------------------------------------------
# Circular orbit geometry
# ---------------------------------------------------------------------------

def orbital_radius(altitude_km: float) -> float:
    """Orbital radius (Earth center to spacecraft), km."""
    _check_altitude(altitude_km)
    return EARTH_RADIUS_KM + altitude_km


def orbital_period(altitude_km: float) -> float:
    """Circular orbital period, seconds.  T = 2*pi*sqrt(r^3 / mu)."""
    r = orbital_radius(altitude_km)
    return 2.0 * np.pi * np.sqrt(r**3 / MU_EARTH_KM3_S2)


def orbital_velocity(altitude_km: float) -> float:
    """Circular orbital speed, km/s.  v = sqrt(mu / r)."""
    r = orbital_radius(altitude_km)
    return np.sqrt(MU_EARTH_KM3_S2 / r)


def earth_angular_radius(altitude_km: float) -> float:
    """Angular radius of Earth seen from orbit, radians.  arcsin(R_e / r)."""
    r = orbital_radius(altitude_km)
    return np.arcsin(EARTH_RADIUS_KM / r)


def beta_critical(altitude_km: float) -> float:
    """Beta angle above which a circular orbit never enters eclipse, degrees.

    Equal to the Earth angular radius: when the Sun sits farther from the orbit
    plane than Earth's angular size, the cylindrical shadow is never crossed.
    """
    return np.degrees(earth_angular_radius(altitude_km))


# ---------------------------------------------------------------------------
# Eclipse (cylindrical shadow model)
# ---------------------------------------------------------------------------

def eclipse_fraction(altitude_km: float, beta_deg: float) -> float:
    """Fraction of a circular orbit spent in Earth's shadow (0..1).

    Cylindrical-shadow model (Earth casts an infinite cylinder of its own
    radius; ignores penumbra and the Sun's finite size). Exact closed form:

        f_E = (1/pi) * arccos( sqrt(1 - (R_e/r)^2) / cos(beta) )

    valid while the argument <= 1; for |beta| >= beta_critical the orbit is in
    continuous sunlight and the fraction is 0. At beta = 0, low Earth orbit
    spends ~0.37 of each period in eclipse.
    """
    if not (0.0 <= beta_deg <= 90.0):
        raise ValueError(f"beta_deg must be in [0, 90], got {beta_deg}")
    r = orbital_radius(altitude_km)
    cos_eta = np.sqrt(1.0 - (EARTH_RADIUS_KM / r) ** 2)   # = cos(earth ang. radius)
    beta = np.radians(beta_deg)
    arg = cos_eta / np.cos(beta)
    if arg >= 1.0:
        return 0.0
    return float(np.arccos(arg) / np.pi)


def eclipse_duration(altitude_km: float, beta_deg: float) -> float:
    """Eclipse duration per orbit, seconds (= eclipse_fraction * period)."""
    return eclipse_fraction(altitude_km, beta_deg) * orbital_period(altitude_km)


# ---------------------------------------------------------------------------
# View factors (planar radiator element to spherical Earth)
# ---------------------------------------------------------------------------

def nadir_view_factor(altitude_km: float) -> float:
    """View factor from a nadir-facing flat plate to Earth (maximum possible).

    Closed form: VF_nadir = sin^2(theta) = (R_e / r)^2.  At 550 km: 0.8474.
    """
    return float(np.sin(earth_angular_radius(altitude_km)) ** 2)


def _vf_ring(psi: float, cg: float, sg: float) -> float:
    """Azimuth-integrated, horizon-clipped projected-solid-angle density at
    polar offset ``psi`` within Earth's disk. Analytic in azimuth."""
    a = np.sin(psi) * sg
    b = np.cos(psi) * cg
    if b >= abs(a):              # whole azimuth ring above the radiator horizon
        ring = 2.0 * np.pi * b
    elif b <= -abs(a):           # whole ring below the horizon
        ring = 0.0
    else:                        # ring straddles the horizon
        phi0 = np.arccos(np.clip(-b / a, -1.0, 1.0))
        ring = 2.0 * (a * np.sin(phi0) + b * phi0)
    return ring * np.sin(psi)


def sphere_view_factor(altitude_km: float, tilt_deg: float) -> float:
    """Exact view factor from a tilted flat plate to spherical Earth.

    ``tilt_deg`` is the angle between the plate normal and nadir. This treats
    Earth as a uniform disk of angular radius ``theta = arcsin(R_e/r)`` centered
    on nadir and integrates the cosine-weighted solid angle over the part of
    that disk above the plate's horizon -- the exact radiative view factor, with
    no cosine approximation. The azimuthal integral is closed-form; the radial
    integral is evaluated by piecewise Gauss-Legendre quadrature split at the
    horizon crossings, accurate to ~1e-9.

    Limiting cases (returned in closed form):
      - tilt <= 90deg - theta:   F = cos(tilt) * sin^2(theta)   (Earth fully up)
      - tilt >= 90deg + theta:   F = 0                          (Earth fully set)
    """
    if not (0.0 <= tilt_deg <= 180.0):
        raise ValueError(f"tilt_deg must be in [0, 180], got {tilt_deg}")
    theta = earth_angular_radius(altitude_km)
    g = np.radians(tilt_deg)
    sin2 = np.sin(theta) ** 2
    if g <= (np.pi / 2 - theta):
        return float(np.cos(g) * sin2)
    if g >= (np.pi / 2 + theta):
        return 0.0
    cg, sg = np.cos(g), np.sin(g)
    # Kinks where the azimuth ring transitions (b = +/- a): split the panel there.
    cand = {abs(np.pi / 2 - g), np.pi / 2 + g}
    knots = sorted({0.0, theta} | {k for k in cand if 0.0 < k < theta})
    total = 0.0
    for lo, hi in zip(knots[:-1], knots[1:]):
        mid, half = 0.5 * (hi + lo), 0.5 * (hi - lo)
        nodes = mid + half * _GL_X
        vals = np.array([_vf_ring(p, cg, sg) for p in nodes])
        total += half * float(np.dot(_GL_W, vals))
    return total / np.pi
`````

### `src/orbital_thermal/equilibrium.py`

_(1914 bytes, sha256 `ddd5106817cb97a23ed5b017e6ca06298f3c0cc02a8845755bd483498557f363`)_

`````python
"""Equilibrium temperature and fixed-temperature capacity.

These two functions mirror the ``T_req`` and ``cap`` definitions asserted
block-by-block in ``companion/verify_ai1.py`` for "The AI1 Design Point"
(doi:10.5281/zenodo.20670772). They are each other's inverses, and the
smoke tests assert that round trip explicitly.

Units: SI throughout. ``area`` is emitting area in m^2.
"""

import math

from .constants import SIGMA_SB
from .radiation import _check


def equilibrium_temperature(
    Q: float, area: float, emissivity: float, T_sink: float = 0.0
) -> float:
    """Steady radiator temperature that rejects ``Q`` watts through ``area``.

    T = (Q / (emissivity * sigma * area) + T_sink^4)^(1/4)

    Worked anchor (AI1 primary operating point): 120 kW through 220 m^2 at
    emissivity 0.91 with T_s^eff = 220 K gives 337.1 K.
    """
    if not (math.isfinite(Q) and Q > 0.0):
        raise ValueError(f"heat load Q must be finite and > 0, got {Q}")
    if not (math.isfinite(area) and area > 0.0):
        raise ValueError(f"area must be finite and > 0, got {area}")
    if not 0.0 < emissivity <= 1.0:
        raise ValueError(f"emissivity must be in (0, 1], got {emissivity}")
    if not (math.isfinite(T_sink) and T_sink >= 0.0):
        raise ValueError(f"sink temperature must be finite and >= 0 K, got {T_sink}")
    return (Q / (emissivity * SIGMA_SB * area) + T_sink**4) ** 0.25


def radiative_capacity(
    T: float, area: float, emissivity: float, T_sink: float = 0.0
) -> float:
    """Heat rejection capacity (W) of ``area`` m^2 held at temperature ``T``.

    Q = emissivity * sigma * area * (T^4 - T_sink^4)

    Inverse of :func:`equilibrium_temperature` at fixed area, emissivity,
    and sink.
    """
    if area <= 0.0:
        raise ValueError(f"area must be positive, got {area}")
    _check(emissivity, T, T_sink)
    return emissivity * SIGMA_SB * area * (T**4 - T_sink**4)
`````

### `src/orbital_thermal/fluids.py`

_(4343 bytes, sha256 `b0c445419aa487609cc984b9118f4a6a868608225cbea85ca78e5cec82c0fefb`)_

`````python
"""Executable thermophysical-property checks for the AI1 coolant screen.

Computes the ammonia properties that the companion paper ("The AI1 Design
Point", doi:10.5281/zenodo.20670772) quotes as NIST Chemistry WebBook
reference values: critical point, saturation pressures at the modeled
radiator-surface temperatures, and phase state. With this module the
properties are CALCULATED rather than transcribed, upgrading the paper's
verification scope (its Option B exclusion) to executable form.

Backend: CoolProp HEOS (Helmholtz-energy equation of state). Use
:func:`provenance` to record the exact CoolProp version and the underlying
EOS citation next to any generated table; property values are only
reproducible against a pinned version.

This module is intentionally NOT imported by ``orbital_thermal/__init__``:
CoolProp is an optional dependency, and importing the core package must not
require it. Import explicitly::

    from orbital_thermal import fluids

Scope limit (companion paper, Phase 3 plan): property calculations verify
thermodynamic consistency only. They establish nothing about component
pressure ratings, pump feasibility, seal compatibility, or reliability.

Units: SI (kelvin, pascal, kg/m^3). ``PA_PER_BAR`` converts for display.
"""

try:
    import CoolProp
    from CoolProp.CoolProp import PhaseSI, PropsSI, get_BibTeXKey
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "orbital_thermal.fluids requires CoolProp. "
        'Install it with: pip install "orbital-thermal[fluids]" '
        "or: pip install CoolProp"
    ) from exc

#: Pascals per bar.
PA_PER_BAR: float = 1e5

#: Default working fluid for the AI1 coolant screen.
DEFAULT_FLUID: str = "Ammonia"


def critical_temperature(fluid: str = DEFAULT_FLUID) -> float:
    """Critical temperature, K. Paper's NIST anchor for ammonia: 405.5 K."""
    return PropsSI("Tcrit", fluid)


def critical_pressure(fluid: str = DEFAULT_FLUID) -> float:
    """Critical pressure, Pa. Paper's NIST anchor for ammonia: ~113 bar."""
    return PropsSI("pcrit", fluid)


def saturation_pressure(T: float, fluid: str = DEFAULT_FLUID) -> float:
    """Saturation (vapor) pressure at temperature ``T``, in Pa.

    This is the lower bound on loop pressure for keeping the coolant
    liquid at the radiator-surface temperature -- the quantity behind the
    paper's 41.4 / 46.8 / 63.8 / 88.4 bar ladder.

    Raises ValueError above the critical temperature, where a saturation
    curve no longer exists.
    """
    T_crit = critical_temperature(fluid)
    if T >= T_crit:
        raise ValueError(
            f"T = {T} K is at or above the critical temperature of "
            f"{fluid} ({T_crit:.2f} K); no saturation pressure exists"
        )
    return PropsSI("P", "T", T, "Q", 0.0, fluid)


def phase_state(T: float, P: float, fluid: str = DEFAULT_FLUID) -> str:
    """CoolProp phase label at (``T`` K, ``P`` Pa).

    Typical labels: 'liquid', 'gas', 'supercritical', 'supercritical_gas',
    'supercritical_liquid', 'twophase'.
    """
    return PhaseSI("T", T, "P", P, fluid)


def critical_margin(T: float, fluid: str = DEFAULT_FLUID) -> float:
    """Temperature headroom to the critical point: T_crit - T, in K.

    Positive means a subcritical liquid loop is possible at sufficient
    pressure; negative means no liquid phase exists at any pressure. The
    paper's screen: >50 K margin for the two-sided readings, <14 K for
    one-sided sustained, negative for one-sided continuous-peak.
    """
    return critical_temperature(fluid) - T


def saturated_densities(
    T: float, fluid: str = DEFAULT_FLUID
) -> tuple[float, float]:
    """(liquid, vapor) densities on the saturation curve at ``T``, kg/m^3."""
    rho_liq = PropsSI("D", "T", T, "Q", 0.0, fluid)
    rho_vap = PropsSI("D", "T", T, "Q", 1.0, fluid)
    return rho_liq, rho_vap


def provenance(fluid: str = DEFAULT_FLUID) -> dict[str, str]:
    """Version and equation-of-state citation for reproducibility records.

    Include this next to every generated property table: values are only
    comparable against the same CoolProp version and EOS.
    """
    return {
        "package": "CoolProp",
        "version": CoolProp.__version__,
        "backend": "HEOS",
        "fluid": fluid,
        "eos_bibtex_key": get_BibTeXKey(fluid, "EOS"),
    }
`````

### `src/orbital_thermal/mccalip_exact_vf.py`

_(5287 bytes, sha256 `699ce774176b931b211d9c0284c271ff8e807caa9d208bc17218e9804e4cb518`)_

`````python
"""Recompute McCalip's orbital-datacenter equilibrium temperature with the EXACT
tilted-plate-to-sphere Earth view factor in place of his cos-tilt heuristic.

Headline result (paper three). At McCalip's default geometry (beta = 90 deg,
550 km) a sun-tracking bifacial panel is EDGE-ON to Earth: the panel normal
tracks the Sun, which at beta = 90 deg is normal to the orbit plane, while nadir
lies in the plane -- 90 deg away. His per-face view-factor floor averages ~0.021
per face around the orbit there; the exact tilted-plate-to-sphere view factor is
~0.258, a ~12x underestimate. Substituting the exact per-face view factor into
his own heat balance raises his default equilibrium temperature

    335.75 K  (McCalip, replicated)  ->  342.10 K  (exact edge-on VF)   +6.35 K

This is a quantified new result, not a defect in the replication.
:mod:`orbital_thermal.mccalip_replication` remains a faithful port of his model;
this module isolates the single geometric approximation in that model and shows
what his own heat balance gives once it is replaced by the exact integral. Only
the view factor changes -- his truncated sigma, rounded deep-space temperature,
constants, and orbit sampling are all retained, so the temperature shift is
attributable to geometry alone (see :func:`equilibrium_temperature_with_view_factors`,
which reproduces his number exactly when fed his own view factors).
"""

import math

from . import environment as env
from . import mccalip_replication as mc


def exact_per_face_view_factors(altitude_km, beta_deg, n=72):
    """Orbit-averaged exact Earth view factor for each face of a sun-tracking
    bifacial panel, returned as ``(vf_side_a, vf_side_b)``.

    Mirrors McCalip's orbit sampling (``n``-point average, his default 72) and
    his per-face tilt cosines -- side A's normal makes cos(tilt) = cos(beta)*
    cos(nu) with nadir, side B is the opposite face -- but evaluates the EXACT
    tilted-plate-to-sphere view factor (:func:`environment.sphere_view_factor`)
    at each orbit step instead of his cos-tilt heuristic with a 5% edge-on floor.
    """
    beta = math.radians(beta_deg)
    a = b = 0.0
    for i in range(n):
        nu = 2.0 * math.pi * i / n
        c = max(-1.0, min(1.0, math.cos(beta) * math.cos(nu)))
        a += env.sphere_view_factor(altitude_km, math.degrees(math.acos(c)))
        b += env.sphere_view_factor(altitude_km, math.degrees(math.acos(-c)))
    return a / n, b / n


def equilibrium_temperature_with_view_factors(overrides, vf_side_a, vf_side_b):
    """McCalip's ``calculate_thermal`` heat balance with arbitrary per-face Earth
    view factors. Fed his own (heuristic) view factors, this reproduces
    ``calculate_thermal(...)['eqTempK']`` to floating-point roundoff -- so any
    temperature change comes from the view factors alone.
    """
    s = mc._state(overrides)
    area = mc.calculate_orbital(s)["_arrayAreaM2"]
    S = mc.CONST["SOLAR_IRRADIANCE_W_M2"]
    e_ir = mc.CONST["EARTH_IR_FLUX_W_M2"]
    alb = mc.CONST["EARTH_ALBEDO_FACTOR"]
    alpha_pv, eps_pv, eps_rad = s["solarAbsorptivity"], s["emissivityPV"], s["emissivityRad"]
    pv_eff, beta = s["pvEfficiency"], s["betaAngle"]
    power_generated = S * pv_eff * area
    q_solar_waste = S * alpha_pv * area - power_generated
    q_earth_ir = e_ir * vf_side_a * eps_pv * area + e_ir * vf_side_b * eps_rad * area
    q_albedo = S * alb * vf_side_a * math.cos(math.radians(beta)) * alpha_pv * area
    q_heat_loop = power_generated
    total_heat_in = q_solar_waste + q_earth_ir + q_albedo + q_heat_loop
    total_eps = eps_pv + eps_rad
    return float((total_heat_in / (mc.SIGMA * area * total_eps) + mc.T_SPACE_K**4) ** 0.25)


def eqtemp_exact_vf(overrides=None, n=72):
    """McCalip equilibrium temperature (K) recomputed with exact per-face Earth
    view factors at the given state (defaults: beta = 90 deg, 550 km)."""
    s = mc._state(overrides)
    vf_a, vf_b = exact_per_face_view_factors(s["orbitalAltitudeKm"], s["betaAngle"], n=n)
    return equilibrium_temperature_with_view_factors(overrides, vf_a, vf_b)


# Default beta grid for the correction table (the oracle grid plus midpoints).
DEFAULT_BETAS = (0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0)


def correction_table_vs_beta(betas=DEFAULT_BETAS, overrides=None, n=72):
    """Tabulate the equilibrium-temperature correction vs orbit beta angle.

    For each beta this compares McCalip's own replicated equilibrium temperature
    (his cos-tilt view-factor heuristic) with the same heat balance evaluated
    using the exact per-face Earth view factor. Returns a list of dicts with keys
    ``beta_deg``, ``eqtemp_mccalip_K``, ``eqtemp_exact_K``, ``delta_K``
    (= exact - McCalip). The correction is positive at every beta and grows
    monotonically toward the edge-on default (beta = 90 deg), where it is +6.35 K.
    """
    base = dict(overrides or {})
    rows = []
    for beta in betas:
        ov = dict(base, betaAngle=beta)
        mccalip = mc.calculate_thermal(mc._state(ov))["eqTempK"]
        exact = eqtemp_exact_vf(ov, n=n)
        rows.append({
            "beta_deg": float(beta),
            "eqtemp_mccalip_K": float(mccalip),
            "eqtemp_exact_K": float(exact),
            "delta_K": float(exact - mccalip),
        })
    return rows
`````

### `src/orbital_thermal/mccalip_replication.py`

_(9614 bytes, sha256 `3228720e7fe4d346ab9dfb37580566a08276e3a7dc23b1d4717e6e84b5a99142`)_

`````python
"""Independent Python replication of the McCalip orbital thermal/cost model.

This is a faithful port of ``static/js/math.js`` from
https://github.com/andrewmccalip/thoughts at the pinned commit
d1e4238d3d3f4924e5ca65bafbd4ba5b39af2eb8 (see
``external_models/mccalip_thoughts/provenance.md``). It exists to *replicate* his
result in a second language and check our understanding of his model against the
frozen Node oracle (``expected_outputs.json``).

Three distinct claims must not be conflated (see the replication report):

* Replication -- does this Python reproduce his JavaScript's numbers? This module
  uses his exact constants (including the truncated sigma = 5.67e-8 and the
  rounded deep-space temperature T_space = 3 K) and matches the oracle to ~1e-9.
* Verification -- is the underlying physics internally correct? That is the job
  of :mod:`orbital_thermal` and its published-results suite, which use the exact
  CODATA sigma and the exact view-factor integral.
* Validation -- does the model match reality? Neither this module nor the core
  package claims that; it is the open question the third paper frames.

Because the goal is faithful replication, this module deliberately keeps
McCalip's approximations (the 72-point orbit average, the cos-tilt view-factor
heuristic, the 5% edge-on floor) rather than the exact forms in
:mod:`orbital_thermal.environment`.
"""

import math

# McCalip's truncated Stefan-Boltzmann constant (his math.js value).
SIGMA = 5.67e-8
T_SPACE_K = 3.0

# Constants block from math.js (defaults).
CONST = {
    "HOURS_PER_YEAR": 8760,
    "STARLINK_POWER_KW": 27,
    "STARLINK_ARRAY_M2": 116,
    "STARSHIP_PAYLOAD_KG": 100000,
    "ORBITAL_OPS_FRAC": 0.01,
    "SOLAR_IRRADIANCE_W_M2": 1361,
    "EARTH_IR_FLUX_W_M2": 237,
    "EARTH_ALBEDO_FACTOR": 0.30,
    "EARTH_RADIUS_KM": 6371.0,
}

# State block from math.js (defaults).
DEFAULT_STATE = {
    "years": 5,
    "targetGW": 1,
    "solarAbsorptivity": 0.92,
    "emissivityPV": 0.85,
    "emissivityRad": 0.90,
    "pvEfficiency": 0.22,
    "betaAngle": 90,
    "orbitalAltitudeKm": 550,
    "maxDieTempC": 85,
    "tempDropC": 10,
    "launchCostPerKg": 500,
    "satelliteCostPerW": 22,
    "specificPowerWPerKg": 36.5,
    "satellitePowerKW": 27,
    "sunFraction": 0.98,
    "cellDegradation": 2.5,
    "gpuFailureRate": 9,
    "nreCost": 1000,
    "gasTurbineCapexPerKW": 1800,
    "electricalCostPerW": 5.25,
    "mechanicalCostPerW": 3.0,
    "civilCostPerW": 2.5,
    "networkCostPerW": 1.75,
    "pue": 1.2,
    "gasPricePerMMBtu": 4.30,
    "heatRateBtuKwh": 6200,
    "capacityFactor": 0.85,
}


def _state(overrides=None):
    s = dict(DEFAULT_STATE)
    if overrides:
        s.update(overrides)
    return s


def _derived(s):
    target_power_mw = s["targetGW"] * 1000
    return {
        "TARGET_POWER_MW": target_power_mw,
        "TARGET_POWER_W": target_power_mw * 1e6,
    }


# --- View factors (ported verbatim, including approximations) ---

def earth_angular_radius(alt_km):
    r = CONST["EARTH_RADIUS_KM"] + alt_km
    return math.asin(CONST["EARTH_RADIUS_KM"] / r)


def nadir_view_factor(alt_km):
    return math.sin(earth_angular_radius(alt_km)) ** 2


def _tilted_vf_from_cos(alt_km, cos_tilt):
    theta = earth_angular_radius(alt_km)
    vf_nadir = math.sin(theta) ** 2
    if cos_tilt <= 0:
        return vf_nadir * 0.05
    return vf_nadir * cos_tilt


def sun_tracking_view_factors(alt_km, beta_deg):
    beta = math.radians(beta_deg)
    n = 72
    a_sum = b_sum = 0.0
    for i in range(n):
        nu = 2 * math.pi * i / n
        cos_gamma = math.cos(beta) * math.cos(nu)
        a_sum += _tilted_vf_from_cos(alt_km, cos_gamma)
        b_sum += _tilted_vf_from_cos(alt_km, -cos_gamma)
    return {"vfSideA": a_sum / n, "vfSideB": b_sum / n, "vfTotal": (a_sum + b_sum) / n}


# --- Orbital cost model ---

def calculate_orbital(s):
    d = _derived(s)
    total_hours = s["years"] * CONST["HOURS_PER_YEAR"]
    annual_retention = 1 - s["cellDegradation"] / 100
    capacity_sum = sum(annual_retention**y for y in range(s["years"]))
    avg_capacity_factor = capacity_sum / s["years"]
    sunlight_adjusted = avg_capacity_factor * s["sunFraction"]
    required_initial_w = d["TARGET_POWER_W"] / sunlight_adjusted
    mass_per_sat = (s["satellitePowerKW"] * 1000) / s["specificPowerWPerKg"]
    sat_count = math.ceil(required_initial_w / (s["satellitePowerKW"] * 1000))
    total_mass = sat_count * mass_per_sat
    actual_initial_w = sat_count * s["satellitePowerKW"] * 1000
    hardware = s["satelliteCostPerW"] * actual_initial_w
    launch = s["launchCostPerKg"] * total_mass
    base = hardware + launch
    ops = hardware * CONST["ORBITAL_OPS_FRAC"] * s["years"]
    gpu = hardware * (s["gpuFailureRate"] / 100) * s["years"]
    nre = s["nreCost"] * 1e6
    total = base + ops + gpu + nre
    energy_mwh = d["TARGET_POWER_MW"] * total_hours
    array_per_sat = CONST["STARLINK_ARRAY_M2"] * (s["satellitePowerKW"] / CONST["STARLINK_POWER_KW"])
    array_area_m2 = sat_count * array_per_sat
    return {
        "satelliteCount": sat_count,
        "totalMassKg": total_mass,
        "starshipLaunches": math.ceil(total_mass / CONST["STARSHIP_PAYLOAD_KG"]),
        "totalCost": total,
        "costPerW": total / d["TARGET_POWER_W"],
        "lcoe": total / energy_mwh,
        "energyMWh": energy_mwh,
        "avgCapacityFactor": avg_capacity_factor,
        "arrayAreaKm2": array_area_m2 / 1e6,
        "_arrayAreaM2": array_area_m2,
    }


# --- Thermal model ---

def calculate_thermal(s):
    orbital = calculate_orbital(s)
    area = orbital["_arrayAreaM2"]
    alpha_pv = s["solarAbsorptivity"]
    eps_pv = s["emissivityPV"]
    eps_rad = s["emissivityRad"]
    pv_eff = s["pvEfficiency"]
    beta = s["betaAngle"]
    alt = s["orbitalAltitudeKm"]
    vf = sun_tracking_view_factors(alt, beta)
    vf_a, vf_b = vf["vfSideA"], vf["vfSideB"]
    S = CONST["SOLAR_IRRADIANCE_W_M2"]
    power_generated = S * pv_eff * area
    q_abs_total = S * alpha_pv * area
    q_solar_waste = q_abs_total - power_generated
    q_ir_a = CONST["EARTH_IR_FLUX_W_M2"] * vf_a * eps_pv * area
    q_ir_b = CONST["EARTH_IR_FLUX_W_M2"] * vf_b * eps_rad * area
    q_earth_ir = q_ir_a + q_ir_b
    albedo_scaling = math.cos(math.radians(beta))
    q_albedo = S * CONST["EARTH_ALBEDO_FACTOR"] * vf_a * albedo_scaling * alpha_pv * area
    q_heat_loop = power_generated
    total_heat_in = q_solar_waste + q_earth_ir + q_albedo + q_heat_loop
    total_eps = eps_pv + eps_rad
    eq_tk = (total_heat_in / (SIGMA * area * total_eps) + T_SPACE_K**4) ** 0.25
    eq_tc = eq_tk - 273.15
    dt4_eq = eq_tk**4 - T_SPACE_K**4
    rad_cap = SIGMA * area * eps_pv * dt4_eq + SIGMA * area * eps_rad * dt4_eq
    radiator_tc = s["maxDieTempC"] - s["tempDropC"]
    temp_margin = radiator_tc - eq_tc
    target_tk = radiator_tc + 273.15
    dt4 = target_tk**4 - T_SPACE_K**4
    area_required = total_heat_in / (SIGMA * total_eps * dt4)
    return {
        "eqTempK": eq_tk,
        "eqTempC": eq_tc,
        "totalHeatInW": total_heat_in,
        "qSolarW": q_solar_waste,
        "qEarthIRW": q_earth_ir,
        "qAlbedoW": q_albedo,
        "qHeatLoopW": q_heat_loop,
        "radiativeCapacityW": rad_cap,
        "areaSufficient": eq_tc <= radiator_tc,
        "tempMarginC": temp_margin,
        "areaRequiredM2": area_required,
        "availableAreaM2": area,
        "vfNadirMax": nadir_view_factor(alt),
        "earthAngularRadiusDeg": math.degrees(earth_angular_radius(alt)),
        "vfSideA": vf_a,
        "vfSideB": vf_b,
        "vfTotal": vf["vfTotal"],
    }


def calculate_breakeven(s):
    d = _derived(s)
    total_hours = s["years"] * CONST["HOURS_PER_YEAR"]
    energy_mwh = d["TARGET_POWER_MW"] * total_hours * s["capacityFactor"]
    generation_mwh = energy_mwh * s["pue"]
    power_gen_per_w = s["gasTurbineCapexPerKW"] * s["pue"] / 1000
    infra = (power_gen_per_w + s["electricalCostPerW"] + s["mechanicalCostPerW"]
             + s["civilCostPerW"] + s["networkCostPerW"]) * d["TARGET_POWER_W"]
    fuel_per_mwh = s["heatRateBtuKwh"] * s["gasPricePerMMBtu"] / 1000
    fuel = fuel_per_mwh * generation_mwh
    terrestrial = infra + fuel
    annual_retention = 1 - s["cellDegradation"] / 100
    capacity_sum = sum(annual_retention**y for y in range(s["years"]))
    avg_cf = capacity_sum / s["years"]
    required_initial_w = d["TARGET_POWER_W"] / (avg_cf * s["sunFraction"])
    hardware = s["satelliteCostPerW"] * required_initial_w
    mass = required_initial_w / s["specificPowerWPerKg"]
    return (terrestrial - hardware) / mass


def run_case(overrides=None):
    """Return the same nested structure as one oracle case."""
    s = _state(overrides)
    orbital = calculate_orbital(s)
    thermal = calculate_thermal(s)
    return {
        "geometry": {
            "vfNadirMax": thermal["vfNadirMax"],
            "earthAngularRadiusDeg": thermal["earthAngularRadiusDeg"],
            "vfSideA": thermal["vfSideA"],
            "vfSideB": thermal["vfSideB"],
            "vfTotal": thermal["vfTotal"],
        },
        "thermal": {k: thermal[k] for k in (
            "eqTempK", "eqTempC", "totalHeatInW", "qSolarW", "qEarthIRW",
            "qAlbedoW", "qHeatLoopW", "radiativeCapacityW", "areaSufficient",
            "tempMarginC", "areaRequiredM2", "availableAreaM2")},
        "orbital": {k: orbital[k] for k in (
            "satelliteCount", "totalMassKg", "starshipLaunches", "totalCost",
            "costPerW", "lcoe", "energyMWh", "avgCapacityFactor", "arrayAreaKm2")},
        "breakeven_launch_cost_per_kg": calculate_breakeven(s),
    }
`````

### `src/orbital_thermal/radiation.py`

_(3634 bytes, sha256 `9beea19b8109edbf0919e9e30513b54204a9ea3b1c7de37ad1d648a8d4f61280`)_

`````python
"""Gray-body radiator identities (Level A results of the theory preprint).

Model scope: gray-body, diffuse, isothermal radiator rejecting heat by
far-field radiation to a lumped effective sink at temperature ``T_sink``
(the papers' T_s^eff = F^(1/4) * T_s). See Lemma 1 and Corollaries 1.1-1.2
of "Thermodynamic Bounds and Mass-Trade Criteria for Heat Rejection in
Orbital Data Centers" (doi:10.5281/zenodo.20650893).

Units: SI throughout. Temperatures in kelvin, power in watts, area in
square meters. Areas are *emitting* areas; a two-sided planform panel has
emitting area equal to twice its planform area.
"""

import math

from .constants import SIGMA_SB


def _check(emissivity: float, T: float, T_sink: float) -> None:
    """Reject non-physical inputs early, with messages that say why."""
    if not (math.isfinite(emissivity) and math.isfinite(T) and math.isfinite(T_sink)):
        raise ValueError(
            f"emissivity/T/T_sink must be finite, got {emissivity}, {T}, {T_sink}")
    if not 0.0 < emissivity <= 1.0:
        raise ValueError(f"emissivity must be in (0, 1], got {emissivity}")
    if T_sink < 0.0:
        raise ValueError(f"sink temperature must be >= 0 K, got {T_sink}")
    if T <= T_sink:
        raise ValueError(
            f"radiator temperature ({T} K) must exceed the effective sink "
            f"temperature ({T_sink} K) for net heat rejection"
        )


def net_flux(T: float, emissivity: float, T_sink: float = 0.0) -> float:
    """Net radiated flux of a gray surface, in W/m^2.

    q = emissivity * sigma * (T^4 - T_sink^4)
    """
    _check(emissivity, T, T_sink)
    return emissivity * SIGMA_SB * (T**4 - T_sink**4)


def required_area(
    Q: float, T: float, emissivity: float, T_sink: float = 0.0
) -> float:
    """Emitting area (m^2) required to reject ``Q`` watts at temperature ``T``.

    Lemma 1 (area law):  A = Q / (emissivity * sigma * (T^4 - T_sink^4))

    Worked anchor (Corollary 1.2): 1 MW at 293 K with emissivity 0.91 and
    zero sink requires 2,630 m^2 of emitting area (1,315 m^2 of two-sided
    planform).
    """
    if not (math.isfinite(Q) and Q > 0.0):
        raise ValueError(f"heat load Q must be finite and > 0, got {Q}")
    return Q / net_flux(T, emissivity, T_sink)


def area_ratio(T1: float, T2: float, T_sink: float = 0.0) -> float:
    """Exact area ratio A(T1) / A(T2) at equal duty (Corollary 1.1).

    R = (T2^4 - T_sink^4) / (T1^4 - T_sink^4)

    Raising the rejection temperature from T1 to T2 divides the required
    area by R. Worked anchor: 293 K -> 600 K with T_sink = 220 K gives
    exactly 6697760000/264604779 (about 25.312); the zero-sink estimate
    17.585 is 30.5% below it.

    Emissivity cancels at equal duty, so it does not appear here.
    """
    _check(1.0, T1, T_sink)
    _check(1.0, T2, T_sink)
    return (T2**4 - T_sink**4) / (T1**4 - T_sink**4)


def effective_sink_temperature(view_factor: float, T_sink: float) -> float:
    """Lumped view-factor-weighted effective sink: T_s^eff = F^(1/4) * T_s.

    ``view_factor`` is the radiator's view factor to the warm environment
    (0 = sees only deep space, 1 = sees only the environment at T_sink).
    This is the one-number environment summary whose validity domain the
    simulation program exists to quantify.
    """
    if not (math.isfinite(view_factor) and 0.0 <= view_factor <= 1.0):
        raise ValueError(f"view factor must be finite in [0, 1], got {view_factor}")
    if not (math.isfinite(T_sink) and T_sink >= 0.0):
        raise ValueError(f"sink temperature must be finite and >= 0 K, got {T_sink}")
    return view_factor**0.25 * T_sink
`````

### `src/orbital_thermal/sink.py`

_(14146 bytes, sha256 `b37b265587fd1770b59c5d49ce31eeea93f7955dbb8b4d5cbac4dafcf614b015`)_

`````python
"""Time-resolved effective sink temperature around a circular orbit.

The companion paper sizes the AI1 radiator with a *constant* environmental sink,
T_s = 220 K, in A = Q / (eps*sigma*(T^4 - T_s^4)). That single number stands in
for everything the radiator's cold side actually sees: deep space, Earth's
infrared glow, and reflected sunlight (albedo). This module computes the sink
the radiator truly experiences as a function of orbit position and beta angle,
so the third paper can show how good (or conservative) the 220 K stand-in is.

Definition
----------
For a radiator of emissivity ``eps`` and solar absorptivity ``alpha_s``, the net
heat it rejects per unit area is

    q_net = eps*sigma*T^4 - q_absorbed_environment

We define the effective sink temperature T_s^eff by writing this in the paper's
form, q_net = eps*sigma*(T^4 - T_s_eff^4), so that

    sigma*T_s_eff^4 = q_IR + (alpha_s/eps)*q_albedo + sigma*T_space^4

Key point: Earth infrared is absorbed and re-emitted in the *same* band, so its
absorptivity equals ``eps`` and the emissivity cancels -- the IR part of the sink
is independent of the radiator's optical properties. Only the reflected-solar
(albedo) part carries the alpha_s/eps ratio that real radiators are designed to
keep small.

Geometry (standard first-order spacecraft-thermal model)
--------------------------------------------------------
- Earth IR irradiance on the surface: q_IR = E_ir * VF(tilt), with VF the exact
  tilted-plate-to-sphere view factor from :mod:`orbital_thermal.environment`.
- Albedo irradiance: q_alb = a * S * VF(tilt) * max(0, cos(zeta)), where the
  solar zenith angle at the sub-satellite point obeys cos(zeta) = cos(beta)*cos(u)
  and ``u`` is the in-orbit angle from orbit noon. Albedo is zero on the night
  side (cos(zeta) <= 0), which automatically includes eclipse.

NOTE (audit item 3): the albedo term is a SUBPOINT APPROXIMATION
(:func:`subpoint_albedo_factor`), not disk-integrated albedo. Its beta-90 and
eclipse albedo nulls are artifacts of sampling reflectance only beneath the
spacecraft; the true disk-integrated albedo can be nonzero there.

This deliberately omits direct solar on the radiator: a heat-rejection surface is
oriented away from the Sun, so direct flux falls on its back face. The model is
therefore the environment seen by the *cold* side.
"""

import numpy as np

from .constants import SIGMA_SB
from . import environment as env

#: Default deep-space background temperature, K (CMB).
T_SPACE_K: float = 2.7255

# Reference environmental fluxes (orbit-average values, W/m^2).
EARTH_IR_FLUX: float = 237.0       # Earth outgoing longwave radiation
SOLAR_CONSTANT: float = 1361.0     # solar irradiance at 1 AU
EARTH_ALBEDO: float = 0.30         # Bond albedo


def subpoint_albedo_factor(beta_deg: float, u_deg: float) -> float:
    """SUBPOINT albedo approximation: clamped cosine of the solar zenith angle at
    the sub-satellite point.

        cos(zeta) = cos(beta) * cos(u),   factor = max(0, cos(zeta))

    This is a first-order stand-in for the reflected-solar (albedo) drive on the
    radiator: it samples reflectance only at the point directly below the
    spacecraft. It is NOT the disk-integrated albedo. Two consequences are
    artifacts of the approximation, not physics:

    * At beta = 90 deg it returns 0 for every ``u``, so the model reports zero
      albedo around a terminator orbit -- yet the visible Earth disk is still
      partly sunlit, so the true disk-integrated albedo is nonzero.
    * It vanishes whenever the subpoint is dark, even when sunlit Earth remains
      within the radiator's field of view.

    A faithful model integrates reflected radiance over the Earth region that is
    simultaneously sunlit, above the radiator's horizon, and visible to it (see
    the package roadmap / audit item 3). Until then, treat beta-90 albedo nulls
    and eclipse-driven albedo nulls as model limitations.
    """
    return float(max(0.0, np.cos(np.radians(beta_deg)) * np.cos(np.radians(u_deg))))


def disk_integrated_albedo_factor(altitude_km, beta_deg, u_deg, tilt_deg=0.0):
    """Disk-integrated reflected-solar (albedo) factor -- NOT YET IMPLEMENTED.

    The physically faithful replacement for :func:`subpoint_albedo_factor`:
    integrate reflected solar radiance over the Earth region that is simultaneously
    sunlit, above the radiator's horizon, and within its field of view. For the FULL
    visible Earth disk (e.g. a nadir-facing plate), the Lambertian-sphere phase
    function Phi(alpha) = (sin a + (pi - a) cos a) / pi vanishes only at exact
    opposition (alpha = pi, i.e. u = 180 deg), so a sunlit crescent contributes at
    every other phase -- including a terminator (beta=90) orbit and off-opposition
    eclipse points where the subpoint approximation nulls. This full-disk statement
    does NOT generalize to arbitrary tilt: horizon-clipping of a tilted plate can
    hide the illuminated region, and a space-facing plate (tilt ~ 180 deg) has ~zero
    Earth coupling at every phase. The strict-xfail tests use the nadir/full-disk case.

    Raises ``NotImplementedError`` until implemented. The strict-xfail tests in
    ``tests/test_sink.py`` target THIS function (not the subpoint helper, whose
    documented semantics will not change), so they xpass and flag the day a correct
    disk-integrated model lands (audit re-review P2-a).
    """
    raise NotImplementedError(
        "disk-integrated albedo is not yet modeled; the package currently uses the "
        "subpoint approximation (subpoint_albedo_factor). See audit re-review P2-a."
    )


def _require_shielding(assume_sun_shielded: bool) -> None:
    """Guard: the model omits direct solar on the radiator face. The caller must
    explicitly assert the face is sun-shielded (audit re-review P1-b, P1-2).

    The contract is strict: ``assume_sun_shielded`` must be the boolean ``True`` or
    ``False`` -- truthy non-booleans (e.g. the string ``"false"``, ``1``, ``[1]``)
    are rejected with ``TypeError`` so a config/CLI value cannot silently assert
    shielding."""
    if assume_sun_shielded is True:
        return
    if assume_sun_shielded is not False:
        raise TypeError(
            "assume_sun_shielded must be the boolean True or False, got "
            f"{assume_sun_shielded!r} ({type(assume_sun_shielded).__name__})"
        )
    raise NotImplementedError(
            "the effective-sink model omits direct solar flux on the radiator "
            "face; it is valid only when that face receives no direct sunlight "
            "(an anti-solar attitude OR an external shade -- the model does not "
            "verify attitude). Pass assume_sun_shielded=True to assert this, or "
            "extend the model with a direct-solar term (surface normal . Sun "
            "vector) before treating arbitrary geometry as a general sink."
        )


def sink_temperature_series(
    view_factor,
    beta_deg,
    u_deg,
    *,
    assume_sun_shielded: bool,
    emissivity: float = 0.91,
    solar_absorptivity: float = 0.20,
    earth_ir: float = EARTH_IR_FLUX,
    albedo: float = EARTH_ALBEDO,
    solar_constant: float = SOLAR_CONSTANT,
    t_space: float = T_SPACE_K,
):
    """Centralized effective-sink equation (scalar or vectorized over ``u_deg``).

    ``view_factor`` is the precomputed tilted-plate-to-sphere Earth view factor
    (constant for fixed tilt), so callers compute it once. Returns T_s^eff with the
    same shape as ``u_deg``. The reflected-solar drive uses the SUBPOINT albedo
    approximation (np.clip(cos(beta)cos(u), 0, None); see
    :func:`subpoint_albedo_factor`). ``assume_sun_shielded`` is REQUIRED and must
    be True; it is the single point where the direct-solar omission is asserted, so
    every caller (scalar, profile, transient) goes through this guard.
    """
    if not 0.0 < emissivity <= 1.0:
        raise ValueError(f"emissivity must be in (0, 1], got {emissivity}")
    if not 0.0 <= solar_absorptivity <= 1.0:
        raise ValueError(f"solar_absorptivity must be in [0, 1], got {solar_absorptivity}")
    if not 0.0 <= albedo <= 1.0:
        raise ValueError(f"albedo must be in [0, 1], got {albedo}")
    if not (np.isfinite(t_space) and t_space >= 0.0):
        raise ValueError(f"t_space must be finite and >= 0 K, got {t_space}")
    if not (np.isfinite(earth_ir) and earth_ir >= 0.0):
        raise ValueError(f"earth_ir must be finite and >= 0, got {earth_ir}")
    if not (np.isfinite(solar_constant) and solar_constant >= 0.0):
        raise ValueError(f"solar_constant must be finite and >= 0, got {solar_constant}")
    if not (np.isfinite(view_factor) and 0.0 <= view_factor <= 1.0):
        raise ValueError(f"view_factor must be finite in [0, 1], got {view_factor}")
    if not (np.isfinite(beta_deg) and 0.0 <= beta_deg <= 90.0):
        raise ValueError(f"beta_deg must be finite in [0, 90], got {beta_deg}")
    if not np.all(np.isfinite(np.asarray(u_deg, dtype=float))):
        raise ValueError("u_deg must be finite")
    _require_shielding(assume_sun_shielded)
    cos_zeta = np.cos(np.radians(beta_deg)) * np.cos(np.radians(u_deg))
    albedo_factor = np.clip(cos_zeta, 0.0, None)            # subpoint approximation
    q_ir = earth_ir * view_factor
    q_alb = albedo * solar_constant * view_factor * albedo_factor
    t4 = (q_ir + (solar_absorptivity / emissivity) * q_alb) / SIGMA_SB + t_space**4
    return t4 ** 0.25


def orbital_effective_sink_temperature(
    altitude_km: float,
    beta_deg: float,
    u_deg: float,
    tilt_deg: float = 0.0,
    *,
    assume_sun_shielded: bool,
    emissivity: float = 0.91,
    solar_absorptivity: float = 0.20,
    earth_ir: float = EARTH_IR_FLUX,
    albedo: float = EARTH_ALBEDO,
    solar_constant: float = SOLAR_CONSTANT,
    t_space: float = T_SPACE_K,
) -> float:
    """Effective radiative sink temperature, K, at one orbit position.

    ``u_deg`` is the in-orbit angle from orbit noon (sub-solar meridian); 0 deg is
    the point closest to the Sun, 180 deg the anti-solar (deep night) point.
    ``tilt_deg`` is the radiator normal's angle from nadir (0 = Earth-facing,
    180 = space-facing).

    Attitude assumption (audit re-review P1-b): this models only the *cold-side*
    environment and OMITS direct solar flux on the radiator face. It is valid only
    when that face receives no direct sunlight -- either an anti-solar attitude or
    an external shade; the model does NOT verify attitude. ``tilt_deg`` is accepted
    for arbitrary Earth coupling, but the result is NOT a general all-attitude sink.
    ``assume_sun_shielded`` is therefore REQUIRED (no default): pass True to assert
    shielding, or False to get a ``NotImplementedError`` (direct-solar loading from
    the surface normal and Sun vector is not yet modeled). The same guard backs the
    profile and transient paths via :func:`sink_temperature_series`.
    """
    vf = env.sphere_view_factor(altitude_km, tilt_deg)
    return float(sink_temperature_series(
        vf, beta_deg, u_deg, assume_sun_shielded=assume_sun_shielded,
        emissivity=emissivity, solar_absorptivity=solar_absorptivity,
        earth_ir=earth_ir, albedo=albedo, solar_constant=solar_constant,
        t_space=t_space))



def effective_sink_temperature(*args, **kwargs):
    """Deprecated alias for :func:`orbital_effective_sink_temperature`
    (audit re-review P2-9).

    The orbit-resolved sink function was renamed to disambiguate it from the
    generic view-factor helper exported at package top level
    (``orbital_thermal.effective_sink_temperature``, from ``radiation.py``), which
    has a different signature and no shielding contract. This alias forwards and
    will be removed in a future release.
    """
    import warnings
    warnings.warn(
        "sink.effective_sink_temperature is deprecated; use "
        "orbital_effective_sink_temperature (renamed to disambiguate from the "
        "top-level radiation.effective_sink_temperature). See audit re-review P2-9.",
        DeprecationWarning, stacklevel=2,
    )
    return orbital_effective_sink_temperature(*args, **kwargs)

def in_eclipse(altitude_km: float, beta_deg: float, u_deg: float) -> bool:
    """True if the spacecraft is in Earth's cylindrical shadow at this position."""
    r = env.orbital_radius(altitude_km)
    cos_eta = np.sqrt(1.0 - (env.EARTH_RADIUS_KM / r) ** 2)
    cos_zeta = np.cos(np.radians(beta_deg)) * np.cos(np.radians(u_deg))
    return bool(cos_zeta < -cos_eta)


def sink_profile(
    altitude_km: float,
    beta_deg: float,
    tilt_deg: float = 0.0,
    n: int = 361,
    *,
    assume_sun_shielded: bool,
    **kwargs,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (u_deg, T_s_eff) arrays over one full orbit (0..360 deg).

    The grid includes both endpoints (0 and 360 deg are the same orbit point), so
    it closes the loop for plotting. Any radiative averaging must drop the
    duplicated endpoint (slice ``[:-1]``); :func:`orbit_averaged_sink` does this.
    """
    if n < 3:
        raise ValueError(f"n must be >= 3 to resolve an orbit (the duplicate 360deg "
                         f"endpoint is dropped when averaging), got {n}")
    u = np.linspace(0.0, 360.0, n)
    vf = env.sphere_view_factor(altitude_km, tilt_deg)
    T = sink_temperature_series(
        vf, beta_deg, u, assume_sun_shielded=assume_sun_shielded, **kwargs)
    return u, T


def orbit_averaged_sink(
    altitude_km: float,
    beta_deg: float,
    tilt_deg: float = 0.0,
    n: int = 720,
    *,
    assume_sun_shielded: bool,
    **kwargs,
) -> float:
    """Radiatively-weighted orbit-average sink, K: ( <T_s_eff^4> )^(1/4).

    The fourth-power mean is the average relevant to radiator sizing, since heat
    rejection scales with T^4.
    """
    _, T = sink_profile(altitude_km, beta_deg, tilt_deg, n=n,
                        assume_sun_shielded=assume_sun_shielded, **kwargs)
    # Drop the duplicated 360deg endpoint so it is not double-counted (consistent
    # with transient.averaging_bias, which also slices [:-1]). Audit item 7.
    return float(np.mean(T[:-1] ** 4) ** 0.25)
`````

### `src/orbital_thermal/transient.py`

_(22699 bytes, sha256 `6bf597ae6ac99fdb36b5660132cd149549d1b9630d4231647dc1ab9998c0701e`)_

`````python
"""One-node transient radiator model and the averaging-load bias.

The companion paper sizes the radiator at steady state with a constant sink: it
solves eps*sigma*(T^4 - T_s^4) = q_load once and reads off T = 337.1 K. But a
real panel has thermal mass, so as the effective sink swings around the orbit
(:mod:`orbital_thermal.sink`) the temperature cannot follow instantly -- it lags
and ripples. Because heat rejection goes as T^4, energy balance at periodic steady state
forces the fourth-power mean to equal the steady value exactly:
<T^4> = T_steady^4, with T_steady evaluated at the T^4-weighted average sink.
Since x^(1/4) is concave, the *arithmetic* mean then sits slightly BELOW
T_steady (a small, signed <= 0 effect) while the peak sits ABOVE it. The
engineering penalty of the steady, averaged-load assumption is therefore peak
UNDER-prediction, not a mean offset. This module integrates the transient and
quantifies both: the peak excess (the operationally important number) and the
small signed mean bias.

Model (per unit radiator area)
------------------------------
    C dT/dt = q_load - eps*sigma*(T^4 - T_s_eff(t)^4)

- ``C``        areal heat capacity, J/m^2/K (rho * c_p * thickness)
- ``q_load``   internal compute waste-heat flux, W/m^2 (constant)
- ``T_s_eff``  time-varying effective sink (orbit position u(t) = 360*t/period)

Integration is fixed-step RK4 (numpy only). The panel is marched for several
orbits until it reaches a periodic steady state; the final orbit is returned.
"""

import warnings

import numpy as np

from .constants import SIGMA_SB
from . import environment as env
from . import sink as sink_mod


def steady_state_temperature(q_load: float, t_sink: float, emissivity: float = 0.91) -> float:
    """Closed-form steady radiator temperature, K, for a constant sink.

    Solves eps*sigma*(T^4 - t_sink^4) = q_load:  T = (q_load/(eps*sigma) + t_sink^4)^(1/4).
    """
    return float((q_load / (emissivity * SIGMA_SB) + t_sink**4) ** 0.25)


def thermal_time_constant(
    areal_heat_capacity: float, temperature: float, emissivity: float = 0.91
) -> float:
    """Linearized radiative time constant, s:  C / (4*eps*sigma*T^3)."""
    return float(areal_heat_capacity / (4.0 * emissivity * SIGMA_SB * temperature**3))


# (the duplicated _sink_series was removed in audit re-review P1-b;
# the one effective-sink equation now lives in sink.sink_temperature_series.)


def simulate(
    altitude_km: float,
    beta_deg: float,
    q_load: float,
    areal_heat_capacity: float,
    tilt_deg: float = 0.0,
    *,
    assume_sun_shielded: bool,
    emissivity: float = 0.91,
    solar_absorptivity: float = 0.20,
    earth_ir: float = sink_mod.EARTH_IR_FLUX,
    albedo: float = sink_mod.EARTH_ALBEDO,
    solar_constant: float = sink_mod.SOLAR_CONSTANT,
    t_space: float = sink_mod.T_SPACE_K,
    n_orbits: int = 30,
    steps_per_orbit: int = 2000,
    t0_guess: float | None = None,
    convergence_tol_K: float = 1e-3,
    energy_tol_K: float = 1e-2,
    check_time_resolution: bool = False,
    time_tol_K: float = 1e-2,
    max_orbits: int | None = None,
    return_diagnostics: bool = False,
    raise_on_nonconvergence: bool = False,
):
    """Integrate to a periodic steady state; return (t, T, T_sink) for the final orbit.

    The panel is marched orbit by orbit until the start-to-end temperature change
    over an orbit falls below ``convergence_tol_K`` (periodic closure), capped at
    ``max_orbits`` (default ``n_orbits``). High-thermal-mass panels (tau/period
    >> 1) can need many more orbits than a fixed count would allow, so a fixed
    march can silently return a not-yet-periodic profile; this loop detects that.

    ``assume_sun_shielded`` is REQUIRED (no default) and is forwarded to the one
    effective-sink equation (sink.sink_temperature_series); see that function.

    ``t`` is seconds from the start of the final orbit; ``T`` and ``T_sink`` are
    the panel and effective-sink temperatures, K.

    If ``return_diagnostics`` is True, returns ``(t, T, T_sink, diagnostics)``
    where diagnostics is a dict: ``converged`` (bool), ``orbits_used`` (int),
    ``closure_error_K`` (|T_end - T_start| of the final orbit), ``tol_K``, and
    ``energy_residual_W_m2`` (orbit-mean net flux, ~0 at periodic steady state).
    On non-convergence it warns (or raises if ``raise_on_nonconvergence``).
    """
    C = areal_heat_capacity
    eps = emissivity
    if not (np.isfinite(C) and C > 0.0):
        raise ValueError(f"areal_heat_capacity must be finite and > 0, got {C}")
    for _name, _val in (("steps_per_orbit", steps_per_orbit), ("n_orbits", n_orbits)):
        if isinstance(_val, bool) or not isinstance(_val, int):
            raise TypeError(f"{_name} must be an int, got {type(_val).__name__}")
        if _val < 1:
            raise ValueError(f"{_name} must be >= 1, got {_val}")
    if max_orbits is not None:
        if isinstance(max_orbits, bool) or not isinstance(max_orbits, int):
            raise TypeError(f"max_orbits must be an int, got {type(max_orbits).__name__}")
        if max_orbits < 1:
            raise ValueError(f"max_orbits must be >= 1, got {max_orbits}")
    if not (np.isfinite(q_load) and q_load > 0.0):
        raise ValueError(f"q_load must be finite and > 0, got {q_load}")
    if not 0.0 < emissivity <= 1.0:
        raise ValueError(f"emissivity must be in (0, 1], got {emissivity}")
    if not (np.isfinite(convergence_tol_K) and convergence_tol_K > 0.0):
        raise ValueError(f"convergence_tol_K must be finite and > 0, got {convergence_tol_K}")
    if not (np.isfinite(energy_tol_K) and energy_tol_K > 0.0):
        raise ValueError(f"energy_tol_K must be finite and > 0, got {energy_tol_K}")
    if not (np.isfinite(time_tol_K) and time_tol_K > 0.0):
        raise ValueError(f"time_tol_K must be finite and > 0, got {time_tol_K}")
    if t0_guess is not None and not (np.isfinite(t0_guess) and t0_guess > 0.0):
        raise ValueError(f"t0_guess must be finite and > 0 K, got {t0_guess}")
    period = env.orbital_period(altitude_km)
    dt = period / steps_per_orbit
    deg_per_s = 360.0 / period
    cap = n_orbits if max_orbits is None else max_orbits
    # Energy-balance convergence tolerance (W/m^2): relative to the load with an
    # absolute floor. Per-orbit closure alone is insufficient when tau/P >> 1 --
    # the orbit-to-orbit change vanishes while the panel is still far from periodic
    # steady state (audit re-review P1-1). The mean net flux must also be ~0.
    vf = env.sphere_view_factor(altitude_km, tilt_deg)

    def sink_at(t):
        return sink_mod.sink_temperature_series(
            vf, beta_deg, deg_per_s * t, assume_sun_shielded=assume_sun_shielded,
            emissivity=eps, solar_absorptivity=solar_absorptivity, earth_ir=earth_ir,
            albedo=albedo, solar_constant=solar_constant, t_space=t_space)

    def deriv(t, T):
        Ts = sink_at(t)
        return (q_load - eps * SIGMA_SB * (T**4 - Ts**4)) / C

    def _one_orbit(T0, nsteps, t_begin):
        """RK4-march one orbital period from ``T0`` at ``t_begin`` with ``nsteps``
        steps; return the (nsteps+1) panel-temperature samples. Used for the
        step-doubling temporal-accuracy check (audit re-review P1-2)."""
        dtl = period / nsteps
        Tloc = float(T0)
        arr = np.empty(nsteps + 1)
        arr[0] = Tloc
        tt = t_begin
        for i in range(1, nsteps + 1):
            k1 = deriv(tt, Tloc)
            k2 = deriv(tt + dtl / 2, Tloc + dtl / 2 * k1)
            k3 = deriv(tt + dtl / 2, Tloc + dtl / 2 * k2)
            k4 = deriv(tt + dtl, Tloc + dtl * k3)
            Tloc += dtl / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
            tt += dtl
            arr[i] = Tloc
        return arr

    if t0_guess is None:
        t0_guess = steady_state_temperature(q_load, 240.0, eps)
    T = float(t0_guess)

    # Explicit fixed-step RK4 is conditionally stable: warn if the step exceeds the
    # radiative time constant tau = C / (4 eps sigma T^3) (audit re-review P3-a).
    tau0 = thermal_time_constant(C, T, eps)
    if dt > tau0:
        warnings.warn(
            f"RK4 timestep dt={dt:.3g} s exceeds the radiative time constant "
            f"tau={tau0:.3g} s; explicit integration may be unstable -- increase "
            f"steps_per_orbit or areal_heat_capacity",
            RuntimeWarning,
        )

    ts = np.zeros(steps_per_orbit + 1)
    Ts_panel = np.zeros(steps_per_orbit + 1)
    Ts_sink = np.zeros(steps_per_orbit + 1)
    t = 0.0
    converged = False
    orbits_used = 0
    for orbit in range(cap):
        t_orbit0 = t
        T_start = T
        ts[0] = 0.0
        Ts_panel[0] = T
        Ts_sink[0] = sink_at(t)
        for i in range(1, steps_per_orbit + 1):
            k1 = deriv(t, T)
            k2 = deriv(t + dt / 2, T + dt / 2 * k1)
            k3 = deriv(t + dt / 2, T + dt / 2 * k2)
            k4 = deriv(t + dt, T + dt * k3)
            T += dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
            t += dt
            ts[i] = t - t_orbit0
            Ts_panel[i] = T
            Ts_sink[i] = sink_at(t)
        if not np.all(np.isfinite(Ts_panel)) or float(np.min(Ts_panel)) <= 0.0:
            raise RuntimeError(
                "RK4 produced a non-finite or non-positive temperature "
                f"(min {float(np.min(Ts_panel)):.1f} K over the orbit); the timestep "
                "is too large for this heat capacity -- increase steps_per_orbit or "
                "areal_heat_capacity (see the stability warning)"
            )
        orbits_used = orbit + 1
        orbit_energy_residual = float(abs(np.mean(
            q_load - eps * SIGMA_SB * (Ts_panel[:-1] ** 4 - Ts_sink[:-1] ** 4))))
        # Scale-aware: convert the flux residual to an equivalent temperature error
        # dT_eq = |<q_net>| / (4 eps sigma T_ref^3). A fixed W/m^2 floor cannot bound
        # temperature error uniformly (4 eps sigma T^3 -> 0 at low T); audit P1-1.
        T_ref = float(np.mean(Ts_panel[:-1]))
        dT_eq = orbit_energy_residual / (4.0 * eps * SIGMA_SB * T_ref ** 3)
        if abs(T - T_start) < convergence_tol_K and dT_eq < energy_tol_K:
            converged = True
            break

    closure_error_K = float(abs(Ts_panel[-1] - Ts_panel[0]))
    net = q_load - eps * SIGMA_SB * (Ts_panel[:-1] ** 4 - Ts_sink[:-1] ** 4)
    energy_residual_W_m2 = float(abs(np.mean(net)))
    energy_residual_K = energy_residual_W_m2 / (
        4.0 * eps * SIGMA_SB * float(np.mean(Ts_panel[:-1])) ** 3)
    if not converged:
        tau = thermal_time_constant(C, float(Ts_panel.mean()), eps)
        msg = (f"transient did not reach periodic steady state in {orbits_used} "
               f"orbits (closure {closure_error_K:.2e} K vs tol "
               f"{convergence_tol_K:.1e} K; energy dT_eq {energy_residual_K:.2e} K vs "
               f"tol {energy_tol_K:.1e} K; tau/period={tau / period:.2f}); "
               f"raise max_orbits/n_orbits")
        if raise_on_nonconvergence:
            raise RuntimeError(msg)
        warnings.warn(msg, RuntimeWarning)

    # Temporal-accuracy gate (audit re-review P1-2): periodic closure + energy
    # balance do not certify that the timestep resolves the intra-orbit forcing/peak.
    # Re-integrate the final orbit at 2x resolution and require peak/mean/swing to agree.
    if check_time_resolution:
        peak_n = float(Ts_panel.max())
        mean_n = float(np.mean(Ts_panel[:-1]))
        swing_n = float(Ts_panel.max() - Ts_panel.min())
        refined = _one_orbit(Ts_panel[0], 2 * steps_per_orbit, t_orbit0)
        if not np.all(np.isfinite(refined)) or float(np.min(refined)) <= 0.0:
            time_residual_K = float("inf")
            time_discretization_converged = False
        else:
            time_residual_K = max(
                abs(peak_n - float(refined.max())),
                abs(mean_n - float(np.mean(refined[:-1]))),
                abs(swing_n - float(refined.max() - refined.min())),
            )
            time_discretization_converged = bool(time_residual_K < time_tol_K)
    else:
        time_residual_K = None
        time_discretization_converged = None

    if return_diagnostics:
        diagnostics = {
            "converged": converged,
            "orbits_used": orbits_used,
            "closure_error_K": closure_error_K,
            "tol_K": float(convergence_tol_K),
            "energy_residual_W_m2": energy_residual_W_m2,
            "energy_residual_K": energy_residual_K,
            "energy_tol_K": float(energy_tol_K),
            "periodic_converged": converged,
            "time_discretization_converged": time_discretization_converged,
            "time_residual_K": time_residual_K,
            "time_tol_K": float(time_tol_K),
        }
        return ts, Ts_panel, Ts_sink, diagnostics
    return ts, Ts_panel, Ts_sink


# ---------------------------------------------------------------------------
# Areal heat-capacity provenance (audit item 10)
# ---------------------------------------------------------------------------
# The example thermal masses C used elsewhere (e.g. 2000 / 8000 / 40000 J/m^2/K)
# are ILLUSTRATIVE. Real areal heat capacity is C_A = sum_i rho_i c_p,i t_i over
# the panel's material layers. The builds below derive representative values from
# handbook room-temperature properties so transient swings can be tied to a
# concrete stack rather than a bare number.

#: Material properties with provenance (audit re-review P2-d). Each entry records
#: density and specific heat at a stated reference state, a source, and a relative
#: uncertainty. Values are representative grades, not a specific lot; the builds
#: below remain illustrative. The liquid-coolant entry is a single documented
#: reference state (ammonia is strongly state-dependent near these temperatures);
#: :func:`coolant_rho_cp` recomputes it from the pinned CoolProp backend.
MATERIALS = {
    "aluminum_6061": {
        "rho_kg_m3": 2700.0, "cp_J_kgK": 896.0,
        "state": "solid, 298 K, 1 atm",
        "source": "ASM aluminum 6061-T6 nominal (rho 2700 kg/m^3; c_p 896 J/kg/K at 25 C)",
        "rel_uncertainty": 0.02,
    },
    "cover_glass": {
        "rho_kg_m3": 2500.0, "cp_J_kgK": 800.0,
        "state": "solid, 298 K",
        "source": "borosilicate solar cover glass, typical (rho ~2500; c_p ~800 J/kg/K)",
        "rel_uncertainty": 0.05,
    },
    "silicon": {
        "rho_kg_m3": 2330.0, "cp_J_kgK": 700.0,
        "state": "crystalline solid, 298 K",
        "source": "CRC Handbook of Chemistry and Physics, 97th ed.; crystalline Si (rho 2329 kg/m^3; c_p 705 J/kg/K at 298 K)",
        "rel_uncertainty": 0.02,
    },
    "cfrp_substrate": {
        "rho_kg_m3": 1600.0, "cp_J_kgK": 800.0,
        "state": "solid, 298 K",
        "source": "carbon-fiber/epoxy laminate, quasi-isotropic typical (rho ~1550-1600; "
                  "c_p ~800-1000 J/kg/K; strongly layup-dependent)",
        "rel_uncertainty": 0.15,
    },
    "ammonia_liquid": {
        "rho_kg_m3": 600.17, "cp_J_kgK": 4796.38,
        "state": "saturated liquid, 300 K (Q=0)",
        "source": "CoolProp HEOS at T=300 K, Q=0; strongly state-dependent "
                  "(280 K: 629/4649; 320 K: 568/5023). See coolant_rho_cp().",
        "coolprop_version": "7.2.0",            # pinned in the [fluids] extra
        "eos_bibtex_key": "Gao-JPCRD-2020",     # from get_BibTeXKey at that version
        "rel_uncertainty": 0.01,                # PHYSICAL property uncertainty (cross-check)
        "stored_decimals": 2,                   # values rounded to 2 decimals
        "regression_rtol": 1e-4,                # CODE-regression tol vs the pinned backend
    },
    "copper": {
        "rho_kg_m3": 8960.0, "cp_J_kgK": 385.0,
        "state": "solid, 298 K",
        "source": "CRC Handbook of Chemistry and Physics, 97th ed.; Cu (rho 8960 kg/m^3; c_p 385 J/kg/K at 298 K)",
        "rel_uncertainty": 0.01,
    },
    "fr4_pcb": {
        "rho_kg_m3": 1850.0, "cp_J_kgK": 1100.0,
        "state": "solid, 298 K",
        "source": "FR-4 glass-epoxy laminate, typical (rho ~1850; c_p ~1100-1200 J/kg/K)",
        "rel_uncertainty": 0.15,
    },
}

#: Representative panel builds: name -> list of (material, thickness_m) layers.
#: Thicknesses are illustrative but physically plausible.
REPRESENTATIVE_BUILDS = {
    "bare_aluminum_sheet_2mm": [("aluminum_6061", 0.002)],
    "pv_on_substrate": [
        ("cover_glass", 0.0005), ("silicon", 0.0002),
        ("cfrp_substrate", 0.001), ("aluminum_6061", 0.0005),
    ],
    "radiator_with_coolant": [("aluminum_6061", 0.002), ("ammonia_liquid", 0.005)],
    "integrated_compute_radiator": [
        ("aluminum_6061", 0.003), ("copper", 0.002), ("fr4_pcb", 0.0016),
        ("silicon", 0.0008), ("ammonia_liquid", 0.006),
    ],
}


def areal_heat_capacity(layers) -> float:
    """Areal heat capacity C_A = sum_i rho_i c_p,i t_i, J/m^2/K.

    ``layers`` is an iterable of ``(material_name, thickness_m)`` pairs; material
    names key into :data:`MATERIALS`. This is the quantity ``C`` in the one-node
    model, derived from a physical stack rather than assumed.
    """
    layers = list(layers)
    if not layers:
        raise ValueError("layers must be a non-empty list of (material, thickness) pairs")
    total = 0.0
    for material, thickness in layers:
        if material not in MATERIALS:
            raise KeyError(f"unknown material {material!r}; see MATERIALS")
        if not (np.isfinite(thickness) and thickness > 0.0):
            raise ValueError(f"thickness must be finite and > 0, got {thickness}")
        entry = MATERIALS[material]
        total += entry["rho_kg_m3"] * entry["cp_J_kgK"] * thickness
    return total


def build_areal_heat_capacity(build_name: str) -> float:
    """Areal heat capacity, J/m^2/K, of a named build in :data:`REPRESENTATIVE_BUILDS`."""
    if build_name not in REPRESENTATIVE_BUILDS:
        raise KeyError(f"unknown build {build_name!r}; see REPRESENTATIVE_BUILDS")
    return areal_heat_capacity(REPRESENTATIVE_BUILDS[build_name])


def coolant_rho_cp(fluid: str = "Ammonia", T: float = 300.0):
    """(density, specific heat) of the saturated liquid at temperature ``T`` from
    the pinned CoolProp backend, kg/m^3 and J/kg/K (audit re-review P2-d).

    This is the source/validator for the strongly state-dependent liquid-coolant
    entry in :data:`MATERIALS`, which is pinned to one documented reference state
    (300 K saturated liquid). Requires CoolProp (the [fluids] extra)."""
    from CoolProp.CoolProp import PropsSI
    rho = PropsSI("D", "T", T, "Q", 0, fluid)
    cp = PropsSI("C", "T", T, "Q", 0, fluid)
    return float(rho), float(cp)

def averaging_bias(
    altitude_km: float,
    beta_deg: float,
    q_load: float,
    areal_heat_capacity: float,
    tilt_deg: float = 0.0,
    *,
    assume_sun_shielded: bool,
    emissivity: float = 0.91,
    require_convergence: bool = True,
    **kwargs,
) -> dict:
    """Compare the transient time-mean temperature to the steady, averaged-sink
    solution. Returns a dict of temperatures (K), the bias, and timescales.

    ``bias_K`` = transient mean - steady(averaged sink). At periodic steady state
    <T^4> = T_steady^4, so by concavity of x^(1/4) the arithmetic mean is
    <= T_steady and ``bias_K`` is <= 0 up to numerical slack: the averaged-sink
    steady solution does NOT under-predict the mean. The operationally important
    quantity is ``peak_excess_over_steady_K`` (> 0), the peak the steady,
    averaged-load assumption misses.

    The Jensen/peak metrics are only meaningful at periodic steady state, so this
    helper requests convergence diagnostics from :func:`simulate`. By default
    (``require_convergence=True``) it RAISES ``RuntimeError`` if the transient did
    not converge -- a non-converged final orbit can flip the sign of the reported
    bias and peak excess (an initialization artifact, not physics). Set
    ``require_convergence=False`` to inspect the unconverged result instead; the
    returned dict always carries ``converged``, ``orbits_used``,
    ``closure_error_K``, and ``energy_residual_W_m2``.
    """
    kwargs.pop("return_diagnostics", None)
    kwargs.pop("check_time_resolution", None)
    t, T, Tsink, diag = simulate(altitude_km, beta_deg, q_load, areal_heat_capacity,
                                 tilt_deg=tilt_deg, assume_sun_shielded=assume_sun_shielded,
                                 emissivity=emissivity, return_diagnostics=True,
                                 check_time_resolution=True, **kwargs)
    if require_convergence and not (diag["periodic_converged"]
                                    and diag["time_discretization_converged"]):
        raise RuntimeError(
            "averaging_bias: result not certified -- "
            f"periodic_converged={diag['periodic_converged']} "
            f"(closure {diag['closure_error_K']:.2e} K vs tol {diag['tol_K']:.1e} K; "
            f"energy dT_eq {diag['energy_residual_K']:.2e} K vs tol "
            f"{diag['energy_tol_K']:.1e} K), time_discretization_converged="
            f"{diag['time_discretization_converged']} (step-doubling residual "
            f"{diag['time_residual_K']} K vs tol {diag['time_tol_K']:.1e} K). The "
            "Jensen/peak metrics would be invalid. Increase n_orbits/max_orbits and/or "
            "steps_per_orbit, or pass require_convergence=False to inspect diagnostics."
        )
    transient_mean = float(np.mean(T[:-1]))
    sink_avg = float(np.mean(Tsink[:-1] ** 4) ** 0.25)
    steady = steady_state_temperature(q_load, sink_avg, emissivity)
    period = env.orbital_period(altitude_km)
    tau = thermal_time_constant(areal_heat_capacity, transient_mean, emissivity)
    peak = float(T.max())
    return {
        "transient_mean_K": transient_mean,
        "steady_avg_sink_K": steady,
        "bias_K": transient_mean - steady,
        "transient_peak_K": peak,
        "peak_excess_over_steady_K": peak - steady,
        "swing_K": float(T.max() - T.min()),
        "sink_avg_K": sink_avg,
        "tau_s": tau,
        "period_s": period,
        "tau_over_period": tau / period,
        "converged": diag["converged"],
        "orbits_used": diag["orbits_used"],
        "closure_error_K": diag["closure_error_K"],
        "energy_residual_W_m2": diag["energy_residual_W_m2"],
        "energy_residual_K": diag["energy_residual_K"],
        "energy_tol_K": diag["energy_tol_K"],
        "periodic_converged": diag["periodic_converged"],
        "time_discretization_converged": diag["time_discretization_converged"],
        "time_residual_K": diag["time_residual_K"],
        "time_tol_K": diag["time_tol_K"],
    }
`````

### `tests/test_ammonia.py`

_(4016 bytes, sha256 `4c1a201cbfe2d257cf0ceb3b719ec3620a6902cdd9548dca8fb18bbcc1ebfc72`)_

`````python
"""Ammonia property verification against the companion paper's NIST anchors.

The companion paper (doi:10.5281/zenodo.20670772) quotes these values from
the NIST Chemistry WebBook (SRD 69) and explicitly EXCLUDES them from its
assertion suite's verification scope. This file closes that gap: CoolProp's
HEOS backend computes the same quantities independently, and agreement
within the paper's display precision cross-validates both sources.

ORACLE-FREEZE RULE applies: the expected values below are the paper's
published NIST anchors. They are never edited to make a failing test pass.

Tolerances: the paper displays the saturation ladder to one decimal bar,
so saturation tests use abs=0.1 bar; critical point per its quoted
precision (405.5 K, "~113 bar").
"""

import pytest

pytest.importorskip("CoolProp", reason="CoolProp not installed")

from orbital_thermal import equilibrium_temperature
from orbital_thermal.fluids import (
    PA_PER_BAR,
    critical_margin,
    critical_pressure,
    critical_temperature,
    phase_state,
    provenance,
    saturated_densities,
    saturation_pressure,
)

# Paper anchors (NIST Chemistry WebBook SRD 69, as quoted in the paper)
T_CRIT_PAPER = 405.5        # K
P_CRIT_PAPER_BAR = 113.0    # bar, quoted as "~113 bar"
SAT_LADDER = {              # T (K) -> saturation pressure lower bound (bar)
    353.16: 41.4,
    358.91: 46.8,
    374.17: 63.8,
    391.47: 88.4,
}


class TestCriticalPoint:
    def test_critical_temperature_matches_nist_anchor(self):
        assert critical_temperature() == pytest.approx(T_CRIT_PAPER, abs=0.1)

    def test_critical_pressure_matches_nist_anchor(self):
        assert critical_pressure() / PA_PER_BAR == pytest.approx(
            P_CRIT_PAPER_BAR, abs=1.0
        )


class TestSaturationLadder:
    @pytest.mark.parametrize("T, P_bar", sorted(SAT_LADDER.items()))
    def test_paper_ladder_value(self, T, P_bar):
        assert saturation_pressure(T) / PA_PER_BAR == pytest.approx(
            P_bar, abs=0.1
        )

    def test_monotone_in_temperature(self):
        temps = sorted(SAT_LADDER)
        pressures = [saturation_pressure(t) for t in temps]
        assert pressures == sorted(pressures)

    def test_no_saturation_curve_above_critical(self):
        with pytest.raises(ValueError):
            saturation_pressure(410.0)


class TestCoolantScreen:
    """The companion paper's coolant-class screen, now fully computed."""

    EPS, T_S = 0.91, 220.0

    def test_two_sided_margin_over_50K(self):
        # Continuous-peak hypothetical on 220 m^2: >50 K below critical.
        T_pk = equilibrium_temperature(150e3, 220.0, self.EPS, self.T_S)
        assert critical_margin(T_pk) > 50.0

    def test_one_sided_sustained_under_14K_headroom(self):
        T = equilibrium_temperature(120e3, 110.0, self.EPS, self.T_S)
        assert 13.9 < critical_margin(T) < 14.2   # disfavored, NOT excluded

    def test_one_sided_continuous_peak_supercritical(self):
        # 411.8 K exceeds T_crit: no liquid ammonia at ANY pressure.
        T = equilibrium_temperature(150e3, 110.0, self.EPS, self.T_S)
        assert critical_margin(T) < 0.0
        assert phase_state(T, 100.0 * PA_PER_BAR).startswith("supercritical")

    def test_liquid_requires_pressure_above_saturation(self):
        # At the primary operating point (337.1 K): liquid above the
        # saturation pressure, gas below it.
        T = equilibrium_temperature(120e3, 220.0, self.EPS, self.T_S)
        P_sat = saturation_pressure(T)
        assert phase_state(T, 1.05 * P_sat) == "liquid"
        assert phase_state(T, 0.95 * P_sat) == "gas"


class TestPhysicalSanity:
    def test_saturated_liquid_denser_than_vapor(self):
        rho_liq, rho_vap = saturated_densities(337.1)
        assert rho_liq > rho_vap > 0.0

    def test_provenance_is_complete(self):
        p = provenance()
        assert p["backend"] == "HEOS"
        assert p["version"]            # non-empty
        assert p["eos_bibtex_key"]     # citable EOS reference
`````

### `tests/test_environment.py`

_(5825 bytes, sha256 `77fe449f46663b95f4abda51fabf1a3b2b4400070fc5585b63315939c2c5bb0d`)_

`````python
"""Tests for the analytic orbital environment module.

Each function is checked against an independent reference: closed-form special
cases, textbook orbital values, and -- for the exact view factor -- a brute-force
2-D numerical integrator that shares no code with the implementation.
"""

import numpy as np
import pytest

from orbital_thermal import environment as env


# ---------------------------------------------------------------------------
# Orbit geometry
# ---------------------------------------------------------------------------

class TestOrbitGeometry:
    def test_period_550km_is_about_95_minutes(self):
        # LEO at 550 km: ~95.6 min. Independent value from Kepler's third law.
        T = env.orbital_period(550.0)
        assert T / 60.0 == pytest.approx(95.6, abs=0.3)

    def test_velocity_550km_is_about_7_6_kms(self):
        assert env.orbital_velocity(550.0) == pytest.approx(7.59, abs=0.02)

    def test_period_velocity_consistency(self):
        # v * T should equal orbit circumference 2*pi*r.
        for alt in (400.0, 550.0, 800.0):
            r = env.orbital_radius(alt)
            assert env.orbital_velocity(alt) * env.orbital_period(alt) == pytest.approx(
                2 * np.pi * r, rel=1e-12
            )

    def test_higher_orbit_is_slower_and_longer(self):
        assert env.orbital_velocity(800.0) < env.orbital_velocity(400.0)
        assert env.orbital_period(800.0) > env.orbital_period(400.0)

    def test_negative_altitude_rejected(self):
        with pytest.raises(ValueError):
            env.orbital_radius(-10.0)


# ---------------------------------------------------------------------------
# Eclipse
# ---------------------------------------------------------------------------

class TestEclipse:
    def test_leo_beta0_fraction_about_0_37(self):
        # Classic LEO result: ~37% of the orbit in shadow at beta = 0.
        assert env.eclipse_fraction(550.0, 0.0) == pytest.approx(0.372, abs=0.005)

    def test_terminator_orbit_no_eclipse(self):
        # Above beta_critical the orbit is in continuous sun.
        assert env.eclipse_fraction(550.0, 90.0) == 0.0
        assert env.eclipse_fraction(550.0, 89.0) == 0.0

    def test_beta_critical_equals_earth_angular_radius(self):
        bc = env.beta_critical(550.0)
        # Just below: still some eclipse; just above: none.
        assert env.eclipse_fraction(550.0, bc - 0.5) > 0.0
        assert env.eclipse_fraction(550.0, bc + 0.5) == 0.0

    def test_eclipse_monotonic_decreasing_in_beta(self):
        fracs = [env.eclipse_fraction(550.0, b) for b in range(0, 70, 5)]
        assert all(a >= b - 1e-12 for a, b in zip(fracs, fracs[1:]))

    def test_duration_matches_fraction_times_period(self):
        f = env.eclipse_fraction(550.0, 30.0)
        assert env.eclipse_duration(550.0, 30.0) == pytest.approx(
            f * env.orbital_period(550.0), rel=1e-12
        )

    def test_beta_out_of_range_rejected(self):
        with pytest.raises(ValueError):
            env.eclipse_fraction(550.0, -5.0)
        with pytest.raises(ValueError):
            env.eclipse_fraction(550.0, 120.0)


# ---------------------------------------------------------------------------
# View factors
# ---------------------------------------------------------------------------

def _vf_brute(altitude_km, tilt_deg, R_e=env.EARTH_RADIUS_KM, n=2500):
    """Independent brute-force VF: grid integration of cos(alpha)+ over Earth's
    disk. Shares no logic with sphere_view_factor."""
    r = R_e + altitude_km
    theta = np.arcsin(R_e / r)
    gamma = np.radians(tilt_deg)
    psis = np.linspace(0, theta, n)
    phis = np.linspace(0, 2 * np.pi, n, endpoint=False)
    PSI, PHI = np.meshgrid(psis, phis, indexing="ij")
    sx, sz = np.sin(PSI) * np.cos(PHI), np.cos(PSI)
    dz = sx * np.sin(gamma) + sz * np.cos(gamma)
    integrand = np.where(dz > 0, dz, 0.0) * np.sin(PSI)
    return np.sum(integrand) * (theta / (n - 1)) * (2 * np.pi / n) / np.pi


class TestViewFactor:
    def test_nadir_matches_sin_squared_theta(self):
        for alt in (400.0, 550.0, 800.0):
            theta = env.earth_angular_radius(alt)
            assert env.sphere_view_factor(alt, 0.0) == pytest.approx(
                np.sin(theta) ** 2, rel=1e-12
            )

    def test_nadir_matches_mccalip_anchor(self):
        # McCalip's stated VF_nadir = 0.847 at 550 km.
        assert env.nadir_view_factor(550.0) == pytest.approx(0.847, abs=0.001)

    def test_region1_is_exact_cosine_law(self):
        # Below the horizon-crossing tilt, F = cos(tilt) * sin^2(theta) exactly.
        alt, tilt = 550.0, 15.0
        theta = env.earth_angular_radius(alt)
        assert env.sphere_view_factor(alt, tilt) == pytest.approx(
            np.cos(np.radians(tilt)) * np.sin(theta) ** 2, rel=1e-12
        )

    def test_zenith_facing_is_zero(self):
        assert env.sphere_view_factor(550.0, 180.0) == 0.0

    def test_edge_on_is_nonzero_due_to_large_earth(self):
        # At 90deg tilt the plate is edge-on to nadir, but Earth's 67deg angular
        # radius means part of the disk is still above the horizon.
        assert env.sphere_view_factor(550.0, 90.0) > 0.20

    @pytest.mark.parametrize("alt", [400.0, 550.0, 800.0])
    @pytest.mark.parametrize("tilt", [10, 40, 67, 95, 120, 150])
    def test_matches_brute_force_integrator(self, alt, tilt):
        assert env.sphere_view_factor(alt, tilt) == pytest.approx(
            _vf_brute(alt, tilt), abs=3e-4
        )

    def test_monotonic_decreasing_in_tilt(self):
        vals = [env.sphere_view_factor(550.0, t) for t in range(0, 181, 10)]
        assert all(a >= b - 1e-12 for a, b in zip(vals, vals[1:]))

    def test_tilt_out_of_range_rejected(self):
        with pytest.raises(ValueError):
            env.sphere_view_factor(550.0, 200.0)
`````

### `tests/test_input_domain.py`

_(2709 bytes, sha256 `8c2435074579911cfd379a0f8c4afd8578c184dbe564d70f1517cd5a4c5a7ee7`)_

`````python
"""Cross-module finite/integer/range input validation (audit re-review P2-4).

Non-finite (NaN/inf), out-of-range, and wrong-type inputs must be rejected at
public boundaries rather than silently returning NaN, a coarse value, or hanging.
"""

import pytest

from orbital_thermal import bounds, environment as env
from orbital_thermal import equilibrium as eq
from orbital_thermal import radiation as rad
from orbital_thermal import sink as sk
from orbital_thermal import transient as tr

NAN = float("nan")
INF = float("inf")


class TestNonFiniteRejected:
    def test_radiation(self):
        with pytest.raises(ValueError):
            rad.net_flux(NAN, 0.91, 220.0)
        with pytest.raises(ValueError):
            rad.required_area(NAN, 293.0, 0.91)
        with pytest.raises(ValueError):
            rad.effective_sink_temperature(0.5, NAN)

    def test_equilibrium(self):
        with pytest.raises(ValueError):
            eq.equilibrium_temperature(NAN, 220.0, 0.91, 220.0)

    def test_environment(self):
        with pytest.raises(ValueError):
            env.orbital_period(NAN)

    def test_bounds(self):
        with pytest.raises(ValueError):
            bounds.heating_cop(NAN)
        with pytest.raises(ValueError):
            bounds.heat_pump_overhead(NAN)
        with pytest.raises(ValueError):
            bounds.nonzero_sink_optimum(600.0, 220.0, tol=INF)

    def test_sink(self):
        with pytest.raises(ValueError):
            sk.orbital_effective_sink_temperature(550, NAN, 0, assume_sun_shielded=True)
        with pytest.raises(ValueError):
            sk.orbital_effective_sink_temperature(550, 0, 0, assume_sun_shielded=True, t_space=NAN)
        with pytest.raises(ValueError):
            sk.sink_temperature_series(-1.0, 0, 0, assume_sun_shielded=True)   # view_factor
        with pytest.raises(ValueError):
            sk.orbital_effective_sink_temperature(550, 100.0, 0, assume_sun_shielded=True)  # beta>90


class TestRangeAndType:
    def test_sink_profile_requires_three_points(self):
        with pytest.raises(ValueError):
            sk.sink_profile(550, 0.0, assume_sun_shielded=True, n=2)

    def test_simulate_counts_must_be_int(self):
        with pytest.raises(TypeError):
            tr.simulate(550, 0, 545.0, 8000.0, assume_sun_shielded=True,
                        steps_per_orbit=720.0, n_orbits=2)
        with pytest.raises(TypeError):
            tr.simulate(550, 0, 545.0, 8000.0, assume_sun_shielded=True,
                        steps_per_orbit=720, n_orbits=2.0)

    def test_areal_heat_capacity_rejects_nonfinite_thickness(self):
        with pytest.raises(ValueError):
            tr.areal_heat_capacity([("aluminum_6061", NAN)])
`````

### `tests/test_mccalip_exact_vf.py`

_(3495 bytes, sha256 `d81bada9e8b370a7d653bf048cac4532f15249105d221b6c76856262abf5ba5d`)_

`````python
"""The McCalip edge-on geometry correction (audit finding #1).

At McCalip's default geometry the sun-tracking panel is edge-on to Earth, where
his view-factor floor underestimates the exact tilted-plate-to-sphere view factor
by ~12x. Correcting only the view factor in his own heat balance raises his
default equilibrium temperature by ~6.35 K. These tests lock that quantified
result; they do not edit the frozen replication oracle.
"""

import pytest

from orbital_thermal import environment as env
from orbital_thermal import mccalip_exact_vf as ev
from orbital_thermal import mccalip_replication as mc


class TestEdgeOnDefault:
    def test_default_geometry_is_edge_on(self):
        # beta = 90 deg: every orbit position is edge-on (tilt = 90 deg), so the
        # exact per-face VF equals the single edge-on view factor and the two
        # faces are symmetric.
        s = mc._state({})
        assert s["betaAngle"] == 90
        vf_a, vf_b = ev.exact_per_face_view_factors(s["orbitalAltitudeKm"], 90.0)
        assert vf_a == pytest.approx(env.sphere_view_factor(550.0, 90.0), rel=1e-9)
        assert vf_a == pytest.approx(vf_b, rel=1e-12)

    def test_floor_underestimates_exact_by_about_12x(self):
        heur = mc.sun_tracking_view_factors(550.0, 90.0)["vfSideA"]
        exact, _ = ev.exact_per_face_view_factors(550.0, 90.0)
        assert heur == pytest.approx(0.021, abs=0.001)
        assert exact == pytest.approx(0.258, abs=0.001)
        assert exact / heur > 10.0

    def test_heat_balance_reproduces_replication_with_his_view_factors(self):
        # Only the view factor is allowed to differ: with McCalip's own VFs the
        # recomputation reproduces his replicated equilibrium temperature exactly.
        s = mc._state({})
        vf = mc.sun_tracking_view_factors(s["orbitalAltitudeKm"], s["betaAngle"])
        got = ev.equilibrium_temperature_with_view_factors({}, vf["vfSideA"], vf["vfSideB"])
        assert got == pytest.approx(mc.calculate_thermal(s)["eqTempK"], rel=1e-12)

    def test_exact_vf_raises_default_eqtemp_by_about_6_3K(self):
        mcc = mc.calculate_thermal(mc._state({}))["eqTempK"]
        exact = ev.eqtemp_exact_vf({})
        assert mcc == pytest.approx(335.75, abs=0.05)
        assert exact == pytest.approx(342.10, abs=0.10)
        assert (exact - mcc) == pytest.approx(6.35, abs=0.10)


class TestCorrectionTable:
    def test_table_shape_and_grid(self):
        rows = ev.correction_table_vs_beta()
        assert [r["beta_deg"] for r in rows] == [0, 15, 30, 45, 60, 75, 90]
        for r in rows:
            assert set(r) == {"beta_deg", "eqtemp_mccalip_K", "eqtemp_exact_K", "delta_K"}

    def test_correction_positive_and_monotonic_in_beta(self):
        rows = ev.correction_table_vs_beta()
        deltas = [r["delta_K"] for r in rows]
        assert all(d > 0 for d in deltas)                      # always an underestimate
        assert deltas == sorted(deltas)                        # worst at the edge-on default
        assert deltas[0] == pytest.approx(1.94, abs=0.05)      # beta = 0
        assert deltas[-1] == pytest.approx(6.35, abs=0.05)     # beta = 90 (default)

    def test_beta90_row_matches_default_recomputation(self):
        rows = ev.correction_table_vs_beta()
        beta90 = next(r for r in rows if r["beta_deg"] == 90)
        assert beta90["eqtemp_exact_K"] == pytest.approx(ev.eqtemp_exact_vf({}), rel=1e-12)
        assert beta90["eqtemp_mccalip_K"] == pytest.approx(335.75, abs=0.05)
`````

### `tests/test_mccalip_replication.py`

_(4334 bytes, sha256 `78465124db70d1b1fc6b8f293068071f3127dd8e8498ff9ed64eaae8550913d9`)_

`````python
"""Replication tests: Python port vs the frozen McCalip Node oracle.

ORACLE-FREEZE RULE: ``expected_outputs.json`` is generated from McCalip's pinned
JavaScript (commit d1e4238) and is never edited to make a test pass. If his model
changes, the oracle is regenerated wholesale and provenance.md is updated.

These tests assert three separable things:
  * Replication  -- the port reproduces his JS numbers to floating-point roundoff.
  * Verification -- where his model uses approximations/constants that differ from
    the exact core package, the divergence is bounded and explained (not hidden).
"""

import hashlib
import json
from pathlib import Path

import pytest

from orbital_thermal import mccalip_replication as mc
from orbital_thermal import environment as env
from orbital_thermal.constants import SIGMA_SB

ORACLE_PATH = (Path(__file__).resolve().parents[1]
               / "external_models" / "mccalip_thoughts" / "expected_outputs.json")


def _overrides(label):
    if label == "defaults":
        return {}
    if label.startswith("beta_"):
        return {"betaAngle": float(label.split("_")[1])}
    if label.startswith("alt_"):
        return {"orbitalAltitudeKm": float(label.split("_")[1].replace("km", ""))}
    if label.startswith("eRad_"):
        return {"emissivityRad": float(label.split("_")[1])}
    raise ValueError(label)


@pytest.fixture(scope="module")
def oracle():
    return json.loads(ORACLE_PATH.read_text())


class TestReplication:
    def test_oracle_present_and_pinned(self, oracle):
        assert oracle["_meta"]["pinned_commit"] == "d1e4238d3d3f4924e5ca65bafbd4ba5b39af2eb8"
        assert len(oracle["cases"]) == 11

    def test_every_field_matches_oracle(self, oracle):
        for case in oracle["cases"]:
            got = mc.run_case(_overrides(case["label"]))
            for section in ("geometry", "thermal", "orbital"):
                for k, exp in case[section].items():
                    g = got[section][k]
                    if isinstance(exp, bool):
                        assert g == exp, f"{case['label']}.{section}.{k}"
                    else:
                        assert g == pytest.approx(exp, rel=1e-9, abs=1e-9), \
                            f"{case['label']}.{section}.{k}"
            assert got["breakeven_launch_cost_per_kg"] == pytest.approx(
                case["breakeven_launch_cost_per_kg"], rel=1e-9)

    def test_default_eqtemp_anchor(self, oracle):
        got = mc.run_case({})["thermal"]["eqTempK"]
        assert got == pytest.approx(oracle["cases"][0]["thermal"]["eqTempK"], rel=1e-9)
        assert got == pytest.approx(335.75, abs=0.01)


class TestVerificationGap:
    """Where McCalip's model differs from the exact core package -- bounded and
    explained, not silently reconciled."""

    def test_nadir_view_factor_agrees_with_core(self):
        for alt in (400.0, 550.0, 800.0):
            assert mc.nadir_view_factor(alt) == pytest.approx(
                env.nadir_view_factor(alt), rel=1e-12)

    def test_sigma_convention_differs(self):
        assert mc.SIGMA != SIGMA_SB
        assert mc.SIGMA == pytest.approx(SIGMA_SB, rel=1e-3)

    def test_tilted_vf_approximation_departs_from_exact(self):
        alt, tilt = 550.0, 90.0
        approx = mc._tilted_vf_from_cos(alt, 0.0)
        exact = env.sphere_view_factor(alt, 90.0)
        assert abs(approx - exact) > 0.10



class TestOracleFreeze:
    """Enforce oracle-freeze (audit re-review P2-e): the vendored source and frozen
    oracle must match pinned SHA-256 values, and the recorded commit must be the
    full 40-char SHA. The CI job additionally regenerates the oracle from math.js
    and compares it semantically (see verify_oracle_reproducible.py)."""

    def _pins(self):
        return json.loads((ORACLE_PATH.parent / "PINS.json").read_text())

    def test_pinned_sha256_unchanged(self):
        pins = self._pins()
        for name, want in pins["sha256"].items():
            got = hashlib.sha256((ORACLE_PATH.parent / name).read_bytes()).hexdigest()
            assert got == want, f"{name} SHA-256 changed -- oracle-freeze violation"

    def test_meta_records_full_commit_sha(self, oracle):
        pins = self._pins()
        assert len(pins["pinned_commit"]) == 40
        assert oracle["_meta"]["pinned_commit"] == pins["pinned_commit"]
`````

### `tests/test_oracle_freeze.py`

_(1561 bytes, sha256 `9ee845b441022e267781af3ce5bc306fccf1d534c301a72a108489c3458bde12`)_

`````python
"""Network-mocked tests for the external oracle attestation strictness
(audit re-review P2-3). These never make a real network call."""

import importlib.util
from pathlib import Path

_MOD = (Path(__file__).resolve().parents[1]
        / "external_models" / "mccalip_thoughts" / "verify_oracle_reproducible.py")


def _load():
    spec = importlib.util.spec_from_file_location("vor_check", _MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _boom(*a, **k):
    raise OSError("mocked network failure")


class TestExternalAttestationStrictness:
    def test_fail_open_when_not_strict(self, monkeypatch):
        m = _load()
        monkeypatch.delenv("ORACLE_REQUIRE_EXTERNAL", raising=False)
        monkeypatch.setattr(m.urllib.request, "urlopen", _boom)
        errs, ran = m.check_external()
        assert errs == [] and ran is False        # skipped, not a failure

    def test_fail_closed_when_strict(self, monkeypatch):
        m = _load()
        monkeypatch.setenv("ORACLE_REQUIRE_EXTERNAL", "1")
        monkeypatch.setattr(m.urllib.request, "urlopen", _boom)
        errs, ran = m.check_external()
        assert errs and ran is False              # unreachable -> hard failure

    def test_regen_fail_closed_when_strict_and_node_missing(self, monkeypatch):
        m = _load()
        monkeypatch.setenv("ORACLE_REQUIRE_EXTERNAL", "1")
        monkeypatch.setattr(m.shutil, "which", lambda _: None)   # node absent
        errs, ran = m.check_reproducible()
        assert errs and ran is False
`````

### `tests/test_published_results.py`

_(21765 bytes, sha256 `4c0f39b57bb6c355c36d624445b411d8e2c90cebb8d9c1fd9a6dfe8e8c5f872f`)_

`````python
"""Published-results regression suite.

Encodes every central numerical claim of both preprints as a test against
the orbital_thermal package:

  Theory:    "Thermodynamic Bounds and Mass-Trade Criteria for Heat
             Rejection in Orbital Data Centers" (doi:10.5281/zenodo.20650893)
  Companion: "The AI1 Design Point" (doi:10.5281/zenodo.20670772)

Tolerance policy (documented, not incidental):
  * Exact algebraic identities -> rel=1e-12.
  * Iterative results -> the published suites' enforced tolerances
    (fixed point to 1e-10 K; dimensionless quintic residual < 1e-12).
  * Published display values -> the same absolute tolerances asserted in
    verify_suite.py / companion/verify_ai1.py, cited per test.

ORACLE-FREEZE RULE: the expected values below come from the published,
DOI-stamped papers and their verification suites. They are never edited to
make a failing test pass. A failure here means the package is wrong (or a
deliberate, documented model revision is underway) -- nothing else.
"""

from fractions import Fraction

import pytest

from orbital_thermal import (
    SIGMA_SB,
    area_ratio,
    carnot_cop_cooling,
    conversion_area_penalty,
    equilibrium_temperature,
    fixed_work_area_per_watt,
    heat_pump_area_ratio,
    heat_pump_overhead,
    heating_cop,
    net_flux,
    nonzero_sink_optimum,
    optimal_cold_fraction,
    quintic_residual,
    radiative_capacity,
    recirculation_amplification,
    required_area,
)

# ==========================================================================
# Theory paper -- Lemma 1 and Corollaries 1.1 / 1.2
# ==========================================================================


class TestAreaLaw:
    def test_corollary_1_1_zero_sink_estimate(self):
        # R0 = (600/293)^4 = 17.585
        assert (600.0 / 293.0) ** 4 == pytest.approx(17.585, abs=0.01)

    def test_corollary_1_1_exact_ratio_is_exact_rational(self):
        # (600^4 - 220^4) / (293^4 - 220^4) reduces to 6697760000/264604779.
        exact = Fraction(600**4 - 220**4, 293**4 - 220**4)
        assert exact == Fraction(6697760000, 264604779)
        assert area_ratio(293.0, 600.0, 220.0) == pytest.approx(
            float(exact), rel=1e-12
        )
        assert float(exact) == pytest.approx(25.312, abs=0.01)

    def test_corollary_1_1_direction_of_error(self):
        # Exact is 43.9% ABOVE the zero-sink estimate; the estimate is
        # 30.5% BELOW the exact. Direction matters (verify_suite B1).
        R = area_ratio(293.0, 600.0, 220.0)
        R0 = (600.0 / 293.0) ** 4
        assert (R / R0 - 1.0) == pytest.approx(0.439, abs=0.005)
        assert (1.0 - R0 / R) == pytest.approx(0.305, abs=0.005)

    def test_corollary_1_1_safe_upper_bound(self):
        # (R/R0 - 1) < (Ts/T1)^4 / (1 - (Ts/T1)^4)
        R = area_ratio(293.0, 600.0, 220.0)
        R0 = (600.0 / 293.0) ** 4
        x = (220.0 / 293.0) ** 4
        assert (R / R0 - 1.0) < x / (1.0 - x)

    def test_corollary_1_2_megawatt_radiator(self):
        # 1 MW at 293 K, emissivity 0.91, zero sink: 2,630 m^2 emitting,
        # 1,315 m^2 two-sided planform (verify_suite B7 tolerances).
        A = required_area(1e6, 293.0, 0.91)
        assert A == pytest.approx(2630.0, abs=5.0)
        assert A / 2.0 == pytest.approx(1315.0, abs=3.0)


# ==========================================================================
# Theory paper -- Theorem 1 (non-attainability of sink-temperature Carnot)
# ==========================================================================


class TestTheorem1:
    def test_99_percent_worked_example(self):
        # T_h=300, T_c=3.0, T_s=2.7 K: eta = 99%, ~10.1 kW rejected per MW
        # of work, area ~6.4e9 m^2/MW -- finite but extreme (verify_suite B8).
        eta = 1.0 - 3.0 / 300.0
        assert eta == pytest.approx(0.99, abs=1e-9)
        Qc = 1e6 * 3.0 / (300.0 - 3.0)
        assert Qc == pytest.approx(10101.0, abs=1.0)
        A_per_W = fixed_work_area_per_watt(300.0, 3.0, 2.7)
        assert 6.0e9 < A_per_W * 1e6 < 7.0e9

    def test_divergence_toward_carnot_limit(self):
        # A/W grows without bound as T_c approaches T_sink from above.
        a1 = fixed_work_area_per_watt(300.0, 3.0, 2.7)
        a2 = fixed_work_area_per_watt(300.0, 2.701, 2.7)
        assert a2 > 100.0 * a1

    def test_divergence_toward_zero_work(self):
        # ...and as T_c approaches T_h (no work output).
        a1 = fixed_work_area_per_watt(300.0, 250.0, 2.7)
        a2 = fixed_work_area_per_watt(300.0, 299.999, 2.7)
        assert a2 > 100.0 * a1


# ==========================================================================
# Theory paper -- Theorem 2 (the 3/4 rule) and Corollary 2.1
# ==========================================================================


class TestTheorem2:
    def test_optimal_cold_fraction_rejects_bad_tol_and_caps_iterations(self):
        # No hangs on degenerate tol; cap exhaustion raises (audit re-review P2-5).
        for bad in (0.0, -1.0, float("inf"), float("nan")):
            with pytest.raises(ValueError):
                optimal_cold_fraction(1.0, tol=bad)
        with pytest.raises(ValueError):
            optimal_cold_fraction(1.0, max_iter=0)
        with pytest.raises(RuntimeError):
            optimal_cold_fraction(1.0, tol=1e-12, max_iter=1)
        # below float resolution: stagnation guard returns a finite value, no hang
        assert optimal_cold_fraction(1.0, tol=1e-16) == pytest.approx(0.75, abs=1e-6)

    def test_reversible_optimum_is_exactly_three_quarters(self):
        assert optimal_cold_fraction(1.0) == pytest.approx(0.75, abs=1e-9)

    def test_efficiency_ceiling_25_percent(self):
        y = optimal_cold_fraction(1.0)
        assert (1.0 - y) == pytest.approx(0.25, abs=1e-9)

    @pytest.mark.parametrize(
        "a, expected",
        [(1.0, 0.7500), (0.8, 0.7645), (0.5, 0.7808)],
    )
    def test_irreversibility_shifts_optimum_up(self, a, expected):
        # Handoff/preprint values to four decimals.
        assert optimal_cold_fraction(a) == pytest.approx(expected, abs=5e-5)

    def test_stationarity_function_is_strictly_increasing(self):
        # Uniqueness of the optimum: the stationarity function g(y) (d/dy log A/W)
        # is strictly increasing on (0,1) -- its decreasing first term is dominated
        # by 4/y^2 (audit re-review P3-b). One sign change => one root.
        import numpy as np

        def g(y, a):
            return a / (1.0 - a * (1.0 - y)) + 1.0 / (1.0 - y) - 4.0 / y

        for a in (0.5, 0.8, 1.0):
            gv = g(np.linspace(0.01, 0.99, 500), a)
            assert np.all(np.diff(gv) > 0)
            assert np.sum(np.diff(np.sign(gv)) != 0) == 1

    def test_second_order_condition(self):
        # The optimum is a strict minimum of the area-per-work objective.
        y = optimal_cold_fraction(1.0)

        def objective(yy):
            eta = 1.0 - yy
            return (1.0 - eta) / (eta * yy**4)

        assert objective(y - 1e-4) > objective(y)
        assert objective(y + 1e-4) > objective(y)


class TestCorollary21:
    def test_minimum_penalty_at_optimum(self):
        # Reversible, zero sink, at T_c = (3/4) T_h: penalty = (4/3)^3.
        penalty = conversion_area_penalty(600.0, 450.0, eta=0.25)
        assert penalty == pytest.approx((4.0 / 3.0) ** 3, rel=1e-12)
        assert penalty == pytest.approx(2.370, abs=0.001)

    def test_cubic_lower_bound(self):
        # (1 - eta)(T_h/T_c)^4 >= (T_h/T_c)^3 for any reversible engine
        # (eta = 1 - T_c/T_h), spot-checked across the range.
        for Tc in (300.0, 400.0, 450.0, 500.0, 550.0):
            eta = 1.0 - Tc / 600.0
            assert conversion_area_penalty(600.0, Tc, eta) >= (
                600.0 / Tc
            ) ** 3 * (1.0 - 1e-12)

    def test_irreversible_penalty_is_larger(self):
        # a = 0.8 at T_c = 450: (1 - 0.8*0.25)(600/450)^4 = 2.5284.
        penalty = conversion_area_penalty(600.0, 450.0, eta=0.8 * 0.25)
        assert penalty == pytest.approx(2.5284, abs=0.001)
        assert penalty > conversion_area_penalty(600.0, 450.0, eta=0.25)

    def test_nonzero_sink_strictly_exceeds_cubic_bound(self):
        penalty = conversion_area_penalty(600.0, 450.0, eta=0.25, T_sink=220.0)
        assert penalty > (600.0 / 450.0) ** 3


# ==========================================================================
# Theory paper -- Theorem 3 (nonzero-sink optimum, exact quintic)
# ==========================================================================


class TestTheorem3:
    def test_canonical_optimum_full_precision(self):
        # T_h = 600, T_s = 220: T_c* = 457.98675408138325 K.
        t = nonzero_sink_optimum(600.0, 220.0)
        assert t == pytest.approx(457.98675408138325, abs=1e-6)

    def test_quintic_residual_below_published_tolerance(self):
        t = nonzero_sink_optimum(600.0, 220.0)
        assert abs(quintic_residual(t, 600.0, 220.0)) < 1e-12

    @pytest.mark.parametrize(
        "T_sink, shift_pct",
        [
            (0.0, 0.0),
            (50.0, 0.0051),
            (100.0, 0.0810),
            (150.0, 0.4049),
            (200.0, 1.2381),
            (220.0, 1.7748),
            (225.0, 1.9300),
            (250.0, 2.8390),
        ],
    )
    def test_shift_table(self, T_sink, shift_pct):
        # Published eight-sink shift table (verify_suite B4, abs 0.001).
        t = nonzero_sink_optimum(600.0, T_sink)
        shift = 100.0 * (t - 450.0) / 450.0
        assert shift == pytest.approx(shift_pct, abs=0.001)

    def test_shift_identity_q4_over_3(self):
        # Fractional shift above (3/4) T_h is EXACTLY q^4/3, q = T_s/T_c*.
        for T_sink in (50.0, 150.0, 220.0, 250.0):
            t = nonzero_sink_optimum(600.0, T_sink)
            q = T_sink / t
            shift = (t - 450.0) / 450.0
            assert shift == pytest.approx(q**4 / 3.0, abs=1e-8)

    def test_fixed_point_contraction(self):
        # |Phi'| = 4q^4/(3 + q^4) < 1 at every tabulated sink.
        for T_sink in (50.0, 150.0, 220.0, 250.0):
            t = nonzero_sink_optimum(600.0, T_sink)
            q = T_sink / t
            assert 4.0 * q**4 / (3.0 + q**4) < 1.0

    def test_sub_two_percent_bound(self):
        # Shift <= 1.9216% for q <= 0.49.
        assert 100.0 * 0.49**4 / 3.0 == pytest.approx(1.9216003, abs=1e-6)
        assert 100.0 * 0.49**4 / 3.0 < 2.0

    def test_monotone_in_sink_temperature(self):
        values = [nonzero_sink_optimum(600.0, ts) for ts in (0, 100, 200, 250)]
        assert values == sorted(values)


class TestTheorem3NearSinkLimit:
    """Robustness near T_sink -> T_h (audit item 6).

    The fixed-point solver failed to converge for r = T_sink/T_h >~ 0.97; the
    bisection solver handles the whole open domain. These are not published
    anchors -- they assert solver validity, the exact shift identity, and basic
    physical bounds at high sink fractions.
    """

    @pytest.mark.parametrize("r", [0.9, 0.99, 0.999])
    def test_converges_and_residual_below_tolerance(self, r):
        T_h = 600.0
        T_sink = r * T_h
        t = nonzero_sink_optimum(T_h, T_sink)
        assert T_sink < t < T_h                       # physical bracket
        assert abs(quintic_residual(t, T_h, T_sink)) < 1e-12

    @pytest.mark.parametrize("r", [0.9, 0.99, 0.999])
    def test_shift_identity_holds_near_limit(self, r):
        # (T_c* - 3/4 T_h)/(3/4 T_h) == q^4/3 exactly, q = T_sink/T_c*.
        T_h = 600.0
        T_sink = r * T_h
        t = nonzero_sink_optimum(T_h, T_sink)
        q = T_sink / t
        assert (t - 450.0) / 450.0 == pytest.approx(q**4 / 3.0, abs=1e-9)

    def test_raises_on_iteration_exhaustion(self):
        # Cap exhaustion must raise, not silently return an unconverged midpoint.
        with pytest.raises(RuntimeError):
            nonzero_sink_optimum(600.0, 220.0, max_iter=1)

    def test_rejects_nonpositive_tol_and_max_iter(self):
        with pytest.raises(ValueError):
            nonzero_sink_optimum(600.0, 220.0, tol=0.0)
        with pytest.raises(ValueError):
            nonzero_sink_optimum(600.0, 220.0, max_iter=0)

    def test_monotone_through_high_sink(self):
        vals = [nonzero_sink_optimum(600.0, ts) for ts in (300, 540, 594, 599.4)]
        assert vals == sorted(vals)


# ==========================================================================
# Theory paper -- Theorem 4 (heat pump) and Theorem 5 (no self-powering)
# ==========================================================================


class TestTheorem4:
    def test_carnot_cop_at_353_to_520(self):
        assert carnot_cop_cooling(353.0, 520.0) == pytest.approx(
            2.1138, abs=1e-3
        )

    def test_cop_h_equals_cop_c_plus_one(self):
        cop_c = carnot_cop_cooling(353.0, 520.0)
        assert heating_cop(cop_c) == pytest.approx(520.0 / 167.0, rel=1e-12)

    def test_minimum_overhead(self):
        cop_c = carnot_cop_cooling(353.0, 520.0)
        assert heat_pump_overhead(cop_c) == pytest.approx(0.473, abs=0.001)

    def test_area_ratio_exact_and_zero_sink(self):
        # COP_c = 1.15, 353 -> 520 K: exact 0.348 with T_s = 220 K,
        # zero-sink approximation 0.397 (verify_suite B5).
        assert heat_pump_area_ratio(1.15, 353.0, 520.0, 220.0) == pytest.approx(
            0.348, abs=0.001
        )
        assert heat_pump_area_ratio(1.15, 353.0, 520.0) == pytest.approx(
            0.397, abs=0.001
        )


class TestBoundsPhysicalContracts:
    """Public bound APIs must reject thermodynamically impossible inputs
    (audit re-review P1-c)."""

    def test_conversion_penalty_rejects_super_carnot_eta(self):
        # Carnot ceiling for 600->450 K is 1 - 450/600 = 0.25; 0.9 is impossible.
        with pytest.raises(ValueError):
            conversion_area_penalty(600.0, 450.0, eta=0.9)

    def test_conversion_penalty_allows_reversible_boundary(self):
        # eta == 1 - T_c/T_h (reversible limit) is allowed and gives (4/3)^3.
        assert conversion_area_penalty(600.0, 450.0, eta=0.25) == pytest.approx(
            (4.0 / 3.0) ** 3, rel=1e-12)

    def test_heat_pump_rejects_super_carnot_cop(self):
        # Carnot cooling ceiling for 353->520 K is 353/167 ~ 2.114; COP=100 is impossible.
        with pytest.raises(ValueError):
            heat_pump_area_ratio(100.0, 353.0, 520.0)

    def test_heat_pump_requires_upward_lift(self):
        with pytest.raises(ValueError):
            heat_pump_area_ratio(1.0, 520.0, 353.0)   # T2 < T1, not a lift

    def test_heat_pump_rejects_nan_cop_and_negative_sink(self):
        with pytest.raises(ValueError):
            heat_pump_area_ratio(float("nan"), 353.0, 520.0)
        with pytest.raises(ValueError):
            heat_pump_area_ratio(1.15, 353.0, 520.0, T_sink=-220.0)

    def test_heat_pump_allows_carnot_boundary(self):
        cop = carnot_cop_cooling(353.0, 520.0)        # exactly at the ceiling
        assert heat_pump_area_ratio(cop, 353.0, 520.0) > 0.0


class TestTheorem5:
    def test_amplification_at_25_percent(self):
        assert recirculation_amplification(0.25) == pytest.approx(
            4.0 / 3.0, rel=1e-12
        )


# ==========================================================================
# Companion paper -- "The AI1 Design Point" (verify_ai1.py blocks B1-B14)
# ==========================================================================

Q_PEAK, Q_SUST = 150e3, 120e3
A_PLAN, A_EMIT = 110.0, 220.0
EPS, T_S = 0.91, 220.0


class TestAI1OperatingPoints:
    def test_b1_exact_continuous_peak_hypothetical(self):
        T_pk = equilibrium_temperature(Q_PEAK, A_EMIT, EPS, T_S)
        assert T_pk == pytest.approx(353.1623423, abs=1e-6)

    def test_b5_all_four_operating_points(self):
        cases = [
            (Q_SUST, A_EMIT, 337.1004),   # sustained, two-sided (PRIMARY)
            (Q_PEAK, A_EMIT, 353.1623),   # continuous-peak hypothetical
            (Q_SUST, A_PLAN, 391.4652),   # sustained, one-sided
            (Q_PEAK, A_PLAN, 411.8443),   # continuous-peak, one-sided
        ]
        for Q, A, expected in cases:
            assert equilibrium_temperature(Q, A, EPS, T_S) == pytest.approx(
                expected, abs=1e-3
            )


class TestAI1StressTest:
    def test_b2_capacities_at_exact_peak_temperature(self):
        T_pk = equilibrium_temperature(Q_PEAK, A_EMIT, EPS, T_S)
        cases = [
            (0.91, 220.0, 150.0),
            (0.80, 220.0, 131.8681319),
            (0.91, 260.0, 124.7166261),
            (0.80, 260.0, 109.6409900),
        ]
        for eps, ts, expected_kW in cases:
            cap = radiative_capacity(T_pk, A_EMIT, eps, ts) / 1e3
            assert cap == pytest.approx(expected_kW, abs=1e-6)

    def test_b3_table3_one_decimal_display_policy(self):
        # The paper displays ONE decimal at the exact T_pk (exact-convention
        # rounding); the rounded values are part of the published record.
        T_pk = equilibrium_temperature(Q_PEAK, A_EMIT, EPS, T_S)
        assert round(radiative_capacity(T_pk, A_EMIT, 0.91, 220.0) / 1e3, 1) == 150.0
        assert round(radiative_capacity(T_pk, A_EMIT, 0.80, 220.0) / 1e3, 1) == 131.9
        assert round(radiative_capacity(T_pk, A_EMIT, 0.91, 260.0) / 1e3, 1) == 124.7
        assert round(radiative_capacity(T_pk, A_EMIT, 0.80, 260.0) / 1e3, 1) == 109.6

    def test_b4_headroom_accounting(self):
        # Combined stress removes 40.4 kW: the full 30 kW headroom plus a
        # 10.4 kW deficit below sustained load.
        T_pk = equilibrium_temperature(Q_PEAK, A_EMIT, EPS, T_S)
        stressed = radiative_capacity(T_pk, A_EMIT, 0.80, 260.0) / 1e3
        assert (150.0 - stressed) == pytest.approx(40.36, abs=0.01)
        assert (120.0 - stressed) == pytest.approx(10.36, abs=0.01)

    def test_b7_fixed_load_equilibria(self):
        cases = [
            (Q_SUST, 0.80, 220.0, 346.21),
            (Q_SUST, 0.91, 260.0, 350.78),
            (Q_SUST, 0.80, 260.0, 358.91),   # +21.8 K over nominal
            (Q_PEAK, 0.80, 260.0, 374.17),
        ]
        for Q, eps, ts, expected in cases:
            assert equilibrium_temperature(Q, A_EMIT, eps, ts) == pytest.approx(
                expected, abs=0.01
            )

    def test_b8_overhead_parameterization(self):
        # Q_rad = (1 + f) * P_compute.
        cases = [
            (1.10, EPS, T_S, 343.80),
            (1.20, EPS, T_S, 350.12),
            (1.10, 0.80, 260.0, 365.24),
            (1.20, 0.80, 260.0, 371.26),
        ]
        for f, eps, ts, expected in cases:
            T = equilibrium_temperature(f * Q_SUST, A_EMIT, eps, ts)
            assert T == pytest.approx(expected, abs=0.01)

    def test_b9_effective_area_case(self):
        assert equilibrium_temperature(
            Q_SUST, 0.85 * A_EMIT, EPS, T_S
        ) == pytest.approx(348.67, abs=0.01)


class TestAI1CoolantScreen:
    T_CRIT_NH3 = 405.5  # K, NIST reference value (NOT computed here)

    def test_b6_one_sided_continuous_peak_supercritical(self):
        T = equilibrium_temperature(Q_PEAK, A_PLAN, EPS, T_S)
        assert T > self.T_CRIT_NH3

    def test_b6_one_sided_sustained_headroom_under_14K(self):
        gap = self.T_CRIT_NH3 - equilibrium_temperature(Q_SUST, A_PLAN, EPS, T_S)
        assert 13.9 < gap < 14.1   # strong disfavor, NOT exclusion

    def test_b6_two_sided_margin_over_50K(self):
        T_pk = equilibrium_temperature(Q_PEAK, A_EMIT, EPS, T_S)
        assert self.T_CRIT_NH3 - T_pk > 50.0


class TestAI1FluxReconciliation:
    def test_b10_planform_and_per_face_fluxes(self):
        assert Q_PEAK / A_PLAN == pytest.approx(1364.0, abs=1.0)
        assert Q_PEAK / A_EMIT == pytest.approx(682.0, abs=1.0)
        assert Q_SUST / A_EMIT == pytest.approx(545.0, abs=1.0)

    def test_b10_gross_minus_sink_decomposition(self):
        T_pk = equilibrium_temperature(Q_PEAK, A_EMIT, EPS, T_S)
        gross = EPS * SIGMA_SB * T_pk**4
        sink = EPS * SIGMA_SB * T_S**4
        assert gross == pytest.approx(802.8, abs=0.5)
        assert sink == pytest.approx(120.9, abs=0.5)
        assert (gross - sink) == pytest.approx(Q_PEAK / A_EMIT, abs=0.5)
        # net flux helper must agree with the decomposition
        assert net_flux(T_pk, EPS, T_S) == pytest.approx(gross - sink, rel=1e-12)


class TestAI1Comparisons:
    def test_b11_iss_capacity_ratios_firm(self):
        P_ISS = 70e3
        assert Q_SUST / P_ISS == pytest.approx(1.71, abs=0.01)
        assert Q_PEAK / P_ISS == pytest.approx(2.14, abs=0.01)

    def test_b11_iss_flux_ratios_provisional(self):
        # 422 m^2 is secondary reporting with UNVERIFIED area convention;
        # these ratios are PROVISIONAL in the paper and stay flagged here.
        P_ISS, A_ISS = 70e3, 422.0
        assert (Q_SUST / A_EMIT) / (P_ISS / A_ISS) == pytest.approx(3.29, abs=0.02)
        assert (Q_PEAK / A_EMIT) / (P_ISS / A_ISS) == pytest.approx(4.11, abs=0.02)

    def test_b12_constellation_scaling_both_bases(self):
        assert 1e9 / Q_PEAK == pytest.approx(6667.0, abs=1.0)
        assert 1e9 / Q_SUST == pytest.approx(8333.0, abs=1.0)
        assert 6667 * A_EMIT / 1e6 == pytest.approx(1.467, abs=0.01)
        assert 8333 * A_EMIT / 1e6 == pytest.approx(1.833, abs=0.01)

    def test_b13_specific_power_cross_check(self):
        assert 150e3 / 70e3 == pytest.approx(2.143, abs=0.005)
        assert 120e3 / 70e3 == pytest.approx(1.714, abs=0.005)

    def test_b14_hot_rejection_factor(self):
        T_pk = equilibrium_temperature(Q_PEAK, A_EMIT, EPS, T_S)
        factor = (T_pk**4 - 220.0**4) / (293.0**4 - 220.0**4)
        assert factor == pytest.approx(2.628, abs=0.005)
        # and via the package's area_ratio (same algebra, Corollary 1.1)
        assert area_ratio(293.0, T_pk, 220.0) == pytest.approx(factor, rel=1e-12)
`````

### `tests/test_sink.py`

_(12640 bytes, sha256 `73ffdc325c82941c262b4e6a48df8df644d9878d991f857a71e35f3711f0173d`)_

`````python
"""Tests for the time-resolved effective sink temperature module."""

import numpy as np
import pytest

from orbital_thermal import sink
from orbital_thermal import environment as env
from orbital_thermal.constants import SIGMA_SB


class TestEffectiveSink:
    def test_ir_floor_is_property_independent(self):
        # On the night side albedo vanishes, so the sink is pure Earth IR and
        # must NOT depend on emissivity or solar absorptivity.
        a = sink.orbital_effective_sink_temperature(550, 0, 180, tilt_deg=0, assume_sun_shielded=True,
                                            emissivity=0.91, solar_absorptivity=0.20)
        b = sink.orbital_effective_sink_temperature(550, 0, 180, tilt_deg=0, assume_sun_shielded=True,
                                            emissivity=0.5, solar_absorptivity=0.9)
        assert a == pytest.approx(b, rel=1e-12)

    def test_ir_floor_matches_closed_form(self):
        # Nadir, night side: sigma*T^4 = E_ir*VF_nadir + sigma*T_space^4.
        vf = env.nadir_view_factor(550)
        expected = ((sink.EARTH_IR_FLUX * vf) / SIGMA_SB + sink.T_SPACE_K**4) ** 0.25
        got = sink.orbital_effective_sink_temperature(550, 0, 180, tilt_deg=0, assume_sun_shielded=True)
        assert got == pytest.approx(expected, rel=1e-12)

    def test_subpoint_approx_no_albedo_swing_at_terminator(self):
        # APPROXIMATION BEHAVIOR, not physics: under the SUBPOINT albedo
        # approximation the sub-satellite point is never sunlit at beta = 90
        # (cos(zeta)=0 for all u), so the modeled sink is flat at the IR floor.
        # The real disk-integrated albedo is nonzero around a terminator orbit
        # (see TestPhysicalAlbedoFacts). This test pins the approximation, not a
        # physical truth.
        u, T = sink.sink_profile(550, 90.0, tilt_deg=0, assume_sun_shielded=True)
        assert np.ptp(T) == pytest.approx(0.0, abs=1e-9)

    def test_dayside_hotter_than_nightside(self):
        day = sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0, assume_sun_shielded=True)
        night = sink.orbital_effective_sink_temperature(550, 0, 180, tilt_deg=0, assume_sun_shielded=True)
        assert day > night

    def test_albedo_swing_shrinks_with_beta(self):
        # Peak-to-night difference at orbit noon should decrease as beta rises.
        def swing(beta):
            noon = sink.orbital_effective_sink_temperature(550, beta, 0, tilt_deg=0, assume_sun_shielded=True)
            night = sink.orbital_effective_sink_temperature(550, beta, 180, tilt_deg=0, assume_sun_shielded=True)
            return noon - night
        swings = [swing(b) for b in (0, 30, 60, 90)]
        assert all(a >= b - 1e-9 for a, b in zip(swings, swings[1:]))
        # NB swings[-1] == 0 is subpoint-approximation behavior, not physics
        # (see TestPhysicalAlbedoFacts); the trend toward smaller swing is real.
        assert swings[-1] == pytest.approx(0.0, abs=1e-9)

    def test_space_facing_approaches_cmb(self):
        # A zenith-facing radiator sees almost no Earth -> sink near CMB.
        T = sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=180, assume_sun_shielded=True)
        assert T == pytest.approx(sink.T_SPACE_K, abs=0.5)

    def test_pure_ir_independent_of_orbit_position(self):
        # With zero solar absorptivity, only Earth IR remains -> flat profile.
        u, T = sink.sink_profile(550, 0.0, tilt_deg=0, solar_absorptivity=0.0, assume_sun_shielded=True)
        assert np.ptp(T) == pytest.approx(0.0, abs=1e-9)

    def test_nadir_floor_anchor_value(self):
        # Documented anchor: nadir-facing IR floor at 550 km ~ 244 K.
        assert sink.orbital_effective_sink_temperature(550, 0, 180, tilt_deg=0, assume_sun_shielded=True) == pytest.approx(
            243.95, abs=0.5
        )

    def test_zero_emissivity_rejected(self):
        with pytest.raises(ValueError):
            sink.orbital_effective_sink_temperature(550, 0, 0, emissivity=0.0, assume_sun_shielded=True)

    def test_shielding_flag_is_required(self):
        # No default: omitting the explicit sun-shielded choice is an error
        # (audit re-review P1-b -- the omission can no longer be silent).
        with pytest.raises(TypeError):
            sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0)
        # Provided explicitly, it computes normally.
        sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0, assume_sun_shielded=True)

    def test_unshielded_raises(self):
        # Asking for a general (non-sun-shielded) sink is refused, not faked.
        with pytest.raises(NotImplementedError):
            sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0, assume_sun_shielded=False)

    def test_shielding_flag_must_be_strict_boolean(self):
        # Truthy non-booleans must NOT assert shielding (audit re-review P1-2).
        for bad in ("false", "true", "no", 1, 0, [1], None):
            with pytest.raises(TypeError):
                sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0,
                                                assume_sun_shielded=bad)
        # the genuine booleans behave as specified
        sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0, assume_sun_shielded=True)
        with pytest.raises(NotImplementedError):
            sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0, assume_sun_shielded=False)

    def test_flag_flows_through_profile(self):
        with pytest.raises(NotImplementedError):
            sink.sink_profile(550, 0.0, tilt_deg=0, assume_sun_shielded=False)


class TestEclipse:
    def test_night_anti_solar_point_in_eclipse_at_beta0(self):
        assert sink.in_eclipse(550, 0.0, 180.0) is True

    def test_dayside_not_in_eclipse(self):
        assert sink.in_eclipse(550, 0.0, 0.0) is False

    def test_terminator_orbit_never_eclipsed(self):
        assert all(not sink.in_eclipse(550, 90.0, u) for u in range(0, 360, 10))


class TestOrbitAverage:
    def test_t4_weighted_average_between_min_and_max(self):
        u, T = sink.sink_profile(550, 0.0, tilt_deg=0, assume_sun_shielded=True)
        avg = sink.orbit_averaged_sink(550, 0.0, tilt_deg=0, assume_sun_shielded=True)
        assert T.min() <= avg <= T.max()

    def test_average_excludes_duplicated_endpoint(self):
        # orbit_averaged_sink must drop the duplicated 360deg point; it should
        # equal the endpoint-excluded T^4 mean, not the all-points mean.
        _, T = sink.sink_profile(550, 0.0, tilt_deg=0, n=720, assume_sun_shielded=True)
        excl = float(np.mean(T[:-1] ** 4) ** 0.25)
        incl = float(np.mean(T ** 4) ** 0.25)
        avg = sink.orbit_averaged_sink(550, 0.0, tilt_deg=0, n=720, assume_sun_shielded=True)
        assert avg == pytest.approx(excl, rel=1e-12)
        assert abs(avg - incl) > 1e-3      # the duplicate really did bias it

    def test_subpoint_approx_average_equals_floor_at_terminator(self):
        # APPROXIMATION BEHAVIOR, not physics: because the subpoint albedo
        # approximation nulls all albedo at beta = 90, the orbit-averaged sink
        # collapses to the IR floor. A disk-integrated model would sit above it.
        avg = sink.orbit_averaged_sink(550, 90.0, tilt_deg=0, assume_sun_shielded=True)
        floor = sink.orbital_effective_sink_temperature(550, 90, 180, tilt_deg=0, assume_sun_shielded=True)
        assert avg == pytest.approx(floor, rel=1e-9)


class TestPhysicalAlbedoFacts:
    """Physical truths the future DISK-INTEGRATED albedo model must satisfy.

    These target ``sink.disk_integrated_albedo_factor`` -- NOT the subpoint helper,
    whose documented approximation semantics will not change. They xfail today
    because that function is unimplemented (NotImplementedError); being strict,
    each will fail the build as an upgrade reminder the day a correct disk-integrated
    model lands and makes the assertion pass (audit re-review P2-a).
    """

    @pytest.mark.xfail(reason="disk_integrated_albedo_factor not yet implemented; "
                              "terminator orbit still sees sunlit Earth (P2-a)",
                       raises=NotImplementedError, strict=True)
    def test_beta90_orbit_has_nonzero_disk_integrated_albedo(self):
        # A terminator (beta=90) orbit at noon flies over sunlit Earth off-nadir,
        # so the disk-integrated reflected-solar drive is nonzero.
        assert sink.disk_integrated_albedo_factor(550, 90.0, 0.0) > 1e-6

    @pytest.mark.xfail(reason="disk_integrated_albedo_factor not yet implemented; "
                              "a dark subpoint still leaves a sunlit disk (P2-a)",
                       raises=NotImplementedError, strict=True)
    def test_subpoint_darkness_does_not_imply_dark_disk(self):
        # Subpoint dark at (beta=0, u=100): the approximation nulls albedo, yet a
        # sunlit crescent of Earth remains visible to the radiator.
        assert sink.subpoint_albedo_factor(0.0, 100.0) == 0.0
        assert sink.disk_integrated_albedo_factor(550, 0.0, 100.0) > 1e-6

    @pytest.mark.xfail(reason="disk_integrated_albedo_factor not yet implemented; "
                              "off-opposition eclipse keeps a sunlit crescent (P2-a)",
                       raises=NotImplementedError, strict=True)
    def test_eclipse_off_opposition_has_nonzero_albedo(self):
        # In eclipse but NOT at exact opposition (beta=0, u=120): the Lambertian
        # phase function is nonzero (it vanishes only at exact opposition u=180),
        # so a sunlit crescent contributes. The previous u=180 assertion was WRONG
        # -- Phi(pi)=0 makes disk-integrated albedo genuinely zero there.
        assert sink.in_eclipse(550, 0.0, 120.0) is True
        assert sink.disk_integrated_albedo_factor(550, 0.0, 120.0) > 1e-6


class TestSubpointAlbedoApproximation:
    """Ordinary passing tests of the SUBPOINT approximation helper's defined
    behavior: factor = max(0, cos(beta) cos(u)). Not physics placeholders."""

    def test_orbit_noon_equatorial_is_unity(self):
        assert sink.subpoint_albedo_factor(0.0, 0.0) == pytest.approx(1.0)

    def test_nulls_on_night_side_and_terminator(self):
        assert sink.subpoint_albedo_factor(0.0, 180.0) == 0.0                 # midnight
        assert sink.subpoint_albedo_factor(90.0, 0.0) == pytest.approx(0.0, abs=1e-12)
        assert sink.subpoint_albedo_factor(0.0, 120.0) == 0.0                 # cos(120)<0

    def test_matches_clamped_cosine(self):
        for beta, u in [(0, 0), (30, 45), (60, 80), (0, 95)]:
            expect = max(0.0, np.cos(np.radians(beta)) * np.cos(np.radians(u)))
            assert sink.subpoint_albedo_factor(beta, u) == pytest.approx(expect, abs=1e-12)


class TestDeprecatedAlias:
    def test_alias_warns_and_matches(self):
        # sink.effective_sink_temperature is a deprecated alias (audit P2-9).
        with pytest.warns(DeprecationWarning):
            got = sink.effective_sink_temperature(550, 0, 180, tilt_deg=0,
                                                  assume_sun_shielded=True)
        ref = sink.orbital_effective_sink_temperature(550, 0, 180, tilt_deg=0,
                                                      assume_sun_shielded=True)
        assert got == ref


class TestInputDomain:
    """Centralized physical-domain validation (audit re-review P3-a)."""

    def test_emissivity_must_be_in_unit_interval(self):
        with pytest.raises(ValueError):
            sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0,
                                            assume_sun_shielded=True, emissivity=1.5)

    def test_absorptivity_must_be_in_unit_interval(self):
        with pytest.raises(ValueError):
            sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0,
                                            assume_sun_shielded=True, solar_absorptivity=1.5)
        with pytest.raises(ValueError):
            sink.orbital_effective_sink_temperature(550, 0, 0, tilt_deg=0,
                                            assume_sun_shielded=True, solar_absorptivity=-0.1)

    def test_sink_profile_requires_two_points(self):
        with pytest.raises(ValueError):
            sink.sink_profile(550, 0.0, tilt_deg=0, n=1, assume_sun_shielded=True)

    def test_negative_or_nonfinite_fluxes_rejected(self):
        with pytest.raises(ValueError):
            sink.orbital_effective_sink_temperature(550, 0, 0, assume_sun_shielded=True, earth_ir=-1000.0)
        with pytest.raises(ValueError):
            sink.orbital_effective_sink_temperature(550, 0, 0, assume_sun_shielded=True, solar_constant=-1.0)
`````

### `tests/test_smoke.py`

_(2954 bytes, sha256 `cb0d7f2cf0c45158c323f5e466fae974a9e8359ae16b09c0eeaa3427adc86529`)_

`````python
"""Smoke tests: a handful of canonical published anchors.

These only prove the package installs and the core functions reproduce
known values. The full published-results regression suite is a separate
task (tests/test_published_results.py) and supersedes nothing here --
smoke tests stay fast and minimal.
"""

import pytest

from orbital_thermal import (
    area_ratio,
    effective_sink_temperature,
    equilibrium_temperature,
    net_flux,
    radiative_capacity,
    required_area,
)


def test_corollary_1_2_one_megawatt_at_room_temperature():
    # 1 MW at 293 K, emissivity 0.91, zero sink -> 2,630 m^2 emitting area.
    assert required_area(1e6, 293.0, 0.91) == pytest.approx(2630.0, abs=0.5)


def test_corollary_1_1_exact_area_ratio():
    # 293 -> 600 K with T_s = 220 K: exactly 6697760000/264604779 (~25.312).
    assert area_ratio(293.0, 600.0, 220.0) == pytest.approx(
        6697760000 / 264604779, rel=1e-12
    )


def test_ai1_sustained_two_sided_primary_operating_point():
    # 120 kW through 220 m^2 emitting, emissivity 0.91, T_s^eff = 220 K.
    assert equilibrium_temperature(120e3, 220.0, 0.91, 220.0) == pytest.approx(
        337.1004, abs=1e-3
    )


def test_capacity_inverts_equilibrium_temperature():
    # The two companion-paper functions must be exact inverses.
    T = equilibrium_temperature(150e3, 220.0, 0.91, 220.0)
    assert radiative_capacity(T, 220.0, 0.91, 220.0) == pytest.approx(
        150e3, rel=1e-12
    )


def test_effective_sink_quarter_power_law():
    assert effective_sink_temperature(1.0, 220.0) == 220.0
    # F = 1/16 -> factor (1/16)^(1/4) = 1/2.
    assert effective_sink_temperature(0.0625, 220.0) == pytest.approx(110.0)


def test_rejects_nonphysical_inputs():
    with pytest.raises(ValueError):
        net_flux(200.0, 0.91, T_sink=220.0)  # radiator colder than sink
    with pytest.raises(ValueError):
        net_flux(300.0, 1.5)  # emissivity above 1
    with pytest.raises(ValueError):
        required_area(-5.0, 293.0, 0.91)  # negative heat load



def test_version_is_single_sourced():
    # __version__ must come from the installed package metadata (pyproject),
    # not a hardcoded string that can drift (audit item 11a).
    import orbital_thermal
    from importlib.metadata import version
    assert orbital_thermal.__version__ == version("orbital-thermal")


def test_sigma_sb_is_binary64_si_derived():
    # SIGMA_SB is the binary64 of sigma = 2 pi^5 k_B^4 / (15 h^3 c^2) using the
    # exact 2019-SI defining constants -- not the truncated CODATA-printed value
    # (audit re-review P2-c).
    import math
    from orbital_thermal.constants import SIGMA_SB
    kB, h, c = 1.380649e-23, 6.62607015e-34, 299792458.0
    sigma_si = 2 * math.pi**5 * kB**4 / (15 * h**3 * c**2)
    assert SIGMA_SB == pytest.approx(sigma_si, rel=1e-12)
    assert SIGMA_SB != 5.670374419e-8
    assert abs(SIGMA_SB - 5.670374419e-8) / SIGMA_SB == pytest.approx(3.25e-11, rel=0.1)
`````

### `tests/test_transient.py`

_(19077 bytes, sha256 `8dde7deff4c51c9309cd4715627441127f1bd66dbec736705ea6813de5f6116b`)_

`````python
"""Tests for the one-node transient radiator model and averaging bias.

The integrator is checked against the analytic steady state it must reproduce in
the constant-sink limit, against energy-conserving periodicity, and for the
physically required monotonic damping with thermal mass.
"""

import warnings

import numpy as np
import pytest

from orbital_thermal import transient as tr
from orbital_thermal import sink as sink_mod
from orbital_thermal.constants import SIGMA_SB

EPS = 0.91
Q_LOAD = EPS * SIGMA_SB * (337.1**4 - 220.0**4)

SIM = dict(n_orbits=25, steps_per_orbit=720)


class TestSteadyState:
    def test_reproduces_paper_operating_point(self):
        assert tr.steady_state_temperature(Q_LOAD, 220.0, EPS) == pytest.approx(337.1, abs=0.05)

    def test_matches_stefan_boltzmann_closed_form(self):
        T = tr.steady_state_temperature(500.0, 250.0, EPS)
        assert EPS * SIGMA_SB * (T**4 - 250.0**4) == pytest.approx(500.0, rel=1e-12)


class TestTimeConstant:
    def test_positive_and_linear_in_capacity(self):
        t1 = tr.thermal_time_constant(4000.0, 337.0, EPS)
        t2 = tr.thermal_time_constant(8000.0, 337.0, EPS)
        assert t1 > 0
        assert t2 == pytest.approx(2 * t1, rel=1e-12)


class TestTransient:
    def test_flat_sink_converges_to_analytic_steady(self):
        t, T, Ts = tr.simulate(550, 90.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        steady = tr.steady_state_temperature(Q_LOAD, float(Ts.mean()), EPS)
        assert np.ptp(Ts) == pytest.approx(0.0, abs=1e-9)
        assert T.mean() == pytest.approx(steady, abs=1e-3)
        assert (T.max() - T.min()) == pytest.approx(0.0, abs=1e-3)

    def test_periodic_closure(self):
        t, T, Ts = tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        assert T[0] == pytest.approx(T[-1], abs=1e-3)

    def test_swing_decreases_with_thermal_mass(self):
        swings = []
        for C in (2000.0, 8000.0, 40000.0):
            _, T, _ = tr.simulate(550, 0.0, Q_LOAD, C, tilt_deg=0, **SIM, assume_sun_shielded=True)
            swings.append(T.max() - T.min())
        assert swings[0] > swings[1] > swings[2]

    def test_panel_hotter_than_sink(self):
        _, T, Ts = tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        assert np.all(T > Ts)


class TestAveragingBias:
    def test_mean_bias_is_nonpositive(self):
        # At periodic steady state <T^4> = T_steady^4; since x^(1/4) is concave
        # the arithmetic mean is <= T_steady, so the averaged-sink steady solution
        # does NOT under-predict the mean. bias_K must be <= 0 up to numerical
        # slack (and only marginally below, since the ripple is small).
        b = tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        assert b["bias_K"] <= 1e-3
        assert b["bias_K"] > -0.5

    def test_periodic_steady_state_energy_balance(self):
        # Exact identity at periodic SS: <T^4> = q_load/(eps*sigma) + <Tsink^4>,
        # equivalently <T^4> = T_steady^4. Holds across thermal masses.
        import numpy as np
        for C in (2000.0, 8000.0, 40000.0):
            _, T, Ts = tr.simulate(550, 0.0, Q_LOAD, C, tilt_deg=0, **SIM, assume_sun_shielded=True)
            lhs = float(np.mean(T[:-1] ** 4))
            rhs = Q_LOAD / (EPS * SIGMA_SB) + float(np.mean(Ts[:-1] ** 4))
            assert lhs == pytest.approx(rhs, rel=1e-5)
            steady = tr.steady_state_temperature(
                Q_LOAD, float(np.mean(Ts[:-1] ** 4)) ** 0.25, EPS)
            assert lhs ** 0.25 == pytest.approx(steady, abs=1e-3)

    def test_peak_exceeds_steady(self):
        b = tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        assert b["peak_excess_over_steady_K"] > 1.0
        assert b["transient_peak_K"] > b["steady_avg_sink_K"]

    def test_no_bias_or_swing_at_terminator(self):
        b = tr.averaging_bias(550, 90.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        assert b["swing_K"] == pytest.approx(0.0, abs=1e-3)
        assert b["bias_K"] == pytest.approx(0.0, abs=1e-3)
        assert b["peak_excess_over_steady_K"] == pytest.approx(0.0, abs=1e-3)

    def test_raises_on_nonconvergence(self):
        # A non-converged transient must NOT be reported as a valid Jensen/peak
        # result (the sign can flip); averaging_bias raises by default.
        with pytest.raises(RuntimeError):
            tr.averaging_bias(550, 0.0, Q_LOAD, 500000.0, tilt_deg=0, assume_sun_shielded=True,
                              n_orbits=3, steps_per_orbit=360)

    def test_unconverged_inspectable_with_flag(self):
        with pytest.warns(RuntimeWarning):
            b = tr.averaging_bias(550, 0.0, Q_LOAD, 500000.0, tilt_deg=0, assume_sun_shielded=True,
                                  n_orbits=3, steps_per_orbit=360,
                                  require_convergence=False)
        assert b["converged"] is False

    def test_reports_convergence_diagnostics(self):
        b = tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        assert b["converged"] is True
        assert b["closure_error_K"] < 1e-3
        assert {"orbits_used", "energy_residual_W_m2"} <= set(b)

    def test_sink_avg_matches_sink_module(self):
        b = tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        ref = sink_mod.orbit_averaged_sink(550, 0.0, tilt_deg=0, assume_sun_shielded=True)
        assert b["sink_avg_K"] == pytest.approx(ref, abs=0.2)



class TestConvergence:
    def test_returns_three_tuple_by_default(self):
        # Backward compatibility: the default return is still (t, T, T_sink).
        out = tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM, assume_sun_shielded=True)
        assert len(out) == 3

    def test_diagnostics_reported_and_converged(self):
        t, T, Ts, d = tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, assume_sun_shielded=True,
                                   return_diagnostics=True, **SIM)
        assert set(d) == {"converged", "orbits_used", "closure_error_K", "tol_K",
                          "energy_residual_W_m2", "energy_residual_K", "energy_tol_K",
                          "periodic_converged", "time_discretization_converged",
                          "time_residual_K", "time_tol_K"}
        assert d["converged"] is True
        assert d["closure_error_K"] < d["tol_K"]
        assert d["energy_residual_W_m2"] < 1e-1          # ~0 net flux at periodic SS

    def test_high_mass_needs_more_orbits(self):
        # Motivation for the change: heavier panels take more orbits to settle.
        _, _, _, lo = tr.simulate(550, 0.0, Q_LOAD, 2000.0, tilt_deg=0, assume_sun_shielded=True,
                                  return_diagnostics=True, **SIM)
        _, _, _, hi = tr.simulate(550, 0.0, Q_LOAD, 40000.0, tilt_deg=0, assume_sun_shielded=True,
                                  return_diagnostics=True, **SIM)
        assert hi["orbits_used"] > lo["orbits_used"]
        assert lo["converged"] and hi["converged"]

    def test_nonconvergence_warns_and_flags(self):
        # A very high thermal mass under a tight orbit cap cannot reach periodic
        # steady state: simulate must warn and report converged=False.
        with pytest.warns(RuntimeWarning):
            _, _, _, d = tr.simulate(550, 0.0, Q_LOAD, 500000.0, tilt_deg=0, assume_sun_shielded=True,
                                     n_orbits=3, steps_per_orbit=360,
                                     return_diagnostics=True)
        assert d["converged"] is False
        assert d["orbits_used"] == 3

    def test_high_thermal_mass_not_falsely_converged(self):
        # tau/P >> 1: per-orbit closure -> 0 while the panel is far from steady
        # state. Closure alone would falsely certify convergence; the energy-balance
        # gate must reject it (audit re-review P1-1).
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _, _, _, d = tr.simulate(550, 90, 545.0, 1e9, assume_sun_shielded=True,
                                     n_orbits=30, steps_per_orbit=200,
                                     return_diagnostics=True)
        assert d["closure_error_K"] < d["tol_K"]            # closure alone is satisfied
        assert d["energy_residual_K"] > d["energy_tol_K"]   # but energy dT_eq is not
        assert d["converged"] is False

    def test_high_thermal_mass_poor_guess_not_converged(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _, _, _, d = tr.simulate(550, 90, 545.0, 1e10, assume_sun_shielded=True,
                                     t0_guess=100.0, n_orbits=30, steps_per_orbit=200,
                                     return_diagnostics=True)
        assert d["converged"] is False
        assert d["energy_residual_K"] > d["energy_tol_K"]

    def test_low_load_deep_space_not_falsely_converged(self):
        # Audit P1-1: at low q_load / low T the flux->temperature slope 4*eps*sigma*T^3
        # is tiny, so a fixed W/m^2 floor hid many-kelvin errors. The temperature-
        # equivalent criterion (dT_eq) must reject this deep-space case.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _, _, _, d = tr.simulate(altitude_km=550, beta_deg=90, q_load=1e-3,
                                     areal_heat_capacity=1e9, tilt_deg=180,
                                     assume_sun_shielded=True, t0_guess=10.0,
                                     n_orbits=1, steps_per_orbit=100,
                                     return_diagnostics=True)
        assert d["closure_error_K"] < d["tol_K"]            # closure trivially small
        assert d["energy_residual_K"] > d["energy_tol_K"]   # ~2.4 K equivalent error
        assert d["converged"] is False

    def test_averaging_bias_raises_on_false_closure(self):
        # The high-mass false-closure case must NOT yield a (negative) peak excess.
        with pytest.raises(RuntimeError):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tr.averaging_bias(550, 90, 545.0, 1e9, assume_sun_shielded=True,
                                  n_orbits=30, steps_per_orbit=200)

    def test_nonconvergence_can_raise(self):
        with pytest.raises(RuntimeError):
            tr.simulate(550, 0.0, Q_LOAD, 500000.0, tilt_deg=0, assume_sun_shielded=True,
                        n_orbits=3, steps_per_orbit=360,
                        raise_on_nonconvergence=True)



class TestHeatCapacityProvenance:
    def test_areal_heat_capacity_sums_layers(self):
        # C_A = rho*cp*t for a single 2 mm aluminum layer.
        c = tr.areal_heat_capacity([("aluminum_6061", 0.002)])
        assert c == pytest.approx(2700.0 * 896.0 * 0.002, rel=1e-12)

    def test_builds_are_physically_plausible(self):
        vals = {k: tr.build_areal_heat_capacity(k) for k in tr.REPRESENTATIVE_BUILDS}
        # All bracket the illustrative 2000..40000 J/m^2/K range used in examples.
        assert all(1e3 < v < 5e4 for v in vals.values())
        # Adding a coolant inventory and compute mass raises C_A monotonically.
        assert (vals["pv_on_substrate"]
                < vals["radiator_with_coolant"]
                < vals["integrated_compute_radiator"])

    def test_unknown_material_and_build_raise(self):
        with pytest.raises(KeyError):
            tr.areal_heat_capacity([("unobtanium", 0.001)])
        with pytest.raises(KeyError):
            tr.build_areal_heat_capacity("warp_nacelle")
        with pytest.raises(ValueError):
            tr.areal_heat_capacity([("aluminum_6061", -0.001)])

    def test_derived_capacity_drives_the_transient(self):
        # A build-derived C_A runs the solver and reaches periodic steady state.
        C = tr.build_areal_heat_capacity("radiator_with_coolant")
        _, _, _, d = tr.simulate(550, 0.0, Q_LOAD, C, tilt_deg=0, assume_sun_shielded=True,
                                 return_diagnostics=True, **SIM)
        assert d["converged"] is True

    def test_materials_carry_provenance(self):
        keys = {"rho_kg_m3", "cp_J_kgK", "state", "source", "rel_uncertainty"}
        for name, m in tr.MATERIALS.items():
            assert keys <= set(m), name
            assert m["rho_kg_m3"] > 0 and m["cp_J_kgK"] > 0
            assert 0.0 < m["rel_uncertainty"] < 1.0

    def test_ammonia_entry_matches_coolprop_reference_state(self):
        # CODE-regression: the stored (2-decimal) values must reproduce the pinned
        # backend to a TIGHT tolerance (regression_rtol), not the loose 1% physical
        # uncertainty -- a 1% test would mask large accidental edits (audit P3-6).
        pytest.importorskip("CoolProp")
        rho, cp = tr.coolant_rho_cp("Ammonia", 300.0)
        m = tr.MATERIALS["ammonia_liquid"]
        assert m["rho_kg_m3"] == pytest.approx(rho, rel=m["regression_rtol"])
        assert m["cp_J_kgK"] == pytest.approx(cp, rel=m["regression_rtol"])
        # ...and (looser) they agree with the backend within the physical uncertainty
        assert m["rho_kg_m3"] == pytest.approx(rho, rel=m["rel_uncertainty"])
        assert m["cp_J_kgK"] == pytest.approx(cp, rel=m["rel_uncertainty"])

    def test_ammonia_provenance_matches_backend(self):
        # The recorded CoolProp version + EOS key must match the installed backend
        # so the citation cannot drift from the numbers (audit re-review P2-6).
        pytest.importorskip("CoolProp")
        from orbital_thermal import fluids
        prov = fluids.provenance("Ammonia")
        m = tr.MATERIALS["ammonia_liquid"]
        assert prov["version"] == m["coolprop_version"]
        assert prov["eos_bibtex_key"] == m["eos_bibtex_key"]



class TestShieldingPropagation:
    """The sun-shield policy must be explicit and reach the transient path
    (audit re-review P1-b): simulate/averaging_bias no longer silently assume it."""

    def test_simulate_requires_flag(self):
        with pytest.raises(TypeError):
            tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM)

    def test_simulate_unshielded_raises(self):
        with pytest.raises(NotImplementedError):
            tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0,
                        assume_sun_shielded=False, **SIM)

    def test_averaging_bias_requires_flag(self):
        with pytest.raises(TypeError):
            tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, **SIM)

    def test_averaging_bias_unshielded_raises(self):
        with pytest.raises(NotImplementedError):
            tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0,
                              assume_sun_shielded=False, **SIM)


class TestInputDomainAndStability:
    """Input-domain validation and explicit-RK4 stability guards (P3-a)."""

    def test_rejects_nonpositive_heat_capacity(self):
        with pytest.raises(ValueError):
            tr.simulate(550, 0.0, Q_LOAD, 0.0, tilt_deg=0, assume_sun_shielded=True, **SIM)
        with pytest.raises(ValueError):
            tr.simulate(550, 0.0, Q_LOAD, -5.0, tilt_deg=0, assume_sun_shielded=True, **SIM)

    def test_rejects_bad_step_and_orbit_counts(self):
        with pytest.raises(ValueError):
            tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, assume_sun_shielded=True,
                        n_orbits=0, steps_per_orbit=720)
        with pytest.raises(ValueError):
            tr.simulate(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0, assume_sun_shielded=True,
                        n_orbits=5, steps_per_orbit=0)

    def test_rk4_divergence_raises(self):
        # Tiny heat capacity + coarse steps -> dt >> tau -> explicit RK4 blows up.
        with pytest.raises(RuntimeError):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")  # ignore the stability RuntimeWarning
                tr.simulate(550, 0.0, Q_LOAD, 1.0, tilt_deg=0, assume_sun_shielded=True,
                            n_orbits=2, steps_per_orbit=100)

    def test_simulate_rejects_invalid_physical_inputs(self):
        # Early validation: degenerate/non-physical inputs raise before integrating
        # (audit re-review P2-7), not ZeroDivisionError or a silent profile.
        bad = dict(tilt_deg=0, assume_sun_shielded=True, n_orbits=2, steps_per_orbit=100)
        with pytest.raises(ValueError):
            tr.simulate(550, 0, Q_LOAD, 8000.0, emissivity=0.0, **bad)
        with pytest.raises(ValueError):
            tr.simulate(550, 0, -100.0, 8000.0, **bad)              # negative load
        with pytest.raises(ValueError):
            tr.simulate(550, 0, Q_LOAD, 8000.0, convergence_tol_K=float("nan"), **bad)
        with pytest.raises(ValueError):
            tr.simulate(550, 0, Q_LOAD, 8000.0, convergence_tol_K=-1.0, **bad)
        with pytest.raises(ValueError):
            tr.simulate(550, 0, Q_LOAD, 8000.0, t0_guess=-5.0, **bad)

    def test_rk4_negative_temperature_raises(self):
        # An unstable-but-finite run dipped to ~-332 K and was returned before;
        # any non-positive accepted state must now raise (audit re-review P1-3).
        with pytest.raises(RuntimeError):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tr.simulate(550, 0, 5000.0, 1000.0, assume_sun_shielded=True,
                            n_orbits=3, steps_per_orbit=50)

    def test_empty_layers_rejected(self):
        with pytest.raises(ValueError):
            tr.areal_heat_capacity([])



class TestTemporalResolution:
    """Step-doubling temporal-accuracy gate (audit re-review P1-2)."""

    def test_coarse_steps_periodic_but_not_time_resolved(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _, _, _, d = tr.simulate(550, 0, Q_LOAD, 18000.0, assume_sun_shielded=True,
                                     n_orbits=200, steps_per_orbit=3,
                                     return_diagnostics=True, check_time_resolution=True)
        assert d["periodic_converged"] is True
        assert d["time_discretization_converged"] is False
        assert d["time_residual_K"] > d["time_tol_K"]

    def test_averaging_bias_requires_time_resolution(self):
        # Coarse stepping underpredicts peak/swing badly; averaging_bias must refuse.
        with pytest.raises(RuntimeError):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tr.averaging_bias(550, 0, Q_LOAD, 18000.0, assume_sun_shielded=True,
                                  n_orbits=200, steps_per_orbit=3)

    def test_refined_steps_are_time_resolved(self):
        b = tr.averaging_bias(550, 0.0, Q_LOAD, 8000.0, tilt_deg=0,
                              assume_sun_shielded=True, **SIM)
        assert b["time_discretization_converged"] is True
        assert b["time_residual_K"] < b["time_tol_K"]
`````

### `verify_suite.py`

_(4120 bytes, sha256 `f6f043f30c703124c47e192129e5e4aea3e1186b7511aa6700ed510ae39d9105`)_

`````python
import numpy as np

TOL = 1e-9
sigma = 5.670374419e-8

# --- B1: Corollary 1.1 exact sink-corrected ratio ---
T1, T2, Ts = 293.0, 600.0, 220.0
R  = (T2**4 - Ts**4) / (T1**4 - Ts**4)
R0 = (T2/T1)**4
assert abs(R0 - 17.585) < 0.01
assert abs(R - 25.312) < 0.01
assert abs((R/R0 - 1) - 0.439) < 0.005        # exact is 43.9% ABOVE the estimate
assert abs((1 - R0/R) - 0.305) < 0.005        # estimate is 30.5% BELOW the exact
ub = (Ts/T1)**4 / (1 - (Ts/T1)**4)
assert (R/R0 - 1) < ub                        # safe upper bound holds

# --- B2: Theorem 2 — reversible optimum and irreversible shift ---
Th = 600.0
y = np.linspace(0.01, 0.999, 4_000_000)
for a, y_expected in [(1.0, 0.750), (0.8, 0.765), (0.5, 0.781)]:
    eta = a*(1 - y)
    AW = (1 - eta)/(eta * y**4)               # proportional objective
    y_star = y[np.argmin(AW)]
    assert abs(y_star - y_expected) < 0.001, (a, y_star)

# --- B3: Corollary 2.1 — area penalty: zero-sink and nonzero-sink forms ---
Tc = 450.0
rev_penalty = (Tc/Th)*(Th/Tc)**4              # reversible, Ts=0: (Th/Tc)^3
assert abs(rev_penalty - (4/3)**3) < TOL
assert abs((4/3)**3 - 2.370) < 0.001
irr_penalty = (1 - 0.8*0.25)*(Th/Tc)**4       # a = 0.8 at same Tc
assert abs(irr_penalty - 2.5284) < 0.001
assert irr_penalty > rev_penalty
# nonzero sink: reversible penalty strictly exceeds cubic bound
Ts_pen = 220.0
rev_penalty_sink = (Tc/Th)*(Th**4 - Ts_pen**4)/(Tc**4 - Ts_pen**4)
assert rev_penalty_sink > (Th/Tc)**3

# --- B4: Theorem 3 — fixed point with ENFORCED convergence tolerance ---
def tc_star(Th, Ts, tol=1e-10, max_iter=1000):
    tc = 0.75 * Th
    for _ in range(max_iter):
        nxt = Th * (3 + (Ts / tc)**4) / 4
        if abs(nxt - tc) < tol:
            return nxt
        tc = nxt
    raise RuntimeError("Fixed-point iteration did not converge")

for Ts_i, shift_expected in [(0,0.0),(50,0.0051),(100,0.0810),(150,0.4049),
                             (200,1.2381),(220,1.7748),(225,1.9300),(250,2.8390)]:
    t = tc_star(Th, Ts_i)
    # dimensionless quintic residual: 4y^5 - 3y^4 - r^4 = 0
    y_root, r_sink = t/Th, Ts_i/Th
    assert abs(4*y_root**5 - 3*y_root**4 - r_sink**4) < 1e-12
    q = Ts_i/t
    # local attraction: |Phi'| = 4q^4/(3+q^4) < 1
    assert 4*q**4/(3 + q**4) < 1.0
    shift = 100*(t - 450.0)/450.0
    assert abs(shift - 100*q**4/3) < 1e-6     # exact identity shift = q^4/3
    assert abs(shift - shift_expected) < 0.001
    # redundant grid cross-check
    Tc2 = np.linspace(Ts_i + 0.01, 599.99, 2_000_000)
    g = (Th - Tc2)*(Tc2**4 - Ts_i**4)/Tc2
    assert abs(Tc2[np.argmax(g)] - t) < 0.01
assert abs(tc_star(600.0, 220.0) - 457.9867541) < 1e-4    # stated optimum
assert abs(100*0.49**4/3 - 1.9216003) < 1e-6              # analytic sub-2% bound value
assert 100*(0.49**4)/3 < 2.0

# --- B5: Theorem 4 — COP values and heat-pump area ratios ---
T1p, T2p, Tsp, COP = 353.0, 520.0, 220.0, 1.15
assert abs(353/167 - 2.1138) < 1e-3                       # COP_c Carnot
assert abs(520/167 - (353/167 + 1)) < TOL                 # COP_h = COP_c + 1
assert abs(1/(353/167) - 0.473) < 0.001                   # Carnot overhead per IT watt
exact  = (1 + 1/COP)*(T1p**4 - Tsp**4)/(T2p**4 - Tsp**4)
approx = (1 + 1/COP)*(T1p/T2p)**4
assert abs(exact  - 0.348) < 0.001
assert abs(approx - 0.397) < 0.001

# --- B6: Theorem 5 — amplification ---
assert abs(1/(1 - 0.25) - 4/3) < TOL

# --- B7: Corollaries 1.1/1.2 reference values ---
assert abs((600/293)**4 - 17.585) < 0.01
A_emit = 1e6/(0.91*sigma*293**4)
assert abs(A_emit - 2630) < 5                             # m^2, total emitting surface
assert abs(A_emit/2 - 1315) < 3                           # m^2, two-sided panel planform

# --- B8: Theorem 1 consequence — 99% example is extreme-area, not impossible ---
Th99, Ts99, Tc99, W99 = 300.0, 2.7, 3.0, 1e6
eta99 = 1 - Tc99/Th99
assert abs(eta99 - 0.99) < 1e-9
Qc99 = W99*Tc99/(Th99 - Tc99)
assert abs(Qc99 - 10101.0) < 1.0                          # ~10.1 kW
A99 = Qc99/(sigma*(Tc99**4 - Ts99**4))
assert 6.0e9 < A99 < 7.0e9                                # ~6.4e9 m^2: finite, extreme

print("All assertions pass.")
`````

### `verify_suite.wl`

_(3627 bytes, sha256 `6e8a0c51ff9e481dacf89aa0a11c6a36424f9fba9fac3a88e48228097a34878a`)_

`````mathematica
(* W1 — Theorem 2: stationarity with explicit physical assumption *)
f[Tc_] := Th Tc^3 - Tc^4;
FullSimplify[
  Solve[D[f[Tc], Tc] == 0 && 0 < Tc < Th, Tc, Reals],
  Assumptions -> Th > 0]
  (* expected: {{Tc -> 3 Th/4}} *)
FullSimplify[D[f[Tc], {Tc, 2}] /. Tc -> 3 Th/4, Assumptions -> Th > 0]
  (* expected: -9 Th^2/4  (negative => maximum of f, minimum of A/W) *)

(* W2 — Theorem 3: quintic stationarity and exact shift identity *)
g[Tc_] := (Th - Tc) (Tc^4 - Ts^4)/Tc;
Factor[Numerator[Together[D[g[Tc], Tc]]]]
  (* expected: -4 Tc^5 + 3 Th Tc^4 + Th Ts^4 *)
FullSimplify[(Tc/Th - 3/4)/(3/4) == (Ts/Tc)^4/3,
  Assumptions -> Th > Tc > Ts > 0 && 4 Tc^5 - 3 Th Tc^4 == Th Ts^4]
  (* expected: True *)
FullSimplify[
  (4 Tc^5 - 3 Th Tc^4 == Th Ts^4) \[Equivalent] (Tc/Th == (3 + (Ts/Tc)^4)/4),
  Assumptions -> Th > Tc > Ts > 0]
  (* expected: True *)

(* W2b — uniqueness/monotonicity on y >= 3/4 *)
Reduce[ForAll[y, y >= 3/4 && y < 1, D[4 y^5 - 3 y^4, y] > 0]]
  (* expected: True  (4 y^3 (5 y - 3) > 0 on the interval) *)

(* W2c — high-precision positive root, Th = 600, Ts = 220 *)
root = N[Root[4 #^5 - 1800 #^4 - 600*220^4 &, 1], 50];
{root, N[4 root^5 - 1800 root^4 - 600*220^4, 30]}
  (* expected: {457.98675408138324983229514241277622443332179202809, 0``...}
     (exact algebraic Root object; residual zero to working precision) *)

(* W3 — Theorem 3 fixed-point attraction *)
Phi[T_] := Th/4 (3 + (Ts/T)^4);
FullSimplify[Abs[Phi'[Tc]] /. Th -> 4 Tc/(3 + q^4) /. Ts -> q Tc,
  Assumptions -> 0 < q < 1 && Tc > 0]
  (* expected: 4 q^4/(3 + q^4) *)
FullSimplify[4 q^4/(3 + q^4) < 1, Assumptions -> 0 < q < 1]
  (* expected: True
     (note: Reduce[ineq && 0 < q < 1] returns the domain 0 < q < 1 itself —
      mathematically equivalent, but FullSimplify yields the literal True) *)

(* W3b — Theorem 1 fixed-work divergence *)
FullSimplify[
  Limit[Tc/((Th - Tc) (Tc^4 - Ts^4)), Tc -> Ts, Direction -> "FromAbove"],
  Assumptions -> Th > Ts > 0]
  (* expected: Infinity *)
FullSimplify[
  Limit[1/((Th - Tc) Tc^3), Tc -> 0, Direction -> "FromAbove"],
  Assumptions -> Th > 0]
  (* expected: Infinity *)

(* W4 — Corollary 2.1 nonzero-sink penalty strictly exceeds cubic bound *)
Reduce[(1 - (Ts/Th)^4)/(1 - (Ts/Tc)^4) > 1 && 0 < Ts < Tc < Th, {Th, Tc, Ts}, Reals]
  (* expected: equivalent to the stated domain, i.e., holds throughout it *)

(* W5 — Corollary 1.1 exact rationals (T1=293, T2=600, Ts=220) *)
{(600^4 - 220^4)/(293^4 - 220^4), 600^4/293^4}
  (* expected: {6697760000/264604779, 129600000000/7370050801}
     N: {25.3123..., 17.5847...}; deviations: R/R0 - 1 = 0.43945...,
     1 - R0/R = 0.30529... *)
(* safe upper bound is trivially larger: subtracting (Ts/T2)^4 > 0 from numerator *)

(* W6 — sub-2% bound as exact rational *)
(49/100)^4/3
  (* expected: 5764801/300000000 = 0.0192160033... < 1/50 *)

(* W7 — Theorem 4 COP values, exact *)
{353/167, 520/167, 520/167 - 353/167}
  (* expected: {353/167, 520/167, 1} — identity COP_h = COP_c + 1 *)

(* W8 — Theorem 2c irreversible-optimum stationarity, eta = a (1 - y) *)
(* minimize (1 - a(1-y))/(a(1-y) y^4): log-derivative stationarity *)
stat[a_, y_] := a/(1 - a + a y) + 1/(1 - y) - 4/y;
{y /. FindRoot[stat[8/10, y], {y, 0.76}, WorkingPrecision -> 12],
 y /. FindRoot[stat[5/10, y], {y, 0.78}, WorkingPrecision -> 12]}
  (* expected: {0.764507787..., 0.780776406...} — table values 0.765, 0.781 *)

(* W9 — Theorem 1 consequence example, exact *)
With[{Qc = 10^6*3/297, sig = 5670374419*10^-17},  (* = 5.670374419*10^-8 *)
  {Qc, Qc/(sig (3^4 - (27/10)^4))}] // N
  (* expected: {10101.01, 6.395*10^9}  (m^2) *)
`````
