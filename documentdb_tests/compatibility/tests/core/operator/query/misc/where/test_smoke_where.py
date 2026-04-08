"""
Smoke test for $where query operator.

Tests basic $where functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_where(collection):
    """Test basic $where query operator behavior."""
    collection.insert_many(
        [{"_id": 1, "x": 5, "y": 10}, {"_id": 2, "x": 15, "y": 10}, {"_id": 3, "x": 5, "y": 3}]
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"$where": "this.y > this.x"}}
    )

    expected = [{"_id": 1, "x": 5, "y": 10}]
    assertSuccess(result, expected, msg="Should support $where query operator")
