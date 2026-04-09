"""
Smoke test for $exists query operator.

Tests basic $exists functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_exists(collection):
    """Test basic $exists query operator behavior."""
    collection.insert_many([{"_id": 1, "x": 5}, {"_id": 2, "y": 10}, {"_id": 3, "x": 15}])

    result = execute_command(
        collection, {"find": collection.name, "filter": {"x": {"$exists": True}}}
    )

    expected = [{"_id": 1, "x": 5}, {"_id": 3, "x": 15}]
    assertSuccess(result, expected, msg="Should support $exists query operator")
