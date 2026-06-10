"""
Tests for $set update operator - data type handling.

Verifies type overwrite, BSON type preservation (int32, int64, double, bool,
Date, ObjectId, Timestamp, Binary, Decimal128), Decimal128 precision,
double special values, and value shapes.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, ObjectId, Timestamp

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_ZERO,
)

SET_DATA_TYPE_TESTS: list[UpdateTestCase] = [
    # Type overwrite
    UpdateTestCase(
        id="array_to_string",
        setup_docs=[{"_id": 1, "field": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"field": "new_string"}},
        expected=[{"_id": 1, "field": "new_string"}],
        msg="Should overwrite array with string",
    ),
    UpdateTestCase(
        id="array_to_object",
        setup_docs=[{"_id": 1, "field": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"field": {"nested": 1}}},
        expected=[{"_id": 1, "field": {"nested": 1}}],
        msg="Should overwrite array with object",
    ),
    # BSON type distinction
    UpdateTestCase(
        id="int32_one",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": 1}},
        expected=[{"_id": 1, "field": 1}],
        msg="Should preserve int32 type",
    ),
    UpdateTestCase(
        id="int64_one",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": Int64(1)}},
        expected=[{"_id": 1, "field": Int64(1)}],
        msg="Should preserve int64 type",
    ),
    UpdateTestCase(
        id="double_one",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": 1.0}},
        expected=[{"_id": 1, "field": 1.0}],
        msg="Should preserve double type",
    ),
    UpdateTestCase(
        id="bool_true_vs_int_one",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": True}},
        expected=[{"_id": 1, "field": True}],
        msg="Should preserve bool (not coerce to int 1)",
    ),
    UpdateTestCase(
        id="bool_false_vs_int_zero",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": False}},
        expected=[{"_id": 1, "field": False}],
        msg="Should preserve bool (not coerce to int 0)",
    ),
    UpdateTestCase(
        id="date_utc",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)}},
        expected=[{"_id": 1, "field": datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)}],
        msg="Should preserve Date type",
    ),
    UpdateTestCase(
        id="objectid_value",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": ObjectId("507f1f77bcf86cd799439011")}},
        expected=[{"_id": 1, "field": ObjectId("507f1f77bcf86cd799439011")}],
        msg="Should preserve ObjectId type",
    ),
    UpdateTestCase(
        id="timestamp_value",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": Timestamp(1700000000, 1)}},
        expected=[{"_id": 1, "field": Timestamp(1700000000, 1)}],
        msg="Should preserve Timestamp type",
    ),
    UpdateTestCase(
        id="binary_user_subtype",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": Binary(b"\x00\x01\x02\x03", 128)}},
        expected=[{"_id": 1, "field": Binary(b"\x00\x01\x02\x03", 128)}],
        msg="Should preserve Binary type",
    ),
    UpdateTestCase(
        id="decimal128_one",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": Decimal128("1")}},
        expected=[{"_id": 1, "field": Decimal128("1")}],
        msg="Should preserve decimal128 type",
    ),
    # Value shapes
    UpdateTestCase(
        id="to_empty_array",
        setup_docs=[{"_id": 1, "field": "old"}],
        query={"_id": 1},
        update={"$set": {"field": []}},
        expected=[{"_id": 1, "field": []}],
        msg="Should set field to empty array",
    ),
    UpdateTestCase(
        id="to_empty_object",
        setup_docs=[{"_id": 1, "field": "old"}],
        query={"_id": 1},
        update={"$set": {"field": {}}},
        expected=[{"_id": 1, "field": {}}],
        msg="Should set field to empty object",
    ),
    UpdateTestCase(
        id="to_nested_array",
        setup_docs=[{"_id": 1, "field": "old"}],
        query={"_id": 1},
        update={"$set": {"field": [[1], [2]]}},
        expected=[{"_id": 1, "field": [[1], [2]]}],
        msg="Should set field to nested array",
    ),
    UpdateTestCase(
        id="to_deeply_nested_object",
        setup_docs=[{"_id": 1, "field": "old"}],
        query={"_id": 1},
        update={"$set": {"field": {"a": {"b": {"c": {"d": 1}}}}}},
        expected=[{"_id": 1, "field": {"a": {"b": {"c": {"d": 1}}}}}],
        msg="Should set field to deeply nested object",
    ),
    UpdateTestCase(
        id="unicode_field_name",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$set": {"日本語": "value"}},
        expected=[{"_id": 1, "日本語": "value"}],
        msg="Unicode field name should work",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SET_DATA_TYPE_TESTS))
def test_set_data_types(collection, test):
    """Test $set type overwrite, BSON type distinction, and value shapes."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, test.expected, msg=test.msg)


SET_SPECIAL_VALUE_TESTS: list[UpdateTestCase] = [
    # Decimal128 precision
    UpdateTestCase(
        id="decimal128_max",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": DECIMAL128_MAX}},
        expected=[{"_id": 1, "field": DECIMAL128_MAX}],
        msg="Should preserve DECIMAL128_MAX",
    ),
    UpdateTestCase(
        id="decimal128_min",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": DECIMAL128_MIN}},
        expected=[{"_id": 1, "field": DECIMAL128_MIN}],
        msg="Should preserve DECIMAL128_MIN",
    ),
    UpdateTestCase(
        id="decimal128_neg_zero",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": DECIMAL128_NEGATIVE_ZERO}},
        expected=[{"_id": 1, "field": DECIMAL128_NEGATIVE_ZERO}],
        msg="Should preserve Decimal128 negative zero",
    ),
    UpdateTestCase(
        id="decimal128_infinity",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": DECIMAL128_INFINITY}},
        expected=[{"_id": 1, "field": DECIMAL128_INFINITY}],
        msg="Should preserve Decimal128 Infinity",
    ),
    UpdateTestCase(
        id="decimal128_neg_infinity",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": DECIMAL128_NEGATIVE_INFINITY}},
        expected=[{"_id": 1, "field": DECIMAL128_NEGATIVE_INFINITY}],
        msg="Should preserve Decimal128 -Infinity",
    ),
    UpdateTestCase(
        id="decimal128_nan",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": DECIMAL128_NAN}},
        expected=[{"_id": 1, "field": DECIMAL128_NAN}],
        msg="Should preserve Decimal128 NaN",
    ),
    UpdateTestCase(
        id="decimal128_small_exp",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": DECIMAL128_SMALL_EXPONENT}},
        expected=[{"_id": 1, "field": DECIMAL128_SMALL_EXPONENT}],
        msg="Should preserve Decimal128 small exponent",
    ),
    UpdateTestCase(
        id="decimal128_large_exp",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": DECIMAL128_LARGE_EXPONENT}},
        expected=[{"_id": 1, "field": DECIMAL128_LARGE_EXPONENT}],
        msg="Should preserve Decimal128 large exponent",
    ),
    UpdateTestCase(
        id="decimal128_zero",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": DECIMAL128_ZERO}},
        expected=[{"_id": 1, "field": DECIMAL128_ZERO}],
        msg="Should preserve Decimal128 zero",
    ),
    UpdateTestCase(
        id="decimal128_high_precision",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": Decimal128("1.234567890123456789012345678901234")}},
        expected=[{"_id": 1, "field": Decimal128("1.234567890123456789012345678901234")}],
        msg="Should preserve Decimal128 high precision",
    ),
    # Double special values
    UpdateTestCase(
        id="double_nan",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": float("nan")}},
        expected=[{"_id": 1, "field": float("nan")}],
        msg="Should preserve double NaN",
    ),
    UpdateTestCase(
        id="double_infinity",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": float("inf")}},
        expected=[{"_id": 1, "field": float("inf")}],
        msg="Should preserve double Infinity",
    ),
    UpdateTestCase(
        id="double_neg_infinity",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": float("-inf")}},
        expected=[{"_id": 1, "field": float("-inf")}],
        msg="Should preserve double -Infinity",
    ),
    UpdateTestCase(
        id="double_neg_zero",
        setup_docs=[{"_id": 1, "field": "placeholder"}],
        query={"_id": 1},
        update={"$set": {"field": -0.0}},
        expected=[{"_id": 1, "field": -0.0}],
        msg="Should preserve double -0.0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SET_SPECIAL_VALUE_TESTS))
def test_set_special_values(collection, test):
    """Test $set preserves Decimal128 precision and double special values."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccessNaN(result, test.expected, msg=test.msg)


def test_set_empty_string_vs_null_distinction(collection):
    """Test $set distinguishes empty string from null (BSON type distinction)."""
    collection.insert_one({"_id": 1, "field": ""})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"field": None}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "field": None}], msg="Empty string → null should modify")
