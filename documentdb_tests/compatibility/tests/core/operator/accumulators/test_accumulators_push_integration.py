"""Tests for $push accumulator composed with sibling accumulators in the same $group."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Push with Sum]: $push collects all values while $sum computes the
# total.  $push is order-dependent (requires $sort); $sum is order-independent.
PUSH_WITH_SUM_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "push_sum_single_group",
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
                    "all_vals": {"$push": "$v"},
                    "total": {"$sum": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "all_vals": [10, 20, 30], "total": 60}],
        msg="$push should collect all values while $sum computes the total",
    ),
    AccumulatorTestCase(
        "push_sum_null_diverges",
        docs=[
            {"cat": "a", "v": None},
            {"cat": "a", "v": 10},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "all_vals": {"$push": "$v"},
                    "total": {"$sum": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "all_vals": [None, 10], "total": 10}],
        msg="$push should include null while $sum ignores it",
    ),
]

# Property [Push with AddToSet]: $push preserves all duplicates while
# $addToSet deduplicates.
PUSH_WITH_ADDTOSET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "push_addtoset_duplicates",
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
                    "all_vals": {"$push": "$v"},
                    "unique_vals": {"$addToSet": "$v"},
                }
            },
        ],
        expected=[
            {"_id": "a", "all_vals": [10, 10, 20], "unique_vals": [10, 20]},
        ],
        msg="$push should preserve duplicates while $addToSet deduplicates",
    ),
]

# Property [Push with Min/Max]: $push collects all values while $min and $max
# independently compute the minimum and maximum.
PUSH_WITH_MIN_MAX_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "push_min_max_basic",
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
                    "all_vals": {"$push": "$v"},
                    "lo": {"$min": "$v"},
                    "hi": {"$max": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "all_vals": [10, 20, 30], "lo": 10, "hi": 30}],
        msg="$push should collect all values while $min/$max find extremes",
    ),
]

# Property [Push with First/Last]: $push collects all values while $first and
# $last pick the first and last values from the sorted input.
PUSH_WITH_FIRST_LAST_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "push_first_last_with_sort",
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
                    "all_vals": {"$push": "$v"},
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "all_vals": [10, 20, 30], "first_v": 10, "last_v": 30}],
        msg="$push should collect all values while $first/$last pick sorted extremes",
    ),
]

# Property [Push with Avg]: $push collects all values while $avg computes
# the mean.  $push includes null; $avg ignores it.
PUSH_WITH_AVG_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "push_avg_basic",
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
                    "all_vals": {"$push": "$v"},
                    "mean": {"$avg": "$v"},
                }
            },
        ],
        expected=[{"_id": "a", "all_vals": [10, 20, 30], "mean": 20.0}],
        msg="$push should collect all values while $avg computes the mean",
    ),
]

# Property [Push with Count]: $push collects all values while $count (via
# $sum: 1) counts documents.  $push excludes missing fields; $count counts
# all documents regardless.
PUSH_WITH_COUNT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "push_count_basic",
        docs=[
            {"cat": "a", "v": 10},
            {"cat": "a", "v": 20},
            {"cat": "a"},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "all_vals": {"$push": "$v"},
                    "count": {"$sum": 1},
                }
            },
        ],
        expected=[{"_id": "a", "all_vals": [10, 20], "count": 3}],
        msg="$push should exclude missing values while $count counts all documents",
    ),
]

# Property [Multiple Push Accumulators]: multiple $push accumulators in the
# same $group independently collect values from different fields.
MULTIPLE_PUSH_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "multiple_push_different_fields",
        docs=[
            {"cat": "a", "name": "x", "score": 10},
            {"cat": "a", "name": "y", "score": 20},
            {"cat": "b", "name": "z", "score": 30},
        ],
        pipeline=[
            {"$sort": {"score": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "names": {"$push": "$name"},
                    "scores": {"$push": "$score"},
                }
            },
        ],
        expected=[
            {"_id": "a", "names": ["x", "y"], "scores": [10, 20]},
            {"_id": "b", "names": ["z"], "scores": [30]},
        ],
        msg="Multiple $push accumulators should independently collect from different fields",
    ),
]

PUSH_INTEGRATION_TESTS = (
    PUSH_WITH_SUM_TESTS
    + PUSH_WITH_ADDTOSET_TESTS
    + PUSH_WITH_MIN_MAX_TESTS
    + PUSH_WITH_FIRST_LAST_TESTS
    + PUSH_WITH_AVG_TESTS
    + PUSH_WITH_COUNT_TESTS
    + MULTIPLE_PUSH_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(PUSH_INTEGRATION_TESTS))
def test_accumulators_push_integration(collection, test_case: AccumulatorTestCase):
    """Test $push accumulator composed with sibling accumulators in the same $group."""
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
