"""
Smoke test for killCursors command.

Tests basic killCursors command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_killCursors(collection):
    """Test basic killCursors command behavior."""
    collection.insert_many([{"_id": 1, "value": 1}, {"_id": 2, "value": 2}])

    initial_result = execute_command(collection, {"find": collection.name, "batchSize": 1})

    cursor_id = initial_result["cursor"]["id"]

    result = execute_command(collection, {"killCursors": collection.name, "cursors": [cursor_id]})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support killCursors command")
