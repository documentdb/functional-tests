"""Tests for getClusterParameter error cases.

Covers error-producing inputs: unknown parameter names, empty and
null arguments, array element type errors, command-key case
sensitivity, and key ordering enforcement. Also verifies that the
command is rejected on non-admin databases.
"""

import pytest

from documentdb_tests.compatibility.tests.system.administration.utils.administration_test_case import (  # noqa: E501
    AdministrationTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    COMMAND_NOT_FOUND_ERROR,
    NO_SUCH_KEY_ERROR,
    TYPE_MISMATCH_ERROR,
    UNAUTHORIZED_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin

_VALID_PARAM = "changeStreamOptions"


_NO_SUCH_KEY_CASES: list[AdministrationTestCase] = [
    AdministrationTestCase(
        id="unknown_single_string_errors",
        command={"getClusterParameter": "unknownParam"},
        error_code=NO_SUCH_KEY_ERROR,
        msg="Single unknown name should fail with no-such-parameter error",
    ),
    AdministrationTestCase(
        id="empty_string_argument",
        command={"getClusterParameter": ""},
        error_code=NO_SUCH_KEY_ERROR,
        msg="Empty-string argument should be treated as an unknown parameter name",
    ),
    AdministrationTestCase(
        id="case_altered",
        command={"getClusterParameter": "ChangeStreamOptions"},
        error_code=NO_SUCH_KEY_ERROR,
        msg="Altered-case known name should not match (case-sensitive)",
    ),
    AdministrationTestCase(
        id="star_in_array_is_literal_name",
        command={"getClusterParameter": ["*"]},
        error_code=NO_SUCH_KEY_ERROR,
        msg="'*' inside an array is a literal name, not a wildcard",
    ),
    AdministrationTestCase(
        id="array_mixed_valid_unknown_errors",
        command={"getClusterParameter": [_VALID_PARAM, "unknownParam"]},
        error_code=NO_SUCH_KEY_ERROR,
        msg="Unknown entry in mixed array should fail",
    ),
]

_TYPE_ERROR_CASES: list[AdministrationTestCase] = [
    AdministrationTestCase(
        id="empty_array_errors",
        command={"getClusterParameter": []},
        error_code=BAD_VALUE_ERROR,
        msg="Empty array must supply at least one name",
    ),
    AdministrationTestCase(
        id="array_nonstring_element_rejects",
        command={"getClusterParameter": [_VALID_PARAM, 123]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Non-string array element should be rejected",
    ),
    AdministrationTestCase(
        id="null_argument",
        command={"getClusterParameter": None},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Null argument should be rejected as a type mismatch",
    ),
    AdministrationTestCase(
        id="array_null_element_rejects",
        command={"getClusterParameter": [None]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Null element in array should be rejected",
    ),
    AdministrationTestCase(
        id="array_doc_element_rejects",
        command={"getClusterParameter": [{"a": 1}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Document element in array should be rejected",
    ),
    AdministrationTestCase(
        id="array_nested_array_rejects",
        command={"getClusterParameter": [[_VALID_PARAM]]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Nested array element should be rejected",
    ),
]

_COMMAND_ROUTING_CASES: list[AdministrationTestCase] = [
    AdministrationTestCase(
        id="wrong_case_command_key_rejected",
        command={"getclusterparameter": "*"},
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="Wrong-case command key should be rejected",
    ),
    AdministrationTestCase(
        id="command_key_not_first_fails",
        command={"comment": "test", "getClusterParameter": "*"},
        error_code=COMMAND_NOT_FOUND_ERROR,
        msg="getClusterParameter must be the first key in the command document",
    ),
]

_ERROR_CASES: list[AdministrationTestCase] = (
    _NO_SUCH_KEY_CASES + _TYPE_ERROR_CASES + _COMMAND_ROUTING_CASES
)


@pytest.mark.parametrize("test", pytest_params(_ERROR_CASES))
def test_getClusterParameter_errors(collection, test):
    """Test all error-producing inputs: unknown names, type mismatches, and command routing."""
    result = execute_admin_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_getClusterParameter_rejected_on_non_admin_database(collection):
    """Test getClusterParameter is rejected against a non-admin database."""
    result = execute_command(collection, {"getClusterParameter": "*"})
    assertFailureCode(
        result,
        UNAUTHORIZED_ERROR,
        msg="getClusterParameter should be rejected on a non-admin database.",
    )
