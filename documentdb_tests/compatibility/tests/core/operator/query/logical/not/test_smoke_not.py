"""
Smoke test for $not query operator.

Tests basic $not functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_not(collection):
    """Test basic $not query operator behavior."""
    collection.insert_many([{"_id": 1, "x": 5}, {"_id": 2, "x": 15}, {"_id": 3, "x": 25}])

    result = execute_command(
        collection, {"find": collection.name, "filter": {"x": {"$not": {"$gt": 10}}}}
    )

    expected = [{"_id": 1, "x": 5}]
    assertSuccess(result, expected, msg="Should support $not query operator")
