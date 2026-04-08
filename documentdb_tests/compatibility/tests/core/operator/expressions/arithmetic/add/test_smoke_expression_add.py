"""
Smoke test for $add expression.

Tests basic $add expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_add(collection):
    """Test basic $add expression behavior."""
    collection.insert_many([{"_id": 1, "a": 10, "b": 20}, {"_id": 2, "a": 5, "b": 15}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"sum": {"$add": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "sum": 30}, {"_id": 2, "sum": 20}]
    assertSuccess(result, expected, msg="Should support $add expression")
