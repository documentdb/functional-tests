"""
Smoke test for $indexOfBytes expression.

Tests basic $indexOfBytes expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_indexOfBytes(collection):
    """Test basic $indexOfBytes expression behavior."""
    collection.insert_many([{"_id": 1, "text": "Hello World"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"index": {"$indexOfBytes": ["$text", "World"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "index": 6}]
    assertSuccess(result, expected, msg="Should support $indexOfBytes expression")
