"""
Smoke test for getMore command.

Tests basic getMore command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_getMore(collection):
    """Test basic getMore command behavior."""
    collection.insert_many([{"_id": 1, "value": 1}, {"_id": 2, "value": 2}, {"_id": 3, "value": 3}])

    initial_result = execute_command(collection, {"find": collection.name, "batchSize": 2})

    cursor_id = initial_result["cursor"]["id"]

    result = execute_command(collection, {"getMore": cursor_id, "collection": collection.name})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support getMore command")
