"""
Smoke test for $addFields aggregation stage.

Tests basic $addFields aggregation functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_addFields(collection):
    """Test basic $addFields aggregation behavior."""
    collection.insert_many([{"_id": 1, "x": 5}, {"_id": 2, "x": 10}])

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$addFields": {"y": 20}}], "cursor": {}},
    )

    expected = [{"_id": 1, "x": 5, "y": 20}, {"_id": 2, "x": 10, "y": 20}]
    assertSuccess(result, expected, msg="Should support $addFields aggregation stage")
