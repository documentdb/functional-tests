"""Aggregation $group stage tests - accumulator type behavior."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import SON, Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_FROM_INT64_MAX,
    DOUBLE_MAX,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    INT32_MAX,
    INT64_MAX,
)

# Property [$sum Return Type Promotion]: $sum promotes the result type
# according to the numeric type hierarchy (int32 < Int64 < double <
# Decimal128), overflows int32 to Int64 and Int64 to double, produces
# infinity on double overflow, and ignores booleans and non-numeric types.
GROUP_SUM_TYPE_PROMOTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="sum_int32_int32_returns_int",
        docs=[{"_id": 1, "v": 5}, {"_id": 2, "v": 10}],
        pipeline=[
            {"$group": {"_id": None, "r": {"$sum": "$v"}}},
            {"$project": {"r": 1, "t": {"$type": "$r"}}},
        ],
        expected=[{"_id": None, "r": 15, "t": "int"}],
        msg="int32 + int32 should produce int32",
    ),
    StageTestCase(
        id="sum_int32_int64_returns_long",
        docs=[{"_id": 1, "v": 5}, {"_id": 2, "v": Int64(10)}],
        pipeline=[
            {"$group": {"_id": None, "r": {"$sum": "$v"}}},
            {"$project": {"r": 1, "t": {"$type": "$r"}}},
        ],
        expected=[{"_id": None, "r": Int64(15), "t": "long"}],
        msg="int32 + Int64 should produce Int64",
    ),
    StageTestCase(
        id="sum_int32_double_returns_double",
        docs=[{"_id": 1, "v": 5}, {"_id": 2, "v": 10.5}],
        pipeline=[
            {"$group": {"_id": None, "r": {"$sum": "$v"}}},
            {"$project": {"r": 1, "t": {"$type": "$r"}}},
        ],
        expected=[{"_id": None, "r": 15.5, "t": "double"}],
        msg="int32 + double should produce double",
    ),
    StageTestCase(
        id="sum_int32_decimal128_returns_decimal",
        docs=[{"_id": 1, "v": 5}, {"_id": 2, "v": Decimal128("10")}],
        pipeline=[
            {"$group": {"_id": None, "r": {"$sum": "$v"}}},
            {"$project": {"r": 1, "t": {"$type": "$r"}}},
        ],
        expected=[{"_id": None, "r": Decimal128("15"), "t": "decimal"}],
        msg="int32 + Decimal128 should produce Decimal128",
    ),
    StageTestCase(
        id="sum_int64_double_returns_double",
        docs=[{"_id": 1, "v": Int64(5)}, {"_id": 2, "v": 10.5}],
        pipeline=[
            {"$group": {"_id": None, "r": {"$sum": "$v"}}},
            {"$project": {"r": 1, "t": {"$type": "$r"}}},
        ],
        expected=[{"_id": None, "r": 15.5, "t": "double"}],
        msg="Int64 + double should produce double",
    ),
    StageTestCase(
        id="sum_int64_decimal128_returns_decimal",
        docs=[{"_id": 1, "v": Int64(5)}, {"_id": 2, "v": Decimal128("10")}],
        pipeline=[
            {"$group": {"_id": None, "r": {"$sum": "$v"}}},
            {"$project": {"r": 1, "t": {"$type": "$r"}}},
        ],
        expected=[{"_id": None, "r": Decimal128("15"), "t": "decimal"}],
        msg="Int64 + Decimal128 should produce Decimal128",
    ),
    StageTestCase(
        id="sum_double_double_returns_double",
        docs=[{"_id": 1, "v": 1.5}, {"_id": 2, "v": 2.5}],
        pipeline=[
            {"$group": {"_id": None, "r": {"$sum": "$v"}}},
            {"$project": {"r": 1, "t": {"$type": "$r"}}},
        ],
        expected=[{"_id": None, "r": 4.0, "t": "double"}],
        msg="double + double should produce double",
    ),
    StageTestCase(
        id="sum_decimal128_decimal128_returns_decimal",
        docs=[
            {"_id": 1, "v": DECIMAL128_ONE_AND_HALF},
            {"_id": 2, "v": DECIMAL128_TWO_AND_HALF},
        ],
        pipeline=[
            {"$group": {"_id": None, "r": {"$sum": "$v"}}},
            {"$project": {"r": 1, "t": {"$type": "$r"}}},
        ],
        expected=[{"_id": None, "r": Decimal128("4.0"), "t": "decimal"}],
        msg="Decimal128 + Decimal128 should produce Decimal128",
    ),
    StageTestCase(
        id="sum_int32_overflow_promotes_to_int64",
        docs=[{"_id": 1, "v": INT32_MAX}, {"_id": 2, "v": 1}],
        pipeline=[
            {"$group": {"_id": None, "r": {"$sum": "$v"}}},
            {"$project": {"r": 1, "t": {"$type": "$r"}}},
        ],
        expected=[{"_id": None, "r": Int64(INT32_MAX + 1), "t": "long"}],
        msg="int32 overflow should promote to Int64",
    ),
    StageTestCase(
        id="sum_int64_overflow_promotes_to_double",
        docs=[{"_id": 1, "v": INT64_MAX}, {"_id": 2, "v": Int64(1)}],
        pipeline=[
            {"$group": {"_id": None, "r": {"$sum": "$v"}}},
            {"$project": {"r": 1, "t": {"$type": "$r"}}},
        ],
        expected=[{"_id": None, "r": DOUBLE_FROM_INT64_MAX, "t": "double"}],
        msg="Int64 overflow should promote to double, not Decimal128",
    ),
    StageTestCase(
        id="sum_double_overflow_produces_infinity",
        docs=[{"_id": 1, "v": DOUBLE_MAX}, {"_id": 2, "v": DOUBLE_MAX}],
        pipeline=[
            {"$group": {"_id": None, "r": {"$sum": "$v"}}},
            {"$project": {"r": 1, "t": {"$type": "$r"}}},
        ],
        expected=[{"_id": None, "r": FLOAT_INFINITY, "t": "double"}],
        msg="double overflow (DBL_MAX + DBL_MAX) should produce infinity",
    ),
    StageTestCase(
        id="sum_inf_plus_inf_produces_infinity",
        docs=[{"_id": 1, "v": FLOAT_INFINITY}, {"_id": 2, "v": FLOAT_INFINITY}],
        pipeline=[{"$group": {"_id": None, "r": {"$sum": "$v"}}}],
        expected=[{"_id": None, "r": FLOAT_INFINITY}],
        msg="inf + inf should produce infinity",
    ),
    StageTestCase(
        id="sum_ignores_booleans",
        docs=[
            {"_id": 1, "v": True},
            {"_id": 2, "v": False},
            {"_id": 3, "v": 10},
        ],
        pipeline=[{"$group": {"_id": None, "r": {"$sum": "$v"}}}],
        expected=[{"_id": None, "r": 10}],
        msg="$sum should ignore boolean values",
    ),
    StageTestCase(
        id="sum_ignores_literal_boolean",
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$group": {"_id": None, "r": {"$sum": True}}}],
        expected=[{"_id": None, "r": 0}],
        msg="$sum should ignore literal boolean values (contribute 0)",
    ),
    StageTestCase(
        id="sum_ignores_non_numeric_types",
        docs=[
            {"_id": 1, "v": "hello"},
            {"_id": 2, "v": [1, 2]},
            {"_id": 3, "v": {"a": 1}},
            {"_id": 4, "v": 10},
        ],
        pipeline=[{"$group": {"_id": None, "r": {"$sum": "$v"}}}],
        expected=[{"_id": None, "r": 10}],
        msg="$sum should ignore non-numeric types (string, array, object)",
    ),
    StageTestCase(
        id="sum_all_booleans_produces_zero",
        docs=[{"_id": 1, "v": True}, {"_id": 2, "v": False}],
        pipeline=[{"$group": {"_id": None, "r": {"$sum": "$v"}}}],
        expected=[{"_id": None, "r": 0}],
        msg="$sum with all-boolean input should produce 0",
    ),
]

# Property [$avg Return Type]: $avg of integer inputs (int32 or Int64)
# produces a double result, while $avg of Decimal128 inputs produces a
# Decimal128 result.
GROUP_AVG_RETURN_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="avg_int32_returns_double",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[
            {"$group": {"_id": None, "r": {"$avg": "$v"}}},
            {"$project": {"r": 1, "t": {"$type": "$r"}}},
        ],
        expected=[{"_id": None, "r": 15.0, "t": "double"}],
        msg="$avg of int32 inputs should produce a double result",
    ),
    StageTestCase(
        id="avg_int64_returns_double",
        docs=[{"_id": 1, "v": Int64(10)}, {"_id": 2, "v": Int64(20)}],
        pipeline=[
            {"$group": {"_id": None, "r": {"$avg": "$v"}}},
            {"$project": {"r": 1, "t": {"$type": "$r"}}},
        ],
        expected=[{"_id": None, "r": 15.0, "t": "double"}],
        msg="$avg of Int64 inputs should produce a double result",
    ),
    StageTestCase(
        id="avg_decimal128_returns_decimal",
        docs=[{"_id": 1, "v": Decimal128("10")}, {"_id": 2, "v": Decimal128("20")}],
        pipeline=[
            {"$group": {"_id": None, "r": {"$avg": "$v"}}},
            {"$project": {"r": 1, "t": {"$type": "$r"}}},
        ],
        expected=[{"_id": None, "r": Decimal128("15"), "t": "decimal"}],
        msg="$avg of Decimal128 inputs should produce a Decimal128 result",
    ),
]

# Property [$addToSet Deduplication Rules]: $addToSet deduplicates numeric
# equivalents (int32, Int64, double, Decimal128), deduplicates -0.0 and 0.0,
# does not deduplicate booleans with numeric equivalents, and treats object
# key order and array element order as significant for deduplication.
GROUP_ADDTOSET_DEDUP_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="addtoset_numeric_equivalents_dedup",
        docs=[
            {"_id": 1, "v": 1},
            {"_id": 2, "v": Int64(1)},
            {"_id": 3, "v": 1.0},
            {"_id": 4, "v": Decimal128("1")},
        ],
        pipeline=[
            {"$group": {"_id": None, "r": {"$addToSet": "$v"}}},
        ],
        expected=[{"_id": None, "r": [1]}],
        msg=(
            "Numeric equivalents (int32, Int64, double, Decimal128) should"
            " deduplicate to one entry"
        ),
    ),
    StageTestCase(
        id="addtoset_bool_not_dedup_with_numeric",
        docs=[
            {"_id": 1, "v": 1},
            {"_id": 2, "v": True},
            {"_id": 3, "v": 0},
            {"_id": 4, "v": False},
        ],
        pipeline=[
            {"$group": {"_id": None, "r": {"$addToSet": "$v"}}},
            {"$project": {"r": {"$sortArray": {"input": "$r", "sortBy": 1}}}},
        ],
        expected=[{"_id": None, "r": [0, 1, False, True]}],
        msg="Boolean values should not be deduplicated with numeric equivalents",
    ),
    StageTestCase(
        id="addtoset_negative_zero_and_zero_dedup",
        docs=[
            {"_id": 1, "v": DOUBLE_NEGATIVE_ZERO},
            {"_id": 2, "v": DOUBLE_ZERO},
            {"_id": 3, "v": 0},
        ],
        pipeline=[
            {"$group": {"_id": None, "r": {"$addToSet": "$v"}}},
        ],
        expected=[{"_id": None, "r": [DOUBLE_NEGATIVE_ZERO]}],
        msg="-0.0 and 0.0 should be deduplicated",
    ),
    StageTestCase(
        id="addtoset_object_key_order_matters",
        docs=[
            {"_id": 1, "v": SON([("a", 1), ("b", 2)])},
            {"_id": 2, "v": SON([("b", 2), ("a", 1)])},
        ],
        pipeline=[
            {"$group": {"_id": None, "r": {"$addToSet": "$v"}}},
            {"$project": {"r": {"$sortArray": {"input": "$r", "sortBy": 1}}}},
        ],
        expected=[{"_id": None, "r": [{"a": 1, "b": 2}, {"b": 2, "a": 1}]}],
        msg="Object key order should matter for $addToSet deduplication",
    ),
    StageTestCase(
        id="addtoset_array_element_order_matters",
        docs=[
            {"_id": 1, "v": [1, 2]},
            {"_id": 2, "v": [2, 1]},
        ],
        pipeline=[
            {"$group": {"_id": None, "r": {"$addToSet": "$v"}}},
            {"$project": {"r": {"$sortArray": {"input": "$r", "sortBy": 1}}}},
        ],
        expected=[{"_id": None, "r": [[1, 2], [2, 1]]}],
        msg="Array element order should matter for $addToSet deduplication",
    ),
    StageTestCase(
        id="addtoset_output_order_nondeterministic",
        docs=[{"_id": i, "v": f"val_{i}"} for i in range(20)],
        pipeline=[
            {"$group": {"_id": None, "r": {"$addToSet": "$v"}}},
            {"$project": {"count": {"$size": "$r"}}},
        ],
        expected=[{"_id": None, "count": 20}],
        msg="$addToSet output order is non-deterministic; verify set completeness only",
    ),
]

# Property [$min/$max BSON Comparison Order]: $min and $max follow BSON
# comparison order for mixed types (MinKey < numbers < string < object <
# Binary < ObjectId < bool < datetime < Timestamp < Regex < Code <
# CodeWithScope < MaxKey), and for booleans False < True.
GROUP_MIN_MAX_MIXED_TYPES_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="min_max_bson_order_all_types",
        docs=[
            {"_id": 1, "v": MinKey()},
            {"_id": 2, "v": 42},
            {"_id": 3, "v": "hello"},
            {"_id": 4, "v": {"a": 1}},
            {"_id": 5, "v": Binary(b"data")},
            {"_id": 6, "v": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": 7, "v": True},
            {"_id": 8, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 9, "v": Timestamp(1, 1)},
            {"_id": 10, "v": Regex("abc", "i")},
            {"_id": 11, "v": Code("function(){}")},
            {"_id": 12, "v": MaxKey()},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "mn": {"$min": "$v"},
                    "mx": {"$max": "$v"},
                }
            }
        ],
        expected=[{"_id": None, "mn": MinKey(), "mx": MaxKey()}],
        msg=(
            "$min should return MinKey and $max should return MaxKey when all"
            " BSON types are present"
        ),
    ),
    StageTestCase(
        id="min_minkey_less_than_number",
        docs=[{"_id": 1, "v": MinKey()}, {"_id": 2, "v": 42}],
        pipeline=[{"$group": {"_id": None, "mn": {"$min": "$v"}, "mx": {"$max": "$v"}}}],
        expected=[{"_id": None, "mn": MinKey(), "mx": 42}],
        msg="MinKey should compare less than numbers in BSON order",
    ),
    StageTestCase(
        id="min_number_less_than_string",
        docs=[{"_id": 1, "v": 42}, {"_id": 2, "v": "hello"}],
        pipeline=[{"$group": {"_id": None, "mn": {"$min": "$v"}, "mx": {"$max": "$v"}}}],
        expected=[{"_id": None, "mn": 42, "mx": "hello"}],
        msg="Numbers should compare less than strings in BSON order",
    ),
    StageTestCase(
        id="min_string_less_than_object",
        docs=[{"_id": 1, "v": "hello"}, {"_id": 2, "v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "mn": {"$min": "$v"}, "mx": {"$max": "$v"}}}],
        expected=[{"_id": None, "mn": "hello", "mx": {"a": 1}}],
        msg="Strings should compare less than objects in BSON order",
    ),
    StageTestCase(
        id="min_object_less_than_binary",
        docs=[{"_id": 1, "v": {"a": 1}}, {"_id": 2, "v": Binary(b"data")}],
        pipeline=[{"$group": {"_id": None, "mn": {"$min": "$v"}, "mx": {"$max": "$v"}}}],
        expected=[{"_id": None, "mn": {"a": 1}, "mx": b"data"}],
        msg="Objects should compare less than Binary in BSON order",
    ),
    StageTestCase(
        id="min_binary_less_than_objectid",
        docs=[
            {"_id": 1, "v": Binary(b"data")},
            {"_id": 2, "v": ObjectId("507f1f77bcf86cd799439011")},
        ],
        pipeline=[{"$group": {"_id": None, "mn": {"$min": "$v"}, "mx": {"$max": "$v"}}}],
        expected=[
            {
                "_id": None,
                "mn": b"data",
                "mx": ObjectId("507f1f77bcf86cd799439011"),
            }
        ],
        msg="Binary should compare less than ObjectId in BSON order",
    ),
    StageTestCase(
        id="min_objectid_less_than_bool",
        docs=[
            {"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": 2, "v": True},
        ],
        pipeline=[{"$group": {"_id": None, "mn": {"$min": "$v"}, "mx": {"$max": "$v"}}}],
        expected=[{"_id": None, "mn": ObjectId("507f1f77bcf86cd799439011"), "mx": True}],
        msg="ObjectId should compare less than bool in BSON order",
    ),
    StageTestCase(
        id="min_bool_less_than_datetime",
        docs=[{"_id": 1, "v": True}, {"_id": 2, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$group": {"_id": None, "mn": {"$min": "$v"}, "mx": {"$max": "$v"}}}],
        expected=[{"_id": None, "mn": True, "mx": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        msg="Bool should compare less than datetime in BSON order",
    ),
    StageTestCase(
        id="min_datetime_less_than_timestamp",
        docs=[
            {"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "v": Timestamp(1, 1)},
        ],
        pipeline=[{"$group": {"_id": None, "mn": {"$min": "$v"}, "mx": {"$max": "$v"}}}],
        expected=[
            {"_id": None, "mn": datetime(2024, 1, 1, tzinfo=timezone.utc), "mx": Timestamp(1, 1)}
        ],
        msg="Datetime should compare less than Timestamp in BSON order",
    ),
    StageTestCase(
        id="min_timestamp_less_than_regex",
        docs=[
            {"_id": 1, "v": Timestamp(1, 1)},
            {"_id": 2, "v": Regex("abc", "i")},
        ],
        pipeline=[{"$group": {"_id": None, "mn": {"$min": "$v"}, "mx": {"$max": "$v"}}}],
        expected=[{"_id": None, "mn": Timestamp(1, 1), "mx": Regex("abc", "i")}],
        msg="Timestamp should compare less than Regex in BSON order",
    ),
    StageTestCase(
        id="min_regex_less_than_code",
        docs=[
            {"_id": 1, "v": Regex("abc", "i")},
            {"_id": 2, "v": Code("function(){}")},
        ],
        pipeline=[{"$group": {"_id": None, "mn": {"$min": "$v"}, "mx": {"$max": "$v"}}}],
        expected=[{"_id": None, "mn": Regex("abc", "i"), "mx": Code("function(){}")}],
        msg="Regex should compare less than Code in BSON order",
    ),
    StageTestCase(
        id="min_code_less_than_maxkey",
        docs=[
            {"_id": 1, "v": Code("function(){}")},
            {"_id": 2, "v": MaxKey()},
        ],
        pipeline=[{"$group": {"_id": None, "mn": {"$min": "$v"}, "mx": {"$max": "$v"}}}],
        expected=[
            {
                "_id": None,
                "mn": Code("function(){}"),
                "mx": MaxKey(),
            }
        ],
        msg="Code should compare less than MaxKey in BSON order",
    ),
    StageTestCase(
        id="min_bool_false_less_than_true",
        docs=[{"_id": 1, "v": True}, {"_id": 2, "v": False}],
        pipeline=[{"$group": {"_id": None, "mn": {"$min": "$v"}, "mx": {"$max": "$v"}}}],
        expected=[{"_id": None, "mn": False, "mx": True}],
        msg="For boolean values, False should compare less than True",
    ),
]


GROUP_ACCUMULATOR_TYPE_TESTS = (
    GROUP_SUM_TYPE_PROMOTION_TESTS
    + GROUP_AVG_RETURN_TYPE_TESTS
    + GROUP_ADDTOSET_DEDUP_TESTS
    + GROUP_MIN_MAX_MIXED_TYPES_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_ACCUMULATOR_TYPE_TESTS))
def test_group_accumulator_types(collection, test_case: StageTestCase):
    """Test $group stage - accumulator type behavior."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
    )
