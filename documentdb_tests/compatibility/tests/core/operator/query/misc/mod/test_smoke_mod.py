"""
Smoke test for $mod query operator.

Tests basic $mod functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_mod(collection):
    """Test basic $mod query operator behavior."""
    collection.insert_many([{"_id": 1, "x": 5}, {"_id": 2, "x": 10}, {"_id": 3, "x": 15}])

    result = execute_command(
        collection, {"find": collection.name, "filter": {"x": {"$mod": [5, 0]}}}
    )

    expected = [{"_id": 1, "x": 5}, {"_id": 2, "x": 10}, {"_id": 3, "x": 15}]
    assertSuccess(result, expected, msg="Should support $mod query operator")
