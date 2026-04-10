"""
Smoke test for $setIntersection expression.

Tests basic $setIntersection expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_setIntersection(collection):
    """Test basic $setIntersection expression behavior."""
    collection.insert_many([{"_id": 1, "set1": [1, 2, 3], "set2": [2, 4, 6]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"intersection": {"$setIntersection": ["$set1", "$set2"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "intersection": [2]}]
    assertSuccess(result, expected, msg="Should support $setIntersection expression")
