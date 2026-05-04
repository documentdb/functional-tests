"""
Smoke test for refineCollectionShardKey change stream event.

Tests basic refineCollectionShardKey change stream event functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
@pytest.mark.skip(reason="refineCollectionShardKey operations not supported in this environment")
def test_smoke_changeStream_refineCollectionShardKey(collection):
    """Test basic refineCollectionShardKey change stream event behavior."""
    collection.insert_one({"_id": 1, "x": 1, "y": 1})

    execute_command(
        collection,
        {"shardCollection": f"{collection.database.name}.{collection.name}", "key": {"x": 1}},
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$changeStream": {"showExpandedEvents": True}},
                {"$match": {"operationType": "refineCollectionShardKey"}},
            ],
            "cursor": {},
        },
    )

    cursor_id = result["cursor"]["id"]

    execute_command(
        collection,
        {
            "refineCollectionShardKey": f"{collection.database.name}.{collection.name}",
            "key": {"x": 1, "y": 1},
        },
    )

    result = execute_command(collection, {"getMore": cursor_id, "collection": collection.name})

    result = result["cursor"]["nextBatch"][0]

    expected = {
        "operationType": "refineCollectionShardKey",
        "ns": {"db": collection.database.name, "coll": collection.name},
    }
    assertSuccessPartial(
        result, expected, msg="Should support refineCollectionShardKey change stream event"
    )
