"""
Smoke test for tailable-cursors.

Tests basic tailable cursor functionality on capped collections.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_tailable_cursors(collection):
    """Test basic tailable cursor creation on capped collection."""
    execute_command(
        collection, {"create": f"{collection.name}_capped", "capped": True, "size": 4096.0}
    )

    capped_collection = collection.database[f"{collection.name}_capped"]
    capped_collection.insert_many([{"_id": 1, "value": "test1"}, {"_id": 2, "value": "test2"}])

    result = execute_command(
        collection, {"find": f"{collection.name}_capped", "tailable": True, "awaitData": False}
    )

    expected = [{"_id": 1, "value": "test1"}, {"_id": 2, "value": "test2"}]
    assertSuccess(result, expected, msg="Should support tailable cursors on capped collections")
