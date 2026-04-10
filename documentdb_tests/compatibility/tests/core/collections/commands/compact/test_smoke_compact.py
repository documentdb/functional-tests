"""
Smoke test for compact command.

Tests basic compact command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_compact(collection):
    """Test basic compact command behavior."""
    collection.insert_many([{"_id": 1, "value": 10}, {"_id": 2, "value": 20}])

    result = execute_command(collection, {"compact": collection.name})

    expected = {"bytesFreed": 0, "ok": 1.0}
    assertSuccess(result, expected, msg="Should support compact command", raw_res=True)
