"""
Smoke test for $count aggregation stage.

Tests basic $count aggregation functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_stages_count(collection):
    """Test basic $count aggregation behavior."""
    collection.insert_many([{"_id": 1, "x": 5}, {"_id": 2, "x": 10}, {"_id": 3, "x": 15}])

    result = execute_command(
        collection, {"aggregate": collection.name, "pipeline": [{"$count": "total"}], "cursor": {}}
    )

    expected = [{"total": 3}]
    assertSuccess(result, expected, msg="Should support $count aggregation stage")
