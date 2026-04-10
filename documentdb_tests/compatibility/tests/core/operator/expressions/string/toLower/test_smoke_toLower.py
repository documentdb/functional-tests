"""
Smoke test for $toLower expression.

Tests basic $toLower expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_toLower(collection):
    """Test basic $toLower expression behavior."""
    collection.insert_many([{"_id": 1, "text": "HELLO"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"lower": {"$toLower": "$text"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "lower": "hello"}]
    assertSuccess(result, expected, msg="Should support $toLower expression")
