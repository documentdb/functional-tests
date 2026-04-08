"""
Smoke test for $or query operator.

Tests basic $or functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_or(collection):
    """Test basic $or query operator behavior."""
    collection.insert_many(
        [{"_id": 1, "x": 5, "y": 10}, {"_id": 2, "x": 15, "y": 10}, {"_id": 3, "x": 5, "y": 20}]
    )

    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"$or": [{"x": {"$gt": 10}}, {"y": {"$gt": 15}}]}},
    )

    expected = [{"_id": 2, "x": 15, "y": 10}, {"_id": 3, "x": 5, "y": 20}]
    assertSuccess(result, expected, msg="Should support $or query operator")
