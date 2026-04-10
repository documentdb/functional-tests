"""
Smoke test for $lt expression.

Tests basic $lt expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_lt(collection):
    """Test basic $lt expression behavior."""
    collection.insert_many([{"_id": 1, "qty": 250}, {"_id": 2, "qty": 200}, {"_id": 3, "qty": 300}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"isLess": {"$lt": ["$qty", 250]}}}],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "isLess": False},
        {"_id": 2, "isLess": True},
        {"_id": 3, "isLess": False},
    ]
    assertSuccess(result, expected, msg="Should support $lt expression")
