"""Tests for $skip composing with other stages at different pipeline positions."""

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

# Property [Sort + Skip]: $skip drops the first N documents from the sorted
# stream regardless of intervening stages between $sort and $skip.
SKIP_SORT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "sort_then_skip",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[{"$sort": {"_id": 1}}, {"$skip": 3}],
        expected=[{"_id": 4}, {"_id": 5}],
        msg="$sort + $skip should drop the first N sorted documents",
    ),
    StageTestCase(
        "sort_addfields_skip",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$addFields": {"w": 1}},
            {"$skip": 3},
        ],
        expected=[
            {"_id": 4, "w": 1},
            {"_id": 5, "w": 1},
        ],
        msg="$sort + $addFields + $skip should preserve sorted order",
    ),
    StageTestCase(
        "sort_match_skip",
        docs=[{"_id": i, "v": i % 2} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$match": {"v": 1}},
            {"$skip": 1},
        ],
        expected=[{"_id": 3, "v": 1}, {"_id": 5, "v": 1}],
        msg="$sort + $match + $skip should return correct results",
    ),
    StageTestCase(
        "sort_unwind_skip",
        docs=[
            {"_id": 1, "v": 3, "arr": [1, 2]},
            {"_id": 2, "v": 1, "arr": [3]},
            {"_id": 3, "v": 2, "arr": [4, 5]},
        ],
        pipeline=[
            {"$sort": {"v": 1}},
            {"$unwind": "$arr"},
            {"$skip": 2},
        ],
        expected=[
            {"_id": 3, "v": 2, "arr": 5},
            {"_id": 1, "v": 3, "arr": 1},
            {"_id": 1, "v": 3, "arr": 2},
        ],
        msg="$unwind between $sort and $skip should produce correct results",
    ),
    StageTestCase(
        "sort_group_skip",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "count": {"$sum": 1}}},
            {"$skip": 1},
        ],
        expected=[],
        msg="$group producing one doc + $skip 1 should return empty",
    ),
    StageTestCase(
        "multiple_sort_skip_pairs",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$skip": 1},
            {"$sort": {"_id": -1}},
            {"$skip": 1},
        ],
        expected=[
            {"_id": 4},
            {"_id": 3},
            {"_id": 2},
        ],
        msg="Multiple sort+skip pairs should each produce correct results",
    ),
]

# Property [Limit Interaction]: $skip followed by $limit skips first then
# limits, and $limit followed by $skip limits first then skips.
SKIP_LIMIT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "skip_then_limit",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[{"$sort": {"_id": 1}}, {"$skip": 2}, {"$limit": 2}],
        expected=[{"_id": 3}, {"_id": 4}],
        msg="$skip then $limit should skip first then limit remaining",
    ),
    StageTestCase(
        "limit_then_skip",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[{"$sort": {"_id": 1}}, {"$limit": 3}, {"$skip": 1}],
        expected=[{"_id": 2}, {"_id": 3}],
        msg="$limit then $skip should limit first then skip from limited set",
    ),
    StageTestCase(
        "skip_zero_then_limit",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[{"$sort": {"_id": 1}}, {"$skip": 0}, {"$limit": 3}],
        expected=[{"_id": 1}, {"_id": 2}, {"_id": 3}],
        msg="$skip 0 + $limit should pass all documents to $limit",
    ),
    StageTestCase(
        "skip_exceeds_limit",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[{"$limit": 3}, {"$skip": 5}],
        expected=[],
        msg="$skip exceeding $limit should return empty",
    ),
    StageTestCase(
        "skip_limit_both_int64_max",
        docs=[{"_id": 1}],
        pipeline=[{"$skip": INT64_MAX}, {"$limit": INT64_MAX}],
        expected=[],
        msg="$skip and $limit both at int64 max should return empty",
    ),
]

# Property [Facet Interaction]: $skip operates independently within each
# $facet sub-pipeline and on the $facet output.
SKIP_FACET_TESTS: list[StageTestCase] = [
    StageTestCase(
        "facet_independent_skips",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$facet": {
                    "a": [{"$skip": 2}],
                    "b": [{"$skip": 4}],
                }
            },
        ],
        expected=[
            {
                "a": [{"_id": 3}, {"_id": 4}, {"_id": 5}],
                "b": [{"_id": 5}],
            }
        ],
        msg="Each $facet sub-pipeline should apply its own $skip independently",
    ),
    StageTestCase(
        "skip_after_facet",
        docs=[{"_id": i} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$facet": {"a": [{"$skip": 2}]}},
            {"$skip": 1},
        ],
        expected=[],
        msg="$skip after $facet should skip the single output document",
    ),
]

# Property [Match + Skip]: $match followed by $skip drops the first N
# matching documents, and $skip followed by $match skips first then filters.
SKIP_MATCH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "match_then_skip",
        docs=[{"_id": i, "v": i % 2} for i in range(1, 6)],
        pipeline=[
            {"$match": {"v": 1}},
            {"$sort": {"_id": 1}},
            {"$skip": 1},
        ],
        expected=[{"_id": 3, "v": 1}, {"_id": 5, "v": 1}],
        msg="$match + $skip should drop the first N matching documents",
    ),
    StageTestCase(
        "skip_then_match",
        docs=[{"_id": i, "v": i % 2} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$skip": 2},
            {"$match": {"v": 1}},
        ],
        expected=[{"_id": 3, "v": 1}, {"_id": 5, "v": 1}],
        msg="$skip + $match should skip first then filter remaining",
    ),
    StageTestCase(
        "match_then_skip_no_matches",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$match": {"v": 99}}, {"$skip": 1}],
        expected=[],
        msg="$match + $skip with no matches should return empty",
    ),
]

# Property [Project + Skip]: $project followed by $skip drops the first N
# projected documents, and $skip followed by $project skips before projecting.
SKIP_PROJECT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "project_then_skip",
        docs=[{"_id": i, "a": i, "b": "x"} for i in range(1, 6)],
        pipeline=[
            {"$project": {"a": 1}},
            {"$sort": {"_id": 1}},
            {"$skip": 3},
        ],
        expected=[{"_id": 4, "a": 4}, {"_id": 5, "a": 5}],
        msg="$project + $skip should drop the first N projected documents",
    ),
    StageTestCase(
        "skip_then_project",
        docs=[{"_id": i, "a": i, "b": "x"} for i in range(1, 6)],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$skip": 3},
            {"$project": {"a": 1}},
        ],
        expected=[{"_id": 4, "a": 4}, {"_id": 5, "a": 5}],
        msg="$skip + $project should skip before projecting",
    ),
]

# Property [Group + Skip]: $group followed by $skip drops the first N grouped
# results.
SKIP_GROUP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "group_then_skip",
        docs=[
            {"_id": 1, "cat": "a", "v": 1},
            {"_id": 2, "cat": "b", "v": 2},
            {"_id": 3, "cat": "a", "v": 3},
            {"_id": 4, "cat": "c", "v": 4},
        ],
        pipeline=[
            {"$group": {"_id": "$cat", "total": {"$sum": "$v"}}},
            {"$sort": {"_id": 1}},
            {"$skip": 1},
        ],
        expected=[{"_id": "b", "total": 2}, {"_id": "c", "total": 4}],
        msg="$group + $skip should drop the first N grouped results",
    ),
]

# Property [Lookup + Skip]: $lookup followed by $skip drops the first N
# joined documents.
SKIP_LOOKUP_TESTS: list[StageTestCase] = [
    StageTestCase(
        "lookup_then_skip",
        docs=[{"_id": 1, "code": "a"}, {"_id": 2, "code": "b"}, {"_id": 3, "code": "c"}],
        setup=lambda c: c.database["lookup_skip_foreign"].insert_many(
            [{"_id": 1, "code": "a", "v": 10}, {"_id": 2, "code": "b", "v": 20}]
        ),
        pipeline=[
            {
                "$lookup": {
                    "from": "lookup_skip_foreign",
                    "localField": "code",
                    "foreignField": "code",
                    "as": "matched",
                }
            },
            {"$sort": {"_id": 1}},
            {"$skip": 1},
        ],
        expected=[
            {"_id": 2, "code": "b", "matched": [{"_id": 2, "code": "b", "v": 20}]},
            {"_id": 3, "code": "c", "matched": []},
        ],
        msg="$lookup + $skip should drop the first N joined documents",
    ),
]

# Property [Pagination]: $sort + $skip + $limit produces correct,
# non-overlapping pages that together cover the full result set.
SKIP_PAGINATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "page_1",
        docs=[{"_id": i, "v": i * 10} for i in range(1, 8)],
        pipeline=[{"$sort": {"_id": 1}}, {"$skip": 0}, {"$limit": 3}],
        expected=[
            {"_id": 1, "v": 10},
            {"_id": 2, "v": 20},
            {"_id": 3, "v": 30},
        ],
        msg="First page should return the first 3 documents",
    ),
    StageTestCase(
        "page_2",
        docs=[{"_id": i, "v": i * 10} for i in range(1, 8)],
        pipeline=[{"$sort": {"_id": 1}}, {"$skip": 3}, {"$limit": 3}],
        expected=[
            {"_id": 4, "v": 40},
            {"_id": 5, "v": 50},
            {"_id": 6, "v": 60},
        ],
        msg="Second page should return the next 3 documents",
    ),
    StageTestCase(
        "page_3_partial",
        docs=[{"_id": i, "v": i * 10} for i in range(1, 8)],
        pipeline=[{"$sort": {"_id": 1}}, {"$skip": 6}, {"$limit": 3}],
        expected=[{"_id": 7, "v": 70}],
        msg="Final partial page should return remaining documents",
    ),
    StageTestCase(
        "page_beyond_end",
        docs=[{"_id": i, "v": i * 10} for i in range(1, 8)],
        pipeline=[{"$sort": {"_id": 1}}, {"$skip": 9}, {"$limit": 3}],
        expected=[],
        msg="Page beyond end of data should return empty",
    ),
]

SKIP_POSITION_TESTS = (
    SKIP_SORT_TESTS
    + SKIP_LIMIT_TESTS
    + SKIP_FACET_TESTS
    + SKIP_MATCH_TESTS
    + SKIP_PROJECT_TESTS
    + SKIP_GROUP_TESTS
    + SKIP_LOOKUP_TESTS
    + SKIP_PAGINATION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(SKIP_POSITION_TESTS))
def test_stages_position_skip(collection, test_case: StageTestCase):
    """Test $skip composing with other stages at different pipeline positions."""
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
