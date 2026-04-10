"""
Smoke test for $setIsSubset expression.

Tests basic $setIsSubset expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_setIsSubset(collection):
    """Test basic $setIsSubset expression behavior."""
    collection.insert_many(
        [
            {"_id": 1, "set1": [1, 2], "set2": [1, 2, 3, 4]},
            {"_id": 2, "set1": [1, 5], "set2": [1, 2, 3, 4]},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"isSubset": {"$setIsSubset": ["$set1", "$set2"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "isSubset": True}, {"_id": 2, "isSubset": False}]
    assertSuccess(result, expected, msg="Should support $setIsSubset expression")
