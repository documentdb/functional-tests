"""Unit tests for the deselected-tests sidecar written at collection time."""

import json
from types import SimpleNamespace

import pytest

from documentdb_tests.conftest import _write_deselected_sidecar


def _config(report_path, json_report=True):
    """Minimal stand-in for pytest config; only the json-report options are read."""
    return SimpleNamespace(
        option=SimpleNamespace(json_report=json_report, json_report_file=report_path)
    )


@pytest.mark.unit
class TestWriteDeselectedSidecar:
    def test_writes_reasons_next_to_report(self, tmp_path):
        report = tmp_path / "report.json"
        reasons = {"tests/x/test_a.py::t": {"replica_set": True}}
        _write_deselected_sidecar(_config(str(report)), reasons)
        sidecar = tmp_path / "report.json.deselected.json"
        assert json.loads(sidecar.read_text()) == reasons

    def test_empty_reasons_overwrite_stale_sidecar(self, tmp_path):
        report = tmp_path / "report.json"
        sidecar = tmp_path / "report.json.deselected.json"
        sidecar.write_text(json.dumps({"tests/x/test_a.py::t": {"replica_set": True}}))
        _write_deselected_sidecar(_config(str(report)), {})
        assert json.loads(sidecar.read_text()) == {}

    def test_noop_without_json_report(self, tmp_path):
        _write_deselected_sidecar(_config(None), {"n": {"cap": True}})
        assert list(tmp_path.iterdir()) == []

    def test_noop_when_plugin_inactive(self, tmp_path):
        # json_report_file has a default even when --json-report isn't passed.
        report = tmp_path / "report.json"
        _write_deselected_sidecar(_config(str(report), json_report=False), {"n": {"cap": True}})
        assert list(tmp_path.iterdir()) == []

    def test_creates_missing_report_directory(self, tmp_path):
        # Collection runs before pytest-json-report creates the directory.
        report = tmp_path / "not-yet" / "report.json"
        _write_deselected_sidecar(_config(str(report)), {})
        assert (tmp_path / "not-yet" / "report.json.deselected.json").exists()

    def test_leaves_no_temp_files_behind(self, tmp_path):
        report = tmp_path / "report.json"
        _write_deselected_sidecar(_config(str(report)), {"n": {"cap": True}})
        leftovers = [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")]
        assert leftovers == []
