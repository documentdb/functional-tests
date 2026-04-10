"""
Smoke test for $gt expression.

Tests basic $gt expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_gt(collection):
    """Test basic $gt expression behavior."""
    collection.insert_many([{"_id": 1, "qty": 250}, {"_id": 2, "qty": 200}, {"_id": 3, "qty": 300}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"isGreater": {"$gt": ["$qty", 250]}}}],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "isGreater": False},
        {"_id": 2, "isGreater": False},
        {"_id": 3, "isGreater": True},
    ]
    assertSuccess(result, expected, msg="Should support $gt expression")
