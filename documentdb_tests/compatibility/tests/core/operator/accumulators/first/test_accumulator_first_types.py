"""Tests for $first accumulator BSON type preservation and type fidelity."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
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

# ---------------------------------------------------------------------------
# Property [BSON Constant Arguments]: $first accepts BSON constants as the
# accumulator argument (not field references). The constant is returned for
# every document, so the "first" value is that constant.
# ---------------------------------------------------------------------------
FIRST_BSON_CONSTANT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "const_true",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": True}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": True}],
        msg="$first with boolean True constant should return True",
    ),
    AccumulatorTestCase(
        "const_false",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": False}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": False}],
        msg="$first with boolean False constant should return False",
    ),
    AccumulatorTestCase(
        "const_int64",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": Int64(42)}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Int64(42)}],
        msg="$first with Int64 constant should return that Int64 value",
    ),
    AccumulatorTestCase(
        "const_double",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": 3.14}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 3.14}],
        msg="$first with double constant should return that double value",
    ),
    AccumulatorTestCase(
        "const_decimal128",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": Decimal128("3.14")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Decimal128("3.14")}],
        msg="$first with Decimal128 constant should return that Decimal128 value",
    ),
    AccumulatorTestCase(
        "const_string",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": "hello"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "hello"}],
        msg="$first with string constant (no $) should return that string",
    ),
    AccumulatorTestCase(
        "const_binary",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": Binary(b"\x01\x02")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": b"\x01\x02"}],
        msg="$first with Binary constant should return that Binary value",
    ),
    AccumulatorTestCase(
        "const_objectid",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$first": ObjectId("000000000000000000000000")},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": ObjectId("000000000000000000000000")}],
        msg="$first with ObjectId constant should return that ObjectId",
    ),
    AccumulatorTestCase(
        "const_datetime",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$first": datetime(2020, 1, 1, tzinfo=timezone.utc)},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        msg="$first with datetime constant should return that datetime",
    ),
    AccumulatorTestCase(
        "const_timestamp",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": Timestamp(1, 1)}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Timestamp(1, 1)}],
        msg="$first with Timestamp constant should return that Timestamp",
    ),
    AccumulatorTestCase(
        "const_regex",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": Regex("abc", "i")}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": Regex("abc", "i")}],
        msg="$first with Regex constant should return that Regex",
    ),
    AccumulatorTestCase(
        "const_null",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": None}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$first with null constant should return null",
    ),
    AccumulatorTestCase(
        "const_minkey",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": MinKey()}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"": MinKey()}}],
        msg="$first with MinKey constant should return MinKey wrapped in document",
    ),
    AccumulatorTestCase(
        "const_maxkey",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": MaxKey()}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"": MaxKey()}}],
        msg="$first with MaxKey constant should return MaxKey wrapped in document",
    ),
]

# ---------------------------------------------------------------------------
# Property [Expression Types]: $first accepts various expression types as
# its operand and evaluates them per document before picking the first.
# ---------------------------------------------------------------------------
FIRST_EXPRESSION_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_operator_single",
        docs=[{"v": -10}, {"v": 20}, {"v": -5}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": {"$abs": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 10}],
        msg="$first should accept single-input expression operator",
    ),
    AccumulatorTestCase(
        "expr_operator_multi_arg",
        docs=[{"v": -10, "w": 3}, {"v": 20, "w": 7}, {"v": -5, "w": 1}],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$first": {"$add": ["$v", "$w"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": -7}],
        msg="$first should accept a multi-arg expression operator",
    ),
    AccumulatorTestCase(
        "expr_nested",
        docs=[{"v": -10}, {"v": 20}, {"v": -5}],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$first": {"$add": [1, {"$abs": "$v"}]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 11}],
        msg="$first should accept nested expression operators",
    ),
    AccumulatorTestCase(
        "expr_sysvar_remove",
        docs=[{"v": 1}, {"v": 2}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": "$$REMOVE"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$first with $$REMOVE should treat value as missing and return null",
    ),
    AccumulatorTestCase(
        "expr_object_expression",
        docs=[{"v": 10}, {"v": 20}, {"v": 5}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$first": {"a": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"a": 5}}],
        msg="$first should accept an object expression",
    ),
    AccumulatorTestCase(
        "expr_object_with_operator",
        docs=[{"v": -10}, {"v": 20}, {"v": -5}],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$first": {"a": {"$abs": "$v"}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": {"a": 10}}],
        msg="$first should accept an object expression containing an operator",
    ),
    AccumulatorTestCase(
        "expr_let",
        docs=[{"v": 10}, {"v": 20}, {"v": 5}],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$first": {"$let": {"vars": {"x": "$v"}, "in": "$$x"}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 5}],
        msg="$first should accept a $let expression as its operand",
    ),
]

FIRST_TYPE_SUCCESS_TESTS = (
    FIRST_BSON_TYPE_TESTS
    + FIRST_SPECIAL_NUMERIC_TESTS
    + FIRST_DECIMAL_PRECISION_TESTS
    + FIRST_MIXED_TYPE_TESTS
    + FIRST_BSON_CONSTANT_TESTS
    + FIRST_EXPRESSION_TYPE_TESTS
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
