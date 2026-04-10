"""
Smoke test for $group stage.

Tests basic $group functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_group(collection):
    """Test basic $group behavior."""
    collection.insert_many(
        [{"_id": 1, "category": "A", "amount": 10}, {"_id": 2, "category": "A", "amount": 30}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$group": {"_id": "$category", "total": {"$sum": "$amount"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "total": 40}]
    assertSuccess(result, expected, msg="Should support $group stage")
