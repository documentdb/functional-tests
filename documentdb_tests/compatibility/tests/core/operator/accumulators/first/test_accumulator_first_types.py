"""Tests for $first accumulator BSON type preservation and type fidelity."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Decimal128,
    Int64,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [BSON Type Preservation]: $first returns the first document's
# value with its BSON type preserved exactly.
FIRST_BSON_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "type_int32",
        docs=[{"v": 42}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": 42}],
        msg="$first should preserve int32 type",
    ),
    AccumulatorTestCase(
        "type_int64",
        docs=[{"v": Int64(42)}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": Int64(42)}],
        msg="$first should preserve Int64 type",
    ),
    AccumulatorTestCase(
        "type_double",
        docs=[{"v": 3.14}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": 3.14}],
        msg="$first should preserve double type",
    ),
    AccumulatorTestCase(
        "type_decimal128",
        docs=[{"v": Decimal128("3.14")}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": Decimal128("3.14")}],
        msg="$first should preserve Decimal128 type",
    ),
    AccumulatorTestCase(
        "type_string",
        docs=[{"v": "hello"}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": "hello"}],
        msg="$first should preserve string type",
    ),
    AccumulatorTestCase(
        "type_bool_true",
        docs=[{"v": True}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": True}],
        msg="$first should preserve boolean True",
    ),
    AccumulatorTestCase(
        "type_bool_false",
        docs=[{"v": False}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": False}],
        msg="$first should preserve boolean False",
    ),
    AccumulatorTestCase(
        "type_null",
        docs=[{"v": None}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first should preserve null value",
    ),
    AccumulatorTestCase(
        "type_embedded_doc",
        docs=[{"v": {"a": 1, "b": 2}}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": {"a": 1, "b": 2}}],
        msg="$first should preserve embedded document",
    ),
    AccumulatorTestCase(
        "type_empty_doc",
        docs=[{"v": {}}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": {}}],
        msg="$first should preserve empty document",
    ),
    AccumulatorTestCase(
        "type_array",
        docs=[{"v": [1, 2, 3]}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": [1, 2, 3]}],
        msg="$first should preserve array value",
    ),
    AccumulatorTestCase(
        "type_empty_array",
        docs=[{"v": []}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": []}],
        msg="$first should preserve empty array",
    ),
    AccumulatorTestCase(
        "type_binary",
        docs=[{"v": Binary(b"\x01\x02")}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": b"\x01\x02"}],
        msg="$first should preserve Binary value",
    ),
    AccumulatorTestCase(
        "type_binary_custom_subtype",
        docs=[{"v": Binary(b"\x01", 5)}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": Binary(b"\x01", 5)}],
        msg="$first should preserve Binary with custom subtype",
    ),
    AccumulatorTestCase(
        "type_objectid",
        docs=[{"v": ObjectId("000000000000000000000001")}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": ObjectId("000000000000000000000001")}],
        msg="$first should preserve ObjectId value",
    ),
    AccumulatorTestCase(
        "type_datetime",
        docs=[{"v": datetime(2023, 6, 15, tzinfo=timezone.utc)}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": datetime(2023, 6, 15, tzinfo=timezone.utc)}],
        msg="$first should preserve datetime value",
    ),
    AccumulatorTestCase(
        "type_timestamp",
        docs=[{"v": Timestamp(100, 1)}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": Timestamp(100, 1)}],
        msg="$first should preserve Timestamp value",
    ),
    AccumulatorTestCase(
        "type_regex",
        docs=[{"v": Regex("abc", "i")}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": Regex("abc", "i")}],
        msg="$first should preserve Regex value",
    ),
]

# Property [Special Numeric Preservation]: $first passes through special
# numeric values exactly as stored in the first document.
FIRST_SPECIAL_NUMERIC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "special_float_nan",
        docs=[{"v": FLOAT_NAN}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$first should preserve float NaN",
    ),
    AccumulatorTestCase(
        "special_float_neg_zero",
        docs=[{"v": DOUBLE_NEGATIVE_ZERO}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": DOUBLE_NEGATIVE_ZERO}],
        msg="$first should preserve double -0.0",
    ),
    AccumulatorTestCase(
        "special_float_inf",
        docs=[{"v": FLOAT_INFINITY}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": FLOAT_INFINITY}],
        msg="$first should preserve float Infinity",
    ),
    AccumulatorTestCase(
        "special_float_neg_inf",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": FLOAT_NEGATIVE_INFINITY}],
        msg="$first should preserve float -Infinity",
    ),
    AccumulatorTestCase(
        "special_decimal_nan",
        docs=[{"v": DECIMAL128_NAN}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": DECIMAL128_NAN}],
        msg="$first should preserve Decimal128 NaN",
    ),
    AccumulatorTestCase(
        "special_decimal_neg_nan",
        docs=[{"v": DECIMAL128_NEGATIVE_NAN}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": DECIMAL128_NEGATIVE_NAN}],
        msg="$first should preserve Decimal128 -NaN",
    ),
    AccumulatorTestCase(
        "special_decimal_neg_zero",
        docs=[{"v": DECIMAL128_NEGATIVE_ZERO}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": DECIMAL128_NEGATIVE_ZERO}],
        msg="$first should preserve Decimal128 -0",
    ),
    AccumulatorTestCase(
        "special_decimal_inf",
        docs=[{"v": DECIMAL128_INFINITY}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": DECIMAL128_INFINITY}],
        msg="$first should preserve Decimal128 Infinity",
    ),
    AccumulatorTestCase(
        "special_decimal_neg_inf",
        docs=[{"v": DECIMAL128_NEGATIVE_INFINITY}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": DECIMAL128_NEGATIVE_INFINITY}],
        msg="$first should preserve Decimal128 -Infinity",
    ),
]

# Property [Decimal128 Precision]: $first passes through Decimal128 values
# without modifying precision, trailing zeros, or exponent.
FIRST_DECIMAL_PRECISION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "decimal_high_precision",
        docs=[{"v": Decimal128("1.234567890123456789012345678901234")}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": Decimal128("1.234567890123456789012345678901234")}],
        msg="$first should preserve 34-digit Decimal128 precision",
    ),
    AccumulatorTestCase(
        "decimal_trailing_zeros",
        docs=[{"v": Decimal128("1.00")}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": Decimal128("1.00")}],
        msg="$first should preserve trailing zeros in Decimal128",
    ),
    AccumulatorTestCase(
        "decimal_large_exponent",
        docs=[{"v": DECIMAL128_LARGE_EXPONENT}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": DECIMAL128_LARGE_EXPONENT}],
        msg="$first should preserve Decimal128 with large exponent",
    ),
    AccumulatorTestCase(
        "decimal_small_positive",
        docs=[{"v": DECIMAL128_MIN_POSITIVE}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": DECIMAL128_MIN_POSITIVE}],
        msg="$first should preserve smallest positive Decimal128",
    ),
    AccumulatorTestCase(
        "decimal_zero",
        docs=[{"v": DECIMAL128_ZERO}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": DECIMAL128_ZERO}],
        msg="$first should preserve Decimal128 zero",
    ),
]

# Property [No Coercion]: $first preserves BSON type distinctions without
# coercing similar-looking values.
FIRST_TYPE_DISTINCTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "distinct_false_not_zero",
        docs=[{"v": False}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": False}],
        msg="$first should return False, not coerce to 0",
    ),
    AccumulatorTestCase(
        "distinct_true_not_one",
        docs=[{"v": True}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": True}],
        msg="$first should return True, not coerce to 1",
    ),
    AccumulatorTestCase(
        "distinct_zero_not_false",
        docs=[{"v": 0}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": 0}],
        msg="$first should return int32(0), not coerce to False",
    ),
    AccumulatorTestCase(
        "distinct_empty_string",
        docs=[{"v": ""}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": ""}],
        msg="$first should return empty string, not coerce to null",
    ),
    AccumulatorTestCase(
        "distinct_string_number",
        docs=[{"v": "123"}, {"v": 999}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": "123"}],
        msg="$first should return string '123', not coerce to int",
    ),
]

# Property [Position-Based]: $first picks the first document's value
# regardless of what other documents contain.
FIRST_MIXED_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mixed_int_then_string",
        docs=[{"v": 42}, {"v": "hello"}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": 42}],
        msg="$first should return int when first doc is int, second is string",
    ),
    AccumulatorTestCase(
        "mixed_string_then_int",
        docs=[{"v": "hello"}, {"v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": "hello"}],
        msg="$first should return string when first doc is string, second is int",
    ),
    AccumulatorTestCase(
        "mixed_bool_then_number",
        docs=[{"v": True}, {"v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": True}],
        msg="$first should return True when first doc is bool, second is int",
    ),
    AccumulatorTestCase(
        "mixed_array_then_scalar",
        docs=[{"v": [1, 2, 3]}, {"v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": [1, 2, 3]}],
        msg="$first should return array when first doc is array, second is scalar",
    ),
]

# Property [Return Type]: $first preserves the BSON type of the returned
# value, verified using $type projection.
FIRST_RETURN_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "return_type_int32",
        docs=[{"v": 42}, {"v": 999}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": 42, "type": "int"}],
        msg="$first of int32 should return type 'int'",
    ),
    AccumulatorTestCase(
        "return_type_int64",
        docs=[{"v": Int64(42)}, {"v": 999}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": Int64(42), "type": "long"}],
        msg="$first of Int64 should return type 'long'",
    ),
    AccumulatorTestCase(
        "return_type_double",
        docs=[{"v": 3.14}, {"v": 999}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": 3.14, "type": "double"}],
        msg="$first of double should return type 'double'",
    ),
    AccumulatorTestCase(
        "return_type_decimal",
        docs=[{"v": Decimal128("3.14")}, {"v": 999}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": Decimal128("3.14"), "type": "decimal"}],
        msg="$first of Decimal128 should return type 'decimal'",
    ),
    AccumulatorTestCase(
        "return_type_string",
        docs=[{"v": "hello"}, {"v": 999}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": "hello", "type": "string"}],
        msg="$first of string should return type 'string'",
    ),
    AccumulatorTestCase(
        "return_type_boolean",
        docs=[{"v": True}, {"v": 999}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": True, "type": "bool"}],
        msg="$first of boolean should return type 'bool'",
    ),
    AccumulatorTestCase(
        "return_type_date",
        docs=[{"v": datetime(2023, 6, 15, tzinfo=timezone.utc)}, {"v": 999}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": datetime(2023, 6, 15, tzinfo=timezone.utc), "type": "date"}],
        msg="$first of datetime should return type 'date'",
    ),
    AccumulatorTestCase(
        "return_type_null",
        docs=[{"v": None}, {"v": 999}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$first": "$v"}}},
            {"$project": {"_id": 0, "value": "$result", "type": {"$type": "$result"}}},
        ],
        expected=[{"value": None, "type": "null"}],
        msg="$first of null should return type 'null'",
    ),
]

FIRST_TYPE_SUCCESS_TESTS = (
    FIRST_BSON_TYPE_TESTS
    + FIRST_SPECIAL_NUMERIC_TESTS
    + FIRST_DECIMAL_PRECISION_TESTS
    + FIRST_TYPE_DISTINCTION_TESTS
    + FIRST_MIXED_TYPE_TESTS
    + FIRST_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(FIRST_TYPE_SUCCESS_TESTS))
def test_accumulator_first_types(collection, test_case: AccumulatorTestCase):
    """Test $first accumulator BSON type preservation and type fidelity."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
