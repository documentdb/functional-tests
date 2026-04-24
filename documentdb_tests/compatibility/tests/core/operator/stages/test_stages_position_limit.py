"""Tests for $limit composing with other stages at different pipeline positions."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_MAX

# Property [Sort + Limit]: $sort followed by $limit returns the correct N
# documents in sorted order, including when non-reshaping stages like
# $addFields or $match appear between them, and when reshaping stages like
# $unwind or $group appear between them.
LIMIT_SORT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sort_then_limit",
        docs=[{"_id": i, "v": 10 - i} for i in range(1, 6)],
        pipeline=[{"$sort": {"v": 1}}, {"$limit": 3}],
        expected=[{"_id": 5, "v": 5}, {"_id": 4, "v": 6}, {"_id": 3, "v": 7}],
        msg="$sort + $limit should return the N smallest documents",
    ),
    StageTestCase(
        "sort_addfields_limit",
        docs=[{"_id": i, "v": 10 - i} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$addFields": {"w": 1}},
            {"$limit": 3},
        ],
        expected=[
            {"_id": 5, "v": 5, "w": 1},
            {"_id": 4, "v": 6, "w": 1},
            {"_id": 3, "v": 7, "w": 1},
        ],
        msg="$sort + $addFields + $limit should preserve sorted order",
    ),
    StageTestCase(
        "sort_match_limit",
        docs=[{"_id": i, "v": 10 - i} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$match": {"v": {"$gte": 6}}},
            {"$limit": 2},
        ],
        expected=[{"_id": 4, "v": 6}, {"_id": 3, "v": 7}],
        msg="$sort + $match + $limit should return correct results",
    ),
    StageTestCase(
        "sort_unwind_limit",
        docs=[
            {"_id": 1, "v": 3, "arr": [1, 2]},
            {"_id": 2, "v": 1, "arr": [3]},
            {"_id": 3, "v": 2, "arr": [4, 5]},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$unwind": "$arr"},
            {"$limit": 2},
        ],
        expected=[{"_id": 2, "v": 1, "arr": 3}, {"_id": 3, "v": 2, "arr": 4}],
        msg="$unwind between $sort and $limit should produce correct results",
    ),
    StageTestCase(
        "sort_group_limit",
        docs=[{"_id": i, "v": 10 - i} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$group": {"_id": None, "count": {"$sum": 1}}},
            {"$limit": 1},
        ],
        expected=[{"_id": None, "count": 5}],
        msg="$group between $sort and $limit should produce correct results",
    ),
    StageTestCase(
        "multiple_sort_limit_pairs",
        docs=[{"_id": i, "v": 10 - i} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$limit": 4},
            {"$sort": {"v": -1}},
            {"$limit": 2},
        ],
        expected=[{"_id": 2, "v": 8}, {"_id": 3, "v": 7}],
        msg="Multiple sort+limit pairs should each produce correct results",
    ),
]

# Property [Skip Interaction]: $limit followed by $skip reduces output by the
# skip amount, and $skip followed by $limit skips first then limits.
LIMIT_SKIP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "limit_then_skip",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[{"$sort": {"_id": 1}}, {"$limit": 3}, {"$skip": 1}],
        expected=[{"_id": 2}, {"_id": 3}],
        msg="$limit then $skip should reduce output by skip amount",
    ),
    StageTestCase(
        "limit_then_skip_exceeds",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[{"$limit": 3}, {"$skip": 5}],
        expected=[],
        msg="$limit then $skip where skip >= limit should return 0 documents",
    ),
    StageTestCase(
        "skip_then_limit",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[{"$sort": {"_id": 1}}, {"$skip": 2}, {"$limit": 2}],
        expected=[{"_id": 3}, {"_id": 4}],
        msg="$skip then $limit should skip first then limit remaining",
    ),
    StageTestCase(
        "skip_limit_both_int64_max",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": INT64_MAX}, {"$limit": INT64_MAX}],
        expected=[],
        msg="$skip and $limit both at int64 max should return 0 documents",
    ),
]

# Property [Facet Interaction]: each $facet sub-pipeline applies its own
# $limit independently, and $limit after $facet limits the single output
# document.
LIMIT_FACET_TESTS: list[StageTestCase] = [
    StageTestCase(
        "facet_independent_limits",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$facet": {
                    "a": [{"$limit": 2}],
                    "b": [{"$limit": 3}],
                }
            },
        ],
        expected=[
            {
                "a": [{"_id": 1}, {"_id": 2}],
                "b": [{"_id": 1}, {"_id": 2}, {"_id": 3}],
            }
        ],
        msg="Each $facet sub-pipeline should apply its own $limit independently",
    ),
    StageTestCase(
        "limit_after_facet",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$facet": {"a": [{"$limit": 2}]}},
            {"$limit": 1},
        ],
        expected=[{"a": [{"_id": 1}, {"_id": 2}]}],
        msg="$limit after $facet should limit the single output document",
    ),
]

# Property [Match + Limit]: $match followed by $limit returns at most N
# documents from the filtered set, and $limit followed by $match filters
# only the limited set.
LIMIT_MATCH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "match_then_limit",
        docs=[{"_id": i, "v": i % 2} for i in range(1, 6)],
        pipeline=[
            {"$match": {"v": 1}},
            {"$sort": {"_id": 1}},
            {"$limit": 2},
        ],
        expected=[{"_id": 1, "v": 1}, {"_id": 3, "v": 1}],
        msg="$match + $limit should return at most N matching documents",
    ),
    StageTestCase(
        "limit_then_match",
        docs=[{"_id": i, "v": i % 2} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$limit": 3},
            {"$match": {"v": 1}},
        ],
        expected=[{"_id": 1, "v": 1}, {"_id": 3, "v": 1}],
        msg="$limit + $match should filter only the limited set",
    ),
    StageTestCase(
        "match_then_limit_no_matches",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$match": {"v": 99}}, {"$limit": 5}],
        expected=[],
        msg="$match + $limit with no matches should return empty",
    ),
]

# Property [Project + Limit]: $project followed by $limit returns at most N
# projected documents, and $limit followed by $project limits before
# projecting.
LIMIT_PROJECT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "project_then_limit",
        docs=[{"_id": i, "a": i, "b": "x"} for i in range(1, 6)],
        pipeline=[
            {"$project": {"a": 1}},
            {"$sort": {"_id": 1}},
            {"$limit": 2},
        ],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        msg="$project + $limit should return at most N projected documents",
    ),
    StageTestCase(
        "limit_then_project",
        docs=[{"_id": i, "a": i, "b": "x"} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$limit": 2},
            {"$project": {"a": 1}},
        ],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        msg="$limit + $project should limit before projecting",
    ),
]

# Property [Group + Limit]: $group followed by $limit returns at most N
# grouped results.
LIMIT_GROUP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "group_then_limit",
        docs=[
            {"_id": 1, "cat": "a", "v": 1},
            {"_id": 2, "cat": "b", "v": 2},
            {"_id": 3, "cat": "a", "v": 3},
            {"_id": 4, "cat": "c", "v": 4},
        ],
        pipeline=[
            {"$group": {"_id": "$cat", "total": {"$sum": "$v"}}},
            {"$sort": {"_id": 1}},
            {"$limit": 2},
        ],
        expected=[{"_id": "a", "total": 4}, {"_id": "b", "total": 2}],
        msg="$group + $limit should return at most N grouped results",
    ),
]

# Property [Lookup + Limit]: $lookup followed by $limit returns at most N
# joined documents.
LIMIT_LOOKUP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "lookup_then_limit",
        docs=[{"_id": 1, "code": "a"}, {"_id": 2, "code": "b"}, {"_id": 3, "code": "c"}],
        setup=lambda c: c.database["lookup_limit_foreign"].insert_many(
            [{"_id": 1, "code": "a", "v": 10}, {"_id": 2, "code": "b", "v": 20}]
        ),
        pipeline=[
            {
                "$lookup": {
                    "from": "lookup_limit_foreign",
                    "localField": "code",
                    "foreignField": "code",
                    "as": "matched",
                }
            },
            {"$sort": {"_id": 1}},
            {"$limit": 2},
        ],
        expected=[
            {"_id": 1, "code": "a", "matched": [{"_id": 1, "code": "a", "v": 10}]},
            {"_id": 2, "code": "b", "matched": [{"_id": 2, "code": "b", "v": 20}]},
        ],
        msg="$lookup + $limit should return at most N joined documents",
    ),
]

LIMIT_POSITION_TESTS = (
    LIMIT_SORT_TESTS
    + LIMIT_SKIP_TESTS
    + LIMIT_FACET_TESTS
    + LIMIT_MATCH_TESTS
    + LIMIT_PROJECT_TESTS
    + LIMIT_GROUP_TESTS
    + LIMIT_LOOKUP_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(LIMIT_POSITION_TESTS))
def test_stages_position_limit(collection, test_case: StageTestCase):
    """Test $limit composing with other stages at different pipeline positions."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
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
