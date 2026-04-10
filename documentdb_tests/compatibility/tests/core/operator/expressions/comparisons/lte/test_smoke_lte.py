"""
Smoke test for $lte expression.

Tests basic $lte expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_lte(collection):
    """Test basic $lte expression behavior."""
    collection.insert_many([{"_id": 1, "qty": 250}, {"_id": 2, "qty": 200}, {"_id": 3, "qty": 300}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"isLessOrEqual": {"$lte": ["$qty", 250]}}}],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "isLessOrEqual": True},
        {"_id": 2, "isLessOrEqual": True},
        {"_id": 3, "isLessOrEqual": False},
    ]
    assertSuccess(result, expected, msg="Should support $lte expression")
