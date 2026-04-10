"""
Smoke test for $eq query operator.

Tests basic $eq query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_query_eq(collection):
    """Test basic $eq query operator behavior."""
    collection.insert_many([{"_id": 1, "qty": 20}, {"_id": 2, "qty": 30}, {"_id": 3, "qty": 20}])

    result = execute_command(collection, {"find": collection.name, "filter": {"qty": {"$eq": 20}}})

    expected = [{"_id": 1, "qty": 20}, {"_id": 3, "qty": 20}]
    assertSuccess(result, expected, msg="Should support $eq query operator")
