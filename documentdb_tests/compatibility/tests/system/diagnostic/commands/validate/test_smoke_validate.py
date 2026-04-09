"""
Smoke test for validate command.

Tests basic validate command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_validate(collection):
    """Test basic validate command behavior."""
    collection.insert_one({"_id": 1, "x": 1})

    result = execute_command(collection, {"validate": collection.name})

    expected = {"ok": 1.0, "ns": f"{collection.database.name}.{collection.name}"}
    assertSuccessPartial(result, expected, msg="Should support validate command")
