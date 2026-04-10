"""
Smoke test for $bitOr expression.

Tests basic $bitOr expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_bitOr(collection):
    """Test basic $bitOr expression behavior."""
    collection.insert_many([{"_id": 1, "a": 5, "b": 3}, {"_id": 2, "a": 12, "b": 10}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$bitOr": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": 7}, {"_id": 2, "result": 14}]
    assertSuccess(result, expected, msg="Should support $bitOr expression")
