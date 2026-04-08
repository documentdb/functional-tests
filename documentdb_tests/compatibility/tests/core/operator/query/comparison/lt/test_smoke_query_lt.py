"""
Smoke test for $lt query operator.

Tests basic $lt query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_query_lt(collection):
    """Test basic $lt query operator behavior."""
    collection.insert_many([{"_id": 1, "qty": 20}, {"_id": 2, "qty": 30}, {"_id": 3, "qty": 15}])

    result = execute_command(collection, {"find": collection.name, "filter": {"qty": {"$lt": 20}}})

    expected = [{"_id": 3, "qty": 15}]
    assertSuccess(result, expected, msg="Should support $lt query operator")
