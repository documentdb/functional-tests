"""
Smoke test for $gte expression.

Tests basic $gte expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_gte(collection):
    """Test basic $gte expression behavior."""
    collection.insert_many([{"_id": 1, "qty": 250}, {"_id": 2, "qty": 200}, {"_id": 3, "qty": 300}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"isGreaterOrEqual": {"$gte": ["$qty", 250]}}}],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "isGreaterOrEqual": True},
        {"_id": 2, "isGreaterOrEqual": False},
        {"_id": 3, "isGreaterOrEqual": True},
    ]
    assertSuccess(result, expected, msg="Should support $gte expression")
