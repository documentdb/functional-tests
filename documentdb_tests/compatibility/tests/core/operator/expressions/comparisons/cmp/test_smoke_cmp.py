"""
Smoke test for $cmp expression.

Tests basic $cmp expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_cmp(collection):
    """Test basic $cmp expression behavior."""
    collection.insert_many(
        [{"_id": 1, "a": 10, "b": 5}, {"_id": 2, "a": 5, "b": 10}, {"_id": 3, "a": 7, "b": 7}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$cmp": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": 1}, {"_id": 2, "result": -1}, {"_id": 3, "result": 0}]
    assertSuccess(result, expected, msg="Should support $cmp expression")
