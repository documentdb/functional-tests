"""
Smoke test for $or expression.

Tests basic $or expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_or(collection):
    """Test basic $or expression behavior."""
    collection.insert_many([{"_id": 1, "a": True, "b": False}, {"_id": 2, "a": False, "b": False}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$or": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": True}, {"_id": 2, "result": False}]
    assertSuccess(result, expected, msg="Should support $or expression")
