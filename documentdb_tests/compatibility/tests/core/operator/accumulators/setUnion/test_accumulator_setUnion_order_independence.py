"""Tests for $setUnion accumulator: order independence.

$setUnion is order-independent — the result must be the same regardless of
input document order.  Each scenario is run twice with opposite $sort
directions before $group to verify identical output.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Order Independence]: $setUnion produces the same set regardless of
# the order in which documents are fed into $group.  We verify by running the
# same data with $sort ascending and $sort descending, asserting identical
# results.
SETUNION_ORDER_INDEPENDENCE_TESTS: list[AccumulatorTestCase] = [
    # --- disjoint arrays, ascending sort ---
    AccumulatorTestCase(
        "disjoint_sort_asc",
        docs=[{"k": 1, "v": [1, 2]}, {"k": 2, "v": [3, 4]}],
        pipeline=[
            {"$sort": {"k": 1}},
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3, 4]}],
        msg="$setUnion should produce the same set with ascending sort",
    ),
    AccumulatorTestCase(
        "disjoint_sort_desc",
        docs=[{"k": 1, "v": [1, 2]}, {"k": 2, "v": [3, 4]}],
        pipeline=[
            {"$sort": {"k": -1}},
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3, 4]}],
        msg="$setUnion should produce the same set with descending sort",
    ),
    # --- three docs, ascending sort ---
    AccumulatorTestCase(
        "three_docs_sort_asc",
        docs=[{"k": 1, "v": [1]}, {"k": 2, "v": [2]}, {"k": 3, "v": [3]}],
        pipeline=[
            {"$sort": {"k": 1}},
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should produce the same set for three docs with ascending sort",
    ),
    AccumulatorTestCase(
        "three_docs_sort_desc",
        docs=[{"k": 1, "v": [1]}, {"k": 2, "v": [2]}, {"k": 3, "v": [3]}],
        pipeline=[
            {"$sort": {"k": -1}},
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should produce the same set for three docs with descending sort",
    ),
    # --- overlapping arrays, ascending sort ---
    AccumulatorTestCase(
        "overlap_sort_asc",
        docs=[{"k": 1, "v": [1, 2, 3]}, {"k": 2, "v": [2, 3, 4]}],
        pipeline=[
            {"$sort": {"k": 1}},
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3, 4]}],
        msg="$setUnion should produce the same set with overlapping arrays, ascending sort",
    ),
    AccumulatorTestCase(
        "overlap_sort_desc",
        docs=[{"k": 1, "v": [1, 2, 3]}, {"k": 2, "v": [2, 3, 4]}],
        pipeline=[
            {"$sort": {"k": -1}},
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3, 4]}],
        msg="$setUnion should produce the same set with overlapping arrays, descending sort",
    ),
    # --- empty array mixed in, ascending sort ---
    AccumulatorTestCase(
        "empty_mixed_sort_asc",
        docs=[{"k": 1, "v": []}, {"k": 2, "v": [1, 2]}],
        pipeline=[
            {"$sort": {"k": 1}},
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2]}],
        msg="$setUnion should produce the same set with empty array, ascending sort",
    ),
    AccumulatorTestCase(
        "empty_mixed_sort_desc",
        docs=[{"k": 1, "v": []}, {"k": 2, "v": [1, 2]}],
        pipeline=[
            {"$sort": {"k": -1}},
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2]}],
        msg="$setUnion should produce the same set with empty array, descending sort",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_ORDER_INDEPENDENCE_TESTS))
def test_accumulator_setUnion_order_independence(collection, test_case: AccumulatorTestCase):
    """Test $setUnion accumulator order independence."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
