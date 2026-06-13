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
