"""
Smoke test for $gt query operator.

Tests basic $gt query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_query_gt(collection):
    """Test basic $gt query operator behavior."""
    collection.insert_many([{"_id": 1, "qty": 20}, {"_id": 2, "qty": 30}, {"_id": 3, "qty": 15}])

    result = execute_command(collection, {"find": collection.name, "filter": {"qty": {"$gt": 20}}})

    expected = [{"_id": 2, "qty": 30}]
    assertSuccess(result, expected, msg="Should support $gt query operator")
