"""
Smoke test for $split expression.

Tests basic $split expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_split(collection):
    """Test basic $split expression behavior."""
    collection.insert_many([{"_id": 1, "text": "a,b,c"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"parts": {"$split": ["$text", ","]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "parts": ["a", "b", "c"]}]
    assertSuccess(result, expected, msg="Should support $split expression")
