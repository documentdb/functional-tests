"""Tests for getClusterParameter argument and command-document handling.

Covers the parameter argument's accepted/rejected BSON types, the three
documented argument forms (single name / array / wildcard), array-form edge
cases, null/empty-string coercion, and command-document quirks (comment field,
case-sensitive command key, unrecognized fields).

Parameter values vary by deployment, so success cases assert on response
structure (ok, clusterParameters length/type) and never on exact values.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.compatibility.tests.system.administration.commands.getClusterParameter.utils import (  # noqa: E501
    valid_parameter_names,
)
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
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gt, IsType, Len
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import BsonType

pytestmark = pytest.mark.admin


# ---------------------------------------------------------------------------
# Category #1 / #3: argument BSON-type rejection
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
# Category #2 / #10: documented argument forms and array shapes
# ---------------------------------------------------------------------------


def test_getClusterParameter_single_name_returns_one(collection):
    """Test a single parameter name returns exactly one entry."""
    (name,) = valid_parameter_names(collection, 1)
    result = execute_admin_command(collection, {"getClusterParameter": name})
    assertProperties(
        result,
        {"ok": Eq(1.0), "clusterParameters": Len(1)},
        msg="Single name should return exactly one clusterParameters entry.",
        raw_res=True,
    )


def test_getClusterParameter_array_single_name_returns_one(collection):
    """Test a one-element array behaves like the single-name form."""
    names = valid_parameter_names(collection, 1)
    result = execute_admin_command(collection, {"getClusterParameter": names})
    assertProperties(
        result,
        {"ok": Eq(1.0), "clusterParameters": Len(1)},
        msg="One-element array should return exactly one entry.",
        raw_res=True,
    )


def test_getClusterParameter_array_two_names_returns_two(collection):
    """Test an array of two valid names returns two entries."""
    names = valid_parameter_names(collection, 2)
    result = execute_admin_command(collection, {"getClusterParameter": names})
    assertProperties(
        result,
        {"ok": Eq(1.0), "clusterParameters": Len(2)},
        msg="Array of two names should return two entries.",
        raw_res=True,
    )


def test_getClusterParameter_array_three_names_returns_three(collection):
    """Test an array of three valid names returns three entries."""
    names = valid_parameter_names(collection, 3)
    result = execute_admin_command(collection, {"getClusterParameter": names})
    assertProperties(
        result,
        {"ok": Eq(1.0), "clusterParameters": Len(3)},
        msg="Array of three names should return three entries.",
        raw_res=True,
    )


def test_getClusterParameter_wildcard_succeeds(collection):
    """Test the '*' wildcard returns an array of parameters with ok:1."""
    result = execute_admin_command(collection, {"getClusterParameter": "*"})
    assertProperties(
        result,
        {"ok": Eq(1.0), "clusterParameters": IsType("array")},
        msg="'*' should return a clusterParameters array with ok:1.",
        raw_res=True,
    )


def test_getClusterParameter_wildcard_is_non_empty(collection):
    """Test the '*' wildcard returns at least one parameter."""
    result = execute_admin_command(collection, {"getClusterParameter": "*"})
    count = len(result["clusterParameters"])
    assertProperties(
        {"count": count},
        {"count": Gt(0)},
        msg=f"'*' should return at least one parameter (got {count}).",
        raw_res=True,
    )


def test_getClusterParameter_duplicate_names(collection):
    """Test an array with a duplicated valid name is accepted."""
    names = valid_parameter_names(collection, 1)
    result = execute_admin_command(collection, {"getClusterParameter": [names[0], names[0]]})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="Array with a duplicated valid name should be accepted.",
    )


def test_getClusterParameter_many_names_no_truncation(collection):
    """Test a large array of names is handled without truncation or failure."""
    names = valid_parameter_names(collection, 1)
    big = [names[0]] * 100
    result = execute_admin_command(collection, {"getClusterParameter": big})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="Large array of names should succeed without truncation.",
    )


# ---------------------------------------------------------------------------
# Argument / array-element error cases (parametrized)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ArgumentErrorCase(BaseTestCase):
    """An argument value expected to produce a specific error code."""

    argument: Any = None


_ARGUMENT_ERROR_CASES: list[ArgumentErrorCase] = [
    ArgumentErrorCase(
        "array_with_int_element",
        argument=["validNamePlaceholder", 123],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Array with a non-string (int) element should be rejected.",
    ),
    ArgumentErrorCase(
        "nested_array_element",
        argument=[["validNamePlaceholder"]],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Array with a nested-array element should be rejected.",
    ),
    ArgumentErrorCase(
        "object_element",
        argument=[{"x": 1}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Array with a document element should be rejected.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(_ARGUMENT_ERROR_CASES))
def test_getClusterParameter_array_element_rejects_type(collection, test):
    """Test array elements that are not strings are rejected."""
    result = execute_admin_command(collection, {"getClusterParameter": test.argument})
    assertFailureCode(result, test.error_code, msg=test.msg)


# ---------------------------------------------------------------------------
# Category #6: null / empty-string coercion of the argument
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


def test_getClusterParameter_empty_array_argument(collection):
    """Test an empty array does not return all parameters."""
    result = execute_admin_command(collection, {"getClusterParameter": []})
    assertFailureCode(
        result,
        BAD_VALUE_ERROR,
        msg="Empty array should not return all parameters.",
    )


# ---------------------------------------------------------------------------
# Category #15: command-document quirks
# ---------------------------------------------------------------------------


def test_getClusterParameter_comment_accepted(collection):
    """Test the optional comment field is accepted and does not affect success."""
    result = execute_admin_command(
        collection, {"getClusterParameter": "*", "comment": "functional-test"}
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="comment field should be accepted.",
    )


def test_getClusterParameter_unrecognized_field_ignored(collection):
    """Test an unrecognized top-level field is ignored rather than rejected."""
    result = execute_admin_command(collection, {"getClusterParameter": "*", "bogusField": 1})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg="Unrecognized top-level field should be ignored.",
    )


def test_getClusterParameter_wrong_case_command_key(collection):
    """Test the command key is case-sensitive (getclusterparameter is unknown)."""
    result = execute_admin_command(collection, {"getclusterparameter": "*"})
    assertFailureCode(
        result,
        COMMAND_NOT_FOUND_ERROR,
        msg="Lower-case command key should be an unknown command.",
    )
