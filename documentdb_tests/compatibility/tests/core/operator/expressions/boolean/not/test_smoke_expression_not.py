"""
Smoke test for $not expression.

Tests basic $not expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_not(collection):
    """Test basic $not expression behavior."""
    collection.insert_many([{"_id": 1, "value": True}, {"_id": 2, "value": False}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$not": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": False}, {"_id": 2, "result": True}]
    assertSuccess(result, expected, msg="Should support $not expression")
