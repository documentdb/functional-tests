"""Tests for $isNumber with non-numeric BSON types — all should return false."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = pytest.mark.aggregate


@dataclass(frozen=True)
class IsNumberTest(BaseTestCase):
    value: Any = None


# Property [Non-Numeric Types]: $isNumber returns false for all non-numeric BSON types.
NON_NUMERIC_TYPE_TESTS: list[IsNumberTest] = [
    # String
    IsNumberTest(
        "string_empty", value="", expected=False, msg="Should return false for empty string"
    ),
    IsNumberTest(
        "string_word", value="hello", expected=False, msg="Should return false for string"
    ),
    IsNumberTest(
        "string_numeric", value="42", expected=False, msg="Should return false for numeric string"
    ),
    # Boolean
    IsNumberTest(
        "bool_true", value=True, expected=False, msg="Should return false for boolean true"
    ),
    IsNumberTest(
        "bool_false", value=False, expected=False, msg="Should return false for boolean false"
    ),
    # Array
    IsNumberTest(
        "array_empty", value=[], expected=False, msg="Should return false for empty array"
    ),
    IsNumberTest(
        "array_of_numbers",
        value=[1, 2, 3],
        expected=False,
        msg="Should return false for array of numbers",
    ),
    # Object
    IsNumberTest(
        "object_empty", value={}, expected=False, msg="Should return false for empty object"
    ),
    IsNumberTest(
        "object_with_fields", value={"a": 1}, expected=False, msg="Should return false for object"
    ),
    # ObjectId
    IsNumberTest(
        "objectid", value=ObjectId(), expected=False, msg="Should return false for ObjectId"
    ),
    # Date
    IsNumberTest(
        "date",
        value=datetime(2024, 1, 1, tzinfo=timezone.utc),
        expected=False,
        msg="Should return false for Date",
    ),
    # Timestamp
    IsNumberTest(
        "timestamp", value=Timestamp(1, 0), expected=False, msg="Should return false for Timestamp"
    ),
    # Binary
    IsNumberTest(
        "binary", value=Binary(b"\x00"), expected=False, msg="Should return false for Binary"
    ),
    # Regex
    IsNumberTest("regex", value=Regex(".*"), expected=False, msg="Should return false for Regex"),
    # MinKey / MaxKey
    IsNumberTest("minkey", value=MinKey(), expected=False, msg="Should return false for MinKey"),
    IsNumberTest("maxkey", value=MaxKey(), expected=False, msg="Should return false for MaxKey"),
    # Code
    IsNumberTest(
        "code",
        value=Code("function(){}"),
        expected=False,
        msg="Should return false for JavaScript Code",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NON_NUMERIC_TYPE_TESTS))
def test_isNumber_non_numeric_literal(collection, test):
    """Test $isNumber returns false for non-numeric BSON type literals."""
    result = execute_expression(collection, {"$isNumber": test.value})
    assert_expression_result(result, expected=test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(NON_NUMERIC_TYPE_TESTS))
def test_isNumber_non_numeric_field(collection, test):
    """Test $isNumber returns false when referencing a document field with a non-numeric value."""
    result = execute_expression_with_insert(
        collection, {"$isNumber": "$value"}, {"value": test.value}
    )
    assert_expression_result(result, expected=test.expected, msg=test.msg)
