"""
Smoke test for update change stream event.

Tests basic update change stream event functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_changeStream_update(collection):
    """Test basic update change stream event behavior."""
    collection.insert_one({"_id": 1, "x": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$changeStream": {}}, {"$match": {"operationType": "update"}}],
            "cursor": {},
        },
    )

    cursor_id = result["cursor"]["id"]

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 2.0}}}]},
    )

    result = execute_command(collection, {"getMore": cursor_id, "collection": collection.name})
    result = result["cursor"]["nextBatch"][0]

    expected = {
        "operationType": "update",
        "ns": {"db": collection.database.name, "coll": collection.name},
    }
    assertSuccessPartial(result, expected, msg="Should support update change stream event")
