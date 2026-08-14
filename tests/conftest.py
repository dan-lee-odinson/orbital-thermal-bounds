"""Shared test helpers.

``_child_env`` lives here rather than in one test module because D107 found a second
subprocess call that did not use it. One definition, one import, one thing to keep
right -- a second spelling of a correct answer is a second thing to drift.
"""

from __future__ import annotations

import os
import sys


def _child_env() -> dict[str, str]:
    """Environment for a test subprocess, carrying this interpreter's import path.

    A subprocess does not inherit pytest's ``pythonpath`` setting, so from a bare tree
    with nothing installed the child would fail to import ``orbital_thermal`` even
    though the parent test session imports it fine. Passing ``sys.path`` through
    ``PYTHONPATH`` makes the child resolve the package the same way the parent did.

    Prepended rather than replacing any inherited ``PYTHONPATH``, so a caller's own
    setting still applies but cannot shadow the package under test.

    D107: a child launched without this imports ``orbital_thermal`` only from an
    ambient install, which is the dependency ``pyproject.toml``'s ``pythonpath`` comment
    exists to forbid -- *"a suite whose result depends on ambient install state can lie
    about itself."* It lied quietly: the check that needed it passed on a machine with
    an editable install and failed on a bare checkout, so a hand-back carried a suite
    total that did not reproduce.
    """
    inherited = os.environ.get("PYTHONPATH", "")
    entries = [p for p in sys.path if p]
    if inherited:
        entries.append(inherited)
    return {**os.environ, "PYTHONPATH": os.pathsep.join(entries)}
