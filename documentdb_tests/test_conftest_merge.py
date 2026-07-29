"""Unit tests for merging Phase 2 (no_parallel) JSON reports into Phase 1."""

import json

import pytest

from documentdb_tests.conftest import _merge_json_reports


def _merge(tmp_path, p1_summary, p2_summary):
    """Write two minimal reports, merge, and return the merged summary."""
    p1 = tmp_path / "p1.json"
    p2 = tmp_path / "p2.json"
    p1.write_text(json.dumps({"summary": p1_summary, "tests": [], "duration": 1.0}))
    p2.write_text(json.dumps({"summary": p2_summary, "tests": [], "duration": 1.0}))
    _merge_json_reports(str(p1), str(p2))
    return json.loads(p1.read_text())["summary"]


@pytest.mark.unit
class TestMergeJsonReports:
    def test_outcome_buckets_are_summed(self, tmp_path):
        merged = _merge(
            tmp_path,
            {"collected": 10, "total": 8, "passed": 7, "failed": 1},
            {"collected": 10, "total": 2, "passed": 1, "failed": 1},
        )
        assert merged["passed"] == 8 and merged["failed"] == 2 and merged["total"] == 10

    def test_xfailed_and_xpassed_are_summed(self, tmp_path):
        merged = _merge(
            tmp_path,
            {"collected": 10, "total": 8, "passed": 7, "xfailed": 1},
            {"collected": 10, "total": 2, "passed": 1, "xfailed": 1},
        )
        assert merged["xfailed"] == 2

    def test_collected_taken_from_phase2(self, tmp_path):
        # Phase 2 runs without xdist, so its collected count is the true
        # pre-deselection total.
        merged = _merge(
            tmp_path,
            {"collected": 8, "total": 8, "passed": 8},
            {"collected": 10, "total": 2, "passed": 2},
        )
        assert merged["collected"] == 10

    def test_merged_summary_reconciles_with_no_deselection(self, tmp_path):
        # collected == total after merging, so no_parallel tests are not
        # misreported as unsupported.
        merged = _merge(
            tmp_path,
            {"collected": 8, "total": 8, "passed": 8},
            {"collected": 10, "total": 2, "passed": 2},
        )
        assert merged["collected"] == merged["total"] == 10
