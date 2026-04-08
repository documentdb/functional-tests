"""
Smoke test for $radiansToDegrees expression.

Tests basic $radiansToDegrees expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_radiansToDegrees(collection):
    """Test basic $radiansToDegrees expression behavior."""
    collection.insert_many([{"_id": 1, "radians": 0}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"degrees": {"$radiansToDegrees": "$radians"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "degrees": 0.0}]
    assertSuccess(result, expected, msg="Should support $radiansToDegrees expression")
