"""Tests for failure extraction and categorization in the analyzer."""

from documentdb_tests.compatibility.result_analyzer.analyzer import (
    extract_exception_type,
    extract_failure_tag,
    is_infrastructure_error,
)


def _make_test_result(crash_message: str) -> dict:
    """Helper to build a minimal test result dict with a crash message."""
    return {"call": {"crash": {"message": crash_message}}}


# --- extract_failure_tag ---


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


# --- extract_exception_type ---


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
