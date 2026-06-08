"""Tests for $last accumulator composed with sibling accumulators in the same $group."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Last with Sum]: $last picks the last value while $sum independently
# computes the total.  $last is order-dependent; $sum is order-independent.
LAST_WITH_SUM_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "last_sum_single_group",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a", "v": 30},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "last_v": {"$last": "$v"},
                    "total": {"$sum": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "last_v": 30, "total": 60}],
        msg="$last should return last sorted value while $sum computes total",
    ),
    AccumulatorTestCase(
        "last_sum_multiple_groups",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "b", "v": 5},
            {"cat": "b", "v": 15},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "last_v": {"$last": "$v"},
                    "total": {"$sum": "$v"},
                }
            },
        ],
        expected=[
            {"_id": "a", "last_v": 20, "total": 30},
            {"_id": "b", "last_v": 15, "total": 20},
        ],
        msg="$last and $sum should produce correct results per group",
    ),
    AccumulatorTestCase(
        "last_sum_null_handling_diverges",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": None},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "last_v": {"$last": "$v"},
                    "total": {"$sum": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "last_v": 10, "total": 10}],
        msg="$last returns last sorted value (10 after null) while $sum ignores null",
    ),
]

# Property [Last with Avg]: $last picks the last value while $avg computes
# the mean.  $last preserves the original type; $avg always returns double.
LAST_WITH_AVG_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "last_avg_basic",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a", "v": 30},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "last_v": {"$last": "$v"},
                    "mean": {"$avg": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "last_v": 30, "mean": 20.0}],
        msg="$last should return last sorted value while $avg computes mean",
    ),
    AccumulatorTestCase(
        "last_avg_all_null",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": None},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "last_v": {"$last": "$v"},
                    "mean": {"$avg": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "last_v": None, "mean": None}],
        msg="$last returns null and $avg returns null when all values are null",
    ),
]

# Property [Last with Min/Max]: $last picks the last sorted value while
# $min/$max pick the extreme values regardless of sort order.
LAST_WITH_MIN_MAX_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "last_min_max_basic",
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
                    "last_v": {"$last": "$v"},
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "last_v": 30, "lo": 10, "hi": 30}],
        msg="$last returns last sorted value while $min/$max return extremes",
    ),
    AccumulatorTestCase(
        "last_min_max_mixed_types",
        docs=[
            {"cat": "a", "v": 5},
            {"cat": "a", "v": Int64(100)},
            {"cat": "a", "v": 2.5},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "last_v": {"$last": "$v"},
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "last_v": Int64(100), "lo": 2.5, "hi": Int64(100)}],
        msg="$last preserves Int64 type of last value while $min/$max pick extremes",
    ),
]

# Property [Last with Push]: $last picks the last value while $push collects
# all values into an array.  The $push array order matches the $sort order.
LAST_WITH_PUSH_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "last_push_basic",
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
                    "last_v": {"$last": "$v"},
                    "all_vals": {"$push": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "last_v": 30, "all_vals": [10, 20, 30]}],
        msg="$last returns last sorted value while $push collects all in sort order",
    ),
]

# Property [Last with AddToSet]: $last picks the last value while $addToSet
# collects unique values.
LAST_WITH_ADDTOSET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "last_addtoset_with_duplicates",
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
                    "last_v": {"$last": "$v"},
                    "unique_vals": {"$addToSet": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "last_v": 20, "unique_vals": [10, 20]}],
        msg="$last returns last sorted value while $addToSet deduplicates",
    ),
]

# Property [Last with Count]: $last picks the last value while $count
# (via $sum: 1) counts all documents including those with null/missing values.
LAST_WITH_COUNT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "last_count_basic",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a", "v": 30},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "last_v": {"$last": "$v"},
                    "count": {"$sum": 1},
                }
            },
        ],
        expected=[{"_id": "a", "last_v": 30, "count": 3}],
        msg="$last returns last sorted value while $sum(1) counts all documents",
    ),
    AccumulatorTestCase(
        "last_count_with_null",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": None},
            {"cat": "a", "v": 30},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "last_v": {"$last": "$v"},
                    "count": {"$sum": 1},
                }
            },
        ],
        expected=[{"_id": "a", "last_v": 30, "count": 3}],
        msg="$last returns last sorted value while $sum(1) counts all docs including null",
    ),
]

# Property [Last with MergeObjects]: $last picks the last value while
# $mergeObjects combines per-document metadata into a single object.
LAST_WITH_MERGE_OBJECTS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "last_merge_objects",
        docs=[
            {"cat": "a", "v": 10, "meta": {"src": "x"}},
            {"cat": "a", "v": 20, "meta": {"quality": "high"}},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "last_v": {"$last": "$v"},
                    "merged": {"$mergeObjects": "$meta"},
                }
            },
        ],
        expected=[
            {"_id": "a", "last_v": 20, "merged": {"src": "x", "quality": "high"}},
        ],
        msg="$last returns last sorted value while $mergeObjects combines metadata",
    ),
]

# Property [Last with Multiple Siblings]: $last coexists with several
# accumulators in the same $group, all computing independently.
LAST_WITH_MULTIPLE_SIBLINGS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "last_sum_min_max_count",
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
                    "last_v": {"$last": "$v"},
                    "total": {"$sum": "$v"},
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                    "count": {"$sum": 1},
                }
            },
        ],
        expected=[
            {"_id": "a", "last_v": 30, "total": 60, "lo": 10, "hi": 30, "count": 3},
        ],
        msg="$last should coexist with $sum, $min, $max, and $sum(1) in same $group",
    ),
]

# Property [Last Type Preservation with Numeric Sibling]: $last preserves
# Decimal128 type while $sum promotes to Decimal128 independently.
LAST_TYPE_PRESERVATION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "last_decimal128_with_int_sum",
        docs=[
            {"cat": "a", "v": Decimal128("1.5")},
            {"cat": "a", "v": Decimal128("2.5")},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "last_v": {"$last": "$v"},
                    "total": {"$sum": "$v"},
                    "count": {"$sum": 1},
                }
            },
        ],
        expected=[
            {"_id": "a", "last_v": Decimal128("2.5"), "total": Decimal128("4.0"), "count": 2},
        ],
        msg="$last preserves Decimal128 passthrough while $sum promotes to Decimal128",
    ),
]

# Property [Multiple Last on Different Fields]: multiple $last accumulators
# in the same $group independently pick the last value of different fields.
MULTIPLE_LAST_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "multiple_last_different_fields",
        docs=[
            {"cat": "a", "x": 1, "y": "p"},
            {"cat": "a", "x": 2, "y": "q"},
            {"cat": "a", "x": 3, "y": "r"},
        ],
        pipeline=[
            {"$sort": {"x": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "last_x": {"$last": "$x"},
                    "last_y": {"$last": "$y"},
                }
            },
        ],
        expected=[{"_id": "a", "last_x": 3, "last_y": "r"}],
        msg="Multiple $last accumulators should independently pick last value per field",
    ),
    AccumulatorTestCase(
        "multiple_last_field_and_expression",
        docs=[
            {"cat": "a", "x": 2, "y": 3},
            {"cat": "a", "x": 4, "y": 5},
        ],
        pipeline=[
            {"$sort": {"x": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "last_x": {"$last": "$x"},
                    "last_product": {"$last": {"$multiply": ["$x", "$y"]}},
                }
            },
        ],
        expected=[{"_id": "a", "last_x": 4, "last_product": 20}],
        msg="$last should independently pick last field value and last computed expression",
    ),
]

LAST_INTEGRATION_TESTS = (
    LAST_WITH_SUM_TESTS
    + LAST_WITH_AVG_TESTS
    + LAST_WITH_MIN_MAX_TESTS
    + LAST_WITH_PUSH_TESTS
    + LAST_WITH_ADDTOSET_TESTS
    + LAST_WITH_COUNT_TESTS
    + LAST_WITH_MERGE_OBJECTS_TESTS
    + LAST_WITH_MULTIPLE_SIBLINGS_TESTS
    + LAST_TYPE_PRESERVATION_TESTS
    + MULTIPLE_LAST_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LAST_INTEGRATION_TESTS))
def test_accumulators_last_integration(collection, test_case: AccumulatorTestCase):
    """Test $last accumulator composed with sibling accumulators in the same $group."""
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
