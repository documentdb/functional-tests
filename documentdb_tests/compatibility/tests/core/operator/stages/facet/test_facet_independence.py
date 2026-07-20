"""Aggregation $facet stage tests - sub-pipeline independence.

Verifies that $facet sub-pipelines are fully independent: they share the same
input snapshot, one sub-pipeline's transformations do not affect another's
input, and a $limit/$match in one does not reduce the input seen by others.
"""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [
    {"_id": 1, "cat": "A", "v": 10},
    {"_id": 2, "cat": "A", "v": 20},
    {"_id": 3, "cat": "B", "v": 30},
]

# Property [Sub-Pipeline Independence]: a $limit, $match, or $addFields in one
# sub-pipeline does not affect the input seen by another; a runtime error in any
# sub-pipeline fails the whole stage.
FACET_INDEPENDENCE_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="limit_in_one_does_not_reduce_input",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "limited": [{"$sort": {"_id": 1}}, {"$limit": 1}],
                    "counted": [{"$count": "n"}],
                }
            }
        ],
        expected=[{"limited": [DOCS[0]], "counted": [{"n": 3}]}],
        msg="A $limit in one sub-pipeline must not affect another sub-pipeline's input",
    ),
    StageTestCase(
        id="count_counts_all_input",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "filtered": [{"$match": {"cat": "A"}}],
                    "counted": [{"$count": "n"}],
                }
            }
        ],
        expected=[{"filtered": [DOCS[0], DOCS[1]], "counted": [{"n": 3}]}],
        msg="$count should count all input documents regardless of sibling sub-pipelines",
    ),
    StageTestCase(
        id="transformation_does_not_leak",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "adder": [{"$addFields": {"extra": 1}}, {"$match": {"_id": 1}}],
                    "viewer": [{"$match": {"_id": 1}}, {"$project": {"_id": 1, "extra": 1}}],
                }
            }
        ],
        expected=[{"adder": [{"_id": 1, "cat": "A", "v": 10, "extra": 1}], "viewer": [{"_id": 1}]}],
        msg="A field added in one sub-pipeline must not leak into another sub-pipeline",
    ),
    StageTestCase(
        id="sample_before_facet_shared_snapshot",
        docs=DOCS,
        pipeline=[
            {"$sample": {"size": 10}},
            {
                "$facet": {
                    "a": [{"$sort": {"_id": 1}}],
                    "b": [{"$sort": {"_id": 1}}],
                }
            },
        ],
        expected=[{"a": DOCS, "b": DOCS}],
        msg="$sample before $facet: both sub-pipelines receive the same document snapshot",
    ),
    StageTestCase(
        id="same_result_as_independent_pipelines",
        docs=DOCS,
        pipeline=[
            {
                "$facet": {
                    "byCat": [
                        {"$group": {"_id": "$cat", "sum": {"$sum": "$v"}}},
                        {"$sort": {"_id": 1}},
                    ],
                    "high": [{"$match": {"v": {"$gte": 20}}}, {"$sort": {"_id": 1}}],
                }
            }
        ],
        expected=[
            {
                "byCat": [{"_id": "A", "sum": 30}, {"_id": "B", "sum": 30}],
                "high": [DOCS[1], DOCS[2]],
            }
        ],
        msg="Sub-pipeline results should equal running each pipeline independently",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(FACET_INDEPENDENCE_TESTS))
def test_facet_independence(collection, test_case: StageTestCase):
    """Test sub-pipeline independence of the $facet stage."""
    coll = populate_collection(collection, test_case)
    command: dict[str, Any] = {
        "aggregate": coll.name,
        "pipeline": test_case.pipeline,
        "cursor": {},
    }
    command.update(test_case.extra_command_fields)
    result = execute_command(coll, command)
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_doc_order=test_case.ignore_doc_order,
        ignore_order_in=test_case.ignore_order_in,
    )


@pytest.mark.aggregate
def test_rand_before_facet_shared_snapshot(collection):
    """$rand before $facet is frozen: both sub-pipelines see the same value per document."""
    collection.insert_many(DOCS)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"r": {"$rand": {}}}},
                {
                    "$facet": {
                        "a": [{"$sort": {"_id": 1}}, {"$project": {"_id": 1, "r": 1}}],
                        "b": [{"$sort": {"_id": 1}}, {"$project": {"_id": 1, "r": 1}}],
                    }
                },
            ],
            "cursor": {},
        },
    )
    a_branch = result["cursor"]["firstBatch"][0]["a"]
    assertSuccess(
        result,
        [{"a": a_branch, "b": a_branch}],
        msg="Both sub-pipelines must see the same pre-computed $rand values from the snapshot",
    )
