"""
Smoke test for $nin query operator.

Tests basic $nin query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_nin(collection):
    """Test basic $nin query operator behavior."""
    collection.insert_many([{"_id": 1, "qty": 20}, {"_id": 2, "qty": 30}, {"_id": 3, "qty": 15}])

    result = execute_command(
        collection, {"find": collection.name, "filter": {"qty": {"$nin": [15, 30]}}}
    )

    expected = [{"_id": 1, "qty": 20}]
    assertSuccess(result, expected, msg="Should support $nin query operator")
