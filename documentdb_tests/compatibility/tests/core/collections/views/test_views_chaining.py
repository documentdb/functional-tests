"""Tests for view chaining and depth limits."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import VIEW_DEPTH_LIMIT_ERROR
from documentdb_tests.framework.executor import execute_command


# Property [View-on-View Composition]: a view referencing another view
# composes both pipelines correctly.
@pytest.mark.collection_mgmt
def test_views_chaining_composition(database_client, collection):
    """Test view-on-view pipeline composition."""
    collection.insert_many(
        [
            {"_id": 1, "x": 10, "y": "a"},
            {"_id": 2, "x": 20, "y": "b"},
            {"_id": 3, "x": 30, "y": "a"},
        ]
    )
    view1 = f"{collection.name}_v1"
    view2 = f"{collection.name}_v2"
    database_client.command(
        "create",
        view1,
        viewOn=collection.name,
        pipeline=[{"$match": {"x": {"$gte": 20}}}],
    )
    database_client.command(
        "create",
        view2,
        viewOn=view1,
        pipeline=[{"$project": {"x": 1}}],
    )
    result = execute_command(
        database_client[view2],
        {"find": view2, "sort": {"_id": 1}},
    )
    assertSuccess(
        result,
        [{"_id": 2, "x": 20}, {"_id": 3, "x": 30}],
        msg="view-on-view should compose both pipelines correctly",
    )


# Property [Depth Limit Exceeded]: querying a view chain deeper than 20
# levels produces the view-depth-limit error.
@pytest.mark.collection_mgmt
def test_views_depth_limit_exceeded(database_client, collection):
    """Test view depth limit is enforced at query time."""
    collection.insert_many([{"_id": 1, "x": 10}])
    prev = collection.name
    for i in range(1, 21):
        name = f"{collection.name}_d{i}"
        database_client.command("create", name, viewOn=prev, pipeline=[])
        prev = name
    result = execute_command(
        database_client[prev],
        {"find": prev},
    )
    assertFailureCode(
        result,
        VIEW_DEPTH_LIMIT_ERROR,
        msg="querying a view chain exceeding depth 20 should fail",
    )


# Property [Depth Limit Boundary]: a view chain at exactly depth 19 is
# queryable without error.
@pytest.mark.collection_mgmt
def test_views_depth_limit_at_boundary(database_client, collection):
    """Test view at exactly depth 19 is queryable."""
    collection.insert_many([{"_id": 1, "x": 10}])
    prev = collection.name
    for i in range(1, 20):
        name = f"{collection.name}_b{i}"
        database_client.command("create", name, viewOn=prev, pipeline=[])
        prev = name
    result = execute_command(
        database_client[prev],
        {"find": prev, "sort": {"_id": 1}},
    )
    assertSuccess(
        result,
        [{"_id": 1, "x": 10}],
        msg="view chain at depth 19 should be queryable",
    )
