"""
Smoke test for $setDifference expression.

Tests basic $setDifference expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_setDifference(collection):
    """Test basic $setDifference expression behavior."""
    collection.insert_many([{"_id": 1, "set1": [1, 2, 4], "set2": [2, 4, 6]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"difference": {"$setDifference": ["$set1", "$set2"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "difference": [1]}]
    assertSuccess(result, expected, msg="Should support $setDifference expression")
