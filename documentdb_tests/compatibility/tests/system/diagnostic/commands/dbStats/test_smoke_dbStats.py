"""
Smoke test for dbStats command.

Tests basic dbStats command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_dbStats(collection):
    """Test basic dbStats command behavior."""
    collection.insert_one({"_id": 1, "x": 1})

    result = execute_command(collection, {"dbStats": 1})

    expected = {"ok": 1.0, "db": collection.database.name}
    assertSuccessPartial(result, expected, msg="Should support dbStats command")
