"""
Smoke test for rename change stream event.

Tests basic rename change stream event functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_changeStream_rename(collection):
    """Test basic rename change stream event behavior."""
    collection.insert_one({"_id": 1, "x": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$changeStream": {"showExpandedEvents": True}},
                {"$match": {"operationType": "rename"}},
            ],
            "cursor": {},
        },
    )

    cursor_id = result["cursor"]["id"]

    execute_admin_command(
        collection,
        {
            "renameCollection": f"{collection.database.name}.{collection.name}",
            "to": f"{collection.database.name}.{collection.name}_renamed",
        },
    )

    result = execute_command(collection, {"getMore": cursor_id, "collection": collection.name})
    result = result["cursor"]["nextBatch"][0]

    expected = {
        "operationType": "rename",
        "ns": {"db": collection.database.name, "coll": collection.name},
    }
    assertSuccessPartial(result, expected, msg="Should support rename change stream event")
