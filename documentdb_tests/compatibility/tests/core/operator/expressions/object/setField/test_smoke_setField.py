"""
Smoke test for $setField expression.

Tests basic $setField expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_setField(collection):
    """Test basic $setField expression behavior."""
    collection.insert_many([{"_id": 1, "item": {"name": "Alice", "age": 30}}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "updated": {"$setField": {"field": "age", "input": "$item", "value": 31}}
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "updated": {"name": "Alice", "age": 31}}]
    assertSuccess(result, expected, msg="Should support $setField expression")
