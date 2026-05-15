"""
Smoke test for views.

Tests basic view functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_views(collection):
    """Test basic view creation and querying."""
    collection.insert_many(
        [
            {"_id": 1, "name": "Alice", "age": 30.0},
            {"_id": 2, "name": "Bob", "age": 25.0},
            {"_id": 3, "name": "Charlie", "age": 35.0},
        ]
    )

    execute_command(
        collection,
        {
            "create": f"{collection.name}_view",
            "viewOn": collection.name,
            "pipeline": [{"$match": {"age": {"$gte": 30}}}],
        },
    )

    result = execute_command(collection, {"find": f"{collection.name}_view", "sort": {"_id": 1}})

    expected = [
        {"_id": 1, "name": "Alice", "age": 30.0},
        {"_id": 3, "name": "Charlie", "age": 35.0},
    ]
    assertSuccess(result, expected, msg="Should support creating and querying views")
