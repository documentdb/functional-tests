"""
Smoke test for $expr query operator.

Tests basic $expr functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expr(collection):
    """Test basic $expr query operator behavior."""
    collection.insert_many(
        [{"_id": 1, "x": 5, "y": 10}, {"_id": 2, "x": 15, "y": 10}, {"_id": 3, "x": 5, "y": 3}]
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"$expr": {"$gt": ["$y", "$x"]}}}
    )

    expected = [{"_id": 1, "x": 5, "y": 10}]
    assertSuccess(result, expected, msg="Should support $expr query operator")
