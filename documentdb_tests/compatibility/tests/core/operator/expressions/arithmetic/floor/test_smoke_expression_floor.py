"""
Smoke test for $floor expression.

Tests basic $floor expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_floor(collection):
    """Test basic $floor expression behavior."""
    collection.insert_many([{"_id": 1, "value": 10.3}, {"_id": 2, "value": 20.7}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"floored": {"$floor": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "floored": 10.0}, {"_id": 2, "floored": 20.0}]
    assertSuccess(result, expected, msg="Should support $floor expression")
