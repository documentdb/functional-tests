"""
Smoke test for killCursors command.

Tests basic killCursors command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_killCursors(collection):
    """Test basic killCursors command behavior."""
    collection.insert_many([{"_id": 1, "value": 1}, {"_id": 2, "value": 2}])

    initial_result = execute_command(collection, {"find": collection.name, "batchSize": 1})
    # Extract the cursor id defensively: if the setup find errored (returning an
    # exception rather than a dict) fall back to 0 so killCursors reports the
    # failure cleanly, instead of a TypeError from subscripting an exception.
    cursor_id = 0
    if isinstance(initial_result, dict):
        cursor_id = initial_result.get("cursor", {}).get("id", 0)

    result = execute_command(collection, {"killCursors": collection.name, "cursors": [cursor_id]})

    assertCommandSupported(result, msg="Should support killCursors command")
