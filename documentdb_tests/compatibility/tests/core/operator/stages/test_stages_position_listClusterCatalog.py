"""Tests for $listClusterCatalog pipeline position and composition."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.listClusterCatalog.utils.listClusterCatalog_helpers import (  # noqa: E501
    ListClusterCatalogTestCase,
    StageContext,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import LIST_CLUSTER_CATALOG_COLLECTION_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Exists, Gte, IsType, NotExists

# Property [Sub-pipeline Restriction]: $listClusterCatalog cannot appear
# inside sub-pipelines.
SUB_PIPELINE_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="inside_facet",
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [{"$facet": {"catalog": [{"$listClusterCatalog": {}}]}}],
            "cursor": {},
        },
        error_code=LIST_CLUSTER_CATALOG_COLLECTION_ERROR,
        msg="$listClusterCatalog inside $facet should produce a collection-level error",
    ),
    ListClusterCatalogTestCase(
        id="inside_lookup",
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$lookup": {
                        "from": "other",
                        "pipeline": [{"$listClusterCatalog": {}}],
                        "as": "result",
                    }
                }
            ],
            "cursor": {},
        },
        error_code=LIST_CLUSTER_CATALOG_COLLECTION_ERROR,
        msg="$listClusterCatalog inside $lookup should produce a collection-level error",
    ),
    ListClusterCatalogTestCase(
        id="inside_unionWith",
        docs=[],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$unionWith": {
                        "coll": "other",
                        "pipeline": [{"$listClusterCatalog": {}}],
                    }
                }
            ],
            "cursor": {},
        },
        error_code=LIST_CLUSTER_CATALOG_COLLECTION_ERROR,
        msg="$listClusterCatalog inside $unionWith should produce a collection-level error",
    ),
]

# Property [Downstream Stage Composition]: $listClusterCatalog output can be
# filtered, projected, sorted, grouped, and counted by downstream stages.
COMPOSITION_TESTS: list[ListClusterCatalogTestCase] = [
    ListClusterCatalogTestCase(
        id="match_by_type",
        docs=[],
        pipeline=[
            {"$listClusterCatalog": {}},
            {"$match": {"type": "collection"}},
        ],
        expected={"type": Eq("collection"), "ns": IsType("string")},
        msg="$match should filter catalog output by type",
    ),
    ListClusterCatalogTestCase(
        id="project_fields",
        docs=[],
        pipeline=[
            {"$listClusterCatalog": {}},
            {"$project": {"ns": 1, "type": 1, "_id": 0}},
            {"$limit": 1},
        ],
        expected={
            "ns": IsType("string"),
            "type": Exists(),
            "db": NotExists(),
            "options": NotExists(),
        },
        msg="$project should exclude non-projected fields",
    ),
    ListClusterCatalogTestCase(
        id="count",
        docs=[],
        pipeline=[
            {"$listClusterCatalog": {}},
            {"$count": "total"},
        ],
        expected={"total": Gte(1), "ns": NotExists()},
        msg="$count should produce a single document with only the count field",
    ),
    ListClusterCatalogTestCase(
        id="group_by_type",
        docs=[],
        pipeline=[
            {"$listClusterCatalog": {}},
            {"$group": {"_id": "$type", "count": {"$sum": 1}}},
        ],
        expected={"_id": IsType("string"), "count": Gte(1), "ns": NotExists()},
        msg="$group should produce grouped documents without original fields",
    ),
    ListClusterCatalogTestCase(
        id="sort_and_limit",
        docs=[],
        pipeline=[
            {"$listClusterCatalog": {}},
            {"$sort": {"ns": 1}},
            {"$limit": 1},
        ],
        expected={"ns": IsType("string"), "db": IsType("string")},
        msg="$sort followed by $limit should return a single catalog document",
    ),
    ListClusterCatalogTestCase(
        id="add_fields",
        docs=[],
        pipeline=[
            {"$listClusterCatalog": {}},
            {"$addFields": {"dbUpper": {"$toUpper": "$db"}}},
            {"$limit": 1},
        ],
        expected={"dbUpper": IsType("string"), "db": IsType("string"), "ns": IsType("string")},
        msg="$addFields should add computed fields while preserving originals",
    ),
]

POSITION_TESTS: list[ListClusterCatalogTestCase] = SUB_PIPELINE_TESTS + COMPOSITION_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test", pytest_params(POSITION_TESTS))
def test_listClusterCatalog_position(collection: Collection, test: ListClusterCatalogTestCase):
    """Test $listClusterCatalog pipeline position and composition."""
    db = collection.database
    resolved = test.prepare(db, collection)
    ctx = StageContext.from_collection(resolved)
    result = execute_command(resolved, test.build_command(collection, ctx))
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
