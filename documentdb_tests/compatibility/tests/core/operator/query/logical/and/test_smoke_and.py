"""
Smoke test for $and query operator.

Tests basic $and functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_and(collection):
    """Test basic $and query operator behavior."""
    collection.insert_many(
        [{"_id": 1, "x": 5, "y": 10}, {"_id": 2, "x": 15, "y": 10}, {"_id": 3, "x": 5, "y": 20}]
    )

    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"$and": [{"x": {"$gt": 1}}, {"y": {"$lt": 15}}]}},
    )

    expected = [{"_id": 1, "x": 5, "y": 10}, {"_id": 2, "x": 15, "y": 10}]
    assertSuccess(result, expected, msg="Should support $and query operator")
