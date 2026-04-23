"""Tests for $count aggregation stage — core counting behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Core Counting Behavior]: the output is exactly one document whose
# field value equals the number of documents reaching the $count stage.
COUNT_CORE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "core_single_doc",
        docs=[{"_id": 1, "x": 1}],
        pipeline=[{"$count": "total"}],
        expected=[{"total": 1}],
        msg="$count should return 1 for a single input document",
    ),
    StageTestCase(
        "core_multiple_docs",
        docs=[{"_id": 1}, {"_id": 2}, {"_id": 3}, {"_id": 4}, {"_id": 5}],
        pipeline=[{"$count": "total"}],
        expected=[{"total": 5}],
        msg="$count should return the number of input documents",
    ),
    StageTestCase(
        "core_large_collection",
        docs=[{"_id": i} for i in range(10_000)],
        pipeline=[{"$count": "total"}],
        expected=[{"total": 10_000}],
        msg="$count should return correct count for a large number of documents",
    ),
]

# Property [Empty Input Behavior]: when zero documents reach the $count stage,
# the result is an empty cursor rather than a document with count 0.
COUNT_EMPTY_INPUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nonexistent_collection",
        docs=None,
        pipeline=[{"$count": "total"}],
        expected=[],
        msg="$count should return empty cursor on a non-existent collection",
    ),
    StageTestCase(
        "empty_collection",
        docs=[],
        pipeline=[{"$count": "total"}],
        expected=[],
        msg="$count should return empty cursor on an empty collection",
    ),
]

# Property [Single Document Output]: the output is always exactly 0 or 1
# documents, and consecutive $count stages each count the single document
# output by the previous stage.
COUNT_SINGLE_OUTPUT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "cardinality_many_docs_one_output",
        docs=[{"_id": i} for i in range(50)],
        pipeline=[
            {"$count": "total"},
            {"$count": "num_results"},
        ],
        expected=[{"num_results": 1}],
        msg="$count should produce exactly one document regardless of input count",
    ),
]

# Property [Return Type]: the count value is int32 for practically testable
# document counts. The server promotes to long when the count exceeds the
# int32 maximum (~2.1 billion), and to double beyond int64, but exercising
# those transitions would require inserting billions of documents.
COUNT_RETURN_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "return_type_single",
        docs=[{"_id": 1}],
        pipeline=[
            {"$count": "n"},
            {"$addFields": {"type": {"$type": "$n"}}},
        ],
        expected=[{"n": 1, "type": "int"}],
        msg="$count should return int32 for a count of 1",
    ),
    StageTestCase(
        "return_type_multiple",
        docs=[{"_id": i} for i in range(10_000)],
        pipeline=[
            {"$count": "n"},
            {"$addFields": {"type": {"$type": "$n"}}},
        ],
        expected=[{"n": 10_000, "type": "int"}],
        msg="$count should return int32 for a count of 10000",
    ),
]

COUNT_BEHAVIOR_TESTS = (
    COUNT_CORE_TESTS + COUNT_EMPTY_INPUT_TESTS + COUNT_SINGLE_OUTPUT_TESTS + COUNT_RETURN_TYPE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(COUNT_BEHAVIOR_TESTS))
def test_count_behavior(collection, test_case: StageTestCase):
    """Test $count core counting behavior."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
