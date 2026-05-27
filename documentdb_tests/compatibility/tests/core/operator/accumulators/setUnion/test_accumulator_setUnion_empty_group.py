"""Tests for $setUnion accumulator: empty-group behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Empty-Group Behavior]: when $group with _id: null runs against an
# empty collection (or all documents are filtered out), no group is produced
# and the result is an empty cursor.
SETUNION_EMPTY_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "empty_group_empty_collection",
        docs=None,
        pipeline=[
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
        ],
        expected=[],
        msg="$setUnion with _id: null on empty collection should produce no output",
    ),
    AccumulatorTestCase(
        "empty_group_all_filtered_out",
        docs=[{"v": [1, 2]}, {"v": [3, 4]}],
        pipeline=[
            {"$match": {"v": {"$exists": False}}},
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
        ],
        expected=[],
        msg="$setUnion with _id: null after filtering all docs should produce no output",
    ),
    AccumulatorTestCase(
        "empty_group_match_impossible",
        docs=[{"v": [1, 2], "cat": "A"}, {"v": [3, 4], "cat": "B"}],
        pipeline=[
            {"$match": {"cat": "Z"}},
            {"$group": {"_id": None, "result": {"$setUnion": "$v"}}},
        ],
        expected=[],
        msg="$setUnion with _id: null after $match with no matches should produce no output",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_EMPTY_GROUP_TESTS))
def test_accumulator_setUnion_empty_group(collection, test_case: AccumulatorTestCase):
    """Test $setUnion accumulator empty-group behavior."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
