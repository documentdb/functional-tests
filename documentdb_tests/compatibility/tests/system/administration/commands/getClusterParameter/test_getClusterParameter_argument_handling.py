"""Tests for getClusterParameter argument handling.

Covers BSON type rejection/acceptance for the <parameter> argument,
argument forms (single/array/wildcard/empty), undocumented coercion
edge cases, array-form edge cases, and command-document quirks.

Categories: #1, #2, #3 (type/field portions), #6, #10, #15
"""

import pytest

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertProperties,
    assertSuccessPartial,
)
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    COMMAND_NOT_FOUND_ERROR,
    NO_SUCH_KEY_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Eq, Len
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin

_VALID_PARAM = "changeStreamOptions"
_VALID_PARAM_2 = "changeStreams"


# ---------------------------------------------------------------------------
# §1 / §6  BSON type rejection for non-string / non-array argument types
# The argument must be a string (single name or '*') or an array of strings.
# Every other BSON type is rejected with a type-mismatch error. NULL is handled
# separately in the coercion tests below.
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# §2  Argument forms — accepted
# ---------------------------------------------------------------------------


def test_getClusterParameter_wildcard_returns_all(collection):
    """Test '*' argument returns all available cluster parameters with ok:1."""
    result = execute_admin_command(collection, {"getClusterParameter": "*"})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Wildcard '*' should return ok:1")


def test_getClusterParameter_single_name_returns_one(collection):
    """Test single string name returns exactly one clusterParameters entry."""
    result = execute_admin_command(collection, {"getClusterParameter": _VALID_PARAM})
    assertProperties(
        result,
        {"ok": Eq(1.0), "clusterParameters": Len(1)},
        msg="Single name should return ok:1 with one parameter",
        raw_res=True,
    )


def test_getClusterParameter_array_two_names_returns_two(collection):
    """Test array of two valid names returns two clusterParameters entries."""
    result = execute_admin_command(
        collection, {"getClusterParameter": [_VALID_PARAM, _VALID_PARAM_2]}
    )
    assertProperties(
        result,
        {"ok": Eq(1.0), "clusterParameters": Len(2)},
        msg="Array of two names should return two parameters",
        raw_res=True,
    )


def test_getClusterParameter_array_duplicate_names(collection):
    """Test array with duplicate valid names succeeds."""
    result = execute_admin_command(
        collection, {"getClusterParameter": [_VALID_PARAM, _VALID_PARAM]}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Duplicate names in array should succeed")


# ---------------------------------------------------------------------------
# §2  Argument forms — rejected
# ---------------------------------------------------------------------------


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


def test_getClusterParameter_unrecognized_field_accepted(collection):
    """Test extra comment field is accepted (MongoDB treats it as generic command field)."""
    result = execute_admin_command(collection, {"getClusterParameter": "*", "comment": "test"})
    assertSuccessPartial(result, {"ok": 1.0}, msg="comment field should be accepted")


# ---------------------------------------------------------------------------
# §6  Undocumented coercion edge cases
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# §15  Command-document quirks
# ---------------------------------------------------------------------------


def test_getClusterParameter_wrong_case_command_key_rejected(collection):
    """Test wrong-case command key 'getclusterparameter' is rejected as unknown command."""
    result = execute_admin_command(collection, {"getclusterparameter": "*"})
    assertFailureCode(
        result, COMMAND_NOT_FOUND_ERROR, msg="Wrong-case command key should be rejected"
    )
