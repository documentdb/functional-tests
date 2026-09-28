"""Tests for find command field type validation."""

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_NAMESPACE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class FindFieldValidationTest(BaseTestCase):
    """Test case for find command field validation."""

    command: Any = None


# Property [Command Field Rejection]: find rejects non-string types for the collection
# name field. Wire-protocol namespace validation (INVALID_NAMESPACE_ERROR for non-string
# types) is foundational behavior per TEST_COVERAGE.md §19. One representative case wires
# find to that behavior; the full type matrix belongs in the centralized namespace test
# site (currently TBD).
FIND_FIELD_TESTS: list[FindFieldValidationTest] = [
    FindFieldValidationTest(
        "find_field_rejects_non_string",
        command={"find": 1},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="find should reject non-string type for collection name field.",
    ),
    FindFieldValidationTest(
        "find_field_rejects_empty_string",
        command={"find": ""},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="find should reject empty string collection name.",
    ),
    FindFieldValidationTest(
        "find_field_rejects_dollar_prefix",
        command={"find": "$invalid"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="find should reject dollar-prefixed collection name.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_FIELD_TESTS))
def test_find_field_validation(collection, test):
    """Test find command field validation."""
    result = execute_command(collection, test.command)
    assertResult(result, error_code=test.error_code, msg=test.msg)


# Property [Filter Type Rejection]: find rejects non-document types for the filter field.
FILTER_TYPE_TESTS: list[FindFieldValidationTest] = [
    FindFieldValidationTest(
        "filter_rejects_string",
        command=None,
        error_code=TYPE_MISMATCH_ERROR,
        msg="find should reject string filter.",
    ),
    FindFieldValidationTest(
        "filter_rejects_integer",
        command=None,
        error_code=TYPE_MISMATCH_ERROR,
        msg="find should reject integer filter.",
    ),
    FindFieldValidationTest(
        "filter_rejects_boolean",
        command=None,
        error_code=TYPE_MISMATCH_ERROR,
        msg="find should reject boolean filter.",
    ),
    FindFieldValidationTest(
        "filter_rejects_array",
        command=None,
        error_code=TYPE_MISMATCH_ERROR,
        msg="find should reject array filter.",
    ),
    FindFieldValidationTest(
        "filter_rejects_null",
        command=None,
        error_code=TYPE_MISMATCH_ERROR,
        msg="find should reject null filter.",
    ),
]

_FILTER_DYNAMIC_COMMANDS = {
    "filter_rejects_string": lambda name: {"find": name, "filter": "invalid"},
    "filter_rejects_integer": lambda name: {"find": name, "filter": 123},
    "filter_rejects_boolean": lambda name: {"find": name, "filter": True},
    "filter_rejects_array": lambda name: {"find": name, "filter": [{"a": 1}]},
    "filter_rejects_null": lambda name: {"find": name, "filter": None},
}


@pytest.mark.parametrize("test", pytest_params(FILTER_TYPE_TESTS))
def test_find_filter_type_validation(collection, test):
    """Test find filter field type validation."""
    command = _FILTER_DYNAMIC_COMMANDS[test.id](collection.name)
    result = execute_command(collection, command)
    assertResult(result, error_code=test.error_code, msg=test.msg)


# Property [Skip Validation]: find rejects invalid skip values.
SKIP_VALIDATION_TESTS: list[FindFieldValidationTest] = [
    FindFieldValidationTest(
        "skip_rejects_negative",
        command=None,
        error_code=BAD_VALUE_ERROR,
        msg="find should reject negative skip value.",
    ),
    FindFieldValidationTest(
        "skip_rejects_string",
        command=None,
        error_code=TYPE_MISMATCH_ERROR,
        msg="find should reject string skip value.",
    ),
]

_SKIP_DYNAMIC_COMMANDS = {
    "skip_rejects_negative": lambda name: {"find": name, "skip": -1},
    "skip_rejects_string": lambda name: {"find": name, "skip": "invalid"},
}


@pytest.mark.parametrize("test", pytest_params(SKIP_VALIDATION_TESTS))
def test_find_skip_validation(collection, test):
    """Test find skip field validation."""
    command = _SKIP_DYNAMIC_COMMANDS[test.id](collection.name)
    result = execute_command(collection, command)
    assertResult(result, error_code=test.error_code, msg=test.msg)


# Property [Limit Validation]: find rejects invalid limit values.
LIMIT_VALIDATION_TESTS: list[FindFieldValidationTest] = [
    FindFieldValidationTest(
        "limit_rejects_negative",
        command=None,
        error_code=BAD_VALUE_ERROR,
        msg="find should reject negative limit value.",
    ),
    FindFieldValidationTest(
        "limit_rejects_string",
        command=None,
        error_code=TYPE_MISMATCH_ERROR,
        msg="find should reject string limit value.",
    ),
]

_LIMIT_DYNAMIC_COMMANDS = {
    "limit_rejects_negative": lambda name: {"find": name, "limit": -1},
    "limit_rejects_string": lambda name: {"find": name, "limit": "invalid"},
}


@pytest.mark.parametrize("test", pytest_params(LIMIT_VALIDATION_TESTS))
def test_find_limit_validation(collection, test):
    """Test find limit field validation."""
    command = _LIMIT_DYNAMIC_COMMANDS[test.id](collection.name)
    result = execute_command(collection, command)
    assertResult(result, error_code=test.error_code, msg=test.msg)


def test_find_skip_accepts_whole_double(collection):
    """Test find accepts whole-number double for skip."""
    collection.insert_many([{"_id": i} for i in range(5)])
    result = execute_command(collection, {"find": collection.name, "skip": 2.0, "sort": {"_id": 1}})
    assertResult(
        result,
        expected=[{"_id": 2}, {"_id": 3}, {"_id": 4}],
        msg="find should accept whole-number double for skip.",
    )


def test_find_limit_accepts_whole_double(collection):
    """Test find accepts whole-number double for limit."""
    collection.insert_many([{"_id": i} for i in range(5)])
    result = execute_command(
        collection, {"find": collection.name, "limit": 2.0, "sort": {"_id": 1}}
    )
    assertResult(
        result,
        expected=[{"_id": 0}, {"_id": 1}],
        msg="find should accept whole-number double for limit.",
    )


def test_find_skip_accepts_int64(collection):
    """Test find accepts Int64 for skip."""
    collection.insert_many([{"_id": i} for i in range(5)])
    result = execute_command(
        collection, {"find": collection.name, "skip": Int64(2), "sort": {"_id": 1}}
    )
    assertResult(
        result,
        expected=[{"_id": 2}, {"_id": 3}, {"_id": 4}],
        msg="find should accept Int64 for skip.",
    )


def test_find_limit_accepts_int64(collection):
    """Test find accepts Int64 for limit."""
    collection.insert_many([{"_id": i} for i in range(5)])
    result = execute_command(
        collection, {"find": collection.name, "limit": Int64(2), "sort": {"_id": 1}}
    )
    assertResult(
        result,
        expected=[{"_id": 0}, {"_id": 1}],
        msg="find should accept Int64 for limit.",
    )


def test_find_sort_rejects_array(collection):
    """Test find rejects array type for sort field."""
    result = execute_command(collection, {"find": collection.name, "sort": [1, -1]})
    assertResult(
        result,
        error_code=TYPE_MISMATCH_ERROR,
        msg="find should reject array type for sort field.",
    )


def test_find_projection_rejects_string(collection):
    """Test find rejects string type for projection field."""
    result = execute_command(collection, {"find": collection.name, "projection": "a"})
    assertResult(
        result,
        error_code=TYPE_MISMATCH_ERROR,
        msg="find should reject string type for projection field.",
    )


def test_find_projection_rejects_integer(collection):
    """Test find rejects integer type for projection field."""
    result = execute_command(collection, {"find": collection.name, "projection": 123})
    assertResult(
        result,
        error_code=TYPE_MISMATCH_ERROR,
        msg="find should reject integer type for projection field.",
    )


def test_find_projection_rejects_array(collection):
    """Test find rejects array type for projection field."""
    result = execute_command(collection, {"find": collection.name, "projection": ["a"]})
    assertResult(
        result,
        error_code=TYPE_MISMATCH_ERROR,
        msg="find should reject array type for projection field.",
    )


def test_find_rejects_unrecognized_field(collection):
    """Test find rejects unrecognized top-level command fields."""
    result = execute_command(collection, {"find": collection.name, "unknownField": 123})
    assertResult(
        result,
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="find should reject unrecognized command fields.",
    )
