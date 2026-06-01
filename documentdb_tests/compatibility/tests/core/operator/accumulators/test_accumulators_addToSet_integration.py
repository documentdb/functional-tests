"""Tests for $addToSet accumulator composed with sibling accumulators in the same $group."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Property lists
# ---------------------------------------------------------------------------

# Property [AddToSet with Sum]: $addToSet collects unique values while $sum
# computes the total independently in the same $group.
ADDTOSET_WITH_SUM_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "addtoset_sum_basic",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a", "v": 10},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "unique": {"$addToSet": "$v"},
                    "total": {"$sum": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "unique": [10, 20], "total": 40}],
        msg="$addToSet should collect unique values while $sum totals all values "
        "including duplicates",
    ),
    AccumulatorTestCase(
        "addtoset_sum_multiple_groups",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 10},
            {"cat": "b", "v": 5},
            {"cat": "b", "v": 15},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "unique": {"$addToSet": "$v"},
                    "total": {"$sum": "$v"},
                }
            }
        ],
        expected=[
            {"_id": "a", "unique": [10], "total": 20},
            {"_id": "b", "unique": [5, 15], "total": 20},
        ],
        msg="$addToSet and $sum should compute independently across " "multiple groups",
    ),
]

# Property [AddToSet with Count]: $addToSet collects unique values while
# $sum(1) counts all documents including those with duplicate values.
ADDTOSET_WITH_COUNT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "addtoset_count_dedup_vs_total",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "unique": {"$addToSet": "$v"},
                    "count": {"$sum": 1},
                }
            }
        ],
        expected=[{"_id": "a", "unique": [10, 20], "count": 3}],
        msg="$addToSet should have 2 unique values while $sum(1) counts " "all 3 documents",
    ),
]

# Property [AddToSet with Push]: $addToSet collects unique values while $push
# collects all values including duplicates.
ADDTOSET_WITH_PUSH_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "addtoset_push_dedup_vs_all",
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
                    "unique": {"$addToSet": "$v"},
                    "all_vals": {"$push": "$v"},
                }
            },
        ],
        expected=[
            {"_id": "a", "unique": [10, 20], "all_vals": [10, 10, 20]},
        ],
        msg="$addToSet should deduplicate while $push preserves all values",
    ),
]

# Property [AddToSet with Min/Max]: $addToSet collects the full unique set
# while $min/$max extract extremes independently.
ADDTOSET_WITH_MIN_MAX_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "addtoset_min_max",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a", "v": 10},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "unique": {"$addToSet": "$v"},
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            }
        ],
        expected=[
            {"_id": "a", "unique": [10, 20, 30], "lo": 10, "hi": 30},
        ],
        msg="$addToSet should collect all unique values while $min/$max " "extract extremes",
    ),
]

# Property [AddToSet with Avg]: $addToSet collects unique values while $avg
# computes the mean over all documents including duplicates.
ADDTOSET_WITH_AVG_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "addtoset_avg_includes_duplicates",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 40},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "unique": {"$addToSet": "$v"},
                    "mean": {"$avg": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "unique": [10, 40], "mean": 20.0}],
        msg="$addToSet should have 2 unique values while $avg computes "
        "mean over all 3 docs (including duplicate)",
    ),
]

# Property [AddToSet Null Handling vs Sum]: $addToSet collects null as a value
# while $sum ignores null.
ADDTOSET_NULL_VS_SUM_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "addtoset_null_collected_sum_ignores",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": None},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "unique": {"$addToSet": "$v"},
                    "total": {"$sum": "$v"},
                }
            }
        ],
        expected=[{"_id": "a", "unique": [None, 10], "total": 10}],
        msg="$addToSet should collect null as a value while $sum ignores "
        "null and totals only numeric values",
    ),
]

# Property [AddToSet with First/Last]: $addToSet collects all unique values
# regardless of order while $first/$last pick positional values after $sort.
ADDTOSET_WITH_FIRST_LAST_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "addtoset_first_last",
        docs=[
            {"cat": "a", "v": 30},
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a", "v": 10},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "unique": {"$addToSet": "$v"},
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
        ],
        expected=[
            {"_id": "a", "unique": [10, 20, 30], "first_v": 10, "last_v": 30},
        ],
        msg="$addToSet should collect all unique values while $first/$last "
        "pick sorted positional extremes",
    ),
]

# Property [AddToSet with MergeObjects]: $addToSet collects unique values
# while $mergeObjects combines per-document metadata independently.
ADDTOSET_WITH_MERGEOBJECTS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "addtoset_mergeobjects",
        docs=[
            {"cat": "a", "v": 10, "meta": {"src": "x"}},
            {"cat": "a", "v": 20, "meta": {"quality": "high"}},
            {"cat": "a", "v": 10, "meta": {"reviewed": True}},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "unique": {"$addToSet": "$v"},
                    "merged": {"$mergeObjects": "$meta"},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "unique": [10, 20],
                "merged": {"src": "x", "quality": "high", "reviewed": True},
            }
        ],
        msg="$addToSet should deduplicate values while $mergeObjects "
        "merges metadata from all documents including duplicates",
    ),
]

# Property [Multiple AddToSet]: multiple $addToSet accumulators in the same
# $group independently collect unique values from different fields.
MULTIPLE_ADDTOSET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "multiple_addtoset_different_fields",
        docs=[
            {"cat": "a", "color": "red", "size": "S"},
            {"cat": "a", "color": "blue", "size": "M"},
            {"cat": "a", "color": "red", "size": "S"},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$cat",
                    "colors": {"$addToSet": "$color"},
                    "sizes": {"$addToSet": "$size"},
                }
            }
        ],
        expected=[
            {
                "_id": "a",
                "colors": ["red", "blue"],
                "sizes": ["S", "M"],
            },
        ],
        msg="Multiple $addToSet accumulators should independently collect "
        "unique values from different fields",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

ADDTOSET_INTEGRATION_TESTS = (
    ADDTOSET_WITH_SUM_TESTS
    + ADDTOSET_WITH_COUNT_TESTS
    + ADDTOSET_WITH_PUSH_TESTS
    + ADDTOSET_WITH_MIN_MAX_TESTS
    + ADDTOSET_WITH_AVG_TESTS
    + ADDTOSET_NULL_VS_SUM_TESTS
    + ADDTOSET_WITH_FIRST_LAST_TESTS
    + ADDTOSET_WITH_MERGEOBJECTS_TESTS
    + MULTIPLE_ADDTOSET_TESTS
)

# ---------------------------------------------------------------------------
# Test function
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("test_case", pytest_params(ADDTOSET_INTEGRATION_TESTS))
def test_accumulators_addToSet_integration(collection, test_case: AccumulatorTestCase):
    """Test $addToSet accumulator composed with sibling accumulators."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline or [],
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=True,
        ignore_order_in=["unique", "colors", "sizes"],
    )
