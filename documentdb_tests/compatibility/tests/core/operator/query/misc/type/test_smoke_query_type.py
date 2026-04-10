"""
Smoke test for $type query operator.

Tests basic $type functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_query_type(collection):
    """Test basic $type query operator behavior."""
    collection.insert_many([{"_id": 1, "x": 5}, {"_id": 2, "x": "text"}, {"_id": 3, "x": 15}])

    result = execute_command(
        collection, {"find": collection.name, "filter": {"x": {"$type": "string"}}}
    )

    expected = [{"_id": 2, "x": "text"}]
    assertSuccess(result, expected, msg="Should support $type query operator")
