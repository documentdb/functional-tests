"""
Smoke test for $bitAnd expression.

Tests basic $bitAnd expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_bitAnd(collection):
    """Test basic $bitAnd expression behavior."""
    collection.insert_many([{"_id": 1, "a": 5, "b": 3}, {"_id": 2, "a": 12, "b": 10}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$bitAnd": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": 1}, {"_id": 2, "result": 8}]
    assertSuccess(result, expected, msg="Should support $bitAnd expression")
