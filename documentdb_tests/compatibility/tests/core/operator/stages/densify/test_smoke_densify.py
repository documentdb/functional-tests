"""
Smoke test for $densify stage.

Tests basic $densify functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_densify(collection):
    """Test basic $densify behavior."""
    collection.insert_many([{"_id": 1, "val": 1, "time": 1}, {"_id": 2, "val": 2, "time": 5}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$densify": {"field": "time", "range": {"step": 1, "bounds": "full"}}}],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "val": 1, "time": 1},
        {"time": 2},
        {"time": 3},
        {"time": 4},
        {"_id": 2, "val": 2, "time": 5},
    ]
    assertSuccess(result, expected, msg="Should support $densify stage")
