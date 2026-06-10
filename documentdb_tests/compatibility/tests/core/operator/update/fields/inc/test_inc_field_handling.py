"""
Field handling tests for $inc update field operator.

Tests sign handling, missing fields, argument variations, and dot notation.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Sign Handling]: $inc correctly adds with positive, negative, and zero increments.
SIGN_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "zero_inc",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": 0}},
        expected={"_id": 1, "val": 10},
        msg="$inc should leave field unchanged when increment is zero",
    ),
    UpdateTestCase(
        "positive_inc_on_positive",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": 5}},
        expected={"_id": 1, "val": 15},
        msg="$inc should add positive increment to positive field",
    ),
    UpdateTestCase(
        "negative_inc_on_positive",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": -3}},
        expected={"_id": 1, "val": 7},
        msg="$inc should subtract when increment is negative",
    ),
    UpdateTestCase(
        "positive_inc_on_negative",
        setup_docs=[{"_id": 1, "val": -10}],
        query={"_id": 1},
        update={"$inc": {"val": 5}},
        expected={"_id": 1, "val": -5},
        msg="$inc should add positive increment toward zero on negative field",
    ),
    UpdateTestCase(
        "negative_inc_on_negative",
        setup_docs=[{"_id": 1, "val": -10}],
        query={"_id": 1},
        update={"$inc": {"val": -5}},
        expected={"_id": 1, "val": -15},
        msg="$inc should make negative field more negative with negative increment",
    ),
]

# Property [Missing Field]: $inc on non-existent field creates it with the increment value.
MISSING_FIELD_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "missing_field_int32",
        setup_docs=[{"_id": 1, "other": "data"}],
        query={"_id": 1},
        update={"$inc": {"val": 5}},
        expected={"_id": 1, "other": "data", "val": 5},
        msg="$inc should create missing field with int32 increment value",
    ),
    UpdateTestCase(
        "missing_field_int64",
        setup_docs=[{"_id": 1, "other": "data"}],
        query={"_id": 1},
        update={"$inc": {"val": Int64(5)}},
        expected={"_id": 1, "other": "data", "val": Int64(5)},
        msg="$inc should create missing field with int64 increment value",
    ),
    UpdateTestCase(
        "missing_field_double",
        setup_docs=[{"_id": 1, "other": "data"}],
        query={"_id": 1},
        update={"$inc": {"val": 2.5}},
        expected={"_id": 1, "other": "data", "val": 2.5},
        msg="$inc should create missing field with double increment value",
    ),
    UpdateTestCase(
        "missing_field_decimal128",
        setup_docs=[{"_id": 1, "other": "data"}],
        query={"_id": 1},
        update={"$inc": {"val": Decimal128("3.5")}},
        expected={"_id": 1, "other": "data", "val": Decimal128("3.5")},
        msg="$inc should create missing field with Decimal128 increment value",
    ),
]

# Property [Argument Handling]: $inc supports empty operand, single field, and multiple fields.
ARGUMENT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "empty_operand_noop",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {}},
        expected={"_id": 1, "val": 10},
        msg="$inc should be a no-op with empty operand",
    ),
    UpdateTestCase(
        "single_field",
        setup_docs=[{"_id": 1, "a": 10, "b": 20}],
        query={"_id": 1},
        update={"$inc": {"a": 1}},
        expected={"_id": 1, "a": 11, "b": 20},
        msg="$inc should only affect the specified field",
    ),
    UpdateTestCase(
        "multiple_fields",
        setup_docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        query={"_id": 1},
        update={"$inc": {"a": 1, "b": 2, "c": 3}},
        expected={"_id": 1, "a": 11, "b": 22, "c": 33},
        msg="$inc should increment all specified fields independently",
    ),
    UpdateTestCase(
        "multiple_fields_some_missing",
        setup_docs=[{"_id": 1, "a": 10}],
        query={"_id": 1},
        update={"$inc": {"a": 1, "b": 2}},
        expected={"_id": 1, "a": 11, "b": 2},
        msg="$inc should create missing fields when incrementing multiple fields",
    ),
]

# Property [Dot Notation]: $inc supports dot notation for nested fields and array indices.
DOT_NOTATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "embedded_field",
        setup_docs=[{"_id": 1, "a": {"b": 5}}],
        query={"_id": 1},
        update={"$inc": {"a.b": 1}},
        expected={"_id": 1, "a": {"b": 6}},
        msg="$inc should work on embedded field via dot notation",
    ),
    UpdateTestCase(
        "array_index",
        setup_docs=[{"_id": 1, "arr": [10, 20, 30]}],
        query={"_id": 1},
        update={"$inc": {"arr.0": 1}},
        expected={"_id": 1, "arr": [11, 20, 30]},
        msg="$inc should work on array element by numeric index",
    ),
    UpdateTestCase(
        "missing_nested_creates_path",
        setup_docs=[{"_id": 1, "a": {}}],
        query={"_id": 1},
        update={"$inc": {"a.b": 1}},
        expected={"_id": 1, "a": {"b": 1}},
        msg="$inc should create missing nested field via dot notation",
    ),
]

ALL_FIELD_TESTS = SIGN_TESTS + MISSING_FIELD_TESTS + ARGUMENT_TESTS + DOT_NOTATION_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_FIELD_TESTS))
def test_inc_field_handling(collection, test: UpdateTestCase):
    """Test $inc field handling behavior."""
    collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)
