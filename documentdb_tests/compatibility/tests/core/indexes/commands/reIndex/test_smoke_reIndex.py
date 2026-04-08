"""
Smoke test for reIndex command.

Tests basic reIndex command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_reIndex(collection):
    """Test basic reIndex command behavior."""
    collection.insert_one({"_id": 1, "name": "test"})
    collection.create_index([("name", 1)])

    result = execute_command(collection, {"reIndex": collection.name})

    expected = {
        "nIndexesWas": 2,
        "nIndexes": 2,
        "indexes": [
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"name": 1}, "name": "name_1"},
        ],
        "ok": 1.0,
    }
    assertSuccess(result, expected, msg="Should support reIndex command", raw_res=True)
