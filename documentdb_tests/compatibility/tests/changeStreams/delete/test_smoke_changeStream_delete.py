"""
Smoke test for delete change stream event.

Tests basic delete change stream event functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_changeStream_delete(collection):
    """Test basic delete change stream event behavior."""
    collection.insert_one({"_id": 1, "x": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$changeStream": {}}, {"$match": {"operationType": "delete"}}],
            "cursor": {},
        },
    )

    cursor_id = result["cursor"]["id"]

    execute_command(
        collection, {"delete": collection.name, "deletes": [{"q": {"_id": 1}, "limit": 1}]}
    )

    result = execute_command(collection, {"getMore": cursor_id, "collection": collection.name})
    result = result["cursor"]["nextBatch"][0]

    expected = {
        "operationType": "delete",
        "ns": {"db": collection.database.name, "coll": collection.name},
    }
    assertSuccessPartial(result, expected, msg="Should support delete change stream event")
