"""Tests for $planCacheStats output behavior."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Exists, Gte, IsType, NotExists
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ViewCollection,
)

# Property [Empty Plan Cache Behavior]: when no plan cache entries exist for
# the collection, the stage returns an empty result set.
EMPTY_PLAN_CACHE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_freshly_created_collection",
        docs=[],
        pipeline=[{"$planCacheStats": {}}],
        expected=[],
        msg="$planCacheStats on a freshly created collection should return empty",
    ),
    StageTestCase(
        "empty_collection_with_documents_no_queries",
        docs=[{"_id": 1, "value": 10}],
        pipeline=[{"$planCacheStats": {}}],
        expected=[],
        msg=(
            "$planCacheStats on a collection with documents but no prior"
            " queries should return empty"
        ),
    ),
]

# Property [Output Document Structure]: each plan cache entry has the expected
# field types, structure, and required fields. Multiple distinct query shapes
# produce multiple cache entries.
OUTPUT_STRUCTURE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "output_document_structure",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", 1)])],
        docs=[{"_id": i, "a": i, "b": i} for i in range(10)],
        # Warm the plan cache by running a query that triggers index competition.
        setup=lambda c: list(c.find({"a": 5, "b": 5})),
        pipeline=[{"$planCacheStats": {}}],
        expected={
            "_id": NotExists(),
            "version": IsType("string"),
            "planCacheShapeHash": IsType("string"),
            "planCacheKey": IsType("string"),
            "estimatedSizeBytes": IsType("long"),
            "works": IsType("long"),
            "timeOfCreation": IsType("date"),
            "isActive": IsType("bool"),
            "indexFilterSet": IsType("bool"),
            "host": IsType("string"),
            "createdFromQuery": IsType("object"),
            "cachedPlan": IsType("object"),
            "shard": NotExists(),
            "queryHash": IsType("string"),
            "creationExecStats": Exists(),
            "candidatePlanScores": Exists(),
        },
        msg="$planCacheStats output document structure",
    ),
    StageTestCase(
        "multiple_distinct_query_shapes",
        indexes=[IndexModel([("a", 1)]), IndexModel([("b", 1)])],
        docs=[{"_id": i, "a": i, "b": i} for i in range(10)],
        setup=lambda c: (
            list(c.find({"a": 5, "b": 5})),
            list(c.find({"a": {"$gt": 3}, "b": 1})),
        ),
        pipeline=[{"$planCacheStats": {}}, {"$count": "total"}],
        expected={"total": Gte(2)},
        msg="multiple distinct query shapes should produce multiple cache entries",
    ),
]

# Property [Collection Type Behavior]: $planCacheStats succeeds on capped
# collections, views, and the regular fixture collection.
COLLECTION_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "collection_type_capped",
        target_collection=CappedCollection(size=1_048_576),
        docs=[],
        pipeline=[{"$planCacheStats": {}}],
        expected=[],
        msg="$planCacheStats on capped collection should succeed",
    ),
    StageTestCase(
        "collection_type_view",
        target_collection=ViewCollection(),
        docs=[],
        pipeline=[{"$planCacheStats": {}}],
        expected=[],
        msg="$planCacheStats on view should succeed",
    ),
]

PLANCACHESTATS_OUTPUT_TESTS = (
    EMPTY_PLAN_CACHE_TESTS + OUTPUT_STRUCTURE_TESTS + COLLECTION_TYPE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(PLANCACHESTATS_OUTPUT_TESTS))
def test_planCacheStats_output(collection: Collection, test_case: StageTestCase):
    """Test $planCacheStats output behavior."""
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
