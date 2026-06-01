"""Tests for $min accumulator composed with sibling accumulators in the same $group."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Min with Max]: $min and $max coexist in the same $group and
# independently compute the minimum and maximum.  Both preserve the BSON type
# of the winning value.
MIN_WITH_MAX_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "min_max_single_group",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "lo": 10, "hi": 30}],
        msg="$min and $max should independently compute minimum and maximum",
    ),
    AccumulatorTestCase(
        "min_max_multiple_groups",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "b", "v": 5},
            {"cat": "b", "v": 15},
            {"cat": "b", "v": 25},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            }
        ],
        expected=[
            {"_id": "a", "lo": 10, "hi": 20},
            {"_id": "b", "lo": 5, "hi": 25},
        ],
        msg="$min and $max should produce correct results across multiple groups",
    ),
    AccumulatorTestCase(
        "min_max_mixed_numeric_types",
        docs=[
            {"cat": "a", "v": 5},
            {"cat": "a", "v": Int64(100)},
            {"cat": "a", "v": 2.5},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "lo": 2.5, "hi": Int64(100)}],
        msg="$min and $max should preserve original BSON types of winning values",
    ),
    AccumulatorTestCase(
        "min_max_single_doc",
        docs=[{"cat": "a", "v": 42}],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "lo": 42, "hi": 42}],
        msg="$min and $max should return the same value for a single-document group",
    ),
    AccumulatorTestCase(
        "min_max_null_handling",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": None},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "lo": 10, "hi": 20}],
        msg="$min and $max should both ignore null values",
    ),
    AccumulatorTestCase(
        "min_max_all_null",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": None},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "lo": None, "hi": None}],
        msg="$min and $max should both return null when all values are null",
    ),
]

# Property [Min with Sum]: $min picks the smallest value while $sum computes
# the total.  $sum returns 0 for all-null groups; $min returns null.
MIN_WITH_SUM_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "min_sum_basic",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "total": {"$sum": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "lo": 10, "total": 60}],
        msg="$min and $sum should independently compute minimum and total",
    ),
    AccumulatorTestCase(
        "min_sum_null_diverges",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": None},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "total": {"$sum": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "lo": None, "total": 0}],
        msg="$min returns null but $sum returns 0 when all values are null",
    ),
    AccumulatorTestCase(
        "min_sum_mixed_types",
        docs=[
            {"cat": "a", "v": 5},
            {"cat": "a", "v": Int64(100)},
            {"cat": "a", "v": 2.5},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "total": {"$sum": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "lo": 2.5, "total": 107.5}],
        msg="$min preserves original type while $sum promotes to double",
    ),
]

# Property [Min with Avg]: $min picks the smallest value while $avg computes
# the mean.  $avg always returns double; $min preserves the winning value's
# type.  When all values are null, $min returns null and $avg returns null.
MIN_WITH_AVG_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "min_avg_basic",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a", "v": 30},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "mean": {"$avg": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "lo": 10, "mean": 20.0}],
        msg="$min and $avg should independently compute minimum and mean",
    ),
    AccumulatorTestCase(
        "min_avg_null_handling",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "mean": {"$avg": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "lo": 10, "mean": 10.0}],
        msg="$min and $avg should both ignore null (single non-null value)",
    ),
    AccumulatorTestCase(
        "min_avg_all_null",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": None},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "mean": {"$avg": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "lo": None, "mean": None}],
        msg="$min and $avg should both return null when all values are null",
    ),
]

# Property [Min with First/Last]: $min picks the globally smallest value
# while $first/$last pick positional values.  A preceding $sort establishes
# order for $first and $last; $min is order-independent.
MIN_WITH_FIRST_LAST_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "min_first_last_with_sort",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "lo": 10, "first_v": 10, "last_v": 30}],
        msg="$min should equal $first when sorted ascending; $last gets the max",
    ),
    AccumulatorTestCase(
        "min_first_last_desc_sort",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {"$sort": {"v": -1}},
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "lo": 10, "first_v": 30, "last_v": 10}],
        msg="$min should equal $last when sorted descending; $first gets the max",
    ),
]

# Property [Min with Push/AddToSet]: $min picks the minimum while $push
# collects all values and $addToSet collects unique values.
MIN_WITH_PUSH_ADDTOSET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "min_push_addtoset",
        docs=[
            {"cat": "a", "v": 20},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "all_vals": {"$push": "$v"},
                    "unique_vals": {"$addToSet": "$v"},
                }
            },
        ],
        expected=[
            {"_id": "a", "lo": 10, "all_vals": [10, 20, 20], "unique_vals": [10, 20]},
        ],
        msg="$min picks minimum while $push keeps all values and $addToSet keeps unique values",
    ),
    AccumulatorTestCase(
        "min_push_with_nulls",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 5},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "all_vals": {"$push": "$v"},
                }
            },
        ],
        expected=[
            {"_id": "a", "lo": 5, "all_vals": [None, 5, 10]},
        ],
        msg="$min ignores null but $push includes it in collected values",
    ),
]

# Property [Min with Count]: $min picks the minimum while $count (or $sum(1))
# counts all documents, including those with null values that $min ignores.
MIN_WITH_COUNT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "min_count_basic",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "b", "v": 5},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[
            {"_id": "a", "lo": 10, "count": 2},
            {"_id": "b", "lo": 5, "count": 1},
        ],
        msg="$min and $sum(1) should independently compute minimum and count",
    ),
    AccumulatorTestCase(
        "min_count_null_counted_but_not_min",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": None},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[{"_id": "a", "lo": 10, "count": 3}],
        msg="$min ignores null values but $sum(1) counts all documents",
    ),
]

# Property [Min with MergeObjects]: $min computes the minimum while
# $mergeObjects combines per-document metadata into a single object.
MIN_WITH_MERGE_OBJECTS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "min_merge_objects",
        docs=[
            {"cat": "a", "v": 20, "meta": {"src": "x"}},
            {"cat": "a", "v": 10, "meta": {"quality": "high"}},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "merged": {"$mergeObjects": "$meta"},
                }
            }
        ],
        expected=[
            {"_id": "a", "lo": 10, "merged": {"src": "x", "quality": "high"}},
        ],
        msg="$min computes minimum while $mergeObjects combines metadata objects",
    ),
]

# Property [Multiple Min Expressions]: multiple $min accumulators in the same
# $group independently find the minimum of different fields.
MULTIPLE_MIN_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "multiple_min_different_fields",
        docs=[
            {"cat": "a", "price": 100, "qty": 2},
            {"cat": "a", "price": 200, "qty": 3},
            {"cat": "b", "price": 50, "qty": 10},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "min_price": {"$min": "$price"},
                    "min_qty": {"$min": "$qty"},
                }
            }
        ],
        expected=[
            {"_id": "a", "min_price": 100, "min_qty": 2},
            {"_id": "b", "min_price": 50, "min_qty": 10},
        ],
        msg="Multiple $min accumulators should independently find minimum of different fields",
    ),
    AccumulatorTestCase(
        "min_field_and_expression",
        docs=[
            {"cat": "a", "price": 100, "qty": 2},
            {"cat": "a", "price": 200, "qty": 3},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "min_price": {"$min": "$price"},
                    "min_revenue": {"$min": {"$multiply": ["$price", "$qty"]}},
                }
            }
        ],
        expected=[{"_id": "a", "min_price": 100, "min_revenue": 200}],
        msg="$min should independently find minimum of a field and a computed expression",
    ),
]

# Property [Min Type Preservation with Sibling]: $min preserving Decimal128
# does not interfere with sibling accumulators that return simpler types.
MIN_TYPE_PRESERVATION_WITH_SIBLING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "min_decimal128_with_int_count",
        docs=[
            {"cat": "a", "v": Decimal128("1.5")},
            {"cat": "a", "v": Decimal128("2.5")},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[{"_id": "a", "lo": Decimal128("1.5"), "count": 2}],
        msg="$min preserving Decimal128 should not affect sibling $sum(1) returning int32",
    ),
    AccumulatorTestCase(
        "min_int64_with_double_avg",
        docs=[
            {"cat": "a", "v": Int64(10)},
            {"cat": "a", "v": Int64(20)},
            {"cat": "a", "v": Int64(30)},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "mean": {"$avg": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "lo": Int64(10), "mean": 20.0}],
        msg="$min preserving Int64 should not affect sibling $avg returning double",
    ),
]

# Property [Full Pipeline — Min with All Common Siblings]: $min coexists with
# $max, $sum, $avg, $first, $last, and $sum(1) in a single $group, each
# accumulator independently computing its result.
MIN_FULL_PIPELINE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "min_all_siblings",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                    "total": {"$sum": "$v"},
                    "mean": {"$avg": "$v"},
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                    "count": {"$sum": 1},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "lo": 10,
                "hi": 30,
                "total": 60,
                "mean": 20.0,
                "first_v": 10,
                "last_v": 30,
                "count": 3,
            },
        ],
        msg="$min should coexist with $max, $sum, $avg, $first, $last, and count",
    ),
    AccumulatorTestCase(
        "min_all_siblings_multiple_groups",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "b", "v": 100},
            {"cat": "b", "v": 200},
            {"cat": "b", "v": 300},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                    "total": {"$sum": "$v"},
                    "mean": {"$avg": "$v"},
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                    "count": {"$sum": 1},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "lo": 10,
                "hi": 20,
                "total": 30,
                "mean": 15.0,
                "first_v": 10,
                "last_v": 20,
                "count": 2,
            },
            {
                "_id": "b",
                "lo": 100,
                "hi": 300,
                "total": 600,
                "mean": 200.0,
                "first_v": 100,
                "last_v": 300,
                "count": 3,
            },
        ],
        msg="All accumulators should independently compute correct results per group",
    ),
]

MIN_INTEGRATION_TESTS = (
    MIN_WITH_MAX_TESTS
    + MIN_WITH_SUM_TESTS
    + MIN_WITH_AVG_TESTS
    + MIN_WITH_FIRST_LAST_TESTS
    + MIN_WITH_PUSH_ADDTOSET_TESTS
    + MIN_WITH_COUNT_TESTS
    + MIN_WITH_MERGE_OBJECTS_TESTS
    + MULTIPLE_MIN_TESTS
    + MIN_TYPE_PRESERVATION_WITH_SIBLING_TESTS
    + MIN_FULL_PIPELINE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MIN_INTEGRATION_TESTS))
def test_accumulators_min_integration(collection, test_case: AccumulatorTestCase):
    """Test $min accumulator composed with sibling accumulators in the same $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
        ignore_order_in=["unique_vals"],
    )
