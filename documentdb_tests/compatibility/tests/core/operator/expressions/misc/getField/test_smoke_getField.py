"""
Smoke test for $getField expression.

Tests basic $getField expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_getField(collection):
    """Test basic $getField expression behavior."""
    collection.insert_many([{"_id": 1, "item": {"name": "Alice", "age": 30}}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"value": {"$getField": {"field": "name", "input": "$item"}}}}
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "value": "Alice"}]
    assertSuccess(result, expected, msg="Should support $getField expression")
