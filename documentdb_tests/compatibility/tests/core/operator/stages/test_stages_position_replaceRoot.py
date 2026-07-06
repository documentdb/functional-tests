"""Tests for $replaceRoot composing with other stages at different pipeline positions."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Filtering Composition]: $replaceRoot composes with $match in either
# position, and only the promoted fields are visible to a following $match.
REPLACEROOT_POSITION_FILTER_TESTS: list[StageTestCase] = [
    StageTestCase(
        "filter_match_then_replace",
        docs=[
            {"_id": 1, "a": 10, "inner": {"x": 1}},
            {"_id": 2, "a": 30, "inner": {"x": 2}},
        ],
        pipeline=[
            {"$match": {"a": {"$gt": 15}}},
            {"$replaceRoot": {"newRoot": "$inner"}},
        ],
        expected=[{"x": 2}],
        msg="$replaceRoot should promote only documents kept by a preceding $match",
    ),
    StageTestCase(
        "filter_replace_then_match_new_field",
        docs=[
            {"_id": 1, "inner": {"x": 10}},
            {"_id": 2, "inner": {"x": 20}},
        ],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$match": {"x": {"$gt": 15}}},
        ],
        expected=[{"x": 20}],
        msg="$replaceRoot should expose promoted fields to a following $match",
    ),
    StageTestCase(
        "filter_replace_then_match_dropped_field",
        docs=[{"_id": 1, "inner": {"x": 10}, "keep": "orig"}],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$match": {"keep": "orig"}},
        ],
        expected=[],
        msg="$match on a field dropped by a preceding $replaceRoot should return empty",
    ),
]

# Property [Reshape Composition]: $sort and $project after $replaceRoot operate
# on the promoted document shape, not the original input.
REPLACEROOT_POSITION_RESHAPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "reshape_replace_then_sort",
        docs=[
            {"_id": 1, "x": 1, "inner": {"x": 30}},
            {"_id": 2, "x": 2, "inner": {"x": 10}},
            {"_id": 3, "x": 3, "inner": {"x": 20}},
        ],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$sort": {"x": 1}},
        ],
        expected=[{"x": 10}, {"x": 20}, {"x": 30}],
        msg="$sort after $replaceRoot should order by the promoted field, not the outer one",
    ),
    StageTestCase(
        "reshape_replace_then_project",
        docs=[{"_id": 1, "x": 99, "inner": {"x": 10, "y": 20, "z": 30}}],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$project": {"x": 1}},
        ],
        expected=[{"x": 10}],
        msg="$project after $replaceRoot should keep the promoted field, not the outer one",
    ),
    StageTestCase(
        "reshape_merge_objects_then_project",
        docs=[{"_id": 1, "a": 1, "extra": {"b": 2}}],
        pipeline=[
            {"$replaceRoot": {"newRoot": {"$mergeObjects": ["$$ROOT", "$extra"]}}},
            {"$project": {"a": 1, "b": 1}},
        ],
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="$project should see fields grafted onto the input by $mergeObjects in $replaceRoot",
    ),
]

# Property [Grouping Composition]: a following $group keys on the promoted _id
# or its absence, and a preceding $group's accumulator output can be promoted.
REPLACEROOT_POSITION_GROUP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "group_replace_drops_id_then_group",
        docs=[
            {"_id": 1, "inner": {"x": 10}},
            {"_id": 2, "inner": {"x": 20}},
        ],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$group": {"_id": "$_id", "c": {"$sum": 1}}},
        ],
        expected=[{"_id": None, "c": 2}],
        msg="$group after $replaceRoot should bucket under null when the promoted root lacks _id",
    ),
    StageTestCase(
        "group_replace_promotes_own_id_then_group",
        docs=[
            {"_id": 1, "inner": {"_id": 99, "x": 10}},
            {"_id": 2, "inner": {"_id": 99, "x": 20}},
        ],
        pipeline=[
            {"$replaceRoot": {"newRoot": "$inner"}},
            {"$group": {"_id": "$_id", "c": {"$sum": 1}}},
        ],
        expected=[{"_id": 99, "c": 2}],
        msg="$group after $replaceRoot should bucket on the _id carried by the promoted document",
    ),
    StageTestCase(
        "group_then_replace_promotes_accumulator",
        docs=[
            {"_id": 1, "cat": "a", "v": 5},
            {"_id": 2, "cat": "a", "v": 7},
            {"_id": 3, "cat": "b", "v": 3},
        ],
        pipeline=[
            {"$group": {"_id": "$cat", "stats": {"$push": "$v"}}},
            {"$replaceRoot": {"newRoot": {"cat": "$_id", "values": "$stats"}}},
            {"$sort": {"cat": 1}},
        ],
        expected=[
            {"cat": "a", "values": [5, 7]},
            {"cat": "b", "values": [3]},
        ],
        msg="$replaceRoot should promote a document constructed from $group accumulator output",
    ),
]

# Property [Flattening Composition]: $replaceRoot composes with $unwind to
# promote each element of an array of sub-documents to the top level, the
# canonical array-flattening pipeline idiom.
REPLACEROOT_POSITION_FLATTEN_TESTS: list[StageTestCase] = [
    StageTestCase(
        "flatten_unwind_then_replace",
        docs=[{"_id": 1, "items": [{"name": "a"}, {"name": "b"}]}],
        pipeline=[
            {"$unwind": "$items"},
            {"$replaceRoot": {"newRoot": "$items"}},
        ],
        expected=[{"name": "a"}, {"name": "b"}],
        msg="$replaceRoot should promote each array element produced by a preceding $unwind",
    ),
]

REPLACEROOT_POSITION_TESTS: list[StageTestCase] = (
    REPLACEROOT_POSITION_FILTER_TESTS
    + REPLACEROOT_POSITION_RESHAPE_TESTS
    + REPLACEROOT_POSITION_GROUP_TESTS
    + REPLACEROOT_POSITION_FLATTEN_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REPLACEROOT_POSITION_TESTS))
def test_stages_position_replaceRoot_cases(collection, test_case: StageTestCase):
    """Test $replaceRoot composing with other stages at different pipeline positions."""
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
