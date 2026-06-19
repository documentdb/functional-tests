"""Tests for dropConnections command argument validation.

Verifies type rejection for the hostAndPort field, missing field errors,
array element type handling, command field value variations, and
unrecognized field rejection.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.bson_type_validator import (
    BsonTypeTestCase,
    generate_bson_acceptance_test_cases,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import (
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import BsonType

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


# --- hostAndPort field type rejection ---

# Property [hostAndPort Type Rejection]: dropConnections rejects non-array
# BSON types for the hostAndPort field.
_HOST_AND_PORT_TYPE_SPEC = [
    BsonTypeTestCase(
        id="hostAndPort",
        msg="dropConnections should reject non-array types for hostAndPort",
        keyword="hostAndPort",
        valid_types=[BsonType.ARRAY],
        default_error_code=TYPE_MISMATCH_ERROR,
        skip_rejection_types=[BsonType.NULL],
    ),
]

_REJECTION_CASES = generate_bson_rejection_test_cases(_HOST_AND_PORT_TYPE_SPEC)


@pytest.mark.parametrize("bson_type,sample_value,spec", _REJECTION_CASES)
def test_dropConnections_hostAndPort_rejects_type(collection, bson_type, sample_value, spec):
    """Test dropConnections rejects non-array types for hostAndPort."""
    result = execute_admin_command(collection, {"dropConnections": 1, "hostAndPort": sample_value})
    assertFailureCode(
        result,
        spec.expected_code(bson_type),
        msg=f"dropConnections should reject {bson_type.value} for hostAndPort.",
    )


# --- hostAndPort missing field ---


def test_dropConnections_missing_hostAndPort(collection):
    """Test dropConnections rejects command without hostAndPort field."""
    result = execute_admin_command(collection, {"dropConnections": 1})
    assertFailureCode(
        result,
        MISSING_FIELD_ERROR,
        msg="dropConnections should require hostAndPort field.",
    )


def test_dropConnections_null_hostAndPort(collection):
    """Test dropConnections rejects null for hostAndPort field."""
    result = execute_admin_command(collection, {"dropConnections": 1, "hostAndPort": None})
    assertFailureCode(
        result,
        MISSING_FIELD_ERROR,
        msg="dropConnections should treat null hostAndPort as missing field.",
    )


# --- hostAndPort array element type validation ---


@dataclass(frozen=True)
class ElementTypeTestCase(BaseTestCase):
    """Test case for hostAndPort array element type checking."""

    element: Any = None


# Property [Array Element Types]: dropConnections rejects non-string array
# elements with TYPE_MISMATCH_ERROR, except null which is silently ignored.
_ELEMENT_REJECTION_TESTS: list[ElementTypeTestCase] = [
    ElementTypeTestCase(
        "int_element",
        element=1,
        error_code=TYPE_MISMATCH_ERROR,
        msg="dropConnections should reject int element in hostAndPort.",
    ),
    ElementTypeTestCase(
        "bool_element",
        element=True,
        error_code=TYPE_MISMATCH_ERROR,
        msg="dropConnections should reject bool element in hostAndPort.",
    ),
    ElementTypeTestCase(
        "object_element",
        element={"host": "x"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="dropConnections should reject object element in hostAndPort.",
    ),
    ElementTypeTestCase(
        "nested_array_element",
        element=[],
        error_code=TYPE_MISMATCH_ERROR,
        msg="dropConnections should reject nested array element in hostAndPort.",
    ),
    ElementTypeTestCase(
        "double_element",
        element=3.14,
        error_code=TYPE_MISMATCH_ERROR,
        msg="dropConnections should reject double element in hostAndPort.",
    ),
]

_ELEMENT_IGNORE_TESTS: list[ElementTypeTestCase] = [
    ElementTypeTestCase(
        "null_element_ignored",
        element=None,
        expected={"ok": 1.0},
        msg="dropConnections should silently ignore null element in hostAndPort.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(_ELEMENT_REJECTION_TESTS))
def test_dropConnections_hostAndPort_element_rejects_type(collection, test):
    """Test dropConnections rejects non-string, non-null array elements."""
    result = execute_admin_command(
        collection, {"dropConnections": 1, "hostAndPort": [test.element]}
    )
    assertFailureCode(result, test.error_code, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(_ELEMENT_IGNORE_TESTS))
def test_dropConnections_hostAndPort_element_ignored(collection, test):
    """Test dropConnections silently ignores null array elements."""
    result = execute_admin_command(
        collection, {"dropConnections": 1, "hostAndPort": [test.element]}
    )
    assertSuccessPartial(result, test.expected, msg=test.msg)


# --- Command field value variations ---

# Property [Command Field Acceptance]: dropConnections accepts various BSON
# types for the command field value (the value of the "dropConnections" key).
_COMMAND_FIELD_PARAMS = [
    BsonTypeTestCase(
        id="dropConnections_value",
        msg="dropConnections should accept all BSON types for command field value",
        keyword="dropConnections",
        valid_types=list(BsonType),
    ),
]

_COMMAND_FIELD_ACCEPTANCE = generate_bson_acceptance_test_cases(_COMMAND_FIELD_PARAMS)


@pytest.mark.parametrize("bson_type,sample_value,spec", _COMMAND_FIELD_ACCEPTANCE)
def test_dropConnections_command_field_accepts_type(collection, bson_type, sample_value, spec):
    """Test dropConnections accepts any BSON type for command field value."""
    result = execute_admin_command(collection, {"dropConnections": sample_value, "hostAndPort": []})
    assertSuccessPartial(
        result,
        {"ok": 1.0},
        msg=f"dropConnections should accept {bson_type.value} for command field value.",
    )


# --- Unrecognized field rejection ---


def test_dropConnections_unrecognized_field(collection):
    """Test dropConnections rejects unrecognized top-level fields."""
    result = execute_admin_command(
        collection,
        {"dropConnections": 1, "hostAndPort": [], "unknownField": 1},
    )
    assertFailureCode(
        result,
        UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="dropConnections should reject unrecognized fields.",
    )
