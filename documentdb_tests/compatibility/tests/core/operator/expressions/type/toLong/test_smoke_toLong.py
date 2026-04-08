"""
Smoke test for $toLong expression.

Tests basic $toLong expression functionality.
"""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_toLong(collection):
    """Test basic $toLong expression behavior."""
    collection.insert_many([{"_id": 1, "value": "123"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"long": {"$toLong": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "long": Int64(123)}]
    assertSuccess(result, expected, msg="Should support $toLong expression")
