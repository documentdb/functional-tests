"""
Smoke test for create change stream event.

Tests basic create change stream event functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_changeStream_create(collection):
    """Test basic create change stream event behavior."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$changeStream": {"showExpandedEvents": True}},
                {"$match": {"operationType": "create"}},
            ],
            "cursor": {},
        },
    )

    cursor_id = result["cursor"]["id"]

    new_coll_name = f"{collection.name}_create_event"
    execute_command(collection, {"create": new_coll_name})

    result = execute_command(collection, {"getMore": cursor_id, "collection": "$cmd.aggregate"})
    result = result["cursor"]["nextBatch"][0]

    expected = {
        "operationType": "create",
        "ns": {"db": collection.database.name, "coll": new_coll_name},
    }
    assertSuccessPartial(result, expected, msg="Should support create change stream event")
