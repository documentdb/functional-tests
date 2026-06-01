"""Tests for view chaining."""

from __future__ import annotations

import pytest

from documentdb_tests.framework.assertions import assertSuccess
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
