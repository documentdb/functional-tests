"""
Smoke test for $concatArrays expression.

Tests basic $concatArrays expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_concatArrays(collection):
    """Test basic $concatArrays expression behavior."""
    collection.insert_many(
        [{"_id": 1, "a": [1, 2], "b": [3, 4]}, {"_id": 2, "a": [5, 6], "b": [7, 8]}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"combined": {"$concatArrays": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "combined": [1, 2, 3, 4]}, {"_id": 2, "combined": [5, 6, 7, 8]}]
    assertSuccess(result, expected, msg="Should support $concatArrays expression")
