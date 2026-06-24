"""
readConcern with views tests.

Verifies that readConcern is accepted when querying views.
"""

import uuid

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


@pytest.fixture
def view_collection(database_client, collection):
    """Create a view on top of the test collection."""
    collection.insert_many([{"_id": 1, "x": 10}, {"_id": 2, "x": 20}, {"_id": 3, "x": 5}])
    view_name = f"rc_view_{uuid.uuid4().hex[:8]}"
    database_client.command(
        "create", view_name, viewOn=collection.name, pipeline=[{"$match": {"x": {"$gte": 10}}}]
    )
    yield database_client[view_name]
    database_client.drop_collection(view_name)


def test_find_read_concern_on_view(view_collection):
    """Test find with readConcern on a view returns view results."""
    result = execute_command(
        view_collection,
        {
            "find": view_collection.name,
            "filter": {},
            "sort": {"_id": 1},
            "readConcern": {"level": "local"},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "x": 10}, {"_id": 2, "x": 20}],
        msg="find with readConcern on view should return filtered view results.",
    )


def test_aggregate_read_concern_on_view(view_collection):
    """Test aggregate with readConcern on a view returns view results."""
    result = execute_command(
        view_collection,
        {
            "aggregate": view_collection.name,
            "pipeline": [{"$sort": {"_id": 1}}],
            "cursor": {},
            "readConcern": {"level": "majority"},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "x": 10}, {"_id": 2, "x": 20}],
        msg="aggregate with readConcern on view should return view results.",
    )
