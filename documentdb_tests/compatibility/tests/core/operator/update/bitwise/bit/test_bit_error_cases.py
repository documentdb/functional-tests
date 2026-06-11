"""Tests for $bit update operator error cases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CONFLICTING_UPDATE_OPERATORS_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import DATE_EPOCH


@dataclass(frozen=True)
class BitErrorTest(BaseTestCase):
    """Test case for $bit error scenarios."""

    setup_doc: Any = None
    update: Any = None


def run_bit_error(collection, test: BitErrorTest):
    """Insert setup doc and run $bit update, returning the result."""
    collection.insert_one(test.setup_doc)
    return execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": test.update}],
        },
    )


# Property [Field Type Rejection]: $bit rejects all non-integer field values with
# BAD_VALUE_ERROR. Only Int32 and Int64 are accepted.
FIELD_TYPE_ERROR_TESTS: list[BitErrorTest] = [
    BitErrorTest(
        "field_double",
        setup_doc={"_id": 1, "v": 3.14},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject double field value.",
    ),
    BitErrorTest(
        "field_string",
        setup_doc={"_id": 1, "v": "hello"},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject string field value.",
    ),
    BitErrorTest(
        "field_bool_true",
        setup_doc={"_id": 1, "v": True},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject bool field value.",
    ),
    BitErrorTest(
        "field_bool_false",
        setup_doc={"_id": 1, "v": False},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject bool false field value.",
    ),
    BitErrorTest(
        "field_date",
        setup_doc={"_id": 1, "v": DATE_EPOCH},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject date field value.",
    ),
    BitErrorTest(
        "field_null",
        setup_doc={"_id": 1, "v": None},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject null field value.",
    ),
    BitErrorTest(
        "field_object",
        setup_doc={"_id": 1, "v": {"key": "value"}},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject embedded document field value.",
    ),
    BitErrorTest(
        "field_empty_object",
        setup_doc={"_id": 1, "v": {}},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject empty document field value.",
    ),
    BitErrorTest(
        "field_array",
        setup_doc={"_id": 1, "v": [1, 2]},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject array field value.",
    ),
    BitErrorTest(
        "field_empty_array",
        setup_doc={"_id": 1, "v": []},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject empty array field value.",
    ),
    BitErrorTest(
        "field_binary",
        setup_doc={"_id": 1, "v": Binary(b"\x00\x01")},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject binary field value.",
    ),
    BitErrorTest(
        "field_objectid",
        setup_doc={"_id": 1, "v": ObjectId("000000000000000000000000")},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject ObjectId field value.",
    ),
    BitErrorTest(
        "field_regex",
        setup_doc={"_id": 1, "v": Regex("^abc", "i")},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject regex field value.",
    ),
    BitErrorTest(
        "field_javascript",
        setup_doc={"_id": 1, "v": Code("function(){}")},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject JavaScript field value.",
    ),
    BitErrorTest(
        "field_timestamp",
        setup_doc={"_id": 1, "v": Timestamp(0, 1)},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject Timestamp field value.",
    ),
    BitErrorTest(
        "field_decimal128",
        setup_doc={"_id": 1, "v": Decimal128("10")},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject Decimal128 field value.",
    ),
    BitErrorTest(
        "field_minkey",
        setup_doc={"_id": 1, "v": MinKey()},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject MinKey field value.",
    ),
    BitErrorTest(
        "field_maxkey",
        setup_doc={"_id": 1, "v": MaxKey()},
        update={"$bit": {"v": {"and": 1}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject MaxKey field value.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_TYPE_ERROR_TESTS))
def test_bit_field_type_errors(collection, test: BitErrorTest):
    """Test $bit rejects non-integer field types."""
    result = run_bit_error(collection, test)
    assertFailureCode(result, test.error_code, msg=test.msg)  # type: ignore[arg-type]


# Property [Operand Type Rejection]: $bit rejects all non-integer operand values with
# BAD_VALUE_ERROR. Only Int32 and Int64 are accepted as operands.
OPERAND_TYPE_ERROR_TESTS: list[BitErrorTest] = [
    BitErrorTest(
        "operand_double",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"and": 10.5}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject double operand.",
    ),
    BitErrorTest(
        "operand_string",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"and": "10"}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject string operand.",
    ),
    BitErrorTest(
        "operand_bool",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"and": True}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject bool operand.",
    ),
    BitErrorTest(
        "operand_null",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"and": None}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject null operand.",
    ),
    BitErrorTest(
        "operand_decimal128",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"and": Decimal128("10")}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject Decimal128 operand.",
    ),
    BitErrorTest(
        "operand_array",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"and": [10]}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject array operand.",
    ),
    BitErrorTest(
        "operand_object",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"and": {"value": 10}}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject object operand.",
    ),
    BitErrorTest(
        "operand_objectid",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"and": ObjectId("000000000000000000000000")}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject ObjectId operand.",
    ),
    BitErrorTest(
        "operand_date",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"and": DATE_EPOCH}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject date operand.",
    ),
    BitErrorTest(
        "operand_binary",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"and": Binary(b"")}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject binary operand.",
    ),
    BitErrorTest(
        "operand_regex",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"and": Regex("x")}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject regex operand.",
    ),
    BitErrorTest(
        "operand_timestamp",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"and": Timestamp(0, 0)}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject Timestamp operand.",
    ),
    BitErrorTest(
        "operand_minkey",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"and": MinKey()}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject MinKey operand.",
    ),
    BitErrorTest(
        "operand_maxkey",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"and": MaxKey()}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject MaxKey operand.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OPERAND_TYPE_ERROR_TESTS))
def test_bit_operand_type_errors(collection, test: BitErrorTest):
    """Test $bit rejects non-integer operand types."""
    result = run_bit_error(collection, test)
    assertFailureCode(result, test.error_code, msg=test.msg)  # type: ignore[arg-type]


# Property [Operation Key Rejection]: $bit rejects unknown operation keys with
# BAD_VALUE_ERROR.
OPERATION_KEY_ERROR_TESTS: list[BitErrorTest] = [
    BitErrorTest(
        "op_invalid_key",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"invalid": 10}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject unknown operation key.",
    ),
    BitErrorTest(
        "op_not_key",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {"not": 10}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject 'not' as operation key.",
    ),
    BitErrorTest(
        "op_empty_sub_doc",
        setup_doc={"_id": 1, "v": 10},
        update={"$bit": {"v": {}}},
        error_code=BAD_VALUE_ERROR,
        msg="$bit should reject empty operations sub-document.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OPERATION_KEY_ERROR_TESTS))
def test_bit_operation_key_errors(collection, test: BitErrorTest):
    """Test $bit rejects invalid operation keys."""
    result = run_bit_error(collection, test)
    assertFailureCode(result, test.error_code, msg=test.msg)  # type: ignore[arg-type]


# Property [Path Conflicts]: $bit rejects conflicting update paths and conflicts with
# other update operators on the same field.


def test_bit_path_conflict_parent_and_child(collection):
    """Test $bit rejects conflicting parent and child paths."""
    collection.insert_one({"_id": 1, "a": {"b": 10}})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$bit": {"a": {"or": 1}, "a.b": {"or": 1}}}}],
        },
    )
    assertFailureCode(
        result,
        CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$bit should reject conflicting parent and child paths.",
    )


def test_bit_array_element_non_integer(collection):
    """Test $bit on non-integer array element fails."""
    collection.insert_one({"_id": 1, "arr": ["hello", 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$bit": {"arr.0": {"and": 1}}}}],
        },
    )
    assertFailureCode(result, BAD_VALUE_ERROR, msg="$bit should reject non-integer array element.")
