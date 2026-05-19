"""Tests for $last accumulator: BSON type passthrough, null/missing, sort order, expressions."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_MAX,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)


def _group_last(acc):
    """Build a $sort + $group pipeline for $last."""
    return [
        {"$sort": {"_id": 1}},
        {"$group": {"_id": None, "result": {"$last": acc}}},
        {"$project": {"_id": 0, "result": 1}},
    ]


# Property [BSON Type Passthrough]: $last returns the last value in a group
# unchanged, preserving its exact BSON type without coercion.
LAST_BSON_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_double",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 3.14}],
        pipeline=_group_last("$v"),
        expected=[{"result": 3.14}],
        msg="$last should return double value unchanged",
    ),
    AccumulatorTestCase(
        "bson_int32",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 42}],
        pipeline=_group_last("$v"),
        expected=[{"result": 42}],
        msg="$last should return int32 value unchanged",
    ),
    AccumulatorTestCase(
        "bson_int64",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Int64(9223372036854775807)}],
        pipeline=_group_last("$v"),
        expected=[{"result": Int64(9223372036854775807)}],
        msg="$last should return int64 value unchanged",
    ),
    AccumulatorTestCase(
        "bson_decimal128",
        docs=[
            {"_id": 0, "v": 1},
            {"_id": 1, "v": Decimal128("123.456")},
        ],
        pipeline=_group_last("$v"),
        expected=[{"result": Decimal128("123.456")}],
        msg="$last should return Decimal128 value unchanged",
    ),
    AccumulatorTestCase(
        "bson_string",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": "hello"}],
        pipeline=_group_last("$v"),
        expected=[{"result": "hello"}],
        msg="$last should return string value unchanged",
    ),
    AccumulatorTestCase(
        "bson_bool_true",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": True}],
        pipeline=_group_last("$v"),
        expected=[{"result": True}],
        msg="$last should return boolean true unchanged",
    ),
    AccumulatorTestCase(
        "bson_bool_false",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": False}],
        pipeline=_group_last("$v"),
        expected=[{"result": False}],
        msg="$last should return boolean false unchanged",
    ),
    AccumulatorTestCase(
        "bson_date",
        docs=[
            {"_id": 0, "v": 1},
            {"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=_group_last("$v"),
        expected=[{"result": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        msg="$last should return datetime value unchanged",
    ),
    AccumulatorTestCase(
        "bson_null",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": None}],
        pipeline=_group_last("$v"),
        expected=[{"result": None}],
        msg="$last should return null value unchanged",
    ),
    AccumulatorTestCase(
        "bson_object",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": {"nested": "doc"}}],
        pipeline=_group_last("$v"),
        expected=[{"result": {"nested": "doc"}}],
        msg="$last should return embedded document unchanged",
    ),
    AccumulatorTestCase(
        "bson_array",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": [1, 2, 3]}],
        pipeline=_group_last("$v"),
        expected=[{"result": [1, 2, 3]}],
        msg="$last should return entire array unchanged without traversal",
    ),
    AccumulatorTestCase(
        "bson_binary",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Binary(b"\x00\x01\x02")}],
        pipeline=_group_last("$v"),
        expected=[{"result": b"\x00\x01\x02"}],
        msg="$last should return Binary value unchanged",
    ),
    AccumulatorTestCase(
        "bson_objectid",
        docs=[
            {"_id": 0, "v": 1},
            {"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")},
        ],
        pipeline=_group_last("$v"),
        expected=[{"result": ObjectId("507f1f77bcf86cd799439011")}],
        msg="$last should return ObjectId unchanged",
    ),
    AccumulatorTestCase(
        "bson_regex",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Regex("^abc", "i")}],
        pipeline=_group_last("$v"),
        expected=[{"result": Regex("^abc", "i")}],
        msg="$last should return Regex unchanged",
    ),
    AccumulatorTestCase(
        "bson_code",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Code("function(){}")}],
        pipeline=_group_last("$v"),
        expected=[{"result": "function(){}"}],
        msg="$last should return Code as string via runCommand",
    ),
    AccumulatorTestCase(
        "bson_timestamp",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Timestamp(1, 1)}],
        pipeline=_group_last("$v"),
        expected=[{"result": Timestamp(1, 1)}],
        msg="$last should return Timestamp unchanged",
    ),
    AccumulatorTestCase(
        "bson_minkey",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": MinKey()}],
        pipeline=_group_last("$v"),
        expected=[{"result": {"": MinKey()}}],
        msg="$last should return MinKey wrapped as object via runCommand",
    ),
    AccumulatorTestCase(
        "bson_maxkey",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": MaxKey()}],
        pipeline=_group_last("$v"),
        expected=[{"result": {"": MaxKey()}}],
        msg="$last should return MaxKey wrapped as object via runCommand",
    ),
]

# Property [Null and Missing Handling]: $last returns whatever value the last
# document has. If the field is missing, $last returns null. Unlike numeric
# accumulators, $last does NOT ignore nulls.
LAST_NULL_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "null_last_doc",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": None}],
        pipeline=_group_last("$v"),
        expected=[{"result": None}],
        msg="$last should return null when last document has null value",
    ),
    AccumulatorTestCase(
        "missing_last_doc",
        docs=[{"_id": 0, "v": 1}, {"_id": 1}],
        pipeline=_group_last("$v"),
        expected=[{"result": None}],
        msg="$last should return null when last document has missing field",
    ),
    AccumulatorTestCase(
        "null_all",
        docs=[{"_id": 0, "v": None}, {"_id": 1, "v": None}],
        pipeline=_group_last("$v"),
        expected=[{"result": None}],
        msg="$last should return null when all values are null",
    ),
    AccumulatorTestCase(
        "missing_all",
        docs=[{"_id": 0}, {"_id": 1}],
        pipeline=_group_last("$v"),
        expected=[{"result": None}],
        msg="$last should return null when all documents have missing field",
    ),
    AccumulatorTestCase(
        "null_not_last",
        docs=[{"_id": 0, "v": None}, {"_id": 1, "v": 10}],
        pipeline=_group_last("$v"),
        expected=[{"result": 10}],
        msg="$last should return last value even when earlier values are null",
    ),
    AccumulatorTestCase(
        "missing_not_last",
        docs=[{"_id": 0}, {"_id": 1, "v": 10}],
        pipeline=_group_last("$v"),
        expected=[{"result": 10}],
        msg="$last should return last value even when earlier fields are missing",
    ),
    AccumulatorTestCase(
        "null_among_values",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": None}, {"_id": 2, "v": 20}],
        pipeline=_group_last("$v"),
        expected=[{"result": 20}],
        msg="$last should return value from last document regardless of intermediate nulls",
    ),
    AccumulatorTestCase(
        "missing_among_values",
        docs=[{"_id": 0, "v": 10}, {"_id": 1}, {"_id": 2, "v": 20}],
        pipeline=_group_last("$v"),
        expected=[{"result": 20}],
        msg="$last should return value from last doc regardless of intermediate missing fields",
    ),
]

# Property [Sort Order Dependency]: $last returns the value from the last
# document as determined by the preceding $sort stage.
LAST_SORT_ORDER_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "sort_ascending",
        docs=[
            {"_id": 0, "v": 10},
            {"_id": 1, "v": 20},
            {"_id": 2, "v": 30},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 30}],
        msg="$last should return highest value when sorted ascending",
    ),
    AccumulatorTestCase(
        "sort_descending",
        docs=[
            {"_id": 0, "v": 10},
            {"_id": 1, "v": 20},
            {"_id": 2, "v": 30},
        ],
        pipeline=[
            {"$sort": {"v": -1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 10}],
        msg="$last should return lowest value when sorted descending",
    ),
    AccumulatorTestCase(
        "sort_by_secondary_field",
        docs=[
            {"_id": 0, "s": 1, "v": "a"},
            {"_id": 1, "s": 3, "v": "c"},
            {"_id": 2, "s": 2, "v": "b"},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "c"}],
        msg="$last should return value from document with highest sort key",
    ),
    AccumulatorTestCase(
        "sort_by_id",
        docs=[
            {"_id": 3, "v": "third"},
            {"_id": 1, "v": "first"},
            {"_id": 2, "v": "second"},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "third"}],
        msg="$last should return value from document with highest _id when sorted by _id",
    ),
    AccumulatorTestCase(
        "compound_sort",
        docs=[
            {"_id": 0, "cat": "A", "val": 1, "v": "a1"},
            {"_id": 1, "cat": "A", "val": 2, "v": "a2"},
            {"_id": 2, "cat": "B", "val": 1, "v": "b1"},
        ],
        pipeline=[
            {"$sort": {"cat": 1, "val": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "b1"}],
        msg="$last should return value from last document by compound sort order",
    ),
]

# Property [Special Numeric Passthrough]: $last passes through special numeric
# values (NaN, Infinity, negative zero) without transformation.
LAST_SPECIAL_NUMERIC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nan_double",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": FLOAT_NAN}],
        pipeline=_group_last("$v"),
        expected=[{"result": pytest.approx(math.nan, nan_ok=True)}],
        msg="$last should return double NaN unchanged",
    ),
    AccumulatorTestCase(
        "nan_decimal128",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Decimal128("NaN")}],
        pipeline=_group_last("$v"),
        expected=[{"result": Decimal128("NaN")}],
        msg="$last should return Decimal128 NaN unchanged",
    ),
    AccumulatorTestCase(
        "inf_double",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": FLOAT_INFINITY}],
        pipeline=_group_last("$v"),
        expected=[{"result": FLOAT_INFINITY}],
        msg="$last should return double Infinity unchanged",
    ),
    AccumulatorTestCase(
        "neg_inf_double",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=_group_last("$v"),
        expected=[{"result": FLOAT_NEGATIVE_INFINITY}],
        msg="$last should return double -Infinity unchanged",
    ),
    AccumulatorTestCase(
        "inf_decimal128",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Decimal128("Infinity")}],
        pipeline=_group_last("$v"),
        expected=[{"result": Decimal128("Infinity")}],
        msg="$last should return Decimal128 Infinity unchanged",
    ),
    AccumulatorTestCase(
        "neg_inf_decimal128",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": Decimal128("-Infinity")}],
        pipeline=_group_last("$v"),
        expected=[{"result": Decimal128("-Infinity")}],
        msg="$last should return Decimal128 -Infinity unchanged",
    ),
    AccumulatorTestCase(
        "neg_zero_double",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": DOUBLE_NEGATIVE_ZERO}],
        pipeline=_group_last("$v"),
        expected=[{"result": DOUBLE_NEGATIVE_ZERO}],
        msg="$last should preserve double -0.0 unchanged",
    ),
    AccumulatorTestCase(
        "neg_zero_decimal128",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": DECIMAL128_NEGATIVE_ZERO}],
        pipeline=_group_last("$v"),
        expected=[{"result": DECIMAL128_NEGATIVE_ZERO}],
        msg="$last should preserve Decimal128 -0 unchanged",
    ),
]

# Property [Numeric Boundary Passthrough]: $last passes through numeric
# boundary values without corruption.
LAST_BOUNDARY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "boundary_int32_max",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": INT32_MAX}],
        pipeline=_group_last("$v"),
        expected=[{"result": INT32_MAX}],
        msg="$last should return INT32_MAX unchanged",
    ),
    AccumulatorTestCase(
        "boundary_int32_min",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": INT32_MIN}],
        pipeline=_group_last("$v"),
        expected=[{"result": INT32_MIN}],
        msg="$last should return INT32_MIN unchanged",
    ),
    AccumulatorTestCase(
        "boundary_int64_max",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": INT64_MAX}],
        pipeline=_group_last("$v"),
        expected=[{"result": INT64_MAX}],
        msg="$last should return INT64_MAX unchanged",
    ),
    AccumulatorTestCase(
        "boundary_int64_min",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": INT64_MIN}],
        pipeline=_group_last("$v"),
        expected=[{"result": INT64_MIN}],
        msg="$last should return INT64_MIN unchanged",
    ),
    AccumulatorTestCase(
        "boundary_double_max",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": DOUBLE_MAX}],
        pipeline=_group_last("$v"),
        expected=[{"result": DOUBLE_MAX}],
        msg="$last should return DOUBLE_MAX unchanged",
    ),
    AccumulatorTestCase(
        "boundary_double_min_subnormal",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": DOUBLE_MIN_SUBNORMAL}],
        pipeline=_group_last("$v"),
        expected=[{"result": DOUBLE_MIN_SUBNORMAL}],
        msg="$last should return double min subnormal unchanged",
    ),
    AccumulatorTestCase(
        "boundary_decimal128_max",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": DECIMAL128_MAX}],
        pipeline=_group_last("$v"),
        expected=[{"result": DECIMAL128_MAX}],
        msg="$last should return DECIMAL128_MAX unchanged",
    ),
    AccumulatorTestCase(
        "boundary_decimal128_min",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": DECIMAL128_MIN}],
        pipeline=_group_last("$v"),
        expected=[{"result": DECIMAL128_MIN}],
        msg="$last should return DECIMAL128_MIN unchanged",
    ),
]

# Property [Array Passthrough]: in accumulator context, $last returns the
# entire array from the last document without traversal.
LAST_ARRAY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "array_whole",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": [1, 2, 3]}],
        pipeline=_group_last("$v"),
        expected=[{"result": [1, 2, 3]}],
        msg="$last should return entire array without traversal",
    ),
    AccumulatorTestCase(
        "array_nested",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": [[1, 2], [3, 4]]}],
        pipeline=_group_last("$v"),
        expected=[{"result": [[1, 2], [3, 4]]}],
        msg="$last should return nested array unchanged",
    ),
    AccumulatorTestCase(
        "array_empty",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": []}],
        pipeline=_group_last("$v"),
        expected=[{"result": []}],
        msg="$last should return empty array unchanged",
    ),
    AccumulatorTestCase(
        "array_of_objects",
        docs=[
            {"_id": 0, "v": 1},
            {"_id": 1, "v": [{"a": 1}, {"a": 2}]},
        ],
        pipeline=_group_last("$v"),
        expected=[{"result": [{"a": 1}, {"a": 2}]}],
        msg="$last should return array of objects unchanged",
    ),
    AccumulatorTestCase(
        "array_single_element",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": [42]}],
        pipeline=_group_last("$v"),
        expected=[{"result": [42]}],
        msg="$last should return single-element array as array, not scalar",
    ),
    AccumulatorTestCase(
        "array_mixed_types",
        docs=[
            {"_id": 0, "v": 1},
            {"_id": 1, "v": [1, "two", None, True]},
        ],
        pipeline=_group_last("$v"),
        expected=[{"result": [1, "two", None, True]}],
        msg="$last should return mixed-type array unchanged",
    ),
]

# Property [Expression Arguments]: $last accepts various expression types
# beyond simple field paths.
LAST_EXPRESSION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_field_path",
        docs=[{"_id": 0, "v": 10}, {"_id": 1, "v": 20}],
        pipeline=_group_last("$v"),
        expected=[{"result": 20}],
        msg="$last should accept field path expression",
    ),
    AccumulatorTestCase(
        "expr_nested_field",
        docs=[
            {"_id": 0, "a": {"b": 10}},
            {"_id": 1, "a": {"b": 20}},
        ],
        pipeline=_group_last("$a.b"),
        expected=[{"result": 20}],
        msg="$last should accept nested field path",
    ),
    AccumulatorTestCase(
        "expr_deep_nested",
        docs=[
            {"_id": 0, "a": {"b": {"c": 10}}},
            {"_id": 1, "a": {"b": {"c": 20}}},
        ],
        pipeline=_group_last("$a.b.c"),
        expected=[{"result": 20}],
        msg="$last should accept deeply nested field path",
    ),
    AccumulatorTestCase(
        "expr_literal",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 2}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": {"$literal": 99}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 99}],
        msg="$last should accept literal expression",
    ),
    AccumulatorTestCase(
        "expr_computed",
        docs=[
            {"_id": 0, "a": 2, "b": 3},
            {"_id": 1, "a": 4, "b": 5},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": {"$multiply": ["$a", "$b"]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 20}],
        msg="$last should accept computed sub-expression",
    ),
    AccumulatorTestCase(
        "expr_conditional",
        docs=[
            {"_id": 0, "v": -5},
            {"_id": 1, "v": 10},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {"$last": {"$cond": [{"$gte": ["$v", 0]}, "$v", 0]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 10}],
        msg="$last should accept conditional expression",
    ),
    AccumulatorTestCase(
        "expr_constant_value",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 2}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": 42}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 42}],
        msg="$last should accept constant literal value",
    ),
    AccumulatorTestCase(
        "expr_missing_nested",
        docs=[
            {"_id": 0, "a": {"b": 10}},
            {"_id": 1, "a": {}},
        ],
        pipeline=_group_last("$a.b"),
        expected=[{"result": None}],
        msg="$last should return null when nested field is missing in last document",
    ),
]

# Property [Mixed BSON Types in Group]: $last does not perform any type
# checking and returns whatever type the last document has.
LAST_MIXED_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "mixed_types_last_wins",
        docs=[
            {"_id": 0, "v": 1},
            {"_id": 1, "v": "hello"},
            {"_id": 2, "v": True},
        ],
        pipeline=_group_last("$v"),
        expected=[{"result": True}],
        msg="$last should return last value regardless of mixed types in group",
    ),
]

LAST_SUCCESS_TESTS = (
    LAST_BSON_TYPE_TESTS
    + LAST_NULL_MISSING_TESTS
    + LAST_SORT_ORDER_TESTS
    + LAST_SPECIAL_NUMERIC_TESTS
    + LAST_BOUNDARY_TESTS
    + LAST_ARRAY_TESTS
    + LAST_EXPRESSION_TESTS
    + LAST_MIXED_TYPE_TESTS
)


def _run(collection, test_case: AccumulatorTestCase):
    """Insert docs and execute the pipeline."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    return execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )


@pytest.mark.parametrize("test_case", pytest_params(LAST_SUCCESS_TESTS))
def test_accumulator_last(collection, test_case: AccumulatorTestCase):
    """Test $last accumulator success cases."""
    result = _run(collection, test_case)
    assertSuccess(result, test_case.expected, msg=test_case.msg)
