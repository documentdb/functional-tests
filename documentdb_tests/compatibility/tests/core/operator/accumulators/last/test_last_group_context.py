"""Tests for $last accumulator in $group context.

Covers empty collection, single document, multiple groups, large groups,
pipeline interactions, compound _id, multiple accumulators, and stage contexts
($bucket, $bucketAuto).
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Empty Collection]: empty collection produces no group output.
LAST_EMPTY_COLLECTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "empty_collection",
        docs=None,
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
        ],
        expected=[],
        msg="$last on empty collection should produce no output",
    ),
    AccumulatorTestCase(
        "all_filtered_out",
        docs=[
            {"_id": 0, "cat": "A", "v": 10},
            {"_id": 1, "cat": "A", "v": 20},
        ],
        pipeline=[
            {"$match": {"cat": "Z"}},
            {"$group": {"_id": "$cat", "result": {"$last": "$v"}}},
        ],
        expected=[],
        msg="$last should produce no output when all documents are filtered out",
    ),
]

# Property [Single Document]: $last on a single-document group returns that
# document's value.
LAST_SINGLE_DOCUMENT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "single_document",
        docs=[{"_id": 0, "v": 42}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 42}],
        msg="$last should return value from single document",
    ),
    AccumulatorTestCase(
        "single_per_group",
        docs=[
            {"_id": 0, "cat": "A", "v": 10},
            {"_id": 1, "cat": "B", "v": 20},
            {"_id": 2, "cat": "C", "v": 30},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": "$cat", "result": {"$last": "$v"}}},
            {"$sort": {"_id": 1}},
            {"$project": {"result": 1}},
        ],
        expected=[
            {"_id": "A", "result": 10},
            {"_id": "B", "result": 20},
            {"_id": "C", "result": 30},
        ],
        msg="$last should return correct value when each group has one document",
    ),
]

# Property [Multiple Groups]: $last computes correct last value per group
# independently.
LAST_MULTIPLE_GROUPS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "different_group_sizes",
        docs=[
            {"_id": 0, "cat": "A", "v": 1},
            {"_id": 1, "cat": "A", "v": 2},
            {"_id": 2, "cat": "A", "v": 3},
            {"_id": 3, "cat": "B", "v": 10},
            {"_id": 4, "cat": "B", "v": 20},
            {"_id": 5, "cat": "C", "v": 100},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": "$cat", "result": {"$last": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": 3},
            {"_id": "B", "result": 20},
            {"_id": "C", "result": 100},
        ],
        msg="$last should return correct last value for groups of different sizes",
    ),
    AccumulatorTestCase(
        "different_types_per_group",
        docs=[
            {"_id": 0, "cat": "int", "v": 10},
            {"_id": 1, "cat": "int", "v": 20},
            {"_id": 2, "cat": "str", "v": "hello"},
            {"_id": 3, "cat": "str", "v": "world"},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": "$cat", "result": {"$last": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "int", "result": 20},
            {"_id": "str", "result": "world"},
        ],
        msg="$last should return correct type per group",
    ),
    AccumulatorTestCase(
        "mixed_null_groups",
        docs=[
            {"_id": 0, "cat": "A", "v": None},
            {"_id": 1, "cat": "A", "v": None},
            {"_id": 2, "cat": "B", "v": 10},
            {"_id": 3, "cat": "B", "v": 20},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": "$cat", "result": {"$last": "$v"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "result": None},
            {"_id": "B", "result": 20},
        ],
        msg="$last should return null for all-null group and value for numeric group",
    ),
]

# Property [Large Group]: $last returns the last value from a large group.
LAST_LARGE_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "large_group_1000",
        docs=[{"_id": i, "v": i} for i in range(1000)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 999}],
        msg="$last should return the value from the 1000th document",
    ),
]

# Property [Multiple Accumulators]: $last works correctly alongside other
# accumulators in the same $group stage.
LAST_MULTIPLE_ACCUMULATORS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "last_and_first",
        docs=[
            {"_id": 0, "v": 10},
            {"_id": 1, "v": 20},
            {"_id": 2, "v": 30},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "last": {"$last": "$v"},
                    "first": {"$first": "$v"},
                }
            },
            {"$project": {"_id": 0, "last": 1, "first": 1}},
        ],
        expected=[{"last": 30, "first": 10}],
        msg="$last and $first should return different values on same field",
    ),
    AccumulatorTestCase(
        "last_on_two_fields",
        docs=[
            {"_id": 0, "a": 1, "b": "x"},
            {"_id": 1, "a": 2, "b": "y"},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "lastA": {"$last": "$a"},
                    "lastB": {"$last": "$b"},
                }
            },
            {"$project": {"_id": 0, "lastA": 1, "lastB": 1}},
        ],
        expected=[{"lastA": 2, "lastB": "y"}],
        msg="$last should return correct values for multiple fields",
    ),
    AccumulatorTestCase(
        "last_and_sum",
        docs=[
            {"_id": 0, "v": 10},
            {"_id": 1, "v": 20},
            {"_id": 2, "v": 30},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "last": {"$last": "$v"},
                    "total": {"$sum": "$v"},
                }
            },
            {"$project": {"_id": 0, "last": 1, "total": 1}},
        ],
        expected=[{"last": 30, "total": 60}],
        msg="$last passthrough and $sum computation should coexist",
    ),
]

# Property [Compound Group ID]: $last works with compound and expression-based
# group _id.
LAST_COMPOUND_ID_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "compound_id",
        docs=[
            {"_id": 0, "cat": "A", "sub": "x", "v": 1},
            {"_id": 1, "cat": "A", "sub": "x", "v": 2},
            {"_id": 2, "cat": "B", "sub": "y", "v": 10},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": {"cat": "$cat", "sub": "$sub"},
                    "result": {"$last": "$v"},
                }
            },
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": {"cat": "A", "sub": "x"}, "result": 2},
            {"_id": {"cat": "B", "sub": "y"}, "result": 10},
        ],
        msg="$last should work with compound group _id",
    ),
    AccumulatorTestCase(
        "expression_id",
        docs=[
            {"_id": 0, "cat": "hello", "v": 1},
            {"_id": 1, "cat": "hello", "v": 2},
            {"_id": 2, "cat": "world", "v": 10},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": {"$toUpper": "$cat"},
                    "result": {"$last": "$v"},
                }
            },
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "HELLO", "result": 2},
            {"_id": "WORLD", "result": 10},
        ],
        msg="$last should work with expression-based group _id",
    ),
]

# Property [Pipeline Interactions]: $last works correctly when preceded by
# various pipeline stages.
LAST_PIPELINE_INTERACTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "after_match",
        docs=[
            {"_id": 0, "cat": "A", "v": 10},
            {"_id": 1, "cat": "B", "v": 20},
            {"_id": 2, "cat": "A", "v": 30},
        ],
        pipeline=[
            {"$match": {"cat": "A"}},
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 30}],
        msg="$last should work after $match filtering",
    ),
    AccumulatorTestCase(
        "after_project",
        docs=[
            {"_id": 0, "x": 10},
            {"_id": 1, "x": 20},
        ],
        pipeline=[
            {"$project": {"_id": 1, "v": "$x"}},
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$last": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 20}],
        msg="$last should work after $project field rename",
    ),
    AccumulatorTestCase(
        "after_unwind",
        docs=[
            {"_id": 0, "tags": ["a", "b"]},
            {"_id": 1, "tags": ["c"]},
        ],
        pipeline=[
            {"$unwind": "$tags"},
            {"$sort": {"_id": 1, "tags": 1}},
            {"$group": {"_id": None, "result": {"$last": "$tags"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": "c"}],
        msg="$last should work after $unwind",
    ),
]

# Property [Bucket Smoke]: $last works correctly in $bucket context.
LAST_BUCKET_SMOKE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_basic",
        docs=[
            {"_id": 0, "v": 10},
            {"_id": 1, "v": 20},
            {"_id": 2, "v": 30},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$last": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 30}],
        msg="$last should return last value in $bucket context",
    ),
]

# Property [BucketAuto Smoke]: $last works correctly in $bucketAuto context.
LAST_BUCKET_AUTO_SMOKE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_auto_basic",
        docs=[
            {"_id": 0, "v": 10},
            {"_id": 1, "v": 20},
            {"_id": 2, "v": 30},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$last": "$v"}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 30}],
        msg="$last should return last value in $bucketAuto context",
    ),
]

LAST_GROUP_CONTEXT_TESTS: list[AccumulatorTestCase] = (
    LAST_EMPTY_COLLECTION_TESTS
    + LAST_SINGLE_DOCUMENT_TESTS
    + LAST_MULTIPLE_GROUPS_TESTS
    + LAST_LARGE_GROUP_TESTS
    + LAST_MULTIPLE_ACCUMULATORS_TESTS
    + LAST_COMPOUND_ID_TESTS
    + LAST_PIPELINE_INTERACTION_TESTS
    + LAST_BUCKET_SMOKE_TESTS
    + LAST_BUCKET_AUTO_SMOKE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LAST_GROUP_CONTEXT_TESTS))
def test_last_group_context(collection, test_case: AccumulatorTestCase):
    """Test $last in group context with grouping behavior."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)
