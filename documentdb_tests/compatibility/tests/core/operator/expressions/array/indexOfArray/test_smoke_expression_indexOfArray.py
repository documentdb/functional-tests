"""
Smoke test for $indexOfArray expression.

Tests basic $indexOfArray expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_indexOfArray(collection):
    """Test basic $indexOfArray expression behavior."""
    collection.insert_many(
        [
            {"_id": 1, "array": [10, 20, 30], "search": 20},
            {"_id": 2, "array": [5, 15, 25], "search": 15},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"index": {"$indexOfArray": ["$array", "$search"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "index": 1}, {"_id": 2, "index": 1}]
    assertSuccess(result, expected, msg="Should support $indexOfArray expression")
