"""
Smoke test for shardCollection change stream event.

Tests basic shardCollection change stream event functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
@pytest.mark.skip(reason="shardCollection events not captured even with showExpandedEvents")
def test_smoke_changeStream_shardCollection(collection):
    """Test basic shardCollection change stream event behavior."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$changeStream": {"showExpandedEvents": True}},
                {"$match": {"operationType": "shardCollection"}},
            ],
            "cursor": {},
        },
    )

    cursor_id = result["cursor"]["id"]

    execute_command(
        collection,
        {"shardCollection": f"{collection.database.name}.{collection.name}", "key": {"_id": 1}},
    )

    result = execute_command(collection, {"getMore": cursor_id, "collection": "$cmd.aggregate"})

    result = result["cursor"]["nextBatch"][0]

    expected = {
        "operationType": "shardCollection",
        "ns": {"db": collection.database.name, "coll": collection.name},
    }
    assertSuccessPartial(result, expected, msg="Should support shardCollection change stream event")
