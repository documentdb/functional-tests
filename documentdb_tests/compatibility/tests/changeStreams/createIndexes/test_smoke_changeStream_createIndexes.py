"""
Smoke test for createIndexes change stream event.

Tests basic createIndexes change stream event functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_changeStream_createIndexes(collection):
    """Test basic createIndexes change stream event behavior."""
    collection.insert_one({"_id": 1, "x": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$changeStream": {"showExpandedEvents": True}},
                {"$match": {"operationType": "createIndexes"}},
            ],
            "cursor": {},
        },
    )

    cursor_id = result["cursor"]["id"]

    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"x": 1}, "name": "x_1"}]},
    )

    result = execute_command(collection, {"getMore": cursor_id, "collection": collection.name})
    result = result["cursor"]["nextBatch"][0]

    expected = {
        "operationType": "createIndexes",
        "ns": {"db": collection.database.name, "coll": collection.name},
    }
    assertSuccessPartial(result, expected, msg="Should support createIndexes change stream event")
