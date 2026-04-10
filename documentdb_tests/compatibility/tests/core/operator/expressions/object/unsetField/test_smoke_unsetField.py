"""
Smoke test for $unsetField expression.

Tests basic $unsetField expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_unsetField(collection):
    """Test basic $unsetField expression behavior."""
    collection.insert_many([{"_id": 1, "item": {"name": "Alice", "age": 30}}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"updated": {"$unsetField": {"field": "age", "input": "$item"}}}}
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "updated": {"name": "Alice"}}]
    assertSuccess(result, expected, msg="Should support $unsetField expression")
