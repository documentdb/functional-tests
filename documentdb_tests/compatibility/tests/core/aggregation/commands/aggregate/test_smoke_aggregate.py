"""
Smoke test for aggregate command.

Tests basic aggregate command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_aggregate(collection):
    """Test basic aggregate command behavior."""
    collection.insert_many([{"_id": 1, "x": 10}])

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$match": {"x": {"$gt": 0}}}], "cursor": {}},
    )

    expected = [{"_id": 1, "x": 10}]
    assertSuccess(result, expected, msg="Should support aggregate command")
