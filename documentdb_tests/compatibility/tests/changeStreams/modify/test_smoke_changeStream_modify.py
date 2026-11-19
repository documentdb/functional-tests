"""
Smoke test for modify change stream event.

Tests basic modify change stream event functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertChangeStreamEvent
from documentdb_tests.framework.executor import execute_command

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

    execute_command(collection, {"collMod": collection.name, "validator": {"x": {"$type": "int"}}})

    result = execute_command(collection, {"getMore": cursor_id, "collection": collection.name})

    # An empty batch means the expanded modify event was not emitted; fail with a
    # clear message instead of an IndexError when indexing nextBatch[0].
    assertChangeStreamEvent(result, msg="Should support modify change stream event")
