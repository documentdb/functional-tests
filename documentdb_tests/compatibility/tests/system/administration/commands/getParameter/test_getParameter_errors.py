"""Tests for getParameter command error cases."""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    COMMAND_NOT_FOUND_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNAUTHORIZED_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


PARAM_NAME_ERROR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "empty_string_param_name",
        command={"getParameter": 1, "": 1},
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject empty string parameter name",
    ),
    DiagnosticTestCase(
        "special_chars_param_name",
        command={"getParameter": 1, "!@#$%": 1},
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject parameter name with special characters",
    ),
    DiagnosticTestCase(
        "very_long_param_name",
        command={"getParameter": 1, "a" * 1000: 1},
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should reject very long parameter name",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PARAM_NAME_ERROR_TESTS))
def test_getParameter_param_name_errors(collection, test):
    """Test getParameter rejects invalid parameter names."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


SUBFIELD_TYPE_ERROR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "showDetails_non_bool",
        command={"getParameter": {"showDetails": "yes"}, "logLevel": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject non-boolean showDetails",
    ),
    DiagnosticTestCase(
        "allParameters_non_bool",
        command={"getParameter": {"allParameters": "yes"}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject non-boolean allParameters",
    ),
    DiagnosticTestCase(
        "setAt_non_string",
        command={"getParameter": {"allParameters": True, "setAt": 123}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject non-string setAt",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SUBFIELD_TYPE_ERROR_TESTS))
def test_getParameter_subfield_type_errors(collection, test):
    """Test getParameter rejects wrong BSON types for document-form sub-fields."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


SELECTOR_ERROR_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "arbitrary_string_not_star",
        command={"getParameter": "foo"},
        error_code=INVALID_OPTIONS_ERROR,
        msg="Non-'*' string value should be rejected as a parameter name",
    ),
    DiagnosticTestCase(
        "int_form_no_param_name",
        command={"getParameter": 1},
        error_code=INVALID_OPTIONS_ERROR,
        msg="Integer form without a named parameter should fail",
    ),
    DiagnosticTestCase(
        "empty_doc_no_param_name",
        command={"getParameter": {}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="Empty document without a named parameter should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SELECTOR_ERROR_TESTS))
def test_getParameter_selector_errors(collection, test):
    """Test getParameter rejects invalid or missing parameter selectors."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_getParameter_on_non_admin_db_fails(collection):
    """Test getParameter run on a non-admin database fails with Unauthorized."""
    result = execute_command(collection, {"getParameter": 1, "logLevel": 1})
    assertFailureCode(result, UNAUTHORIZED_ERROR, msg="Non-admin DB should fail")


def test_getParameter_param_name_case_sensitive(collection):
    """Test that parameter names are case-sensitive."""
    result = execute_admin_command(collection, {"getParameter": 1, "LOGLEVEL": 1})
    assertFailureCode(
        result, INVALID_OPTIONS_ERROR, msg="Case-mismatched parameter name should fail"
    )


def test_getParameter_unrecognized_field_treated_as_param(collection):
    """Test an unknown top-level field is treated as a non-existent parameter name."""
    result = execute_admin_command(collection, {"getParameter": 1, "unknownField": 1})
    assertFailureCode(
        result,
        INVALID_OPTIONS_ERROR,
        msg="Unknown field alone treated as non-existent parameter",
    )


def test_getParameter_doc_form_unrecognized_field_fails(collection):
    """Test the document form with unrecognized fields fails."""
    result = execute_admin_command(
        collection, {"getParameter": {"unknownField": True}, "logLevel": 1}
    )
    assertFailureCode(
        result, UNRECOGNIZED_COMMAND_FIELD_ERROR, msg="Unrecognized doc field should fail"
    )


def test_getParameter_no_getParameter_field_fails(collection):
    """Test a command without the getParameter field fails with CommandNotFound."""
    result = execute_admin_command(collection, {"logLevel": 1})
    assertFailureCode(result, COMMAND_NOT_FOUND_ERROR, msg="Missing getParameter field should fail")


def test_getParameter_command_field_not_first_fails(collection):
    """Test the command fails when getParameter is not the first field."""
    result = execute_admin_command(collection, {"logLevel": 1, "getParameter": 1})
    assertFailureCode(result, COMMAND_NOT_FOUND_ERROR, msg="Command field not first should fail")


def test_getParameter_setAt_invalid_value(collection):
    """Test setAt with an invalid value fails with BadValue."""
    result = execute_admin_command(
        collection, {"getParameter": {"allParameters": True, "setAt": "invalid"}}
    )
    assertFailureCode(result, BAD_VALUE_ERROR, msg="Invalid setAt value should fail")


def test_getParameter_setAt_empty_string(collection):
    """Test setAt with an empty string fails with BadValue, not treated as no filter."""
    result = execute_admin_command(
        collection, {"getParameter": {"allParameters": True, "setAt": ""}}
    )
    assertFailureCode(result, BAD_VALUE_ERROR, msg="Empty-string setAt value should fail")
