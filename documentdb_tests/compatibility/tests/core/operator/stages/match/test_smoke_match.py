"""
Smoke test for $match stage.

Tests basic $match functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_match(collection):
    """Test basic $match behavior."""
    collection.insert_many(
        [
            {"_id": 1, "status": "active", "value": 10},
            {"_id": 2, "status": "inactive", "value": 20},
            {"_id": 3, "status": "active", "value": 30},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"status": "active"}}],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "status": "active", "value": 10},
        {"_id": 3, "status": "active", "value": 30},
    ]
    assertSuccess(result, expected, msg="Should support $match stage")
