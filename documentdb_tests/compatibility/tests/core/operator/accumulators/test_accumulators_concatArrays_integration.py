"""Tests for $concatArrays accumulator composed with sibling accumulators in the same $group."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [ConcatArrays vs AddToSet]: $concatArrays preserves all elements
# including duplicates while $addToSet deduplicates in the same $group.
CONCATARRAYS_WITH_ADDTOSET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "concatArrays_vs_addToSet_duplicates",
        docs=[
            {"_id": 1, "cat": "a", "v": [1, 2]},
            {"_id": 2, "cat": "a", "v": [2, 3]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "concat": {"$concatArrays": "$v"},
                    "unique": {"$addToSet": "$v"},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "concat": [1, 2, 2, 3],
                "unique": [[1, 2], [2, 3]],
            }
        ],
        msg="$concatArrays should preserve duplicates while $addToSet collects unique arrays",
    ),
    AccumulatorTestCase(
        "concatArrays_vs_addToSet_identical_arrays",
        docs=[
            {"_id": 1, "cat": "a", "v": [1, 2]},
            {"_id": 2, "cat": "a", "v": [1, 2]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "concat": {"$concatArrays": "$v"},
                    "unique": {"$addToSet": "$v"},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "concat": [1, 2, 1, 2],
                "unique": [[1, 2]],
            }
        ],
        msg="$concatArrays should repeat elements from identical arrays while $addToSet keeps one",
    ),
]

# Property [ConcatArrays vs Push]: $concatArrays flattens one level
# (concatenates arrays) while $push nests each array as an element.
CONCATARRAYS_WITH_PUSH_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "concatArrays_vs_push_flattening",
        docs=[
            {"_id": 1, "cat": "a", "v": [1, 2]},
            {"_id": 2, "cat": "a", "v": [3, 4]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "concat": {"$concatArrays": "$v"},
                    "pushed": {"$push": "$v"},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "concat": [1, 2, 3, 4],
                "pushed": [[1, 2], [3, 4]],
            }
        ],
        msg="$concatArrays should flatten arrays while $push nests them",
    ),
]

# Property [ConcatArrays with Count]: $concatArrays concatenates arrays while
# $count (via $sum: 1) counts documents independently.
CONCATARRAYS_WITH_COUNT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "concatArrays_with_count",
        docs=[
            {"_id": 1, "cat": "a", "v": [10, 20]},
            {"_id": 2, "cat": "a", "v": [30]},
            {"_id": 3, "cat": "b", "v": [40, 50]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "concat": {"$concatArrays": "$v"},
                    "count": {"$sum": 1},
                }
            },
        ],
        expected=[
            {"_id": "a", "concat": [10, 20, 30], "count": 2},
            {"_id": "b", "concat": [40, 50], "count": 1},
        ],
        msg="$concatArrays should concatenate while $sum(1) counts documents",
    ),
]

# Property [ConcatArrays with First/Last]: $concatArrays concatenates all
# arrays while $first/$last pick positional values from the sorted group.
CONCATARRAYS_WITH_FIRST_LAST_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "concatArrays_with_first_last",
        docs=[
            {"_id": 1, "cat": "a", "v": [3, 4]},
            {"_id": 2, "cat": "a", "v": [1, 2]},
            {"_id": 3, "cat": "a", "v": [5]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "concat": {"$concatArrays": "$v"},
                    "first_v": {"$first": "$v"},
                    "last_v": {"$last": "$v"},
                }
            },
        ],
        expected=[
            {
                "_id": "a",
                "concat": [3, 4, 1, 2, 5],
                "first_v": [3, 4],
                "last_v": [5],
            }
        ],
        msg="$concatArrays should concatenate all arrays while $first/$last pick endpoints",
    ),
]

# Property [ConcatArrays with Missing Divergence]: $concatArrays excludes
# missing fields while $sum ignores them (returns 0), showing independent
# missing-field handling.
CONCATARRAYS_WITH_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "concatArrays_missing_vs_sum_missing",
        docs=[
            {"_id": 1, "cat": "a", "v": [1, 2], "n": 10},
            {"_id": 2, "cat": "a", "n": 20},
            {"_id": 3, "cat": "a", "v": [3]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": "$cat",
                    "concat": {"$concatArrays": "$v"},
                    "total": {"$sum": "$n"},
                }
            },
        ],
        expected=[{"_id": "a", "concat": [1, 2, 3], "total": 30}],
        msg="$concatArrays should skip missing v while $sum should skip missing n",
    ),
]

CONCATARRAYS_INTEGRATION_TESTS = (
    CONCATARRAYS_WITH_ADDTOSET_TESTS
    + CONCATARRAYS_WITH_PUSH_TESTS
    + CONCATARRAYS_WITH_COUNT_TESTS
    + CONCATARRAYS_WITH_FIRST_LAST_TESTS
    + CONCATARRAYS_WITH_MISSING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(CONCATARRAYS_INTEGRATION_TESTS))
def test_accumulators_concatArrays_integration(collection, test_case: AccumulatorTestCase):
    """Test $concatArrays accumulator composed with sibling accumulators in the same $group."""
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
        ignore_order_in=["unique"],
    )
