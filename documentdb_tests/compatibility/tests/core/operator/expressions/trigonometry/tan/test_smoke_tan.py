"""
Smoke test for $tan expression.

Tests basic $tan expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_tan(collection):
    """Test basic $tan expression behavior."""
    collection.insert_many([{"_id": 1, "value": 0}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$tan": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": 0.0}]
    assertSuccess(result, expected, msg="Should support $tan expression")
