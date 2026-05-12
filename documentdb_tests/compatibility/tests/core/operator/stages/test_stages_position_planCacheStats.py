"""Tests for $planCacheStats pipeline position and composition."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FACET_PIPELINE_INVALID_STAGE_ERROR,
    NOT_FIRST_STAGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Exists, Gte, NotExists

# Property [$facet Restriction Error]: $planCacheStats inside a $facet stage
# produces an error regardless of its position in the sub-pipeline.
FACET_RESTRICTION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "facet_first_in_sub_pipeline",
        docs=[{"_id": 1}],
        pipeline=[{"$facet": {"stats": [{"$planCacheStats": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$planCacheStats first in $facet sub-pipeline should error",
    ),
    StageTestCase(
        "facet_not_first_in_sub_pipeline",
        docs=[{"_id": 1}],
        pipeline=[{"$facet": {"stats": [{"$match": {}}, {"$planCacheStats": {}}]}}],
        error_code=FACET_PIPELINE_INVALID_STAGE_ERROR,
        msg="$planCacheStats not first in $facet sub-pipeline should error",
    ),
]

# Property [Pipeline Position Errors]: $planCacheStats must be the first
# stage in a pipeline.
PIPELINE_POSITION_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "position_not_first_after_project",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"a": 1}}, {"$planCacheStats": {}}],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="$planCacheStats not as first stage should error",
    ),
    StageTestCase(
        "position_second_plancachestats",
        docs=[{"_id": 1}],
        pipeline=[{"$planCacheStats": {}}, {"$planCacheStats": {}}],
        error_code=NOT_FIRST_STAGE_ERROR,
        msg="a second $planCacheStats in the same pipeline should error",
    ),
]

# Property [Multi-Stage Composition Empty Cache]: $planCacheStats composes
# correctly with subsequent stages when the plan cache is empty.
MULTI_STAGE_EMPTY_CACHE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_cache_followed_by_match",
        docs=[{"_id": 1}],
        pipeline=[{"$planCacheStats": {}}, {"$match": {"isActive": True}}],
        expected=[],
        msg="$planCacheStats followed by $match on empty cache should return empty",
    ),
    StageTestCase(
        "empty_cache_followed_by_project",
        docs=[{"_id": 1}],
        pipeline=[{"$planCacheStats": {}}, {"$project": {"planCacheKey": 1}}],
        expected=[],
        msg="$planCacheStats followed by $project on empty cache should return empty",
    ),
    StageTestCase(
        "empty_cache_followed_by_count",
        docs=[{"_id": 1}],
        pipeline=[{"$planCacheStats": {}}, {"$count": "total"}],
        expected=[],
        msg="$planCacheStats followed by $count on empty cache should return empty",
    ),
    StageTestCase(
        "empty_cache_followed_by_sort",
        docs=[{"_id": 1}],
        pipeline=[
            {"$planCacheStats": {}},
            {"$sort": {"estimatedSizeBytes": -1}},
        ],
        expected=[],
        msg="$planCacheStats followed by $sort on empty cache should return empty",
    ),
    StageTestCase(
        "empty_cache_followed_by_group",
        docs=[{"_id": 1}],
        pipeline=[
            {"$planCacheStats": {}},
            {"$group": {"_id": "$isActive", "count": {"$sum": 1}}},
        ],
        expected=[],
        msg="$planCacheStats followed by $group on empty cache should return empty",
    ),
    StageTestCase(
        "empty_cache_followed_by_limit",
        docs=[{"_id": 1}],
        pipeline=[{"$planCacheStats": {}}, {"$limit": 5}],
        expected=[],
        msg="$planCacheStats followed by $limit on empty cache should return empty",
    ),
]

# Property [Multi-Stage Composition Warmed Cache]: $planCacheStats composes
# correctly with subsequent stages when the plan cache has entries.
MULTI_STAGE_WARMED_CACHE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "warmed_cache_followed_by_match",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", 1)])],
        docs=[{"_id": i, "a": i, "b": i} for i in range(10)],
        setup=lambda c: list(c.find({"a": 5, "b": 5})),
        pipeline=[
            {"$planCacheStats": {}},
            {"$match": {"isActive": {"$exists": True}}},
        ],
        expected={"isActive": Exists()},
        msg="$match should filter to docs containing isActive",
    ),
    StageTestCase(
        "warmed_cache_followed_by_project",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", 1)])],
        docs=[{"_id": i, "a": i, "b": i} for i in range(10)],
        setup=lambda c: list(c.find({"a": 5, "b": 5})),
        pipeline=[
            {"$planCacheStats": {}},
            {"$project": {"planCacheKey": 1, "isActive": 1}},
        ],
        expected={"planCacheKey": Exists(), "isActive": Exists(), "cachedPlan": NotExists()},
        msg="$project should include only projected fields",
    ),
    StageTestCase(
        "warmed_cache_followed_by_count",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", 1)])],
        docs=[{"_id": i, "a": i, "b": i} for i in range(10)],
        setup=lambda c: list(c.find({"a": 5, "b": 5})),
        pipeline=[{"$planCacheStats": {}}, {"$count": "total"}],
        expected={"total": Gte(1)},
        msg="$count should produce at least 1",
    ),
    StageTestCase(
        "warmed_cache_followed_by_sort_limit",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", 1)])],
        docs=[{"_id": i, "a": i, "b": i} for i in range(10)],
        setup=lambda c: list(c.find({"a": 5, "b": 5})),
        pipeline=[
            {"$planCacheStats": {}},
            {"$sort": {"estimatedSizeBytes": -1}},
            {"$limit": 1},
        ],
        expected={"estimatedSizeBytes": Exists()},
        msg="$sort and $limit should return a doc with the sorted field",
    ),
    StageTestCase(
        "warmed_cache_followed_by_group",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", 1)])],
        docs=[{"_id": i, "a": i, "b": i} for i in range(10)],
        setup=lambda c: list(c.find({"a": 5, "b": 5})),
        pipeline=[
            {"$planCacheStats": {}},
            {"$group": {"_id": "$isActive", "count": {"$sum": 1}}},
        ],
        expected={"_id": Exists(), "count": Gte(1)},
        msg="$group should produce groups with counts",
    ),
]

ALL_TESTS = (
    FACET_RESTRICTION_ERROR_TESTS
    + PIPELINE_POSITION_ERROR_TESTS
    + MULTI_STAGE_EMPTY_CACHE_TESTS
    + MULTI_STAGE_WARMED_CACHE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(ALL_TESTS))
def test_planCacheStats_position(collection: Collection, test_case: StageTestCase):
    """Test $planCacheStats pipeline position and multi-stage composition."""
    coll = populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(coll)
    result = execute_command(
        coll,
        {
            "aggregate": coll.name,
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
