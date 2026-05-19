"""Tests for $sum accumulator composed with sibling accumulators in the same $group."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Sum with Avg]: $sum and $avg coexist in the same $group and
# independently compute the total and the mean.  $sum returns int32 when all
# inputs are int32; $avg always returns double.
SUM_WITH_AVG_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "sum_avg_single_group",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a", "v": 30},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "total": {"$sum": "$v"},
                    "mean": {"$avg": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "total": 60, "mean": 20.0}],
        msg="$sum and $avg should independently produce total and mean",
    ),
    AccumulatorTestCase(
        "sum_avg_multiple_groups",
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
                    "total": {"$sum": "$v"},
                    "mean": {"$avg": "$v"},
                }
            }
        ],
        expected=[
            {"_id": "a", "total": 30, "mean": 15.0},
            {"_id": "b", "total": 45, "mean": 15.0},
        ],
        msg="$sum and $avg should produce correct results across multiple groups",
    ),
    AccumulatorTestCase(
        "sum_avg_null_handling_diverges",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "total": {"$sum": "$v"},
                    "mean": {"$avg": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "total": 10, "mean": 10.0}],
        msg="$sum and $avg should both ignore null (sum=10, avg=10.0 from one value)",
    ),
    AccumulatorTestCase(
        "sum_avg_all_null_diverges",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": None},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "total": {"$sum": "$v"},
                    "mean": {"$avg": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "total": 0, "mean": None}],
        msg="$sum returns 0 but $avg returns null when all values are null",
    ),
]

# Property [Sum with Count]: $sum of a field and $sum with constant 1 (count
# pattern) coexist, independently computing a total and a document count.
SUM_WITH_COUNT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "sum_count_basic",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "b", "v": 5},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "total": {"$sum": "$v"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[
            {"_id": "a", "total": 30, "count": 2},
            {"_id": "b", "total": 5, "count": 1},
        ],
        msg="$sum of field and $sum(1) should independently compute total and count",
    ),
    AccumulatorTestCase(
        "sum_count_non_numeric_ignored_but_counted",
        docs=[
            {"cat": "a", "v": "hello"},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": True},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "total": {"$sum": "$v"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[{"_id": "a", "total": 10, "count": 3}],
        msg="$sum ignores non-numeric values but $sum(1) counts all documents",
    ),
]

# Property [Sum with Min/Max]: $sum, $min, and $max coexist in the same
# $group, each independently computing the total, minimum, and maximum.
SUM_WITH_MIN_MAX_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "sum_min_max_basic",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "total": {"$sum": "$v"},
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "total": 60, "lo": 10, "hi": 30}],
        msg="$sum, $min, and $max should independently compute total, min, and max",
    ),
    AccumulatorTestCase(
        "sum_min_max_mixed_types",
        docs=[
            {"cat": "a", "v": 5},
            {"cat": "a", "v": Int64(100)},
            {"cat": "a", "v": 2.5},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "total": {"$sum": "$v"},
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "total": 107.5, "lo": 2.5, "hi": Int64(100)}],
        msg="$sum should promote to double while $min/$max preserve original types",
    ),
]

# Property [Sum with First/Last]: $sum computes the total while $first/$last
# pick positional values from the group.  A preceding $sort establishes order
# for $first and $last; $sum is order-independent.
SUM_WITH_FIRST_LAST_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "sum_first_last_with_sort",
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
                    "total": {"$sum": "$v"},
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "total": 60, "first_v": 10, "last_v": 30}],
        msg="$sum should compute total while $first/$last pick sorted extremes",
    ),
]

# Property [Sum with Push/AddToSet]: $sum computes the total while $push
# collects all values and $addToSet collects unique values.
SUM_WITH_PUSH_ADDTOSET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "sum_push_addtoset",
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
                    "total": {"$sum": "$v"},
                    "all_vals": {"$push": "$v"},
                    "unique_vals": {"$addToSet": "$v"},
                }
            },
        ],
        expected=[
            {"_id": "a", "total": 40, "all_vals": [10, 10, 20], "unique_vals": [10, 20]},
        ],
        msg="$sum computes total while $push keeps all values and $addToSet keeps unique values",
    ),
]

# Property [Sum with MergeObjects]: $sum computes the total while
# $mergeObjects combines per-document metadata into a single object.
SUM_WITH_MERGE_OBJECTS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "sum_merge_objects",
        docs=[
            {"cat": "a", "v": 10, "meta": {"src": "x"}},
            {"cat": "a", "v": 20, "meta": {"quality": "high"}},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "total": {"$sum": "$v"},
                    "merged": {"$mergeObjects": "$meta"},
                }
            }
        ],
        expected=[
            {"_id": "a", "total": 30, "merged": {"src": "x", "quality": "high"}},
        ],
        msg="$sum computes total while $mergeObjects combines metadata objects",
    ),
]

# Property [Multiple Sum Expressions]: multiple $sum accumulators in the same
# $group independently sum different fields or expressions.
MULTIPLE_SUM_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "multiple_sum_different_fields",
        docs=[
            {"cat": "a", "price": 100, "qty": 2},
            {"cat": "a", "price": 200, "qty": 3},
            {"cat": "b", "price": 50, "qty": 10},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "total_price": {"$sum": "$price"},
                    "total_qty": {"$sum": "$qty"},
                }
            }
        ],
        expected=[
            {"_id": "a", "total_price": 300, "total_qty": 5},
            {"_id": "b", "total_price": 50, "total_qty": 10},
        ],
        msg="Multiple $sum accumulators should independently sum different fields",
    ),
    AccumulatorTestCase(
        "multiple_sum_field_and_expression",
        docs=[
            {"cat": "a", "price": 100, "qty": 2},
            {"cat": "a", "price": 200, "qty": 3},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "total_price": {"$sum": "$price"},
                    "total_revenue": {"$sum": {"$multiply": ["$price", "$qty"]}},
                }
            }
        ],
        expected=[{"_id": "a", "total_price": 300, "total_revenue": 800}],
        msg="$sum should independently sum a field and a computed expression",
    ),
    AccumulatorTestCase(
        "sum_field_and_constant",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "b", "v": 5},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "total": {"$sum": "$v"},
                    "count": {"$sum": 1},
                    "five_per_doc": {"$sum": 5},
                }
            }
        ],
        expected=[
            {"_id": "a", "total": 30, "count": 2, "five_per_doc": 10},
            {"_id": "b", "total": 5, "count": 1, "five_per_doc": 5},
        ],
        msg="$sum should work with field, constant 1, and constant 5 in the same $group",
    ),
]

# Property [Sum Type Promotion with Sibling]: $sum type promotion to
# Decimal128 does not interfere with sibling accumulators that return simpler
# types.
SUM_TYPE_PROMOTION_WITH_SIBLING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "sum_decimal128_with_int_count",
        docs=[
            {"cat": "a", "v": Decimal128("1.5")},
            {"cat": "a", "v": Decimal128("2.5")},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "total": {"$sum": "$v"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[{"_id": "a", "total": Decimal128("4.0"), "count": 2}],
        msg="$sum promoting to Decimal128 should not affect sibling $sum(1) returning int32",
    ),
]

SUM_INTEGRATION_TESTS = (
    SUM_WITH_AVG_TESTS
    + SUM_WITH_COUNT_TESTS
    + SUM_WITH_MIN_MAX_TESTS
    + SUM_WITH_FIRST_LAST_TESTS
    + SUM_WITH_PUSH_ADDTOSET_TESTS
    + SUM_WITH_MERGE_OBJECTS_TESTS
    + MULTIPLE_SUM_TESTS
    + SUM_TYPE_PROMOTION_WITH_SIBLING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUM_INTEGRATION_TESTS))
def test_accumulators_sum_integration(collection, test_case: AccumulatorTestCase):
    """Test $sum accumulator composed with sibling accumulators in the same $group."""
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
