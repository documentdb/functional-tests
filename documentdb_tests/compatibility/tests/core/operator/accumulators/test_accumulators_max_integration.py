"""Tests for $max accumulator composed with sibling accumulators in the same $group."""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ===========================================================================
# 1. $max with $min
# ===========================================================================

# Property [Max with Min]: $max and $min coexist in the same $group and
# independently compute the maximum and minimum of a field.
MAX_WITH_MIN_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "max_min_single_group",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "hi": {"$max": "$v"},
                    "lo": {"$min": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "hi": 30, "lo": 10}],
        msg="$max and $min should independently compute max and min",
    ),
    AccumulatorTestCase(
        "max_min_multiple_groups",
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
                    "hi": {"$max": "$v"},
                    "lo": {"$min": "$v"},
                }
            }
        ],
        expected=[
            {"_id": "a", "hi": 20, "lo": 10},
            {"_id": "b", "hi": 25, "lo": 5},
        ],
        msg="$max and $min should produce correct results across multiple groups",
    ),
    AccumulatorTestCase(
        "max_min_cross_type_preserves_types",
        docs=[
            {"cat": "a", "v": 5},
            {"cat": "a", "v": Int64(100)},
            {"cat": "a", "v": 2.5},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "hi": {"$max": "$v"},
                    "lo": {"$min": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "hi": Int64(100), "lo": 2.5}],
        msg="$max and $min should each preserve the original type of their result",
    ),
    AccumulatorTestCase(
        "max_min_null_handling",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "hi": {"$max": "$v"},
                    "lo": {"$min": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "hi": 20, "lo": 10}],
        msg="$max and $min should both skip null values",
    ),
    AccumulatorTestCase(
        "max_min_all_null",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": None},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "hi": {"$max": "$v"},
                    "lo": {"$min": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "hi": None, "lo": None}],
        msg="$max and $min should both return null when all values are null",
    ),
]


# ===========================================================================
# 2. $max with $sum
# ===========================================================================

# Property [Max with Sum]: $max picks the largest value while $sum
# accumulates the total; $sum type-promotes while $max preserves types.
MAX_WITH_SUM_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "max_sum_basic",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "hi": {"$max": "$v"},
                    "total": {"$sum": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "hi": 30, "total": 60}],
        msg="$max should pick largest while $sum computes total",
    ),
    AccumulatorTestCase(
        "max_sum_null_diverges",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": None},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "hi": {"$max": "$v"},
                    "total": {"$sum": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "hi": None, "total": 0}],
        msg="$max returns null but $sum returns 0 when all values are null",
    ),
    AccumulatorTestCase(
        "max_sum_type_preservation",
        docs=[
            {"cat": "a", "v": 5},
            {"cat": "a", "v": Int64(100)},
            {"cat": "a", "v": 2.5},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "hi": {"$max": "$v"},
                    "total": {"$sum": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "hi": Int64(100), "total": 107.5}],
        msg="$max preserves Int64 type while $sum promotes to double",
    ),
]


# ===========================================================================
# 3. $max with $avg
# ===========================================================================

# Property [Max with Avg]: $max picks the largest value while $avg computes
# the arithmetic mean; $avg always returns double, $max preserves types.
MAX_WITH_AVG_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "max_avg_basic",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a", "v": 30},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "hi": {"$max": "$v"},
                    "mean": {"$avg": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "hi": 30, "mean": 20.0}],
        msg="$max should pick largest while $avg computes mean",
    ),
    AccumulatorTestCase(
        "max_avg_all_null_diverges",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": None},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "hi": {"$max": "$v"},
                    "mean": {"$avg": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "hi": None, "mean": None}],
        msg="$max and $avg both return null when all values are null",
    ),
]


# ===========================================================================
# 4. $max with $first / $last
# ===========================================================================

# Property [Max with First/Last]: $max picks the globally largest value
# while $first/$last pick positional values from the group.  A preceding
# $sort establishes order for $first and $last; $max is order-independent.
MAX_WITH_FIRST_LAST_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "max_first_last_with_sort",
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
                    "hi": {"$max": "$v"},
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "hi": 30, "first_v": 10, "last_v": 30}],
        msg="$max should equal $last when $sort ascending, " "$first picks smallest",
    ),
    AccumulatorTestCase(
        "max_first_last_with_sort_desc",
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
                    "hi": {"$max": "$v"},
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "hi": 30, "first_v": 30, "last_v": 10}],
        msg="$max should equal $first when $sort descending, " "$last picks smallest",
    ),
]


# ===========================================================================
# 5. $max with $push / $addToSet
# ===========================================================================

# Property [Max with Push/AddToSet]: $max picks the largest value while
# $push collects all values and $addToSet collects unique values.
MAX_WITH_PUSH_ADDTOSET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "max_push_addtoset",
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
                    "hi": {"$max": "$v"},
                    "all_vals": {"$push": "$v"},
                    "unique_vals": {"$addToSet": "$v"},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "hi": 20,
                "all_vals": [10, 10, 20],
                "unique_vals": [10, 20],
            },
        ],
        msg="$max picks largest while $push keeps all and $addToSet keeps unique",
    ),
]


# ===========================================================================
# 6. $max with $count ($sum: 1)
# ===========================================================================

# Property [Max with Count]: $max picks the largest value while $sum(1)
# counts documents.  $max skips null but $sum(1) counts all documents.
MAX_WITH_COUNT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "max_count_basic",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "b", "v": 5},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "hi": {"$max": "$v"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[
            {"_id": "a", "hi": 20, "count": 2},
            {"_id": "b", "hi": 5, "count": 1},
        ],
        msg="$max picks largest per group while $sum(1) counts documents",
    ),
    AccumulatorTestCase(
        "max_count_null_counted_but_skipped",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": None},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "hi": {"$max": "$v"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[{"_id": "a", "hi": 10, "count": 3}],
        msg="$max skips nulls but $sum(1) counts all documents including nulls",
    ),
]


# ===========================================================================
# 7. $max with $mergeObjects
# ===========================================================================

# Property [Max with MergeObjects]: $max picks the largest value while
# $mergeObjects combines per-document metadata into a single object.
MAX_WITH_MERGE_OBJECTS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "max_merge_objects",
        docs=[
            {"cat": "a", "v": 10, "meta": {"src": "x"}},
            {"cat": "a", "v": 20, "meta": {"quality": "high"}},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "hi": {"$max": "$v"},
                    "merged": {"$mergeObjects": "$meta"},
                }
            }
        ],
        expected=[
            {
                "_id": "a",
                "hi": 20,
                "merged": {"src": "x", "quality": "high"},
            },
        ],
        msg="$max picks largest while $mergeObjects combines metadata",
    ),
]


# ===========================================================================
# 8. Multiple $max expressions
# ===========================================================================

# Property [Multiple Max Expressions]: multiple $max accumulators in the
# same $group independently compute the maximum of different fields.
MULTIPLE_MAX_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "multiple_max_different_fields",
        docs=[
            {"cat": "a", "price": 100, "qty": 2},
            {"cat": "a", "price": 200, "qty": 3},
            {"cat": "b", "price": 50, "qty": 10},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "max_price": {"$max": "$price"},
                    "max_qty": {"$max": "$qty"},
                }
            }
        ],
        expected=[
            {"_id": "a", "max_price": 200, "max_qty": 3},
            {"_id": "b", "max_price": 50, "max_qty": 10},
        ],
        msg="Multiple $max accumulators should independently find max of different fields",
    ),
    AccumulatorTestCase(
        "max_field_and_expression",
        docs=[
            {"cat": "a", "price": 100, "qty": 2},
            {"cat": "a", "price": 200, "qty": 3},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "max_price": {"$max": "$price"},
                    "max_revenue": {"$max": {"$multiply": ["$price", "$qty"]}},
                }
            }
        ],
        expected=[{"_id": "a", "max_price": 200, "max_revenue": 600}],
        msg="$max should independently find max of a field and a computed expression",
    ),
]


# ===========================================================================
# 9. $max with Decimal128 type alongside simpler sibling types
# ===========================================================================

# Property [Max Decimal128 with Sibling]: $max returning Decimal128 does
# not interfere with sibling accumulators that return simpler types.
MAX_DECIMAL128_WITH_SIBLING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "max_decimal128_with_int_count",
        docs=[
            {"cat": "a", "v": Decimal128("1.5")},
            {"cat": "a", "v": Decimal128("2.5")},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "hi": {"$max": "$v"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[{"_id": "a", "hi": Decimal128("2.5"), "count": 2}],
        msg="$max returning Decimal128 should not affect sibling $sum(1)",
    ),
]


# ===========================================================================
# Combined tests and test function
# ===========================================================================

MAX_INTEGRATION_TESTS = (
    MAX_WITH_MIN_TESTS
    + MAX_WITH_SUM_TESTS
    + MAX_WITH_AVG_TESTS
    + MAX_WITH_FIRST_LAST_TESTS
    + MAX_WITH_PUSH_ADDTOSET_TESTS
    + MAX_WITH_COUNT_TESTS
    + MAX_WITH_MERGE_OBJECTS_TESTS
    + MULTIPLE_MAX_TESTS
    + MAX_DECIMAL128_WITH_SIBLING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MAX_INTEGRATION_TESTS))
def test_accumulators_max_integration(collection, test_case: AccumulatorTestCase):
    """Test $max accumulator composed with sibling accumulators in the same $group."""
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
