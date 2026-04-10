"""
Smoke test for $ne query operator.

Tests basic $ne query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_query_ne(collection):
    """Test basic $ne query operator behavior."""
    collection.insert_many([{"_id": 1, "qty": 20}, {"_id": 2, "qty": 30}, {"_id": 3, "qty": 20}])

    result = execute_command(collection, {"find": collection.name, "filter": {"qty": {"$ne": 20}}})

    expected = [{"_id": 2, "qty": 30}]
    assertSuccess(result, expected, msg="Should support $ne query operator")
