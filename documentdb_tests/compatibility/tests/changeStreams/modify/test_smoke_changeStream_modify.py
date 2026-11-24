"""
Smoke test for modify change stream event.

Tests basic modify change stream event functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertChangeStreamEvent
from documentdb_tests.framework.executor import execute_command, execute_command_until

pytestmark = pytest.mark.smoke


@pytest.mark.requires(change_streams=True)
def test_smoke_changeStream_modify(collection):
    """Test basic modify change stream event behavior."""
    collection.insert_one({"_id": 1, "x": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$changeStream": {"showExpandedEvents": True}},
                {"$match": {"operationType": "modify"}},
            ],
            "cursor": {},
        },
    )
    # Extract the cursor id defensively: if opening the change stream errored,
    # fall back to 0 so the getMore + single assertion below report the failure
    # cleanly instead of a TypeError from subscripting an exception object.
    cursor_id = result.get("cursor", {}).get("id", 0) if isinstance(result, dict) else 0

    # A $jsonSchema validator is the most widely supported validator form, so the
    # probe tests the modify event rather than which query operators a validator
    # may use.
    execute_command(
        collection,
        {"collMod": collection.name, "validator": {"$jsonSchema": {"required": ["x"]}}},
    )

    # Some engines publish the DDL event after the first getMore returns, so
    # read until a batch is non-empty or the timeout passes.
    result = execute_command_until(
        collection,
        {"getMore": cursor_id, "collection": collection.name},
        lambda r: bool(r.get("cursor", {}).get("nextBatch")),
    )

    # An empty batch means the modify event was not emitted; fail with a clear
    # message instead of an IndexError when indexing nextBatch[0].
    assertChangeStreamEvent(result, msg="Should support modify change stream event")
