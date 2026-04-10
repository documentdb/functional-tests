"""
Smoke test for $bitXor expression.

Tests basic $bitXor expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_bitXor(collection):
    """Test basic $bitXor expression behavior."""
    collection.insert_many([{"_id": 1, "a": 5, "b": 3}, {"_id": 2, "a": 12, "b": 10}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$bitXor": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": 6}, {"_id": 2, "result": 6}]
    assertSuccess(result, expected, msg="Should support $bitXor expression")
