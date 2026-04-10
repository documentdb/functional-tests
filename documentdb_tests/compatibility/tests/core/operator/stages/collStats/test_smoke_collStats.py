"""
Smoke test for $collStats aggregation stage.

Tests basic $collStats functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_collStats(collection):
    """Test basic $collStats aggregation stage behavior."""
    collection.insert_many([{"_id": 1, "x": 5}, {"_id": 2, "x": 10}])

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$collStats": {"count": {}}}], "cursor": {}},
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $collStats aggregation stage")
