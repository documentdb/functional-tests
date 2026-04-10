"""
Smoke test for $substrCP expression.

Tests basic $substrCP expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_substrCP(collection):
    """Test basic $substrCP expression behavior."""
    collection.insert_many([{"_id": 1, "text": "Hello World"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"substring": {"$substrCP": ["$text", 0, 5]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "substring": "Hello"}]
    assertSuccess(result, expected, msg="Should support $substrCP expression")
