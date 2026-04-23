"""Tests for interesting $sort combinations with other pipeline stages."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Sort → Project → Group Field Visibility]: when $sort feeds into
# $project then $group, the projection controls which fields the downstream
# $group accumulator can see. Some server implementations optimize this
# pipeline shape by merging the sort into the group, which risks bypassing
# the intermediate projection and exposing fields that should have been
# removed. Using $first makes the $sort functionally necessary (it
# determines which document's value the accumulator picks) while still
# exercising the optimizer path.
SORT_PROJECT_GROUP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "inclusion_project_preserves_field_for_group",
        docs=[
            {"_id": 1, "cat": "a", "val": 10},
            {"_id": 2, "cat": "a", "val": 20},
            {"_id": 3, "cat": "b", "val": 30},
        ],
        pipeline=[
            {"$sort": {"val": -1}},
            {"$project": {"cat": 1, "val": 1}},
            {"$group": {"_id": "$cat", "top": {"$first": "$val"}}},
        ],
        expected=[
            {"_id": "a", "top": 20},
            {"_id": "b", "top": 30},
        ],
        msg="Inclusion projection that keeps a field should let $group $first see its value",
    ),
    StageTestCase(
        "inclusion_project_excludes_field_from_group",
        docs=[
            {"_id": 1, "cat": "a", "val": 10},
            {"_id": 2, "cat": "a", "val": 20},
            {"_id": 3, "cat": "b", "val": 30},
        ],
        pipeline=[
            {"$sort": {"val": -1}},
            {"$project": {"cat": 1}},
            {"$group": {"_id": "$cat", "top": {"$first": "$val"}}},
        ],
        expected=[
            {"_id": "a", "top": None},
            {"_id": "b", "top": None},
        ],
        msg="Inclusion projection that omits a field should make $group $first receive missing",
    ),
    StageTestCase(
        "exclusion_project_removes_unrelated_field",
        docs=[
            {"_id": 1, "cat": "a", "val": 10, "extra": "x"},
            {"_id": 2, "cat": "a", "val": 20, "extra": "y"},
            {"_id": 3, "cat": "b", "val": 30, "extra": "z"},
        ],
        pipeline=[
            {"$sort": {"val": -1}},
            {"$project": {"extra": 0}},
            {"$group": {"_id": "$cat", "top": {"$first": "$val"}}},
        ],
        expected=[
            {"_id": "a", "top": 20},
            {"_id": "b", "top": 30},
        ],
        msg="Exclusion projection removing an unrelated field should not affect $group $first",
    ),
    StageTestCase(
        "exclusion_project_removes_needed_field",
        docs=[
            {"_id": 1, "cat": "a", "val": 10},
            {"_id": 2, "cat": "a", "val": 20},
            {"_id": 3, "cat": "b", "val": 30},
        ],
        pipeline=[
            {"$sort": {"val": -1}},
            {"$project": {"val": 0}},
            {"$group": {"_id": "$cat", "top": {"$first": "$val"}}},
        ],
        expected=[
            {"_id": "a", "top": None},
            {"_id": "b", "top": None},
        ],
        msg=(
            "Exclusion projection removing the accumulated field should"
            " make $group $first receive missing"
        ),
    ),
]

# Property [Sort → Group Order-Dependent Accumulators]: $last in $group
# respects the document order established by a preceding $sort.
SORT_GROUP_ORDER_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sort_desc_group_last",
        docs=[
            {"_id": 1, "cat": "a", "val": 10},
            {"_id": 2, "cat": "a", "val": 30},
            {"_id": 3, "cat": "a", "val": 20},
            {"_id": 4, "cat": "b", "val": 5},
            {"_id": 5, "cat": "b", "val": 15},
        ],
        pipeline=[
            {"$sort": {"val": -1}},
            {"$group": {"_id": "$cat", "last_val": {"$last": "$val"}}},
        ],
        expected=[
            {"_id": "a", "last_val": 10},
            {"_id": "b", "last_val": 5},
        ],
        msg="Sort descending then $group with $last should pick the lowest value",
    ),
]

# Property [Sort → Limit/Skip Pagination]: $sort followed by $limit or
# $skip and $limit returns the correct documents in sorted order.
SORT_LIMIT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sort_limit_top_n",
        docs=[
            {"_id": 1, "val": 50},
            {"_id": 2, "val": 10},
            {"_id": 3, "val": 40},
            {"_id": 4, "val": 30},
            {"_id": 5, "val": 20},
        ],
        pipeline=[{"$sort": {"val": -1}}, {"$limit": 3}],
        expected=[
            {"_id": 1, "val": 50},
            {"_id": 3, "val": 40},
            {"_id": 4, "val": 30},
        ],
        msg="$sort descending then $limit should return the top N documents in order",
    ),
    StageTestCase(
        "sort_skip_limit_page",
        docs=[
            {"_id": 1, "val": 50},
            {"_id": 2, "val": 10},
            {"_id": 3, "val": 40},
            {"_id": 4, "val": 30},
            {"_id": 5, "val": 20},
        ],
        pipeline=[{"$sort": {"val": 1}}, {"$skip": 1}, {"$limit": 2}],
        expected=[
            {"_id": 5, "val": 20},
            {"_id": 4, "val": 30},
        ],
        msg="$sort then $skip then $limit should return the correct page window",
    ),
]

# Property [Sort → Unwind → Group Order Preservation]: sort order established
# before $unwind is preserved through array expansion for downstream
# order-dependent accumulators.
SORT_UNWIND_GROUP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sort_unwind_group_first",
        docs=[
            {"_id": 1, "cat": "a", "val": 30, "tags": ["x", "y"]},
            {"_id": 2, "cat": "a", "val": 10, "tags": ["z"]},
        ],
        pipeline=[
            {"$sort": {"val": -1}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$cat", "first_tag": {"$first": "$tags"}}},
        ],
        expected=[{"_id": "a", "first_tag": "x"}],
        msg="$first after $sort and $unwind should pick from the document that sorted first",
    ),
]

# Property [Match → Sort → Group Filter-Then-Pick]: $match narrows input before
# $sort establishes order for an order-dependent $group accumulator.
MATCH_SORT_GROUP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "match_sort_group_first",
        docs=[
            {"_id": 1, "cat": "a", "val": 5, "active": False},
            {"_id": 2, "cat": "a", "val": 30, "active": True},
            {"_id": 3, "cat": "a", "val": 20, "active": True},
            {"_id": 4, "cat": "b", "val": 10, "active": True},
        ],
        pipeline=[
            {"$match": {"active": True}},
            {"$sort": {"val": -1}},
            {"$group": {"_id": "$cat", "top": {"$first": "$val"}}},
        ],
        expected=[
            {"_id": "a", "top": 30},
            {"_id": "b", "top": 10},
        ],
        msg="$match filtering before $sort and $group $first should respect filtered sort order",
    ),
]

# Property [Sort → AddFields → Group Computed Override]: when $addFields
# overwrites the sort field with a computed value, the downstream $group
# accumulator should see the computed value, not the original. Some server
# implementations may optimize this pipeline shape in a way that bypasses
# the $addFields override.
SORT_ADDFIELDS_GROUP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sort_addfields_overwrites_sort_field",
        docs=[
            {"_id": 1, "cat": "a", "val": 10},
            {"_id": 2, "cat": "a", "val": 20},
            {"_id": 3, "cat": "b", "val": 30},
        ],
        pipeline=[
            {"$sort": {"val": -1}},
            {"$addFields": {"val": {"$multiply": ["$val", -1]}}},
            {"$group": {"_id": "$cat", "top": {"$first": "$val"}}},
        ],
        expected=[
            {"_id": "a", "top": -20},
            {"_id": "b", "top": -30},
        ],
        msg="$group $first should see the $addFields-computed value, not the original sort field",
    ),
]

STAGE_COMBINATIONS_SORT_TESTS = (
    SORT_PROJECT_GROUP_TESTS
    + SORT_GROUP_ORDER_TESTS
    + SORT_LIMIT_TESTS
    + SORT_UNWIND_GROUP_TESTS
    + MATCH_SORT_GROUP_TESTS
    + SORT_ADDFIELDS_GROUP_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(STAGE_COMBINATIONS_SORT_TESTS))
def test_stage_combinations_sort(collection, test_case: StageTestCase):
    """Test interesting $sort combinations with other pipeline stages."""
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
        ignore_doc_order=True,
    )
