"""
Smoke test for createIndexes command.

Tests basic createIndexes command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_createIndexes(collection):
    """Test basic createIndexes command behavior."""
    collection.insert_one({"_id": 1, "name": "test"})

    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"name": 1}, "name": "name_1"}]},
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support createIndexes command")
