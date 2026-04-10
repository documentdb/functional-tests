"""
Smoke test for $degreesToRadians expression.

Tests basic $degreesToRadians expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_degreesToRadians(collection):
    """Test basic $degreesToRadians expression behavior."""
    collection.insert_many([{"_id": 1, "degrees": 0}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"radians": {"$degreesToRadians": "$degrees"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "radians": 0.0}]
    assertSuccess(result, expected, msg="Should support $degreesToRadians expression")
