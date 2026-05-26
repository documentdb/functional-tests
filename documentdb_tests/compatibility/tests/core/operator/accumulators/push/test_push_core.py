"""Tests for $push accumulator: BSON type preservation, ordering, duplicates, special values,
type preservation, nested structures, grouping, field paths, and system variables."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [BSON Type Preservation]: $push collects and preserves every
# non-deprecated BSON type in the output array without coercion or
# normalization.
PUSH_BSON_TYPE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_int32",
        docs=[{"v": 42}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [42]}],
        msg="$push should preserve int32 value in output array",
    ),
    AccumulatorTestCase(
        "bson_int64",
        docs=[{"v": Int64(42)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Int64(42)]}],
        msg="$push should preserve Int64 value in output array",
    ),
    AccumulatorTestCase(
        "bson_double",
        docs=[{"v": 3.14}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [3.14]}],
        msg="$push should preserve double value in output array",
    ),
    AccumulatorTestCase(
        "bson_decimal128",
        docs=[{"v": Decimal128("1.5")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Decimal128("1.5")]}],
        msg="$push should preserve Decimal128 value in output array",
    ),
    AccumulatorTestCase(
        "bson_string",
        docs=[{"v": "hello"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": ["hello"]}],
        msg="$push should preserve string value in output array",
    ),
    AccumulatorTestCase(
        "bson_bool_true",
        docs=[{"v": True}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [True]}],
        msg="$push should preserve boolean true in output array",
    ),
    AccumulatorTestCase(
        "bson_bool_false",
        docs=[{"v": False}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [False]}],
        msg="$push should preserve boolean false in output array",
    ),
    AccumulatorTestCase(
        "bson_datetime",
        docs=[{"v": datetime(2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [datetime(2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc)]}],
        msg="$push should preserve datetime value in output array",
    ),
    AccumulatorTestCase(
        "bson_timestamp",
        docs=[{"v": Timestamp(1, 1)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Timestamp(1, 1)]}],
        msg="$push should preserve Timestamp value in output array",
    ),
    AccumulatorTestCase(
        "bson_objectid",
        docs=[{"v": ObjectId("507f1f77bcf86cd799439011")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [ObjectId("507f1f77bcf86cd799439011")]}],
        msg="$push should preserve ObjectId value in output array",
    ),
    AccumulatorTestCase(
        "bson_binary",
        docs=[{"v": Binary(b"\x01\x02\x03")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Binary(b"\x01\x02\x03")]}],
        msg="$push should preserve Binary value in output array",
    ),
    AccumulatorTestCase(
        "bson_regex",
        docs=[{"v": Regex("abc", "i")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Regex("abc", "i")]}],
        msg="$push should preserve Regex value in output array",
    ),
    AccumulatorTestCase(
        "bson_code",
        docs=[{"v": Code("function(){}")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Code("function(){}")]}],
        msg="$push should preserve Code value in output array",
    ),
    AccumulatorTestCase(
        "bson_minkey",
        docs=[{"v": MinKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [MinKey()]}],
        msg="$push should preserve MinKey value in output array",
    ),
    AccumulatorTestCase(
        "bson_maxkey",
        docs=[{"v": MaxKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [MaxKey()]}],
        msg="$push should preserve MaxKey value in output array",
    ),
    AccumulatorTestCase(
        "bson_null",
        docs=[{"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [None]}],
        msg="$push should preserve null value in output array",
    ),
    AccumulatorTestCase(
        "bson_object",
        docs=[{"v": {"a": 1, "b": 2}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [{"a": 1, "b": 2}]}],
        msg="$push should preserve embedded object in output array",
    ),
    AccumulatorTestCase(
        "bson_empty_object",
        docs=[{"v": {}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [{}]}],
        msg="$push should preserve empty object in output array",
    ),
    AccumulatorTestCase(
        "bson_array",
        docs=[{"v": [1, 2, 3]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [[1, 2, 3]]}],
        msg="$push should preserve array value as nested array in output",
    ),
    AccumulatorTestCase(
        "bson_empty_array",
        docs=[{"v": []}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [[]]}],
        msg="$push should preserve empty array in output array",
    ),
    AccumulatorTestCase(
        "bson_mixed_types",
        docs=[
            {"v": 1, "s": 1},
            {"v": "hello", "s": 2},
            {"v": True, "s": 3},
            {"v": None, "s": 4},
            {"v": [1, 2], "s": 5},
            {"v": {"a": 1}, "s": 6},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, "hello", True, None, [1, 2], {"a": 1}]}],
        msg="$push should preserve all mixed BSON types in correct order",
    ),
    AccumulatorTestCase(
        "bson_all_numeric_types",
        docs=[
            {"v": 1, "s": 1},
            {"v": Int64(2), "s": 2},
            {"v": 3.0, "s": 3},
            {"v": Decimal128("4"), "s": 4},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, Int64(2), 3.0, Decimal128("4")]}],
        msg="$push should preserve all numeric types without promotion or normalization",
    ),
]

# Property [Order Dependence]: the order of elements in the $push output array
# matches the order of documents entering the $group stage.
PUSH_ORDER_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "order_ascending",
        docs=[{"v": 30}, {"v": 10}, {"v": 20}],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [10, 20, 30]}],
        msg="$push should produce ascending order when preceded by ascending $sort",
    ),
    AccumulatorTestCase(
        "order_descending",
        docs=[{"v": 30}, {"v": 10}, {"v": 20}],
        pipeline=[
            {"$sort": {"v": -1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [30, 20, 10]}],
        msg="$push should produce descending order when preceded by descending $sort",
    ),
    AccumulatorTestCase(
        "order_multiple_groups",
        docs=[
            {"cat": "A", "v": 3, "s": 1},
            {"cat": "B", "v": 2, "s": 2},
            {"cat": "A", "v": 1, "s": 3},
            {"cat": "B", "v": 4, "s": 4},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": "$cat", "result": {"$push": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": [1, 3]},
            {"_id": "B", "result": [2, 4]},
        ],
        msg="$push should produce independently ordered arrays for each group",
    ),
    AccumulatorTestCase(
        "order_compound_sort",
        docs=[
            {"cat": "A", "v": 2, "p": 10},
            {"cat": "A", "v": 1, "p": 20},
            {"cat": "A", "v": 1, "p": 10},
        ],
        pipeline=[
            {"$sort": {"v": 1, "p": 1}},
            {"$group": {"_id": "$cat", "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": "A", "result": [1, 1, 2]}],
        msg="$push should respect compound sort order within each group",
    ),
]

# Property [Duplicate Handling]: $push preserves all duplicate values in the
# output array, unlike $addToSet which deduplicates.
PUSH_DUPLICATE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "dup_all_same",
        docs=[{"v": 10}, {"v": 10}, {"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [10, 10, 10]}],
        msg="$push should preserve all duplicate values in the array",
    ),
    AccumulatorTestCase(
        "dup_nulls",
        docs=[{"v": None}, {"v": None}, {"v": None}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [None, None, None]}],
        msg="$push should preserve duplicate null values",
    ),
    AccumulatorTestCase(
        "dup_objects",
        docs=[{"v": {"a": 1}}, {"v": {"a": 1}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [{"a": 1}, {"a": 1}]}],
        msg="$push should preserve duplicate objects in the array",
    ),
    AccumulatorTestCase(
        "dup_order_preserved",
        docs=[{"v": 10, "s": 1}, {"v": 20, "s": 2}, {"v": 10, "s": 3}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [10, 20, 10]}],
        msg="$push should preserve order of duplicates when sorted",
    ),
]

# Property [Special Numeric Value Preservation]: $push preserves NaN,
# Infinity, and negative zero without normalization.
PUSH_SPECIAL_NUMERIC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "special_float_nan",
        docs=[{"v": FLOAT_NAN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [pytest.approx(math.nan, nan_ok=True)]}],
        msg="$push should preserve float NaN in output array",
    ),
    AccumulatorTestCase(
        "special_decimal128_nan",
        docs=[{"v": DECIMAL128_NAN}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [DECIMAL128_NAN]}],
        msg="$push should preserve Decimal128 NaN in output array",
    ),
    AccumulatorTestCase(
        "special_nan_with_finite",
        docs=[{"v": FLOAT_NAN, "s": 1}, {"v": 5.0, "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [pytest.approx(math.nan, nan_ok=True), 5.0]}],
        msg="$push should preserve NaN alongside finite values in correct position",
    ),
    AccumulatorTestCase(
        "special_float_inf",
        docs=[{"v": FLOAT_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [FLOAT_INFINITY]}],
        msg="$push should preserve float Infinity in output array",
    ),
    AccumulatorTestCase(
        "special_float_neg_inf",
        docs=[{"v": FLOAT_NEGATIVE_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [FLOAT_NEGATIVE_INFINITY]}],
        msg="$push should preserve float -Infinity in output array",
    ),
    AccumulatorTestCase(
        "special_decimal128_inf",
        docs=[{"v": DECIMAL128_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [DECIMAL128_INFINITY]}],
        msg="$push should preserve Decimal128 Infinity in output array",
    ),
    AccumulatorTestCase(
        "special_decimal128_neg_inf",
        docs=[{"v": DECIMAL128_NEGATIVE_INFINITY}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [DECIMAL128_NEGATIVE_INFINITY]}],
        msg="$push should preserve Decimal128 -Infinity in output array",
    ),
    AccumulatorTestCase(
        "special_negative_zero",
        docs=[{"v": -0.0}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 0,
                    "result": {"$map": {"input": "$result", "in": {"$toString": "$$this"}}},
                }
            },
        ],
        expected=[{"result": ["-0"]}],
        msg="$push should preserve double -0.0 in output array",
    ),
    AccumulatorTestCase(
        "special_decimal128_neg_zero",
        docs=[{"v": Decimal128("-0")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 0,
                    "result": {"$map": {"input": "$result", "in": {"$toString": "$$this"}}},
                }
            },
        ],
        expected=[{"result": ["-0"]}],
        msg="$push should preserve Decimal128 -0 in output array",
    ),
]

# Property [Type Preservation]: $push preserves the exact BSON type of each
# collected value without coercing numerically equivalent values.
PUSH_TYPE_PRESERVATION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "type_int32_vs_int64",
        docs=[{"v": 1, "s": 1}, {"v": Int64(1), "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 0,
                    "types": {"$map": {"input": "$result", "in": {"$type": "$$this"}}},
                }
            },
        ],
        expected=[{"types": ["int", "long"]}],
        msg="$push should preserve distinct types for int32(1) and Int64(1)",
    ),
    AccumulatorTestCase(
        "type_int32_vs_double",
        docs=[{"v": 0, "s": 1}, {"v": 0.0, "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 0,
                    "types": {"$map": {"input": "$result", "in": {"$type": "$$this"}}},
                }
            },
        ],
        expected=[{"types": ["int", "double"]}],
        msg="$push should preserve distinct types for int32(0) and double(0.0)",
    ),
    AccumulatorTestCase(
        "type_bool_vs_int",
        docs=[{"v": False, "s": 1}, {"v": 0, "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 0,
                    "types": {"$map": {"input": "$result", "in": {"$type": "$$this"}}},
                }
            },
        ],
        expected=[{"types": ["bool", "int"]}],
        msg="$push should preserve distinct types for false and int32(0)",
    ),
    AccumulatorTestCase(
        "type_string_vs_null",
        docs=[{"v": "", "s": 1}, {"v": None, "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 0,
                    "types": {"$map": {"input": "$result", "in": {"$type": "$$this"}}},
                }
            },
        ],
        expected=[{"types": ["string", "null"]}],
        msg="$push should preserve distinct types for empty string and null",
    ),
    AccumulatorTestCase(
        "type_all_numerics_preserved",
        docs=[
            {"v": 1, "s": 1},
            {"v": Int64(1), "s": 2},
            {"v": 1.0, "s": 3},
            {"v": Decimal128("1"), "s": 4},
        ],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {
                "$project": {
                    "_id": 0,
                    "types": {"$map": {"input": "$result", "in": {"$type": "$$this"}}},
                }
            },
        ],
        expected=[{"types": ["int", "long", "double", "decimal"]}],
        msg="$push should preserve all four numeric types without normalization",
    ),
]

# Property [Nested Array and Document Handling]: $push collects array and
# document values as-is, creating nested structures.
PUSH_NESTED_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "nested_arrays",
        docs=[{"v": [1, 2], "s": 1}, {"v": [3, 4], "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [[1, 2], [3, 4]]}],
        msg="$push should nest array values inside the result array",
    ),
    AccumulatorTestCase(
        "nested_empty_arrays",
        docs=[{"v": [], "s": 1}, {"v": [], "s": 2}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [[], []]}],
        msg="$push should preserve empty arrays as nested elements",
    ),
    AccumulatorTestCase(
        "nested_mixed_arrays_and_scalars",
        docs=[{"v": [1, 2], "s": 1}, {"v": 3, "s": 2}, {"v": [4], "s": 3}],
        pipeline=[
            {"$sort": {"s": 1}},
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [[1, 2], 3, [4]]}],
        msg="$push should handle mix of arrays and scalars in output",
    ),
    AccumulatorTestCase(
        "nested_deep_objects",
        docs=[{"v": {"a": {"b": {"c": 1}}}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
        ],
        expected=[{"_id": None, "result": [{"a": {"b": {"c": 1}}}]}],
        msg="$push should preserve deeply nested objects exactly",
    ),
    AccumulatorTestCase(
        "nested_field_path",
        docs=[{"a": {"b": {"c": 10}}}, {"a": {"b": {"c": 20}}}],
        pipeline=[
            {"$sort": {"a.b.c": 1}},
            {"$group": {"_id": None, "result": {"$push": "$a.b.c"}}},
        ],
        expected=[{"_id": None, "result": [10, 20]}],
        msg="$push should resolve nested field paths to collect leaf values",
    ),
]

# Property [Grouping Behavior]: each group produces an independent array, and
# groups with varying sizes produce arrays of corresponding lengths.
PUSH_GROUPING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "group_multiple",
        docs=[
            {"cat": "A", "v": 1},
            {"cat": "B", "v": 2},
            {"cat": "A", "v": 3},
            {"cat": "B", "v": 4},
            {"cat": "B", "v": 5},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": "$cat", "result": {"$push": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": [1, 3]},
            {"_id": "B", "result": [2, 4, 5]},
        ],
        msg="$push should produce independent arrays for each group",
    ),
    AccumulatorTestCase(
        "group_single_doc_per_group",
        docs=[{"cat": "A", "v": 10}, {"cat": "B", "v": 20}, {"cat": "C", "v": 30}],
        pipeline=[
            {"$group": {"_id": "$cat", "result": {"$push": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": [10]},
            {"_id": "B", "result": [20]},
            {"_id": "C", "result": [30]},
        ],
        msg="$push should produce single-element arrays for single-document groups",
    ),
    AccumulatorTestCase(
        "group_large",
        docs=[{"v": 1} for _ in range(10_000)],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$v"}}},
            {"$project": {"_id": 0, "count": {"$size": "$result"}}},
        ],
        expected=[{"count": 10_000}],
        msg="$push should collect exactly 10000 elements for a 10000-document group",
    ),
]

# Property [Field Path Resolution]: $push correctly resolves simple, nested,
# and non-existent field paths.
PUSH_FIELD_PATH_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "field_simple",
        docs=[{"a": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$a"}}},
        ],
        expected=[{"_id": None, "result": [1]}],
        msg="$push should resolve simple field path",
    ),
    AccumulatorTestCase(
        "field_nested",
        docs=[{"a": {"b": 1}}, {"a": {"b": 2}}],
        pipeline=[
            {"$sort": {"a.b": 1}},
            {"$group": {"_id": None, "result": {"$push": "$a.b"}}},
        ],
        expected=[{"_id": None, "result": [1, 2]}],
        msg="$push should resolve nested field path",
    ),
    AccumulatorTestCase(
        "field_nonexistent",
        docs=[{"a": 1}, {"a": 2}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$push": "$nonexistent"}}},
        ],
        expected=[{"_id": None, "result": []}],
        msg="$push should produce empty array for non-existent field path",
    ),
]

# Property [System Variables]: $push accepts system variables as its expression
# argument; $$ROOT collects entire documents.
PUSH_SYSTEM_VARIABLE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "sysvar_root",
        docs=[{"a": 1}, {"a": 2}],
        pipeline=[
            {"$sort": {"a": 1}},
            {"$group": {"_id": None, "result": {"$push": "$$ROOT"}}},
            {"$project": {"_id": 0, "result": {"$map": {"input": "$result", "in": "$$this.a"}}}},
        ],
        expected=[{"result": [1, 2]}],
        msg="$push with $$ROOT should collect entire documents",
    ),
    AccumulatorTestCase(
        "sysvar_current",
        docs=[{"a": 1}, {"a": 2}],
        pipeline=[
            {"$sort": {"a": 1}},
            {"$group": {"_id": None, "result": {"$push": "$$CURRENT"}}},
            {"$project": {"_id": 0, "result": {"$map": {"input": "$result", "in": "$$this.a"}}}},
        ],
        expected=[{"result": [1, 2]}],
        msg="$push with $$CURRENT should collect entire documents like $$ROOT",
    ),
]

PUSH_CORE_SUCCESS_TESTS = (
    PUSH_BSON_TYPE_TESTS
    + PUSH_ORDER_TESTS
    + PUSH_DUPLICATE_TESTS
    + PUSH_SPECIAL_NUMERIC_TESTS
    + PUSH_TYPE_PRESERVATION_TESTS
    + PUSH_NESTED_TESTS
    + PUSH_GROUPING_TESTS
    + PUSH_FIELD_PATH_TESTS
    + PUSH_SYSTEM_VARIABLE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(PUSH_CORE_SUCCESS_TESTS))
def test_push_core(collection, test_case: AccumulatorTestCase):
    """Test $push core behavior."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
