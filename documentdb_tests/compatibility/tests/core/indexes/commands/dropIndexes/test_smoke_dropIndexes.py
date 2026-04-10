"""
Smoke test for dropIndexes command.

Tests basic dropIndexes command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_dropIndexes(collection):
    """Test basic dropIndexes command behavior."""
    collection.insert_one({"_id": 1, "name": "test"})
    collection.create_index([("name", 1)], name="name_1")

    result = execute_command(collection, {"dropIndexes": collection.name, "index": "name_1"})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support dropIndexes command")
