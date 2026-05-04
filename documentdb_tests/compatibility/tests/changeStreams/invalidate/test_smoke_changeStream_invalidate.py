"""
Smoke test for invalidate change stream event.

Tests basic invalidate change stream event functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.replica_set
def test_smoke_changeStream_invalidate(collection):
    """Test basic invalidate change stream event behavior."""
    collection.insert_one({"_id": 1, "x": 1})

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$changeStream": {}}], "cursor": {}},
    )

    cursor_id = result["cursor"]["id"]

    execute_command(collection, {"drop": collection.name})

    result = execute_command(collection, {"getMore": cursor_id, "collection": collection.name})
    result = result["cursor"]["nextBatch"][1]

    expected = {"operationType": "invalidate"}
    assertSuccessPartial(result, expected, msg="Should support invalidate change stream event")
