"""
Smoke test for $limit stage.

Tests basic $limit functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_limit(collection):
    """Test basic $limit behavior."""
    collection.insert_many(
        [{"_id": 1, "value": 10}, {"_id": 2, "value": 20}, {"_id": 3, "value": 30}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$sort": {"_id": 1}}, {"$limit": 2}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "value": 10}, {"_id": 2, "value": 20}]
    assertSuccess(result, expected, msg="Should support $limit stage")
