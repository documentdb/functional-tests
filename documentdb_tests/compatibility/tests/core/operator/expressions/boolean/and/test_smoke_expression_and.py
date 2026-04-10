"""
Smoke test for $and expression.

Tests basic $and expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_and(collection):
    """Test basic $and expression behavior."""
    collection.insert_many([{"_id": 1, "a": True, "b": True}, {"_id": 2, "a": True, "b": False}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$and": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": True}, {"_id": 2, "result": False}]
    assertSuccess(result, expected, msg="Should support $and expression")
