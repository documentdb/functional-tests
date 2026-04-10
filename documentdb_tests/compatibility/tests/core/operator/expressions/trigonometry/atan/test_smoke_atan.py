"""
Smoke test for $atan expression.

Tests basic $atan expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_atan(collection):
    """Test basic $atan expression behavior."""
    collection.insert_many([{"_id": 1, "value": 0}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$atan": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": 0.0}]
    assertSuccess(result, expected, msg="Should support $atan expression")
