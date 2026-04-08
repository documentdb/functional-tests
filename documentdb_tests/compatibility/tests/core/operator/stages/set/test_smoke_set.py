"""
Smoke test for $set stage.

Tests basic $set functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_set(collection):
    """Test basic $set behavior."""
    collection.insert_many(
        [{"_id": 1, "name": "Alice", "age": 30}, {"_id": 2, "name": "Bob", "age": 25}]
    )

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$set": {"status": "active"}}], "cursor": {}},
    )

    expected = [
        {"_id": 1, "name": "Alice", "age": 30, "status": "active"},
        {"_id": 2, "name": "Bob", "age": 25, "status": "active"},
    ]
    assertSuccess(result, expected, msg="Should support $set stage")
