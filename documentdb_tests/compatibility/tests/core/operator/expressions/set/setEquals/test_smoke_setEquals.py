"""
Smoke test for $setEquals expression.

Tests basic $setEquals expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_setEquals(collection):
    """Test basic $setEquals expression behavior."""
    collection.insert_many(
        [
            {"_id": 1, "set1": [1, 2, 3], "set2": [3, 2, 1]},
            {"_id": 2, "set1": [1, 2, 3], "set2": [1, 2, 4]},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"isEqual": {"$setEquals": ["$set1", "$set2"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "isEqual": True}, {"_id": 2, "isEqual": False}]
    assertSuccess(result, expected, msg="Should support $setEquals expression")
