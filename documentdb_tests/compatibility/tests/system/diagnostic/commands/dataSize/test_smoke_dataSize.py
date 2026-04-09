"""
Smoke test for dataSize command.

Tests basic dataSize command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_dataSize(collection):
    """Test basic dataSize command behavior."""
    collection.insert_one({"_id": 1, "x": 1})

    result = execute_command(
        collection, {"dataSize": f"{collection.database.name}.{collection.name}"}
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support dataSize command")
