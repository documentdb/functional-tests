"""
Smoke test for $replaceWith stage.

Tests basic $replaceWith functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_replaceWith(collection):
    """Test basic $replaceWith behavior."""
    collection.insert_many(
        [
            {"_id": 1, "data": {"name": "Alice", "age": 30}},
            {"_id": 2, "data": {"name": "Bob", "age": 25}},
        ]
    )

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$replaceWith": "$data"}], "cursor": {}},
    )

    expected = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
    assertSuccess(result, expected, msg="Should support $replaceWith stage")
