"""
Smoke test for $trim expression.

Tests basic $trim expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_trim(collection):
    """Test basic $trim expression behavior."""
    collection.insert_many([{"_id": 1, "text": "   Hello   "}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"trimmed": {"$trim": {"input": "$text"}}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "trimmed": "Hello"}]
    assertSuccess(result, expected, msg="Should support $trim expression")
