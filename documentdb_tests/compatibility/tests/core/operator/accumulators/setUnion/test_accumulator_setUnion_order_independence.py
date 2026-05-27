"""Tests for $setUnion accumulator: order independence."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Order Independence]: $setUnion produces the same set regardless of
# the order in which documents are inserted or processed.
SETUNION_ORDER_INDEPENDENCE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "order_ab_vs_ba",
        docs=[{"v": [1, 2]}, {"v": [3, 4]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3, 4]}],
        msg="$setUnion should produce the same set when docs are in order A, B",
    ),
    AccumulatorTestCase(
        "order_ba_vs_ab",
        docs=[{"v": [3, 4]}, {"v": [1, 2]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3, 4]}],
        msg="$setUnion should produce the same set when docs are in order B, A",
    ),
    AccumulatorTestCase(
        "order_three_permutation_abc",
        docs=[{"v": [1]}, {"v": [2]}, {"v": [3]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should produce the same set for permutation A, B, C",
    ),
    AccumulatorTestCase(
        "order_three_permutation_cba",
        docs=[{"v": [3]}, {"v": [2]}, {"v": [1]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3]}],
        msg="$setUnion should produce the same set for permutation C, B, A",
    ),
    AccumulatorTestCase(
        "order_overlap_ab",
        docs=[{"v": [1, 2, 3]}, {"v": [2, 3, 4]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3, 4]}],
        msg="$setUnion should produce the same set with overlapping arrays in order A, B",
    ),
    AccumulatorTestCase(
        "order_overlap_ba",
        docs=[{"v": [2, 3, 4]}, {"v": [1, 2, 3]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2, 3, 4]}],
        msg="$setUnion should produce the same set with overlapping arrays in order B, A",
    ),
    AccumulatorTestCase(
        "order_with_empty_array_first",
        docs=[{"v": []}, {"v": [1, 2]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2]}],
        msg="$setUnion should produce the same set with empty array first",
    ),
    AccumulatorTestCase(
        "order_with_empty_array_last",
        docs=[{"v": [1, 2]}, {"v": []}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
            {"$project": {"_id": 0, "result": {"$sortArray": {"input": "$result", "sortBy": 1}}}},
        ],
        expected=[{"result": [1, 2]}],
        msg="$setUnion should produce the same set with empty array last",
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
