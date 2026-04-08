"""
Smoke test for $subtract expression.

Tests basic $subtract expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_subtract(collection):
    """Test basic $subtract expression behavior."""
    collection.insert_many([{"_id": 1, "a": 20, "b": 5}, {"_id": 2, "a": 30, "b": 10}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"difference": {"$subtract": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "difference": 15}, {"_id": 2, "difference": 20}]
    assertSuccess(result, expected, msg="Should support $subtract expression")
