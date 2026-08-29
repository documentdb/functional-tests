"""
Smoke test for getMore command.

Tests basic getMore command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_getMore(collection):
    """Test basic getMore command behavior."""
    collection.insert_many([{"_id": 1, "value": 1}, {"_id": 2, "value": 2}, {"_id": 3, "value": 3}])

    initial_result = execute_command(collection, {"find": collection.name, "batchSize": 2})
    # Extract the cursor id defensively: if the setup find errored (returning an
    # exception rather than a dict) fall back to 0 so getMore reports the failure
    # cleanly, instead of a TypeError from subscripting an exception object.
    cursor_id = 0
    if isinstance(initial_result, dict):
        cursor_id = initial_result.get("cursor", {}).get("id", 0)

    result = execute_command(collection, {"getMore": cursor_id, "collection": collection.name})

    assertCommandSupported(result, msg="Should support getMore command")
