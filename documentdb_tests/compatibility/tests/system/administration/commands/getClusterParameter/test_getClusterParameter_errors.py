"""Tests for getClusterParameter error cases.

Consolidates all error-producing inputs: BSON type rejection for the
argument field, unknown parameter names, invalid argument forms, null
coercion, array element type errors, namespace enforcement, and
command-key case sensitivity.

Categories: #1, #2, #3, #6, #11, #15, #16, #18
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    COMMAND_NOT_FOUND_ERROR,
    INVALID_OPTIONS_ERROR,
    NO_SUCH_KEY_ERROR,
    TYPE_MISMATCH_ERROR,
    UNAUTHORIZED_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin

_VALID_PARAM = "changeStreamOptions"
_PARAM = "changeStreamOptions"


_ARGUMENT_TYPE_SPEC = [
    BsonTypeTestCase(
        id="getClusterParameter_argument",
        msg="getClusterParameter should reject non-string/non-array argument types",
        keyword="getClusterParameter",
        valid_types=[BsonType.STRING, BsonType.ARRAY],
        default_error_code=TYPE_MISMATCH_ERROR,
        skip_rejection_types=[BsonType.NULL],
    ),
]

_ARGUMENT_REJECTION_CASES = generate_bson_rejection_test_cases(_ARGUMENT_TYPE_SPEC)


@pytest.mark.parametrize("bson_type,sample_value,spec", _ARGUMENT_REJECTION_CASES)
def test_getClusterParameter_argument_rejects_type(collection, bson_type, sample_value, spec):
    """Test getClusterParameter rejects non-string/non-array argument types."""
    result = execute_admin_command(collection, {"getClusterParameter": sample_value})
    assertFailureCode(
        result,
        spec.expected_code(bson_type),
        msg=f"getClusterParameter should reject {bson_type.value} argument.",
    )


@dataclass(frozen=True)
class NameCase(BaseTestCase):
    """Test case for literal name semantics."""

    name: Any = None


_BOUNDARY_NAMES: list[NameCase] = [
    NameCase(
        "whitespace_only",
        name="   ",
        error_code=NO_SUCH_KEY_ERROR,
        msg="Whitespace-only string should be treated as a literal no-match",
    ),
    NameCase(
        "dotted_name",
        name="a.b.c",
        error_code=NO_SUCH_KEY_ERROR,
        msg="Dotted name should not be traversed as a field path",
    ),
    NameCase(
        "dollar_prefix",
        name="$foo",
        error_code=NO_SUCH_KEY_ERROR,
        msg="Dollar-prefixed name should not be interpreted as an operator",
    ),
    NameCase(
        "unicode_name",
        name="paramétré",
        error_code=NO_SUCH_KEY_ERROR,
        msg="Unicode name should be treated as a literal no-match",
    ),
    NameCase(
        "very_long_name",
        name="x" * 10000,
        error_code=NO_SUCH_KEY_ERROR,
        msg="Very long name should not crash or timeout",
    ),
    NameCase(
        "case_altered",
        name="ChangeStreamOptions",
        error_code=NO_SUCH_KEY_ERROR,
        msg="Altered-case known name should not match (case-sensitive)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(_BOUNDARY_NAMES))
def test_getClusterParameter_name_is_literal_string(collection, test):
    """Test that parameter names are treated as exact literal strings."""
    result = execute_admin_command(collection, {"getClusterParameter": test.name})
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_getClusterParameter_star_in_array_is_literal_name(collection):
    """Test ['*'] treats '*' as a literal name (not expand-all) and errors."""
    result = execute_admin_command(collection, {"getClusterParameter": ["*"]})
    assertFailureCode(
        result, NO_SUCH_KEY_ERROR, msg="'*' inside an array is a literal name, not a wildcard"
    )


def test_getClusterParameter_double_star_no_glob(collection):
    """Test '**' is treated as a literal name, not a pattern."""
    result = execute_admin_command(collection, {"getClusterParameter": "**"})
    assertFailureCode(result, NO_SUCH_KEY_ERROR, msg="'**' should not be treated as a glob")


def test_getClusterParameter_star_prefix_no_glob(collection):
    """Test '*foo' is treated as a literal name, not a pattern."""
    result = execute_admin_command(collection, {"getClusterParameter": "*foo"})
    assertFailureCode(result, NO_SUCH_KEY_ERROR, msg="'*foo' should not be treated as a glob")


def test_getClusterParameter_array_star_and_valid_name(collection):
    """Test ['*', validName] treats '*' as a literal no-match and errors."""
    result = execute_admin_command(collection, {"getClusterParameter": ["*", _VALID_PARAM]})
    assertFailureCode(
        result,
        NO_SUCH_KEY_ERROR,
        msg="'*' inside array with valid name should still error on '*' literal",
    )


def test_getClusterParameter_unknown_single_string_errors(collection):
    """Test single unknown string fails with NO_SUCH_KEY_ERROR."""
    result = execute_admin_command(collection, {"getClusterParameter": "unknownParam"})
    assertFailureCode(
        result,
        NO_SUCH_KEY_ERROR,
        msg="Single unknown name should fail with no-such-parameter error",
    )


def test_getClusterParameter_unknown_in_array_errors(collection):
    """Test ['unknownParam'] fails with same error as 'unknownParam' string."""
    result = execute_admin_command(collection, {"getClusterParameter": ["unknownParam"]})
    assertFailureCode(
        result,
        NO_SUCH_KEY_ERROR,
        msg="Array containing single unknown name should fail identically to string form",
    )


def test_getClusterParameter_empty_array_errors(collection):
    """Test empty array argument fails with BAD_VALUE_ERROR."""
    result = execute_admin_command(collection, {"getClusterParameter": []})
    assertFailureCode(result, BAD_VALUE_ERROR, msg="Empty array must supply at least one name")


def test_getClusterParameter_array_nonstring_element_rejects(collection):
    """Test array containing a non-string element fails with TYPE_MISMATCH_ERROR."""
    result = execute_admin_command(collection, {"getClusterParameter": [_VALID_PARAM, 123]})
    assertFailureCode(
        result, TYPE_MISMATCH_ERROR, msg="Non-string array element should be rejected"
    )


def test_getClusterParameter_unknown_name_errors(collection):
    """Test an unknown parameter name fails with NO_SUCH_KEY_ERROR (code 4)."""
    result = execute_admin_command(collection, {"getClusterParameter": "doesNotExist"})
    assertFailureCode(result, NO_SUCH_KEY_ERROR, msg="Unknown parameter name should fail")


def test_getClusterParameter_null_argument(collection):
    """Test a null argument is rejected with a type-mismatch error."""
    result = execute_admin_command(collection, {"getClusterParameter": None})
    assertFailureCode(
        result,
        TYPE_MISMATCH_ERROR,
        msg="Null argument should be rejected as a type mismatch.",
    )


def test_getClusterParameter_empty_string_argument(collection):
    """Test an empty-string argument is treated as an unknown parameter name."""
    result = execute_admin_command(collection, {"getClusterParameter": ""})
    assertFailureCode(
        result,
        NO_SUCH_KEY_ERROR,
        msg="Empty-string argument should be treated as an unknown parameter name.",
    )


def test_getClusterParameter_array_null_element_rejects(collection):
    """Test array containing null element fails with TYPE_MISMATCH_ERROR."""
    result = execute_admin_command(collection, {"getClusterParameter": [None]})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="Null element in array should be rejected")


def test_getClusterParameter_array_doc_element_rejects(collection):
    """Test array containing a document element fails with TYPE_MISMATCH_ERROR."""
    result = execute_admin_command(collection, {"getClusterParameter": [{"a": 1}]})
    assertFailureCode(
        result, TYPE_MISMATCH_ERROR, msg="Document element in array should be rejected"
    )


def test_getClusterParameter_array_nested_array_rejects(collection):
    """Test array containing a nested array element fails with TYPE_MISMATCH_ERROR."""
    result = execute_admin_command(collection, {"getClusterParameter": [[_VALID_PARAM]]})
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="Nested array element should be rejected")


def test_getClusterParameter_array_mixed_valid_unknown_errors(collection):
    """Test array with one valid and one unknown name fails with NO_SUCH_KEY_ERROR."""
    result = execute_admin_command(
        collection, {"getClusterParameter": [_VALID_PARAM, "unknownParam"]}
    )
    assertFailureCode(result, NO_SUCH_KEY_ERROR, msg="Unknown entry in mixed array should fail")


def test_getClusterParameter_wrong_case_command_key_rejected(collection):
    """Test wrong-case command key 'getclusterparameter' is rejected as unknown command."""
    result = execute_admin_command(collection, {"getclusterparameter": "*"})
    assertFailureCode(
        result, COMMAND_NOT_FOUND_ERROR, msg="Wrong-case command key should be rejected"
    )


def test_getClusterParameter_rejected_on_non_admin_database(collection):
    """Test getClusterParameter is rejected against a non-admin database."""
    result = execute_command(collection, {"getClusterParameter": "*"})
    assertFailureCode(
        result,
        UNAUTHORIZED_ERROR,
        msg="getClusterParameter should be rejected on a non-admin database.",
    )


def test_getClusterParameter_name_not_retrievable_via_getParameter(collection):
    """Test a cluster parameter name cannot be retrieved via getParameter."""
    result = execute_admin_command(collection, {"getParameter": 1, _PARAM: 1})
    assertFailureCode(
        result,
        INVALID_OPTIONS_ERROR,
        msg="Cluster parameter name should not be retrievable via getParameter",
    )
