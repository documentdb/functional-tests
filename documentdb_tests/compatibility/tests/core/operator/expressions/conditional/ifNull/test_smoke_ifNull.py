"""
Smoke test for $ifNull expression.

Tests basic $ifNull expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_ifNull(collection):
    """Test basic $ifNull expression behavior."""
    collection.insert_many([{"_id": 1, "name": "Alice"}, {"_id": 2, "name": None}, {"_id": 3}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"name": {"$ifNull": ["$name", "Unknown"]}}}],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "name": "Alice"},
        {"_id": 2, "name": "Unknown"},
        {"_id": 3, "name": "Unknown"},
    ]
    assertSuccess(result, expected, msg="Should support $ifNull expression")
