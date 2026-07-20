"""Tests for failure extraction and categorization in the analyzer."""

import pytest

from documentdb_tests.compatibility.result_analyzer.analyzer import (
    TestOutcome,
    build_reconciliation,
    categorize_outcome,
    extract_exception_type,
    extract_failure_tag,
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
