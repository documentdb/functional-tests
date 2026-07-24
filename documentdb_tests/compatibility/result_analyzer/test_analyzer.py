"""Tests for failure extraction and categorization in the analyzer."""

import pytest

from documentdb_tests.compatibility.result_analyzer.analyzer import (
    TestOutcome,
    build_reconciliation,
    categorize_outcome,
    extract_exception_type,
    extract_failure_tag,
    extract_skip_reason,
    feature_path,
    group_by_feature,
    is_infrastructure_error,
)


def _make_test_result(crash_message: str) -> dict:
    """Helper to build a minimal test result dict with a crash message."""
    return {"call": {"crash": {"message": crash_message}}}


def _make_setup_error_result(crash_message: str, longrepr: str = "") -> dict:
    """An errored test: failure lives in the setup phase, with no call phase."""
    return {
        "setup": {
            "outcome": "failed",
            "crash": {"message": crash_message},
            "longrepr": longrepr,
        },
        "teardown": {"outcome": "passed"},
    }


# --- extract_failure_tag ---


@pytest.mark.unit
class TestExtractFailureTag:
    def test_result_mismatch(self):
        result = _make_test_result("[RESULT_MISMATCH] Expected [1,2,3] but got [1,2]")
        assert extract_failure_tag(result) == "RESULT_MISMATCH"

    def test_unexpected_error(self):
        result = _make_test_result("[UNEXPECTED_ERROR] Expected success but got exception")
        assert extract_failure_tag(result) == "UNEXPECTED_ERROR"

    def test_error_mismatch(self):
        result = _make_test_result("[ERROR_MISMATCH] Expected code 11000 but got 26")
        assert extract_failure_tag(result) == "ERROR_MISMATCH"

    def test_unexpected_success(self):
        result = _make_test_result("[UNEXPECTED_SUCCESS] Expected error but got result")
        assert extract_failure_tag(result) == "UNEXPECTED_SUCCESS"

    def test_test_exception(self):
        result = _make_test_result("[TEST_EXCEPTION] Bad test setup")
        assert extract_failure_tag(result) == "TEST_EXCEPTION"

    def test_no_tag(self):
        result = _make_test_result("AssertionError: values differ")
        assert extract_failure_tag(result) == ""

    def test_empty_message(self):
        result = _make_test_result("")
        assert extract_failure_tag(result) == ""

    def test_missing_call(self):
        assert extract_failure_tag({}) == ""

    def test_reads_setup_phase_when_no_call(self):
        # Errored tests have no call phase; the tag must come from setup.
        result = _make_setup_error_result("[TEST_EXCEPTION] fixture blew up")
        assert extract_failure_tag(result) == "TEST_EXCEPTION"

    def test_reads_strict_xpass_from_failing_phase(self):
        result = {"call": {"outcome": "failed", "longrepr": "[XPASS(strict)] stale marker"}}
        assert extract_failure_tag(result) == "XPASS_STRICT"


# extract_skip_reason.


@pytest.mark.unit
class TestExtractSkipReason:
    def test_reads_reason_from_setup_longrepr(self):
        result = {
            "setup": {
                "outcome": "skipped",
                "longrepr": "('/path/test_x.py', 17, 'Skipped: Requires auditing to be enabled')",
            }
        }
        assert extract_skip_reason(result) == "Requires auditing to be enabled"

    def test_no_setup_is_empty(self):
        assert extract_skip_reason({}) == ""

    def test_non_string_longrepr_is_empty(self):
        assert extract_skip_reason({"setup": {"longrepr": None}}) == ""

    def test_longrepr_without_skip_marker_is_empty(self):
        assert extract_skip_reason({"setup": {"longrepr": "some other text"}}) == ""


# --- extract_exception_type ---


@pytest.mark.unit
class TestExtractExceptionType:
    def test_simple_exception(self):
        assert extract_exception_type("ConnectionError: refused") == "ConnectionError"

    def test_dotted_exception(self):
        assert (
            extract_exception_type("pymongo.errors.OperationFailure: code 11000")
            == "pymongo.errors.OperationFailure"
        )

    def test_no_colon(self):
        assert extract_exception_type("just a message") == ""

    def test_empty(self):
        assert extract_exception_type("") == ""


# --- is_infrastructure_error ---


@pytest.mark.unit
class TestIsInfrastructureError:
    def test_connection_error(self):
        result = _make_test_result("ConnectionError: Cannot connect")
        assert is_infrastructure_error(result) is True

    def test_timeout_error(self):
        result = _make_test_result("TimeoutError: timed out")
        assert is_infrastructure_error(result) is True

    def test_pymongo_connection_failure(self):
        result = _make_test_result("pymongo.errors.ConnectionFailure: connection lost")
        assert is_infrastructure_error(result) is True

    def test_pymongo_server_selection(self):
        result = _make_test_result("pymongo.errors.ServerSelectionTimeoutError: no servers")
        assert is_infrastructure_error(result) is True

    def test_assertion_error_not_infra(self):
        result = _make_test_result("AssertionError: [RESULT_MISMATCH] wrong value")
        assert is_infrastructure_error(result) is False

    def test_operation_failure_not_infra(self):
        result = _make_test_result("pymongo.errors.OperationFailure: code 11000")
        assert is_infrastructure_error(result) is False

    def test_empty_message(self):
        result = _make_test_result("")
        assert is_infrastructure_error(result) is False

    def test_missing_call(self):
        assert is_infrastructure_error({}) is False

    def test_reads_setup_phase_when_no_call(self):
        # An infra crash during setup must still be detected without a call phase.
        result = _make_setup_error_result("pymongo.errors.ConnectionFailure: connection lost")
        assert is_infrastructure_error(result) is True


# build_reconciliation.


@pytest.mark.unit
class TestBuildReconciliation:
    def test_pass_rate_excludes_skipped_and_xfailed(self):
        # Denominator is passed + failed + error; skipped/xfailed don't move it.
        summary = {
            "collected": 20,
            "total": 20,
            "passed": 8,
            "failed": 2,
            "error": 0,
            "skipped": 5,
            "xfailed": 5,
        }
        result = build_reconciliation(summary)
        # 8 / (8 + 2 + 0) = 80%, not 8/20
        assert result["pass_rate"] == 80.0

    def test_error_counts_against_pass_rate(self):
        # A run with any error cannot read 100%.
        summary = {"total": 10, "passed": 9, "failed": 0, "error": 1}
        result = build_reconciliation(summary)
        assert result["pass_rate"] == 90.0

    def test_all_passed_is_100(self):
        summary = {"total": 5, "passed": 5, "failed": 0, "error": 0}
        assert build_reconciliation(summary)["pass_rate"] == 100.0

    def test_no_verdicts_is_zero_not_division_error(self):
        # Everything deselected/skipped: denominator is 0, must not raise.
        summary = {"collected": 12, "deselected": 4, "total": 8, "skipped": 8}
        result = build_reconciliation(summary)
        assert result["pass_rate"] == 0.0

    def test_counts_are_surfaced_from_native_summary(self):
        summary = {
            "collected": 30,
            "deselected": 5,
            "total": 25,
            "passed": 20,
            "failed": 3,
            "error": 2,
            "skipped": 0,
            "xfailed": 0,
        }
        result = build_reconciliation(summary)
        assert result["collected"] == 30
        assert result["deselected"] == 5
        assert result["error"] == 2

    def test_missing_keys_default_to_zero(self):
        result = build_reconciliation({})
        assert result["collected"] == 0 and result["pass_rate"] == 0.0

    def test_deselected_derived_from_collected_minus_total(self):
        # pytest often omits a 'deselected' count; derive it so the breakdown
        # always reconciles: collected == deselected + total.
        summary = {"collected": 100, "total": 80, "passed": 80}
        result = build_reconciliation(summary)
        assert result["deselected"] == 20
        assert result["collected"] == result["deselected"] + result["total"]


# categorize_outcome.


@pytest.mark.unit
class TestCategorizeOutcome:
    def test_passed(self):
        assert categorize_outcome({"outcome": "passed"}) == TestOutcome.PASS

    def test_error_is_its_own_category(self):
        # A setup/fixture crash reports outcome "error"; it must not be lumped
        # into FAIL (it never reached a verdict).
        assert categorize_outcome({"outcome": "error"}) == TestOutcome.ERROR

    def test_skipped(self):
        assert categorize_outcome({"outcome": "skipped"}) == TestOutcome.SKIPPED

    def test_xfailed(self):
        assert categorize_outcome({"outcome": "xfailed"}) == TestOutcome.XFAIL

    def test_xpassed(self):
        assert categorize_outcome({"outcome": "xpassed"}) == TestOutcome.XPASS

    def test_failed(self):
        assert categorize_outcome({"outcome": "failed"}) == TestOutcome.FAIL

    def test_unknown_outcome_defaults_to_fail(self):
        assert categorize_outcome({"outcome": ""}) == TestOutcome.FAIL


# feature_path.


@pytest.mark.unit
class TestFeaturePath:
    def test_extracts_path_including_file(self):
        nodeid = (
            "documentdb_tests/compatibility/tests/core/operator/expressions/"
            "arithmetic/add/test_add_numeric.py::test_add"
        )
        assert feature_path(nodeid) == [
            "core",
            "operator",
            "expressions",
            "arithmetic",
            "add",
            "test_add_numeric.py",
        ]

    def test_shallow_path(self):
        nodeid = (
            "documentdb_tests/compatibility/tests/changeStreams/create/"
            "test_smoke_changeStream_create.py::test_it"
        )
        assert feature_path(nodeid) == [
            "changeStreams",
            "create",
            "test_smoke_changeStream_create.py",
        ]

    def test_file_is_deepest_tier_selector_dropped(self):
        nodeid = "documentdb_tests/compatibility/tests/core/test_x.py::test_y[param]"
        # Directory + file are tiers; the ::test[param] selector is dropped.
        assert feature_path(nodeid) == ["core", "test_x.py"]

    def test_missing_root_returns_empty(self):
        assert feature_path("some/other/path/test_x.py::test_y") == []


# group_by_feature.


@pytest.mark.unit
class TestGroupByFeature:
    def _tests(self):
        base = "documentdb_tests/compatibility/tests/"
        return [
            {"name": base + "core/operator/string/test_a.py::t", "outcome": TestOutcome.PASS},
            {"name": base + "core/operator/string/test_b.py::t", "outcome": TestOutcome.FAIL},
            {"name": base + "core/operator/array/test_c.py::t", "outcome": TestOutcome.PASS},
            {"name": base + "system/security/test_d.py::t", "outcome": TestOutcome.ERROR},
        ]

    def test_counts_aggregate_up_the_tree(self):
        tree = group_by_feature(self._tests())
        # core holds 3 tests (2 pass, 1 fail); operator holds the same 3.
        core = tree["children"]["core"]
        assert core["counts"]["passed"] == 2
        assert core["counts"]["failed"] == 1
        assert core["children"]["operator"]["counts"]["passed"] == 2

    def test_leaf_holds_its_own_tests(self):
        tree = group_by_feature(self._tests())
        string_node = tree["children"]["core"]["children"]["operator"]["children"]["string"]
        # string aggregates its two files; each file is the actual leaf.
        assert string_node["counts"]["passed"] == 1
        assert string_node["counts"]["failed"] == 1
        assert set(string_node["children"]) == {"test_a.py", "test_b.py"}
        leaf = string_node["children"]["test_a.py"]
        assert leaf["counts"]["passed"] == 1 and leaf["children"] == {}

    def test_ragged_depths_coexist(self):
        # system/security is depth 2; core/operator/string is depth 3, both group.
        tree = group_by_feature(self._tests())
        assert tree["children"]["system"]["children"]["security"]["counts"]["error"] == 1

    def test_root_totals_all_tests(self):
        tree = group_by_feature(self._tests())
        c = tree["counts"]
        assert c["passed"] == 2 and c["failed"] == 1 and c["error"] == 1

    def test_empty_input(self):
        tree = group_by_feature([])
        assert tree["children"] == {} and tree["counts"]["passed"] == 0

    def test_deselected_tests_appear_with_reasons(self):
        base = "documentdb_tests/compatibility/tests/"
        deselected = {
            base + "changeStreams/insert/test_x.py::t": {"replica_set": True},
            base + "changeStreams/update/test_y.py::t": {"replica_set": True},
        }
        tree = group_by_feature([], deselected)
        cs = tree["children"]["changeStreams"]
        # Deselected tests are counted separately (not as passed) and their
        # required capability is recorded for display.
        assert cs["counts"]["deselected"] == 2
        assert cs["counts"]["passed"] == 0
        assert cs["requires"] == {"replica_set"}

    def test_deselected_and_run_tests_coexist(self):
        base = "documentdb_tests/compatibility/tests/"
        tests = [{"name": base + "core/operator/test_a.py::t", "outcome": TestOutcome.PASS}]
        deselected = {base + "changeStreams/insert/test_x.py::t": {"replica_set": True}}
        tree = group_by_feature(tests, deselected)
        assert tree["children"]["core"]["counts"]["passed"] == 1
        assert tree["children"]["changeStreams"]["counts"]["deselected"] == 1
