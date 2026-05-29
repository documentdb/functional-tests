"""Tests for $avg accumulator composed with sibling accumulators in the same $group."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Avg with Sum]: $avg and $sum coexist in the same $group and
# independently compute the mean and the total.  $avg always returns double
# for integer inputs; $sum returns int32 when all inputs are int32.
AVG_WITH_SUM_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "avg_sum_single_group",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a", "v": 30},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "mean": {"$avg": "$v"},
                    "total": {"$sum": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "mean": 20.0, "total": 60}],
        msg="$avg and $sum should independently produce mean and total",
    ),
    AccumulatorTestCase(
        "avg_sum_multiple_groups",
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
                    "mean": {"$avg": "$v"},
                    "total": {"$sum": "$v"},
                }
            }
        ],
        expected=[
            {"_id": "a", "mean": 15.0, "total": 30},
            {"_id": "b", "mean": 15.0, "total": 45},
        ],
        msg="$avg and $sum should produce correct results across multiple groups",
    ),
    AccumulatorTestCase(
        "avg_sum_null_handling_diverges",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "mean": {"$avg": "$v"},
                    "total": {"$sum": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "mean": 10.0, "total": 10}],
        msg="$avg and $sum should both ignore null (avg=10.0 from one value, sum=10)",
    ),
    AccumulatorTestCase(
        "avg_sum_all_null_diverges",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": None},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "mean": {"$avg": "$v"},
                    "total": {"$sum": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "mean": None, "total": 0}],
        msg="$avg returns null but $sum returns 0 when all values are null",
    ),
]

# Property [Avg with Count]: $avg of a field and $sum with constant 1 (count
# pattern) coexist, independently computing a mean and a document count.
AVG_WITH_COUNT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "avg_count_basic",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "b", "v": 5},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "mean": {"$avg": "$v"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[
            {"_id": "a", "mean": 15.0, "count": 2},
            {"_id": "b", "mean": 5.0, "count": 1},
        ],
        msg="$avg of field and $sum(1) should independently compute mean and count",
    ),
    AccumulatorTestCase(
        "avg_count_non_numeric_ignored_but_counted",
        docs=[
            {"cat": "a", "v": "hello"},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": True},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "mean": {"$avg": "$v"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[{"_id": "a", "mean": 10.0, "count": 3}],
        msg="$avg ignores non-numeric values but $sum(1) counts all documents",
    ),
]

# Property [Avg with Min/Max]: $avg, $min, and $max coexist in the same
# $group, each independently computing the mean, minimum, and maximum.
AVG_WITH_MIN_MAX_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "avg_min_max_basic",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "mean": {"$avg": "$v"},
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "mean": 20.0, "lo": 10, "hi": 30}],
        msg="$avg, $min, and $max should independently compute mean, min, and max",
    ),
    AccumulatorTestCase(
        "avg_min_max_mixed_types",
        docs=[
            {"cat": "a", "v": 5},
            {"cat": "a", "v": Int64(100)},
            {"cat": "a", "v": 2.5},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "mean": {"$avg": "$v"},
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "mean": 35.833333333333336, "lo": 2.5, "hi": Int64(100)}],
        msg="$avg should return double while $min/$max preserve original types",
    ),
]

# Property [Avg with First/Last]: $avg computes the mean while $first/$last
# pick positional values from the group.  A preceding $sort establishes order
# for $first and $last; $avg is order-independent.
AVG_WITH_FIRST_LAST_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "avg_first_last_with_sort",
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
                    "mean": {"$avg": "$v"},
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "mean": 20.0, "first_v": 10, "last_v": 30}],
        msg="$avg should compute mean while $first/$last pick sorted extremes",
    ),
]

# Property [Avg with Push/AddToSet]: $avg computes the mean while $push
# collects all values and $addToSet collects unique values.
AVG_WITH_PUSH_ADDTOSET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "avg_push_addtoset",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a", "v": 10},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "mean": {"$avg": "$v"},
                    "all_vals": {"$push": "$v"},
                    "unique_vals": {"$addToSet": "$v"},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "mean": 13.333333333333334,
                "all_vals": [10, 10, 20],
                "unique_vals": [10, 20],
            },
        ],
        msg="$avg computes mean while $push keeps all values and $addToSet keeps unique values",
    ),
]

# Property [Avg with MergeObjects]: $avg computes the mean while
# $mergeObjects combines per-document metadata into a single object.
AVG_WITH_MERGE_OBJECTS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "avg_merge_objects",
        docs=[
            {"cat": "a", "v": 10, "meta": {"src": "x"}},
            {"cat": "a", "v": 20, "meta": {"quality": "high"}},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "mean": {"$avg": "$v"},
                    "merged": {"$mergeObjects": "$meta"},
                }
            }
        ],
        expected=[
            {"_id": "a", "mean": 15.0, "merged": {"src": "x", "quality": "high"}},
        ],
        msg="$avg computes mean while $mergeObjects combines metadata objects",
    ),
]

# Property [Multiple Avg Expressions]: multiple $avg accumulators in the same
# $group independently average different fields or expressions.
MULTIPLE_AVG_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "multiple_avg_different_fields",
        docs=[
            {"cat": "a", "price": 100, "qty": 2},
            {"cat": "a", "price": 200, "qty": 3},
            {"cat": "b", "price": 50, "qty": 10},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "avg_price": {"$avg": "$price"},
                    "avg_qty": {"$avg": "$qty"},
                }
            }
        ],
        expected=[
            {"_id": "a", "avg_price": 150.0, "avg_qty": 2.5},
            {"_id": "b", "avg_price": 50.0, "avg_qty": 10.0},
        ],
        msg="Multiple $avg accumulators should independently average different fields",
    ),
    AccumulatorTestCase(
        "multiple_avg_different_expressions",
        docs=[
            {"cat": "a", "price": 100, "qty": 2, "revenue": 200},
            {"cat": "a", "price": 200, "qty": 3, "revenue": 600},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "avg_price": {"$avg": "$price"},
                    "avg_revenue": {"$avg": "$revenue"},
                }
            }
        ],
        expected=[{"_id": "a", "avg_price": 150.0, "avg_revenue": 400.0}],
        msg="Multiple $avg accumulators should independently average different fields",
    ),
]

# Property [Avg Type Promotion with Sibling]: $avg promoting to Decimal128
# does not interfere with sibling accumulators that return simpler types.
AVG_TYPE_PROMOTION_WITH_SIBLING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "avg_decimal128_with_int_count",
        docs=[
            {"cat": "a", "v": Decimal128("1.5")},
            {"cat": "a", "v": Decimal128("2.5")},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "mean": {"$avg": "$v"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[{"_id": "a", "mean": Decimal128("2.0"), "count": 2}],
        msg="$avg promoting to Decimal128 should not affect sibling $sum(1) returning int32",
    ),
]

AVG_INTEGRATION_TESTS = (
    AVG_WITH_SUM_TESTS
    + AVG_WITH_COUNT_TESTS
    + AVG_WITH_MIN_MAX_TESTS
    + AVG_WITH_FIRST_LAST_TESTS
    + AVG_WITH_PUSH_ADDTOSET_TESTS
    + AVG_WITH_MERGE_OBJECTS_TESTS
    + MULTIPLE_AVG_TESTS
    + AVG_TYPE_PROMOTION_WITH_SIBLING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(AVG_INTEGRATION_TESTS))
def test_accumulators_avg_integration(collection, test_case: AccumulatorTestCase):
    """Test $avg accumulator composed with sibling accumulators in the same $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
        ignore_order_in=["unique_vals"],
    )
