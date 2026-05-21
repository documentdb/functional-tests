"""Tests for $first accumulator in $group context."""

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

# Property [Null and Missing NOT Excluded]: $first returns whatever the
# first document has, including null and missing values.
FIRST_NULL_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_first_then_value",
        docs=[{"v": None}, {"v": 5}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when first doc has null (first wins)",
    ),
    AccumulatorTestCase(
        "null_missing_first_then_value",
        docs=[{"x": 1}, {"v": 5}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when first doc has missing field",
    ),
    AccumulatorTestCase(
        "null_value_first_then_null",
        docs=[{"v": 5}, {"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": 5}],
        msg="$first should return 5 when first doc has value, second is null",
    ),
    AccumulatorTestCase(
        "null_value_first_then_missing",
        docs=[{"v": 5}, {"x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": 5}],
        msg="$first should return 5 when first doc has value, second is missing",
    ),
    AccumulatorTestCase(
        "null_all",
        docs=[{"v": None}, {"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when all docs have null",
    ),
    AccumulatorTestCase(
        "null_missing_all",
        docs=[{"x": 1}, {"x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when all docs have missing field",
    ),
    AccumulatorTestCase(
        "null_and_missing_mixed",
        docs=[{"v": None}, {"x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when first is null and second is missing",
    ),
    AccumulatorTestCase(
        "null_remove_first_then_value",
        docs=[{"v": -1}, {"v": 5}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$first": {"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            }
        ],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when first doc produces $$REMOVE",
    ),
    AccumulatorTestCase(
        "null_remove_all",
        docs=[{"v": -1}, {"v": -2}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$first": {"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            }
        ],
        expected=[{"_id": None, "result": None}],
        msg="$first should return null when all docs produce $$REMOVE",
    ),
    AccumulatorTestCase(
        "null_remove_second_value_first",
        docs=[{"v": 5}, {"v": -1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$first": {"$cond": [{"$gt": ["$v", 0]}, "$v", "$$REMOVE"]}},
                }
            }
        ],
        expected=[{"_id": None, "result": 5}],
        msg="$first should return value when first doc has value, second $$REMOVE",
    ),
]

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

# Property [Input Forms]: $first accumulator accepts various expression types as its operand.
FIRST_INPUT_FORM_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "input_field_path",
        docs=[{"v": 10}, {"v": 20}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": 10}],
        msg="$first should accept a basic field path reference",
    ),
    AccumulatorTestCase(
        "input_nested_field",
        docs=[{"a": {"b": 10}}, {"a": {"b": 20}}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$a.b"}}}],
        expected=[{"_id": None, "result": 10}],
        msg="$first should accept a nested document field path",
    ),
    AccumulatorTestCase(
        "input_literal",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": 42}}}],
        expected=[{"_id": None, "result": 42}],
        msg="$first with a literal constant should return that constant",
    ),
    AccumulatorTestCase(
        "input_null_literal",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": None}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first with null literal should return null",
    ),
]

# Property [Edge Cases]: edge cases unique to the accumulator context.
FIRST_EDGE_CASE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "edge_single_doc",
        docs=[{"v": 42}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": 42}],
        msg="$first of a single document should return that document's value",
    ),
    AccumulatorTestCase(
        "edge_single_null_doc",
        docs=[{"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first of a single null document should return null",
    ),
    AccumulatorTestCase(
        "edge_single_missing_doc",
        docs=[{"x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": None}],
        msg="$first of a single document with missing field should return null",
    ),
    AccumulatorTestCase(
        "edge_many_docs",
        docs=[{"v": i} for i in range(100)],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": 0}],
        msg="$first should return first document's value (v=0) across 100 documents",
    ),
    AccumulatorTestCase(
        "edge_empty_collection",
        docs=None,
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[],
        msg="$first on empty collection should return empty result",
    ),
    AccumulatorTestCase(
        "edge_array_not_traversed",
        docs=[{"v": [5, 1, 8]}, {"v": [3, 9, 2]}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": "$v"}}}],
        expected=[{"_id": None, "result": [5, 1, 8]}],
        msg="$first should return array as whole value, not traverse it",
    ),
    AccumulatorTestCase(
        "edge_literal_constant",
        docs=[{"v": 1}, {"v": 2}, {"v": 3}],
        pipeline=[{"$group": {"_id": None, "result": {"$first": 42}}}],
        expected=[{"_id": None, "result": 42}],
        msg="$first with literal constant should always return that constant",
    ),
]

FIRST_GROUP_SUCCESS_TESTS = (
    FIRST_NULL_MISSING_TESTS
    + FIRST_BSON_TYPE_TESTS
    + FIRST_SPECIAL_NUMERIC_TESTS
    + FIRST_DECIMAL_PRECISION_TESTS
    + FIRST_TYPE_DISTINCTION_TESTS
    + FIRST_MIXED_TYPE_TESTS
    + FIRST_INPUT_FORM_TESTS
    + FIRST_EDGE_CASE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(FIRST_GROUP_SUCCESS_TESTS))
def test_accumulator_first_group(collection, test_case: AccumulatorTestCase):
    """Test $first accumulator success cases via $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


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


@pytest.mark.parametrize("test_case", pytest_params(FIRST_RETURN_TYPE_TESTS))
def test_accumulator_first_return_type(collection, test_case: AccumulatorTestCase):
    """Test $first return type verification."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
