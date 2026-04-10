"""
Smoke test for $substr expression.

Tests basic $substr expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_substr(collection):
    """Test basic $substr expression behavior."""
    collection.insert_many([{"_id": 1, "text": "Hello World"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"substring": {"$substr": ["$text", 0, 5]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "substring": "Hello"}]
    assertSuccess(result, expected, msg="Should support $substr expression")
