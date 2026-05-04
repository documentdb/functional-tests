"""
Smoke test for drop change stream event.

Tests basic drop change stream event functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_changeStream_drop(collection):
    """Test basic drop change stream event behavior."""
    collection.insert_one({"_id": 1, "x": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$changeStream": {}}, {"$match": {"operationType": "drop"}}],
            "cursor": {},
        },
    )

    cursor_id = result["cursor"]["id"]

    execute_command(collection, {"drop": collection.name})

    result = execute_command(collection, {"getMore": cursor_id, "collection": collection.name})
    result = result["cursor"]["nextBatch"][0]

    expected = {
        "operationType": "drop",
        "ns": {"db": collection.database.name, "coll": collection.name},
    }
    assertSuccessPartial(result, expected, msg="Should support drop change stream event")
