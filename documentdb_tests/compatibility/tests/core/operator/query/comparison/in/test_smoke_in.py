"""
Smoke test for $in query operator.

Tests basic $in query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_in(collection):
    """Test basic $in query operator behavior."""
    collection.insert_many([{"_id": 1, "qty": 20}, {"_id": 2, "qty": 30}, {"_id": 3, "qty": 15}])

    result = execute_command(
        collection, {"find": collection.name, "filter": {"qty": {"$in": [15, 30]}}}
    )

    expected = [{"_id": 2, "qty": 30}, {"_id": 3, "qty": 15}]
    assertSuccess(result, expected, msg="Should support $in query operator")
